# Bloons+ 0.1.0 Preview 6

This preview reduces repository clutter and fixes the evidenced early Rake Reverse defeat.

## Changes

- Moved browser code into `assets/app`, catalogs into `data/catalogs`, runtime configuration into `data/config`, and maintenance utilities into `tools`.
- Kept the conventional root entry points and package files visible for developers.
- Updated every server, replay, installer, browser, test, and documentation path for the new layout.
- Fixed two browser resources that previously pointed at missing root files.
- Reworked the GitHub banner with a more recognizable Bloons TD 6 inspired monkey, dart, track, and bloon scene.
- Changed Rake Reverse to place its Tack Shooter before Sauda, preventing an undefended opening while cash rebuilds.
- Added bounded two-frame life-loss confirmation so truncated OCR values cannot repeatedly activate emergency spending.
- Retained Preview 5 cash, round, hero, freeze-cycle, and route retry improvements.

## Install

Download `BloonsPlusSetup.exe` and run it over the existing installation. The updated installer preserves user data and downloads system dependencies during setup.

## Known limits

Routes remain sensitive to BTD6 balance changes and account unlocks. The Rake fix is evidence based and packaged, but still needs a complete live replay before the route is marked confirmed. Bloons+ is independent of Ninja Kiwi.
