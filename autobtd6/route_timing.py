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
