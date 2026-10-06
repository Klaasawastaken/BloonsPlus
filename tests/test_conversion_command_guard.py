"""Read-only checks of source omissions and exact guarded recording bytes."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]

class ConversionCommandGuardTests(unittest.TestCase):
    def test_catalog_matches_audited_omissions_and_preserves_new_candidates(self):
        result = subprocess.run([sys.executable, '-X', 'utf8', 'tools/audit-btd6bot-conversions.py'],
                                cwd=ROOT, text=True, capture_output=True, check=True)
        findings = {row['file']: row for row in json.loads(result.stdout)['findings']}
        guard = json.loads((ROOT/'data/catalogs/route-selection-guard.json').read_text())
        targeted = 0
        for filename, entry in guard.items():
            row = findings[filename]
            self.assertTrue(row['missingSelectionCommands'] or row['missingTargetSpecialCommands'])
            self.assertEqual(entry['hash'], hashlib.sha256((ROOT/'autobtd6/playthroughs'/filename).read_bytes()).hexdigest())
            if row['missingTargetSpecialCommands']:
                targeted += 1
                self.assertIn('targeted special', entry['reason'])
        self.assertGreater(targeted, 0)
        candidates = [row for name,row in findings.items() if '#special-target-preserved' in name]
        self.assertEqual(len(candidates), 14)
        for row in candidates:
            self.assertFalse(row['missingTargetSpecialCommands'])
            self.assertFalse(row['missingSelectionCommands'])
            self.assertNotIn(row['file'], guard)

if __name__ == '__main__': unittest.main()
