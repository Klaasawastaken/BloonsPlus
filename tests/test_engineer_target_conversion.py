"""Source-faithful Engineer targeting; no gameplay input or route replacement."""
import ast
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('engineer_import', ROOT / 'tools/import-public-routes.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class EngineerTargetTests(unittest.TestCase):
    def test_every_standard_transition_reaches_requested_target(self):
        for initial in module.TARGETS:
            for desired in module.TARGETS:
                route = module.Route('btd6bot', 'fixture.py', 'logs', 'hard')
                route.place('engi', 'engineer', 100, 200)
                route.set_target('engi', initial)
                start = len(route.lines)
                route.set_target('engi', desired)
                count = (module.TARGETS.index(desired) - module.TARGETS.index(initial)) % 4
                self.assertEqual(route.lines[start:], ['retarget engineer0'] * count)
                self.assertFalse(route.lossy)

    def test_moved_selector_is_preserved_and_positional_target_stays_excluded(self):
        route = module.Route('btd6bot', 'fixture.py', 'logs', 'hard')
        route.place('engi', 'engineer', 100, 200)
        module.btd6bot_statement(route, ast.parse('engi.target("strong", cpos=(0.3, 0.4))').body[0])
        self.assertEqual(route.lines[-3:], ['retarget engineer0 at 576, 432'] * 3)
        module.btd6bot_statement(route, ast.parse('engi.target("strong", x=0.1, y=0.2)').body[0])
        self.assertIn("positional targeting 'strong'", route.lossy)

    def test_unknown_target_does_not_emit_input(self):
        route = module.Route('btd6bot', 'fixture.py', 'logs', 'hard')
        route.place('engi', 'engineer', 100, 200)
        before = list(route.lines)
        route.set_target('engi', 'independent')
        self.assertEqual(route.lines, before)
        self.assertTrue(route.lossy)

    def test_actual_plans_retain_unrelated_omissions(self):
        for name in ('last_resortHardChimps.py', 'muddy_puddlesHardChimps.py',
                     'peninsulaHardChimps.py', 'sanctuaryHardChimps.py'):
            route = module.convert_btd6bot(module.BTD6BOT_PLANS / name)
            self.assertTrue(route.lossy, name)
            self.assertFalse(any('engineer targeting' in item for item in route.lossy), name)
            self.assertTrue(any(line.startswith('retarget engineer') for line in route.lines), name)


if __name__ == '__main__':
    unittest.main()
