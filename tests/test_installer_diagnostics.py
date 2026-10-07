"""Shared native diagnostics must remove values from structured log fields."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from native_installer_harness import compile_harness


@unittest.skipUnless(os.name == 'nt', 'Windows native compiler')
class InstallerDiagnosticsTests(unittest.TestCase):
    def test_structured_credentials_and_identities_are_removed_without_losing_run_details(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = compile_harness(folder, 'StructuredDiagnosticsChecks', r'''
using System;
internal static class StructuredDiagnosticsChecks {
 static void Check(bool value, string why) { if (!value) throw new Exception(why); }
 static int Main() {
  try {
   string[] inputs = {
    "{\"password\":\"fixture-secret\",\"round\":60,\"map\":\"skulltweak\"}",
    "{'secret': 'fixture-secret', 'round': 60, 'map': 'skulltweak'}",
    "{\"password\":\"fixture-prefix\\\"fixture-secret\",\"round\":60,\"map\":\"skulltweak\"}",
    "{'password': 'fixture-prefix\\'fixture-secret', 'round': 60, 'map': 'skulltweak'}",
    "{\"accountId\":\"fixture-secret\",\"round\":60,\"map\":\"skulltweak\"}",
    "{\"playerName\":\"fixture-secret\",\"round\":60,\"map\":\"skulltweak\"}",
    "{\"sessionId\":\"fixture-secret\",\"round\":60,\"map\":\"skulltweak\"}",
    "{\"access_token\":\"fixture-secret\",\"round\":60,\"map\":\"skulltweak\"}",
    "{\"X-Bloons-Setup-Key\":\"fixture-secret\",\"round\":60,\"map\":\"skulltweak\"}",
    "password=fixture-secret, round=60, map=skulltweak",
    "{\"password\":\"fixture-prefix\\\nfixture-secret\",\"round\":60,\"map\":\"skulltweak\"}",
    "{\"password\":\"fixture-prefix\\\r\nfixture-secret\",\"round\":60,\"map\":\"skulltweak\"}",
    "{'password': 'fixture-prefix\\\nfixture-secret', 'round':60, 'map':'skulltweak'}",
    "{'password': 'fixture-prefix\\\r\nfixture-secret', 'round':60, 'map':'skulltweak'}",
    "{\"authorization\":\"Bearer fixture-prefix\\\"fixture-secret\",\"round\":60,\"map\":\"skulltweak\"}",
    "{'authorization':'Basic fixture-prefix\\'fixture-secret','round':60,'map':'skulltweak'}"
   };
   foreach (string input in inputs) {
    string redacted = InstallerDiagnostics.Redact(input);
    Check(!redacted.Contains("fixture-secret"), "Structured sensitive value survived shared export");
    Check(!redacted.Contains("fixture-prefix"), "Escaped string leaked a credential prefix");
    Check(redacted.Contains("60") && redacted.Contains("skulltweak"), "Safe gameplay context was erased");
    Check(InstallerDiagnostics.Redact(redacted) == redacted, "Redaction changed on a second export pass");
   }
   Check(InstallerDiagnostics.Redact(null) == "", "Missing details are not empty");
   foreach (string input in new[] {
    "{\"password\":\"fixture-prefix fixture-secret",
    "{'password': 'fixture-prefix fixture-secret",
    "{\"password\":\"fixture-prefix\\"
   }) {
    string redacted = InstallerDiagnostics.Redact(input);
    Check(!redacted.Contains("fixture-secret") && !redacted.Contains("fixture-prefix"), "Truncated credential survived shared export");
   }
   return 0;
  } catch (Exception error) { Console.Error.WriteLine(error.Message); return 1; }
 }
}
''')
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
