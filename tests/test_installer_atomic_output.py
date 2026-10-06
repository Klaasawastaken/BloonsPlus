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
    def test_shared_setup_and_startup_assets_are_required(self):
        required = set(builder.REQUIRED_RUNTIME_FILES)
        self.assertTrue({'lib/setup-session.js','lib/setup-controller.js','assets/app/setup-client.js',
            'assets/app/startup.js','assets/app/startup.css','assets/app/brand-tokens.css','assets/logo.svg'} <= required)

    def test_inventory_excludes_personal_routes_and_configuration(self):
        import json
        with tempfile.TemporaryDirectory() as folder:
            stage = Path(folder)
            app = stage / 'resources/app'
            (app / 'data/config').mkdir(parents=True)
            (app / 'route-library').mkdir()
            (app / 'package.json').write_text('{"version":"0.1.0"}')
            (app / 'server.js').write_text('app code')
            (app / 'data/config/calibration.json').write_text('user calibration')
            (app / 'route-library/custom.btd6').write_text('personal route')
            (app / 'autobtd6').mkdir()
            (app / 'autobtd6/userconfig.json').write_text('user choices')
            builder.write_inventory(stage)
            inventory = json.loads((stage / 'bloons-package.json').read_text())
            self.assertEqual({item['path'] for item in inventory['files']}, {'resources/app/package.json', 'resources/app/server.js'})
            self.assertEqual(len(inventory['fingerprint']), 64)
            (app / 'data/config/calibration.json').write_text('new calibration')
            builder.write_inventory(stage)
            self.assertEqual(json.loads((stage / 'bloons-package.json').read_text())['fingerprint'], inventory['fingerprint'])

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
            bootstrap.write_bytes(b'stub' + 'installer-result-'.encode('utf-16le'))
            if failure == 'capability':
                bootstrap.write_bytes(b'old-stub')
            with patch.object(builder, 'DIST', dist), patch.object(builder, 'OUTPUT', output), \
                 patch.object(builder, 'PACKAGE', payload), patch.object(builder.subprocess, 'run') as compile_call:
                if failure == 'capability':
                    with self.assertRaisesRegex(ValueError, 'capability'):
                        builder.build_installer()
                elif failure == 'copy':
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
                self.assertEqual(output.read_bytes(), b'stub' + 'installer-result-'.encode('utf-16le') + b'payloadBLPZIP01' + (7).to_bytes(8, 'little', signed=True))
                command = compile_call.call_args.args[0]
                self.assertTrue(any('presentation' in value and value.endswith('InstallerView.cs') for value in command))
                self.assertTrue(any(value.startswith('/resource:') and 'BloonsPlus.Engineer' in value for value in command))
            self.assertFalse(list(dist.glob('*.tmp')), 'Partial build must be cleaned up')

    def test_failed_copy_preserves_previous_installer(self):
        self.run_build('copy')

    def test_locked_output_preserves_previous_installer(self):
        self.run_build('replace')

    def test_success_publishes_complete_footer_and_payload(self):
        self.run_build()

    def test_incompatible_native_stub_preserves_previous_installer(self):
        self.run_build('capability')


if __name__ == '__main__':
    unittest.main()
