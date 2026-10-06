"""Import public, permissively licensed BTD6 bot strategies as AutoBTD6 routes.

Sources (all MIT licensed; the strategy files are vendored under route-library/public-sources and
btd6bot/, with their LICENSE files, so a rerun needs no network):
  * j-miet/BTD6bot            btd6bot/btd6bot/plans/*.py            relative 0..1 coordinates
  * piweiblen/BloonsPlayer    public-sources/piweiblen-BloonsPlayer  relative play-field coordinates
  * ThuyTran735/BTD6-Everything-Macro  public-sources/ThuyTran735-...  absolute 1920x1080 pixels
  * Randy-Hodges/BTD6-Autoplay         public-sources/Randy-Hodges-... absolute 1920x1080 pixels

Routes retain source placement and upgrade order where supported. A conversion is not
proof of victory or timing equivalence. Existing recordings, including repaired imports and original CHIMPS, are never regenerated in place.
  * supported BTD6bot waits: emitted as non-blocking seconds-based wait commands;
  * annotated omissions: no-ops and legacy timing/flow omissions are recorded in headers.
    Older "dropped (timing only)" wording does not prove those omissions harmless;
  * lossy commands: written as #lossy drafts, with each omitted operation listed;
  * fatal commands (paid hero levels, unknown tower/hero, moved tower coordinates,
    unreadable statements): rejected rather than replaced with invented actions.
Rejections and remaining gaps go to route-gaps.json.

A final pass adds compatibility copies of existing trusted routes, following AutoBTD6's own
helper.listBTD6InstructionsFileCompatability table (e.g. a CHIMPS route that uses only magic
towers also clears Magic Monkeys Only; a Hard route also clears Medium and Easy). Each copy is
flagged #compat and names its source file in the header.

All written files are validated with AutoBTD6's own parser (helper.parseBTD6InstructionsFile,
run in a subprocess with cwd=autobtd6). Run: .venv/Scripts/python.exe import-public-routes.py
Then: node tools/route-coverage-report.js
"""
import ast
import os
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUTO = ROOT / "autobtd6"
PT = AUTO / "playthroughs"
LIB = ROOT / "route-library"
PUB = LIB / "public-sources"
BTD6BOT_PLANS = ROOT / "btd6bot" / "btd6bot" / "plans"
TOWERS = json.loads((AUTO / "towers.json").read_text(encoding="utf-8"))
MAPS = json.loads((AUTO / "maps.json").read_text(encoding="utf-8"))
GUIDES = json.loads((LIB / "metadata" / "online-guide-sources.json").read_text(encoding="utf-8"))
GENERATOR = "import-public-routes.py"
W, H = 1920, 1080

MODES = ["easy", "primary_only", "deflation", "medium", "military_only", "reverse", "apopalypse",
         "hard", "magic_monkeys_only", "double_hp_moabs", "half_cash", "alternate_bloons_rounds",
         "impoppable", "chimps"]
UNVERIFIED_OK = {"easy", "medium", "hard"}      # automation.js MODES_REQUIRING_VERIFIED_ROUTE complement
CLASS_OF_MODE = {"primary_only": "primary", "military_only": "military", "magic_monkeys_only": "magic"}

SOURCES = {
    "btd6bot": {"repo": "https://github.com/j-miet/BTD6bot", "license": "MIT (c) 2025 Jani Miettinen",
                "commit": "2d6dac0957a0d55d0af201bd497afbebf7f3e5c2", "local": "btd6bot/btd6bot/plans"},
    "bloonsplayer": {"repo": "https://github.com/piweiblen/BloonsPlayer", "license": "MIT (c) 2021 piweiblen",
                     "commit": "17d624879c5ad777e82594da34450e66b2d60756",
                     "local": "route-library/public-sources/piweiblen-BloonsPlayer"},
    "everythingmacro": {"repo": "https://github.com/ThuyTran735/BTD6-Everything-Macro",
                        "license": "MIT (c) 2026 ThuyTran735", "commit": "afd8a30917bcab798a9ed8bf15f83897f6fb0a60",
                        "local": "route-library/public-sources/ThuyTran735-BTD6-Everything-Macro"},
    "randyhodges": {"repo": "https://github.com/Randy-Hodges/BTD6-Autoplay", "license": "MIT (c) 2021 Randy-Hodges",
                    "commit": "7c36862ffec1d64bb95ddabecf20c73cb54046fd",
                    "local": "route-library/public-sources/Randy-Hodges-BTD6-Autoplay"},
}

TOWER_ALIASES = {
    "dart": "dart", "boomerang": "boomerang", "boomer": "boomerang", "boom": "boomerang", "bomb": "bomb",
    "tack": "tack", "ice": "ice", "glue": "glue", "desperado": "desperado", "sniper": "sniper", "sub": "sub",
    "buccaneer": "buccaneer", "boat": "buccaneer", "ace": "ace", "plane": "ace", "heli": "heli",
    "mortar": "mortar", "dartling": "dartling", "wizard": "wizard", "super": "super", "ninja": "ninja",
    "alchemist": "alchemist", "alch": "alchemist", "druid": "druid", "mermonkey": "mermonkey",
    "farm": "farm", "banana": "farm", "spike": "spike", "spikes": "spike", "spactory": "spike",
    "village": "village", "engineer": "engineer", "engi": "engineer", "beast": "beasthandler",
    "beasthandler": "beasthandler",
}
HERO_ALIASES = {
    "quincy": "quincy", "gwen": "gwendolin", "gwendolin": "gwendolin", "striker": "striker_jones",
    "striker jones": "striker_jones", "obyn": "obyn_greenfoot", "obyn greenfoot": "obyn_greenfoot",
    "silas": "silas", "ben": "benjamin", "benjamin": "benjamin", "pat": "pat_fusty", "pat fusty": "pat_fusty",
    "churchill": "captain_churchill", "captain churchill": "captain_churchill", "ezili": "ezili",
    "rosalia": "rosalia", "etienne": "etienne", "sauda": "sauda", "adora": "adora",
    "brickell": "admiral_brickell", "admiral brickell": "admiral_brickell", "psi": "psi",
    "geraldo": "geraldo", "corvus": "corvus",
}
TARGETS = ["first", "last", "close", "strong"]
STANDARD_TARGETING_HEROES = {"quincy", "gwendolin", "striker_jones", "obyn_greenfoot", "silas", "pat_fusty",
                             "captain_churchill", "ezili", "rosalia", "sauda", "adora", "admiral_brickell",
                             "psi", "corvus"}

norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
MAP_BY_NORM = {norm(v.get("name") or k): k for k, v in MAPS.items()}
MAP_BY_NORM.update({norm(k): k for k in MAPS})
MAP_BY_NORM.update({"glacial": "glacial_trail", "skulltweak": "skulltweak", "spiceisland": "spice_islands",
                    "ouch": "ouch", "threeminesround": "three_mines_round"})


def map_slug(name):
    return MAP_BY_NORM.get(norm(name))


class Unsupported(Exception):
    pass


