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
