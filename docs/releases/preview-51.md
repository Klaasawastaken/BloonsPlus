# Bloons+ Preview 51

## Placement recovery

- Try same-tower positions from other routes on the current map after nearby recovery fails.
- Treat those positions as unverified hints, not confirmed legal spots.
- Require a positive live placement preview; unknown readings cannot authorize a distant hint.
- Keep occupancy, bounds and range checks. CHIMPS and changing terrain retain their existing recovery path.
- Permit one targeted fresh attempt for non-CHIMPS Infernal Heli routes, while preserving unrelated failure exclusions and owned-medal skipping.

## Verification limits

Offline actual-function checks cover normalized coordinates, exact map/tower matching, deduplication, bounds, local-first search, unknown-preview rejection, occupancy/range checks and the CHIMPS/dynamic guards. Existing HUD/placement and attempt-exclusion checks pass. No validation-only game was launched. Infernal Heli recovery has not yet earned a new medal; full V1.0 coverage remains unfinished.
