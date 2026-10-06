# Bloons+ Preview 99 — Finished-route HUD Hotfix

## Additions

- Add eight offline recovery checks, including the actual replay gate, fresh captures, changed result screens, missing frames, pending action ownership and supported scales.

## Changes

- Keep checking an unreadable HUD after the last route action. The old cash/round gate could skip panel recovery once the action queue was empty.
- Wait one second and capture a fresh in-game frame before recovering. Cancel an observed leftover placement using its close control; use two centre clicks for a positively observed tower panel. Unknown or unobstructed layouts receive no recovery clicks.
- Capture again before the second centre click, so a newly visible victory, defeat or missing frame cannot authorize it from older pixels.
- Preserve pending placement, ability and round controls. Recheck replay ownership, focus and pause state, and prevent automatic Play or repeated abilities from using the frame preceding recovery input.
- Verify eight focused checks, all 373 Python tests and the captured private Magic failure frame. Keep ordinary gameplay running toward a real result. Live recovery and full production acceptance remain open.
- Package the 246,877,193-byte online installer. All 126 runtime comparisons, 1,692 inventory hashes and seven exact icon frames in both executables pass; source/payload privacy checks report no findings.
- Retain the approved Spike targeting, separate Last Resort/Erosion candidates, prior Magic shop repair and original CHIMPS recordings. Private account evidence stays outside the installer and repository.

## Removed

- Remove the assumption that HUD recovery is unnecessary after route actions finish.
