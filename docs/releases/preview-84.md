# Bloons+ Preview 84

## Replay recovery

- Fix a single-Play receipt that could remain pending after a short round ended before speed confirmation. A confirmed higher, paused round now completes the receipt without pressing Play again or inventing a speed.
- Keep ongoing round progression insufficient for confirming a speed change. Unknown states, busy input, malformed counters and same-round pauses remain blocked.
- Allow explicit resume of a stopped round-control receipt. Validate its timing and route position; the runner still checks the source route hash, current map scene, round and tower ledger before sending input.
- Keep stopped purchases excluded from this resume path. Automatic resume still requires a ready checkpoint.

## Readable roadmap

- Organize the active TODO into priorities, a short immediate queue, named task IDs and smaller sections.
- Keep completed milestones separate and preserve detailed evidence in the history archive.

## Verification and limits

All 282 Python checks pass. Explicit-resume admission and candidate-selection, saved-binding and direct-route legality checks pass. The cursor-candidate preservation check now includes the #Ouch CHIMPS conversion whose manual controls became supported in Preview 82; original recordings remain unchanged.

The replay fix reproduces the observed Bloody Puddles Impoppable stall: a Play receipt issued from fast at round 13 remained pending while the live game showed a paused round 14. This release does not claim a new victory, universal timing equivalence or production readiness. No game or save files are modified.
