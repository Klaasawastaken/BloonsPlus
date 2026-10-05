"""Identify held placement UI independently of cash or playfield movement."""
from functools import lru_cache
from pathlib import Path

import cv2


@lru_cache(maxsize=2)
def _template(name):
    return cv2.imread(str(Path(__file__).parent / 'images/hud' / name))


def held_placement_visible(frame):
    """Require both the placement close control and the lower cancel control.

    A tower panel's close button alone is insufficient. Unknown layouts return
    False and retain the existing recovery path; this is positive evidence only.
    """
    if frame is None or frame.ndim != 3 or frame.shape[2] < 3:
        return False
    if abs(frame.shape[0] / frame.shape[1] - 9 / 16) > .02:
        return False
    normalized = cv2.resize(frame[:, :, :3], (960, 540), interpolation=cv2.INTER_AREA)
    for name, box in (('placement-close.png', (778, 38, 822, 82)),
                      ('placement-cancel.png', (828, 482, 883, 535))):
        template = _template(name)
        if template is None:
            return False
        x1, y1, x2, y2 = box
        score = cv2.minMaxLoc(cv2.matchTemplate(normalized[y1:y2, x1:x2], template,
                                              cv2.TM_CCOEFF_NORMED))[1]
        if score < .92:
            return False
    return True
