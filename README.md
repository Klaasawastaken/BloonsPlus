# Bloons+ — BTD6 Companion

For a fresh GitHub checkout, see [GITHUB_SETUP.md](GITHUB_SETUP.md). Recent code changes and
remaining implementation gaps are recorded in [CODE_REVIEW_2026-10-03.md](CODE_REVIEW_2026-10-03.md).
Some scanner descriptions below reflect the earlier implementation; current account progress
also comes from the read-only Steam Profile.Save reader.

Local Bloons+ companion with a glass interface, saved map queue, read-only progress views, and a recorded-playthrough connector.

## Start

Run `npm install` once, then `npm start`, then open http://127.0.0.1:4173/.
Queue and preferences are saved in the browser on this PC. Observations are stored separately in game-observations.json. `tessdata/eng.traineddata` (OCR language data, ~5MB) is already checked in, so scanning runs fully offline; if it's ever missing, the first scan falls back to a one-time fetch from tesseract.js's default CDN and re-warns until you restore the file.

The scanner scales its saved screen regions to the captured game window. `calibrate.html` remains available for correcting a region if the game UI changes. Map-border recognition is still incomplete until its color palette is calibrated.

## Available

- Searchable map dropdown and bulk queue, excluding detected black borders. Unknown maps remain eligible.
- Read-only progress and achievement category/status filters. Legacy manual values stay in backups but are not treated as game observations.
- Glass navigation, modal, controls, responsive layouts, and reduced-motion support.
- Read-only Windows process detection for BloonsTD6 every 15 seconds while the app is visible.
- **Live screen scanner** (`scanner.js`, `capture.js`, `pixels.js`, `ocr.js`): every 5 seconds while BTD6 is detected running, captures the window (`PrintWindow`, no mods/memory access) and updates `game-observations.json` with `"source": "live-scan"`:
  - Player level and XP, read via OCR from a calibrated box on the main menu.
  - Per-map border color (none/bronze/silver/gold/black), read via color sampling of a calibrated box per map tile on the map-select screen, matched against a palette you build during calibration.
  - A field is only updated while its screen is recognized; anything not currently visible keeps its last known value rather than being overwritten with a guess.

## Map order and recordings

- `map-catalog.js` stores the current category and tile order. `autobtd6/maps.json` is synchronized from it, including new catalog entries such as Skulltweak and Three Mines 'Round.
- Visiting map-selection pages lets `map-order-scanner.js` learn visible labels and page/slot positions into `map-order.json`. Repeatedly recognized unknown labels are added as discovered maps. These entries survive app restarts.
- Before a recorded replay clicks a map tile, `verify-map-page.js` checks that the visible page and target tile label match the recording's map. An uncertain read stops the replay before entering a potentially wrong map.
- The map picker lists maps without a compatible recording as **route needed**. A map entry does not itself contain a winning strategy. New routes will only be generated after the existing replay flow is confirmed working in the live game.
- Replay screenshots and simulated clicks now use the BTD6 client area. A windowed 1920×1080 or 2560×1440 game is normalized to the matching reference layout, with clicks translated back into window coordinates. Near 16:9 custom window sizes are scaled to the nearer layout.
- The mode picker reads both 1080p and 1440p recordings and shows every variation. It marks modes without a compatible recording as **route needed**. The last replay log and exit code remain visible after a run stops and are saved across app restarts.
- The vendored Python replay runtime currently requires a separate Python installation with its listed modules. Bloons+ disables replay controls while that runtime is unavailable.
  Bloons+ looks for `BLOONS_PYTHON`, `.venv/Scripts/python.exe`, `py`, then `python` in that order.

## Input (`input.js`)

Moves the real mouse and clicks/scrolls, targeting the BTD6 window specifically. This replaced an earlier attempt at an independent virtual controller (ViGEmBus + Steam Input's per-game "mouse joystick" override): that path was abandoned after proving unreliable in practice — Steam Input needed re-binding after every game relaunch, input delivery was intermittent even when configured correctly, and the cursor it drove turned out invisible to both `PrintWindow` and screen-grab capture (so it couldn't even be tracked to verify a move). Real input has none of those problems: `GetCursorPos`-equivalent tracking and capture both agree with reality.

- `moveMouseTo(x, y, { durationMs })` — client-area coordinates (same space as `capture.js`/`calibration.json`). Eases from the cursor's current position over `durationMs` using ease-in-out, as a self-contained loop inside one PowerShell call (no per-step process spawn) — smooth, never a teleport.
- `click({ button, holdMs })`, `scroll(ticks, direction)`, `moveAndClick(x, y, opts)`.
- Every call brings the BTD6 window to the foreground first (`capture.js`'s `focusWindow`), since it's easy to lose focus (e.g. switching to another window) and input would otherwise silently go nowhere.

This does touch the real, shared mouse/keyboard — a deliberate, explicit tradeoff after the independent-device approach didn't pan out. Nothing in `server.js`/the web app calls this yet; it's a standalone module, exercised so far only via manual scripts.

## Still to build

Tower upgrade unlock scanning, full map-border recognition, and a verified route planner for maps without recordings remain incomplete. Tower XP is read passively from each visible category page, but uncertain OCR reads are discarded.

## Interaction requirements

The Steam game must remain unmodified: no mods, game-file edits, or memory injection. Interaction is real mouse/keyboard input only, always moved smoothly (never an instant jump) and always through the actual BTD6 window.
