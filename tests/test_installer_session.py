import os
import subprocess
import tempfile
import unittest
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native compiler')
class InstallerSessionTests(unittest.TestCase):
    def test_checkpoint_identity_transitions_weights_and_restart_persistence(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'SessionChecks', r'''
using System;
using System.IO;
internal static class SessionChecks {
    static void Check(bool value, string why) { if (!value) throw new Exception(why); }
    static void Main(string[] args) {
        string root = Path.Combine(Path.GetTempPath(), "Bloons-session-" + Guid.NewGuid().ToString("N"));
        try {
            var session = InstallSession.LoadOrCreate(root, "install", true);
            string identity = session.Snapshot.SessionId; long sequence = session.Snapshot.Sequence;
            Check(!session.TryCommand("stale", sequence, "start"), "Stale session accepted");
            Check(!session.TryCommand(identity, sequence-1, "start"), "Stale sequence accepted");
            Check(session.TryCommand(identity, sequence, "start"), "Start rejected");
            Check(!session.TryCommand(identity, session.Snapshot.Sequence, "start"), "Duplicate start accepted");
            session.Observe("downloading", "files", "Downloading", 25, 100, "Download");
            Check(!session.Snapshot.Indeterminate && session.Snapshot.StageNumerator == 25, "Measured bytes lost");
            Check(session.Snapshot.PlanWeight == 100, "Plan changed");
            session.Observe("installing_dependency", "python", "Installing", null, null, null);
            Check(session.Snapshot.Indeterminate, "Unknown work invented progress");
            try { session.Complete(); throw new Exception("Unvalidated complete accepted"); }
            catch (InvalidOperationException) {}
            session.RequireRestart("Restart Windows to finish dependency setup.");
            Check(session.TryCommand(identity, session.Snapshot.Sequence, "restart_later"), "Later rejected");
            var resumed = InstallSession.LoadOrCreate(root, "resume", true);
            Check(resumed.Snapshot.SessionId == identity && resumed.Snapshot.Phase == "restart_required", "Restart checkpoint lost");
            Check(resumed.Snapshot.RestartDeferred, "Later choice lost");
            Check(resumed.Snapshot.PlanWeight == 100, "Resume denominator changed");
            string backup = Path.Combine(Path.GetTempPath(), "BloonsPlus-data-" + Guid.NewGuid().ToString("N"));
            resumed.RetainBackup(backup);
            try { resumed.RetainBackup(Path.Combine(root, "outside")); throw new Exception("Foreign cleanup path accepted"); }
            catch (ArgumentException) {}
            resumed.ObserveMilestone(InstallerStage.Python);
            Check(resumed.Snapshot.CompletedWeight == 50, "Verified stage milestones missing");
            Check(resumed.TryCommand(identity, resumed.Snapshot.Sequence, "resume"), "Resume rejected");
            resumed.Observe("validating", "runtime", "Verifying", null, null, null);
            resumed.MarkValidated(true, false);
            try { resumed.Complete(); throw new Exception("Missing environment accepted"); }
            catch (InvalidOperationException) {}
            resumed.MarkValidated(true, true); resumed.Complete();
            Check(resumed.Snapshot.Phase == "complete", "Validated completion missing");
            var completed = InstallSession.LoadOrCreate(root, "repair", false);
            Check(completed.Snapshot.SessionId != identity, "Completed session reused for mutation");
            Check(Directory.GetFiles(root, "*.tmp", SearchOption.AllDirectories).Length == 0, "Temporary checkpoint left");
            try { completed.Observe("invented", "bad", "Bad", null, null, null); throw new Exception("Invalid phase accepted"); }
            catch (ArgumentException) {}
        } finally { if (Directory.Exists(root)) Directory.Delete(root, true); }
    }
}
''')
            run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
