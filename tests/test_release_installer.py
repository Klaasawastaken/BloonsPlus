import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('setup_release', Path(__file__).resolve().parents[1] / 'vm/setup-vm.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class ReleaseInstallerTests(unittest.TestCase):
    def test_noninstall_actions_and_explicit_installer_do_not_resolve_release(self):
        with patch.object(setup, 'default_installer', side_effect=AssertionError('Unexpected installer lookup')):
            self.assertIsNone(setup.parse_args(['steam-install']).installer)
            self.assertIsNone(setup.parse_args(['launch-app']).installer)
            self.assertEqual(setup.parse_args(['provision', '--installer', 'explicit.exe']).installer, Path('explicit.exe'))

    def test_release_precedes_generic_and_incomplete_release_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            generic = root / 'dist/BloonsPlusSetup.exe'
            released = root / 'dist/preview87/BloonsPlusSetup.exe'
            released.parent.mkdir(parents=True)
            (root / 'docs').mkdir()
            generic.write_bytes(b'old')
            released.write_bytes(b'released')
            metadata = root / 'docs/release.json'
            metadata.write_text(json.dumps({'tag_name': 'v0.1.0-preview.87', 'assets': [
                {'name': 'BloonsPlusSetup.exe', 'size': 8}]}))
            with patch.object(setup, 'ROOT', root):
                self.assertEqual(setup.default_installer(), released)
                released.write_bytes(b'truncated')
                with self.assertRaisesRegex(RuntimeError, 'incomplete|size'):
                    setup.default_installer()
                released.unlink()
                self.assertEqual(setup.default_installer(), generic)

    def test_invalid_metadata_keeps_standard_layout(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            generic = root / 'dist/BloonsPlusSetup.exe'
            generic.parent.mkdir()
            generic.write_bytes(b'build')
            (root / 'docs').mkdir()
            metadata = root / 'docs/release.json'
            with patch.object(setup, 'ROOT', root):
                for data in ('not JSON', '[]', json.dumps({'tag_name': 'v0.1.0-preview.../../outside'}),
                             json.dumps({'tag_name': 'v0.1.0-preview.87', 'assets': [{'name': '../outside.exe', 'size': 8}]})):
                    metadata.write_text(data)
                    self.assertEqual(setup.default_installer(), generic)


if __name__ == '__main__':
    unittest.main()
