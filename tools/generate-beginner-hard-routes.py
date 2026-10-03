"""Create map-specific Hard Standard routes from one documented Beginner-map build.

The published build is Sauda, 0-2-4 Wizard, 0-2-4 Sniper, 0-2-4 Dart, and
2-4-0 Druid. Placement points are drawn only from existing routes for the same
map and normalized to the 1920x1080 route coordinate system. Each generated
file is hashed into route-library/metadata/online-guide-sources.json so source
verification is invalidated if someone edits the actions.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAYTHROUGHS = ROOT / "autobtd6" / "playthroughs"
MAPS = json.loads((ROOT / "autobtd6" / "maps.json").read_text(encoding="utf-8"))
CATALOG = (ROOT / "map-catalog.js").read_text(encoding="utf-8")
SOURCE_URL = "https://www.reddit.com/r/btd6/comments/1j9511e/almost_foolproof_strategy_for_beginner_maps/"
METADATA_PATH = ROOT / "route-library" / "metadata" / "online-guide-sources.json"
BUILD = ("dart", "wizard", "sniper", "druid")


def slug_for(name):
    normalized = re.sub(r"[^a-z0-9]", "", name.lower())
    return next((slug for slug, item in MAPS.items()
                 if re.sub(r"[^a-z0-9]", "", item.get("name", slug).lower()) == normalized), None)


def read_map_points(map_slug):
    points = []
    for path in sorted(PLAYTHROUGHS.glob(f"{map_slug}#*.btd6")):
        parts = path.name[:-5].split("#")
        resolution = parts[2] if len(parts) > 2 else "1920x1080"
        sx, sy = (0.75, 0.75) if resolution == "2560x1440" else (1.0, 1.0)
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            match = re.match(r"place\s+([a-z_]+)\s+(\w+)\s+at\s+(\d+),\s*(\d+)$", line)
            if not match:
                continue
            tower, name, x, y = match.groups()
            x, y = round(int(x) * sx), round(int(y) * sy)
            if not (20 <= x <= 1900 and 20 <= y <= 1060):
                continue
            point = (x, y)
            if all((x - px) ** 2 + (y - py) ** 2 >= 72 ** 2 for px, py, *_ in points):
                points.append((x, y, tower, name))
    return points


def choose_points(points):
    if len(points) < 5:
        raise ValueError(f"need five distinct map positions, found {len(points)}")
    selected = []

    def take(predicate):
        for point in points:
            if predicate(point) and point not in selected:
                selected.append(point)
                return point
        for point in points:
            if point not in selected:
                selected.append(point)
                return point
        raise ValueError("not enough distinct placement points")

    hero = take(lambda p: p[2] in {"sauda", "quincy", "gwendolin", "obyn_greenfoot"})
    sniper = take(lambda p: p[2] == "sniper")
    wizard = take(lambda p: p[2] == "wizard")
    dart = take(lambda p: p[2] == "dart")
    druid = take(lambda p: p[2] == "druid")
    return hero, wizard, sniper, dart, druid


def upgrade_lines(name, path, count):
    return [f"upgrade {name} path {path}" for _ in range(count)]


def build_route(hero, wizard, sniper, dart, druid):
    # A cheap Dart opener covers the gap before Sauda's Hard-mode price is met.
    lines = [
        "round 3", f"place dart dart0 at {dart[0]}, {dart[1]}",
        "round 6", f"place sauda hero0 at {hero[0]}, {hero[1]}",
        "round 10", f"place wizard wizard0 at {wizard[0]}, {wizard[1]}",
    ]
    # Early camo/lead coverage, followed by the source's full crosspaths.
    lines += upgrade_lines("wizard0", 2, 2)
    lines += ["round 24"] + upgrade_lines("wizard0", 2, 1)
    lines += upgrade_lines("wizard0", 1, 2)
    lines += upgrade_lines("wizard0", 2, 1)
    lines += ["round 30", f"place sniper sniper0 at {sniper[0]}, {sniper[1]}"]
    lines += upgrade_lines("sniper0", 2, 2) + upgrade_lines("sniper0", 2, 2)
    lines += ["round 45"] + upgrade_lines("dart0", 1, 2) + upgrade_lines("dart0", 2, 4)
    lines += ["round 55", f"place druid druid0 at {druid[0]}, {druid[1]}"]
    lines += upgrade_lines("druid0", 0, 2) + upgrade_lines("druid0", 1, 4)
    return "\n".join(lines) + "\n"


def main():
    category = re.search(r'"Beginner"\s*:\s*\[([^\]]+)\]', CATALOG, re.S)
    if not category:
        raise RuntimeError("could not read Beginner map catalog")
    names = re.findall(r'"([^"]+)"', category.group(1))
    try:
        metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        metadata = {}
    added, skipped = [], {}
    for name in names:
        map_slug = slug_for(name)
        if not map_slug:
            skipped[name] = "map slug not found"
            continue
        filename = f"{map_slug}#hard#1920x1080#guide#beginner-hard.btd6"
        try:
            hero, wizard, sniper, dart, druid = choose_points(read_map_points(map_slug))
        except ValueError as error:
            skipped[map_slug] = str(error)
            continue
        content = build_route(hero, wizard, sniper, dart, druid)
        (PLAYTHROUGHS / filename).write_text(content, encoding="utf-8")
        metadata[filename] = {
            "source": SOURCE_URL,
            "sourceMode": "hard",
            "routeHash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "sourceClaimsWin": True,
            "notes": "Adapted published Beginner-map strategy (Sauda, 0-2-4 Wizard, 0-2-4 Sniper, 0-2-4 Dart, 2-4-0 Druid). Positions come from existing routes on this same map. Source reports the build across Beginner maps; this exact placement/timing has not been locally replayed.",
        }
        added.append(filename)
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    METADATA_PATH.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"created": len(added), "skipped": skipped, "files": added}, indent=2))


if __name__ == "__main__":
    main()
