"""Create cautious Bloons+ draft routes from simple BTD6bot plans.

This extracts literal Monkey/Hero placements and upgrade targets only. Dynamic
round logic, abilities, removals, and map-specific events stay out of the draft.
Output is tagged "hard" (never a MODES_REQUIRING_VERIFIED_ROUTE mode) and
"converted" (not "generated"), so it's a real, immediately usable candidate for
the sweep/specific-map picker the same way other BTD6bot conversions already
are (automation.js's getRecordedCombos only excludes "generated" files; a
"converted" one with no contradicting online guide is trusted by default,
same as every other converted plan) - just never eligible for the restricted
special modes (chimps, impoppable, etc.) without a separate confirmed win.
"""
import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "btd6bot" / "btd6bot" / "plans"
OUT = ROOT / "autobtd6" / "playthroughs"
# BTD6bot's plan-filename suffix -> the real Bloons+ gamemode slug (as MODES_REQUIRING_VERIFIED_ROUTE
# and every other route filename in autobtd6/playthroughs already spell it) plus which difficulty
# tier tag to write for a plain Standard plan. Every suffix maps to exactly one real gamemode; the
# "Standard" ones are the three plain difficulties, everything else is a special/restricted mode.
_MODE_SUFFIX_TO_GAMEMODE = {
    "EasyStandard": "easy", "MediumStandard": "medium", "HardStandard": "hard",
    "HardChimps": "chimps", "HardImpoppable": "impoppable",
    "EasyPrimary": "primary_only", "EasyDeflation": "deflation",
    "MediumMilitary": "military_only", "MediumApopalypse": "apopalypse",
    "HardAlternate": "alternate_bloons_rounds", "HardReverse": "reverse",
    "HardApopalypse": "apopalypse", "HardMagic": "magic_monkeys_only",
    "HardDoubleHp": "double_hp_moabs", "HardHalfCash": "half_cash",
}
def _map_slug_from_plan(stem):
    for suffix in _MODE_SUFFIX_TO_GAMEMODE:
        if stem.endswith(suffix):
            return stem[: -len(suffix)], suffix
    return None, None
def _normalize(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())
REAL_MAPS = json.loads((ROOT / "autobtd6" / "maps.json").read_text(encoding="utf-8"))
_REAL_SLUG_BY_NORM = {_normalize(slug): slug for slug in REAL_MAPS}
def _real_slug(raw_slug):
    # btd6bot's own plan filenames spell a few slugs differently from AutoBTD6's
    # maps.json (apostrophes, missing underscores, etc.) - match on normalized
    # form so the draft lands on the map it's actually for, not an orphan slug
    # sweepCandidates() will never look up.
    return _REAL_SLUG_BY_NORM.get(_normalize(raw_slug))
# A prior session already tried converting these maps' BTD6bot plans and found the source itself
# broken (duplicate/looping constructor matches producing corrupt drafts - "monkey X placed twice"
# at runtime) - see route-library/unsupported-conversions/. The regex-based extractor below has no
# way to detect that on its own, so skip these maps entirely rather than re-generate known-bad output.
_KNOWN_BROKEN_PLAN_SLUGS = {"#ouch", "skull_tweak", "three_mines_'round", "tricky_tracks"}
# One (real map slug, real gamemode slug) -> plan file, for every plan BTD6bot ships. A map/mode
# with several plans (e.g. multiple HardChimps drafts) keeps only the first alphabetically - matches
# the old choose_plan()'s "first sorted match wins" behavior.
TARGETS = {}
_CHIMPS_PLAN_BY_SLUG = {}
for path in sorted(PLANS.glob("*.py")):
    if path.stem in {"__init__", "_plan_imports"}: continue
    raw_slug, suffix = _map_slug_from_plan(path.stem)
    if not raw_slug or raw_slug in _KNOWN_BROKEN_PLAN_SLUGS: continue
    slug = _real_slug(raw_slug)
    if not slug: continue
    gamemode = _MODE_SUFFIX_TO_GAMEMODE[suffix]
    TARGETS.setdefault((slug, gamemode), path)
    if suffix == "HardChimps": _CHIMPS_PLAN_BY_SLUG.setdefault(slug, path)
# Every map has a HardChimps plan (86/86), but very few have a dedicated HardStandard/EasyStandard/
# MediumStandard one. A CHIMPS build's economy is strictly harder than Hard's (see HARD_REUSE_MODES
# in automation.js for the same logic run the other direction on the runtime side), so fall back to
# it for "hard" wherever a map has no plan of its own - this is what gets every map a "hard" route.
for slug, plan in _CHIMPS_PLAN_BY_SLUG.items():
    TARGETS.setdefault((slug, "hard"), plan)
TOWER_ALIASES = {
    "boomer": "boomerang", "boat": "buccaneer", "alch": "alchemist",
    "ace_wing": "ace", "spike_factory": "spike",
}
HERO_ALIASES = {
    "gwen": "gwendolin", "obyn": "obyn_greenfoot", "pat": "pat_fusty",
    "jones": "striker_jones", "churchill": "captain_churchill",
    "brickell": "admiral_brickell",
}
TOWER_DATA = json.loads((ROOT / "autobtd6" / "towers.json").read_text(encoding="utf-8"))
VALID_TOWERS = set(TOWER_DATA.get("monkeys", {}))
VALID_HEROES = set(TOWER_DATA.get("heros", {}))

