"""Compile the exact native production sources into an isolated test executable."""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def compile_harness(folder, name, source):
    folder = Path(folder)
    harness = folder / (name + '.cs')
    harness.write_text(source, encoding='utf-8')
    binary = folder / (name + '.exe')
    compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    result = subprocess.run([str(compiler), '/nologo', '/target:exe', '/main:' + name,
        '/reference:System.IO.Compression.dll', '/reference:Microsoft.CSharp.dll',
        '/reference:System.Web.Extensions.dll', '/out:' + str(binary),
        *map(str, sorted((ROOT / 'installer/native').glob('*.cs'))), str(harness)],
        capture_output=True, text=True)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return binary
