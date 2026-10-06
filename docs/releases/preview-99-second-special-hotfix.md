# Bloons+ Preview 99 — Second Special Hotfix

## Additions

- Add a separate Firing Range CHIMPS candidate with Rosalia's two second-special target clicks, original placements, waits, abilities and upgrade order.
- Add offline coverage for source conversion, saved bindings, target and selector scaling, recording, resume, keypad identity and direct-start prerequisites.

## Changes

- Preserve second-special commands as `special2` in recordings and use the exact `TowerSpecial2` keyboard binding from the game's saved profile.
- Reuse the existing selected-tower input path. Block missing or unsupported second-special bindings in both sweep candidates and direct starts.
- Keep first and second recorder shortcuts distinct, including PageDown and Numpad3. Preserve all original CHIMPS recordings.
- Include the prior achievement-source repair in this batch. Apply runtime updates between completed replays.
- Keep clean-machine, physical accessibility and full production acceptance open. Offline conversion does not establish a victory.
- Verify 394 Python checks, 64 JavaScript check files, 126 runtime source comparisons, 1,698 inventory hashes and both application icons.

## Removed

- Remove the importer omission of second-special commands from the new complete candidate.
- Remove guessed second-special keys and duplicate recorder actions caused by overlapping shortcuts.
