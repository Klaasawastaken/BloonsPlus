# Bloons+ Preview 87

## Clearer installer progress

- Show five named installation steps: preparation, app files, Microsoft C++ runtime, Python packages and finishing.
- Show measured percentages for file extraction and downloads with a known size. Package installation and runtime checks show an animated working indicator instead of an invented percentage.
- Keep Python package output in the current step. It no longer jumps the progress bar to 98%.
- Preserve the failed step when setup pauses, so a retry has a clear starting point.
- Reuse a healthy private Python environment even when its old requirements receipt is missing. Exact package versions, `pip check` and the runtime import probe must all pass before reuse.

## Less background UI work

- Defer map, tower, boss and achievement card construction while their views are hidden. Overview and navigation counters keep refreshing.
- Retain existing map cards when only the save-read timestamp changes. New medals, search text and filters still refresh the list.
- Render the current map and achievement data immediately when opening their pages.

## Verification and limits

All 297 Python checks, ten VM setup transport checks and 48 JavaScript check files pass. The startup-failure harness now includes the actual hero-navigation classifier, so its pre-game failure checks run correctly. The app's map list and search were checked in the browser without console errors. Installer step rendering was checked offscreen without starting an installation.

The installer is 246,300,076 bytes. Its payload passes 28 exact source comparisons, footer/length verification and the publication guard with zero findings.

The missing-medal sweep continued during development. Dark Castle Military Monkeys Only was confirmed by both victory and its saved medal; the next missing-medal replay is running. No original CHIMPS recordings or game/save files were changed.

Clean-machine installation, interrupted-install acceptance and broader live performance checks remain open. This is a preview, not production v1.0 or a guarantee that every route wins.
