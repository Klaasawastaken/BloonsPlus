"""Offline command preservation and simulated callback order; no game input."""
import ast
import importlib.util
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('special_import', ROOT/'tools/import-public-routes.py')
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)
sys.path.insert(0, str(ROOT/'autobtd6'))
from targeted_special import perform_targeted_special

class TargetedSpecialTests(unittest.TestCase):
    def test_source_target_and_selector_are_distinct(self):
        route = importer.Route('test', 'test', 'logs', 'hard')
        route.place('gun', 'dartling', 300, 400)
        importer.btd6bot_statement(route, ast.parse('gun.special(1, x=.6, y=.7, cpos=(.2,.3))').body[0])
        self.assertEqual(route.lines[-1], 'special dartling0 to 1152, 756 at 384, 324')
        self.assertFalse(route.lossy)

    def test_second_special_remains_unsupported(self):
        route = importer.Route('test', 'test', 'logs', 'hard')
        route.place('gun', 'dartling', 300, 400)
        importer.btd6bot_statement(route, ast.parse('gun.special(2, x=.6, y=.7)').body[0])
        self.assertIn('second special ability', route.lossy)

    def test_runtime_key_then_target_click(self):
        calls = []
        action = dict(action='special', key='tab', pos=(100,200), to=(600,700))
        perform_targeted_special(action, lambda key:calls.append(('key',key)),
            lambda point:calls.append(('move',point)), lambda:calls.append(('click',)),
            lambda seconds:calls.append(('wait',seconds)))
        self.assertEqual([item for item in calls if item[0]!='wait'], [('key','tab'),('move',(600,700)),('click',)])
        self.assertEqual(action['pos'], (100,200))
        self.assertEqual(action['to'], (600,700))

if __name__ == '__main__': unittest.main()
