"""Observe ordinary tower tier pips and retry only an unchanged, available upgrade."""
import numpy as np

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
                elif abs(b-36) <= 22 and abs(g-74) <= 22 and abs(r-128) <= 26:
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


def observe_upgrade(path, capture, press, click, wait):
    """One hotkey, then at most one button retry supported by unchanged pips.

    Unknown panels retain the existing single input behavior. No retry is
    authorized from a cash delta or a missing/occluded panel.
    """
    before = read_upgrade_panel(capture())
    press()
    wait(1.0)
    after = read_upgrade_panel(capture())
    def result(panel):
        if before is None or panel is None or panel['side'] != before['side']:
            return 'unknown'
        expected = list(before['tiers'])
        expected[path] += 1
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
            'after': after['tiers'] if after else None, 'buttonRetry': bool(retried)}
