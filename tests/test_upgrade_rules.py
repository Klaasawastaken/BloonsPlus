"""Offline upgrade legality regressions; no game imports or inputs."""

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "upgrade_rules", ROOT / "autobtd6" / "upgrade_rules.py"
)
RULES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RULES)
can_upgrade_path = RULES.can_upgrade_path


class UpgradeRules(unittest.TestCase):
    def test_main_path_allows_two_crosspath_tiers(self):
        for main_path in range(3):
            for secondary_path in range(3):
                if main_path == secondary_path:
                    continue
                for main_tier in (3, 4, 5):
                    levels = [0, 0, 0]
                    levels[main_path] = main_tier
                    self.assertTrue(can_upgrade_path(levels, secondary_path))
                    levels[secondary_path] = 1
                    self.assertTrue(can_upgrade_path(levels, secondary_path))
                    levels[secondary_path] = 2
                    self.assertFalse(can_upgrade_path(levels, secondary_path))

    def test_third_path_is_never_opened(self):
        for empty_path in range(3):
            levels = [1, 1, 1]
            levels[empty_path] = 0
            self.assertFalse(can_upgrade_path(levels, empty_path))

    def test_main_path_can_continue_beside_crosspath(self):
        self.assertTrue(can_upgrade_path([2, 2, 0], 0))
        self.assertTrue(can_upgrade_path([4, 2, 0], 0))
        self.assertFalse(can_upgrade_path([5, 2, 0], 0))
        self.assertFalse(can_upgrade_path([3, 2, 0], 1))

    def test_invalid_input_cannot_authorize_an_upgrade(self):
        for levels in (None, [], [0, 0], [0, 0, 0, 0], "000",
                       [True, 0, 0], [1.0, 0, 0], [-1, 0, 0],
                       [6, 0, 0], [1, 1, 1], [3, 3, 0]):
            with self.subTest(levels=levels):
                self.assertFalse(can_upgrade_path(levels, 0))
        for path in (None, True, False, "0", 0.0, -1, 3):
            with self.subTest(path=path):
                self.assertFalse(can_upgrade_path([0, 0, 0], path))

    def test_input_is_preserved(self):
        levels = [3, 1, 0]
        self.assertTrue(can_upgrade_path(levels, 1))
        self.assertEqual(levels, [3, 1, 0])
        self.assertTrue(can_upgrade_path((3, 1, 0), 1))


if __name__ == "__main__":
    unittest.main()
