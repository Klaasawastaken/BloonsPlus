"""Exercise installer progress without installing software or opening the UI."""
import os
import re
from pathlib import Path
import subprocess
import tempfile
import unittest


class InstallerProgressChecks(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows .NET compiler')
    def test_healthy_runtime_without_old_stamp_is_reused(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / 'installer/installer-bootstrap.cs').read_text(encoding='utf-8')
        start = source.index('        string probe = Quote(')
        end = source.index('            SetStatus("Existing Python packages are ready.', start)
        condition = re.search(r'if \((.*?)\)\s*\{', source[start:end], re.S)[1]
        compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
        with tempfile.TemporaryDirectory() as folder:
            harness = Path(folder) / 'ReuseChecks.cs'
            harness.write_text(r'''
using System;
using System.IO;
using System.Collections.Generic;
internal static class ReuseChecks {
    static List<string> calls = new List<string>();
    static string rejected = null;
    static bool ProcessSucceeds(string executable, string args, int timeout = 30000) {
        calls.Add(args); return args != rejected;
    }
    static bool Ready() {
        string stamp = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        string requirementsHash = "no stamp required";
        string venvPython = "unused", installedCheck = "versions", probe = "imports";
        return ''' + condition + r''';
    }
    static void Main() {
        if (!Ready() || calls.Count != 3) throw new Exception("Healthy runtime was not reused without a stamp");
        foreach (string failure in new[] {"versions", "-m pip check", "imports"}) {
            calls.Clear(); rejected = failure;
            if (Ready()) throw new Exception("Unhealthy runtime reused: " + failure);
        }
        Console.WriteLine("Actual runtime reuse condition accepts healthy unstamped environments and rejects failed probes.");
    }
}
''', encoding='utf-8')
            binary = Path(folder) / 'reuse-checks.exe'
            result = subprocess.run([str(compiler), '/nologo', '/out:' + str(binary), str(harness)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            run = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    @unittest.skipUnless(os.name == 'nt', 'Windows .NET compiler')
    def test_named_steps_unknown_work_and_failure(self):
        root = Path(__file__).resolve().parents[1]
        compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
        with tempfile.TemporaryDirectory() as folder:
            harness = Path(folder) / 'ProgressChecks.cs'
            harness.write_text(r'''
using System;
internal static class ProgressChecks {
    static void Check(bool value) { if (!value) throw new Exception("Progress assertion failed"); }
    static void Main() {
        var state = new InstallerProgress();
        state.Update(InstallerStage.Files, 43);
        Check(state.Caption == "Install step 2 of 5 · App files · 43%");
        Check(state.Value == 430 && !state.IsBusy);
        state.Update(InstallerStage.Python, null);
        Check(state.Caption == "Install step 4 of 5 · Python packages · Working…");
        Check(state.IsBusy && state.Percent == null);
        state.Fail();
        Check(!state.IsBusy && state.Caption == "Setup paused · Install step 4 of 5 · Python packages");
        state.Update(InstallerStage.Prepare, null);
        Check(!state.Failed && state.IsBusy);
        state.Update(InstallerStage.CppRuntime, 50, "Download");
        Check(state.Caption.EndsWith("Download 50%"));
        state.Update(InstallerStage.Finish, 100);
        Check(!state.IsBusy && state.Value == 1000);
        foreach (int bad in new[] {-1, 101}) {
            bool rejected = false;
            try { state.Update(InstallerStage.Files, bad); } catch (ArgumentOutOfRangeException) { rejected = true; }
            Check(rejected);
        }
        bool invalidStage = false;
        try { state.Update((InstallerStage)6, null); } catch (ArgumentOutOfRangeException) { invalidStage = true; }
        Check(invalidStage);
        Console.WriteLine("Named installer steps, measured progress, unknown work, failure and retry passed.");
    }
}
''', encoding='utf-8')
            binary = Path(folder) / 'progress-checks.exe'
            compile_result = subprocess.run([
                str(compiler), '/nologo', '/target:exe', '/main:ProgressChecks',
                '/reference:System.Windows.Forms.dll', '/reference:System.Drawing.dll',
                '/reference:System.IO.Compression.dll', '/reference:Microsoft.CSharp.dll',
                '/reference:System.Web.Extensions.dll', '/out:' + str(binary),
                str(root / 'installer/installer-bootstrap.cs'), str(harness)
            ], capture_output=True, text=True)
            self.assertEqual(compile_result.returncode, 0, compile_result.stdout + compile_result.stderr)
            run = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == '__main__':
    unittest.main()