class Route:
    """Builds one AutoBTD6 route while tracking tower state so every line stays valid."""

    def __init__(self, source, source_file, map_slug_, mode, hero=None):
        self.source, self.source_file, self.map, self.mode, self.hero = source, source_file, map_slug_, mode, hero
        self.lines, self.harmless, self.lossy = [], set(), set()
        self.towers = {}           # our name -> {"type", "up": [a,b,c], "target": idx, "hero": bool}
        self.alias = {}            # source name -> our name
        self.counts = {}
        self.last_round = None
        self.source_autostart = True
        self.source_autostart_initialized = False
        self.source_flow_active = False
        self.source_called_forward = False
        self.source_skip_roundcheck = False

    def point(self, x, y):
        x, y = int(round(x)), int(round(y))
        if not (0 <= x < W and 0 <= y < H):
            raise Unsupported(f"position outside {W}x{H}")
        return x, y

    def place(self, source_name, kind, x, y):
        x, y = self.point(x, y)
        if kind == "hero":
            if source_name in self.alias:
                raise Unsupported(f"hero {source_name} placed twice")
            if not self.hero:
                raise Unsupported("hero placement without a named hero")
            name, tower = "hero0", self.hero
            if name in self.towers:
                raise Unsupported("second hero placement")
        else:
            tower = TOWER_ALIASES.get(kind.lower().strip())
            if tower not in TOWERS["monkeys"]:
                raise Unsupported(f"unknown tower {kind}")
            # Python plans sometimes reassign a local variable to a newly placed tower after the
            # previous tower is no longer referenced. Preserve both physical towers and point
            # subsequent source actions at the new one, matching Python's assignment semantics.
            if source_name in self.alias:
                self.harmless.add(f"source variable {source_name} reused for a later {tower}")
            index = self.counts.get(tower, 0)
            self.counts[tower] = index + 1
            name = f"{tower}{index}"
        self.alias[source_name] = name
        self.towers[name] = {"type": tower, "up": [0, 0, 0], "target": 0, "hero": kind == "hero"}
        self.lines.append(f"place {tower} {name} at {x}, {y}")
        return name

    def tower(self, source_name):
        if source_name not in self.alias:
            raise Unsupported(f"action on unplaced tower {source_name}")
        return self.alias[source_name]

    def upgrade(self, source_name, path):
        name = self.tower(source_name)
        state = self.towers[name]
        if state["hero"]:
            raise Unsupported("paid hero levels cannot be replaced by passive XP")
        up = list(state["up"])
        up[path] += 1
        if up[path] > 5 or sum(v > 0 for v in up) > 2 or sum(v > 2 for v in up) > 1:
            raise Unsupported(f"invalid crosspath {up} on {name}")
        state["up"] = up
        self.lines.append(f"upgrade {name} path {path}" + self.selection_suffix(name))

    def upgrade_to(self, source_name, target):
        """Upgrade to an absolute crosspath, buying top, middle then bottom tiers (source order)."""
        name = self.tower(source_name)
        if self.towers[name]["hero"]:
            raise Unsupported("paid hero levels cannot be replaced by passive XP")
        current = self.towers[name]["up"]
        if any(t < c for t, c in zip(target, current)):
            raise Unsupported(f"upgrade target {target} below current {current} on {source_name} ({name}); "
                              "likely a typo in the source plan (a path cannot be un-upgraded)")
        for path in range(3):
            for _ in range(target[path] - current[path]):
                self.upgrade(source_name, path)

    def retarget(self, source_name, times=1, to=None, reverse=False):
        name = self.tower(source_name)
        for i in range(times):
            if to and i == times - 1:
                self.lines.append(f"retarget {name} to {to[0]}, {to[1]}" + self.selection_suffix(name))
            else:
                self.lines.append(f"retarget {name}" + (' reverse' if reverse else '') + self.selection_suffix(name))

    def selection_suffix(self, name):
        point = self.towers[name].get('selectionPos')
        return f' at {point[0]}, {point[1]}' if point is not None else ''

    def update_selection(self, source_name, point):
        if point is None:
            return  # Source cpos=None keeps the previously selected coordinate.
        if (not isinstance(point, (tuple, list)) or len(point) != 2
                or any(type(value) not in (int, float) or not 0 <= value < 1 for value in point)):
            raise Unsupported('cpos needs two normalized coordinates in [0, 1)')
        name = self.tower(source_name)
        self.towers[name]['selectionPos'] = self.point(point[0] * W, point[1] * H)

    def set_target(self, source_name, target, to=None):
        """Standard First/Last/Close/Strong cycle; AutoBTD6 retarget = one Tab (forward)."""
        name = self.tower(source_name)
        state = self.towers[name]
        kind = state["type"]
        if kind == "spike":
            # Pinned BTD6bot uses this five-state cycle for x-x-2 through
            # x-x-5. Preserve its shortest forward/reverse input sequence.
            cycle = ('normal', 'close', 'smart', 'set', 'automatic')
            current = state.get('spikeTarget', 'normal')
            desired = target.lower()
            if desired in cycle and current in cycle and 2 <= state['up'][2] <= 5:
                if to is not None and (desired != 'set' or current in ('smart', 'automatic')):
                    # Source concatenates two strings in its Set click guard.
                    # Do not invent a click for those ambiguous calls.
                    self.lossy.add(f"ambiguous pinned Spike positional targeting '{target}' from {current}")
                    return
                delta = (cycle.index(desired) - cycle.index(current)) % len(cycle)
                reverse = delta > 2
                self.retarget(source_name, len(cycle)-delta if reverse else delta, reverse=reverse)
                if to is not None and current in ('normal', 'close'):
                    self.special(source_name, to)
                state['spikeTarget'] = desired
                return
            self.lossy.add(f"spike targeting '{target}' (needs a special cycle or click)")
            return
        if to is not None:
            self.lossy.add(f"positional targeting '{target}'")
            return
        # Engineer uses the ordinary First/Last/Close/Strong cycle in the
        # pinned source. Foam/trap placement uses separate special commands.
        if kind in ("heli", "ace", "mortar", "dartling", "spike", "farm", "village", "beasthandler"):
            self.lossy.add(f"{kind} targeting '{target}' (needs a special cycle or click)")
            return
        if state["hero"] and kind not in STANDARD_TARGETING_HEROES:
            self.lossy.add(f"{kind} hero targeting '{target}'")
            return
        target = target.lower()
        if target not in TARGETS:
            self.lossy.add(f"targeting '{target}'")
            return
        steps = (TARGETS.index(target) - state["target"]) % 4
        state["target"] = TARGETS.index(target)
        for _ in range(steps):
            self.lines.append(f"retarget {name}" + self.selection_suffix(name))

    def special(self, source_name, to=None):
        name = self.tower(source_name)
        self.lines.append(f"special {name}" + (f" to {to[0]}, {to[1]}" if to is not None else '') + self.selection_suffix(name))

    def sell(self, source_name):
        name = self.tower(source_name)
        self.lines.append(f"sell {name}" + self.selection_suffix(name))
        del self.alias[source_name]

    def round(self, number):
        if not isinstance(number, int) or number < 1:
            raise Unsupported(f"invalid round {number}")
        if number != self.last_round:
            self.lines.append(f"round {number}")
            self.last_round = number

    def round_offset(self, number, seconds):
        import math
        if type(number) is not int or number < 1:
            raise Unsupported('round offset needs a positive round')
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
            raise Unsupported('round offset must be finite and non-negative')
        self.lines.append(f'round {number} after {seconds:g} seconds')
        self.last_round = number

    def cash(self, amount):
        self.lines.append(f"cash {int(amount)}")

    def remove(self, x, y, price):
        x, y = self.point(x, y)
        self.lines.append(f"remove obstacle at {x}, {y} for {int(price)}")

    def click(self, x, y):
        x, y = self.point(x, y)
        self.lines.append(f"click map at {x}, {y}")

    def wait(self, seconds):
        import math
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
            raise Unsupported('wait duration must be finite and non-negative')
        if seconds:
            self.lines.append(f'wait {seconds:g} seconds')

    def ability(self, slot, timer=0, target=None, cursor_delay=0):
        slot = int(slot)
        timer, cursor_delay = float(timer), float(cursor_delay)
        if not 1 <= slot <= 10:
            raise Unsupported(f"ability slot {slot} outside 1-10")
        if timer < 0 or cursor_delay < 0:
            raise Unsupported("negative ability timing")
        line = f"ability {slot}"
        if timer:
            line += f" after {timer:g} seconds"
        if target is not None:
            x, y = self.point(*target)
            line += f" at {x}, {y}"
            if cursor_delay:
                line += f" move after {cursor_delay:g} seconds"
        elif cursor_delay:
            raise Unsupported("ability cursor delay without a target")
        self.lines.append(line)

    def body(self):
        if not any(line.startswith("place ") for line in self.lines):
            raise Unsupported("no tower placements")
        return self.lines


# ----------------------------------------------------------------------------------------- BTD6bot
BTD6BOT_MODES = {"EasyStandard": ("easy", 1, 40), "EasyPrimary": ("primary_only", 1, 40),
                 "EasyDeflation": ("deflation", 31, 60), "MediumStandard": ("medium", 1, 60),
                 "MediumMilitary": ("military_only", 1, 60), "MediumReverse": ("reverse", 1, 60),
                 "MediumApopalypse": ("apopalypse", 1, 60), "HardStandard": ("hard", 3, 80),
                 "HardMagic": ("magic_monkeys_only", 3, 80), "HardDouble_hp": ("double_hp_moabs", 3, 80),
                 "HardHalf_cash": ("half_cash", 3, 80), "HardAlternate": ("alternate_bloons_rounds", 3, 80),
                 "HardImpoppable": ("impoppable", 6, 100), "HardChimps": ("chimps", 6, 100)}
BTD6BOT_FLOW_CONTROLS = {"forward", "change_autostart", "end_round"}


def literal(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError) as error:
        raise Unsupported("dynamic expression") from error


def call_parts(node):
    if not isinstance(node, ast.Call):
        raise Unsupported("non-call statement")
    if isinstance(node.func, ast.Name):
        return None, node.func.id
    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        return node.func.value.id, node.func.attr
    raise Unsupported("dynamic call")


def convert_btd6bot(path):
    stem = path.stem
    identity = next(((stem[:-len(s)], *cfg) for s, cfg in BTD6BOT_MODES.items()
                     if stem.endswith(s) and len(stem) > len(s)), None)
    if identity is None:
        raise Unsupported("not a map plan")
    raw_map, mode, begin, end = identity
    slug = map_slug(raw_map.replace("#", ""))
    if not slug:
        raise Unsupported(f"map '{raw_map}' is not in autobtd6/maps.json")
    source = path.read_text(encoding="utf-8")
    match = re.search(r"^\[Hero\]\s+(.+)$", source, re.M)
    hero_raw = match.group(1).strip().lower() if match else "-"
    hero = None if hero_raw in ("-", "") else HERO_ALIASES.get(hero_raw)
    if hero_raw not in ("-", "") and not hero:
        raise Unsupported(f"unknown hero {hero_raw}")
    route = Route("btd6bot", f"btd6bot/plans/{path.name}", slug, mode, hero)
    module = ast.parse(source)
    play = next((n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "play"), None)
    loop = next((n for n in play.body if isinstance(n, ast.While)), None) if play else None
    convert_btd6bot_loop(route, loop, begin, end)
    return route


