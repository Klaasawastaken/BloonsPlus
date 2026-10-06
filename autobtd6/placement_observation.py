"""Identify held placement UI independently of cash or playfield movement."""
from functools import lru_cache
from pathlib import Path

import cv2


@lru_cache(maxsize=2)
def _template(name):
    return cv2.imread(str(Path(__file__).parent / 'images/hud' / name))


def held_placement_visible(frame):
    """Require the placement close control plus cancel or tower-shop evidence.

    A tower panel's close button alone is insufficient. Unknown layouts return
    False and retain the existing recovery path; this is positive evidence only.
    """
    if frame is None or frame.ndim != 3 or frame.shape[2] < 3:
        return False
    if abs(frame.shape[0] / frame.shape[1] - 9 / 16) > .02:
        return False
    normalized = cv2.resize(frame[:, :, :3], (960, 540), interpolation=cv2.INTER_AREA)
    def match(name, box):
        template = _template(name)
        if template is None:
            return False
        x1, y1, x2, y2 = box
        score = cv2.minMaxLoc(cv2.matchTemplate(normalized[y1:y2, x1:x2], template,
                                              cv2.TM_CCOEFF_NORMED))[1]
        return score >= .92

    if not match('placement-close.png', (778, 38, 822, 82)):
        return False
    if match('placement-cancel.png', (828, 482, 883, 535)):
        return True
    # Ordinary placement keeps the tower shop, with no lower nudge-mode cancel
    # button. Require the same placement-only close anchor plus several cyan
    # shop-card rows, so an upgrade panel's close control alone cannot qualify.
    shop_rows = 0
    for y1, y2 in ((148, 210), (216, 276), (280, 343)):
        row = normalized[y1:y2, 828:940]
        hsv = cv2.cvtColor(row, cv2.COLOR_BGR2HSV)
        cyan = cv2.inRange(hsv, (85, 90, 90), (115, 255, 255))
        shop_rows += cv2.countNonZero(cyan) / cyan.size >= .30
    return shop_rows >= 2