def legal_upgrade_path(levels):
    return max(levels, default=0) <= 5 and sum(level > 2 for level in levels) <= 1 and sum(level > 0 for level in levels) <= 2

def normalize_hero(name):
    key = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    key = HERO_ALIASES.get(key, key)
    return key if key in VALID_HEROES else None

def convert(path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    hero_match = re.search(r"^\s*\[Hero\]\s*(.*?)\s*$", text, re.IGNORECASE | re.MULTILINE)
    hero_type = normalize_hero(hero_match.group(1)) if hero_match and hero_match.group(1) != "-" else None
    entries = {}
    aliases = {}
    # BTD6bot uses normalized coordinates in Monkey/Hero constructors. Keep
    # the source variable so later ``engi.upgrade(...)`` calls survive.
    ctor = re.compile(
        r"(?:(?P<var>[A-Za-z_]\w*)\s*=\s*)?(?P<kind>Monkey|Hero)\(\s*"
        r"(?:[\"'](?P<tower>[a-z_]+)[\"']\s*,\s*)?"
        r"(?P<x>[0-9.]+)\s*,\s*(?P<y>[0-9.]+)"
    )
    for match in ctor.finditer(text):
        kind, raw_tower = match.group("kind"), match.group("tower")
        if kind == "Hero":
            if not hero_type:
                continue
            tower, base = hero_type, "hero"
        else:
            raw_tower = raw_tower or ""
            tower = TOWER_ALIASES.get(raw_tower, raw_tower)
            if tower not in VALID_TOWERS:
                continue
            base = raw_tower
        source_var = match.group("var") or ("hero" if kind == "Hero" else raw_tower)
        name = f"{base}{sum(1 for v in entries.values() if v['tower'] == tower)}"
        aliases[source_var] = name
        entries[name] = {"tower": tower, "x": round(float(match.group("x")) * 1920), "y": round(float(match.group("y")) * 1080), "upgrades": [0, 0, 0]}
    lines = []
    # Preserve the plan's round gates. This intentionally ignores dynamic
    # calls, abilities, targeting, and end_round timing, but keeps the useful
    # placement/upgrade order instead of flattening everything onto round 3.
    blocks = [(3, text)]
    gated = list(re.finditer(r"(?:elif|if)\s+round\s*==\s*(\d+)\s*:", text))
    if gated:
        blocks = []
        first_end = gated[0].start()
        blocks.append((3, text[:first_end]))
        for i, match in enumerate(gated):
            end = gated[i + 1].start() if i + 1 < len(gated) else len(text)
            blocks.append((int(match.group(1)), text[match.end():end]))
    for round_no, block in blocks:
        actions = []
        for match in ctor.finditer(block):
            raw_tower = match.group("tower")
            source_var = match.group("var") or ("hero" if match.group("kind") == "Hero" else raw_tower or "hero")
            name = aliases.get(source_var)
            if name and name in entries:
                item = entries[name]
                actions.append(f"place {item['tower']} {name} at {item['x']}, {item['y']}")
        for variable, target in re.findall(r"([a-zA-Z_][a-zA-Z0-9_]*)\.upgrade\(\s*\[\s*[\"']([0-5]-[0-5]-[0-5])[\"']", block):
            variable = aliases.get(variable, variable)
            if variable not in entries: continue
            goal = [int(v) for v in target.split("-")]
            current = entries[variable]["upgrades"]
            # BTD6bot expresses each call as a complete target path. Validate
            # the entire transition before emitting individual AutoBTD6 clicks;
            # otherwise an illegal third crosspath can leave a noisy bad draft.
            if any(goal[index] < current[index] for index in range(3)) or not legal_upgrade_path(goal):
                continue
            next_levels = current.copy()
            transition = []
            valid_transition = True
            for path_index, level in enumerate(goal):
                while next_levels[path_index] < level:
                    next_levels[path_index] += 1
                    if not legal_upgrade_path(next_levels):
                        valid_transition = False
                        break
                    transition.append(f"upgrade {variable} path {path_index}")
                if not valid_transition:
                    break
            if valid_transition:
                actions.extend(transition)
                entries[variable]["upgrades"] = next_levels
        if actions:
            lines.append(f"round {round_no}")
            lines.extend(actions)
    return "\n".join(lines) + "\n"

created = []
skipped_empty = []
for (map_slug, gamemode), plan in sorted(TARGETS.items()):
    text = convert(plan)
    if "place " not in text:
        skipped_empty.append(f"{map_slug}#{gamemode}")
        continue
    out = OUT / f"{map_slug}#{gamemode}#1920x1080#converted#source_btd6bot_partial.btd6"
    out.write_text(text, encoding="utf-8")
    created.append(out.name)
print(f"updated {len(created)} partial drafts")
for name in created: print(name)
if skipped_empty:
    print(f"skipped {len(skipped_empty)} plans with nothing extractable: {', '.join(skipped_empty)}")
