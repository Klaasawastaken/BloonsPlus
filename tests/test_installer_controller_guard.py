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
internal static class GuardTests {
    static void Check(bool value) { if (!value) throw new Exception("Guard assertion failed"); }
    static void Main() {
        foreach (string json in new[] { "Not found", "null", "{}", "[]", "{\"running\":true}", "{\"running\":0}", "{\"running\":\"false\"}" })
            Check(!InstallerForm.IsIdleResponse(json));
        Check(InstallerForm.IsIdleResponse("{\"running\":false}"));
        string root = @"C:\Apps\Bloons+";
        Check(InstallerForm.IsOwnedAppProcess("node", root + @"\resources\app\node.exe", root));
        Check(InstallerForm.IsOwnedAppProcess("Bloons+", root + @"\Bloons+.exe", root));
        Check(!InstallerForm.IsOwnedAppProcess("node", @"C:\Other\node.exe", root));
        Check(!InstallerForm.IsOwnedAppProcess("node", root + @"-other\resources\app\node.exe", root));
        Check(!InstallerForm.IsOwnedAppProcess("BloonsTD6", root + @"\BloonsTD6.exe", root));
        Check(!InstallerForm.IsOwnedAppProcess("python", root + @"\resources\app\.venv\Scripts\python.exe", root));
        Console.WriteLine("Installer idle/ownership guards passed; no processes controlled.");
    }
}
''', encoding='utf-8')
            binary = Path(folder) / 'guard-tests.exe'
            result = subprocess.run([str(compiler), '/nologo', '/target:exe', '/main:GuardTests',
                '/reference:System.Windows.Forms.dll', '/reference:System.Drawing.dll',
                '/reference:System.IO.Compression.dll', '/reference:Microsoft.CSharp.dll',
                '/reference:System.Web.Extensions.dll', '/out:' + str(binary),
                str(root / 'installer/installer-bootstrap.cs'), str(test)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            run = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == '__main__':
    unittest.main()
