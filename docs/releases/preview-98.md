# Bloons+ Preview 98

## Additions

- Save the exact hero-picker frame read by OCR when hero lookup, Select confirmation or button recognition fails. Diagnostics include the expected hero, observed title and button readings, click position, attempt count and frame age.
- Add real renderer checks for nested disabled fieldsets, native legend exceptions and dropdown options disabled while their menu is open.

## Changes

- Keep early strategy defeats consumed instead of replaying the same candidate because it lost near the opening. The existing bounded retry allowance now requires an evidenced placement or OCR failure.
- Refresh custom dropdown availability when a containing fieldset is enabled or disabled. Recheck the native field and option before accepting a menu click, including clicks before the mutation observer runs.
- Preserve the complete failure screenshot path when Windows folders contain spaces.
- Reject malformed non-object hero OCR responses. Keep unknown hero selection unconfirmed instead of guessing a successful selection.
- Hero failure images use the existing bounded screenshot retention; their diagnostic log entries remain in persistent route history. Game and save files are unchanged, and original CHIMPS recordings are preserved.
- Verified 350 offline Python checks, ten isolated setup-transport checks and 61 JavaScript check files, including the separate unpublished route draft check. Hero recognition across every layout, clean-machine setup and the remaining V1.0 acceptance gates still require evidence.
- Rebuilt the 235.4 MiB online installer. All 126 packaged runtime source comparisons and 1,689 inventory hashes match; both executables contain all seven application icon frames. Publication checks found no private-file findings. These checks verify the artifact, not a clean-machine installation.

## Removed

- Remove the stale-menu selection path that bypassed disabled native controls.
