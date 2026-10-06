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
    public FakeOperations(InstallerOptions options) : base(options) {}
    public override void CloseInstalledControllers() { Calls.Add("controllers"); }
    public override void ReadEmbeddedPackage(string path) { Calls.Add("package"); }
    public override void BackupExistingData(string path) { Calls.Add("backup"); }
    public override void InstallAppFiles(string path) { Calls.Add("files"); SetStatus("Files ready", InstallerStage.Files, 100); }
    public override void RestoreExistingData(string path) { Calls.Add("restore"); }
    public override void EnsureVisualCppRuntime() { Calls.Add("cpp"); }
    public override void ConfigurePython() {
        Calls.Add("python"); SetDetail("Dependency probe");
        if (FailPython) throw new IOException("probe failed");
    }
    public override void CreateStartMenuShortcut() { Calls.Add("shortcut"); }
    public override void KeepInstallerCopy() { Calls.Add("copy"); }
    public override void SaveSetupIntent() { Calls.Add("intent"); }
    public override void LaunchApp() { Calls.Add("launch"); }
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
            Check(String.Join(",", operations.Calls) == "controllers,package,backup,files,restore,cpp,python,shortcut,copy,intent,launch", "Operation order changed");
            Check(events.Count > 2 && events[0].Stage == InstallerStage.Prepare && events[events.Count-1].Percent == 100, "Missing window-free progress");
            Check(events[0].Percent == null, "Earlier event mutated");
            Check(details.Contains("Dependency probe"), "Missing detail event");
            Check(File.ReadAllText(options.ResultPath) == "OK" && File.ReadAllText(options.AttemptResultPath) == "OK", "Wrong receipts");
            operations = new FakeOperations(options) { FailPython = true };
            engine = new InstallerEngine(options, operations);
            engine.ProgressChanged += events.Add;
            result = engine.RunAsync(CancellationToken.None).GetAwaiter().GetResult();
            Check(!result.LocalReady && result.ExitCode == 1 && result.Receipt == "ERROR: probe failed", "Failure swallowed");
            Check(!operations.Calls.Contains("launch") && operations.Calls[operations.Calls.Count-1] == "restore", "Failure launched app or skipped restore");
            Check(events[events.Count-1].Failed, "Failure not observable");
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
