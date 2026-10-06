import os
import subprocess
import tempfile
import unittest
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native compiler')
class InstallerProcessOwnerTests(unittest.TestCase):
    def test_live_child_and_unknown_identity_block_new_owner(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'ProcessOwnerChecks', r'''
using System;
using System.IO;
using System.Diagnostics;
using System.Threading;
internal static class ProcessOwnerChecks {
    static void Check(bool value, string why) { if (!value) throw new Exception(why); }
    static void Main(string[] args) {
        if (args.Length > 0 && args[0] == "child") { Thread.Sleep(30000); return; }
        if (args.Length > 0 && args[0] == "worker") {
            var journal = new OwnedProcess(args[1]);
            string self = Process.GetCurrentProcess().MainModule.FileName;
            journal.RecordIntent(self, "dependency");
            using (var orphan = Process.Start(new ProcessStartInfo(self, "child") {UseShellExecute=false,CreateNoWindow=true})) {
                journal.Attach(orphan); File.WriteAllText(Path.Combine(args[1], "child.pid"), orphan.Id.ToString());
            }
            return; // Installer parent exits; its dependency keeps running.
        }
        string root = Path.Combine(Path.GetTempPath(), "Bloons-child-" + Guid.NewGuid().ToString("N"));
        Process child = null;
        try {
            var owner = new OwnedProcess(root);
            string executable = Process.GetCurrentProcess().MainModule.FileName;
            owner.RecordIntent(executable, "dependency");
            try { using (InstallerEngine.AcquireInstallLock(root)) {} throw new Exception("Unknown start accepted"); }
            catch (InvalidOperationException) {}
            owner.RecordTerminal(-1); // This fixture intent never started a process.
            using (var worker = Process.Start(new ProcessStartInfo(executable, "worker \"" + root + "\"") {UseShellExecute=false,CreateNoWindow=true})) {
                Check(worker.WaitForExit(10000) && worker.ExitCode == 0, "Fixture parent did not finish");
            }
            child = Process.GetProcessById(Int32.Parse(File.ReadAllText(Path.Combine(root, "child.pid"))));
            var reopened = new OwnedProcess(root);
            Check(reopened.Observe() == "running", "Live child not observed");
            try { using (InstallerEngine.AcquireInstallLock(root)) {} throw new Exception("Concurrent child accepted"); }
            catch (InvalidOperationException) {}
            Check(!OwnedProcess.Matches(child.Id, child.StartTime.ToUniversalTime().Ticks + 1, executable), "PID reuse matched");
            child.Kill(); child.WaitForExit();
            Check(reopened.Observe() == "unknown", "Unobserved terminal state guessed as complete");
            owner.RecordTerminal(-1); // This test deliberately terminated and waited for its own fixture child.
            using (InstallerEngine.AcquireInstallLock(root)) {}
            var priorBoot = new OwnedProcess(root, () => "prior-boot");
            priorBoot.RecordIntent(executable, "microsoft_runtime");
            Check(new OwnedProcess(root, () => "same-unavailable-boot").Observe() == "idle", "Known reboot did not release old work");
            Check(new OwnedProcess(root, () => null).Observe() == "unknown", "Unavailable boot identity guessed idle");
        } finally {
            if (child != null) { try { if (!child.HasExited) {child.Kill();child.WaitForExit();} } catch {} child.Dispose(); }
            if (Directory.Exists(root)) Directory.Delete(root, true);
        }
    }
}
''')
            run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=40)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
