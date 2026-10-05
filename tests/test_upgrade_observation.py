"""Tier recognition and retry regressions without game input."""
import sys
from pathlib import Path
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'autobtd6'))
from upgrade_observation import read_upgrade_panel, observe_upgrade, PIP_ROWS
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
        self.assertNotIn('click', calls)
        self.assertIn(1.0, calls)

    def test_only_unchanged_available_path_gets_button_retry(self):
        result, calls = self.run_observation([panel([0, 0, 0]), panel([0, 0, 0]), panel([1, 0, 0])])
        self.assertEqual(result['status'], 'confirmed')
        self.assertEqual(calls.count('click'), 1)
        self.assertTrue(result['buttonRetry'])

    def test_unavailable_and_unknown_panels_do_not_authorize_retry(self):
        for after in (panel([0, 0, 0], available=False), None, panel([2, 0, 0]), panel([0, 0, 0], side='left')):
            result, calls = self.run_observation([panel([0, 0, 0]), after])
            self.assertNotIn('click', calls)
            self.assertNotEqual(result['status'], 'confirmed')

    def test_confirmed_panel_reconciles_ledger_even_with_income(self):
        state = GameState({'map': 'test', 'gamemode': 'hard'}, 'test')
        action = {'action': 'upgrade', 'name': 'tower1', 'path': 0, 'pos': (1, 1),
                  'upgradeObservation': {'status': 'confirmed', 'after': [3, 2, 0]}}
        state.confirm_purchase(action, {}, 100, 120)
        self.assertEqual(state.towers['tower1']['upgrades'], [3, 2, 0])
        self.assertEqual(state.events[-1]['status'], 'panel-tier-confirmed')


if __name__ == '__main__':
    unittest.main()
