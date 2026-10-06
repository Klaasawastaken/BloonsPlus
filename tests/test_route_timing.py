from pathlib import Path
import sys
import unittest
import re
import io
import textwrap

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'autobtd6'))
from route_timing import delay_ready, round_offset_ready, ability_ready, issue_ability
from resume_recovery import restore_action
from autostart_control import parse_autostart_command
from game_runtime import normalize_action


class RouteTimingTests(unittest.TestCase):
    def test_delay_keeps_pending_without_blocking(self):
        step = dict(action='await_delay', seconds=2.5)
        self.assertFalse(delay_ready(step, 10))
        self.assertFalse(delay_ready(step, 12))
        self.assertTrue(delay_ready(step, 12.5))

    def test_ability_wait_is_nonblocking_and_round_change_does_not_reset_it(self):
        step = dict(action='ability', timer=8)
        self.assertFalse(ability_ready(step, 102, 100))
        self.assertFalse(ability_ready(step, 107, 106))
        self.assertTrue(ability_ready(step, 108, 106))
        self.assertEqual(step['abilityDeadline'], 108)

    def test_ability_overdue_zero_and_missing_anchor_keep_legacy_behavior(self):
        self.assertTrue(ability_ready(dict(action='ability', timer=2), 105, 100))
        self.assertTrue(ability_ready(dict(action='ability'), 100, 100))
        self.assertTrue(ability_ready(dict(action='ability', timer=5), 100, None))
        self.assertTrue(ability_ready(dict(action='upgrade'), 100, 100))

    def test_ability_invalid_timer_and_deadline_rejected(self):
        for value in (-1, True, '5', float('inf'), float('nan')):
            with self.assertRaises(ValueError):
                ability_ready(dict(action='ability', timer=value), 100, 100)
        with self.assertRaises(ValueError):
            ability_ready(dict(action='ability', abilityDeadline=float('nan')), 100, 100)

    def test_replay_no_long_sleep_before_ability_input(self):
        source = (Path(__file__).resolve().parents[1] / 'autobtd6/replay.py').read_text(encoding='utf-8')
        start = source.index("                    elif action['action'] == 'ability':")
        branch = source[start:source.index("                    elif action['action'] == 'speed':", start)]
        self.assertNotIn('time.sleep(', branch)
        self.assertIn('issue_ability(', branch)
        gate = source[source.index('                nextStepDelayReady = '):source.index('                nextStepCost = ', source.index('                nextStepDelayReady = '))]
        self.assertIn('ability_ready(nextStep', gate)

    def test_resume_preserves_unchanged_ability_deadline(self):
        source = dict(action='ability', timer=8)
        saved = dict(source, abilityDeadline=108)
        step = restore_action(source, saved)
        self.assertFalse(ability_ready(step, 107, 106))
        self.assertTrue(ability_ready(step, 108, 106))
        self.assertNotIn('abilityDeadline', restore_action(dict(source, timer=9), saved))
        with self.assertRaises(ValueError):
            restore_action(source, dict(saved, abilityDeadline=float('nan')))

    def test_delayed_cursor_keeps_observation_alive_and_sends_key_once(self):
        calls = []
        step = dict(action='ability', key='1', pos=(100, 200), cursor_delay=2)
        press = lambda key: calls.append(('key', key))
        move = lambda pos: calls.append(('move', pos))
        click = lambda: calls.append(('click',))
        self.assertFalse(issue_ability(step, 100, press, move, click))
        self.assertFalse(ability_ready(step, 101, 100))
        self.assertFalse(issue_ability(step, 101, press, move, click))
        self.assertTrue(ability_ready(step, 102, 101))
        self.assertTrue(issue_ability(step, 102, press, move, click))
        self.assertEqual(calls, [('key', '1'), ('move', (100, 200))])

    def test_immediate_cursor_preserves_move_and_click(self):
        calls = []
        step = dict(action='ability', key='1', pos=(100, 200))
        self.assertTrue(issue_ability(step, 100, lambda key: calls.append('key'),
                                     lambda pos: calls.append('move'), lambda: calls.append('click')))
        self.assertEqual(calls, ['key', 'move', 'click'])

    def test_resume_delayed_cursor_does_not_repeat_ability(self):
        source = dict(action='ability', key='1', timer=0, cursor_delay=2, pos=(100, 200))
        saved = dict(source, abilityInputSent=True, cursorDeadline=102)
        restored = restore_action(source, saved)
        calls = []
        self.assertTrue(issue_ability(restored, 103, lambda key: calls.append('key'),
                                      lambda pos: calls.append('move'), lambda: calls.append('click')))
        self.assertEqual(calls, ['move'])
        self.assertNotIn('abilityInputSent', restore_action(dict(source, key='2'), saved))
        with self.assertRaises(ValueError):
            restore_action(source, dict(saved, cursorDeadline=float('nan')))

    def test_actual_replay_cursor_branch_keeps_action_queued(self):
        from types import SimpleNamespace
        source = (Path(__file__).resolve().parents[1] / 'autobtd6/replay.py').read_text(encoding='utf-8')
        start = source.index("                    elif action['action'] == 'ability':")
        branch = textwrap.dedent(source[start:source.index("                    elif action['action'] == 'speed':", start)]).replace('elif ', 'if ', 1)
        calls = []
        action = dict(action='ability', slot=1, key='1', pos=(100, 200), cursor_delay=2)
        context = dict(action=action, thisIterationAction=action, mapConfig={'steps': []},
                       issue_ability=issue_ability, time=SimpleNamespace(time=lambda: 100),
                       sendKey=lambda key: calls.append('key'), customPrint=lambda message: None,
                       pyautogui=SimpleNamespace(moveTo=lambda pos: calls.append('move'), click=lambda: calls.append('click')))
        exec(branch, context)
        self.assertEqual(context['mapConfig']['steps'], [action])
        context['mapConfig']['steps'].pop(0)
        context['time'] = SimpleNamespace(time=lambda: 102)
        exec(branch, context)
        self.assertEqual(context['mapConfig']['steps'], [])
        self.assertIsNone(context['thisIterationAction'])
        self.assertEqual(calls, ['key', 'move'])

    def test_round_offsets_share_one_round_start(self):
        first = dict(action='await_round', round=20, secondsAfterRound=5)
        second = dict(action='await_round', round=20, secondsAfterRound=8)
        self.assertFalse(round_offset_ready(first, 104, 20, 100))
        self.assertTrue(round_offset_ready(first, 106, 20, 100))
        self.assertFalse(round_offset_ready(second, 107, 20, 100))
        self.assertTrue(round_offset_ready(second, 108, 20, 100))
        self.assertFalse(round_offset_ready(first, 200, 19, 100))
        self.assertTrue(round_offset_ready(first, 200, 21, 200))
        self.assertFalse(round_offset_ready(first, 200, 20, None))

    def test_round_offset_validation_and_parser(self):
        for seconds in (-1, float('nan'), float('inf'), True, '2'):
            with self.assertRaises(ValueError):
                round_offset_ready(dict(action='await_round', round=20, secondsAfterRound=seconds), 10, 20, 0)
            with self.assertRaises(ValueError):
                normalize_action(dict(action='await_round', round=20, secondsAfterRound=seconds))
        helper = (Path(__file__).resolve().parents[1] / 'autobtd6/helper.py').read_text(encoding='utf-8')
        start = helper.index('    for line in configLines:')
        code = helper[start:helper.index('        ability = re.search(', start)]
        context = dict(re=re,parse_autostart_command=parse_autostart_command, configLines=['round 20 after 5.5 seconds'], newMapConfig={'steps': []})
        exec('if True:\n' + code, context)
        self.assertEqual(context['newMapConfig']['steps'], [dict(action='await_round', round=20, secondsAfterRound=5.5, cost=0)])

    def test_round_offset_recording_retains_offset(self):
        helper = (Path(__file__).resolve().parents[1] / 'autobtd6/helper.py').read_text(encoding='utf-8')
        start = helper.index('        elif action["action"] == "await_round":')
        end = helper.index('        elif action["action"] == "await_cash":', start)
        branch = helper[start:end].replace('elif ', 'if ', 1)
        for seconds in (0, 5.5):
            output = io.StringIO()
            exec(textwrap.dedent(branch), dict(action=dict(action='await_round', round=20, secondsAfterRound=seconds), fp=output))
            self.assertEqual(output.getvalue(), f'round 20 after {seconds} seconds\n')

    def test_zero_and_other_actions(self):
        self.assertTrue(delay_ready(dict(action='await_delay', seconds=0), 10))
        self.assertTrue(delay_ready(dict(action='upgrade'), 10))
        self.assertTrue(delay_ready(None, 10))

    def test_invalid_duration(self):
        for seconds in (-1, float('nan'), float('inf'), True, '2'):
            with self.assertRaises(ValueError):
                delay_ready(dict(action='await_delay', seconds=seconds), 10)

    def test_parser_emits_canonical_delay(self):
        helper = (Path(__file__).resolve().parents[1] / 'autobtd6/helper.py').read_text(encoding='utf-8')
        start = helper.index('    for line in configLines:')
        code = helper[start:helper.index('        ability = re.search(', start)]
        context = dict(re=re,parse_autostart_command=parse_autostart_command, configLines=['wait 1.5 seconds'], newMapConfig={'steps': []})
        exec('if True:\n' + code, context)
        action = context['newMapConfig']['steps'][0]
        self.assertEqual(action, dict(action='await_delay', seconds=1.5, cost=0))
        self.assertEqual(normalize_action(action)['kind'], 'await_delay')

    def test_resume_preserves_deadline_only_for_unchanged_wait(self):
        source = dict(action='await_delay', seconds=5)
        saved = dict(source, delayDeadline=105)
        restored = restore_action(source, saved)
        self.assertFalse(delay_ready(restored, 103))
        self.assertTrue(delay_ready(restored, 106))
        changed = restore_action(dict(source, seconds=8), saved)
        self.assertNotIn('delayDeadline', changed)
        with self.assertRaises(ValueError):
            restore_action(source, dict(saved, delayDeadline=float('nan')))

    def test_replay_execution_gate_holds_delay_including_deflation(self):
        source = (Path(__file__).resolve().parents[1] / 'autobtd6/replay.py').read_text(encoding='utf-8')
        start = source.index("elif len(mapConfig['steps']) and nextStepDelayReady") + len('elif ')
        expression = source[start:source.index(':\n', start)]
        for mode in ('hard', 'deflation'):
            context = dict(mapConfig={'steps': [{'action':'await_delay'}], 'gamemode':mode},
                           nextStepDelayReady=False, nextStepCost=0)
            self.assertFalse(eval(expression, context))
            context['nextStepDelayReady'] = True
            self.assertTrue(eval(expression, context))


if __name__ == '__main__':
    unittest.main()
