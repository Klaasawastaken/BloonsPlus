"""Exercise real Windows file ownership without installing or stopping apps."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallerOwnershipTests(unittest.TestCase):
    def test_ownership_precedes_result_and_file_mutations(self):
        source = (ROOT / 'installer/native/InstallerEngine.cs').read_text(encoding='utf-8')
        method = source[source.index('    private InstallerResult Run('):]
        self.assertIn('AcquireInstallLock(options.InstallRoot)', method)
        self.assertLess(method.index('AcquireInstallLock(options.InstallRoot)'), method.index('WriteResult("RUNNING")'))
        self.assertIn('if (installLock != null) WriteResult(receipt);', method,
                      'A duplicate installer must not overwrite the owner receipt')
        self.assertIn('if (installLock != null) installLock.Dispose();', method)
        self.assertIn('else WriteAttemptResult("ERROR: " + error.Message);', method)

    @unittest.skipUnless(os.name == 'nt', 'Windows .NET compiler')
    def test_real_cross_process_lock_and_release(self):
        compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
        with tempfile.TemporaryDirectory() as folder:
            harness = Path(folder) / 'OwnershipTests.cs'
            harness.write_text(r'''
using System;
using System.IO;
using System.Diagnostics;
internal static class OwnershipTests {
    [STAThread]
    static void Main(string[] args) {
        if (args.Length == 1) {
            try { using (InstallerEngine.AcquireInstallLock(args[0])) {} }
            catch (InvalidOperationException) { Console.WriteLine("busy"); return; }
            throw new Exception("Second process acquired the active installation");
        }
        string root = Path.Combine(Path.GetTempPath(), "Bloons-owner-" + Guid.NewGuid().ToString("N"));
        try {
            string token = Guid.NewGuid().ToString("N");
            string receipt = InstallerEngine.AttemptResultPath(root, token);
            if (receipt != Path.Combine(root, "installer-result-" + token + ".txt"))
                throw new Exception("Wrong attempt receipt");
            if (InstallerEngine.AttemptResultPath(root, null) != null)
                throw new Exception("Legacy installer must not invent an attempt");
            try { InstallerEngine.AttemptResultPath(root, "../outside"); throw new Exception("Unsafe receipt accepted"); }
            catch (ArgumentException) {}
            using (InstallerEngine.AcquireInstallLock(root)) {
                File.WriteAllText(Path.Combine(root, "receipt"), "RUNNING");
                var options = new InstallerOptions(root, root, "unused.exe", true, token);
                File.WriteAllText(options.ResultPath, "RUNNING");
                var duplicate = new InstallerEngine(options, new WindowsInstallerOperations(options));
                var result = duplicate.RunAsync(System.Threading.CancellationToken.None).GetAwaiter().GetResult();
                if (result.ExitCode != 1) throw new Exception("Duplicate did not return failure");
                if (!File.ReadAllText(receipt).StartsWith("ERROR: Another Bloons+ installer"))
                    throw new Exception("Duplicate did not report its own failure");
                if (File.ReadAllText(options.ResultPath) != "RUNNING")
                    throw new Exception("Duplicate overwrote owner receipt");
                var start = new ProcessStartInfo(Process.GetCurrentProcess().MainModule.FileName,
                    "\"" + root + "\"") {UseShellExecute=false, CreateNoWindow=true, RedirectStandardOutput=true};
                using (var child = Process.Start(start)) {
                    string output = child.StandardOutput.ReadToEnd();
                    if (!child.WaitForExit(10000) || child.ExitCode != 0 || output.Trim() != "busy")
                        throw new Exception("Cross-process ownership failed");
                }
                if (File.ReadAllText(Path.Combine(root, "receipt")) != "RUNNING")
                    throw new Exception("Receipt changed");
            }
            using (InstallerEngine.AcquireInstallLock(root)) {} // retry after release
            using (InstallerEngine.AcquireInstallLock(root))
            using (InstallerEngine.AcquireInstallLock(Path.Combine(root, "other"))) {} // independent root
            Console.WriteLine("Real installation lock rejects duplicates, releases, and scopes to its root.");
        } finally { Directory.Delete(root, true); }
    }
}
''', encoding='utf-8')
            binary = Path(folder) / 'ownership.exe'
            result = subprocess.run([str(compiler), '/nologo', '/target:exe', '/main:OwnershipTests',
                '/reference:System.Windows.Forms.dll', '/reference:System.Drawing.dll',
                '/reference:System.IO.Compression.dll', '/reference:Microsoft.CSharp.dll',
                '/reference:System.Web.Extensions.dll', '/out:' + str(binary),
                str(ROOT / 'installer/installer-bootstrap.cs'), *map(str, sorted((ROOT / 'installer/native').glob('*.cs'))), *map(str, sorted((ROOT / 'installer/presentation').glob('*.cs'))), str(harness)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == '__main__':
    unittest.main()
