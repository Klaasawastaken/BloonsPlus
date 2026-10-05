# Bloons+ Preview 13

## Round-relative strategy timing

- Recorded routes can now schedule `round 20 after 5 seconds`. Multiple actions share the observed round-start timestamp rather than stacking per-action waits.
- Waiting remains non-blocking so the replay keeps reading the game screen.
- Explicit offsets survive emergency wait release; overdue and resumed-mid-round timing cases produce recovery logs.
- Two separate timing-preserved source candidates were added: **Dark Castle Deflation** and **Tricky Tracks Impoppable**. Existing recordings, including original CHIMPS routes, are untouched.
- The offline validator now locates the project’s existing AutoHotkey runtime without requiring a global PATH change.

## Verification limits

Nine offline timing/recording checks and eight converter checks pass. Both new candidates pass the full Python parser and JavaScript route legality checks. This does not prove victory; live timing verification remains pending gameplay for missing medals only. A resumed mid-round clock uses a fresh observation anchor and reports that limitation. Manual-round controls remain unfinished.

## Install

Download **BloonsPlusSetup.exe** below. Close Bloons+ before updating. Update a connected VM between replays from Settings on the main PC.

This is a preview, not production 1.0. Steam sign-in and ownership of BTD6 are required.
