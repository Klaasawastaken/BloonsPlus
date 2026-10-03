"""Import simple BTD6bot round plans as AutoBTD6 route drafts.

The parser rejects a plan if it cannot preserve every gameplay action.
"""
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "btd6bot" / "btd6bot" / "plans"
DST = ROOT / "autobtd6" / "playthroughs"
TOWERS = json.loads((ROOT / "autobtd6" / "towers.json").read_text(encoding="utf-8"))
MAPS = json.loads((ROOT / "autobtd6" / "maps.json").read_text(encoding="utf-8"))
MAP_NAMES = {"#ouch": "ouch", "skull_tweak": "skulltweak",
             "three_mines_'round": "three_mines_round"}
NAMES = {"boomer": "boomerang", "boat": "buccaneer", "alch": "alchemist",
         "spactory": "spike", "beast": "beasthandler"}
HERO_NAMES = {"gwen": "gwendolin", "obyn": "obyn_greenfoot", "-": ""}
MODES = {"EasyStandard": ("easy", 1, 40), "EasyPrimary": ("primary_only", 1, 40),
         "EasyDeflation": ("deflation", 31, 60), "MediumStandard": ("medium", 1, 60),
         "MediumMilitary": ("military_only", 1, 60), "MediumReverse": ("reverse", 1, 60),
         "MediumApopalypse": ("apopalypse", 1, 60), "HardStandard": ("hard", 3, 80),
         "HardMagic": ("magic_monkeys_only", 3, 80), "HardDouble_hp": ("double_hp_moabs", 3, 80),
         "HardHalf_cash": ("half_cash", 3, 80), "HardAlternate": ("alternate_bloons_rounds", 3, 80),
         "HardImpoppable": ("impoppable", 6, 100), "HardChimps": ("chimps", 6, 100)}

class Unsupported(Exception):
    pass

def literal(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError) as error:
        raise Unsupported("dynamic expression") from error

def call_name(node):
    if not isinstance(node, ast.Call):
        raise Unsupported("non-call")
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        return node.func.value.id + "." + node.func.attr
    raise Unsupported("dynamic call")

