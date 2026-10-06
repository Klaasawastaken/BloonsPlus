"""Read same-tower route coordinates as hints, never as placement confirmation."""
from functools import lru_cache
from pathlib import Path
import re


@lru_cache(maxsize=128)
def route_placement_hints(directory, map_name, footprint):
    if not re.fullmatch(r'[a-z0-9_]+', str(map_name)):
        return ()
    parts = str(footprint).split(':')
    if len(parts) not in (2, 3) or len(parts) == 3 and parts[1] != 'hero':
        return ()
    kind = parts[-1]
    if not re.fullmatch(r'[a-z0-9_]+', kind):
        return ()
    hints = {}
    for file in sorted(Path(directory).glob(str(map_name) + '#*.btd6')):
        fields = file.stem.split('#')
        resolution = re.fullmatch(r'(\d+)x(\d+)', fields[2]) if len(fields) > 2 else None
        if not resolution:
            continue
        width, height = map(int, resolution.groups())
        if width <= 0 or height <= 0 or abs(height / width - 9 / 16) > .02:
            continue
        try:
            lines = file.read_text(encoding='utf-8').splitlines()
        except (OSError, UnicodeError):
            continue
        for line in lines:
            match = re.match(r'^place\s+(\w+)\s+\w+\s+at\s+(\d+),\s*(\d+)(?:\s|$)', line.strip())
            if not match or match[1].lower() != kind:
                continue
            x, y = int(match[2]), int(match[3])
            if not (0 <= x < width and 0 <= y < height):
                continue
            point = (round(x * 1920 / width), round(y * 1080 / height))
            hints.setdefault(point, file.name)
    return tuple((point, source) for point, source in hints.items())
