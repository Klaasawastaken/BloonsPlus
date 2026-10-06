"""Observe ordinary tower tier pips and retry only an unchanged, available upgrade."""
from placement_observation import held_placement_visible
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


@lru_cache(maxsize=2)
def _hud_template(name):
    return cv2.imread(str(Path(__file__).resolve().parent / 'images/hud' / name))


def round_hud_on_right_panel(frame):
    """Locate the fixed HUD gear, independently of playfield colours."""
    if frame is None or frame.ndim != 3 or abs(frame.shape[0] / frame.shape[1] - 9 / 16) > .02:
        return None
    template = _hud_template('round-gear.png')
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


def cash_hud_shifted(frame):
    """Locate the currency glyph, avoiding lives in the displaced HUD."""
    if frame is None or frame.ndim != 3 or abs(frame.shape[0] / frame.shape[1] - 9 / 16) > .02:
        return None
    template = _hud_template('currency-symbol.png')
    if template is None:
        return None
    hud = cv2.resize(frame[:max(1, round(36 * frame.shape[1] / 960)), :, :3],
                     (960, 36), interpolation=cv2.INTER_AREA)
    scores = [float(cv2.minMaxLoc(cv2.matchTemplate(hud[5:36, x:x+24], template,
                    cv2.TM_CCOEFF_NORMED))[1]) for x in (168, 362)]
    winner = int(np.argmax(scores))
    # Native HUD downsampling and alternate hero skins change the glyph's
    # background. A recorded Sauda panel scored .80 here and .14 at the normal
    # HUD location; .82 rejected it and let cash read the shifted life counter.
    # Require stronger separation when accepting this slightly softer match.
    if scores[winner] >= .78 and scores[winner] - scores[1-winner] >= .35:
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
    cash_anchor = cash_hud_shifted(frame)
    if cash_anchor is not None:
        left_guess = cash_anchor
    return left_guess, right_guess  # Heroes use a different panel without path pips.


def recover_finished_route_hud(capture, click, wait, input_ready, report=lambda message: None):
    """Clear an observed orphan overlay only after route inputs have finished.

    Return whether input was issued, not whether the HUD has recovered. The
    input-owning loop must read the resulting screen on its next iteration.
    """
    if not input_ready(None):
        return False
    wait(1.0)
    frame = capture()
    if frame is None or frame.ndim != 3 or frame.shape[2] < 3 or not input_ready(frame):
        return False
    if held_placement_visible(frame):
        report('HUD_RECOVERY cancelling observed leftover placement after final route action')
        click((round(frame.shape[1] * 800 / 960), round(frame.shape[0] * 60 / 540)))
        wait(1.0)
        return True
    left, right = resolve_hud_panels(frame, False, False)
    if not (left or right):
        report('HUD_RECOVERY no blocking overlay confirmed; withholding recovery clicks')
        return False
    centre = (frame.shape[1] // 2, frame.shape[0] // 2)
    report('HUD_RECOVERY closing observed tower panel after final route action')
    click(centre)
    wait(.2)
    # The first click can reveal a result screen. Never authorize the second
    # click using the earlier INGAME pixels, even during this short wait.
    next_frame = capture()
    if (next_frame is not None and next_frame.ndim == 3 and next_frame.shape[2] >= 3
            and input_ready(next_frame)):
        click(centre)
        wait(1.0)
    return True


def select_tower(position, capture, click, wait, report=lambda message: None):
    """Clear a covering panel before selecting a world position.

    Hero panels have no tower tier pips, so use the same independent HUD
    anchors as the cash/round reader. Two centre clicks follow the requested
    panel-close behavior and never open the pause menu.
    """
    frame = capture()
    if held_placement_visible(frame):
        report('SELECTION_RECOVERY cancelling held placement before tower selection at ' + str(position))
        click((round(frame.shape[1] * 800 / 960), round(frame.shape[0] * 60 / 540)))
        wait(1.0)
        frame = capture()
        if held_placement_visible(frame):
            report('SELECTION_RECOVERY held placement remains; withholding target click')
            return False
    if frame is not None and frame.ndim == 3:
        left, right = resolve_hud_panels(frame, False, False)
        scale = frame.shape[1] / 960
        x, y = position
        covered = (25 * scale <= y <= 480 * scale and
                   (left and 0 <= x <= 210 * scale or right and 620 * scale <= x <= 825 * scale))
        if covered:
            centre = (frame.shape[1] // 2, frame.shape[0] // 2)
            report('SELECTION_RECOVERY closing covering panel before tower click at ' + str(position))
            click(centre)
            wait(0.15)
            click(centre)
            wait(0.35)
    click(position)
    return True


def verify_tower_placement(position, capture, click, wait):
    """Observe a newly selected base tower after ambiguous placement cash.

    Never buy, press a hotkey, or reuse an already open panel as evidence.
    Hero panels have different controls and are outside this observer's scope.
    """
    frame = capture()
    if frame is None or frame.ndim != 3:
        return False, {'status': 'unknown', 'reason': 'missing-frame'}
    if held_placement_visible(frame):
        return False, {'status': 'held'}
    left, right = resolve_hud_panels(frame, False, False)
    if left or right:
        centre = (frame.shape[1] // 2, frame.shape[0] // 2)
        click(centre)
        wait(.15)
        click(centre)
        wait(.35)
        frame = capture()
        if frame is None or frame.ndim != 3:
            return False, {'status': 'unknown', 'reason': 'missing-frame'}
        if held_placement_visible(frame) or any(resolve_hud_panels(frame, False, False)):
            return False, {'status': 'unknown', 'reason': 'previous-panel-not-cleared'}
    click(position)
    wait(1.0)
    frame = capture()
    if held_placement_visible(frame):
        return False, {'status': 'held'}
    panel = read_upgrade_panel(frame)
    if panel is None:
        return False, {'status': 'unselected'}
    if panel['tiers'] != [0, 0, 0]:
        return False, {'status': 'unexpected', 'tiers': panel['tiers']}
    return True, {'status': 'confirmed', 'tiers': panel['tiers'], 'side': panel['side']}


def observe_upgrade(path, capture, press, click, wait, reselect=None, expected_tiers=None):
    """Prefer a visible available button; allow one retry supported by unchanged pips.

    No input is sent to an unreadable panel. Reselecting is safe because it
    cannot buy another tier. Cash alone never authorizes a purchase retry.
    An unavailable button does not authorize a hotkey fallback: it may mean
    insufficient cash, a locked path, or a temporarily disabled tower.
    """
    before = read_upgrade_panel(capture())
    def matches_intent(panel):
        if panel is None:
            return False
        if expected_tiers is None:
            return True
        if len(expected_tiers) != 3:
            return False
        next_tiers = list(panel['tiers'])
        next_tiers[path] += 1
        return (next_tiers == list(expected_tiers)
                or all(actual >= target for actual, target in zip(panel['tiers'], expected_tiers)))

    for _ in range(2):
        # A readable panel can still belong to the previously selected tower.
        # Reselect before giving up; never send purchase input on a mismatch.
        if matches_intent(before) or reselect is None:
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
    if not before['available'][path]:
        return {'status': 'unchanged', 'before': before['tiers'],
                'after': before['tiers'], 'buttonRetry': False,
                'inputMethod': 'none', 'reason': 'button-unavailable'}
    click(before['buttons'][path])
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
            'inputMethod': 'button'}
