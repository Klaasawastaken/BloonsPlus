"""Advisory hero-picker locations; cached positions never prove selection."""
import json
import os
import tempfile


def read_memory(path):
    try:
        with open(path, encoding='utf-8') as file:
            value = json.load(file)
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def valid_hint(hint, resolution, slots):
    if not isinstance(hint, dict) or type(hint.get('page')) is not int or not 0 <= hint['page'] < 5:
        return None
    if (not isinstance(resolution, (list, tuple)) or len(resolution) != 2
            or any(type(value) is not int or value <= 0 for value in resolution)
            or not isinstance(slots, (list, tuple))
            or any(not isinstance(point, (list, tuple)) or len(point) != 2
                   or any(type(value) is not int for value in point) for point in slots)):
        return None
    expected = [list(point) for point in slots]
    if hint.get('resolution') != list(resolution) or hint.get('slots') != expected:
        return None
    point = hint.get('position')
    if (not isinstance(point, (list, tuple)) or len(point) != 2
            or any(type(value) is not int for value in point) or list(point) not in expected):
        return None
    return {'page': hint['page'], 'position': list(point),
            'resolution': list(resolution), 'slots': expected}


def lookup_hint(memory, hero, resolution, slots):
    hints = memory.get('pickerHints') if isinstance(memory, dict) else None
    return valid_hint(hints.get(hero), resolution, slots) if isinstance(hints, dict) else None


def save_selection(path, hero, updated_at, hint=None):
    """Save only after live selection confirmation; preserve older advisory hints."""
    memory = read_memory(path)
    hints = memory.get('pickerHints', {})
    hints = dict(hints) if isinstance(hints, dict) else {}
    if isinstance(hint, dict):
        resolution, slots = hint.get('resolution'), hint.get('slots')
        if (isinstance(resolution, (list, tuple)) and len(resolution) == 2
                and all(type(value) is int and value > 0 for value in resolution)
                and isinstance(slots, list)):
            checked = valid_hint(hint, resolution, slots)
            if checked is not None:
                hints[hero] = checked
    directory = os.path.dirname(os.path.abspath(path))
    descriptor, temporary = tempfile.mkstemp(prefix='hero-picker-', suffix='.tmp', dir=directory)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as file:
            json.dump({'hero': hero, 'updatedAt': updated_at, 'pickerHints': hints}, file)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
