"""Offline placement UI regressions; no game input."""
import sys
import unittest
from pathlib import Path
import cv2
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'autobtd6'))
from placement_observation import held_placement_visible

class HeldPlacement(unittest.TestCase):
    def frame(self, close=True, cancel=True):
        frame = np.zeros((540, 960, 3), dtype=np.uint8)
        root = Path(__file__).resolve().parents[1] / 'autobtd6/images/hud'
        for enabled, name, x, y in ((close, 'placement-close.png',784,44),
                                     (cancel, 'placement-cancel.png',835,489)):
            if enabled:
                image = cv2.imread(str(root / name))
                h,w = image.shape[:2]
                frame[y:y+h,x:x+w] = image
        return frame

    def test_requires_both_controls(self):
        for close,cancel in ((False,False),(True,False),(False,True)):
            self.assertFalse(held_placement_visible(self.frame(close,cancel)))
        self.assertTrue(held_placement_visible(self.frame()))

    def test_supported_resolutions(self):
        for size in ((1920,1080),(2560,1440)):
            self.assertTrue(held_placement_visible(cv2.resize(self.frame(),size)))

    def test_unknown_layout(self):
        for frame in (None,np.zeros((540,960)),np.zeros((200,300,3),np.uint8)):
            self.assertFalse(held_placement_visible(frame))

if __name__ == '__main__':
    unittest.main()
