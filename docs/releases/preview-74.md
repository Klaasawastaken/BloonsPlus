# Bloons+ Preview 74

## Exclude old copies with omitted target commands

- Extended the pinned-source conversion audit to count targeted special commands separately from moved-tower selectors.
- Guarded 23 exact recording versions with source omissions: missing selection updates, missing targeted special commands, or both.
- Preserved the existing exact-file-hash guard and saved-clear exception. Original recordings remain unchanged.
- The 14 new target-preserving candidates remain available; offline eligibility stays at 521/1,204 map/mode pairs.

## Checks

Read-only audit checks compare the guard with pinned-source findings and exact recording hashes. All 14 new candidates retain their required selectors and targeted commands. Existing route selection and saved-clear exception checks pass. No gameplay was launched for validation, and no new victory is claimed.
