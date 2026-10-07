"""Check installer guards using owned fixture executables, never gameplay."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native process observation')
class InstallerActivePythonTests(unittest.TestCase):
    def test_installed_python_blocks_changes_without_being_closed(self):
        with tempfile.TemporaryDirectory(prefix='bloons-active-python-') as folder:
            binary = compile_harness(folder, 'InstalledPythonChecks', SOURCE)
            run = subprocess.run([str(binary), str(Path(folder) / 'fixture')],
                                 capture_output=True, text=True, timeout=40)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


SOURCE = r'''
using System;
using System.IO;
using System.Diagnostics;
using System.Threading;
internal static class InstalledPythonChecks {
    static void Check(bool value,string why) {if(!value)throw new Exception(why);}
    static string Self {get{return Process.GetCurrentProcess().MainModule.FileName;}}
    static void Main(string[] args) {
        try {Run(args);}catch(Exception error){Console.Error.WriteLine(error.ToString());Environment.ExitCode=1;}
    }
    static void Run(string[] args) {
        if(args.Length==2&&args[0]=="hold") {File.WriteAllText(args[1],"ready");Thread.Sleep(20000);return;}
        string fixture=Path.GetFullPath(args[0]),root=Path.Combine(fixture,"app");
        Directory.CreateDirectory(root);
        string[] paths={
            Path.Combine(root,"resources","app",".venv","Scripts","python.exe"),
            Path.Combine(root,"resources","app",".venv","Scripts","pythonw.exe"),
            Path.Combine(root,"resources","app","python","python.exe"),
            Path.Combine(root,"resources","app","python","pythonw.exe"),
            Path.Combine(root+"-other","resources","app",".venv","Scripts","python.exe"),
            Path.Combine(fixture,"unrelated","python.exe")
        };
        for(int index=0;index<paths.Length;index++) {
            string executable=paths[index],ready=Path.Combine(fixture,"ready-"+index);
            Directory.CreateDirectory(Path.GetDirectoryName(executable));File.Copy(Self,executable);
            using(var child=Process.Start(new ProcessStartInfo(executable,"hold \""+ready+"\"") {UseShellExecute=false,CreateNoWindow=true})) {
                try {
                    var timer=Stopwatch.StartNew();while(!File.Exists(ready)&&!child.HasExited&&timer.ElapsedMilliseconds<5000)Thread.Sleep(20);
                    Check(File.Exists(ready)&&!child.HasExited,"Own fixture did not become ready");
                    long created=child.StartTime.ToUniversalTime().Ticks;
                    Check(OwnedProcess.Matches(child.Id,created,executable),"Own fixture executable identity differs");
                    bool blocked=false;
                    var options=new InstallerOptions(root,Path.Combine(fixture,"data"),Self,true,null);
                    using(var operations=new WindowsInstallerOperations(options)) {
                        try {operations.CloseInstalledControllers();}
                        catch(InvalidOperationException){blocked=true;}
                    }
                    Check(blocked==(index<4),index<4?"Installed Python work was ignored":"Unrelated Python work blocked installation");
                    Check(OwnedProcess.Matches(child.Id,created,executable),"Installer terminated the Python fixture");
                }finally {
                    if(!child.HasExited&&String.Equals(child.MainModule.FileName,executable,StringComparison.OrdinalIgnoreCase)) {child.Kill();child.WaitForExit(5000);}
                }
            }
        }
        CheckLatePython(fixture,root);
        Console.WriteLine("Installed Python guards passed; only owned fixtures were stopped.");
    }
    static Process StartFixture(string executable,string ready) {
        Directory.CreateDirectory(Path.GetDirectoryName(executable));File.Copy(Self,executable,true);
        var child=Process.Start(new ProcessStartInfo(executable,"hold \""+ready+"\"") {UseShellExecute=false,CreateNoWindow=true});
        try {
            var timer=Stopwatch.StartNew();while(!File.Exists(ready)&&!child.HasExited&&timer.ElapsedMilliseconds<5000)Thread.Sleep(20);
            Check(File.Exists(ready)&&!child.HasExited,"Own late fixture did not become ready");
            return child;
        }catch {StopFixture(child,executable);throw;}
    }
    static void StopFixture(Process child,string executable) {
        if(child==null)return;
        try {if(!child.HasExited&&String.Equals(child.MainModule.FileName,executable,StringComparison.OrdinalIgnoreCase)) {child.Kill();child.WaitForExit(5000);}}
        finally {child.Dispose();}
    }
    static void CheckLatePython(string fixture,string root) {
        string node=Path.Combine(root,"resources","app","node.exe");
        string python=Path.Combine(root,"resources","app",".venv","Scripts","python.exe");
        var controller=StartFixture(node,Path.Combine(fixture,"late-node-ready"));
        LatePythonOperations operations=null;
        try {
            var options=new InstallerOptions(root,Path.Combine(fixture,"data"),Self,true,null);
            operations=new LatePythonOperations(options,python,Path.Combine(fixture,"late-python-ready"));
            bool blocked=false;
            try {operations.CloseInstalledControllers();}catch(InvalidOperationException){blocked=true;}
            Check(operations.Child!=null,"Idle-status fixture was not exercised");
            Check(blocked,"Python started during the idle check was ignored");
            Check(controller.HasExited,"Owned idle controller did not close");
            Check(OwnedProcess.Matches(operations.Child.Id,operations.Created,python),"Installer terminated late Python work");
        }finally {
            if(operations!=null) {StopFixture(operations.Child,python);operations.Dispose();}
            StopFixture(controller,node);
        }
    }
    sealed class LatePythonOperations : WindowsInstallerOperations {
        readonly string executable,ready;
        internal Process Child;internal long Created;
        internal LatePythonOperations(InstallerOptions options,string executable,string ready):base(options) {this.executable=executable;this.ready=ready;}
        internal override string ReadInstalledControllerStatus() {
            Child=StartFixture(executable,ready);Created=Child.StartTime.ToUniversalTime().Ticks;
            return "{\"running\":false}";
        }
    }
}
'''
