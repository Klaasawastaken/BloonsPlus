"""Check public source or installer payload for common credential and player-data leaks.
Outputs only finding locations, never matching secret values. This is a pattern guard,
not a guarantee that arbitrary personal information is detectable.
"""
from pathlib import Path
import argparse, re, subprocess, zipfile
ROOT = Path(__file__).resolve().parent.parent
PATTERNS = {
    'private key': re.compile(r'-----BEGIN (?:OPENSSH|RSA|EC) PRIVATE KEY-----'),
    'GitHub credential': re.compile(r'\b(?:ghp_|github_pat_)[A-Za-z0-9_]{25,}'),
    'OpenAI credential': re.compile(r'\bsk-(?:proj-)?[A-Za-z0-9_-]{35,}'),
    'personal Windows path': re.compile(r'C:[\\/]+Users[\\/]+(?!user\b|Public\b|Default\b|%s|%USERNAME%|\[USER\])[^\\/\s\"\']+', re.I),
    'Steam account identifier': re.compile(r'\b7656119\d{10}\b'),
}
PRIVATE_NAMES = {'live-frame.jpg', 'live-frame.jpg.tmp', 'viewer-request.json', 'profile.save', 'host.json', 'game-state.json', 'route-checkpoint.json', 'experimental-ai-data.json', 'route-failures.json', 'playthrough_stats.json', 'upgrade-memory.json', 'last-hero.json', 'pending-automation.json'}
TEXT_SUFFIXES = {'.js','.py','.cs','.md','.json','.txt','.html','.yml','.yaml','.ps1','.cmd','.toml'}
def inspect(name, data):
    findings=[]; path=Path(name)
    if 'private' in path.parts:
        findings.append((name, 'private project'))
    if path.name.lower() in PRIVATE_NAMES or path.suffix.lower() in {'.key','.pem','.pfx','.p12','.tmp'} or path.name.startswith(('.env','id_appsandbox')):
        findings.append((name,'private runtime file'))
    if path.suffix.lower() in TEXT_SUFFIXES:
        try: content=data.decode('utf-8')
        except UnicodeError: return findings
        for kind,pattern in PATTERNS.items():
            for match in pattern.finditer(content): findings.append((name+':'+str(content.count('\n',0,match.start())+1),kind))
    return findings

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--payload',type=Path);args=parser.parse_args();findings=[]
    if args.payload:
        with zipfile.ZipFile(args.payload) as archive:
            for name in archive.namelist():
                # Third-party Python packages contain neutral example paths; app sources are the boundary.
                if '/python/' in name or '/node_modules/' in name: continue
                findings.extend(inspect(name,archive.read(name)))
    else:
        names=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
        for name in names:
            path=ROOT/name
            if path.is_file(): findings.extend(inspect(name,path.read_bytes()))
    for location,kind in findings: print(kind+': '+location)
    print('Publication guard: '+str(len(findings))+' finding(s)')
    raise SystemExit(1 if findings else 0)
if __name__=='__main__':main()
