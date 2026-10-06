"""Offline control sequence tests; no gameplay is launched."""
import sys
from pathlib import Path
import unittest
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'autobtd6'))
from autostart_control import autostart_ready


class AutoStartControl(unittest.TestCase):
    def setUp(self):
        self.step = {'action': 'set_autostart', 'enabled': False}
        self.inputs, self.saved, self.messages = [], [], []
        self.save_ok = True

    def save(self):
        self.saved.append(deepcopy(self.step))
        return self.save_ok

    def tick(self, now, screen='ingame', state=None, free=True, session='process-a'):
        observation = None if state is None else {'pauseConfirmed': True, 'status': 'known',
                                                  'enabled': state, 'position': (1320, 307)}
        return autostart_ready(self.step, now, screen, observation, free, session,
                               lambda key: self.inputs.append(('key', key)),
                               lambda pos: self.inputs.append(('click', pos)), self.save, self.messages.append)

    def test_full_sequence_waits_for_fresh_observation(self):
        self.assertEqual(self.tick(10), (False, True))
        self.assertEqual(self.tick(10.1, 'pause_menu', True), (False, False))
        self.assertEqual(self.tick(11, 'pause_menu', True), (False, True))
        self.assertEqual(self.tick(11.5, 'pause_menu', False), (False, False))
        self.assertEqual(self.tick(12, 'pause_menu', False), (False, True))
        self.assertEqual(self.tick(12.5), (False, False))
        self.assertEqual(self.tick(13), (True, False))
        self.assertEqual(self.inputs, [('key', '{Esc}'), ('click', (1320, 307)), ('key', '{Esc}')])
        self.assertEqual([s['autostartPending']['phase'] for s in self.saved], ['opening', 'toggling', 'closing'])

    def test_already_matching_switch_never_toggles(self):
        self.assertEqual(self.tick(10, 'pause_menu', False), (False, True))
        self.assertEqual(self.tick(11), (True, False))
        self.assertEqual(self.inputs, [('key', '{Esc}')])

    def test_restart_reopens_and_reobserves_after_saved_close(self):
        self.tick(10, 'pause_menu', False)
        self.assertEqual(self.tick(12, session='process-b'), (False, True))
        self.assertEqual(self.step['autostartPending']['phase'], 'opening')
        self.tick(13, 'pause_menu', False, session='process-b')
        self.assertEqual(self.tick(14, session='process-b'), (True, False))
        self.assertFalse(any(kind == 'click' for kind, value in self.inputs))

    def test_restart_after_toggle_reads_actual_state_instead_of_clicking_again(self):
        self.tick(10, 'pause_menu', True)
        self.tick(12, 'pause_menu', False, session='process-b')
        self.assertEqual(self.inputs, [('click', (1320, 307)), ('key', '{Esc}')])

    def test_busy_unknown_and_ambiguous_do_not_send_input(self):
        self.assertEqual(self.tick(10, free=False), (False, False))
        self.assertEqual(self.tick(10, 'unknown'), (False, False))
        self.assertEqual(self.tick(10, 'pause_menu'), (False, False))
        for obs in ({'pauseConfirmed': True, 'status': 'unknown'},
                    {'pauseConfirmed': False, 'status': 'known', 'enabled': True, 'position': (1320,307)},
                    {'pauseConfirmed': True, 'status': 'known', 'enabled': True, 'position': (-1,307)}):
            result = autostart_ready(self.step, 10, 'pause_menu', obs, True, 'process-a',
                                     self.inputs.append, self.inputs.append, self.save)
            self.assertEqual(result, (False, False))
        self.assertEqual(self.inputs, [])

    def test_failed_checkpoint_never_sends_input(self):
        self.save_ok = False
        self.assertEqual(self.tick(10), (False, False))
        self.assertNotIn('autostartPending', self.step)
        self.assertEqual(self.inputs, [])

    def test_failed_retry_checkpoint_preserves_prior_phase(self):
        self.tick(10, 'pause_menu', True)
        previous = deepcopy(self.step)
        self.save_ok = False
        self.assertEqual(self.tick(13, 'pause_menu', True), (False, False))
        self.assertEqual(self.step, previous)
        self.assertEqual(len(self.inputs), 1)

    def test_open_and_toggle_retries_have_cooldown(self):
        self.tick(10)
        self.assertEqual(self.tick(11), (False, False))
        self.assertEqual(self.tick(13), (False, True))
        self.tick(14, 'pause_menu', True)
        self.assertEqual(self.tick(15, 'pause_menu', True), (False, False))
        self.assertEqual(self.tick(17, 'pause_menu', True), (False, True))

    def test_backwards_clock_requires_saved_rebase(self):
        self.tick(10)
        self.assertEqual(self.tick(5), (False, False))
        self.assertEqual(self.step['autostartPending']['sentAt'], 5)
        self.assertEqual(len(self.inputs), 1)

    def test_closing_retry_does_not_burst_esc(self):
        self.tick(10, 'pause_menu', False)
        self.assertEqual(self.tick(11, 'pause_menu', False), (False, False))
        self.assertEqual(self.tick(13, 'pause_menu', False), (False, True))
        self.assertEqual(len(self.inputs), 2)

    def test_input_callback_observes_saved_intent(self):
        phases = []
        def press(key):
            self.assertEqual(self.saved[-1]['autostartPending'], self.step['autostartPending'])
            phases.append(self.saved[-1]['autostartPending']['phase'])
        result = autostart_ready(self.step, 10, 'ingame', None, True, 'process-a',
                                 press, self.inputs.append, self.save)
        self.assertEqual(result, (False, True))
        self.assertEqual(phases, ['opening'])

    def test_input_exception_leaves_recoverable_intent(self):
        def broken_press(key):
            raise RuntimeError('input transport interrupted')
        with self.assertRaises(RuntimeError):
            autostart_ready(self.step, 10, 'ingame', None, True, 'process-a',
                            broken_press, self.inputs.append, self.save)
        self.assertEqual(self.step['autostartPending']['phase'], 'opening')
        self.assertEqual(self.tick(12, 'pause_menu', False, session='process-b'), (False, True))

    def test_invalid_state_never_sends_input(self):
        for value in (None, 0, 'off'):
            self.step['enabled'] = value
            with self.assertRaises(ValueError): self.tick(10)
        self.assertEqual(self.inputs, [])


if __name__ == '__main__':
    unittest.main()
