"""Exercise the native installation engine without a form or real installation."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallerEngineTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows .NET Framework compiler')
    def test_window_free_engine_events_order_failure_and_receipts(self):
        compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
        with tempfile.TemporaryDirectory() as folder:
            harness = Path(folder) / 'EngineChecks.cs'
            harness.write_text(r'''
using System;
using System.IO;
using System.Collections.Generic;
using System.Threading;
internal sealed class FakeOperations : WindowsInstallerOperations {
    public readonly List<string> Calls = new List<string>();
    public bool FailPython;
    public bool EnvironmentReady = true;
    public bool EnvironmentFailed;
    public Action OnCpp;
    public FakeOperations(InstallerOptions options) : base(options) {}
    public override string GetBootIdentity() { return "fixture-boot"; }
    public override void CloseInstalledControllers() { Calls.Add("controllers"); }
    public override void RecoverAppFiles() { Calls.Add("recovery"); }
    public override void ReadEmbeddedPackage(string path) { Calls.Add("package"); }
    public override void BackupExistingData(string path) { Calls.Add("backup"); }
    public override void InstallAppFiles(string path) { Calls.Add("files"); SetStatus("Files ready", InstallerStage.Files, 100); }
    public override void RestoreExistingData(string path) { Calls.Add("restore"); }
    public override void EnsureVisualCppRuntime() { Calls.Add("cpp"); if (OnCpp != null) OnCpp(); }
    public override void ConfigurePython() {
        Calls.Add("python"); SetDetail("Dependency probe");
        if (FailPython) throw new IOException("probe failed");
    }
    public override void CreateStartMenuShortcut() { Calls.Add("shortcut"); }
    public override void CreateDesktopShortcut() { Calls.Add("desktop"); }
    public override void KeepInstallerCopy() { Calls.Add("copy"); }
    public override void SaveSetupIntent() { Calls.Add("intent"); }
    public override void LaunchApp() { Calls.Add("launch"); }
    public override SetupEnvironmentResult ConfigureEnvironment(string id) {
        Calls.Add("environment");
        if (EnvironmentFailed) return SetupEnvironmentResult.FromSnapshot(new Dictionary<string,object> {
            {"phase","failed"},{"step","provision"},{"status","Setup needs attention"},{"humanAction","retry"},
            {"error",new Dictionary<string,object>{{"component","provision"},{"message","Fixture isolated receipt failure"}}}
        });
        return new SetupEnvironmentResult { Ready = EnvironmentReady, HumanAction = EnvironmentReady ? null : "steam_sign_in", Status = EnvironmentReady ? "Environment ready" : "Sign in to Steam in the VM" };
    }
}
internal static class EngineChecks {
    static void Check(bool value, string message) { if (!value) throw new Exception(message); }
    static void Main() {
        string root = Path.Combine(Path.GetTempPath(), "Bloons-engine-" + Guid.NewGuid().ToString("N"));
        try {
            var options = new InstallerOptions(Path.Combine(root, "app"), root, "unused.exe", true, Guid.NewGuid().ToString("N"));
            var operations = new FakeOperations(options);
            var engine = new InstallerEngine(options, operations);
            Check(!Directory.Exists(root), "Construction mutated disk");
            var events = new List<InstallerProgress>(); var details = new List<string>();
            engine.ProgressChanged += events.Add; engine.DetailAdded += details.Add;
            var result = engine.RunAsync(CancellationToken.None).GetAwaiter().GetResult();
            Check(result.LocalReady && result.ExitCode == 0 && result.Receipt == "OK", "Wrong success");
            Check(!result.EnvironmentReady && !result.EnvironmentDeferred, "Silent install invented VM readiness");
            Check(String.Join(",", operations.Calls) == "controllers,recovery,package,backup,files,restore,copy,cpp,python,shortcut,intent,launch", "File recovery must precede backup/restore; observer must precede dependencies");
            Check(events.Count > 2 && events[0].Stage == InstallerStage.Prepare && events[events.Count-1].Percent == 100, "Missing window-free progress");
            Check(events[0].Percent == null, "Earlier event mutated");
            Check(details.Contains("Dependency probe"), "Missing detail event");
            Check(File.ReadAllText(options.ResultPath) == "OK" && File.ReadAllText(options.AttemptResultPath) == "OK", "Wrong receipts");
            var fullOptions = new InstallerOptions(Path.Combine(root,"full"),root,"unused.exe",false,null);
            var fullOperations = new FakeOperations(fullOptions) { EnvironmentReady = false };
            var fullEngine = new InstallerEngine(fullOptions,fullOperations);
            var pending = fullEngine.RunAsync(CancellationToken.None).GetAwaiter().GetResult();
            Check(pending.LocalReady && !pending.EnvironmentReady && pending.HumanAction == "steam_sign_in", "Human action invented environment readiness");
            Check(!fullOperations.Calls.Contains("launch"), "Dashboard launched before environment acceptance");
            string pendingJournal = Path.Combine(fullOptions.InstallRoot, ".bloons-setup", "app-file-transaction.json");
            File.WriteAllText(pendingJournal, "unfinished files");
            bool refusedResume = false;
            try { fullEngine.ResumeEnvironmentAsync(CancellationToken.None).GetAwaiter().GetResult(); }
            catch (InvalidOperationException) { refusedResume = true; }
            Check(refusedResume && fullOperations.Calls.FindAll(x=>x=="environment").Count == 1,
                "Cached local readiness bypassed pending file recovery");
            File.Delete(pendingJournal);
            typeof(InstallerEngine).GetMethod("ObserveEnvironment",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance).Invoke(fullEngine,new object[]{new Dictionary<string,object>{
                {"phase","downloading"},{"status","Downloading Windows"},{"step","iso"},{"numerator",42L},{"denominator",100L},{"scope","Download"}
            }});
            Check(fullEngine.CurrentSnapshot.StageNumerator==42&&fullEngine.CurrentSnapshot.StageDenominator==100,"Measured environment progress was discarded");
            typeof(InstallerEngine).GetMethod("ObserveEnvironment",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance).Invoke(fullEngine,new object[]{new Dictionary<string,object>{
                {"phase","restart_required"},{"status","Restart Windows"},{"step","vmp"}
            }});
            Check(!String.IsNullOrEmpty(fullEngine.CurrentSnapshot.RestartBootIdentity),"Remote restart did not retain host boot identity");
            typeof(InstallerEngine).GetField("session",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance).GetValue(fullEngine).GetType().GetMethod("Observe").Invoke(
                typeof(InstallerEngine).GetField("session",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance).GetValue(fullEngine),new object[]{"validating","environment","Fixture resume after restart proof",null,null,null});
            fullOperations.EnvironmentReady = true;
            var resumed = fullEngine.ResumeEnvironmentAsync(CancellationToken.None).GetAwaiter().GetResult();
            Check(resumed.EnvironmentReady && fullEngine.CurrentSnapshot.Phase == "complete", "Fresh environment acceptance missing");
            Check(fullOperations.Calls.FindAll(x=>x=="files").Count == 1, "Resume reinstalled validated local files");
            var brokenOptions = new InstallerOptions(Path.Combine(root,"broken-vm"),root,"unused.exe",false,null);
            var brokenEngine = new InstallerEngine(brokenOptions,new FakeOperations(brokenOptions){EnvironmentFailed=true});
            var brokenDetails = new List<string>();brokenEngine.DetailAdded += brokenDetails.Add;
            var brokenResult = brokenEngine.RunAsync(CancellationToken.None).GetAwaiter().GetResult();
            Check(brokenEngine.CurrentSnapshot.Phase=="failed", "VM failure became a generic validating checkpoint");
            Check(brokenResult.Error.Contains("isolated receipt failure"), "Structured VM error was discarded");
            Check(brokenDetails.Exists(line=>line.Contains("isolated receipt failure")), "VM error missing from installer details");
            Check(File.ReadAllText(brokenOptions.LogPath).Contains("isolated receipt failure"), "VM error missing from installer log");
            operations = new FakeOperations(options) { FailPython = true };
            engine = new InstallerEngine(options, operations);
            engine.ProgressChanged += events.Add;
            result = engine.RunAsync(CancellationToken.None).GetAwaiter().GetResult();
            Check(!result.LocalReady && result.ExitCode == 1 && result.Receipt == "ERROR: probe failed", "Failure swallowed");
            Check(!operations.Calls.Contains("launch") && operations.Calls[operations.Calls.Count-1] == "restore", "Failure launched app or skipped restore");
            Check(events[events.Count-1].Failed, "Failure not observable");
            Check(engine.CurrentSnapshot.Phase == "failed", "Failure checkpoint missing");
            var rebootOptions = new InstallerOptions(Path.Combine(root, "reboot"), root, "unused.exe", true, null);
            operations = new FakeOperations(rebootOptions) { OnCpp = () => { throw new InstallerRestartRequiredException("Restart required"); } };
            engine = new InstallerEngine(rebootOptions, operations);
            result = engine.RunAsync(CancellationToken.None).GetAwaiter().GetResult();
            Check(result.RestartRequired && result.ExitCode == 3010 && engine.CurrentSnapshot.Phase == "restart_required", "Reboot falsely completed or lost");
            Check(!operations.Calls.Contains("python") && !operations.Calls.Contains("launch"), "Reboot continued mutation");
            rebootOptions.DesktopShortcut=true;
            engine.CommandEnvironmentAsync("restart_later",CancellationToken.None).GetAwaiter().GetResult();
            Check(engine.CurrentSnapshot.RestartDeferred,"Installer Later choice was not persisted");
            operations = new FakeOperations(rebootOptions); engine = new InstallerEngine(rebootOptions, operations);
            result = engine.RunAsync(CancellationToken.None).GetAwaiter().GetResult();
            Check(result.RestartRequired && operations.Calls.Count == 0, "Retry bypassed the required reboot");
            var cancelOptions = new InstallerOptions(Path.Combine(root, "cancel-after-boundary"), root, "unused.exe", true, null);
            var cancelAtBoundary = new CancellationTokenSource();
            operations = new FakeOperations(cancelOptions) { OnCpp = cancelAtBoundary.Cancel };
            engine = new InstallerEngine(cancelOptions, operations);
            result = engine.RunAsync(cancelAtBoundary.Token).GetAwaiter().GetResult();
            Check(!result.LocalReady && engine.CurrentSnapshot.Phase == "cancelled", "Cancellation not checkpointed");
            Check(!operations.Calls.Contains("python") && !operations.Calls.Contains("launch"), "Cancellation scheduled another component");
            File.WriteAllText(options.ResultPath, "RUNNING");
            using (InstallerEngine.AcquireInstallLock(options.InstallRoot)) {
                operations = new FakeOperations(options); engine = new InstallerEngine(options, operations);
                result = engine.RunAsync(CancellationToken.None).GetAwaiter().GetResult();
                Check(result.ExitCode == 1 && operations.Calls.Count == 0, "Duplicate performed operations");
                Check(File.ReadAllText(options.ResultPath) == "RUNNING", "Duplicate overwrote owner receipt");
                Check(File.ReadAllText(options.AttemptResultPath).StartsWith("ERROR: Another Bloons+ installer"), "Duplicate did not report attempt failure");
            }
            string cancelled = Path.Combine(root, "cancelled");
            options = new InstallerOptions(cancelled, Path.Combine(cancelled, "state"), "unused.exe", true, null);
            engine = new InstallerEngine(options, new FakeOperations(options));
            var cancellation = new CancellationTokenSource(); cancellation.Cancel();
            try { engine.RunAsync(cancellation.Token).GetAwaiter().GetResult(); throw new Exception("Cancelled task ran"); }
            catch (OperationCanceledException) {}
            Check(!Directory.Exists(cancelled), "Cancelled operation mutated disk");
        } finally { if (Directory.Exists(root)) Directory.Delete(root, true); }
    }
}
''', encoding='utf-8')
            binary = Path(folder) / 'engine-checks.exe'
            sources = sorted((ROOT / 'installer/native').glob('*.cs'))
            result = subprocess.run([str(compiler), '/nologo', '/target:exe',
                '/main:EngineChecks', '/reference:System.IO.Compression.dll',
                '/reference:Microsoft.CSharp.dll', '/reference:System.Web.Extensions.dll',
                '/out:' + str(binary), *(str(p) for p in sources), str(harness)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == '__main__':
    unittest.main()