def import_plan(path):
    source = path.read_text(encoding="utf-8")
    if "[Bloons+ fallback of" in source:
        raise Unsupported("copied mode alias")
    identity = next(((path.stem[:-len(suffix)], *config) for suffix, config in MODES.items()
                     if path.stem.endswith(suffix) and len(path.stem) > len(suffix)), None)
    if identity is None:
        raise Unsupported("unknown map or mode")
    map_slug, mode, begin, end = identity
    map_slug = MAP_NAMES.get(map_slug, map_slug)
    if map_slug not in MAPS or not re.fullmatch(r"[a-z0-9_]+", map_slug):
        raise Unsupported("map unavailable in AutoBTD6")
    match = re.search(r"^\[Hero\]\s+(.+)$", source, re.M)
    hero = match.group(1).strip().lower().replace(" ", "_") if match else ""
    hero = HERO_NAMES.get(hero, hero)
    if hero and hero not in TOWERS["heros"]:
        raise Unsupported("unknown hero")
    module = ast.parse(source, filename=str(path))
    play = next((n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "play"), None)
    loop = next((n for n in play.body if isinstance(n, ast.While)), None) if play else None
    branch = next((n for n in loop.body if isinstance(n, ast.If)), None) if loop else None
    if branch is None:
        raise Unsupported("no round branches")
    actions, placed, upgrades = [], {}, {}
    while branch is not None:
        condition = branch.test
        if not (isinstance(condition, ast.Compare) and isinstance(condition.left, ast.Name)
                and condition.left.id == "round" and len(condition.comparators) == 1
                and len(condition.ops) == 1 and isinstance(condition.ops[0], ast.Eq)):
            raise Unsupported("nonstandard round condition")
        rhs = condition.comparators[0]
        number = (begin if rhs.id == "BEGIN" else end) if isinstance(rhs, ast.Name) and rhs.id in ("BEGIN", "END") else literal(rhs)
        if not isinstance(number, int) or number < 1:
            raise Unsupported("invalid round")
        # The opening block carries no round marker, like AutoBTD6's own routes, so it runs at the
        # start of any mode the route is replayed on (Hard starts at round 3, CHIMPS at 6).
        if not (isinstance(rhs, ast.Name) and rhs.id == "BEGIN"):
            actions.append(f"round {number}")
        for stmt in branch.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                name = stmt.targets[0].id
                kind = call_name(stmt.value)
                args = stmt.value.args
                if kind == "Hero" and len(args) >= 2 and hero:
                    tower, x, y = hero, literal(args[0]), literal(args[1])
                elif kind == "Monkey" and len(args) >= 3:
                    raw = literal(args[0])
                    tower, x, y = NAMES.get(raw, raw), literal(args[1]), literal(args[2])
                    if tower not in TOWERS["monkeys"]:
                        raise Unsupported("unknown tower")
                else:
                    raise Unsupported("unsupported placement")
                if name in placed or not (0 <= x <= 1 and 0 <= y <= 1):
                    raise Unsupported("invalid placement")
                placed[name], upgrades[name] = tower, [0, 0, 0]
                actions.append(f"place {tower} {name} at {round(x * 1920)}, {round(y * 1080)}")
            elif isinstance(stmt, ast.Expr):
                action = call_name(stmt.value)
                args = stmt.value.args
                if action == "forward":
                    continue
                if action == "Hero" and len(args) >= 2 and hero:
                    name = "hero0"
                    x, y = literal(args[0]), literal(args[1])
                    if name in placed or not (0 <= x <= 1 and 0 <= y <= 1):
                        raise Unsupported("invalid hero placement")
                    placed[name], upgrades[name] = hero, [0, 0, 0]
                    actions.append(f"place {hero} {name} at {round(x * 1920)}, {round(y * 1080)}")
                    continue
                name, _, operation = action.partition(".")
                if name not in placed:
                    raise Unsupported("unknown tower action")
                if operation == "target" and args:
                    target = literal(args[0]).lower()
                    if placed[name] in ("heli", "dartling", "ace", "mortar", "spike"):
                        raise Unsupported("special targeting needs native runner")
                    cycles = {"first": 0, "last": 1, "close": 2, "strong": 3}
                    if target not in cycles:
                        raise Unsupported("unsupported target " + target)
                    actions.extend(f"retarget {name}" for _ in range(cycles[target]))
                elif operation == "upgrade" and args:
                    for level in literal(args[0]):
                        desired = [int(n) for n in level.split("-")]
                        changes = [i for i in range(3) if desired[i] != upgrades[name][i]] if len(desired) == 3 else []
                        if len(changes) != 1 or desired[changes[0]] != upgrades[name][changes[0]] + 1:
                            raise Unsupported("nonsequential upgrade")
                        actions.append(f"upgrade {name} path {changes[0]}")
                        upgrades[name] = desired
                else:
                    raise Unsupported("unsupported action " + action)
            else:
                raise Unsupported("unsupported statement")
        if not branch.orelse:
            branch = None
        elif len(branch.orelse) == 1 and isinstance(branch.orelse[0], ast.If):
            branch = branch.orelse[0]
        else:
            raise Unsupported("nonstandard branch")
    if not any(action.startswith("place ") for action in actions):
        raise Unsupported("empty plan")
    filename = f"{map_slug}#{mode}#1920x1080#converted#source_btd6bot.btd6"
    (DST / filename).write_text("\n".join(actions) + "\n", encoding="utf-8")
    return filename

if __name__ == "__main__":
    converted, skipped = [], {}
    for plan in sorted(SRC.glob("*.py")):
        try:
            converted.append(import_plan(plan))
        except Unsupported as error:
            skipped[plan.name] = str(error)
    print(json.dumps({"converted": len(converted), "skipped": len(skipped),
                      "convertedFiles": converted, "skippedPlans": skipped}, indent=2))
