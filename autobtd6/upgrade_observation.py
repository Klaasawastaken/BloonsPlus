"""Observe ordinary tower tier pips and retry only an unchanged, available upgrade."""
import numpy as np
import cv2
from functools import lru_cache
from pathlib import Path

PIP_ROWS = ((222, 234, 246, 258, 270),
            (296, 308, 320, 332, 344),
            (370, 382, 394, 406, 418))


def read_upgrade_panel(frame):
    if frame is None or frame.ndim != 3 or frame.shape[2] < 3:
        return None
    scale = frame.shape[1] / 960
    if abs(frame.shape[0] / frame.shape[1] - 9 / 16) > .02:
        return None
    def color(x, y):
        patch = frame[int((y-2)*scale):int((y+2)*scale),
                      int((x-2)*scale):int((x+2)*scale), :3]
        return np.median(patch.reshape(-1, 3), axis=0) if patch.size else (-1, -1, -1)
    panels = []
    for side, x, button_x in (('left', 28, 165), ('right', 639, 776)):
        tiers = []
        for row in PIP_ROWS:
            filled = []
            for y in row:
                b, g, r = color(x, y)
                if b < 100 and g >= 180 and r >= 70:
                    filled.append(1)
                elif ((abs(b-36) <= 22 and abs(g-74) <= 22 and abs(r-128) <= 26)
                      or (abs(b-59) <= 12 and abs(g-110) <= 12 and abs(r-151) <= 12)):
                    # BTD6 dims unused pips on a capped crosspath (native
                    # Heli 2-0-3 capture). They still represent unowned tiers.
                    filled.append(0)
                else:
                    break
            # A path fills from the bottom. Partial/occluded panels are unknown.
            if len(filled) != 5 or filled != sorted(filled):
                break
            tiers.append(sum(filled))
        if len(tiers) != 3 or sum(t > 0 for t in tiers) > 2 or sum(t > 2 for t in tiers) > 1:
            continue
        available = []
        for y in (240, 315, 390):
            b, g, r = color(button_x+26, y)
            available.append(bool(g > 150 and g > r*1.3 and b < 120))
        panels.append({'side': side, 'tiers': tiers, 'available': available,
                       'buttons': [(int(button_x*scale), int(y*scale)) for y in (245, 320, 395)]})
    return panels[0] if len(panels) == 1 else None


@lru_cache(maxsize=1)
def _round_gear_template():
    return cv2.imread(str(Path(__file__).resolve().parent / 'images/hud/round-gear.png'))


def round_hud_on_right_panel(frame):
    """Locate the fixed HUD gear, independently of playfield colours."""
    if frame is None or frame.ndim != 3 or abs(frame.shape[0] / frame.shape[1] - 9 / 16) > .02:
        return None
    template = _round_gear_template()
    if template is None:
        return None
    hud = cv2.resize(frame[:max(1, round(43 * frame.shape[1] / 960)), :, :3],
                     (960, 43), interpolation=cv2.INTER_AREA)
    scores = [float(cv2.minMaxLoc(cv2.matchTemplate(hud[:, x:x+54], template,
                    cv2.TM_CCOEFF_NORMED))[1]) for x in (775, 575)]
    winner = int(np.argmax(scores))
    if scores[winner] >= .9 and scores[winner] - scores[1-winner] >= .15:
        return winner == 1
    return None


def resolve_hud_panels(frame, left_guess, right_guess):
    """A complete tier panel outranks colour guesses influenced by map effects."""
    panel = read_upgrade_panel(frame)
    if panel is not None:
        left_guess, right_guess = panel['side'] == 'left', panel['side'] == 'right'
    right_anchor = round_hud_on_right_panel(frame)
    if right_anchor is not None:
        right_guess = right_anchor
    return left_guess, right_guess  # Heroes use a different panel without path pips.


def observe_upgrade(path, capture, press, click, wait, reselect=None, expected_tiers=None):
    """Prefer a visible available button; allow one retry supported by unchanged pips.

    No input is sent to an unreadable panel. Reselecting is safe because it
    cannot buy another tier. Cash alone never authorizes a purchase retry.
    """
    before = read_upgrade_panel(capture())
    for _ in range(2):
        if before is not None or reselect is None:
            break
        reselect()
        wait(1.0)
        before = read_upgrade_panel(capture())
    if before is None:
        return {'status': 'unselected', 'before': None, 'after': None, 'buttonRetry': False}
    expected = list(before['tiers'])
    expected[path] += 1
    if expected_tiers is not None:
        if (len(expected_tiers) == 3
                and all(actual >= target for actual, target in zip(before['tiers'], expected_tiers))):
            return {'status': 'confirmed', 'before': before['tiers'], 'after': before['tiers'], 'buttonRetry': False}
        if expected != expected_tiers:
            return {'status': 'unexpected', 'before': before['tiers'], 'after': before['tiers'], 'buttonRetry': False}
    # A stale user hotkey can enter tower placement instead of upgrading.
    # When the panel supplies a confirmed green button, use its actual position.
    direct_button = bool(before['available'][path])
    if direct_button:
        click(before['buttons'][path])
    else:
        press()
    wait(1.0)
    after = read_upgrade_panel(capture())
    def result(panel):
        if before is None or panel is None or panel['side'] != before['side']:
            return 'unknown'
        if panel['tiers'] == expected:
            return 'confirmed'
        return 'unchanged' if panel['tiers'] == before['tiers'] else 'unexpected'
    status = result(after)
    retried = status == 'unchanged' and after['available'][path]
    if retried:
        click(after['buttons'][path])
        wait(1.0)
        after = read_upgrade_panel(capture())
        status = result(after)
    return {'status': status, 'before': before['tiers'] if before else None,
            'after': after['tiers'] if after else None, 'buttonRetry': bool(retried),
            'inputMethod': 'button' if direct_button else 'hotkey'}
