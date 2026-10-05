# Bloons+ Preview 18

## Source flow audit

- Inspect the Randy collection runner at its recorded source commit without executing it.
- Correct the converter: explicit start presses Space twice and is now an omitted start/speed control, not a no-op.
- Distinguish the automatic finish handler, which sends no input, from manual-round handling on excluded Sanctuary.
- Ten offline importer checks pass. Existing recordings are unchanged; faithful manual-round conversion and legacy candidate review remain unfinished.

Runtime behavior remains the same as Preview 16. This source workflow correction does not prove any strategy victory. This is a preview, not production 1.0.

## Install

Download **BloonsPlusSetup.exe**. Close Bloons+ before updating; apply VM updates between replays.
