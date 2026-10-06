"""Reconcile saved upgrade intent without repeating tower placements."""
from copy import deepcopy
from math import isfinite
from upgrade_observation import read_upgrade_panel
from autostart_control import restore_autostart_pending


def resumable_round_start(checkpoint):
    """Admit an observed round control, never an ambiguous pending purchase."""
    if (not isinstance(checkpoint, dict) or checkpoint.get('status') != 'pending'
            or checkpoint.get('pendingAction') not in ('start_round', 'speed_toggle')):
        return False
    remaining = checkpoint.get('remainingSteps')
    offset = checkpoint.get('nextStep')
    if (type(offset) is not int or offset < 0 or not isinstance(remaining, list)
            or not remaining or not isinstance(remaining[0], dict)):
        return False
    step = remaining[0]
    relative = step.get('action') == 'speed_toggle'
    pending = step.get('roundStartPending')
    if relative and (not isinstance(pending, dict)
                     or pending.get('from') not in ('paused', 'fast', 'slow')
                     or step.get('speedToggleFrom') not in ('paused', 'fast', 'slow')
                     or step.get('speed') != ('fast' if step['speedToggleFrom'] == 'slow' else 'slow')):
        return False
    return (step.get('action') == checkpoint['pendingAction'] and step.get('speed') in ('fast', 'slow')
            and type(step.get('routeStepIndex')) is int
            and step['routeStepIndex'] == offset)


def restore_action(source, saved):
    """Keep current parsed inputs/economy, retaining only recovery state."""
    step = restore_autostart_pending(source, saved) if source.get('action') == 'set_autostart' else deepcopy(source)
    if source.get('action') == 'speed_toggle':
        pending = saved.get('roundStartPending')
        if pending is not None:
            if (not isinstance(pending, dict) or pending.get('from') not in ('paused', 'fast', 'slow')
                    or type(pending.get('sentAt')) not in (int, float) or not isfinite(pending['sentAt'])
                    or saved.get('speedToggleFrom') not in ('paused', 'fast', 'slow')
                    or saved.get('speed') != ('fast' if saved['speedToggleFrom'] == 'slow' else 'slow')):
                raise ValueError('invalid checkpoint relative speed intent')
            step['speed'] = saved['speed']
            step['speedToggleFrom'] = saved['speedToggleFrom']
            step['roundStartPending'] = {'from': pending['from'], 'sentAt': pending['sentAt']}
    if source.get('action') == 'start_round' and saved.get('speed') == source.get('speed'):
        pending = saved.get('roundStartPending')
        if pending is not None:
            if (not isinstance(pending, dict) or pending.get('from') not in ('paused', 'fast', 'slow')
                    or type(pending.get('sentAt')) not in (int, float) or not isfinite(pending['sentAt'])):
                raise ValueError('invalid checkpoint round start')
            step['roundStartPending'] = {'from': pending['from'], 'sentAt': pending['sentAt']}
    if source.get('action') == 'await_delay' and saved.get('seconds') == source.get('seconds'):
        deadline = saved.get('delayDeadline')
        if deadline is not None:
            if type(deadline) not in (int, float) or not isfinite(deadline):
                raise ValueError('invalid checkpoint delay deadline')
            step['delayDeadline'] = deadline
    if source.get('action') == 'ability' and saved.get('timer', 0) == source.get('timer', 0):
        deadline = saved.get('abilityDeadline')
        if deadline is not None:
            if type(deadline) not in (int, float) or not isfinite(deadline):
                raise ValueError('invalid checkpoint ability deadline')
            step['abilityDeadline'] = deadline
    if source.get('action') == 'ability' and saved.get('abilityInputSent') is True:
        same_intent = (saved.get('key') == source.get('key')
                       and saved.get('timer', 0) == source.get('timer', 0)
                       and saved.get('cursor_delay', 0) == source.get('cursor_delay', 0)
                       and isinstance(saved.get('pos'), (list, tuple))
                       and isinstance(source.get('pos'), (list, tuple))
                       and list(saved['pos']) == list(source['pos']))
        if same_intent:
            deadline = saved.get('cursorDeadline')
            if type(deadline) not in (int, float) or not isfinite(deadline):
                raise ValueError('invalid checkpoint ability cursor deadline')
            step['abilityInputSent'] = True
            step['cursorDeadline'] = deadline
    if source.get('action') == 'upgrade' and 'deferredUpgradeRound' in saved:
        target = saved['deferredUpgradeRound']
        if type(target) is not int or target < 1:
            raise ValueError('invalid checkpoint upgrade deferral')
        step['deferredUpgradeRound'] = target
    for key in ('pos', 'originPos'):
        position = saved.get(key)
        if position is not None:
            if (not isinstance(position, (list, tuple)) or len(position) != 2
                    or any(type(v) not in (int, float) or not isfinite(v) for v in position)):
                raise ValueError('invalid checkpoint action position')
            step[key] = list(position)
    for key in ('selectionAttempts', 'placeAttempts'):
        if key in saved:
            if type(saved[key]) is not int or saved[key] < 0:
                raise ValueError('invalid checkpoint retry count')
            step[key] = saved[key]
    if saved.get('resumeUpgradeProbe') is True:
        step['resumeUpgradeProbe'] = True
    return step


