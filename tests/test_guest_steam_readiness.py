"""Observed Steam handoff decisions; no VM, Steam launch or gameplay input."""
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('setup_steam', Path(__file__).resolve().parents[1] / 'vm/setup-vm.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


def state(*, installed=True, signed_in=True, running=True):
    return dict(steamInstalled=True, steamRunning=running, steamSignedIn=signed_in, btd6Installed=installed)


class GuestSteamReadiness(unittest.TestCase):
    def provision(self, before, after=None):
        observations = iter([before, before if after is None else after])
        queries = []
        def remote(info, command, **kwargs):
            if '/api/setup/guest' in command:
                queries.append(command)
                return json.dumps(next(observations))
            if 'Test-Path' in command:
                return 'True'
            return 'desktop'
        with tempfile.TemporaryDirectory() as folder:
            installer = Path(folder) / 'setup.exe'
            installer.write_bytes(b'MZ' + 'installer-result-'.encode('utf-16le'))
            args = SimpleNamespace(installer=installer, iso=None, reinstall=True, cache_dir=Path(folder))
            client = SimpleNamespace(version=lambda: {}, host=lambda: {})
            with patch.object(setup, 'online_vm', return_value=dict(name='test', ramMb=1, cpuCores=1, gpuMode=1)), \
                    patch.object(setup, 'wait_ssh', return_value={}), patch.object(setup, 'ssh', side_effect=remote), \
                    patch.object(setup, 'guest_install_busy', return_value=False), \
                    patch.object(setup, 'stage_guest_installer', return_value='staged.exe'), \
                    patch.object(setup, 'create_logon_task'), patch.object(setup, 'run_on_vm_desktop') as launch, \
                    patch.object(setup, 'wait_for_guest_install'), patch.object(setup, 'remove_guest_install_task'), \
                    patch.object(setup, 'remove_staged_installer'), patch.object(setup, 'open_display') as display, \
                    patch.object(setup, 'steam_install_prompt') as prompt, patch.object(setup, 'log') as log:
                setup.provision(client, args)
                display.assert_called_once()
                self.assertTrue(any(call.args[1].startswith('BloonsPlusSetup-') for call in launch.call_args_list))
                return launch.call_args_list, prompt.call_count, [call.args[0] for call in log.call_args_list], queries

    def test_ready_update_neither_focuses_steam_nor_opens_install_prompt(self):
        launches, prompts, messages, queries = self.provision(state())
        self.assertEqual(prompts, 0, 'An installed BTD6 must not receive an install URI during app update')
        self.assertFalse(any(call.args[1] == 'BloonsPlusSteam' for call in launches))
        self.assertEqual(len(queries), 2, 'Read readiness before and after installation')
        self.assertIn('Steam is signed in and Bloons TD 6 is already installed.', messages)
        self.assertFalse(any('Enter your Steam login' in item for item in messages))

    def test_installed_signed_out_game_only_requests_sign_in(self):
        launches, prompts, messages, _ = self.provision(state(signed_in=False))
        self.assertEqual(prompts, 0)
        self.assertFalse(any(call.args[1] == 'BloonsPlusSteam' for call in launches))
        self.assertTrue(any('sign in' in item and 'already installed' in item for item in messages))
        self.assertFalse(any('After sign-in Steam installs' in item for item in messages))

    def test_missing_game_keeps_official_install_prompt(self):
        _, prompts, messages, _ = self.provision(state(installed=False))
        self.assertEqual(prompts, 1)
        self.assertTrue(any('official Steam install prompt' in item for item in messages))

    def test_fresh_post_install_state_controls_handoff(self):
        _, prompts, messages, _ = self.provision(state(installed=False), state())
        self.assertEqual(prompts, 0)
        self.assertIn('Steam is signed in and Bloons TD 6 is already installed.', messages)

    def test_unknown_readiness_never_claims_missing_or_installed(self):
        _, prompts, messages, _ = self.provision(None)
        self.assertEqual(prompts, 0, 'Unknown is not an observed missing game')
        self.assertTrue(any('readiness is not available yet' in item for item in messages))
        self.assertFalse(any('already installed' in item for item in messages))

    def test_steam_stopped_during_update_is_opened_for_sign_in(self):
        launches, prompts, messages, _ = self.provision(state(), state(signed_in=False, running=False))
        self.assertEqual(prompts, 0)
        self.assertEqual(sum(call.args[1] == 'BloonsPlusSteam' for call in launches), 1)
        self.assertTrue(any('sign in' in item for item in messages))

    def test_steam_exited_after_earlier_launch_is_reopened(self):
        launches, prompts, messages, _ = self.provision(state(signed_in=False, running=False))
        self.assertEqual(prompts, 0)
        self.assertEqual(sum(call.args[1] == 'BloonsPlusSteam' for call in launches), 2,
                         'The earlier launch is not proof that Steam remains running')
        self.assertTrue(any('sign in' in item for item in messages))

    def test_state_reader_rejects_invalid_schema_without_actions(self):
        bad = ['UNKNOWN', 'null', '[]', '{}', json.dumps({**state(), 'btd6Installed': 'true'}),
               json.dumps({**state(), 'steamSignedIn': 1})]
        for raw in bad:
            with self.subTest(raw=raw), patch.object(setup, 'ssh', return_value=raw) as remote, \
                    patch.object(setup, 'run_on_vm_desktop') as launch:
                self.assertIsNone(setup.guest_steam_state({}))
                self.assertEqual(remote.call_args.kwargs['timeout'], 15)
                self.assertIn('-TimeoutSec 3', remote.call_args.args[1])
                self.assertIn('http://127.0.0.1:4173/api/setup/guest', remote.call_args.args[1])
                launch.assert_not_called()

    def test_state_reader_tolerates_failed_optional_probe(self):
        with patch.object(setup, 'ssh', side_effect=RuntimeError('unavailable')):
            self.assertIsNone(setup.guest_steam_state({}))


if __name__ == '__main__':
    unittest.main()