def convert_btd6bot_loop(route, loop, begin, end):
    """Interpret only the pinned source's bounded round loop, never execute it.

    Each round evaluates independent root if chains in source order. An elif
    chain chooses exactly one body; reassigning round affects subsequent root
    chains and the next iteration, not the currently selected body's remainder.
    HUD waits use the round_check entry value, never a reassigned loop variable.
    Manual input/timing omissions remain tracked by btd6bot_statement.
    """
    if loop is None or ast.unparse(loop.test) != 'round < END + 1':
        raise Unsupported('nonstandard round loop boundary')
    if not loop.body or not isinstance(loop.body[0], ast.Assign):
        raise Unsupported('round loop must begin with round_check')
    check = loop.body[0]
    if (len(check.targets) != 1 or not isinstance(check.targets[0], ast.Name)
            or check.targets[0].id != 'round' or not isinstance(check.value, ast.Call)
            or ast.unparse(check.value.func) != 'Rounds.round_check'
            or check.value.keywords or len(check.value.args) not in (2, 3)
            or ast.unparse(check.value.args[0]) != 'round'
            or ast.unparse(check.value.args[1]) != 'map_start'
            or len(check.value.args) == 3 and ast.unparse(check.value.args[2]) != 'data[2]'):
        raise Unsupported('nonstandard round_check invocation')
    roots = loop.body[1:]
    if not roots or any(not isinstance(node, ast.If) for node in roots):
        raise Unsupported('unsupported top-level round loop command')

    def number(node):
        if isinstance(node, ast.Name) and node.id in ('BEGIN', 'END'):
            return begin if node.id == 'BEGIN' else end
        value = literal(node)
        if type(value) is not int or not begin <= value <= end:
            raise Unsupported('round loop value outside selected mode')
        return value

    chains = []
    for root in roots:
        chain = []
        branch = root
        while branch is not None:
            test = branch.test
            if (not isinstance(test, ast.Compare) or not isinstance(test.left, ast.Name)
                    or test.left.id != 'round' or len(test.ops) != 1
                    or not isinstance(test.ops[0], ast.Eq) or len(test.comparators) != 1):
                raise Unsupported('nonstandard round condition')
            chain.append((number(test.comparators[0]), branch.body))
            if not branch.orelse:
                branch = None
            elif len(branch.orelse) == 1 and isinstance(branch.orelse[0], ast.If):
                branch = branch.orelse[0]
            else:
                raise Unsupported('nonstandard round branch fallback')
        chains.append(chain)

    # Only manual-flow plans need every logical iteration, including empty ones.
    # Ordinary imports retain their existing compact HUD-wait representation.
    manual = any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                 and node.func.id in BTD6BOT_FLOW_CONTROLS for node in ast.walk(loop))
    route.source_flow_active = manual
    if manual:
        route.lines.append('autostart on')  # Rounds.start restores this baseline.
        route.source_autostart_initialized = True
    route.source_loop_trace = []
    route.source_round_trace = []
    current = begin - 1
    visits = set()
    while current < end:
        current += 1  # Rounds.round_check's logical increment.
        entry = current
        if entry in visits:
            raise Unsupported('round reassignment creates a repeated logical round')
        visits.add(entry)
        if manual:
            if entry == begin:
                if route.mode == 'apopalypse':
                    btd6bot_statement(route, ast.parse('forward(1)').body[0])
                route.lines.append(f'source round {entry}')
                route.source_round_trace.append((entry, 'initial'))
            else:
                # end_round does NOT set called_forward in the pinned source.
                if not route.source_called_forward:
                    btd6bot_statement(route, ast.parse('forward()').body[0])
                skip = route.source_skip_roundcheck
                route.source_skip_roundcheck = False
                if not skip:
                    route.round(entry)
                route.lines.append(f'source round {entry}' + (' after play' if skip else ''))
                route.source_round_trace.append((entry, 'after-play' if skip else 'hud'))
        marked = False
        for chain in chains:
            body = next((body for target, body in chain if target == current), None)
            if body is None:
                continue
            route.source_loop_trace.append((entry, current))
            if not manual and not marked and entry != begin:
                route.round(entry)
            marked = True
            for stmt in body:
                if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                        and isinstance(stmt.targets[0], ast.Name) and stmt.targets[0].id == 'round'):
                    target = number(stmt.value)
                    if target < current:
                        raise Unsupported('round reassignment moves source loop backwards')
                    current = target
                else:
                    btd6bot_statement(route, stmt)
    route.source_flow_active = False


def bind_btd6bot_tower_arguments(action, args, kwargs):
    """Bind the pinned Monkey signatures without executing upstream input code."""
    parameters = {
        'upgrade': ('set_upg', 'cpos'),
        'target': ('set_target', 'x', 'y', 'cpos'),
        'special': ('s', 'x', 'y', 'cpos'),
        'sell': ('cpos',),
    }.get(action)
    if parameters is None:
        return args, kwargs
    if len(args) > len(parameters) or set(kwargs) - set(parameters):
        raise Unsupported(f'invalid arguments for {action}')
    bound = dict(kwargs)
    for parameter, node in zip(parameters, args):
        if parameter in bound:
            raise Unsupported(f'duplicate {parameter} argument for {action}')
        bound[parameter] = node
    required = {'upgrade': 'set_upg', 'target': 'set_target'}.get(action)
    if required and required not in bound:
        raise Unsupported(f'{action} requires {required}')
    # None is the source default, not a coordinate target. Keep explicit
    # selection coordinates separate from the special/priority target.
    for parameter in ('x', 'y'):
        if parameter in bound and literal(bound[parameter]) is None:
            del bound[parameter]
    if ('x' in bound) != ('y' in bound):
        raise Unsupported(f'{action} target requires both x and y')
    args = [bound.pop(required)] if required else []
    if action == 'special':
        args = [bound.pop('s', ast.Constant(value=1))]
    return args, bound


def btd6bot_statement(route, stmt):
    if isinstance(stmt, ast.Pass):
        return
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Name):
        route.harmless.add("bare name reference (no-op in source)")
        return
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
        if stmt.targets[0].id == "round" and isinstance(stmt.value, (ast.Name, ast.Constant)):
            raise Unsupported("round reassignment requires the source loop interpreter")
        _, kind = call_parts(stmt.value)
        args = stmt.value.args
        if kind == "Hero" and len(args) >= 2:
            route.place(stmt.targets[0].id, "hero", literal(args[0]) * W, literal(args[1]) * H)
        elif kind == "Monkey" and len(args) >= 3:
            route.place(stmt.targets[0].id, literal(args[0]), literal(args[1]) * W, literal(args[2]) * H)
        else:
            raise Unsupported(f"unsupported assignment {kind}")
        return
    if not isinstance(stmt, ast.Expr):
        raise Unsupported(f"unsupported statement {type(stmt).__name__}")
    owner, action = call_parts(stmt.value)
    args, kwargs = stmt.value.args, {k.arg: k.value for k in stmt.value.keywords}
    if owner is not None:
        if None in kwargs or len(kwargs) != len(stmt.value.keywords):
            raise Unsupported('expanded or duplicate tower keyword arguments')
        args, kwargs = bind_btd6bot_tower_arguments(action, args, kwargs)
    if "cpos" in kwargs:
        if owner is None or action not in ('upgrade', 'target', 'special', 'sell'):
            raise Unsupported('cpos requires a supported tower command')
        route.update_selection(owner, literal(kwargs.pop('cpos')))
    if owner is None:
        if action == "wait":
            timer = literal(args[0]) if args else literal(kwargs['timer']) if 'timer' in kwargs else 0
            if timer == 0:
                route.harmless.add('wait(0)')
            else:
                route.wait(timer)
        elif action == "move_cursor":
            if (len(args) not in (0, 2) or any(key not in ('x', 'y') for key in kwargs)
                    or len(args) == 2 and kwargs or not args and set(kwargs) != {'x', 'y'}):
                raise Unsupported('move_cursor requires exactly x and y')
            x, y = (literal(value) for value in args) if args else (literal(kwargs['x']), literal(kwargs['y']))
            if any(type(value) not in (int, float) or not 0 <= value < 1 for value in (x, y)):
                raise Unsupported('move_cursor needs normalized coordinates in [0, 1)')
            x, y = route.point(x * W, y * H)
            route.lines.append(f'move cursor to {x}, {y}')
        elif action == 'change_autostart':
            if args or kwargs:
                raise Unsupported('change_autostart accepts no arguments')
            # The pinned source runner restores Auto Start on before a plan.
            # Preserve that baseline explicitly; a user's prior setting or a
            # previous route must not invert the source's first toggle.
            if not route.source_autostart_initialized:
                route.lines.insert(0, 'autostart on')
                route.source_autostart_initialized = True
            route.source_autostart = not route.source_autostart
            route.lines.append('autostart on' if route.source_autostart else 'autostart off')
        elif action in ('forward', 'end_round') and route.source_flow_active:
            parameter = 'speed' if action == 'forward' else 'time_limit'
            if (len(args) > 1 or any(key != parameter for key in kwargs)
                    or args and kwargs):
                raise Unsupported(f'{action} requires at most one {parameter}')
            value = literal(args[0]) if args else literal(kwargs[parameter]) if kwargs else (2 if action == 'forward' else 0)
            if action == 'forward':
                if type(value) is not int or value not in (1, 2):
                    raise Unsupported('forward speed must be exactly 1 or 2')
                route.lines.append('play once' if value == 1 else 'play twice')
                # forward(1)'s post-input sleep is explicit. forward(2)'s
                # inter-input delay belongs to the observed two-Play controller.
                if value == 1:
                    route.wait(0.2)
                route.source_called_forward = True
            else:
                route.wait(value)  # Reject bool, nonfinite and negative delays.
                route.lines.append('play once')
                route.wait(0.2)
                route.source_skip_roundcheck = True
        elif action in BTD6BOT_FLOW_CONTROLS:
            # Manual round control can wait for end-of-round cash or alter
            # ability timing. Cursor movement can aim a tower. Neither is a no-op.
            route.lossy.add(f'{action}() control omitted')
        elif action == "Hero" and len(args) >= 2:
            route.place("hero", "hero", literal(args[0]) * W, literal(args[1]) * H)
        elif action == "ability":
            if not args:
                raise Unsupported("ability without a slot")
            timer = literal(args[1]) if len(args) > 1 else literal(kwargs["timer"]) if "timer" in kwargs else 0
            target_node = args[2] if len(args) > 2 else kwargs.get("xy")
            delay = literal(args[3]) if len(args) > 3 else literal(kwargs["delay"]) if "delay" in kwargs else 0
            target = None
            if target_node is not None:
                rx, ry = literal(target_node)
                target = (rx * W, ry * H)
            route.ability(literal(args[0]), timer, target, delay)
        elif action == "click":
            if len(args) < 2:
                raise Unsupported("map click without coordinates")
            route.click(literal(args[0]) * W, literal(args[1]) * H)
        else:
            raise Unsupported(f"unknown command {action}()")
        return
    if action == "upgrade":
        for level in literal(args[0]):
            route.upgrade_to(owner, [int(n) for n in level.split("-")])
    elif action == "target":
        target = literal(args[0])
        if len(args) > 1 or "x" in kwargs:
            x, y = literal(kwargs['x']), literal(kwargs['y'])
            if any(type(value) not in (int, float) or not 0 <= value < 1 for value in (x, y)):
                raise Unsupported('target needs normalized coordinates in [0, 1)')
            route.set_target(owner, target, to=route.point(x * W, y * H))
        else:
            route.set_target(owner, target)
    elif action == "special":
        s = literal(args[0]) if args else literal(kwargs["s"]) if "s" in kwargs else 1
        has_xy = len(args) > 1 or "x" in kwargs
        name = route.tower(owner)
        if str(s) != "1":
            route.lossy.add("second special ability")
        elif has_xy and route.towers[name]["type"] == "mortar":
            x = literal(args[1] if len(args) > 1 else kwargs["x"]) * W
            y = literal(args[2] if len(args) > 2 else kwargs["y"]) * H
            route.retarget(owner, 1, route.point(x, y))
        elif has_xy:
            x = literal(args[1] if len(args) > 1 else kwargs['x'])
            y = literal(args[2] if len(args) > 2 else kwargs['y'])
            if any(type(value) not in (int, float) or not 0 <= value < 1 for value in (x, y)):
                raise Unsupported('special target needs normalized coordinates in [0, 1)')
            route.special(owner, route.point(x * W, y * H))
        else:
            route.special(owner)
    elif action == "sell":
        route.sell(owner)
    elif action in ("center", "force_target", "target_robo", "merge", "shop", "spellbook"):
        route.lossy.add(f"{action}()")
    else:
        raise Unsupported(f"unknown tower action {action}()")


