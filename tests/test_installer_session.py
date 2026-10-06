import os
import subprocess
import tempfile
import unittest
from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native compiler')
class InstallerSessionTests(unittest.TestCase):
    def test_completed_milestones_survive_rechecks_and_resume_without_claiming_readiness(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'MilestoneChecks', r'''
using System;
using System.IO;
internal static class MilestoneChecks {
 static void Check(bool value,string message){if(!value)throw new Exception(message);}
 static void Main(string[] args){
  string root=Path.Combine(Path.GetTempPath(),"Bloons-milestones-"+Guid.NewGuid().ToString("N"));
  try {
   bool environment=args[0]=="environment";
   var session=InstallSession.LoadOrCreate(root,"install",environment);
   string id=session.Snapshot.SessionId;
   Check(session.TryCommand(id,session.Snapshot.Sequence,"start"),"Start failed");
   session.ObserveMilestone(InstallerStage.Finish);
   int earned=session.Snapshot.CompletedWeight;
   Check(earned==(environment?57:95),"Initial completed milestones were invented");
   if(environment){session.ObserveEnvironmentWeight(80);earned=88;}
   session.Observe("recovering","runtime","Checking completed work again",null,null,null);
   session.ObserveMilestone(InstallerStage.Prepare);
   Check(session.Snapshot.CompletedWeight==earned,"Previously completed milestones regressed on local recheck");
   if(environment){
    session.ObserveEnvironmentWeight(0);
    Check(session.Snapshot.CompletedWeight==earned,"Environment recheck erased completed milestones");
    session.ObserveEnvironmentWeight(100);earned=95;
    Check(session.Snapshot.CompletedWeight==earned,"Environment consumed final-validation weight");
    session.ObserveEnvironmentWeight(20);
    Check(session.Snapshot.CompletedWeight==earned,"Out-of-order environment receipt regressed progress");
   }
   Check(session.Snapshot.Indeterminate && !session.Snapshot.StageNumerator.HasValue,
    "Retained milestones fabricated a measured current-task percentage");
   Check(!session.Snapshot.AppValidated && !session.Snapshot.EnvironmentValidated,"Progress fabricated readiness");
   try {session.Complete();throw new Exception("Unvalidated completion accepted");}
   catch(InvalidOperationException){}
   var resumed=InstallSession.LoadOrCreate(root,"resume",environment);
   Check(resumed.Snapshot.SessionId==id && resumed.Snapshot.CompletedWeight==earned,"Resume lost earned milestones");
   resumed.ObserveMilestone(InstallerStage.Files);
   Check(resumed.Snapshot.CompletedWeight==earned,"Resume restarted the overall counter");
   resumed.Observe("validating","runtime","Freshly verified",null,null,null);
   resumed.MarkValidated(true,environment);resumed.Complete();
   var next=InstallSession.LoadOrCreate(root,"update",environment);
   Check(next.Snapshot.SessionId!=id && next.Snapshot.CompletedWeight==0,"New operation inherited prior progress");
  }catch(Exception error){Console.Error.WriteLine(error.Message);Environment.ExitCode=1;}
  finally{if(Directory.Exists(root))Directory.Delete(root,true);}
 }
}
''')
            for mode in ('local', 'environment'):
                with self.subTest(mode=mode):
                    run = subprocess.run([str(binary), mode], capture_output=True, text=True, timeout=30)
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

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
            Check(resumed.Snapshot.CompletedWeight == 30, "Full setup must reserve environment and finalization work");
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
