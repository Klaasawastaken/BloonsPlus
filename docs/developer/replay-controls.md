# Replay timing and ability controls

These commands supplement recorded tower placements and upgrades. They do not prove that a strategy wins. The sweep attempts candidates only for missing medals; original CHIMPS recordings must not be rewritten.

## Command reference

| Command | Meaning |
| --- | --- |
| `wait 2.5 seconds` | Wait without blocking screenshot observation. |
| `round 40` | Wait for the observed round to reach 40. |
| `round 40 after 5 seconds` | Wait until five seconds after the observed start of round 40. |
| `ability 1` | Issue the currently bound first ability key once. |
| `ability 2 after 3 seconds` | Gate against the observed round-start anchor; preserve the first deadline. |
| `ability 1 at 800, 400` | Issue the key, then move and click the recorded target. |
| `ability 1 at 800, 400 move after 2 seconds` | Issue the key once, then defer the recorded move-only targeting continuation. |
| `repeat ability 1` | Register recurring use of the first ability slot. |
| `stop ability 1` | Remove one recurring registration for that slot. |
| `stop all abilities` | Cancel all recurring registrations. |

Slots are 1–10. Canonical slot 10 uses the detected tenth ability binding; BloonsPlayer's literal key `0` converts to this slot. Other unmapped upstream keys are rejected. A slot refers to the current ability bar, not a permanently identified tower. Strategies must account for abilities becoming available or the bar order changing.

## Scheduler and input ownership

`RepeatedAbilities` in `autobtd6/route_timing.py` schedules a cycle of registered entries over at least one second. Duplicate registrations are preserved; stopping a slot removes one occurrence. It runs inside the replay's input-owning loop rather than a competing input thread.

Input waits during route actions, held/retrying placements, pending delayed ability targeting, speed toggles, and uncertain or non-playing frames. Delayed iterations never replay a backlog of missed keypresses. A logged issued key is not proof that the game activated an ability or that its cooldown was ready.

Repeats persist across rounds until cancellation. This follows the [pinned BloonsPlayer implementation](https://github.com/piweiblen/BloonsPlayer/blob/17d624879c5ad777e82594da34450e66b2d60756/src/player.py), whose behavior differs from its README's round-end description.

## Checkpoints

Repeat checkpoints store slot registrations, including duplicates. They do not store arbitrary input keys or old clock deadlines. Resume resolves those slots against the current game bindings. A new map initializes an empty scheduler. Wait and delayed-target checkpoints retain their validated continuation metadata; malformed values are rejected.

## Tower selection and observation

`select_tower` in `autobtd6/upgrade_observation.py` checks whether a detected panel covers the requested world position. Hero panels lack path-tier pips, so the reader also uses independent HUD anchors. A covering panel is closed with two centre clicks before selection; an uncovered position receives its normal selection click. This does not use Escape or open the pause menu.

Upgrade observation confirms tier pips and availability before purchase input. Cash changes alone cannot prove an upgrade succeeded, because pop income, free towers and Monkey Knowledge can change the expected balance.

## Offline checks

Run from the repository root using the configured Python runtime:

```powershell
.venv/Scripts/python.exe -X utf8 tests/test_repeated_abilities.py
.venv/Scripts/python.exe -X utf8 tests/test_route_timing.py
.venv/Scripts/python.exe -X utf8 tests/test_panel_selection.py
.venv/Scripts/python.exe -X utf8 tests/test_upgrade_observation.py
.venv/Scripts/python.exe -X utf8 tests/test_upgrade_queue.py
node tests/test-route-syntax.js
```

The importer option `--ability-candidates` creates separately named complete conversions with recurring abilities and validates their parser output. It refuses to overwrite changed candidates and excludes conversions with remaining omitted commands. Offline checks establish command handling and legality, not in-game victory. Observe gameplay only as the sweep earns missing medals.

## Manual round controls: remaining work

Run `tools/audit-round-controls.py` for a read-only source inventory. The saved report is `data/reports/round-controls-audit.json`. It records exact commands, source line numbers and remaining conversion omissions without rewriting routes or launching BTD6.

The pinned BloonsPlayer implementation uses these controls:

- `change speed` presses Space once. It is a toggle, not an absolute speed request.
- `start round` presses Space, waits the configured input delay, then presses Space again. Only a first argument equal to `slow` removes the second press. Arguments are comma-separated and stripped of parentheses/spaces.
- `toggle autostart` opens pause settings, attempts detected on/off clicks in a three-iteration loop, then closes settings. A failed detection is logged. Its opening sequence can also enable autostart when the upstream user's `ensure autostart` preference is set.

These operations are still omitted and flagged as lossy. Supporting them requires an observed starting state, serialized input ownership, and explicit coordination with the replay's automatic round controller. Checkpoints must distinguish an input already issued from a control confirmed by a later frame; blindly repeating a toggle on resume could undo it. Preserve actual victory/defeat observation after recorded controls end.

The 6 October audit found 12 affected files among 83 source scripts: 11 convert as lossy and one race script is rejected. Six routes have only a round-start omission: Balance CHIMPS, Quarry CHIMPS, Dark Castle Deflation, #Ouch Hard, Ravine Hard and Workshop Hard. This identifies the next implementation candidates; it does not prove those strategies win or authorize replaying owned medals. Original CHIMPS recordings remain unchanged.

### Unregistered source waits

A follow-up audit found six nonzero `wait` commands across Glacial Trail Easy/Hard and Infernal Hard. The pinned runner registers `TAS_delay` but has no `wait` handler. Seconds waits are an interpretation of those scripts, not demonstrated source equivalence; the importer retains the interpreted command in a review draft. The Glacial Trail Easy ability candidate is now labelled lossy, and the old installed filename is treated as a draft too. The audit now identifies 15 affected scripts (14 lossy, one rejected). Restoring these strategies requires reviewing their intended timing and map mechanics. Source-supported `delay` still converts faithfully.
