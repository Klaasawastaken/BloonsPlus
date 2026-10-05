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


if __name__ == '__main__':
    unittest.main()
