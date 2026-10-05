from pathlib import Path
import sys
import unittest
import ast
import textwrap
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'autobtd6'))
from map_availability import predicted_thaw_round
from route_timing import upgrade_ready
from resume_recovery import restore_upgrade_steps


class MapAvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.events = [dict(type='place', tower='dart0', round=1, status='cash-confirmed')]

    def thaw(self, round_number, **overrides):
        args = dict(map_name='glacial_trail', tower_name='dart0', tower_type='dart',
                    events=self.events, current_round=round_number)
        args.update(overrides)
        return predicted_thaw_round(**args)

    def test_two_round_cycle_is_relative_to_each_placement(self):
        for round_number, expected in [(1, None), (9, None), (10, 12), (11, 12),
                                       (12, None), (20, 22), (21, 22)]:
            self.assertEqual(self.thaw(round_number), expected)
        events = [dict(type='place', tower='dart0', round=8, status='cash-confirmed')]
        self.assertEqual(self.thaw(17, events=events), 19)
        self.assertEqual(self.thaw(18, events=events), 19)
        self.assertIsNone(self.thaw(19, events=events))

    def test_unknown_or_immune_towers_never_invent_freeze(self):
        for tower_type in (None, '', 'ice', 'Ice Monkey', 'silas'):
            self.assertIsNone(self.thaw(10, tower_type=tower_type))
        self.assertIsNone(self.thaw(10, map_name='skulltweak'))
        self.assertIsNone(self.thaw(-1))
        self.assertIsNone(self.thaw(True))
        self.assertIsNone(self.thaw(10, events=[]))
        self.assertIsNone(self.thaw(10, events=[dict(type='place', tower='dart0', round=1, status='issued-unverified')]))

    def test_sale_and_replacement_use_current_instance(self):
        sold = self.events + [dict(type='sell', tower='dart0', round=3)]
        self.assertIsNone(self.thaw(10, events=sold))
        replaced = sold + [dict(type='place', tower='dart0', round=5, status='cash-confirmed')]
        self.assertIsNone(self.thaw(10, events=replaced))
        self.assertEqual(self.thaw(14, events=replaced), 16)

    def test_gate_waits_through_unknown_and_frozen_rounds(self):
        step = dict(action='upgrade', deferredUpgradeRound=12)
        for round_number in (None, -1, 10, 11):
            self.assertFalse(upgrade_ready(step, round_number))
        self.assertTrue(upgrade_ready(step, 12))
        self.assertTrue(upgrade_ready(step, 13))
        self.assertTrue(upgrade_ready(dict(action='place'), 10))
        for invalid in (True, 0, -1, 1.5):
            with self.assertRaises(ValueError):
                upgrade_ready(dict(action='upgrade', deferredUpgradeRound=invalid), 12)

    def test_checkpoint_keeps_exact_target_and_deferral_ahead_of_dependents(self):
        original = [dict(action='upgrade', name='dart0', path=0, key='current', cost=200,
                         pos=[10, 20], expectedUpgradeTiers=[2, 0, 0], routeStepIndex=0),
                    dict(action='upgrade', name='dart0', path=0, key='current', cost=300,
                         pos=[10, 20], expectedUpgradeTiers=[3, 0, 0], routeStepIndex=1)]
        pending = dict(original[0], deferredUpgradeRound=12)
        checkpoint = dict(nextStep=1, unresolvedUpgrades=[pending], remainingSteps=[pending, original[1]])
        restored = restore_upgrade_steps(original, checkpoint)
        self.assertEqual([s['routeStepIndex'] for s in restored], [0, 1])
        self.assertEqual(restored[0]['deferredUpgradeRound'], 12)
        self.assertEqual(restored[0]['expectedUpgradeTiers'], [2, 0, 0])
        self.assertTrue(restored[0]['resumeUpgradeProbe'])
        self.assertNotIn('deferredUpgradeRound', original[0])


    def run_recovery_branch(self, map_name, target):
        source = (Path(__file__).resolve().parents[1] / 'autobtd6/replay.py').read_text(encoding='utf-8')
        start = source.index('                            plannedTiers =')
        end = source.index('                            # Retrying on cash alone', start)
        function = next(node for node in ast.parse(source).body
                        if isinstance(node, ast.FunctionDef) and node.name == 'recordUpgradeCheckpoint')
        context = dict(predicted_thaw_round=predicted_thaw_round, customPrint=lambda *args: None,
                       mapConfig=dict(map=map_name, steps=[]), routeCheckpoint={},
                       currentGameState=SimpleNamespace(events=self.events, towers={'dart0': {'type': 'dart'}}),
                       currentValues={'round': 10}, upgradeStatus='unchanged',
                       lastIterationAction=dict(action='upgrade', name='dart0', path=0, key='current',
                           pos=[10, 20], cost=200, selectionAttempts=2, expectedUpgradeTiers=target,
                           upgradeObservation=dict(reason='button-unavailable', before=[1, 0, 0])))
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<checkpoint>', 'exec'), context)
        exec(textwrap.dedent(source[start:end]), context)
        return context

    def test_actual_replay_requeues_at_thaw_even_after_immediate_retry_limit(self):
        context = self.run_recovery_branch('glacial_trail', [2, 0, 0])
        queue = context['mapConfig']['steps']
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]['expectedUpgradeTiers'], [2, 0, 0])
        self.assertEqual(queue[0]['deferredUpgradeRound'], 12)
        self.assertTrue(queue[0]['resumeUpgradeProbe'])
        self.assertEqual(context['routeCheckpoint']['unresolvedUpgrades'][0]['deferredUpgradeRound'], 12)

    def test_actual_replay_keeps_other_maps_and_unknown_intent_bounded(self):
        self.assertEqual(self.run_recovery_branch('skulltweak', [2, 0, 0])['mapConfig']['steps'], [])
        self.assertEqual(self.run_recovery_branch('glacial_trail', None)['mapConfig']['steps'], [])


if __name__ == '__main__':
    unittest.main()
