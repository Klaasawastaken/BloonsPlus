"""Reconcile saved upgrade intent without repeating tower placements."""
from copy import deepcopy
from upgrade_observation import read_upgrade_panel


def restore_upgrade_steps(original, checkpoint):
    offset = checkpoint['nextStep']
    pending = {}
    for entry in checkpoint.get('unresolvedUpgrades', []):
        match = next((step for step in original
                      if step.get('action') == 'upgrade'
                      and step.get('name') == entry.get('name')
                      and step.get('expectedUpgradeTiers') == entry.get('expectedUpgradeTiers')), None)
        if match is None:
            raise ValueError('unresolved upgrade does not match the recorded route')
        step = deepcopy(match)  # Reuse current parsed keybinds, prices and route metadata.
        position = entry.get('pos')
        if isinstance(position, (list, tuple)) and len(position) == 2:
            step['pos'] = list(position)
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
        if type(index) is not int or not 0 <= index < len(original):
            raise ValueError('checkpoint action lacks a valid route position')
        source = original[index]
        if step.get('action') != source.get('action') or step.get('name') != source.get('name'):
            raise ValueError('checkpoint action differs from recorded route')
        if index not in pending:
            restored.append(deepcopy(step))
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
