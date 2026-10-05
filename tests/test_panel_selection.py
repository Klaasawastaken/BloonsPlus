"""Tower selection ownership checks; all clicks are recorded, never sent."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'autobtd6'))
from upgrade_observation import select_tower


class PanelSelectionTests(unittest.TestCase):
    def check(self, width, side, point, covered):
        scale = width / 960
        frame = np.zeros((int(width * 9 / 16), width, 3), dtype=np.uint8)
        clicks, waits, messages = [], [], []
        with patch('upgrade_observation.resolve_hud_panels', return_value=side):
            select_tower(tuple(int(x * scale) for x in point), lambda: frame, clicks.append, waits.append, messages.append)
        target = tuple(int(x * scale) for x in point)
        centre = (width // 2, frame.shape[0] // 2)
        self.assertEqual(clicks, [centre, centre, target] if covered else [target])
        self.assertEqual(waits, [0.15, 0.35] if covered else [])
        self.assertEqual(len(messages), int(covered))

    def test_right_and_left_cover_at_all_supported_scales(self):
        for width in [960, 1920, 2560]:
            self.check(width, (False, True), (712, 165), True)
            self.check(width, (True, False), (100, 250), True)

    def test_uncovered_no_panel_and_hud_coordinates_are_not_closed(self):
        for side, point in [((False, True),(325,257)), ((False,False),(712,165)),
                            ((False,True),(712,10)), ((True,False),(712,165))]:
            self.check(1920, side, point, False)

    def test_missing_frame_sends_only_requested_selection(self):
        clicks = []
        select_tower((100, 200), lambda: None, clicks.append, lambda seconds: None)
        self.assertEqual(clicks, [(100, 200)])


if __name__ == '__main__':
    unittest.main()
