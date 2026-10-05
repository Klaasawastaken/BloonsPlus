"""Non-blocking route delays; the main loop keeps observing the live game."""
import math


def delay_ready(step, now):
    if not step or step.get('action') != 'await_delay':
        return True
    seconds = step.get('seconds')
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError('route delay must be finite and non-negative')
    if 'delayDeadline' not in step:
        step['delayDeadline'] = now + seconds
    deadline = step['delayDeadline']
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError('invalid route delay deadline')
    step['delayDeadline'] = min(deadline, now + seconds)
    return now >= step['delayDeadline']


def round_offset_ready(step, now, observed_round, round_started_at):
    """Gate an offset against the observed round start, never a new per-action delay."""
    if not step or step.get('action') != 'await_round' or 'secondsAfterRound' not in step:
        return True
    seconds = step['secondsAfterRound']
    target = step.get('round')
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError('round offset must be finite and non-negative')
    if type(target) is not int or target < 1:
        raise ValueError('round offset needs a positive round')
    if type(observed_round) is not int or observed_round < target:
        return False
    # An overdue action must not stall forever after a missed transition.
    if observed_round > target:
        return True
    if type(round_started_at) not in (int, float) or not math.isfinite(round_started_at):
        return False
    return now >= round_started_at + seconds


def ability_ready(step, now, round_started_at):
    """Hold ability input in the main loop without blocking screen observation.

    Pin the first observed deadline so a later round transition cannot extend
    the wait. With no known round anchor, preserve legacy immediate execution.
    """
    if not step or step.get('action') != 'ability':
        return True
    seconds = step.get('timer', 0)
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError('ability timer must be finite and non-negative')
    if 'abilityDeadline' not in step:
        anchor = round_started_at
        if type(anchor) not in (int, float) or not math.isfinite(anchor):
            return True
        step['abilityDeadline'] = anchor + seconds
    deadline = step['abilityDeadline']
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError('invalid ability deadline')
    return now >= deadline
