"""Map-specific availability predictions; never infer a successful input."""


def predicted_thaw_round(map_name, tower_name, tower_type, events, current_round):
    """Glacial Trail freezes for rounds placement+9/+10, then repeats every ten.

    This is a prediction used only after an unavailable upgrade observation.
    Missing placement history, sold towers and immune Ice monkeys stay unknown.
    Source: https://bloons.fandom.com/wiki/Glacial_Trail
    """
    if map_name != 'glacial_trail' or type(current_round) is not int or current_round < 1:
        return None
    if not isinstance(tower_type, str) or not tower_type:
        return None
    if tower_type.lower().replace('_', '').replace(' ', '') in ('ice', 'icemonkey', 'icetower', 'silas'):
        return None
    for event in reversed(events or []):
        if event.get('tower') != tower_name:
            continue
        if event.get('type') == 'sell':
            return None
        if event.get('type') != 'place' or event.get('status') not in ('cash-confirmed', 'panel-tier-confirmed', 'visual-confirmed'):
            continue
        placed = event.get('round')
        if type(placed) is not int or placed < 1 or current_round - placed < 9:
            return None
        phase = (current_round - placed) % 10
        return current_round + (2 if phase == 9 else 1) if phase in (9, 0) else None
    return None
