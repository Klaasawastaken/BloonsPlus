## Additions

- Remember authoritative saved medals separately for each Steam save source, including across sweep restarts.
- Keep new route-attempt records separate by save source while retaining existing failure history.

## Changes

- Skip an owned medal even if a later save read regresses or another route candidate becomes available.
- Bind clear confirmation to the save source used at launch; stop safely if that source changes.
- Persist ownership before Stop after replay exits, and preserve the exact positive snapshot at the final launch gate.
- Keep missing records unknown when switching save sources instead of inheriting another source's completion.
- Extend publication checks to reject the private progress ledger.

## Removed

- Removed cross-source clear credit and inherited completion assumptions from the medal sweep.
