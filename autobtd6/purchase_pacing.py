"""Give untimed purchase batches time to finish without changing route commands."""
import math


def pacing_allowed(steps):
    # Explicit source timing owns game speed. Never reinterpret it implicitly.
    controls = {'set_autostart', 'speed', 'speed_toggle', 'start_round', 'await_delay', 'repeat_ability'}
    return not any(step.get('action') in controls or 'secondsAfterRound' in step
                   or step.get('timer', 0) for step in steps)


def affordable_upgrade_batch(steps, cash):
    if type(cash) not in (int, float) or not math.isfinite(cash) or cash < 0:
        return False
    spent, upgrades = 0, 0
    for step in steps:
        kind = step.get('action')
        if kind not in ('place', 'upgrade', 'retarget', 'special'):
            break
        cost = step.get('cost', 0)
        if type(cost) not in (int, float) or not math.isfinite(cost) or cost < 0:
            break
        spent += cost
        if spent > cash:
            break
        if kind == 'upgrade':
            upgrades += 1
        if upgrades >= 2:
            return True
    return False


def purchase_pacing_ready(needed, play_state, input_free, now, last_toggle, key, press):
    """One observed fast→slow input, then a fresh frame before any purchase.

    Paused/slow games need no input. An unknown image does not authorize a
    toggle. This uses observed state, so a resumed replay cannot blindly toggle
    a slow game back to fast. The normal controller restores route speed when
    the purchase batch ends and it is waiting for cash or the next round.
    """
    if not needed or play_state != 'fast' or key is None:
        return True, False
    if not input_free or now - last_toggle < 3:
        return False, False
    press(key)
    return False, True
