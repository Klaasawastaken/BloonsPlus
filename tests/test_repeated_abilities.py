"""Offline repeat command checks. No game input, imported file rewriting or validation games."""
import io
import importlib.util
import re
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'autobtd6'))
from route_timing import RepeatedAbilities
from autostart_control import parse_autostart_command
from game_runtime import normalize_action


class RepeatTests(unittest.TestCase):
    def test_one_second_cycle_no_busy_bursts(self):
        loop = RepeatedAbilities()
        loop.start(1, '1')
        calls = []
        self.assertEqual(loop.tick(10, True, True, calls.append), 1)
        self.assertIsNone(loop.tick(10.1, True, False, calls.append))
        self.assertIsNone(loop.tick(10.2, True, True, calls.append))
        self.assertIsNone(loop.tick(10.9, True, True, calls.append))
        self.assertEqual(loop.tick(11, True, True, calls.append), 1)
        self.assertEqual(calls, ['1', '1'])

    def test_multiple_slots_and_duplicate_entries(self):
        loop = RepeatedAbilities()
        for slot in [1, 2, 1]:
            loop.start(slot, str(slot))
        calls = []
        for now in [0, 0.34, 0.68]:
            loop.tick(now, True, True, calls.append)
        self.assertEqual(calls, ['1', '2', '1'])
        loop.stop(1)
        self.assertEqual(loop.snapshot(), [2, 1])
        loop.stop(7)
        self.assertEqual(loop.snapshot(), [2, 1])
        loop.stop()
        self.assertIsNone(loop.tick(2, True, True, calls.append))

    def test_pause_or_input_owner_suspends_without_catchup(self):
        loop = RepeatedAbilities()
        loop.start(1, '1')
        calls = []
        self.assertIsNone(loop.tick(10, False, True, calls.append))
        self.assertIsNone(loop.tick(20, True, False, calls.append))
        self.assertEqual(loop.tick(30, True, True, calls.append), 1)
        self.assertIsNone(loop.tick(30, True, True, calls.append))
        self.assertEqual(calls, ['1'])
        self.assertEqual(loop.snapshot(), [1])  # persists across round changes

    def test_resume_rebinds_slots_not_keys_or_old_clocks(self):
        loop = RepeatedAbilities()
        loop.restore([10, 1, 1], {10:'F10', 1:'F1'})
        calls = []
        loop.tick(10000, True, True, calls.append)
        self.assertEqual(calls, ['F10'])
        self.assertEqual(loop.snapshot(), [10, 1, 1])
        for bad in [None, [0], [11], [True], ['1']]:
            with self.assertRaises(ValueError):
                loop.restore(bad, {1:'1'})
            self.assertEqual(loop.snapshot(), [10, 1, 1])
        with self.assertRaises(ValueError):
            loop.restore([1], {1:None})

    def test_contract_rejects_bad_slots_and_keys(self):
        for action in ['repeat_ability', 'stop_ability']:
            for slot in [0, 11, True, '1']:
                with self.assertRaises(ValueError):
                    normalize_action(dict(action=action, slot=slot, key='1'))
        self.assertEqual(normalize_action(dict(action='stop_ability', slot=None))['kind'], 'stop_ability')
        with self.assertRaises(ValueError):
            normalize_action(dict(action='repeat_ability', slot=1, key=None))

    def test_parser_and_recording_roundtrip(self):
        helper = (ROOT / 'autobtd6/helper.py').read_text(encoding='utf-8')
        start = helper.index('    for line in configLines:')
        code = helper[start:helper.index('        ability = re.search(', start)]
        context = dict(re=re,parse_autostart_command=parse_autostart_command, configLines=['repeat ability 10', 'stop ability 10', 'stop all abilities'],
                       newMapConfig={'steps': []}, keybinds={'abilities':{10:'F10'}})
        exec('if True:\n' + code, context)
        steps = context['newMapConfig']['steps']
        self.assertEqual([step['action'] for step in steps], ['repeat_ability', 'stop_ability', 'stop_ability'])
        self.assertEqual(steps[0]['key'], 'F10')
        a = helper.index('        elif action["action"] == "repeat_ability":')
        b = helper.index('        elif action["action"] == "await_delay":', a)
        branch = textwrap.dedent(helper[a:b]).replace('elif ', 'if ', 1)
        output = io.StringIO()
        for action in steps:
            exec(branch, dict(action=action, fp=output))
        self.assertEqual(output.getvalue(), 'repeat ability 10\nstop ability 10\nstop all abilities\n')

    def test_actual_runner_dispatch_and_input_gate(self):
        from types import SimpleNamespace
        source = (ROOT / 'autobtd6/replay.py').read_text(encoding='utf-8')
        a = source.index("                    elif action['action'] == 'repeat_ability':")
        b = source.index("                    elif action['action'] == 'speed':", a)
        branch = textwrap.dedent(source[a:b]).replace('elif ', 'if ', 1)
        loop = RepeatedAbilities()
        context = dict(action=dict(action='repeat_ability', slot=1, key='F1'), repeatedAbilities=loop, customPrint=lambda message: None)
        exec(branch, context)
        self.assertEqual(loop.snapshot(), [1])
        a = source.index('                if repeatedAbilities.entries:')
        b = source.index('                lastIterationScreenshotAreas = images', a)
        gate = textwrap.dedent(source[a:b])
        class Cv:
            TM_SQDIFF_NORMED = 0
            def matchTemplate(self, frame, template, mode):
                return [[0.01 if template == 'playing' else 0.2]]
        calls = []
        context.update(cv2=Cv(), cutImage=lambda image, area: image, screenshot='frame',
                       imageAreas={'compare':{'game_state':'area'}}, comparisonImages={'game_state':{'game_playing_fast':'playing', 'game_playing_slow':'other', 'game_paused':'ready'}},
                       mapConfig={'steps':[]}, time=SimpleNamespace(monotonic=lambda: 10), skippingIteration=False,
                       routeActionExecuted=True, playToggleIssued=False, placementRetryPending=False, heldPlacement=False,
                       sendKey=calls.append, currentGameState=None, currentValues={'round':20})
        exec(gate, context)
        self.assertEqual(calls, [])
        context['routeActionExecuted'] = False
        context['mapConfig']['steps'] = [dict(action='ability', abilityInputSent=True)]
        exec(gate, context)
        self.assertEqual(calls, [])
        context['mapConfig']['steps'] = []
        exec(gate, context)
        self.assertEqual(calls, ['F1'])
        context['action'] = dict(action='stop_ability', slot=1)
        exec(branch, context)
        self.assertEqual(loop.snapshot(), [])

    def test_importer_preserves_key_zero_and_cancellation(self):
        spec = importlib.util.spec_from_file_location('route_import', ROOT / 'tools/import-public-routes.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.txt'
            source.write_text('open resort, easy, standard\nplace dart, (0.5, 0.5), d\nrepeat ability 0\nrepeat ability 1\nstop ability 0\nstop all abilities\n', encoding='utf-8')
            result = module.convert_bloonsplayer(source)
            self.assertEqual(result.lines[-4:], ['repeat ability 10', 'repeat ability 1', 'stop ability 10', 'stop all abilities'])
            self.assertNotIn('activated abilities', result.lossy)
            source.write_text('open resort, easy, standard\nplace dart, (0.5, 0.5), d\nrepeat ability -\n', encoding='utf-8')
            with self.assertRaises(module.Unsupported):
                module.convert_bloonsplayer(source)


if __name__ == '__main__':
    unittest.main()
