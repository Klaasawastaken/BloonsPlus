# Bloons+ Preview 62

## Dedicated routes before fallbacks

- Corrects candidate priority so a dedicated map/mode plan is preferred over a reused CHIMPS or Hard recording.
- Preserves exact target-mode confirmed wins as the highest priority.
- Keeps source-specific opening and placement timing, important on maps with effects tied to tower placement rounds.
- Retains persistent failure exclusions, missing-medal admission and fallback candidates when appropriate.

## Verification

Ordering regressions, candidate fallback checks and authoritative medal gates pass. The real route catalog now lists the dedicated Glacial Trail Hard plan first. Original CHIMPS recordings and route hashes are unchanged. This addresses selection priority; it does not claim every route wins or prove a single cause for all defeats.

Includes Preview 61's compact Run Logs view and full-log downloads.
