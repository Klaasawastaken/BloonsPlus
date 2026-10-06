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

    def shop(self, color, rows=3, close=True):
        frame=self.frame(close=close,cancel=False)
        for y1,y2 in ((148,210),(216,276),(280,343))[:rows]:
            frame[y1:y2,828:940]=color
        return frame

    def test_magic_shop_placement_is_recognized_at_supported_scales(self):
        # Magic Monkeys Only uses purple shop cards, not the normal cyan.
        purple=tuple(int(v) for v in cv2.cvtColor(np.uint8([[[135,130,210]]]),cv2.COLOR_HSV2BGR)[0,0])
        for size in ((960,540),(1920,1080),(2560,1440)):
            self.assertTrue(held_placement_visible(cv2.resize(self.shop(purple),size)))

    def test_shop_color_still_requires_close_and_two_distinct_rows(self):
        purple=tuple(int(v) for v in cv2.cvtColor(np.uint8([[[135,130,210]]]),cv2.COLOR_HSV2BGR)[0,0])
        self.assertFalse(held_placement_visible(self.shop(purple,close=False)))
        self.assertFalse(held_placement_visible(self.shop(purple,rows=1)))
        self.assertFalse(held_placement_visible(self.shop((190,190,190))))
        cyan=tuple(int(v) for v in cv2.cvtColor(np.uint8([[[100,150,210]]]),cv2.COLOR_HSV2BGR)[0,0])
        self.assertTrue(held_placement_visible(self.shop(cyan)))

if __name__ == '__main__':
    unittest.main()