# ------------------------------------------------------------------------------------ BloonsPlayer
BP_MODES = {"standard": None, "primary only": "primary_only", "deflation": "deflation",
            "military only": "military_only", "reverse": "reverse", "apopalypse": "apopalypse",
            "magic monkeys only": "magic_monkeys_only", "double hp moabs": "double_hp_moabs",
            "half cash": "half_cash", "alternate bloons rounds": "alternate_bloons_rounds",
            "impoppable": "impoppable", "chimps": "chimps"}


def bp_position(rx, ry):
    """player.RatioFit.convert_pos for a 1920x1080 screen."""
    ratio, sidebar = 19 / 11, 7 / 30
    proper_x = 2 * ((H * ratio) // 2)
    offset_x, width = (W - proper_x) // 2, proper_x - H * sidebar
    width_mod = width / (H * (ratio - sidebar))
    return offset_x + ((rx - 0.5) / width_mod + 0.5) * width, ry * H


def bp_args(text):
    return [a.strip() for a in re.sub(r"[()]", "", text).split(",") if a.strip()]


def convert_bloonsplayer(path):
    rows = [re.sub(r"#.*", "", line).strip() for line in path.read_text(encoding="utf-8").splitlines()]
    rows = [r for r in rows if r and r != "-"]
    head = re.match(r"(?i)open\s+(.+)$", rows[0]) if rows else None
    if not head:
        raise Unsupported("missing open command")
    parts = bp_args(head.group(1))
    if len(parts) < 3:
        raise Unsupported("open command without map/difficulty/mode")
    slug = map_slug(parts[0])
    if not slug:
        raise Unsupported(f"map '{parts[0]}' is not in autobtd6/maps.json")
    difficulty, mode_name = parts[1].lower(), parts[2].lower()
    if mode_name not in BP_MODES:
        raise Unsupported(f"unknown mode {mode_name}")
    mode = BP_MODES[mode_name] or difficulty
    hero = None
    if len(parts) > 3:
        hero = HERO_ALIASES.get(parts[3].lower())
        if not hero:
            raise Unsupported(f"unknown hero {parts[3]}")
    route = Route("bloonsplayer", f"tas/{path.parent.name}/{path.name}", slug, mode, hero)
    last_money = None
    for row in rows[1:]:
        low = row.lower()
        money_before, last_money = last_money, None
        if m := re.match(r"place\s+(.+)$", low):
            a = bp_args(m.group(1))
            if len(a) < 4:
                raise Unsupported(f"bad place: {row}")
            x, y = bp_position(float(a[1]), float(a[2]))
            route.place(a[3], a[0], x, y)
        elif m := re.match(r"upgrade\s+(.+)$", low):
            a = bp_args(m.group(1))
            name = route.tower(a[0])
            if route.towers[name]["hero"]:
                raise Unsupported("paid hero levels cannot be replaced by passive XP")
            for p in a[1:]:
                if p not in ("1", "2", "3"):
                    raise Unsupported(f"bad upgrade path {p}")
                route.upgrade(a[0], int(p) - 1)
        elif m := re.match(r"target\s+(.+)$", low):
            a = bp_args(m.group(1))
            times = int(a[1])
            name = route.tower(a[0])
            kind = route.towers[name]["type"]
            if len(a) >= 4 and kind == "mortar":
                route.retarget(a[0], max(times, 1), route.point(*bp_position(float(a[2]), float(a[3]))))
            elif len(a) >= 4:
                route.lossy.add(f"{kind} target position")
                route.retarget(a[0], times)
            else:
                route.retarget(a[0], times)
        elif m := re.match(r"priority\s+(.+)$", low):
            a = bp_args(m.group(1))
            if len(a) > 1:
                route.lossy.add("priority with a target position")
            else:
                route.special(a[0])
        elif m := re.match(r"sell\s+(.+)$", low):
            route.sell(bp_args(m.group(1))[0])
        elif m := re.match(r"remove\s+(.+)$", low):
            a = bp_args(m.group(1))
            if money_before is None:
                route.lossy.add("obstacle removal without a known price")
            else:
                route.remove(*bp_position(float(a[0]), float(a[1])), money_before)
        elif m := re.match(r"money\s+(\d+)$", low):
            last_money = int(m.group(1))
            route.cash(last_money)
        elif m := re.match(r"round\s+(\d+)$", low):
            route.round(int(m.group(1)))
        elif m := re.fullmatch(r"(delay|wait|lives)\s+(\d+(?:\.\d+)?)", low):
            command, amount = m.groups()
            if command in ("delay", "wait"):
                if float(amount) == 0:
                    route.harmless.add(command + "(0)")
                else:
                    route.wait(float(amount))
                    if command == 'wait':
                        route.lossy.add('BloonsPlayer wait has no pinned source handler; seconds interpretation requires strategy review')
            else:
                route.lossy.add("BloonsPlayer " + command + " " + amount + " control omitted")
        elif low in ('start round', 'start round slow'):
            if any(line.startswith('start round ') for line in route.lines):
                route.lossy.add('multiple explicit round starts require manual-round coordination')
            route.lines.append('start round ' + ('slow' if low.endswith(' slow') else 'fast'))
        elif low == 'change speed':
            route.lines.append('change speed')
        elif low == "toggle autostart" or low.startswith("start round"):
            route.lossy.add("BloonsPlayer " + low + " control omitted")
        elif m := re.fullmatch(r"(use|repeat|stop) ability\s+([0-9])", low):
            command, key = m.groups()
            slot = 10 if key == "0" else int(key)
            if command == "use":
                route.ability(slot)
            else:
                route.lines.append(f"{command} ability {slot}")
        elif low == "stop all abilities":
            route.lines.append("stop all abilities")
        elif re.match(r"(use ability|repeat ability|stop ability|stop all abilities)", low):
            raise Unsupported("unmapped or malformed activated ability key: " + row)
        elif re.match(r"(repeat move|move|stop move)\b", low):
            route.lossy.add("mouse sweeps (banana/cash collection)")
        elif m := re.match(r"click\s+(.+)$", low):
            a = bp_args(m.group(1))
            if len(a) != 2:
                raise Unsupported(f"bad map click: {row}")
            route.click(*bp_position(float(a[0]), float(a[1])))
        elif low.startswith("gerry shop"):
            route.lossy.add("Geraldo shop items")
        else:
            raise Unsupported(f"unknown command: {row}")
    return route


# ----------------------------------------------------------------------------- Everything Macro
EM_MODES = {"standard": None, "primary only": "primary_only", "deflation": "deflation",
            "military only": "military_only", "reverse": "reverse", "apopalypse": "apopalypse",
            "magic monkeys only": "magic_monkeys_only", "double hp moabs": "double_hp_moabs",
            "half cash": "half_cash", "alternate bloons rounds": "alternate_bloons_rounds",
            "impoppable": "impoppable", "chimps": "chimps"}


def convert_everythingmacro(path):
    text = "\n".join(re.sub(r"(^|\s);.*$", "", line) for line in path.read_text(encoding="utf-8-sig").splitlines())
    config = dict(re.findall(r"(\w+):\s*\"([^\"]*)\"", text.split("TowerSetup")[0]))
    if "map" not in config:
        raise Unsupported("no RunConfig")
    slug = map_slug(config["map"])
    if not slug:
        raise Unsupported(f"map '{config['map']}' is not in autobtd6/maps.json")
    mode = EM_MODES.get(config.get("gameMode", "").lower(), "?")
    if mode == "?":
        raise Unsupported(f"unknown mode {config.get('gameMode')}")
    mode = mode or config["difficulty"].lower()
    hero = HERO_ALIASES.get(config.get("hero", "").lower()) if config.get("hero") else None
    if config.get("hero") and not hero:
        raise Unsupported(f"unknown hero {config['hero']}")
    setup = {name: (kind, int(x), int(y)) for name, kind, x, y in re.findall(
        r"\"([^\"]+)\",\s*\{\s*type:\s*\"([^\"]+)\",\s*x:\s*(\d+),\s*y:\s*(\d+)", text)}
    route = Route("everythingmacro", "Maps/" + path.as_posix().split("/Maps/")[1], slug, mode, hero)
    strategy = text.split("strategy :=", 1)[1] if "strategy :=" in text else ""
    for rnd, delay, action, rest in re.findall(r"\[\s*(\d+)\s*,\s*(\d+)\s*,\s*\(\)\s*=>\s*(\w+)\((.*?)\)\s*\]",
                                               strategy, re.S):
        names = re.findall(r"TowerSetup\[\"([^\"]+)\"\]", rest)
        values = re.findall(r"\"([^\"]*)\"", re.sub(r"TowerSetup\[\"[^\"]+\"\]", "", rest))
        if int(rnd) > 0:
            if int(delay):
                route.round_offset(int(rnd), int(delay) / 1000)
            else:
                route.round(int(rnd))
        elif int(delay):
            route.lossy.add("pregame delay of " + delay + " milliseconds omitted")
        if action == "PlaceTower":
            kind, x, y = setup[names[0]]
            route.place(names[0], "hero" if kind.lower() == "hero" else kind, x, y)
        elif action == "UpgradeTower":
            if not re.fullmatch(r"[0-5]{3}", values[0]):
                raise Unsupported(f"bad upgrade target {values[0]}")
            route.upgrade_to(names[0], [int(c) for c in values[0]])
        elif action == "SetTargeting":
            route.set_target(names[0], values[0])
        elif action == "SellTower":
            if re.search(r"\d", re.sub(r"TowerSetup\[\"[^\"]+\"\]", "", rest)):
                raise Unsupported("sell at an overridden (moving-map) position")
            route.sell(names[0])
        elif action == "UseAbility":
            if not values:
                raise Unsupported("UseAbility without a slot")
            route.ability(int(values[0]))
        elif action in ("AimDartling", "LockHeliInPlace", "RetargetDartling", "RetargetHeli", "RetargetMortar",
                        "SetMortarTarget", "SetSubmerge", "PlaceMermonkeyTotem", "RetargetMermonkeyTotem"):
            raise Unsupported(f"{action} needs a coordinate-targeting action AutoBTD6 cannot express")
        else:
            raise Unsupported(f"unknown action {action}")
    return route


# ------------------------------------------------------------------------------ Randy-Hodges
def convert_randyhodges(path):
    module = ast.parse(path.read_text(encoding="utf-8"))
    consts = {n.targets[0].id: n.value.value for n in module.body if isinstance(n, ast.Assign)
              and isinstance(n.targets[0], ast.Name) and isinstance(n.value, ast.Constant)}
    script = next((n.value for n in module.body if isinstance(n, ast.Assign) and isinstance(n.value, ast.List)), None)
    slug = map_slug(path.stem.replace("_script", ""))
    if not slug or script is None:
        raise Unsupported("unknown map or no script list")
    if slug in ("sanctuary", "geared"):
        raise Unsupported("rotating map: the source uses a special moving-position handler")
    # play_collection_event.py opens every map on Hard / Standard; all scripts place Psi.
    route = Route("randyhodges", f"collection_scripts/{path.name}", slug, "hard", "psi")

    def value(node):
        return consts[node.id] if isinstance(node, ast.Name) else literal(node)
    for call in script.elts:
        kind = value(call.args[0])
        kw = {k.arg: k.value for k in call.keywords}
        action = value(kw["action"]) if "action" in kw else None
        name = value(kw["name"]) if "name" in kw else None
        if kind == "place":
            x, y = literal(kw["position"])
            route.place(name, "hero" if action == "Hero" else action, x, y)
        elif kind == "upgrade":
            route.upgrade(name, {"upgrade 1": 0, "upgrade 2": 1, "upgrade 3": 2}[action])
        elif kind == "target":
            route.set_target(name, action)
        elif kind == "start":
            # Pinned automatic handler sends Space twice: start, then fast.
            # Use the observed/checkpointed startup intent rather than blindly
            # duplicating inputs. Manual moving-map handlers are excluded above.
            if any(line.startswith('start round ') for line in route.lines):
                route.lossy.add('multiple explicit round starts require manual-round coordination')
            route.lines.append('start round fast')
        elif kind == "finish":
            # Collection runner selects automatic mode except Sanctuary, which
            # is rejected above. Its ordinary finish handler sends no input.
            route.harmless.add("finish (automatic source handler sends no input)")
        elif kind == "click":
            # The pinned ordinary handler moves to action.position and clicks
            # once. Keep that operation; do not invent an obstacle price.
            if 'position' not in kw:
                raise Unsupported('map click without coordinates')
            position = literal(kw['position'])
            if not isinstance(position, (list, tuple)) or len(position) != 2:
                raise Unsupported('map click needs exactly x and y')
            route.click(*position)
        else:
            raise Unsupported(f"unknown action {kind}")
    return route


# ------------------------------------------------------------------------------------ writing
def own_file(path):
    try:
        return f"# generator: {GENERATOR}" in path.read_text(encoding="utf-8")
    except OSError:
        return False


def route_body(path):
    return [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def existing_routes():
    out = []
    for p in sorted(PT.glob("*.btd6")):
        parts = p.stem.split("#")
        out.append({"file": p.name, "map": parts[0], "mode": parts[1], "res": parts[2], "flags": parts[3:],
                    "own": own_file(p)})
    return out


def header(meta_lines):
    return [f"# {line}" for line in meta_lines] + [f"# generator: {GENERATOR}"]


def placed_groups(lines):
    groups = set()
    for m in re.finditer(r"^place ([a-z_]+) ", "\n".join(lines), re.M):
        if m.group(1) in TOWERS["monkeys"]:
            groups.add(TOWERS["monkeys"][m.group(1)]["type"])
    return groups


def main():
    log_rejects, written = [], []
    # Imported recordings may have acquired repairs or live evidence. Preserve
    # every existing file; body deduplication below avoids re-emitting an
    # unchanged strategy, while changed conversions receive a separate name.
    routes = []
    jobs = [("btd6bot", convert_btd6bot, sorted(p for p in BTD6BOT_PLANS.glob("*.py") if not p.name.startswith("_"))),
            ("bloonsplayer", convert_bloonsplayer,
             sorted(p for p in (PUB / "piweiblen-BloonsPlayer" / "tas").rglob("*.txt") if p.parent.name != "races")),
            ("everythingmacro", convert_everythingmacro,
             sorted(p for p in (PUB / "ThuyTran735-BTD6-Everything-Macro" / "Maps").rglob("*.ahk")
                    if p.name != "MapTemplate.ahk")),
            ("randyhodges", convert_randyhodges,
             sorted((PUB / "Randy-Hodges-BTD6-Autoplay" / "collection_scripts").glob("*_script.py")))]
    for source, convert, files in jobs:
        for path in files:
            try:
                routes.append(convert(path))
            except (Unsupported, KeyError, IndexError, ValueError) as error:
                log_rejects.append({"source": source, "sourceFile": str(path.relative_to(ROOT)).replace("\\", "/"),
                                    "reason": f"{type(error).__name__ if not isinstance(error, Unsupported) else 'unsupported'}: {error}"})

    existing = existing_routes()
    bodies = {}
    for r in existing:
        bodies.setdefault((r["map"], r["mode"]), []).append(route_body(PT / r["file"]))
    covered = {(r["map"], r["mode"]) for r in existing if "generated" not in r["flags"]}
    covered |= {(r["map"], m) for r in existing if r["mode"] == "chimps" and "generated" not in r["flags"]
                for m in ("easy", "medium", "hard", "impoppable")}

    def emit(route, mode, flags, extra_meta, lines):
        src = SOURCES[route.source]
        stem = "#".join([route.map, mode, f"{W}x{H}", "converted", f"source_{route.source}", *flags])
        name = f"{stem}.btd6"
        n = 2
        while (PT / name).exists():
            name = f"{stem}#v{n}.btd6"
            n += 1
        if any(b == lines for b in bodies.get((route.map, mode), [])):
            log_rejects.append({"source": route.source, "sourceFile": route.source_file, "map": route.map,
                                "mode": mode, "reason": "identical route already in autobtd6/playthroughs"})
            return
        meta = [f"source: {src['repo']} (license {src['license']}) commit {src['commit']}",
                f"source file: {route.source_file} (vendored copy: {src['local']})",
                f"source mode: {route.mode}; converted to {W}x{H} AutoBTD6 actions"]
        if route.harmless:
            meta.append("conversion notes (source no-ops): " + "; ".join(sorted(route.harmless)))
        if route.lossy:
            meta.append("dropped (not expressible in AutoBTD6, route may be weaker): " + "; ".join(sorted(route.lossy)))
        meta += extra_meta
        (PT / name).write_text("\n".join(header(meta) + lines) + "\n", encoding="utf-8")
        bodies.setdefault((route.map, mode), []).append(lines)
        covered.add((route.map, mode))
        if mode == "chimps":
            covered.update((route.map, m) for m in ("easy", "medium", "hard", "impoppable"))
        written.append({"file": name, "source": route.source, "sourceFile": route.source_file,
                        "map": route.map, "mode": mode, "lossy": sorted(route.lossy)})

    lossy_routes = []
    for route in routes:
        try:
            lines = route.body()
        except Unsupported as error:
            log_rejects.append({"source": route.source, "sourceFile": route.source_file, "map": route.map,
                                "mode": route.mode, "reason": f"unsupported: {error}"})
            continue
        cls = CLASS_OF_MODE.get(route.mode)
        if cls and placed_groups(lines) - {cls}:
            log_rejects.append({"source": route.source, "sourceFile": route.source_file, "map": route.map,
                                "mode": route.mode, "reason": f"uses towers outside the {cls} class"})
            continue
        if not route.lossy:
            emit(route, route.mode, [], [], lines)
        elif route.mode in UNVERIFIED_OK:
            emit(route, route.mode, ["lossy"], [], lines)
        else:
            lossy_routes.append((route, lines))
    # Preserve lossy drafts for their source mode and applicable standard-mode alternatives.
    # Candidate eligibility is decided by the runner; a generated file does not prove victory.
    # Gameplay may earn missing medals only. There is no achievements/validation sweep,
    # and an owned map/mode must never be replayed to confirm one of these drafts.
    for route, lines in lossy_routes:
        emit(route, route.mode, ["lossy"], [], lines)
        used = False
        if route.mode in ("chimps", "impoppable"):
            for mode in ("easy", "medium", "hard"):
                if (route.map, mode) not in covered:
                    emit(route, mode, ["lossy", "fromChimps" if route.mode == "chimps" else "fromImpoppable"],
                         [f"adapted: {route.mode} build replayed on {mode} (more cash and lives than the source mode)"],
                         lines)
                    used = True
        log_rejects.append({"source": route.source, "sourceFile": route.source_file, "map": route.map,
                            "mode": route.mode,
                            "reason": "written as an unverified #lossy draft for its own mode (drops "
                                      + "; ".join(sorted(route.lossy)) + "), "
                                      + ("and also for uncovered easy/medium/hard" if used else
                                         "easy/medium/hard already covered" if route.mode in ("chimps", "impoppable") else "not chimps/impoppable, so no easy/medium/hard cascade")})

    compat_written = compat_copies(covered, bodies, written, log_rejects)
    validation = validate([w["file"] for w in written + compat_written])
    created = {w['file'] for w in written + compat_written}
    if any(f not in created for f in validation):
        raise ValueError('validator returned a recording outside this import batch')
    bad = {f: e for f, e in validation.items() if e}
    for f, e in bad.items():
        (PT / f).unlink()
        entry = next(w for w in written + compat_written if w["file"] == f)
        log_rejects.append({"source": entry.get("source", "compat"), "sourceFile": entry.get("sourceFile"),
                            "map": entry["map"], "mode": entry["mode"], "reason": f"failed AutoBTD6 parse validation: {e}"})
    written = [w for w in written if w["file"] not in bad]
    compat_written = [w for w in compat_written if w["file"] not in bad]
    report = {"generatedAt": datetime.now(timezone.utc).isoformat(), "written": written,
              "compatCopies": compat_written, "rejected": log_rejects}
    (LIB / "metadata" / "public-route-import.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"written": len(written), "compatCopies": len(compat_written), "rejected": len(log_rejects),
                      "validationFailures": len(bad)}, indent=2))


