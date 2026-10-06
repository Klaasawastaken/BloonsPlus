"""Mocked VM ownership checks; no VM, scheduled tasks or game input."""
import hashlib
import base64
import ctypes
from ctypes import wintypes
import importlib.util
import os
import json
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from native_installer_harness import compile_harness

spec = importlib.util.spec_from_file_location('setup_owned', Path(__file__).resolve().parents[1] / 'vm/setup-vm.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class GuestInstallerOwnershipTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows native observer')
    def test_guest_probe_uses_real_native_dependency_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            observer = compile_harness(folder, 'ReceiptObserver', 'internal static class ReceiptObserver { static void Main() {} }')
            shutil.copy2(observer, root / 'BloonsPlusSetup.exe')
            lock = root / '.bloons-install.lock'
            lock.write_bytes(b'')
            journal = root / '.bloons-setup/owned-process.json'
            journal.parent.mkdir()
            def remote(info, command):
                command = command.replace("catch { 'UNKNOWN' }", "catch { Write-Error $_; 'UNKNOWN' }")
                result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand',
                    base64.b64encode(command.encode('utf-16le')).decode()], capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr)
                return result.stdout.strip()
            with patch.object(setup, 'GUEST_INSTALL_LOCK', str(lock)), patch.object(setup, 'ssh', side_effect=remote):
                journal.write_text(json.dumps({'Executable': str(observer), 'TerminalObserved': True, 'ExitCode': 0}))
                self.assertFalse(setup.guest_install_busy({}))
                journal.write_text(json.dumps({'Executable': str(observer), 'TerminalObserved': False}))
                with self.assertRaisesRegex(RuntimeError, 'ownership'):
                    setup.guest_install_busy({})

    def test_attempt_receipt_is_unique_and_rejects_path_input(self):
        token = '0123456789abcdef0123456789abcdef'
        with patch.object(setup, 'guest_install_busy', return_value=False), patch.object(setup, 'ssh', return_value='OK') as remote:
            setup.wait_for_guest_install({}, attempt=token)
            self.assertIn('installer-result-' + token + '.txt', remote.call_args.args[1])
        with patch.object(setup, 'ssh') as remote:
            for invalid in ['../result', '', 'Z' * 32]:
                with self.assertRaises(ValueError):
                    setup.wait_for_guest_install({}, attempt=invalid)
            remote.assert_not_called()

    def test_legacy_receipts_are_not_used_for_new_install_requests(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'setup.exe'
            source.write_bytes(b'MZlegacy-installer')
            self.assertFalse(setup.supports_attempt_receipts(source))
            source.write_bytes(b'MZ' + 'installer-result-'.encode('utf-16le'))
            self.assertTrue(setup.supports_attempt_receipts(source))

    def test_task_cleanup_targets_only_this_attempt(self):
        token = 'a' * 32
        with patch.object(setup, 'ssh') as remote:
            setup.remove_guest_install_task({}, token)
            command = remote.call_args.args[1]
            self.assertIn('/delete', command)
            self.assertIn('BloonsPlusSetup-' + token, command)
            self.assertNotIn('/end', command)
            self.assertNotIn('Stop-Process', command)
        with patch.object(setup, 'ssh') as remote:
            with self.assertRaises(ValueError):
                setup.remove_guest_install_task({}, '*')
            remote.assert_not_called()

    @unittest.skipUnless(os.name == 'nt', 'Windows file sharing and PowerShell')
    def test_real_powershell_probe_matches_windows_ownership(self):
        def remote(info, command):
            encoded = base64.b64encode(command.encode('utf-16le')).decode('ascii')
            result = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout
        create = ctypes.windll.kernel32.CreateFileW
        create.restype = wintypes.HANDLE
        create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                           wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        close = ctypes.windll.kernel32.CloseHandle
        close.argtypes = [wintypes.HANDLE]
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / '.bloons-install.lock'
            handle = create(str(target), 0xc0000000, 0, None, 4, 0x80, None)
            self.assertNotEqual(handle, ctypes.c_void_p(-1).value)
            try:
                with patch.object(setup, 'GUEST_INSTALL_LOCK', str(target)), patch.object(setup, 'ssh', side_effect=remote):
                    self.assertTrue(setup.guest_install_busy({}))
            finally:
                close(handle)
            with patch.object(setup, 'GUEST_INSTALL_LOCK', str(target)), patch.object(setup, 'ssh', side_effect=remote):
                self.assertFalse(setup.guest_install_busy({}))
                target.unlink()
                self.assertFalse(setup.guest_install_busy({}))

    def test_probe_distinguishes_busy_free_and_unknown(self):
        for result, expected in [('BUSY', True), ('FREE', False)]:
            with patch.object(setup, 'ssh', return_value=result) as remote:
                self.assertEqual(setup.guest_install_busy({}), expected)
                command = remote.call_args.args[1]
                self.assertIn('.bloons-install.lock', command)
                self.assertIn('[IO.FileShare]::None', command)
                self.assertIn('32', command)
                self.assertIn('33', command)
                self.assertNotIn('Get-Process', command)
                self.assertIn('OwnedProcess', command, 'A released parent lock cannot hide surviving dependency work')
        with patch.object(setup, 'ssh', return_value='permission error'):
            with self.assertRaisesRegex(RuntimeError, 'ownership'):
                setup.guest_install_busy({})

    def test_terminal_receipt_waits_for_owner_release(self):
        for receipt in ['OK', 'ERROR: failed']:
            with patch.object(setup, 'guest_install_busy', side_effect=[True, False]) as busy, \
                    patch.object(setup, 'ssh', return_value=receipt), patch.object(setup.time, 'sleep') as sleep:
                if receipt == 'OK':
                    setup.wait_for_guest_install({}, timeout=30)
                else:
                    with self.assertRaisesRegex(RuntimeError, 'failed'):
                        setup.wait_for_guest_install({}, timeout=30)
                self.assertEqual(busy.call_count, 2)
                sleep.assert_called_once_with(5)

    def test_probe_errors_do_not_claim_install_completion(self):
        with patch.object(setup, 'guest_install_busy', side_effect=RuntimeError('ownership unknown')), \
                patch.object(setup, 'ssh', return_value='OK'):
            with self.assertRaisesRegex(RuntimeError, 'ownership unknown'):
                setup.wait_for_guest_install({})

    def test_restart_receipt_reports_action_after_owner_release(self):
        with patch.object(setup, 'guest_install_busy', side_effect=[True, False]), \
                patch.object(setup, 'ssh', return_value='RESTART_REQUIRED: dependency'), patch.object(setup.time, 'sleep'):
            with self.assertRaisesRegex(RuntimeError, 'Restart Windows inside the VM'):
                setup.wait_for_guest_install({}, timeout=30)

    def test_matching_installer_requires_content_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'setup.exe'
            source.write_bytes(b'new installer' + 'installer-result-'.encode('utf-16le'))
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            for result, expected in [(digest.upper(), True), ('OLD', False), ('MISSING', False)]:
                with patch.object(setup, 'ssh', return_value=result) as remote:
                    self.assertEqual(setup.guest_installer_matches({}, source), expected)
                    self.assertIn('Get-FileHash', remote.call_args.args[1])

    def test_provision_waits_before_staging_or_removing_receipt(self):
        self.check_provision_after_owner(True)

    def test_different_update_waits_then_defers_closing_to_guarded_installer(self):
        self.check_provision_after_owner(False)

    def test_older_installer_is_refused_before_staging(self):
        self.check_provision_after_owner(False, compatible=False)

    def check_provision_after_owner(self, matches, compatible=True):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'setup.exe'
            source.write_bytes(b'new installer' + ('installer-result-'.encode('utf-16le') if compatible else b''))
            args = SimpleNamespace(installer=source, iso=None, reinstall=True, cache_dir=Path(folder))
            client = SimpleNamespace(version=lambda: {}, host=lambda: {})
            events = []
            def remote(info, command, **kwargs):
                events.append(command)
                if 'Test-Path' in command:
                    return 'True'
                return 'desktop'
            def wait(info, **kwargs):
                events.append('WAIT')
                if 'attempt' in kwargs:
                    self.assertRegex(kwargs['attempt'], r'^[a-f0-9]{32}$')
            with patch.object(setup, 'online_vm', return_value={'name':'test','ramMb':1,'cpuCores':1,'gpuMode':1}), \
                    patch.object(setup, 'wait_ssh', return_value={}), patch.object(setup, 'ssh', side_effect=remote), \
                    patch.object(setup, 'guest_install_busy', return_value=True), \
                    patch.object(setup, 'wait_for_guest_install', side_effect=wait), \
                    patch.object(setup, 'guest_installer_matches', return_value=matches), \
                    patch.object(setup, 'stage_guest_installer') as stage, \
                    patch.object(setup, 'create_logon_task'), patch.object(setup, 'run_on_vm_desktop') as launch, \
                    patch.object(setup, 'remove_staged_installer'), \
                    patch.object(setup, 'remove_guest_install_task'), \
                    patch.object(setup.subprocess, 'run'), patch.object(setup, 'ssh_command', return_value=[]), \
                    patch.object(setup, 'steam_install_prompt'), patch.object(setup, 'open_display'):
                if compatible:
                    setup.provision(client, args)
                else:
                    with self.assertRaisesRegex(RuntimeError, 'older installer'):
                        setup.provision(client, args)
            if not compatible:
                stage.assert_not_called()
                launch.assert_not_called()
                self.assertFalse(any('Remove-Item' in event or 'Stop-Process' in event for event in events))
                return
            self.assertEqual(events[0], 'WAIT')
            self.assertFalse(any('Stop-Process' in event for event in events),
                             'The native installer must check guest idleness before closing its app')
            if matches:
                stage.assert_not_called()
                self.assertFalse(any('Remove-Item' in event for event in events))
                self.assertFalse(any(call.args[1].startswith('BloonsPlusSetup') for call in launch.call_args_list))
                self.assertEqual(events.count('WAIT'), 1)
            else:
                stage.assert_called_once()
                self.assertEqual(sum(call.args[1].startswith('BloonsPlusSetup') for call in launch.call_args_list), 1)
                self.assertEqual(events.count('WAIT'), 2)
                call = next(call for call in launch.call_args_list if call.args[1].startswith('BloonsPlusSetup'))
                self.assertRegex(call.args[1], r'^BloonsPlusSetup-[a-f0-9]{32}$')
                self.assertRegex(call.args[3], r'^/silent /attempt:[a-f0-9]{32}$')
                self.assertFalse(any('Remove-Item' in event for event in events))


if __name__ == '__main__':
    unittest.main()
