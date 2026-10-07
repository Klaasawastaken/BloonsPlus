"""Real offline pip failure/retry through the production native installer."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from native_installer_harness import compile_harness


def wheel(folder, name):
    dist = name + '-1.0.dist-info'
    files = {
        name + '/__init__.py': 'VALUE = 42\n',
        dist + '/METADATA': f'Metadata-Version: 2.1\nName: {name.replace("_", "-")}\nVersion: 1.0\n',
        dist + '/WHEEL': 'Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n',
    }
    files[dist + '/RECORD'] = ''.join(f'{key},,\n' for key in files) + dist + '/RECORD,,\n'
    with zipfile.ZipFile(folder / (name + '-1.0-py3-none-any.whl'), 'w') as archive:
        for key, value in files.items():
            archive.writestr(key, value)


@unittest.skipUnless(os.name == 'nt', 'Windows native installer')
class InstallerDependencyRetry(unittest.TestCase):
    def test_missing_wheel_retry_preserves_existing_environment(self):
        with tempfile.TemporaryDirectory(prefix='bloons-dependency-retry-') as temp:
            root = Path(temp)
            install = root / 'install'
            app = install / 'resources/app'
            (app / 'autobtd6').mkdir(parents=True)
            requirements = app / 'requirements-installer.txt'
            check = app / 'autobtd6/runtime_check.py'
            check.write_text('import bloons_retry_base\nassert bloons_retry_base.VALUE == 42\n', encoding='utf-8')
            requirements.write_text('bloons-retry-base==1.0\n', encoding='utf-8')
            wheel(root, 'bloons_retry_base')
            binary = compile_harness(root, 'DependencyRetryChecks', SOURCE)
            env = {**{key: value for key, value in os.environ.items() if not key.upper().startswith('PIP_')},
                   'PATH': str(Path(sys._base_executable).parent) + os.pathsep + os.environ.get('PATH', ''),
                   'PIP_CONFIG_FILE': os.devnull,
                   'PIP_NO_INDEX': '1', 'PIP_FIND_LINKS': str(root),
                   'PIP_DISABLE_PIP_VERSION_CHECK': '1'}

            def run(expected):
                # Keep the parent alive until timeout cleanup: the production
                # dependency observer deliberately lets work survive its owner.
                with subprocess.Popen([str(binary), str(install)], env=env,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
                    try:
                        stdout, stderr = process.communicate(timeout=120)
                    except subprocess.TimeoutExpired:
                        if process.poll() is None:
                            subprocess.run([str(Path(os.environ['WINDIR']) / 'System32/taskkill.exe'),
                                            '/PID', str(process.pid), '/T', '/F'],
                                           capture_output=True, text=True, check=True, timeout=20)
                        process.communicate(timeout=20)
                        raise
                    self.assertEqual(process.returncode, expected, stdout + stderr)
                    return stdout + stderr

            run(0)
            venv = app / '.venv'
            stamp = venv / 'bloons-requirements.sha256'
            first_stamp = stamp.read_text()
            base = venv / 'Lib/site-packages/bloons_retry_base/__init__.py'
            base_bytes = base.read_bytes()
            base_mtime = base.stat().st_mtime_ns
            marker = venv / 'preserved-fixture.txt'
            marker.write_text('keep the existing environment', encoding='utf-8')
            config = app / 'config.json'
            config.write_text('{"fixture":true}', encoding='utf-8')

            requirements.write_text('bloons-retry-base==1.0\nbloons-retry-added==1.0\n', encoding='utf-8')
            check.write_text('import bloons_retry_base, bloons_retry_added\n'
                             'assert bloons_retry_base.VALUE == bloons_retry_added.VALUE == 42\n', encoding='utf-8')
            failed = run(1)
            self.assertIn('Python dependency installation failed', failed)
            self.assertIn('No matching distribution found for bloons-retry-added==1.0', failed)
            self.assertEqual(stamp.read_text(), first_stamp, 'Failure must not certify the changed requirements')
            self.assertEqual(base.read_bytes(), base_bytes)
            self.assertEqual(base.stat().st_mtime_ns, base_mtime)
            self.assertFalse((venv / 'Lib/site-packages/bloons_retry_added').exists())

            wheel(root, 'bloons_retry_added')
            run(0)
            # Native HashFile uses BitConverter's hyphenated byte spelling.
            self.assertEqual(bytes.fromhex(stamp.read_text().replace('-', '')),
                             hashlib.sha256(requirements.read_bytes()).digest())
            self.assertTrue((venv / 'Lib/site-packages/bloons_retry_added/__init__.py').exists())
            self.assertEqual(base.read_bytes(), base_bytes)
            self.assertEqual(base.stat().st_mtime_ns, base_mtime, 'Retry should retain the already healthy package')
            self.assertEqual(marker.read_text(), 'keep the existing environment')
            self.assertEqual(config.read_text(), '{"fixture":true}')
            self.assertEqual(list(app.glob('.venv.repair-*')), [], 'A compatible environment must not be replaced')
            reused = run(0)
            self.assertIn('Existing Python packages are ready.', reused)


SOURCE = r'''
using System;
using System.IO;
using System.Diagnostics;
internal static class DependencyRetryChecks {
 static int Main(string[] args) {
  if(InstallerProcessObserver.TryRun(args))return 0;
  int result=0;
  var options=new InstallerOptions(args[0],Path.Combine(args[0],"data"),"unused.exe",true,Guid.NewGuid().ToString("N"));
  try {
   using(var operations=new WindowsInstallerOperations(options)) {
    operations.LogAdded+=Console.WriteLine;
    operations.ProgressChanged+=p=>Console.WriteLine(p.Message);
    operations.ConfigurePython();
   }
  } catch(Exception error) { Console.Error.WriteLine(error.Message); result=1; }
  // Wait for only this fixture's observer after its owning operation is disposed.
  string self=Process.GetCurrentProcess().MainModule.FileName;
  foreach(var process in Process.GetProcesses())using(process){
   if(process.Id==Process.GetCurrentProcess().Id)continue;
   bool fixture=false;try{fixture=String.Equals(process.MainModule.FileName,self,StringComparison.OrdinalIgnoreCase);}catch{}
   if(fixture&&!process.WaitForExit(5000))throw new Exception("Fixture observer did not exit");
  }
  return result;
 }
}
'''


if __name__ == '__main__':
    unittest.main()
