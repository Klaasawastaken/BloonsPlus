"""Bounded income recovery when a manual source clock outruns a paused game."""
from copy import deepcopy
from math import isfinite
from play_once import play_once_ready, restore_play_once


def restore_manual_cash_recovery(saved, first):
    if saved is None:
        return None
    if not isinstance(saved, dict):
        raise ValueError('invalid manual cash recovery checkpoint')
    state = deepcopy(saved)
    if (type(state.get('owner')) is not int
            or type(state.get('attempts')) is not int or not 0 <= state['attempts'] <= 3):
        raise ValueError('manual cash recovery differs from queued purchase')
    if not isinstance(first, dict) or state['owner'] != first.get('routeStepIndex'):
        if state.get('receipt'):
            raise ValueError('pending manual recovery lost its purchase owner')
        return None
    for field in ('watchRound', 'lastStartedRound'):
        if field in state and (type(state[field]) is not int or not 1 <= state[field] <= 200):
            raise ValueError('invalid manual recovery round')
    if 'watchAt' in state and (type(state['watchAt']) not in (int, float) or not isfinite(state['watchAt'])):
        raise ValueError('invalid manual recovery clock')
    if state.get('receipt') is not None:
        state['receipt'] = restore_play_once({'action': 'play_once'}, state['receipt'])
        if state['receipt'].get('playOncePending', {}).get('from') != 'paused':
            raise ValueError('manual cash recovery must originate from a paused game')
    return state


def drive_manual_cash_recovery(config, now, play_state, observed_round, cash, input_free,
                              key, press, persist=lambda: True, report=lambda message: None):
    """Own the frame while confirming one income-start input, never a purchase.

    Preserve the source commands and logical clock. A ten-second, repeated
    paused cash shortage may start one observed round only when the source
    logical round is ahead. Three distinct starts bound one queued purchase.
    """
    first = next(iter(config.get('steps', [])), None)
    if (not first or not config.get('sourceRoundTiming') or config.get('autostartEnabled') is not False
            or config.get('gamemode') == 'deflation' or not input_free
            or play_state not in ('paused', 'fast', 'slow')
            or type(observed_round) is not int or not 1 <= observed_round <= 200
            or type(now) not in (int, float) or not isfinite(now) or key is None):
        previous = config.get('manualCashRecovery')
        if isinstance(previous, dict) and not previous.get('receipt') and 'watchAt' in previous:
            previous.pop('watchAt', None)
            previous.pop('watchRound', None)
            persist()
        return False
    existing = config.get('manualCashRecovery')
    if existing and existing.get('owner') != first.get('routeStepIndex'):
        if existing.get('receipt'):
            raise ValueError('pending manual recovery lost its purchase owner')
        config.pop('manualCashRecovery', None)
        existing = None
    state = restore_manual_cash_recovery(existing, first) if existing else {
        'owner': first.get('routeStepIndex'), 'attempts': 0, 'receipt': None}

    def save():
        old = deepcopy(config.get('manualCashRecovery'))
        config['manualCashRecovery'] = deepcopy(state)
        try:
            success = persist() is True
        except Exception:
            success = False
        if not success:
            if old is None:
                config.pop('manualCashRecovery', None)
            else:
                config['manualCashRecovery'] = old
        return success

    if state.get('receipt'):
        receipt = state['receipt']
        receipt['key'] = key  # Rebind to the actual saved game binding on resume.
        ready, _ = play_once_ready(receipt, now, play_state, observed_round, input_free,
                                  press, save, report)
        if ready:
            state['lastStartedRound'] = receipt['playOncePending']['round']
            state['receipt'] = None
            state.pop('watchAt', None)
            state.pop('watchRound', None)
            if save():
                report('MANUAL_CASH_RECOVERY confirmed income round start; original purchase remains queued')
        return True

    logical = (config.get('sourceRoundContext') or {}).get('round')
    cost = first.get('cost')
    if (play_state != 'paused' or first.get('action') not in ('place', 'upgrade')
            or type(first.get('routeStepIndex')) is not int
            or type(logical) is not int or logical <= observed_round
            or type(cash) not in (int, float) or not isfinite(cash) or cash < 0
            or type(cost) not in (int, float) or not isfinite(cost) or not 0 <= cash < cost
            or state['attempts'] >= 3 or state.get('lastStartedRound') == observed_round):
        if 'watchAt' in state:
            state.pop('watchAt', None)
            state.pop('watchRound', None)
            save()
        return False
    if ('watchAt' not in state or state.get('watchRound') != observed_round or state['watchAt'] > now):
        state.update(watchRound=observed_round, watchAt=now)
        save()
        return False
    if now - state['watchAt'] < 10:
        return False
    state['attempts'] += 1
    state['receipt'] = {'action': 'play_once', 'key': key}
    _, issued = play_once_ready(state['receipt'], now, play_state, observed_round, input_free,
                               press, save, report)
    if issued:
        report('MANUAL_CASH_RECOVERY paused round=' + str(observed_round) + ' source=' + str(logical)
               + ' cash=' + str(cash) + ' required=' + str(cost) + '; one bounded income-start input')
    return issued
