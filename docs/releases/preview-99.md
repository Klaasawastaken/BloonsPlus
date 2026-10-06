# Bloons+ Preview 99

## Additions

- Add separate Last Resort and Erosion CHIMPS candidates preserving the pinned strategy's placements, timing, targeting and selector updates. They pass offline parsing and legality checks; neither is claimed to have won locally.
- Preserve Spike Factory targeting through Tier 5, including reverse changes and supported positional Set clicks. Reverse uses the user's saved BTD6 keyboard binding.
- Check required targeting and special-command bindings before starting a candidate. Missing or unsupported reverse bindings never receive an invented default.

## Changes

- Clear both Play aliases when the saved game binding is unbound or unsupported. Automatic round control reports the problem without sending a guessed key or `None`.
- Keep nested targeting and special actions behind input guards. A changed tower selection coordinate receives a fresh selection before its command.
- Count unresolved upgrades separately across sold and replacement tower instances. Confirming a replacement's path no longer hides an older unresolved purchase.
- Improve dark-mode requirement rows using the app's opaque control background and existing border colors. Actual renderer checks measure readable label/value contrast and keep T1–T5 on one row at desktop and compact widths.
- Prepare existing installer selectors for the approved `v1.0.0` milestone. Validate the selected artifact's metadata and retain preview compatibility. This release remains a preview; production acceptance is still open.
- Refresh offline route coverage to 530 of 1,204 map/mode pairs, with 674 gaps and one map without an eligible route. Eligibility does not establish victories or account prerequisites. Original CHIMPS recordings and game/save files remain unchanged.
- Verify 362 offline Python tests, 61 JavaScript check files and ten setup-transport tests. The unrelated unfinished ABR route draft is excluded from this release. Live targeting, remaining route failures and clean-machine installation still require evidence.
- Rebuild the 235.4 MiB online installer. All 126 packaged runtime comparisons and 1,689 inventory hashes match. Both executable icons contain seven exact application icon frames; publication checks report no private-file findings.

## Removed

- Remove the importer restriction that dropped reverse and Tier 5 Spike Factory targeting. Ambiguous positional Set calls in the pinned source remain excluded.
- Remove the stale white translucent background from dark requirement rows.