# AutoBTD6 helper.listBTD6InstructionsFileCompatability, restricted to what automation.js does not
# already reuse on its own (it reuses CHIMPS routes for easy/medium/hard/impoppable).
COMPAT = {"chimps": ["hard", "medium", "easy"], "hard": ["medium", "easy"], "medium": ["easy"],
          "magic_monkeys_only": ["hard", "medium", "easy"], "double_hp_moabs": ["hard", "medium", "easy"],
          "half_cash": ["hard", "medium", "easy"], "impoppable": ["hard", "medium", "easy"],
          "military_only": ["medium", "easy"], "primary_only": ["easy"]}
CLASS_COMPAT = {"magic": ("magic_monkeys_only", {"hard", "double_hp_moabs", "half_cash", "impoppable", "chimps"}),
                "military": ("military_only", {"medium", "hard", "double_hp_moabs", "half_cash", "impoppable", "chimps"}),
                "primary": ("primary_only", {"easy", "medium", "hard", "double_hp_moabs", "half_cash", "impoppable", "chimps"})}
DIFFICULTY_RANK = {m: i for i, m in enumerate(["chimps", "impoppable", "half_cash", "double_hp_moabs",
                                               "magic_monkeys_only", "hard", "military_only", "medium",
                                               "primary_only", "easy"])}


