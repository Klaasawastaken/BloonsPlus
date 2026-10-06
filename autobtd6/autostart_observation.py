"""Read the pause-menu Auto Start switch; this module sends no input."""
import cv2
import numpy as np


def _crop(frame, box):
    height, width = frame.shape[:2]
    x1, y1, x2, y2 = box
    return frame[round(y1 * height / 1080):round(y2 * height / 1080),
                 round(x1 * width / 1920):round(x2 * width / 1920)]


def _label_match(frame, reference, box):
    live = _crop(frame, box)
    expected = _crop(reference, box)
    if not live.size or not expected.size:
        return 0.0
    live = cv2.resize(live, (expected.shape[1], expected.shape[0]))
    live_edges = cv2.Canny(cv2.cvtColor(live, cv2.COLOR_BGR2GRAY), 80, 180)
    expected_edges = cv2.Canny(cv2.cvtColor(expected, cv2.COLOR_BGR2GRAY), 80, 180)
    if np.count_nonzero(live_edges) < 30 or np.count_nonzero(expected_edges) < 30:
        return 0.0
    return float(cv2.matchTemplate(live_edges, expected_edges, cv2.TM_CCOEFF_NORMED)[0, 0])


def observe_autostart(frame, pause_reference):
    """Require pause heading, switch label and one unambiguous blue knob.

    A green patch alone is never evidence of Auto Start. The reference is the
    existing full pause-menu calibration image, not an account screenshot.
    Returned coordinates are usable only when status is known. Off-state and
    additional live layouts still require gameplay observation before admission.
    """
    for image in (frame, pause_reference):
        if (not isinstance(image, np.ndarray) or image.dtype != np.uint8
                or image.ndim != 3 or image.shape[2] != 3
                or image.shape[0] < 360 or abs(image.shape[1] / image.shape[0] - 16 / 9) > 0.03):
            return {'status': 'unknown', 'reason': 'invalid-frame', 'pauseConfirmed': False}
    heading = _label_match(frame, pause_reference, (872, 10, 1060, 77))
    label = _label_match(frame, pause_reference, (1066, 282, 1248, 337))
    if heading < 0.85 or label < 0.85:
        return {'status': 'unknown', 'reason': 'pause-labels-unconfirmed', 'pauseConfirmed': False,
                'headingScore': round(heading, 3), 'labelScore': round(label, 3)}

    def cyan_fraction(box):
        pixels = _crop(frame, box)
        blue, green, red = (pixels[:, :, channel] for channel in range(3))
        return float(((blue > 170) & (green > 130) & (red < 90)).mean())

    left = cyan_fraction((1280, 295, 1303, 319))
    right = cyan_fraction((1347, 295, 1370, 319))
    rail = _crop(frame, (1277, 298, 1320, 315))
    blue, green, red = (rail[:, :, channel] for channel in range(3))
    # Both calibration resolutions use a lime rail (B=0, G=224..251,
    # R=114..127), not pure green. Compare channels as signed values so uint8
    # subtraction cannot wrap and turn another colour into false evidence.
    g, r, b = green.astype(np.int16), red.astype(np.int16), blue.astype(np.int16)
    green_rail = float(((g > 180) & (g - r > 70) & (g - b > 100) & (b < 100)).mean())
    if right > 0.65 and left < 0.1 and green_rail > 0.6:
        enabled = True
    elif left > 0.65 and right < 0.1 and green_rail < 0.1:
        enabled = False
    else:
        return {'status': 'unknown', 'reason': 'switch-state-ambiguous', 'pauseConfirmed': True,
                'leftKnob': round(left, 3), 'rightKnob': round(right, 3),
                'greenRail': round(green_rail, 3)}
    height, width = frame.shape[:2]
    return {'status': 'known', 'enabled': enabled, 'pauseConfirmed': True,
            'position': (round(1320 * width / 1920), round(307 * height / 1080))}
