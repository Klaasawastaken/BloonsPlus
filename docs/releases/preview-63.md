# Bloons+ Preview 63

## Consistent medal decoding

- The UI and sweep now use one shared read-only medal decoder instead of duplicated rules.
- Preserves exact mode/difficulty mapping, ordinary CHIMPS handling, earned/missing/unknown values and existing public interfaces.
- Includes the dedicated-route priority correction, compact failure-log browsing and placement-panel confirmation.

## Verification

Existing authoritative medal admission, aliases and observation-precedence checks pass before and after the extraction. Browser/server parity covers all 14 supported modes across 14 value schemas; inputs are unchanged. No game saves or original recordings are modified. VM deployment remains between replays; no universal route-win claim is made.
