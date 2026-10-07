# Source controls preserved in four additional candidates

Added 7 October 2026. These are separate, unverified CHIMPS candidates for
**Bazaar, Geared, Sanctuary and Sunset Gulch**, using the pinned
[BTD6bot source](https://github.com/j-miet/BTD6bot/tree/2d6dac0957a0d55d0af201bd497afbebf7f3e5c2/btd6bot/plans).
The [manifest](../../route-library/metadata/complete-controls-routes-2026-10-07.json)
records source, handler and route hashes. The original
[MIT notice](licenses/btd6bot-LICENSE.txt) remains included.

## What was preserved

- Bazaar retains Rosalia's targeted second-special command omitted by the old
  lossy conversion. It uses the saved `TowerSpecial2` binding.
- Geared retains manual round flow, waits, seven targeted second-special commands
  and 38 explicit moved selectors. Review found that the source placement handler
  also initializes each Heli with one targeting press and a special-slot-1 click
  at its helipad. Four existing-syntax commands now explicitly preserve those
  inputs; raw converter output alone did not preserve the entire source behavior.
- Sanctuary retains manual rounds, waits and 50 explicit moved selectors.
- Sunset Gulch retains its complete manual flow, targeting and waits instead of
  the old lossy conversion's shortened action sequence.

No replay engine, importer, admission guard, prerequisite, attempt history or
original recording is changed. All 970 existing recording hashes were preserved.
Sulfur Springs is excluded from this batch because its source-coordinate
adaptation remains a separate unresolved review.

## Evidence and limits

The complete Python parser and JavaScript legality checks accept all four files:
1,285 executable instructions in total. No same-map/mode strategy signature
matches an existing recording. The source-handler review found and then verified
the Heli initialization repair; the final review found no remaining actionable
issue in the amendment. Opening placements cost 645, 595, 650 and 540 respectively
against the CHIMPS starting budget of 650, using bundled prices without Monkey
Knowledge. Later affordability and current-version performance remain unverified.

The actual catalog selection report rises from 545 to **553 of 1,204 pairs**,
leaving **651 gaps**. Existing compatibility rules account for eight additional
eligible pairs; four source candidates do not mean eight verified victories.
Required heroes, upgrades and saved control bindings must still pass the normal
runtime checks. Missing prerequisites remain blockers.

No BTD6 session was launched for route validation. These candidates may run only
for missing medals, after an idle-boundary deployment. A future clear requires
victory plus an authoritative saved medal. Already-owned medals remain skipped.
