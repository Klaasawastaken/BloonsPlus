# Bloons+ Preview 77

## Replay pause recovery

- Confirm the full pause heading and Auto Start label before sending Esc to resume.
- Withhold Esc on repeated small-template matches when those labels are absent, avoiding accidental pause/nudge toggles on live gameplay.
- Read the actual Auto Start switch using its cyan knob and lime rail. Ambiguous switch state remains unknown; it never authorizes a toggle.
- Log pause confirmation and the observed switch state for failure diagnosis.

## Settings

- Remove the redundant preferences reset that also cleared queued runs.
- Refresh connection/setup state whenever Settings opens.
- Hide installation and update controls until their availability is known.
- Keep Appearance, Game & VM, and Help & support in a compact layout.

## Verification limits

Seven offline checks cover both existing pause calibration resolutions, scaled coordinates, synthetic off/ambiguous controls, false green patches and the actual replay pause branch. Settings state and syntax checks pass; the dark layout was reviewed in the local app. Manual-round route execution is still under development and omitted manual controls remain excluded. No new route victory or universal pause detection is claimed.
