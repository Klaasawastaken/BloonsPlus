"""Publication boundaries use synthetic content only."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publication_guard', ROOT / 'tools/check-publication.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class PublicationGuardTests(unittest.TestCase):
    def test_transfer_manifest_is_rejected_at_any_depth_and_case(self):
        for name in ('.scp-list.txt', 'resources/app/.scp-list.txt', 'assets/.SCP-LIST.TXT'):
            with self.subTest(name=name):
                self.assertIn((name, 'private runtime file'), guard.inspect(name, b'server.js\n'))

    def test_public_notices_and_runtime_source_are_not_transfer_metadata(self):
        for name in ('LICENSE.md', '.github/THIRD_PARTY.md', 'lib/automation.js'):
            with self.subTest(name=name):
                self.assertEqual(guard.inspect(name, b'public fixture'), [])


if __name__ == '__main__':
    unittest.main()
