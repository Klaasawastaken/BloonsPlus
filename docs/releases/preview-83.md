# Bloons+ Preview 83

## Manual-route compatibility

- Keep source logical round schedules tied to the actual starting round of the requested mode.
- Prevent unchanged manual CHIMPS plans starting at logical round 6 from being reused in Easy, Medium or Hard standard without matching target-mode evidence. Such reuse can stall on a HUD wait with Auto Start disabled.
- Apply the check to renamed recordings as well as automatic reuse. Dedicated CHIMPS and same-start Impoppable candidates remain available.
- Preserve approved ordinary-route reuse and exact-content target-mode wins.

## Verification and limits

The actual candidate-selection regression covers dedicated routes, renamed copies, normal reuse, same-start reuse and target-specific saved wins. The full coverage command passes its runtime-helper regression. Offline eligibility is 526 of 1,204 map/mode pairs, with 678 gaps and three maps without eligible routes. The difference from Preview 82 removes six unsupported schedule-reuse pairs; it does not remove the eight dedicated candidates.

Preview 82's pending VM update was held before installation while this issue was corrected. The current replay was left running. Original recordings, saved medals and persistent failures are unchanged. No new winning strategy is claimed.
