import os
import subprocess
import tempfile
import unittest
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native compiler')
class InstallerProcessTreeTests(unittest.TestCase):
    def test_direct_exit_does_not_release_live_descendant(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'TreeChecks', r'''
using System;
using System.IO;
using System.Diagnostics;
using System.Threading;
internal static class TreeChecks {
    static void Check(bool value, string why) { if (!value) throw new Exception(why); }
    static void Main(string[] args) {
        if (args.Length > 0 && args[0] == "hold") { Thread.Sleep(30000); return; }
        if (args.Length > 0 && args[0] == "owner") {
            using (var recorded = new OwnedProcess(args[1]))
            using (var surviving = recorded.Start(Process.GetCurrentProcess().MainModule.FileName, "hold", args[1])) {
                surviving.BeginRead(line => {}, line => {});
                File.WriteAllText(Path.Combine(args[1], "surviving.pid"), surviving.Id.ToString());
            }
            return; // Closing observer handles must not terminate dependency work.
        }
        if (args.Length > 0 && args[0] == "parent") {
            using (var descendant = Process.Start(new ProcessStartInfo(Process.GetCurrentProcess().MainModule.FileName, "hold") {UseShellExecute=false,CreateNoWindow=true}))
                File.WriteAllText(Path.Combine(args[1], "descendant.pid"), descendant.Id.ToString());
            return;
        }
        string root = Path.Combine(Path.GetTempPath(), "Bloons-tree-" + Guid.NewGuid().ToString("N"));
        Process descendantProcess = null;
        try {
            var owner = new OwnedProcess(root);
            using (var child = owner.Start(Process.GetCurrentProcess().MainModule.FileName, "parent \"" + root + "\"", root)) {
                child.BeginRead(line => {}, line => {});
                Check(child.WaitForExit(10000), "Parent did not finish");
                descendantProcess = Process.GetProcessById(Int32.Parse(File.ReadAllText(Path.Combine(root, "descendant.pid"))));
                Check(new OwnedProcess(root).Observe() == "running", "Live descendant was lost");
                try { owner.RecordTerminal(child.ExitCode); throw new Exception("Live descendant released ownership"); }
                catch (InvalidOperationException) {}
                try { using (InstallerEngine.AcquireInstallLock(root)) {} throw new Exception("Second installer admitted"); }
                catch (InvalidOperationException) {}
                descendantProcess.Kill(); descendantProcess.WaitForExit();
                owner.RecordTerminal(child.ExitCode);
                using (InstallerEngine.AcquireInstallLock(root)) {}
            }
            using (var exited = Process.Start(new ProcessStartInfo(Process.GetCurrentProcess().MainModule.FileName, "owner \"" + root + "\"") {UseShellExecute=false,CreateNoWindow=true}))
                Check(exited.WaitForExit(10000) && exited.ExitCode == 0, "Owner fixture did not exit");
            descendantProcess.Dispose();
            descendantProcess = Process.GetProcessById(Int32.Parse(File.ReadAllText(Path.Combine(root, "surviving.pid"))));
            Check(new OwnedProcess(root).Observe() == "running", "Closing installer hid or killed its job");
            try { using (InstallerEngine.AcquireInstallLock(root)) {} throw new Exception("Reopened installer ignored surviving job"); }
            catch (InvalidOperationException) {}
            descendantProcess.Kill(); descendantProcess.WaitForExit();
            Thread.Sleep(100); // Allow the kernel to release this exited fixture job.
            Check(new OwnedProcess(root).Observe() == "unknown", "Unobserved exit was guessed successful");
        } finally {
            if (descendantProcess != null) { try { if (!descendantProcess.HasExited) {descendantProcess.Kill();descendantProcess.WaitForExit();} } catch {} descendantProcess.Dispose(); }
            if (Directory.Exists(root)) Directory.Delete(root, true);
        }
    }
}
''')
            run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=40)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
