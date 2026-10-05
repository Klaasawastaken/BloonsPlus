"""Reconcile saved upgrade intent without repeating tower placements."""
from copy import deepcopy
from math import isfinite
from upgrade_observation import read_upgrade_panel


def restore_action(source, saved):
    """Keep current parsed inputs/economy, retaining only recovery state."""
    step = deepcopy(source)
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
    offset = checkpoint['nextStep']
    pending = {}
    for entry in checkpoint.get('unresolvedUpgrades', []):
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
    for step in remaining:
        if not isinstance(step, dict):
            raise ValueError('invalid checkpoint action')
        index = step.get('routeStepIndex')
        if index is None and step.get('action') == 'upgrade' and step.get('extra', {}).get('opportunistic'):
            # The surplus planner re-evaluates current cash and the restored
            # tower ledger. Its temporary plans are not recorded route steps.
            continue
        if type(index) is not int or not 0 <= index < len(original):
            raise ValueError('checkpoint action lacks a valid route position')
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
