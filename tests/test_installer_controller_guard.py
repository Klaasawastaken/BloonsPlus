"""Compile and exercise pure installer guards; never run installer/UI/process stops."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class InstallerControllerGuard(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows .NET Framework compiler')
    def test_idle_status_and_exact_process_ownership(self):
        root = Path(__file__).resolve().parents[1]
        compiler = Path(os.environ['WINDIR']) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
        with tempfile.TemporaryDirectory() as folder:
            test = Path(folder) / 'GuardTests.cs'
            test.write_text(r'''
using System;
using System.IO;
internal static class GuardTests {
    static void Check(bool value) { if (!value) throw new Exception("Guard assertion failed"); }
    static void Main() {
        foreach (string json in new[] { "Not found", "null", "{}", "[]", "{\"running\":true}", "{\"running\":0}", "{\"running\":\"false\"}" })
            Check(!WindowsInstallerOperations.IsIdleResponse(json));
        Check(WindowsInstallerOperations.IsIdleResponse("{\"running\":false}"));
        string root = @"C:\Apps\Bloons+";
        Check(WindowsInstallerOperations.IsOwnedAppProcess("node", root + @"\resources\app\node.exe", root));
        Check(WindowsInstallerOperations.IsOwnedAppProcess("Bloons+", root + @"\Bloons+.exe", root));
        Check(!WindowsInstallerOperations.IsOwnedAppProcess("node", @"C:\Other\node.exe", root));
        Check(!WindowsInstallerOperations.IsOwnedAppProcess("node", root + @"-other\resources\app\node.exe", root));
        Check(!WindowsInstallerOperations.IsOwnedAppProcess("BloonsTD6", root + @"\BloonsTD6.exe", root));
        Check(!WindowsInstallerOperations.IsOwnedAppProcess("python", root + @"\resources\app\.venv\Scripts\python.exe", root));
        using (var output = new MemoryStream()) {
            WindowsInstallerOperations.CopyRuntimeDownload(new MemoryStream(new byte[] {77, 90, 1, 2}), output, 4, null);
            Check(output.Length == 4);
        }
        foreach (var bytes in new[] {new byte[0], new byte[] {77}, new byte[] {60, 104, 116, 109, 108}}) {
            bool rejected = false;
            try { WindowsInstallerOperations.CopyRuntimeDownload(new MemoryStream(bytes), new MemoryStream(), bytes.Length, null); }
            catch (InvalidDataException) { rejected = true; }
            Check(rejected);
        }
        foreach (long length in new long[] {8, 128L * 1024 * 1024 + 1}) {
            bool rejected = false;
            try { WindowsInstallerOperations.CopyRuntimeDownload(new MemoryStream(new byte[] {77, 90, 1, 2}), new MemoryStream(), length, null); }
            catch (InvalidDataException) { rejected = true; }
            Check(rejected);
        }
        using (var output = new MemoryStream()) {
            WindowsInstallerOperations.CopyRuntimeDownload(new MemoryStream(new byte[] {77, 90, 1, 2}), output, -1, null);
            Check(output.Length == 4);
        }
        Console.WriteLine("Installer guards and runtime payload checks passed; no installer launched.");
    }
}
''', encoding='utf-8')
            binary = Path(folder) / 'guard-tests.exe'
            result = subprocess.run([str(compiler), '/nologo', '/target:exe', '/main:GuardTests',
                '/reference:System.Windows.Forms.dll', '/reference:System.Drawing.dll',
                '/reference:System.IO.Compression.dll', '/reference:Microsoft.CSharp.dll',
                '/reference:System.Web.Extensions.dll', '/out:' + str(binary),
                str(root / 'installer/installer-bootstrap.cs'), *map(str, sorted((root / 'installer/native').glob('*.cs'))), *map(str, sorted((root / 'installer/presentation').glob('*.cs'))), str(test)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            run = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == '__main__':
    unittest.main()