def trusted(route):
    flags = route["flags"]
    if route["own"] and ("lossy" in flags or "compat" in flags):
        return False
    if "generated" in flags or "compat" in flags:
        return False
    guide = GUIDES.get(route["file"])
    return not (guide and not guide.get("sourceClaimsWin"))


def compat_copies(covered, bodies, written, log_rejects):
    out = []
    candidates = {}
    for r in existing_routes():
        if not trusted(r) or r["mode"] not in MODES:
            continue
        lines = route_body(PT / r["file"])
        groups = placed_groups(lines)
        targets = list(COMPAT.get(r["mode"], []))
        if len(groups) == 1:
            cls_mode, allowed = CLASS_COMPAT.get(next(iter(groups)), (None, set()))
            if cls_mode and r["mode"] in allowed:
                targets.append(cls_mode)
        for target in targets:
            candidates.setdefault((r["map"], target), []).append((r, lines))
    for (map_, target), options in sorted(candidates.items()):
        if (map_, target) in covered:
            continue
        # Prefer AutoBTD6's own recordings, then the closest harder source mode, then 2560x1440.
        options.sort(key=lambda o: ("converted" in o[0]["flags"] or o[0]["own"], -DIFFICULTY_RANK[o[0]["mode"]],
                                    o[0]["res"] != "2560x1440", o[0]["file"]))
        source, lines = options[0]
        stem = "#".join([map_, target, source["res"], *[f for f in source["flags"] if f not in ("converted",)],
                         "compat", f"from_{source['mode']}"])
        stem = re.sub(r"#+", "#", stem)
        name = f"{stem}.btd6"
        if (PT / name).exists():
            continue
        meta = [f"compatibility copy of {source['file']}",
                f"rule: AutoBTD6 helper.listBTD6InstructionsFileCompatability lists {source['mode']} routes"
                f" as compatible with {target}; route lines are unchanged"]
        original_header = [l[2:] for l in (PT / source["file"]).read_text(encoding="utf-8").splitlines()
                           if l.startswith("# source")]
        meta += [f"original {l}" for l in original_header]
        (PT / name).write_text("\n".join(header(meta) + lines) + "\n", encoding="utf-8")
        covered.add((map_, target))
        out.append({"file": name, "source": "compat", "sourceFile": source["file"], "map": map_, "mode": target})
    return out


VALIDATOR = r"""
import io, json, sys, contextlib, re
sys.argv = ['validator']
from helper import parseBTD6InstructionsFile, towers, maps
result = {}
for name in json.load(sys.stdin):
    path = 'playthroughs/' + name
    res = [int(v) for v in name.split('#')[2].split('x')]
    mode = name.split('#')[1]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        config = parseBTD6InstructionsFile(path, targetResolution=res, gamemode=mode)
    errors = []
    if config is None:
        errors.append('parser returned None')
    else:
        text = open(path, encoding='utf-8').read()
        body = [l for l in text.splitlines() if l.strip() and not l.startswith('#')]
        expected = sum(1 for l in body if re.match(r'^(place|upgrade|retarget|special|sell|remove|click|ability|repeat|stop|round|cash|wait|speed|start|change|move|autostart|source|play) ', l))
        actual = sum(1 for s in config['steps'] if s['action'] in ('place', 'upgrade', 'retarget', 'special', 'sell', 'remove', 'ability', 'repeat_ability', 'stop_ability', 'await_round', 'await_cash', 'await_delay', 'speed', 'speed_toggle', 'start_round', 'move_cursor', 'set_autostart', 'source_round', 'play_once', 'play_twice')
                     or (s['action'] == 'click' and s.get('name') == 'map'))
        if expected != actual or expected != len(body):
            errors.append(f'{len(body)} lines, {expected} recognised, {actual} parsed')
        for m in config['monkeys'].values():
            x, y = m['pos']
            if not (0 <= x < res[0] and 0 <= y < res[1]):
                errors.append(f'{m["name"]} outside resolution')
        if config['map'] not in maps:
            errors.append('unknown map')
    printed = buf.getvalue().strip()
    if printed:
        errors.append(printed[:300])
    result[name] = '; '.join(errors)
print(json.dumps(result))
"""


