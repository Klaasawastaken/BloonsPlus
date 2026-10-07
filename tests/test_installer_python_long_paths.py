"""Actual native ownership and offline pip; no installed app or game changes."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native installer')
class InstallerPythonLongPathsTests(unittest.TestCase):
    def test_extended_executable_keeps_process_identity(self):
        with tempfile.TemporaryDirectory(prefix='bloons-path-owner-') as folder:
            binary = compile_harness(folder, 'PathOwnerChecks', OWNER_SOURCE)
            result = subprocess.run([str(binary), folder], capture_output=True, text=True, timeout=35)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_native_python_setup_installs_long_wheel_and_reuses_it(self):
        # Keep the disposable venv under this owned directory. The extended
        # prefix is needed only to remove its long wheel entries afterwards.
        folder = Path(tempfile.mkdtemp(prefix='bloons-path-pip-')).resolve()
        try:
            install = folder / 'custom installation folder' / 'app'
            app = install / 'resources/app'
            (app / 'autobtd6').mkdir(parents=True)
            member = 'bloons_path_probe/' + '/'.join(['long_header_directory'] * 6) + '/header.h'
            self.assertGreater(len(str(app / '.venv/Lib/site-packages' / member)), 260)
            files = {
                'bloons_path_probe/__init__.py': 'VALUE = 42\n',
                member: 'synthetic header\n',
                'bloons_path_probe-1.0.dist-info/METADATA': 'Metadata-Version: 2.1\nName: bloons-path-probe\nVersion: 1.0\n',
                'bloons_path_probe-1.0.dist-info/WHEEL': 'Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n',
            }
            files['bloons_path_probe-1.0.dist-info/RECORD'] = ''.join(f'{name},,\n' for name in files) + 'bloons_path_probe-1.0.dist-info/RECORD,,\n'
            with zipfile.ZipFile(folder / 'bloons_path_probe-1.0-py3-none-any.whl', 'w') as archive:
                for name, data in files.items():
                    archive.writestr(name, data)
            (app / 'requirements-installer.txt').write_text('bloons-path-probe==1.0\n', encoding='utf-8')
            (app / 'autobtd6/runtime_check.py').write_text(
                'import sys\nfrom pathlib import Path\nimport bloons_path_probe\n'
                'assert bloons_path_probe.VALUE == 42\n'
                'assert not sys.executable.startswith("\\\\\\\\?\\\\")\n'
                f'p = Path(sys.prefix) / "Lib/site-packages" / {member!r}\n'
                'assert Path("\\\\\\\\?\\\\" + str(p)).read_text() == "synthetic header\\n"\n',
                encoding='utf-8')
            binary = compile_harness(folder, 'PythonPathChecks', PYTHON_SOURCE)
            result = subprocess.run([str(binary), str(install)], capture_output=True, text=True, timeout=150,
                                    env={**os.environ, 'PATH': str(Path(sys._base_executable).parent) + os.pathsep + os.environ.get('PATH', ''),
                                         'PIP_NO_INDEX': '1', 'PIP_FIND_LINKS': str(folder),
                                         'PIP_DISABLE_PIP_VERSION_CHECK': '1'})
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        finally:
            # Both absolute paths are checked before recursive cleanup. Use
            # PowerShell for the complete removal, including long filenames.
            if folder.parent != Path(tempfile.gettempdir()).resolve() or not folder.name.startswith('bloons-path-pip-'):
                raise AssertionError('Unexpected fixture cleanup target')
            subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command',
                            'Remove-Item -LiteralPath $env:BLOONS_PATH_FIXTURE -Recurse -Force -ErrorAction Stop'],
                           env={**os.environ, 'BLOONS_PATH_FIXTURE': '\\\\?\\' + str(folder)},
                           capture_output=True, text=True, check=True)


OWNER_SOURCE = r'''
using System;
using System.IO;
using System.Diagnostics;
using System.Threading;
internal static class PathOwnerChecks {
 static void Check(bool value,string why){if(!value)throw new Exception(why);}
 static void Main(string[] args){
  if(InstallerProcessObserver.TryRun(args))return;
  if(args.Length>0&&args[0]=="hold"){Thread.Sleep(2500);return;}
  string self=Process.GetCurrentProcess().MainModule.FileName, extended=@"\\?\"+self;
  Check(OwnedProcess.CanonicalExecutable(@"\\?\UNC\server\share\python.exe")==@"\\server\share\python.exe","UNC identity changed");
  Check(WindowsInstallerOperations.PythonPackageExecutable(@"\\server\share\python.exe")==@"\\?\UNC\server\share\python.exe","UNC package path changed");
  Check(WindowsInstallerOperations.PythonPackageExecutable(extended)==extended,"Extended package path duplicated its prefix");
  try{OwnedProcess.CanonicalExecutable(@"\\?\GLOBALROOT\Device\example");throw new Exception("Device namespace accepted");}catch(ArgumentException){}
  using(var current=Process.GetCurrentProcess()){
   Check(OwnedProcess.Matches(current.Id,current.StartTime.ToUniversalTime().Ticks,extended),"Extended spelling lost actual process identity");
   Check(!OwnedProcess.Matches(current.Id,current.StartTime.ToUniversalTime().Ticks+1,extended),"PID reuse accepted");
   Check(!OwnedProcess.Matches(current.Id,current.StartTime.ToUniversalTime().Ticks,extended+"-other"),"Different executable accepted");
  }
  using(var owner=new OwnedProcess(args[0]))using(var child=owner.Start(extended,"hold",args[0])){
   child.BeginRead(line=>{},line=>{});
   Check(new OwnedProcess(args[0]).Observe()=="running","Extended child ownership was lost");
   try{using(InstallerEngine.AcquireInstallLock(args[0])){}throw new Exception("Live dependency admitted another installer");}catch(InvalidOperationException){}
   Check(child.WaitForExit(10000),"Fixture failed to finish");child.FinishReading();owner.RecordTerminal(child.ExitCode);
   Check(new OwnedProcess(args[0]).Observe()=="idle","Finished fixture retained ownership");
  }
  // The observer exits naturally after the last owner handle closes. Wait for
  // only this fixture executable before TemporaryDirectory removes its image.
  foreach(var process in Process.GetProcesses())using(process){
   if(process.Id==Process.GetCurrentProcess().Id)continue;
   bool fixture=false;try{fixture=String.Equals(process.MainModule.FileName,self,StringComparison.OrdinalIgnoreCase);}catch{}
   if(fixture)Check(process.WaitForExit(5000),"Fixture observer did not exit");
  }
 }
}
'''

PYTHON_SOURCE = r'''
using System;
using System.IO;
internal static class PythonPathChecks {
 static void Main(string[] args){
  if(InstallerProcessObserver.TryRun(args))return;
  var options=new InstallerOptions(args[0],Path.Combine(args[0],"data"),"unused.exe",true,Guid.NewGuid().ToString("N"));
  using(var operations=new WindowsInstallerOperations(options)){
   operations.LogAdded+=Console.WriteLine;
   operations.ConfigurePython();
   string stamp=Path.Combine(args[0],"resources","app",".venv","bloons-requirements.sha256");
   if(!File.Exists(stamp))throw new Exception("Dependency verification did not complete");
   bool reused=false;operations.ProgressChanged+=p=>{if(p.Message=="Existing Python packages are ready.")reused=true;};
   operations.ConfigurePython();
   if(!reused)throw new Exception("Healthy environment was not reused");
   File.Delete(Path.Combine(args[0],"resources","app",".venv","Lib","site-packages","bloons_path_probe","__init__.py"));
   bool repaired=false;operations.LogAdded+=line=>{if(line.Contains("Successfully uninstalled bloons-path-probe"))repaired=true;};
   operations.ConfigurePython();
   if(!repaired)throw new Exception("Damaged package did not reach force-reinstall repair");
  }
 }
}
'''
