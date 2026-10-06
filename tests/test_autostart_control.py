"""Offline control sequence tests; no gameplay is launched."""
import sys
from pathlib import Path
import unittest
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'autobtd6'))
from autostart_control import autostart_ready, parse_autostart_command, serialize_autostart_command, resume_autostart_intent
from resume_recovery import restore_action, restore_upgrade_steps


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


class AutoStartRouteContract(unittest.TestCase):
    def test_absolute_commands_round_trip_without_recovery_metadata(self):
        for line, enabled in (('autostart on', True), ('autostart off', False)):
            step = parse_autostart_command(line)
            self.assertEqual(step, dict(action='set_autostart', enabled=enabled, cost=0))
            step['autostartPending'] = dict(phase='toggling', sentAt=10, session='old')
            self.assertEqual(serialize_autostart_command(step), line)
        self.assertIsNone(parse_autostart_command('start round fast'))
        for line in ('autostart', 'autostart toggle', 'autostart off extra', 'autostart  off'):
            with self.assertRaises(ValueError): parse_autostart_command(line)

    def test_resume_derives_latest_consumed_source_intent(self):
        original = [dict(action='set_autostart', enabled=False, cost=0, routeStepIndex=0),
                    dict(action='await_round', round=10, routeStepIndex=1),
                    dict(action='set_autostart', enabled=True, cost=0, routeStepIndex=2)]
        snapshot = deepcopy(original)
        self.assertIsNone(resume_autostart_intent(original, {'nextStep': 0, 'autostartEnabled': False}))
        for offset in (1, 2):
            self.assertEqual(resume_autostart_intent(original, {'nextStep': offset, 'autostartEnabled': True}),
                             dict(action='set_autostart', enabled=False, cost=0))
        self.assertEqual(resume_autostart_intent(original, {'nextStep': 3}),
                         dict(action='set_autostart', enabled=True, cost=0))
        self.assertEqual(original, snapshot)
        for offset in (-1, 4, True, None):
            with self.assertRaises(ValueError): resume_autostart_intent(original, {'nextStep': offset})

    def test_actual_resume_queue_restores_matching_pending_control(self):
        original = [dict(action='set_autostart', enabled=False, cost=0, routeStepIndex=0)]
        saved = dict(original[0], autostartPending=dict(phase='toggling', sentAt=10, session='old', position='discard'))
        restored = restore_upgrade_steps(original, dict(nextStep=0, remainingSteps=[saved]))
        self.assertEqual(restored[0]['autostartPending'], dict(phase='toggling', sentAt=10, session='old'))
        self.assertEqual(restored[0]['routeStepIndex'], 0)
        for pending in (dict(phase='arbitrary', sentAt=10, session='old'),
                        dict(phase='closing', sentAt=float('nan'), session='old'),
                        dict(phase='closing', sentAt=True, session='old'),
                        dict(phase='closing', sentAt=10, session='')):
            with self.assertRaises(ValueError): restore_action(original[0], dict(saved, autostartPending=pending))
        with self.assertRaises(ValueError): restore_action(original[0], dict(saved, enabled=True))
        with self.assertRaises(ValueError): restore_action(original[0], dict(saved, enabled=0))

    def test_ordinary_queue_has_no_autostart_recheck(self):
        original = [dict(action='await_round', round=1, routeStepIndex=0)]
        self.assertIsNone(resume_autostart_intent(original, {'nextStep': 1}))
        self.assertEqual(restore_upgrade_steps(original, {'nextStep': 0}), original)


if __name__ == '__main__':
    unittest.main()
