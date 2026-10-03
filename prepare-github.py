"""Stage a source snapshot, including modified vendored working trees as ordinary files.

Nested repositories keep their local history. Only their source files enter the outer index.
Run from the project root after `git init`; this helper does not commit or push.
"""
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKIP = {'.git', 'node_modules', '.venv', 'dist', '__pycache__', '.claude', '.codex', '.agents', '.aws', '_install', 'target'}

def git(*args, data=None):
    result = subprocess.run(['git', *args], cwd=ROOT, input=data, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', errors='replace'))
    return result.stdout

def main():
    files = []
    for current, directories, names in os.walk(ROOT):
        directories[:] = sorted(name for name in directories if name not in SKIP)
        for name in sorted(names):
            file = Path(current) / name
            if file.is_symlink():
                continue
            files.append(file.relative_to(ROOT).as_posix())
    encoded = b'\0'.join(name.encode('utf-8') for name in files) + b'\0'
    ignored = subprocess.run(['git', 'check-ignore', '--no-index', '-z', '--stdin'], cwd=ROOT,
                             input=encoded, capture_output=True)
    if ignored.returncode not in (0, 1):
        raise RuntimeError(ignored.stderr.decode('utf-8', errors='replace'))
    excluded = set(ignored.stdout.decode('utf-8').split('\0'))
    files = [name for name in files if name not in excluded]
    large = [name for name in files if (ROOT / name).stat().st_size >= 100 * 1024 * 1024]
    if large:
        raise RuntimeError('GitHub file limit exceeded: ' + ', '.join(large))
    entries = []
    for start in range(0, len(files), 100):
        batch = files[start:start + 100]
        hashes = git('hash-object', '-w', '--', *batch).decode('ascii').splitlines()
        if len(hashes) != len(batch):
            raise RuntimeError('Incomplete Git object output')
        entries.extend(f'100644 {digest}\t{name}'.encode('utf-8') + b'\0'
                       for digest, name in zip(hashes, batch))
    git('update-index', '-z', '--index-info', data=b''.join(entries))
    size = sum((ROOT / name).stat().st_size for name in files)
    print(f'Staged {len(files)} source files ({size / 1024 / 1024:.1f} MiB).')
    print('Vendored sources are ordinary tracked files; nested .git directories are excluded.')

if __name__ == '__main__':
    main()
