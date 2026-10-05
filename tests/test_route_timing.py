from pathlib import Path
import sys
import unittest
import re

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'autobtd6'))
from route_timing import delay_ready
from resume_recovery import restore_action
from game_runtime import normalize_action


class RouteTimingTests(unittest.TestCase):
    def test_delay_keeps_pending_without_blocking(self):
        step = dict(action='await_delay', seconds=2.5)
        self.assertFalse(delay_ready(step, 10))
        self.assertFalse(delay_ready(step, 12))
        self.assertTrue(delay_ready(step, 12.5))

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
        context = dict(re=re, configLines=['wait 1.5 seconds'], newMapConfig={'steps': []})
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
