import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('installer_builder', ROOT / 'installer/make-installer.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class InstallerAtomicOutputTests(unittest.TestCase):
    def test_private_plan_ledger_is_not_packaged(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source'
            (source / '.superpowers/sdd/plan').mkdir(parents=True)
            (source / '.superpowers/sdd/plan/progress.md').write_text('private scratch')
            (source / 'app.js').write_text('public source')
            (source / 'setup-handoff').mkdir()
            (source / 'setup-handoff/session.json').write_text('private authentication key')
            (source / 'setup-sessions').mkdir()
            (source / 'setup-sessions/session.json').write_text('private checkpoint')
            target = Path(folder) / 'target'
            builder.copy_tree(source, target)
            self.assertTrue((target / 'app.js').exists())
            self.assertFalse((target / '.superpowers').exists())
            self.assertFalse((target / 'setup-handoff').exists())
            self.assertFalse((target / 'setup-sessions').exists())

    def run_build(self, failure=None):
        with tempfile.TemporaryDirectory() as folder:
            dist = Path(folder)
            output = dist / 'BloonsPlusSetup.exe'
            output.write_bytes(b'previous-good-installer')
            payload = dist / 'payload.zip'
            payload.write_bytes(b'payload')
            bootstrap = dist / 'BloonsPlusSetup.bootstrap.exe'
            bootstrap.write_bytes(b'stub')
            with patch.object(builder, 'DIST', dist), patch.object(builder, 'OUTPUT', output), \
                 patch.object(builder, 'PACKAGE', payload), patch.object(builder.subprocess, 'run'):
                if failure == 'copy':
                    with patch.object(builder.shutil, 'copyfileobj', side_effect=OSError('disk full')):
                        with self.assertRaises(OSError):
                            builder.build_installer()
                elif failure == 'replace':
                    with patch.object(builder.os, 'replace', side_effect=PermissionError('installer in use')):
                        with self.assertRaises(PermissionError):
                            builder.build_installer()
                else:
                    builder.build_installer()
            if failure:
                self.assertEqual(output.read_bytes(), b'previous-good-installer')
            else:
                self.assertEqual(output.read_bytes(), b'stubpayloadBLPZIP01' + (7).to_bytes(8, 'little', signed=True))
            self.assertFalse(list(dist.glob('*.tmp')), 'Partial build must be cleaned up')

    def test_failed_copy_preserves_previous_installer(self):
        self.run_build('copy')

    def test_locked_output_preserves_previous_installer(self):
        self.run_build('replace')

    def test_success_publishes_complete_footer_and_payload(self):
        self.run_build()


if __name__ == '__main__':
    unittest.main()
