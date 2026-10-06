"""Offline source, full-parser, recording and ledger checks. No gameplay input."""
import ast
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('selection_import', ROOT / 'tools/import-public-routes.py')
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)
sys.path.insert(0, str(ROOT / 'autobtd6'))
from game_runtime import GameState, normalize_action
from resume_recovery import restore_action


class SelectionPositionTests(unittest.TestCase):
    def test_positional_selector_matches_keyword_selector(self):
        positional = ('sniper.upgrade(["1-0-0"], (.5,.5))',
                      'sniper.target("strong", None, None, (.25,.25))',
                      'sniper.special(1, None, None, (.4,.4))',
                      'sniper.sell((.3,.3))')
        keyword = ('sniper.upgrade(["1-0-0"], cpos=(.5,.5))',
                   'sniper.target("strong", cpos=(.25,.25))',
                   'sniper.special(1, cpos=(.4,.4))',
                   'sniper.sell(cpos=(.3,.3))')
        routes = []
        for commands in (positional, keyword):
            route = importer.Route('test', 'test', 'logs', 'hard')
            route.place('sniper', 'sniper', 200, 300)
            for command in commands:
                importer.btd6bot_statement(route, ast.parse(command).body[0])
            routes.append(route)
        self.assertEqual(routes[0].lines, routes[1].lines)
        self.assertEqual(routes[0].towers, routes[1].towers)
        self.assertFalse(routes[0].lossy)

    def test_keyword_tower_arguments_preserve_source_intent(self):
        route = importer.Route('test', 'test', 'logs', 'hard')
        route.place('sniper', 'sniper', 200, 300)
        for command in ('sniper.upgrade(set_upg=["1-0-0"], cpos=(.5,.5))',
                        'sniper.target(set_target="strong")'):
            importer.btd6bot_statement(route, ast.parse(command).body[0])
        self.assertEqual(route.lines[1], 'upgrade sniper0 path 0 at 960, 540')
        self.assertEqual(route.lines[2:], ['retarget sniper0 at 960, 540'] * 3)

    def test_malformed_arguments_are_rejected_before_selector_changes(self):
        for command in ('sniper.sell((.5,.5), cpos=(.25,.25))',
                        'sniper.upgrade(["1-0-0"], unexpected=True, cpos=(.5,.5))',
                        'sniper.sell((.5,.5), True)',
                        'sniper.target("strong", y=.4, cpos=(.5,.5))'):
            with self.subTest(command=command):
                route = importer.Route('test', 'test', 'logs', 'hard')
                route.place('sniper', 'sniper', 200, 300)
                before = list(route.lines)
                with self.assertRaises(importer.Unsupported):
                    importer.btd6bot_statement(route, ast.parse(command).body[0])
                self.assertEqual(route.lines, before)
                self.assertNotIn('selectionPos', route.towers['sniper0'])

    def test_source_coordinate_persists_until_changed(self):
        route = importer.Route('test', 'test', 'logs', 'hard')
        route.place('sniper', 'sniper', 200, 300)
        for text in ('sniper.upgrade(["1-0-0"], cpos=(0.5, 0.5))',
                     'sniper.target("strong")', 'sniper.special(cpos=None)',
                     'sniper.sell(cpos=(0.25, 0.25))'):
            importer.btd6bot_statement(route, ast.parse(text).body[0])
        self.assertEqual(route.lines[1], 'upgrade sniper0 path 0 at 960, 540')
        self.assertTrue(all(line.endswith(' at 960, 540') for line in route.lines[1:-1]))
        self.assertEqual(route.lines[-1], 'sell sniper0 at 480, 270')
        self.assertFalse(route.lossy)

    def test_invalid_source_coordinate_is_rejected(self):
        for value in ('(True, .5)', '(.5, 1)', '(-.1, .5)', '(.5,)', 'dynamic'):
            route = importer.Route('test', 'test', 'logs', 'hard')
            route.place('sniper', 'sniper', 200, 300)
            with self.assertRaises(importer.Unsupported):
                importer.btd6bot_statement(route, ast.parse('sniper.special(cpos=' + value + ')').body[0])

    def test_full_parser_scaling_and_recording_round_trip(self):
        script = r'''
import contextlib,io,json,sys
from pathlib import Path
import helper
from helper import parseBTD6InstructionsFile,writeBTD6InstructionsFile
path,output=sys.argv[1:]
# Only adapt the temporary fixture's absolute filename; production routes use
# playthroughs/<name>. All instruction parsing/scaling/serialization is real.
original_name_parser=helper.parseBTD6InstructionFileName
helper.parseBTD6InstructionFileName=lambda name:original_name_parser(Path(name).name)
with contextlib.redirect_stdout(io.StringIO()):
    cfg=parseBTD6InstructionsFile(path,targetResolution=(2560,1440),gamemode='hard')
    writeBTD6InstructionsFile(cfg,folder=output,resolution='2560x1440')
steps=[dict(action=s['action'],pos=s.get('pos'),to=s.get('to'),selectionPos=s.get('selectionPos')) for s in cfg['steps']]
print(json.dumps(dict(steps=steps,recorded=next(Path(output).glob('*.btd6')).read_text())))
'''
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            route = root / 'logs#hard#1920x1080.btd6'
            route.write_text('place mortar mortar0 at 300, 400\n'
                'upgrade mortar0 path 0 at 600, 700\n'
                'retarget mortar0 to 1000, 800 at 700, 700\n'
                'special mortar0 to 1100, 850 at 800, 700\n'
                'sell mortar0 at 900, 700\n')
            env = dict(os.environ, AHK_PATH=str(ROOT / '.venv/Scripts/AutoHotkey.exe'))
            result = subprocess.run([sys.executable, '-X', 'utf8', '-c', script, str(route), str(root/'output')],
                cwd=ROOT/'autobtd6', env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(value['steps'][0]['pos'], [400, 533])
        self.assertEqual(value['steps'][1]['pos'], [800, 933])
        self.assertEqual(value['steps'][2]['pos'], [933, 933])
        self.assertEqual(value['steps'][2]['to'], [1333, 1067])
        self.assertIn('retarget mortar0 to 1333, 1067 at 933, 933', value['recorded'])
        self.assertIn('upgrade mortar0 path 0 at 800, 933', value['recorded'])
        self.assertEqual(value['steps'][3]['to'], [1467,1133])
        self.assertIn('special mortar0 to 1467, 1133 at 1067, 933', value['recorded'])
        self.assertIn('sell mortar0 at 1200, 933', value['recorded'])

    def test_resume_and_confirmed_ledger_use_updated_selection(self):
        action = normalize_action(dict(action='upgrade', name='dart0', path=0, key='comma',
            pos=[600,700], selectionPos=[600,700], cost=100))
        restored = restore_action(action, dict(action))
        self.assertEqual(restored['pos'], [600,700])
        state = GameState(dict(map='logs',gamemode='hard'), 'test')
        state.towers['dart0'] = dict(type='dart',position=[100,200],upgrades=[0,0,0])
        action['upgradeObservation'] = dict(status='confirmed',after=[1,0,0])
        state.confirm_purchase(action, dict(monkeys=dict(dart0=dict(type='dart',pos=[100,200]))), 1000,900)
        self.assertEqual(state.towers['dart0']['position'], [600,700])
        self.assertEqual(state.events[-1]['position'], [600,700])


if __name__ == '__main__':
    unittest.main()
