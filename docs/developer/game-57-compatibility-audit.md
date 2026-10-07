# Game 57 compatibility — 7 October 2026

This is an evidence record, not a declaration of full 57.0 support.

## New map and tower support

The [official 57.0 notes](https://www.reddit.com/r/btd6/comments/1wzgvfn/bloons_td_6_v570_update_notes/)
identify Ship Capture as an Advanced map and introduce the Sniper Paragon. They
also change Supply Drop behavior and permit disabling individual owned Monkey
Knowledge points.

A fresh, read-only VM profile response contains the exact map key `ShipCapture`.
This confirms the save identifier only. Its map-menu position, terrain behavior,
artwork and executable strategy still need evidence before route admission.
The profile decoder already exposes `paragonUpgradesPurchased`, but this
observation does not establish the Sniper Paragon's exact identifier or unlock
state. No account values are embedded in the catalog or published here.

## Reverse and Apopalypse visual fallback

The official notes state that the two map-menu badges exchanged positions.
`lib/map-order-scanner.js` still reads their earlier positions and ribbon colors.
Both direct tile recognition and inferred tile recognition call this same reader.

A private synthetic image probe called the unchanged production medal reader.
It supplied Easy, Medium and Military prerequisites, then both variation ribbons.
The legacy-position control returned both medals earned; exchanging the ribbon
positions returned both missing. This reproduces sensitivity to the documented
swap. It does not validate the new artwork, pixel thresholds or physical UI.

The save decoder uses named difficulty/mode fields and is independent of badge
coordinates. The running sweep uses that authoritative profile. The proposed
repair stops deriving these two ownership values from unverified screen slots,
retains saved medals and confirmed account history, and leaves unavailable
ownership unknown. Its design approval is pending; production behavior has not
been changed by this audit.

## Remaining acceptance

- Verify and integrate the new map without guessing its page or placements.
- Identify the Sniper Paragon from authoritative game data before exposing support.
- Cover the approved knowledge activation policy and other changed controls.
- Repair the reproduced fallback issue, with old/new-layout and absent-save checks.
- Observe gameplay only while earning missing medals; preserve original recordings.
