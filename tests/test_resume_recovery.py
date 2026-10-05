import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'autobtd6'))
from resume_recovery import restore_upgrade_steps, probe_owned_upgrade


class ResumeRecovery(unittest.TestCase):
    def test_pending_targets_rejoin_in_route_order_without_duplicate(self):
        steps = [dict(action='place', name='dart0', routeStepIndex=0),
                 dict(action='upgrade', name='dart0', path=0, key='current-key',
                      cost=100, pos=(10, 20), expectedUpgradeTiers=[1, 0, 0], routeStepIndex=1),
                 dict(action='upgrade', name='dart0', path=0, key='current-key',
                      cost=200, pos=(10, 20), expectedUpgradeTiers=[2, 0, 0], routeStepIndex=2)]
        checkpoint = dict(nextStep=2, unresolvedUpgrades=[
            dict(name='dart0', expectedUpgradeTiers=[2, 0, 0], pos=[30, 40]),
            dict(name='dart0', expectedUpgradeTiers=[1, 0, 0], pos=[30, 40], key='stale-key')])
        restored = restore_upgrade_steps(steps, checkpoint)
        self.assertEqual([s['routeStepIndex'] for s in restored], [1, 2])
        self.assertTrue(all(s['resumeUpgradeProbe'] for s in restored))
        self.assertEqual(restored[0]['key'], 'current-key')
        self.assertEqual(restored[0]['pos'], [30, 40])
        self.assertNotIn('resumeUpgradeProbe', steps[1])

    def test_unmatched_checkpoint_intent_is_rejected(self):
        with self.assertRaises(ValueError):
            restore_upgrade_steps([], dict(nextStep=0, unresolvedUpgrades=[
                dict(name='unknown', expectedUpgradeTiers=[5, 0, 0])]))

    def test_surplus_intent_is_recomputed_without_rejecting_recorded_queue(self):
        original = [dict(action='await_round', round=80, routeStepIndex=0)]
        checkpoint = dict(nextStep=0, remainingSteps=original, unresolvedUpgrades=[
            dict(name='heli0', expectedUpgradeTiers=[5, 0, 2], opportunistic=True)])
        self.assertEqual(restore_upgrade_steps(original, checkpoint), original)

    def test_saved_queue_does_not_replay_placements_after_an_old_retry(self):
        original = [dict(action='upgrade', name='dart0', path=0, key='x', cost=100,
                         pos=(10, 20), expectedUpgradeTiers=[1, 0, 0], routeStepIndex=0),
                    dict(action='place', name='ninja0', routeStepIndex=1),
                    dict(action='await_round', round=20, routeStepIndex=2)]
        checkpoint = dict(nextStep=0, remainingSteps=[original[0], original[2]],
                          unresolvedUpgrades=[dict(name='dart0', expectedUpgradeTiers=[1, 0, 0])])
        restored = restore_upgrade_steps(original, checkpoint)
        self.assertEqual([s['action'] for s in restored], ['upgrade', 'await_round'])

    def test_owned_target_is_identified_without_purchase_input(self):
        calls = []
        with patch('resume_recovery.read_upgrade_panel', return_value={'tiers': [2, 0, 1]}):
            result = probe_owned_upgrade([1, 0, 1], lambda: object(),
                                         lambda: calls.append('select'), lambda _: None)
        self.assertEqual(result['status'], 'confirmed')
        self.assertEqual(calls, ['select'])

    def test_surplus_plan_is_recomputed_instead_of_replayed_on_resume(self):
        checkpoint = dict(nextStep=0, remainingSteps=[
            dict(action='upgrade', name='dart0', extra={'opportunistic': True})])
        self.assertEqual(restore_upgrade_steps([], checkpoint), [])
        checkpoint['remainingSteps'][0]['action'] = 'place'
        with self.assertRaises(ValueError):
            restore_upgrade_steps([], checkpoint)

    def test_unknown_panel_is_bounded_and_never_confirms(self):
        calls = []
        with patch('resume_recovery.read_upgrade_panel', return_value=None):
            result = probe_owned_upgrade([1, 0, 0], lambda: object(),
                                         lambda: calls.append('select'), lambda _: None)
        self.assertEqual(result['status'], 'unselected')
        self.assertEqual(len(calls), 2)

    def test_missing_tier_remains_unconfirmed(self):
        with patch('resume_recovery.read_upgrade_panel', return_value={'tiers': [0, 0, 1]}):
            result = probe_owned_upgrade([1, 0, 1], lambda: object(), lambda: None, lambda _: None)
        self.assertEqual(result['status'], 'needed')

    def test_saved_queue_uses_current_keybinds_and_prices(self):
        original = [dict(action='upgrade', name='dart0', path=0, key='current', cost=100,
                         pos=(10, 20), expectedUpgradeTiers=[1, 0, 0], routeStepIndex=0)]
        saved = dict(original[0], key='obsolete', cost=999, pos=[30, 40], selectionAttempts=1)
        result = restore_upgrade_steps(original, dict(nextStep=0, remainingSteps=[saved]))[0]
        self.assertEqual(result['key'], 'current')
        self.assertEqual(result['cost'], 100)
        self.assertEqual(result['pos'], [30, 40])
        self.assertEqual(result['selectionAttempts'], 1)

    def test_invalid_saved_position_is_rejected_before_input(self):
        original = [dict(action='upgrade', name='dart0', path=0, key='x', cost=100,
                         pos=(10, 20), expectedUpgradeTiers=[1, 0, 0], routeStepIndex=0)]
        for position in ([float('nan'), 20], ['10', 20], [10], [True, 20]):
            with self.assertRaises(ValueError):
                restore_upgrade_steps(original, dict(nextStep=0, remainingSteps=[dict(original[0], pos=position)]))
