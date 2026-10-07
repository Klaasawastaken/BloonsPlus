"""Publication boundaries use synthetic content only."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publication_guard', ROOT / 'tools/check-publication.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class PublicationGuardTests(unittest.TestCase):
    def test_executable_private_paths_are_detected_without_disclosing_content(self):
        private_path = 'C:' + r'\Users\fixture-person\build\helper.pdb'
        for suffix in ('.exe', '.dll', '.pyd'):
            for encoding in ('utf-8', 'utf-16-le'):
                for padding in (b'\xff\x00', b'\xff'):
                    with self.subTest(suffix=suffix, encoding=encoding, padding=padding):
                        name = 'vm/helper' + suffix
                        findings = guard.inspect(name, padding + private_path.encode(encoding) + b'\x00\x00')
                        self.assertEqual(findings, [(name, 'personal Windows path')])
                        self.assertNotIn('fixture-person', str(findings))

    def test_executable_neutral_paths_and_relative_symbols_are_allowed(self):
        for value in ('C:' + r'\Users\Public\helper.pdb', 'helper.pdb'):
            for encoding in ('utf-8', 'utf-16-le'):
                self.assertEqual(guard.inspect('helper.exe', value.encode(encoding)), [])

    def test_transfer_manifest_is_rejected_at_any_depth_and_case(self):
        for name in ('.scp-list.txt', 'resources/app/.scp-list.txt', 'assets/.SCP-LIST.TXT'):
            with self.subTest(name=name):
                self.assertIn((name, 'private runtime file'), guard.inspect(name, b'server.js\n'))

    def test_account_scoped_medal_and_attempt_history_stays_private(self):
        for name in ('automation-progress.json', 'resources/app/AUTOMATION-PROGRESS.JSON'):
            with self.subTest(name=name):
                self.assertIn((name, 'private runtime file'), guard.inspect(name, b'{}'))

    def test_public_notices_and_runtime_source_are_not_transfer_metadata(self):
        for name in ('LICENSE.md', '.github/THIRD_PARTY.md', 'lib/automation.js'):
            with self.subTest(name=name):
                self.assertEqual(guard.inspect(name, b'public fixture'), [])


if __name__ == '__main__':
    unittest.main()
