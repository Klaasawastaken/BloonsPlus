"""Pure path legality checks for upgrades to an ordinary three-path tower."""


def can_upgrade_path(levels, path):
    """Return whether one more tier preserves the normal tower crosspath rules.

    This checks tier structure only. Affordability, unlocks, special tower rules,
    and the game's one-per-type tier-five limit need separate observations.
    The caller's levels are never changed.
    """
    if type(path) is not int or not 0 <= path < 3:
        return False
    if not isinstance(levels, (list, tuple)) or len(levels) != 3:
        return False
    if any(type(level) is not int or not 0 <= level <= 5 for level in levels):
        return False
    proposed = list(levels)
    proposed[path] += 1
    return (
        proposed[path] <= 5
        and sum(level > 0 for level in proposed) <= 2
        and sum(level > 2 for level in proposed) <= 1
    )


def can_upgrade_in_roster(levels, path, tower_type, roster, *, double_cross=False):
    """Include active tier-five limits when extending a confirmed tower build."""
    if not can_upgrade_path(levels, path):
        return False
    if levels[path] != 4:
        return True
    if not isinstance(roster, dict):
        return False
    limit = 2 if tower_type == 'dart' and path == 2 and double_cross is True else 1
    owned = 0
    for tower in roster.values():
        if not isinstance(tower, dict):
            return False
        if tower.get('type') != tower_type:
            continue
        tiers = tower.get('upgrades')
        if (not isinstance(tiers, (list, tuple)) or len(tiers) != 3
                or any(type(tier) is not int or not 0 <= tier <= 5 for tier in tiers)):
            return False
        owned += tiers[path] == 5
    return owned < limit


def read_upgrade_caps(encoded):
    """Validate an optional read-only profile snapshot without game imports."""
    import json
    try:
        caps = json.loads(encoded)
    except (ValueError, TypeError):
        return None
    if not isinstance(caps, dict):
        return None
    if any(not isinstance(name, str) or not isinstance(tiers, list) or len(tiers) != 3
           or any(type(tier) is not int or not 0 <= tier <= 5 for tier in tiers)
           for name, tiers in caps.items()):
        return None
    return caps
