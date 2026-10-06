# Bloons+ Preview 51

## Placement recovery

- Try same-tower positions from other routes on the current map after nearby recovery fails.
- Treat those positions as unverified hints, not confirmed legal spots.
- Require a positive live placement preview; unknown readings cannot authorize a distant hint.
- Keep occupancy, bounds and range checks. CHIMPS and changing terrain retain their existing recovery path.
- Permit one targeted fresh attempt for non-CHIMPS Infernal Heli routes, while preserving unrelated failure exclusions and owned-medal skipping.

## Hero picker and Settings

- Keep hero search clicks inside the three-column card grid instead of clicking old positions in the detail panel. Selection still requires the displayed hero and Selected state.
- Fold installation details and destructive preference/queue reset away from everyday Settings.
- Disable stale setup/update actions on HTTP connection failures and recheck availability after failed updates.

## Verification limits

Offline actual-function checks cover normalized coordinates, exact map/tower matching, deduplication, bounds, local-first search, unknown-preview rejection, occupancy/range checks and the CHIMPS/dynamic guards. Existing HUD/placement and attempt-exclusion checks pass. No validation-only game was launched. Infernal Heli recovery has not yet earned a new medal; full V1.0 coverage remains unfinished.
