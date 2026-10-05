"""Unresolved planned purchases survive checkpoint updates."""
import ast
from pathlib import Path
import unittest


class UpgradeCheckpoint(unittest.TestCase):
    def setUp(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'autobtd6/replay.py').read_text(encoding='utf-8'))
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'recordUpgradeCheckpoint']
        self.assertEqual(len(functions), 1, 'Missing checkpoint intent recorder')
        env = {}
        exec(compile(ast.Module(body=functions, type_ignores=[]), '<checkpoint>', 'exec'), env)
        self.record = env['recordUpgradeCheckpoint']

    def test_retains_and_deduplicates_unconfirmed_target(self):
        checkpoint = {}
        action = dict(action='upgrade', name='heli0', path=0, cost=21000, key='u',
                      pos=(100, 200), expectedUpgradeTiers=[4, 0, 2],
                      upgradeObservation=dict(status='unchanged', before=[3, 0, 2]))
        self.record(checkpoint, action)
        self.record(checkpoint, action)
        action['expectedUpgradeTiers'][0] = 5
        self.assertEqual(len(checkpoint['unresolvedUpgrades']), 1)
        self.assertEqual(checkpoint['unresolvedUpgrades'][0]['expectedUpgradeTiers'], [4, 0, 2])

    def test_only_observed_sufficient_tiers_clear_matching_tower(self):
        checkpoint = {'unresolvedUpgrades': [
            dict(name='heli0', expectedUpgradeTiers=[4, 0, 2]),
            dict(name='heli0', expectedUpgradeTiers=[5, 0, 2]),
            dict(name='heli1', expectedUpgradeTiers=[4, 0, 2])]}
        self.record(checkpoint, dict(name='heli0', upgradeObservation=dict(status='confirmed', after=[4, 0, 2])))
        self.assertEqual(len(checkpoint['unresolvedUpgrades']), 2)
        self.assertEqual(checkpoint['unresolvedUpgrades'][0]['expectedUpgradeTiers'], [5, 0, 2])


if __name__ == '__main__':
    unittest.main()
