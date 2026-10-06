import ast
import io
import json
import re
import sys
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'autobtd6'))
from route_timing import round_start_ready
from resume_recovery import restore_action
from game_runtime import normalize_action, GameState

class RoundStartTests(unittest.TestCase):
    def test_start_confirm_speed_and_no_same_frame_consumption(self):
        step = dict(action='start_round', speed='fast', key='Space')
        calls = []
        def persist(): calls.append('save'); return True
        def press(key): calls.append(key)
        self.assertEqual(round_start_ready(step, 100, 'paused', True, press, persist), (False, True))
        self.assertEqual(calls, ['save', 'Space'])
        self.assertEqual(round_start_ready(step, 100.2, 'slow', True, press, persist), (False, False))
        self.assertEqual(round_start_ready(step, 101, 'slow', True, press, persist), (False, True))
        self.assertEqual(round_start_ready(step, 102, 'fast', True, press, persist), (True, False))
        self.assertEqual(calls, ['save', 'Space', 'save', 'Space'])

    def test_unknown_busy_and_checkpoint_failure_send_nothing(self):
        for state, free in [(None, True), ('fast', False), ('paused', False)]:
            self.assertEqual(round_start_ready(dict(action='start_round', speed='fast', key='Space'), 1, state, free, self.fail), (False, False))
        step = dict(action='start_round', speed='fast', key='Space')
        self.assertEqual(round_start_ready(step, 1, 'paused', True, self.fail, lambda: False), (False, False))
        self.assertNotIn('roundStartPending', step)

    def test_retry_requires_observed_old_state_and_spacing(self):
        step = dict(action='start_round', speed='slow', key='Space')
        calls = []
        round_start_ready(step, 100, 'paused', True, calls.append)
        for now, state in [(100.1, 'paused'), (101, 'paused'), (103, None)]:
            self.assertEqual(round_start_ready(step, now, state, True, calls.append), (False, False))
        self.assertEqual(calls, ['Space'])
        self.assertEqual(round_start_ready(step, 104, 'paused', True, calls.append), (False, True))
        self.assertEqual(round_start_ready(step, 105, 'slow', True, calls.append), (True, False))

    def test_resume_rebinds_and_observes_before_press(self):
        source = dict(action='start_round', speed='fast', key='F8')
        saved = dict(source, key='Space', roundStartPending={'from':'slow','sentAt':100, 'key':'malicious'})
        step = restore_action(source, json.loads(json.dumps(saved)))
        self.assertEqual(step['key'], 'F8')
        self.assertNotIn('key', step['roundStartPending'])
        self.assertEqual(round_start_ready(step, 102, 'fast', True, self.fail), (True, False))
        self.assertEqual(round_start_ready(step, 50, 'slow', True, self.fail), (False, False))
        for pending in [{'from':'bad','sentAt':100}, {'from':'slow','sentAt':True}, {'from':'slow','sentAt':float('nan')}]:
            with self.assertRaises(ValueError): restore_action(source, dict(saved, roundStartPending=pending))

    def test_parser_recorder_and_contract(self):
        text = (ROOT / 'autobtd6/helper.py').read_text()
        a = text.index('    for line in configLines:')
        b = text.index('        roundOffset =', a)
        ctx = dict(re=re, configLines=['start round fast','start round slow'], newMapConfig={'steps':[]}, keybinds={'others':{'play':'Space'}})
        exec('if True:\n'+text[a:b], ctx)
        for step in ctx['newMapConfig']['steps']: self.assertEqual(normalize_action(step)['action'], 'start_round')
        ctx['keybinds']['others']['round_start'] = None
        ctx['newMapConfig'] = {'steps': []}
        exec('if True:\n'+text[a:b], ctx)
        self.assertIsNone(ctx['newMapConfig']['steps'][0]['key'])
        a = text.index('        elif action["action"] == "start_round":')
        b = text.index('        elif action["action"] == "await_round":', a)
        branch = textwrap.dedent(text[a:b]).replace('elif ', 'if ', 1)
        output = io.StringIO()
        exec(branch, dict(action={'action':'start_round','speed':'slow'}, fp=output))
        self.assertEqual(output.getvalue(), 'start round slow\n')
        with self.assertRaises(ValueError): normalize_action(dict(action='start_round', speed='turbo'))
        state = GameState({}, 'offline')
        state.record_issued_action(dict(action='start_round', speed='fast'))
        self.assertEqual(state.events[-1]['status'], 'issued-unverified')
        state.record_issued_action(dict(action='start_round', speed='fast', playStateConfirmed=True))
        self.assertEqual(state.events[-1]['status'], 'play-state-confirmed')

    def test_saved_unbound_upgrade_path_does_not_keep_default(self):
        source = (ROOT / 'autobtd6/helper.py').read_text()
        tree = ast.parse(source)
        names = {'_UNITY_SCANCODES', '_UNITY_NAMED', '_UNITY_MODIFIERS', '_SAVE_TOWER_NAMES'}
        selected = [node for node in tree.body if
                    isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in node.targets)
                    or isinstance(node, ast.FunctionDef) and node.name in ('unityBindingToKey', 'applyGameHotkeys')]
        ctx = dict(json=json, keybinds={'monkeys': {}, 'path': {'0': '1', '1': '2', '2': '3'},
                                     'others': {'play': 'Space'}, 'abilities': {}})
        exec(compile(ast.Module(body=selected, type_ignores=[]), '<bindings>', 'exec'), ctx)
        apply = ctx['applyGameHotkeys']
        apply(json.dumps({'monkeys': {'NinjaMonkey': {'path': '<Keyboard>/n'},
                                      'Upgrade Path 1': {'path': ''},
                                      'Upgrade Path 2': {'path': '<Keyboard>/2'},
                                      'Upgrade Path 3': {'path': '<Mouse>/leftButton'}}}))
        self.assertIsNone(ctx['keybinds']['path']['0'])
        self.assertEqual(ctx['keybinds']['path']['1'], 3)
        self.assertIsNone(ctx['keybinds']['path']['2'])
        ctx['keybinds']['path']['0'] = 'legacy'
        apply(json.dumps({'monkeys': {}}))
        self.assertEqual(ctx['keybinds']['path']['0'], 'legacy')

    def test_actual_replay_gate_and_automatic_input_ownership(self):
        source = (ROOT / 'autobtd6/replay.py').read_text()
        a = source.index('                roundStartInputIssued = False')
        b = source.index("                if nextStep and 'secondsAfterRound'", a)
        code = textwrap.dedent(source[a:b])
        class Cv:
            TM_SQDIFF_NORMED = 0
            def matchTemplate(self, frame, template, mode): return [[0.01 if template == 'paused' else 0.2]]
        events = []
        step = dict(action='start_round', speed='fast', key='Space')
        ctx = dict(nextStepAction='start_round', nextStepDelayReady=True, nextStep=step, screenshot='frame',
                   cv2=Cv(), cutImage=lambda image, area:image, imageAreas={'compare':{'game_state':None}},
                   comparisonImages={'game_state':dict(game_playing_fast='fast',game_playing_slow='slow',game_paused='paused')},
                   routeCheckpoint={}, mapConfig={'steps':[step]}, skippingIteration=False, heldPlacement=False,
                   routeActionExecuted=False, playToggleIssued=False, round_start_ready=round_start_ready,
                   time=SimpleNamespace(time=lambda:100), sendKey=lambda key:events.append('press'),
                   writeRouteCheckpoint=lambda *args:events.append('save') or True, customPrint=lambda message:None)
        exec(code, ctx)
        self.assertEqual(events, ['save','press'])
        self.assertFalse(ctx['nextStepDelayReady'])
        self.assertTrue(ctx['routeActionExecuted'])
        tree = ast.parse(source)
        gate = next(node.test for node in ast.walk(tree) if isinstance(node, ast.If) and 'startupRoundStartPending' in ast.unparse(node.test))
        expression = compile(ast.Expression(gate), '<gate>', 'eval')
        values = dict(skippingIteration=False, placementRetryPending=False, startupRoundStartPending=True,
                      roundStartInputIssued=False, doAllStepsBeforeStart=False, mapConfig={'gamemode':'easy','steps':[step]},
                      waitingForLaterRound=True)
        self.assertFalse(eval(expression, values))
        values.update(startupRoundStartPending=False, roundStartInputIssued=True)
        self.assertFalse(eval(expression, values))
        values['roundStartInputIssued'] = False
        self.assertTrue(eval(expression, values))

if __name__ == '__main__': unittest.main()
