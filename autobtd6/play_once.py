"""Observed single Play input, distinct from requesting an absolute speed."""
from copy import deepcopy
from math import isfinite


def restore_play_once(source, saved):
    if source.get('action') != 'play_once' or saved.get('action') != 'play_once':
        raise ValueError('single Play checkpoint differs from source')
    step=deepcopy(source)
    pending=saved.get('playOncePending')
    if pending is not None:
        if (not isinstance(pending,dict) or pending.get('from') not in ('paused','slow','fast')
                or type(pending.get('sentAt')) not in (int,float) or not isfinite(pending['sentAt'])
                or type(pending.get('round')) is not int or pending['round'] < 1):
            raise ValueError('invalid single Play checkpoint')
        step['playOncePending']={key:pending[key] for key in ('from','sentAt','round')}
    return step


def play_once_ready(step, now, play_state, observed_round, input_free, press,
                    persist=lambda:True, report=lambda message:None):
    """Send one key, then require evidence before allowing the next command.

    A pending receipt is never blindly replayed after a process restart. A
    paused-origin command may already have finished a short round before the
    next frame, so a fresh higher round also confirms that transition. Running
    origins require the opposite speed, not mere ongoing round progression.
    """
    if step.get('action') != 'play_once':
        raise ValueError('single Play controller needs play_once')
    if type(now) not in (int,float) or not isfinite(now):
        raise ValueError('single Play clock must be finite')
    if not input_free or play_state not in ('paused','slow','fast'):
        return False,False
    if type(observed_round) is not int or observed_round < 1:
        return False,False
    pending=step.get('playOncePending')
    if pending is not None:
        restore_play_once(step,step)
        if pending['sentAt'] > now:
            old=pending['sentAt'];pending['sentAt']=now
            if persist() is not True:pending['sentAt']=old
            return False,False
        if now-pending['sentAt'] < 1:
            return False,False
        origin=pending['from']
        confirmed=(play_state==('fast' if origin=='slow' else 'slow') if origin!='paused'
                   else play_state in ('fast','slow') or observed_round>pending['round'])
        if confirmed:
            step['playStateConfirmed']=True
            step['speed']=play_state if play_state in ('slow','fast') else None
            return True,False
        report('PLAY_ONCE awaiting observed transition; retaining command without another key')
        return False,False
    if step.get('key') is None:
        report('PLAY_ONCE Play/Fast Forward is unbound; withholding input')
        return False,False
    step['playOncePending']={'from':play_state,'sentAt':now,'round':observed_round}
    if persist() is not True:
        step.pop('playOncePending',None)
        report('PLAY_ONCE checkpoint not saved; withholding input')
        return False,False
    press(step['key'])
    report('PLAY_ONCE input issued from='+play_state+' round='+str(observed_round))
    return False,True
