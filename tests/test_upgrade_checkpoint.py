"""Unresolved planned purchases survive checkpoint updates."""
import ast
from pathlib import Path
import unittest


class UpgradeCheckpoint(unittest.TestCase):
    def setUp(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'autobtd6/replay.py').read_text(encoding='utf-8'))
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('recordUpgradeCheckpoint', 'checkpointStepOffset')]
        self.assertEqual(len(functions), 2, 'Missing checkpoint helpers')
        env = {}
        exec(compile(ast.Module(body=functions, type_ignores=[]), '<checkpoint>', 'exec'), env)
        self.record = env['recordUpgradeCheckpoint']
        self.offset = env['checkpointStepOffset']

    def test_offset_uses_original_positions_not_mutable_queue_length(self):
        steps = [dict(routeStepIndex=6), dict(routeStepIndex=6), dict(routeStepIndex=7)]
        self.assertEqual(self.offset(steps, 10), 6)
        self.assertEqual(self.offset([dict(extra={'opportunistic': True}), dict(routeStepIndex=8)], 10), 8)
        self.assertEqual(self.offset([], 10), 10)
        self.assertEqual(self.offset([dict(routeStepIndex=2), dict(routeStepIndex=9)], 10), 2)

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

    def test_retry_refreshes_position_and_observation_without_duplicate(self):
        checkpoint = {}
        action = dict(action='upgrade', name='heli0', path=0, cost=21000, key='u',
                      pos=(100, 200), expectedUpgradeTiers=[4, 0, 2],
                      upgradeObservation=dict(status='unselected'))
        self.record(checkpoint, action)
        action['pos'] = (130, 240)
        action['upgradeObservation'] = dict(status='unchanged')
        self.record(checkpoint, action)
        self.assertEqual(len(checkpoint['unresolvedUpgrades']), 1)
        self.assertEqual(checkpoint['unresolvedUpgrades'][0]['pos'], [130, 240])
        self.assertEqual(checkpoint['unresolvedUpgrades'][0]['observationStatus'], 'unchanged')


if __name__ == '__main__':
    unittest.main()