def validate(files):
    python = ROOT / ".venv" / "Scripts" / "python.exe"
    environment = os.environ.copy()
    local_ahk = ROOT / '.venv' / 'Scripts' / 'AutoHotkey.exe'
    if local_ahk.is_file():
        environment['AHK_PATH'] = str(local_ahk)
    proc = subprocess.run([str(python if python.exists() else sys.executable), "-c", VALIDATOR], cwd=AUTO,
                          input=json.dumps(files), capture_output=True, text=True, timeout=600, env=environment)
    if proc.returncode != 0:
        raise SystemExit(f"validator failed: {proc.stderr[-2000:]}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def emit_manual_candidates():
    """Add complete logical-loop adaptations; keep all existing recordings."""
    written, skipped = [], []
    for path in sorted(BTD6BOT_PLANS.glob('*.py')):
        try:
            route = convert_btd6bot(path)
            if not route.source_round_trace:
                continue
            lines = route.body()
        except (Unsupported, KeyError, IndexError, ValueError) as error:
            skipped.append({'sourceFile': path.name, 'reason': str(error)})
            continue
        if route.lossy:
            skipped.append({'sourceFile': path.name, 'reason': '; '.join(sorted(route.lossy))})
            continue
        source = SOURCES[route.source]
        name = f'{route.map}#{route.mode}#{W}x{H}#converted#source_{route.source}#manual-preserved.btd6'
        target = PT / name
        meta = [f"source: {source['repo']} (license {source['license']}) commit {source['commit']}",
                f'source file: {route.source_file}',
                'Logical source-loop order, Auto Start, forward inputs and end_round delays/skip flags preserved.',
                'Play inputs require observed transitions; timing includes controller observation latency.',
                'Offline-converted candidate; no local victory claimed. Original recordings preserved.']
        content = '\n'.join(header(meta) + lines) + '\n'
        if target.exists() and target.read_text(encoding='utf-8') != content:
            raise RuntimeError(f'Refusing to overwrite changed manual candidate: {name}')
        if not target.exists():
            target.write_text(content, encoding='utf-8', newline='\n')
        written.append(name)
    errors = {name: error for name, error in validate(written).items() if error} if written else {}
    if errors:
        raise RuntimeError('Manual candidate parser errors: ' + json.dumps(errors))
    print(json.dumps({'manualCandidates': written, 'skipped': skipped, 'parserErrors': errors}, indent=2))


def emit_timing_candidates():
    """Add complete timing-preserved candidates without replacing any recording."""
    written = []
    sources = [(convert_btd6bot, path) for path in sorted(BTD6BOT_PLANS.glob('*.py'))]
    sources += [(convert_everythingmacro, path) for path in sorted((PUB / 'ThuyTran735-BTD6-Everything-Macro' / 'Maps').rglob('*.ahk')) if path.name != 'MapTemplate.ahk']
    for converter, source_path in sources:
        if source_path.name.startswith('_'):
            continue
        try:
            route = converter(source_path)
            lines = route.body()
        except (Unsupported, KeyError, IndexError, ValueError):
            continue
        if route.lossy or not any(line.startswith('wait ') or re.match(r'^round \d+ after ', line) for line in lines):
            continue
        source = SOURCES[route.source]
        name = f'{route.map}#{route.mode}#{W}x{H}#converted#source_{route.source}#timing-preserved.btd6'
        target = PT / name
        meta = [f"source: {source['repo']} (license {source['license']}) commit {source['commit']}",
                f"source file: {route.source_file}",
                ('Round-relative offsets preserved against observed round starts; no source actions omitted.' if route.source == 'everythingmacro' else 'Explicit waits preserved; no source actions omitted except zero waits and bare-name no-ops.'),
                'Offline-converted candidate; no local victory claimed. Original recordings preserved.']
        content = '\n'.join(header(meta) + lines) + '\n'
        if target.exists() and target.read_text(encoding='utf-8') != content:
            raise RuntimeError(f'Refusing to overwrite changed timing candidate: {name}')
        if not target.exists():
            target.write_text(content, encoding='utf-8', newline='\n')
        written.append({'file': name, 'sourceFile': route.source_file,
                        'map': route.map, 'mode': route.mode,
                        'waits': sum(line.startswith('wait ') for line in lines)})
    print(json.dumps({'timingCandidates': written}, indent=2))


def emit_cursor_candidates():
    """Preserve explicit source cursor movements in separate complete candidates."""
    written = []
    for path in sorted(BTD6BOT_PLANS.glob('*.py')):
        if path.name.startswith('_'):
            continue
        try:
            route = convert_btd6bot(path)
            lines = route.body()
        except (Unsupported, KeyError, IndexError, ValueError):
            continue
        if route.lossy or not any(line.startswith('move cursor to ') for line in lines):
            continue
        source = SOURCES[route.source]
        name = f'{route.map}#{route.mode}#{W}x{H}#converted#source_{route.source}#cursor-preserved.btd6'
        target = PT / name
        meta = [f"source: {source['repo']} (license {source['license']}) commit {source['commit']}",
                f"source file: {route.source_file}",
                'Explicit move-only cursor targets and waits preserved. No gameplay commands omitted.',
                'Offline-converted candidate; no local victory claimed. Original recordings preserved.']
        content = '\n'.join(header(meta) + lines) + '\n'
        if target.exists() and target.read_text(encoding='utf-8') != content:
            raise RuntimeError(f'Refusing to overwrite changed cursor candidate: {name}')
        if not target.exists():
            target.write_text(content, encoding='utf-8', newline='\n')
        written.append({'file': name, 'map': route.map, 'mode': route.mode})
    failures = {name: error for name, error in validate([item['file'] for item in written]).items() if error}
    if failures:
        raise RuntimeError('Cursor candidate parser validation failed: ' + str(failures))
    print(json.dumps({'cursorCandidates': written}, indent=2))


def emit_ability_candidates():
    """New faithful command candidates only; never overwrite a recording."""
    written = []
    for path in sorted((PUB / 'piweiblen-BloonsPlayer').rglob('*.txt')):
        try:
            route = convert_bloonsplayer(path)
            lines = route.body()
        except (Unsupported, KeyError, IndexError, ValueError):
            continue
        if route.lossy or not any(line.startswith('repeat ability ') for line in lines):
            continue
        source = SOURCES[route.source]
        name = f'{route.map}#{route.mode}#{W}x{H}#converted#source_{route.source}#ability-preserved.btd6'
        target = PT / name
        meta = [f"source: {source['repo']} (license {source['license']}) commit {source['commit']}",
                f"source file: {route.source_file}",
                'Repeated ability keys and cancellation preserved; seconds waits remain non-blocking.',
                'Offline-converted candidate; no local victory claimed. Original recordings preserved.']
        content = '\n'.join(header(meta) + lines) + '\n'
        if target.exists() and target.read_text(encoding='utf-8') != content:
            raise RuntimeError(f'Refusing to overwrite changed ability candidate: {name}')
        if not target.exists():
            target.write_text(content, encoding='utf-8', newline='\n')
        written.append(name)
    errors = {name: error for name, error in validate(written).items() if error} if written else {}
    if errors:
        raise RuntimeError('Ability candidate parser errors: ' + json.dumps(errors))
    print(json.dumps({'abilityCandidates': written, 'parserErrors': errors}, indent=2))


def emit_round_start_candidates():
    """Separate startup-intent adaptations; no original recording is replaced."""
    written = []
    plans = [(path, convert_bloonsplayer) for path in sorted((PUB / 'piweiblen-BloonsPlayer').rglob('*.txt'))]
    plans += [(path, convert_randyhodges) for path in sorted((PUB / 'Randy-Hodges-BTD6-Autoplay').rglob('*_script.py'))]
    for path, convert in plans:
        try:
            route = convert(path)
            lines = route.body()
        except (Unsupported, KeyError, IndexError, ValueError):
            continue
        if route.lossy or sum(line.startswith('start round ') for line in lines) != 1:
            continue
        source = SOURCES[route.source]
        name = f'{route.map}#{route.mode}#{W}x{H}#converted#source_{route.source}#observed-start.btd6'
        target = PT / name
        meta = [f"source: {source['repo']} (license {source['license']}) commit {source['commit']}",
                f'source file: {route.source_file}', f'generator: {GENERATOR}',
                'Startup intent adapted to observed play/speed confirmation, not literal double-Space timing.',
                'Recorded tower positions/upgrades retained. No original recording replaced; no local victory claimed.']
        content = '\n'.join(header(meta) + lines) + '\n'
        if target.exists() and target.read_text(encoding='utf-8') != content:
            raise RuntimeError(f'Refusing to overwrite changed startup candidate: {name}')
        if not target.exists():
            target.write_text(content, encoding='utf-8', newline='\n')
        written.append(name)
    errors = {name: error for name, error in validate(written).items() if error} if written else {}
    if errors:
        raise RuntimeError('Startup candidate parser errors: ' + json.dumps(errors))
    print(json.dumps({'startupCandidates': written, 'parserErrors': errors}, indent=2))


def emit_speed_candidates():
    """Preserve relative controls in separate candidates, never replace recordings."""
    written = []
    for path in sorted((PUB / 'piweiblen-BloonsPlayer').rglob('*.txt')):
        try:
            route = convert_bloonsplayer(path)
            lines = route.body()
        except (Unsupported, KeyError, IndexError, ValueError):
            continue
        if route.lossy or 'change speed' not in lines:
            continue
        source = SOURCES[route.source]
        name = f'{route.map}#{route.mode}#{W}x{H}#converted#source_{route.source}#speed-preserved.btd6'
        meta = [f"source: {source['repo']} (license {source['license']}) commit {source['commit']}",
                f'source file: {route.source_file}', f'generator: {GENERATOR}',
                'Relative speed input adapted to observed, checkpointed play-state confirmation.',
                'Recorded placements and upgrades retained. No original replaced; no local victory claimed.']
        content = '\n'.join(header(meta) + lines) + '\n'
        target = PT / name
        if target.exists() and target.read_text(encoding='utf-8') != content:
            raise RuntimeError(f'Refusing to overwrite changed speed candidate: {name}')
        if not target.exists():
            target.write_text(content, encoding='utf-8', newline='\n')
        written.append(name)
    errors = {name: error for name, error in validate(written).items() if error} if written else {}
    if errors:
        raise RuntimeError('Speed candidate parser errors: ' + json.dumps(errors))
    print(json.dumps({'speedCandidates': written, 'parserErrors': errors}, indent=2))


def emit_spike_target_candidates(target_mode='smart'):
    """Keep source Spike targeting in separate candidates; preserve recordings."""
    if target_mode not in ('smart', 'close', 'cycle'):
        raise Unsupported('unsupported Spike target candidate mode')
    written = []
    for path in sorted(BTD6BOT_PLANS.glob('*.py')):
        if path.name.startswith('_'):
            continue
        if target_mode == 'cycle' and path.name not in ('last_resortHardChimps.py', 'erosionHardChimps.py'):
            continue
        try:
            route = convert_btd6bot(path)
            lines = route.body()
        except (Unsupported, KeyError, IndexError, ValueError):
            continue
        if route.lossy or not any(state.get('spikeTarget') in (
                ('normal', 'close', 'smart', 'set', 'automatic') if target_mode == 'cycle' else (target_mode,))
                for state in route.towers.values()):
            continue
        source = SOURCES[route.source]
        suffix = {'smart':'spike-target-preserved', 'close':'spike-close-preserved', 'cycle':'spike-cycle-preserved'}[target_mode]
        name = f'{route.map}#{route.mode}#{W}x{H}#converted#source_{route.source}#{suffix}.btd6'
        meta = [f"source: {source['repo']} (license {source['license']}) commit {source['commit']}",
                f'source file: {route.source_file}', f'generator: {GENERATOR}',
                ({'smart':'Spike Factory Normal to Smart targeting preserved as two forward presses.',
                  'close':'Spike Factory Normal to Close targeting preserved as one forward press.',
                  'cycle':'Spike Factory targeting preserved through Tier 5, with source reverse inputs and Set clicks.'}[target_mode]),
                'Recorded placements and upgrades retained. No original replaced; no local victory claimed.']
        content = '\n'.join(header(meta) + lines) + '\n'
        target = PT / name
        if target.exists() and target.read_text(encoding='utf-8') != content:
            raise RuntimeError(f'Refusing to overwrite changed Spike target candidate: {name}')
        if not target.exists():
            target.write_text(content, encoding='utf-8', newline='\n')
        written.append(name)
    errors = {name: error for name, error in validate(written).items() if error} if written else {}
    if errors:
        raise RuntimeError('Spike target candidate parser errors: ' + json.dumps(errors))
    print(json.dumps({'spikeTargetCandidates': written, 'parserErrors': errors}, indent=2))


def emit_selection_candidates():
    """Keep source cpos selection updates in separate complete candidates."""
    written = []
    for source in sorted((ROOT / 'btd6bot/btd6bot/plans').glob('*.py')):
        try:
            route = convert_btd6bot(source)
        except Unsupported:
            continue
        lines = route.body()
        selectors = [line for line in lines if re.match(r'^(upgrade|retarget|special|sell)\s.+ at \d+, \d+$', line)]
        if route.lossy or not selectors:
            continue
        name = f'{route.map}#{route.mode}#{W}x{H}#converted#source_{route.source}#selection-preserved.btd6'
        info = SOURCES[route.source]
        content = '\n'.join(header([
            f"source: {info['repo']} (license {info['license']}) commit {info['commit']}",
            'source file: ' + route.source_file,
            'generator: ' + GENERATOR,
            'Source selection-position updates and their persistence preserved. No gameplay commands omitted.',
            'Candidate is unverified until victory and saved medal are confirmed.',
        ]) + lines) + '\n'
        target = PT / name
        if target.exists() and target.read_text(encoding='utf-8') != content:
            raise RuntimeError('Refusing to overwrite changed selection candidate: ' + name)
        if not target.exists():
            target.write_text(content, encoding='utf-8', newline='\n')
        written.append(name)
    errors = {name:error for name,error in validate(written).items() if error} if written else {}
    if errors:
        raise RuntimeError('Selection candidate parser errors: ' + json.dumps(errors))
    print(json.dumps({'selectionCandidates':written,'parserErrors':errors}, indent=2))


def emit_special_target_candidates():
    """Preserve targetable special-1 commands in new complete candidates only."""
    written = []
    for path in sorted((ROOT / 'btd6bot/btd6bot/plans').glob('*.py')):
        try:
            route = convert_btd6bot(path)
        except Unsupported:
            continue
        lines = route.body()
        if route.lossy or not any(re.match(r'^special \w+ to \d+, \d+', line) for line in lines):
            continue
        name = f'{route.map}#{route.mode}#{W}x{H}#converted#source_{route.source}#special-target-preserved.btd6'
        info = SOURCES[route.source]
        content = '\n'.join(header([
            f"source: {info['repo']} (license {info['license']}) commit {info['commit']}",
            'source file: ' + route.source_file,
            'generator: ' + GENERATOR,
            'Special-1 target clicks and independent tower selection coordinates preserved. No gameplay commands omitted.',
            'Candidate is unverified until victory and saved medal are confirmed.',
        ]) + lines) + '\n'
        target = PT / name
        if target.exists() and target.read_text(encoding='utf-8') != content:
            raise RuntimeError('Refusing to overwrite changed special target candidate: ' + name)
        if not target.exists():
            target.write_text(content, encoding='utf-8', newline='\n')
        written.append(name)
    errors = {name:error for name,error in validate(written).items() if error} if written else {}
    if errors:
        raise RuntimeError('Special target candidate parser errors: ' + json.dumps(errors))
    print(json.dumps({'specialTargetCandidates':written,'parserErrors':errors}, indent=2))


def audit_legacy_timing():
    """Read-only inventory of legacy timing omissions; never launch or rewrite routes."""
    files = sorted(PT.glob('*.btd6'))
    alternatives = {tuple(path.stem.split('#')[:2]) for path in files if '#timing-preserved' in path.name}
    findings = []
    for path in files:
        fields = path.stem.split('#')
        for raw in path.read_text(encoding='utf-8-sig').splitlines():
            match = re.match(r'^#\s*dropped \(timing only\):\s*(.*)$', raw, re.I)
            if not match:
                continue
            omitted = [item.strip() for item in match.group(1).split(';') if item.strip()]
            relevant = [item for item in omitted if re.search(
                r'\b(wait|delay|delays|forward|end_round|change_autostart|move_cursor|start|finish|toggle|change|lives)\b', item, re.I)]
            if relevant:
                findings.append({'file': path.name, 'map': fields[0], 'mode': fields[1] if len(fields) > 1 else None,
                                 'omitted': relevant, 'lossyFlag': 'lossy' in fields,
                                 'timingAlternativePresent': tuple(fields[:2]) in alternatives,
                                 'status': 'source-semantics-review-required'})
    return {'scanned': len(files), 'affected': len(findings), 'findings': findings,
            'note': 'Headers identify review candidates, not proof of a defect or victory. Original recordings unchanged.'}


if __name__ == "__main__":
    if '--audit-timing' in sys.argv:
        print(json.dumps(audit_legacy_timing(), indent=2))
    elif '--manual-candidates' in sys.argv:
        emit_manual_candidates()
    elif '--special-target-candidates' in sys.argv:
        emit_special_target_candidates()
    elif '--ability-candidates' in sys.argv:
        emit_ability_candidates()
    elif '--round-start-candidates' in sys.argv:
        emit_round_start_candidates()
    elif '--speed-candidates' in sys.argv:
        emit_speed_candidates()
    elif '--spike-close-candidates' in sys.argv:
        emit_spike_target_candidates('close')
    elif '--spike-cycle-candidates' in sys.argv:
        emit_spike_target_candidates('cycle')
    elif '--spike-target-candidates' in sys.argv:
        emit_spike_target_candidates()
    elif '--selection-candidates' in sys.argv:
        emit_selection_candidates()
    elif '--cursor-candidates' in sys.argv:
        emit_cursor_candidates()
    elif '--timing-candidates' in sys.argv:
        emit_timing_candidates()
    else:
        main()
