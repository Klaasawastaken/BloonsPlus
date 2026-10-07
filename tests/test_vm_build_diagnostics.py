import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('vm_build_setup', ROOT / 'vm/setup-vm.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class FailedBuildClient:
    def __init__(self, folder, diagnostic):
        self.folder = Path(folder)
        self.diagnostic = diagnostic
        self.created = []

    def create(self, **config):
        name = config['name']
        self.created.append(name)
        with (self.folder / 'appsandbox.log').open('a', encoding='utf-8') as output:
            output.write(self.diagnostic(name) + '\n')
        return 202, {}

    def wait_online(self, name, timeout):
        raise RuntimeError('VM vanished during creation: ' + name)


class VmBuildDiagnosticsTests(unittest.TestCase):
    def invoke(self, client):
        with patch.object(setup, 'asb', type('Sdk', (), {
            '__file__': str(client.folder / 'headless-api/asb.py')
        })), patch.object(setup.time, 'sleep'), patch.object(setup, 'log'):
            return setup.create_vm(client, Path('unused.iso'))

    def test_observed_boot_failure_is_reported_without_building_three_images(self):
        with tempfile.TemporaryDirectory() as folder:
            client = FailedBuildClient(folder, lambda name:
                'Error creating VM "%s": Failed to install boot files (bcdboot exit code 183)' % name)
            with self.assertRaisesRegex(RuntimeError, 'bcdboot exit code 183'):
                self.invoke(client)
            self.assertEqual(client.created, ['BloonsPlusVM2'])

    def test_old_failure_for_same_name_does_not_classify_new_attempt(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / 'appsandbox.log'
            log.write_text('Error creating VM "BloonsPlusVM2": Failed to install boot files (bcdboot exit code 183)\n', encoding='utf-8')
            client = FailedBuildClient(folder, lambda name: 'Unknown build failure for ' + name)
            with self.assertRaisesRegex(RuntimeError, 'vanished'):
                self.invoke(client)
            self.assertEqual(client.created, setup.VM_NAMES)

    def test_other_vm_failure_does_not_classify_requested_vm(self):
        with tempfile.TemporaryDirectory() as folder:
            client = FailedBuildClient(folder, lambda name:
                'Error creating VM "UnrelatedVM": Failed to install boot files (bcdboot exit code 183)')
            with self.assertRaisesRegex(RuntimeError, 'vanished'):
                self.invoke(client)
            self.assertEqual(client.created, setup.VM_NAMES)

    def test_log_replacement_retains_unknown_failure_without_echoing_private_text(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / 'appsandbox.log'
            log.write_text('x' * 10000, encoding='utf-8')
            client = FailedBuildClient(folder, lambda name: 'private fixture password must not be reported')
            original = client.create
            def replace_log(**config):
                log.write_text('', encoding='utf-8')
                return original(**config)
            client.create = replace_log
            with self.assertRaisesRegex(RuntimeError, 'vanished') as caught:
                self.invoke(client)
            self.assertNotIn('password', str(caught.exception))
            self.assertEqual(client.created, setup.VM_NAMES)


if __name__ == '__main__':
    unittest.main()