def restore_upgrade_steps(original, checkpoint):
    if not isinstance(checkpoint, dict) or not isinstance(original, list):
        raise ValueError('invalid checkpoint recovery data')
    offset = checkpoint.get('nextStep')
    if type(offset) is not int or not 0 <= offset <= len(original):
        raise ValueError('invalid checkpoint step')
    unresolved = checkpoint.get('unresolvedUpgrades', [])
    if not isinstance(unresolved, list) or any(not isinstance(entry, dict) for entry in unresolved):
        raise ValueError('invalid checkpoint unresolved upgrades')
    pending = {}
    for entry in unresolved:
        if entry.get('opportunistic') is True:
            # Supplemental spending is recalculated from the restored ledger
            # and live tiers/cash; it is not an instruction in the recording.
            continue
        match = next((step for step in original
                      if step.get('action') == 'upgrade'
                      and step.get('name') == entry.get('name')
                      and step.get('expectedUpgradeTiers') == entry.get('expectedUpgradeTiers')), None)
        if match is None:
            raise ValueError('unresolved upgrade does not match the recorded route')
        step = restore_action(match, entry)
        step['resumeUpgradeProbe'] = True
        pending[step['routeStepIndex']] = step
    restored = [pending[index] for index in sorted(pending)]
    remaining = checkpoint.get('remainingSteps', original[offset:])
    if not isinstance(remaining, list):
        raise ValueError('invalid checkpoint action queue')
    seen_indices = set()
    for step in remaining:
        if not isinstance(step, dict):
            raise ValueError('invalid checkpoint action')
        index = step.get('routeStepIndex')
        extra = step.get('extra', {})
        if not isinstance(extra, dict):
            raise ValueError('invalid checkpoint action metadata')
        if index is None and step.get('action') == 'upgrade' and extra.get('opportunistic'):
            # The surplus planner re-evaluates current cash and the restored
            # tower ledger. Its temporary plans are not recorded route steps.
            continue
        if type(index) is not int or not 0 <= index < len(original):
            raise ValueError('checkpoint action lacks a valid route position')
        if index in seen_indices:
            raise ValueError('checkpoint repeats a recorded action')
        seen_indices.add(index)
        source = original[index]
        if step.get('action') != source.get('action') or step.get('name') != source.get('name'):
            raise ValueError('checkpoint action differs from recorded route')
        if index not in pending:
            restored.append(restore_action(source, step))
    return restored


def probe_owned_upgrade(target, capture, select, wait):
    """Only select/read. Never send an upgrade hotkey or purchase click."""
    for _ in range(2):
        select()
        wait(1.0)
        panel = read_upgrade_panel(capture())
        if panel is not None:
            tiers = panel['tiers']
            owned = len(target) == 3 and all(a >= t for a, t in zip(tiers, target))
            return dict(status='confirmed' if owned else 'needed', before=tiers,
                        after=tiers, buttonRetry=False, inputMethod='resume-probe')
    return dict(status='unselected', before=None, after=None, buttonRetry=False,
                inputMethod='resume-probe')
