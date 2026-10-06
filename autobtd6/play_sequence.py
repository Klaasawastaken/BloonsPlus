"""Observed two-input source Play sequence with resumable per-input intent."""
from copy import deepcopy
from math import isfinite


def restore_play_sequence(source, saved):
    if source.get('action') != 'play_twice' or saved.get('action') != 'play_twice':
        raise ValueError('Play sequence differs from source')
    step = deepcopy(source)
    pending = saved.get('sequencePending')
    if pending is None:
        return step
    if (not isinstance(pending, dict) or pending.get('phase') not in ('first', 'second')
            or pending.get('from') not in ('paused', 'slow', 'fast')
            or type(pending.get('sentAt')) not in (int, float) or not isfinite(pending['sentAt'])
            or type(pending.get('round')) is not int or pending['round'] < 1):
        raise ValueError('invalid Play sequence receipt')
    if pending['phase'] == 'second' and pending.get('firstState') not in ('slow', 'fast'):
        raise ValueError('second Play needs an observed first-input state')
    step['sequencePending'] = {key: pending[key] for key in ('phase', 'from', 'sentAt', 'round')}
    if pending['phase'] == 'second':
        first = pending['firstState']
        if pending['from'] != 'paused' and first != ('fast' if pending['from'] == 'slow' else 'slow'):
            raise ValueError('first Play state differs from source transition')
        step['sequencePending']['firstState'] = first
    return step


def persist_intent(step, previous, persist, report):
    try:
        saved = persist() is True
    except Exception as error:
        report('PLAY_SEQUENCE checkpoint error: ' + str(error))
        saved = False
    if not saved:
        if previous is None:
            step.pop('sequencePending', None)
        else:
            step['sequencePending'] = previous
    return saved


def play_sequence_ready(step, now, play_state, observed_round, input_free, press,
                        persist=lambda: True, report=lambda message: None,
                        observe=None, sleep=None, clock=None):
    """Observe the first transition before the second input; never repeat either.

    With a native observation callback, the first input is followed by the
    source's 0.2-second delay and a fresh screen before issuing input two. A
    process interruption resumes the saved phase from actual screen evidence.
    Missing transition evidence retains the action, not another blind toggle.
    """
    if step.get('action') != 'play_twice':
        raise ValueError('Play sequence needs play_twice')
    if type(now) not in (int, float) or not isfinite(now):
        raise ValueError('Play sequence clock must be finite')
    if not input_free or play_state not in ('paused', 'slow', 'fast'):
        return False, False
    if type(observed_round) is not int or observed_round < 1 or step.get('key') is None:
        return False, False
    pending = step.get('sequencePending')
    if pending is not None:
        restore_play_sequence(step, step)
        if pending['sentAt'] > now:
            old = deepcopy(pending); pending['sentAt'] = now
            persist_intent(step, old, persist, report)
            return False, False
        if pending['phase'] == 'second':
            target = 'fast' if pending['firstState'] == 'slow' else 'slow'
            if now >= pending['sentAt'] + 1 and play_state == target:
                step['playStateConfirmed'] = True
                step['speed'] = target
                return True, False
            report('PLAY_SEQUENCE retaining second receipt; awaiting final speed transition')
            return False, False
        first_confirmed = (play_state in ('slow', 'fast') if pending['from'] == 'paused'
                           else play_state == ('fast' if pending['from'] == 'slow' else 'slow'))
        if now < pending['sentAt'] + 0.2 or not first_confirmed:
            report('PLAY_SEQUENCE retaining first receipt; awaiting first speed transition')
            return False, False
        old = deepcopy(pending)
        step['sequencePending'] = dict(pending, phase='second', firstState=play_state, sentAt=now)
        if not persist_intent(step, old, persist, report):
            report('PLAY_SEQUENCE second intent not saved; withholding input')
            return False, False
        press(step['key'])
        report('PLAY_SEQUENCE input two issued from observed=' + play_state)
        return False, True
    step['sequencePending'] = {'phase': 'first', 'from': play_state, 'sentAt': now, 'round': observed_round}
    if not persist_intent(step, None, persist, report):
        report('PLAY_SEQUENCE first intent not saved; withholding input')
        return False, False
    press(step['key'])
    report('PLAY_SEQUENCE input one issued from=' + play_state)
    if observe is not None and sleep is not None and clock is not None:
        sleep(0.2)
        fresh = observe()
        if isinstance(fresh, dict) and fresh.get('foreground') is True:
            play_sequence_ready(step, clock(), fresh.get('state'), fresh.get('round'), True,
                                press, persist, report)
    return False, True
