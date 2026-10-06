# Bloons+ Preview 73

## Preserve targeted tower specials

- Added `special tower to x, y` route commands, including an independent `at x, y` selector for moved towers.
- Replay sends the special hotkey, waits for targeting, moves to the destination, then clicks once. Existing targeting and untargeted special commands retain their behavior.
- Recording, resolution scaling, parser and offline validation retain both coordinates.
- Converted 14 new separate candidates from pinned BTD6bot sources, including dedicated Sanctuary Medium. Candidates with other omitted commands remain excluded.
- Original recordings, including CHIMPS, were not rewritten. New candidates remain unverified until victory and a saved medal are confirmed.

## Checks and remaining work

Three targeted-special tests, four selector/parser/recording tests, four Spike conversion tests, route grammar checks and publication checks pass. Full parser reports no errors for the 14 candidates.

Current eligibility is 521/1,204 map/mode pairs, with 683 gaps. Eligibility does not prove victory. Second-special commands, manual round controls and other conversion gaps still require work.
