import sys
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'autobtd6'))
from purchase_pacing import pacing_allowed, affordable_upgrade_batch, purchase_pacing_ready


class PurchasePacingTests(unittest.TestCase):
    def test_source_controls_opt_out_for_whole_route(self):
        for action in ('speed', 'speed_toggle', 'start_round', 'await_delay', 'repeat_ability'):
            with self.subTest(action=action):
                self.assertFalse(pacing_allowed([dict(action='place'), dict(action=action)]))
        self.assertFalse(pacing_allowed([dict(action='ability', timer=2)]))
        self.assertFalse(pacing_allowed([dict(action='await_round', secondsAfterRound=0)]))
        self.assertTrue(pacing_allowed([dict(action='await_round'), dict(action='upgrade')]))

    def test_affordable_batch_preserves_barriers_and_costs(self):
        steps = [dict(action='place', cost=595), dict(action='retarget', cost=0),
                 dict(action='upgrade', cost=270), dict(action='upgrade', cost=380)]
        self.assertTrue(affordable_upgrade_batch(steps, 1245))
        self.assertFalse(affordable_upgrade_batch(steps, 1244))
        self.assertFalse(affordable_upgrade_batch([steps[2]], 5000))
        for barrier in ('await_round', 'await_cash', 'await_delay', 'sell', 'ability'):
            self.assertFalse(affordable_upgrade_batch([steps[2], dict(action=barrier), steps[3]], 5000))
        for cash in (-1, None, True, float('nan')):
            self.assertFalse(affordable_upgrade_batch(steps, cash))

    def test_fast_to_slow_is_observed_and_owns_the_frame(self):
        calls = []
        self.assertEqual(purchase_pacing_ready(True, 'fast', True, 10, 0, 'Space', calls.append), (False, True))
        self.assertEqual(calls, ['Space'])
        # A later slow frame confirms the toggle without repeating it.
        self.assertEqual(purchase_pacing_ready(True, 'slow', True, 11, 10, 'Space', calls.append), (True, False))
        # Resuming at slow speed also issues nothing.
        self.assertEqual(purchase_pacing_ready(True, 'slow', True, 50, 0, 'Space', calls.append), (True, False))
        self.assertEqual(calls, ['Space'])

    def test_no_blind_or_competing_toggle(self):
        calls = []
        for state in (None, 'paused', 'slow'):
            self.assertEqual(purchase_pacing_ready(True, state, True, 10, 0, 'Space', calls.append), (True, False))
        self.assertEqual(purchase_pacing_ready(False, 'fast', True, 10, 0, 'Space', calls.append), (True, False))
        self.assertEqual(purchase_pacing_ready(True, 'fast', False, 10, 0, 'Space', calls.append), (False, False))
        self.assertEqual(purchase_pacing_ready(True, 'fast', True, 11, 10, 'Space', calls.append), (False, False))
        self.assertEqual(purchase_pacing_ready(True, 'fast', True, 10, 0, None, calls.append), (True, False))
        self.assertEqual(calls, [])

    def test_actual_replay_gate_waits_for_a_new_frame(self):
        source = (Path(__file__).resolve().parents[1] / 'autobtd6/replay.py').read_text()
        start = source.index('                # Panel confirmation takes real time.')
        end = source.index('                if mode == Mode.VALIDATE_PLAYTHROUGHS:', start)
        code = textwrap.dedent(source[start:end])
        for allowed, confidence, expected in ((True, .01, ['Space']), (False, .01, []), (True, .2, [])):
            calls = []
            steps = [dict(action='upgrade', cost=270), dict(action='upgrade', cost=380)]
            context = dict(mapConfig=dict(purchasePacingAllowed=allowed, steps=steps),
                nextStepDelayReady=True, nextStepAction='upgrade', currentValues=dict(money=2000),
                affordable_upgrade_batch=affordable_upgrade_batch, purchase_pacing_ready=purchase_pacing_ready,
                imageAreas=dict(compare=dict(game_state='area')),
                comparisonImages=dict(game_state={name:name for name in ('game_playing_fast','game_playing_slow','game_paused')}),
                cv2=SimpleNamespace(TM_SQDIFF_NORMED=0, matchTemplate=lambda frame, template, method:
                    [[confidence if template == 'game_playing_fast' else .8]]),
                cutImage=lambda frame, area:frame, screenshot='frame', skippingIteration=False,
                heldPlacement=False, routeActionExecuted=False, playToggleIssued=False,
                time=SimpleNamespace(time=lambda:100), lastPlayToggleAt=0,
                keybinds=dict(others=dict(play='Space')), sendKey=calls.append, customPrint=lambda text:None)
            exec(code, context)
            self.assertEqual(calls, expected)
            self.assertEqual(context['nextStepDelayReady'], not bool(expected))
            self.assertEqual(context['routeActionExecuted'], bool(expected))
            self.assertEqual(context['playToggleIssued'], bool(expected))
            self.assertEqual(len(steps), 2)  # The purchase wasn't consumed on the toggle frame.


if __name__ == '__main__':
    unittest.main()
