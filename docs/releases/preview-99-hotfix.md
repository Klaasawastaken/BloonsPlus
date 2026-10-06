# Bloons+ Preview 99 — Magic Placement Hotfix

## Additions

- Add offline checks for purple Magic Monkeys Only shop cards, supported resolutions, missing close controls and cancellation before tower selection.

## Changes

- Recognize held placement in Magic Monkeys Only's purple tower shop. The captured Balance failure frame was previously missed by cyan-only recognition, allowing selection attempts while placement remained active.
- Keep the existing placement-close anchor and two-shop-row requirements. A close control alone, one colored row or neutral shop colors cannot qualify. The normal cyan and cancel-button paths remain supported.
- Verify nine focused checks and all 365 Python tests. The captured private failure frame now qualifies. This is recognition and input-order evidence; a future missing-medal run must confirm live recovery and victory.
- Retain the complete Preview 99 controls, targeting, candidates and installer changes. Keep original CHIMPS recordings, saved progress and persistent route failures. Private account images and logs are excluded from publication.
- Rebuild the 235.4 MiB online installer. All 126 packaged runtime comparisons and 1,690 inventory hashes match; both executables retain seven exact application icon frames. Publication checks report no private-file findings. Clean-machine acceptance remains open.

## Removed

- Remove the cyan-only assumption that excluded Magic Monkeys Only's placement shop.
