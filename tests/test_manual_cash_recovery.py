"""Recover an evidenced paused manual-source cash deadlock without changing purchases."""
from copy import deepcopy
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'autobtd6'))
try:
    from manual_cash_recovery import drive_manual_cash_recovery, restore_manual_cash_recovery
except ImportError:
    drive_manual_cash_recovery = None


class ManualCashRecovery(unittest.TestCase):
    def config(self):
        return {'sourceRoundTiming': True, 'autostartEnabled': False, 'gamemode': 'impoppable',
                'sourceRoundContext': {'round': 41},
                'steps': [{'action': 'upgrade', 'name': 'sniper1', 'routeStepIndex': 223,
                           'expectedUpgradeTiers': [0, 2, 1], 'cost': 540}]}

    def drive(self, config, now, state='paused', cash=263, round=34, free=True, save=True, events=None):
        self.assertTrue(callable(drive_manual_cash_recovery), 'Missing evidence-based manual cash recovery')
        return drive_manual_cash_recovery(config, now, state, round, cash, free, 57,
            lambda key: events.append(('key', key)), lambda: save,
            lambda text: events.append(('log', text)))

    def test_waits_for_consistent_stall_then_issues_one_observed_receipt(self):
        config = self.config(); original = deepcopy(config['steps']); events = []
        self.drive(config, 100, events=events)
        self.drive(config, 109, events=events)
        self.assertFalse(any(kind == 'key' for kind, _ in events))
        self.drive(config, 110, events=events)
        self.assertEqual([value for kind, value in events if kind == 'key'], [57])
        self.drive(config, 112, events=events)
        self.assertEqual([value for kind, value in events if kind == 'key'], [57], 'Never spam ambiguous input')
        self.drive(config, 113, state='fast', events=events)
        self.drive(config, 114, state='fast', cash=600, events=events)
        self.assertEqual(config['steps'], original, 'Keep the original intended purchase queued')
        self.assertEqual(config['sourceRoundContext'], {'round': 41}, 'Do not fabricate a source or HUD round')

    def test_rejects_unknown_busy_ordinary_and_non_drifted_states(self):
        for changes, state, free in (({}, None, True), ({}, 'paused', False),
            ({'sourceRoundTiming': False}, 'paused', True), ({'autostartEnabled': True}, 'paused', True),
            ({'sourceRoundContext': {'round': 34}}, 'paused', True), ({'gamemode': 'deflation'}, 'paused', True)):
            config = self.config(); config.update(changes); before = deepcopy(config); events = []
            self.drive(config, 100, state=state, free=free, events=events)
            self.drive(config, 120, state=state, free=free, events=events)
            self.assertEqual(config, before)
            self.assertFalse(any(kind == 'key' for kind, _ in events))

    def test_failed_receipt_save_does_not_press_and_restart_does_not_repeat_input(self):
        config = self.config(); events = []
        self.drive(config, 100, events=events)
        self.drive(config, 110, save=False, events=events)
        self.assertFalse(any(kind == 'key' for kind, _ in events))
        self.drive(config, 111, events=events)
        restarted = deepcopy(config)
        self.drive(restarted, 113, events=events)
        self.assertEqual([value for kind, value in events if kind == 'key'], [57])
        self.drive(restarted, 114, state='fast', events=events)
        self.assertIsNone(restarted['manualCashRecovery'].get('receipt'))

    def test_limits_recovery_to_three_distinct_rounds_per_queued_purchase(self):
        config = self.config(); events = []
        for attempt, round in enumerate((34, 35, 36, 37)):
            now = 100 + attempt * 20
            self.drive(config, now, round=round, events=events)
            self.drive(config, now+10, round=round, events=events)
            self.drive(config, now+11, round=round, state='fast', events=events)
        self.assertEqual([value for kind, value in events if kind == 'key'], [57]*3)

    def test_running_or_busy_frame_breaks_paused_stall_evidence(self):
        for changes in ({'state': 'fast'}, {'free': False}, {'state': None}):
            config = self.config(); events = []
            self.drive(config, 100, events=events)
            self.drive(config, 108, events=events, **changes)
            self.drive(config, 110, events=events)
            self.drive(config, 119, events=events)
            self.assertFalse(any(kind == 'key' for kind, _ in events))
            self.drive(config, 120, events=events)
            self.assertEqual([value for kind, value in events if kind == 'key'], [57])

    def test_consumed_purchase_discards_completed_recovery_but_not_a_pending_receipt(self):
        state = {'owner': 223, 'attempts': 1, 'lastStartedRound': 34, 'receipt': None}
        self.assertIsNone(restore_manual_cash_recovery(state, {'routeStepIndex': 224}))
        self.assertIsNone(restore_manual_cash_recovery(state, None))
        state['receipt'] = {'action': 'play_once', 'playOncePending': {'from': 'paused', 'round': 34, 'sentAt': 100}}
        with self.assertRaises(ValueError):
            restore_manual_cash_recovery(state, {'routeStepIndex': 224})

    def test_checkpoint_rejects_malformed_receipts_and_clocks(self):
        first = self.config()['steps'][0]
        for state in ({'owner': 223, 'attempts': 4}, {'owner': 223, 'attempts': 0, 'watchAt': float('nan')},
            {'owner': 223, 'attempts': 1, 'receipt': {'action': 'play_once', 'playOncePending': {'from': 'fast', 'sentAt': 100, 'round': 34}}}):
            with self.assertRaises(ValueError):
                restore_manual_cash_recovery(state, first)


if __name__ == '__main__': unittest.main()
