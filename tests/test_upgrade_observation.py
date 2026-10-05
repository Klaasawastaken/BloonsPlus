"""Tier recognition and retry regressions without game input."""
import sys
from pathlib import Path
import unittest
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'autobtd6'))
from upgrade_observation import read_upgrade_panel, observe_upgrade, PIP_ROWS, resolve_hud_panels
from game_runtime import GameState


def panel(tiers, side='right', available=True):
    frame = np.zeros((540, 960, 3), dtype=np.uint8)
    x, bx = (28, 165) if side == 'left' else (639, 776)
    for path, row in enumerate(PIP_ROWS):
        for i, y in enumerate(row):
            frame[y-3:y+3, x-3:x+3] = (0, 254, 204) if i >= 5-tiers[path] else (36, 74, 128)
    if available:
        for y in (240, 315, 390):
            frame[y-3:y+3, bx+23:bx+29] = (0, 240, 80)
    return frame


class UpgradeObservation(unittest.TestCase):
    def test_observed_panel_overrides_unstable_map_colour_guess(self):
        self.assertEqual(resolve_hud_panels(panel([2, 0, 4], 'right'), True, False), (False, True))
        self.assertEqual(resolve_hud_panels(panel([1, 0, 0], 'left'), False, True), (True, False))
        self.assertEqual(resolve_hud_panels(np.zeros((540, 960, 3), dtype=np.uint8), False, False), (False, False))

    def test_gear_anchor_overrides_false_panel_from_brown_map(self):
        gear = cv2.imread(str(Path(__file__).resolve().parents[1] / 'autobtd6/images/hud/round-gear.png'))
        for x, expected in ((784, False), (584, True)):
            frame = np.full((540, 960, 3), (35, 80, 140), np.uint8)
            h, w = gear.shape[:2]
            frame[3:3+h, x:x+w] = gear
            for size in ((1920, 1080), (2560, 1440)):
                scaled = cv2.resize(frame, size)
                self.assertEqual(resolve_hud_panels(scaled, False, not expected)[1], expected)

    def test_dimmed_unused_pips_on_maxed_crosspath(self):
        # Native Heli 2-0-3 panel: unused top-path pips change BGR colour
        # when that crosspath reaches its maximum. Closed middle path is brown.
        for side in ('left', 'right'):
            frame = panel([2, 0, 3], side)
            x = 28 if side == 'left' else 639
            for y in PIP_ROWS[0][:3]:
                frame[y-3:y+3, x-3:x+3] = (59, 110, 151)
            for width, height in ((1920, 1080), (2560, 1440)):
                scaled = cv2.resize(frame, (width, height), interpolation=cv2.INTER_NEAREST)
                result = read_upgrade_panel(scaled)
                self.assertIsNotNone(result)
                self.assertEqual(result['tiers'], [2, 0, 3])

    def test_uncertain_purchase_retains_panel_evidence(self):
        state = GameState({'map': 'test', 'gamemode': 'hard'}, 'test')
        state.events.append(dict(status='issued-unverified', type='upgrade', tower='heli0', path=0))
        observation = dict(status='unselected', screenshot='private-local-shot.png', before=None, after=None)
        state.mark_action_uncertain(dict(action='upgrade', name='heli0', path=0,
                                         upgradeObservation=observation), 22000, 22100)
        self.assertEqual(state.events[-1]['upgradeObservation'], observation)
        self.assertEqual(state.events[-1]['status'], 'cash-ambiguous')

    def test_panels_and_five_tiers(self):
        for side in ('left', 'right'):
            for levels in ([0, 0, 0], [5, 2, 0], [0, 1, 0]):
                result = read_upgrade_panel(panel(levels, side))
                self.assertEqual(result['tiers'], levels)
                self.assertEqual(result['side'], side)
        self.assertIsNone(read_upgrade_panel(np.zeros((540, 960, 3), dtype=np.uint8)))

    def run_observation(self, frames):
        source = iter(frames)
        calls = []
        result = observe_upgrade(0, lambda: next(source), lambda: calls.append('key'),
                                 lambda pos: calls.append('click'), lambda seconds: calls.append(seconds))
        return result, calls

    def test_success_is_not_retried(self):
        result, calls = self.run_observation([panel([0, 0, 0]), panel([1, 0, 0])])
        self.assertEqual(result['status'], 'confirmed')
        self.assertEqual(calls.count('click'), 1)
        self.assertNotIn('key', calls)
        self.assertIn(1.0, calls)

    def test_only_unchanged_available_path_gets_button_retry(self):
        result, calls = self.run_observation([panel([0, 0, 0]), panel([0, 0, 0]), panel([1, 0, 0])])
        self.assertEqual(result['status'], 'confirmed')
        self.assertEqual(calls.count('click'), 2)
        self.assertTrue(result['buttonRetry'])

    def test_unavailable_and_unknown_panels_do_not_authorize_retry(self):
        for after in (panel([0, 0, 0], available=False), None, panel([2, 0, 0]), panel([0, 0, 0], side='left')):
            result, calls = self.run_observation([panel([0, 0, 0]), after])
            self.assertEqual(calls.count('click'), 1)
            self.assertNotEqual(result['status'], 'confirmed')

    def test_confirmed_panel_reconciles_ledger_even_with_income(self):
        state = GameState({'map': 'test', 'gamemode': 'hard'}, 'test')
        action = {'action': 'upgrade', 'name': 'tower1', 'path': 0, 'pos': (1, 1),
                  'upgradeObservation': {'status': 'confirmed', 'after': [3, 2, 0]}}
        state.confirm_purchase(action, {}, 100, 120)
        self.assertEqual(state.towers['tower1']['upgrades'], [3, 2, 0])
        self.assertEqual(state.events[-1]['status'], 'panel-tier-confirmed')

    def test_reselect_before_pressing_upgrade(self):
        frames = iter([None, panel([0, 0, 0]), panel([1, 0, 0])])
        calls = []
        result = observe_upgrade(0, lambda: next(frames), lambda: calls.append('key'),
                                 lambda pos: calls.append('click'), lambda s: None,
                                 reselect=lambda: calls.append('select'))
        self.assertEqual(calls, ['select', 'click'])
        self.assertEqual(result['status'], 'confirmed')

    def test_missing_panel_never_sends_upgrade(self):
        calls = []
        result = observe_upgrade(0, lambda: None, lambda: calls.append('key'),
                                 lambda pos: calls.append('click'), lambda s: None,
                                 reselect=lambda: calls.append('select'))
        self.assertEqual(calls, ['select', 'select'])
        self.assertEqual(result['status'], 'unselected')

    def test_late_purchase_does_not_buy_next_tier_on_retry(self):
        calls = []
        result = observe_upgrade(0, lambda: panel([1, 0, 0]), lambda: calls.append('key'),
                                 lambda pos: calls.append('click'), lambda s: None,
                                 expected_tiers=[1, 0, 0])
        self.assertEqual(calls, [])
        self.assertEqual(result['status'], 'confirmed')

    def test_higher_owned_tier_does_not_trigger_another_purchase(self):
        calls = []
        result = observe_upgrade(0, lambda: panel([4, 0, 2]), lambda: calls.append('key'),
                                 lambda pos: calls.append('click'), lambda s: None,
                                 expected_tiers=[3, 0, 2])
        self.assertEqual(calls, [])
        self.assertEqual(result['status'], 'confirmed')
        self.assertEqual(result['after'], [4, 0, 2])

    def test_missing_prerequisite_does_not_mislabel_a_lower_tier(self):
        calls = []
        result = observe_upgrade(0, lambda: panel([1, 0, 0]), lambda: calls.append('key'),
                                 lambda pos: calls.append('click'), lambda s: None,
                                 expected_tiers=[3, 0, 0])
        self.assertEqual(calls, [])
        self.assertEqual(result['status'], 'unexpected')


if __name__ == '__main__':
    unittest.main()
