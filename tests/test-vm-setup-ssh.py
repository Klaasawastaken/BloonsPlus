"""Setup transport regressions with mocked SSH; never touches a VM or keys."""
import base64
import importlib.util
from pathlib import Path
import subprocess
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('vm_setup', Path(__file__).resolve().parents[1] / 'vm/setup-vm.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)
setup.asb = SimpleNamespace(key_path=lambda: 'test-key')
INFO = {'port': 12345, 'user': 'user', 'keyDeployed': True, 'sshState': 4}


class SetupTransportTests(unittest.TestCase):
    def stage(self, response):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        source = Path(temporary.name) / 'BloonsPlusSetup.exe'
        source.write_bytes(b'MZinstaller-test')
        return source, patch.object(setup, 'ssh', side_effect=[r'C:\Users\user\AppData\Local\BloonsPlus\updates\unique', response])

    def test_update_uses_private_staging_and_checks_bytes(self):
        payload = b'MZinstaller-test'
        source, ssh = self.stage(json.dumps({'size': len(payload), 'sha256': hashlib.sha256(payload).hexdigest().upper()}))
        with ssh as remote, patch.object(setup, 'scp') as copy:
            result = setup.stage_guest_installer(INFO, source)
        self.assertEqual(result, r'C:\Users\user\AppData\Local\BloonsPlus\updates\unique\BloonsPlusSetup.exe')
        self.assertNotIn('Desktop', copy.call_args.args[2])
        self.assertIn('updates', copy.call_args.args[2])
        self.assertIn('Get-FileHash', remote.call_args.args[1])
        self.assertIn('-ErrorAction Stop', remote.call_args.args[1])

    def test_corrupted_or_incomplete_upload_cannot_launch(self):
        for response in ('{}', 'not JSON', json.dumps({'size': 1, 'sha256': 'wrong'})):
            with self.subTest(response=response):
                source, ssh = self.stage(response)
                with ssh, patch.object(setup, 'scp'), patch.object(setup, 'run_on_vm_desktop') as launch:
                    with self.assertRaisesRegex(RuntimeError, 'verify|verification'):
                        setup.stage_guest_installer(INFO, source)
                launch.assert_not_called()

    def test_upload_failure_is_not_retried_or_launched(self):
        source, ssh = self.stage('{}')
        with ssh as remote, patch.object(setup, 'scp', side_effect=RuntimeError('dest open: Failure')) as copy:
            with self.assertRaisesRegex(RuntimeError, 'dest open'):
                setup.stage_guest_installer(INFO, source)
        self.assertEqual(copy.call_count, 1)
        self.assertEqual(remote.call_count, 1)

    def test_powershell_quoted_paths_survive(self):
        command = '$p = "C:\\Folder with spaces\\a.txt"; Get-Content -LiteralPath $p; "OK"'
        with patch.object(setup.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='OK\n', stderr='')) as run:
            self.assertEqual(setup.ssh(INFO, command), 'OK')
        remote = run.call_args.args[0][-1]
        self.assertIn('-EncodedCommand ', remote)
        self.assertEqual(base64.b64decode(remote.split()[-1]).decode('utf-16le'), command)
        self.assertEqual(run.call_args.kwargs['timeout'], 60)

    def test_stdout_error_is_preserved(self):
        with patch.object(setup.subprocess, 'run', return_value=SimpleNamespace(returncode=1, stdout='Guest shell failed', stderr='')):
            with self.assertRaisesRegex(RuntimeError, 'Guest shell failed'):
                setup.ssh(INFO, 'Get-Process')

    def test_empty_error_includes_exit_code(self):
        with patch.object(setup.subprocess, 'run', return_value=SimpleNamespace(returncode=255, stdout='', stderr='')):
            with self.assertRaisesRegex(RuntimeError, '255'):
                setup.ssh(INFO, 'Get-Process')

    def test_timeout_is_actionable_without_retry(self):
        with patch.object(setup.subprocess, 'run', side_effect=subprocess.TimeoutExpired('ssh', 60)) as run:
            with self.assertRaisesRegex(RuntimeError, 'timed out.*60'):
                setup.ssh(INFO, 'Get-Process')
        self.assertEqual(run.call_count, 1)

    def test_key_rejection_keeps_specific_diagnostic(self):
        with patch.object(setup.subprocess, 'run', return_value=SimpleNamespace(returncode=255, stdout='', stderr='Permission denied (publickey).')):
            with self.assertRaisesRegex(RuntimeError, 'SSH key was rejected'):
                setup.ssh(INFO, 'Get-Process')

    def test_local_key_access_is_not_guest_rejection(self):
        with patch.object(setup.subprocess, 'run', return_value=SimpleNamespace(returncode=255, stdout='', stderr='Load key "test-key": Permission denied')):
            with self.assertRaisesRegex(RuntimeError, 'cannot read its App Sandbox SSH key'):
                setup.ssh(INFO, 'Get-Process')

    def test_long_install_can_use_explicit_timeout(self):
        with patch.object(setup.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='OK', stderr='')) as run:
            setup.ssh(INFO, 'Write-Output OK', timeout=600)
        self.assertEqual(run.call_args.kwargs['timeout'], 600)


if __name__ == '__main__':
    unittest.main()
