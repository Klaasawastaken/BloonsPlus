# Bloons+ development roadmap

## Phase 1: reliable deterministic automation

Keep the current AutoBTD6 strategy runner usable while improving it in this order:

1. Stabilize AutoBTD6 interaction, screen recognition, map/mode navigation, and recovery.
2. Finish and validate the BTD6bot integration behind the same gameplay controls.
3. Define a shared strategy format and standardized action interface for placement, upgrades,
   selling, targeting, abilities, round control, and waits.
4. Expand deterministic coverage across every map and the installed game's standard difficulties
   and modes, including Easy Standard, Primary Only, Deflation, Medium Standard, Military Only,
   Reverse, Apopalypse, Hard Standard, Magic Monkeys Only, Double HP MOABs, Half Cash, Alternate
   Bloons Rounds, Impoppable, CHIMPS, and any other current modes found in-game.
5. Record reliable map, mode, round, cash, tower, upgrade, targeting, ability, and result data from
   runs; use it to validate and recover deterministic strategies.
6. Keep map order and route coverage broad, and make testing/recovery and logs reliable.

## Phase 2: future autonomous AI

Do not start AI until deterministic automation has broad, tested coverage. Then add a rule-based
agent that observes the shared GameState and emits the same standardized actions as deterministic
strategies. It must not issue raw coordinates or bypass AutoBTD6's interaction layer. Keep the
deterministic strategy mode fully usable alongside AI mode.

## Engine tabs

Automation V2 (btd6_autoplay) and Automation V3 (BTD6bot) were removed from the app navigation and
server API. Their vendored source trees remain in the workspace for reference; AutoBTD6 remains the
only exposed gameplay automation engine until the shared strategy/action architecture is ready.
