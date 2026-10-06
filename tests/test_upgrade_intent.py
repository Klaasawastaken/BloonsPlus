"""Parsed upgrades retain immutable route intent without importing game input."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


class UpgradeIntent(unittest.TestCase):
    def test_parser_copies_planned_tiers(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'autobtd6/helper.py').read_text(encoding='utf-8'))
        assignment = next(node for node in ast.walk(tree)
                          if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)
                          and any(isinstance(k, ast.Constant) and k.value == 'action'
                                  and isinstance(v, ast.Constant) and v.value == 'upgrade'
                                  for k, v in zip(node.value.keys, node.value.values)))
        tiers = [3, 0, 2]
        groups = {'name': 'heli0', 'path': '0', 'discount': None}
        env = dict(matches=SimpleNamespace(group=groups.get), monkeyUpgrades=tiers,
                   monkeys={'heli0': {'type': 'heli', 'pos': (10, 20)}},
                   towers={'monkeys': {'heli': {'upgrades': [[1]*5]*3}}},
                   keybinds={'path': {'0': 'u'}}, newMapConfig={'difficulty': 2},
                   gamemode='hard', adjustPrice=lambda *args: 1)
        exec(compile(ast.Module(body=[assignment], type_ignores=[]), '<parser-upgrade>', 'exec'), env)
        tiers[0] = 4
        self.assertEqual(env['newStep']['expectedUpgradeTiers'], [3, 0, 2])

    def test_surplus_upgrade_has_exact_intent_from_chosen_tower(self):
        import importlib.util
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('surplus_rules', root / 'autobtd6/upgrade_rules.py')
        rules = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rules)
        tree = ast.parse((root / 'autobtd6/replay.py').read_text(encoding='utf-8'))
        function = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == 'nextSurplusUpgrade')
        first_levels = [2, 0, 0]
        roster = {'first': {'type': 'dart', 'position': [100, 200], 'upgrades': first_levels},
                  'last': {'type': 'dart', 'position': [300, 400], 'upgrades': [0, 0, 0]}}
        env = dict(currentGameState=SimpleNamespace(towers=roster), mapConfig={'gamemode': 'hard', 'difficulty': 2},
                   towers={'monkeys': {'dart': {'type': 'primary', 'upgrades': [[100]*5 for _ in range(3)]}}},
                   can_upgrade_in_roster=rules.can_upgrade_in_roster, userHasMonkeyKnowledge=lambda _: False,
                   surplusUpgradeCaps={'dart': [5, 5, 5]}, surplusUpgradeAttempts=set(), surplusBlockedPaths=set(),
                   adjustPrice=lambda price, *_: price, keybinds={'path': {'0': 'top', '1': 'middle', '2': 'bottom'}})
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<actual-surplus-planner>', 'exec'), env)
        action, stopped = env['nextSurplusUpgrade'](1000)
        self.assertFalse(stopped)
        self.assertEqual(action['name'], 'first')
        self.assertEqual(action['path'], 0)
        self.assertEqual(action['expectedUpgradeTiers'], [3, 0, 0])
        self.assertEqual(action['extra']['upgrade'], (0, 3))
        first_levels[0] = 4
        self.assertEqual(action['expectedUpgradeTiers'], [3, 0, 0])
        self.assertEqual(action['key'], 'top')


if __name__ == '__main__':
    unittest.main()
