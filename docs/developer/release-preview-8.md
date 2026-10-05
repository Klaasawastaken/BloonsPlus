# Bloons+ 0.1.0 Preview 8

## Replay placement correction

- Support-tower coverage optimization now respects the experimental placement setting.
- CHIMPS and maps with changing terrain keep their recorded support-tower positions. Recovery from an actual rejected placement remains available.
- Original CHIMPS recording files are unchanged.

## Verification

An offline regression reproduced repositioning with the experimental setting disabled. The corrected guard passes disabled-setting, CHIMPS, dynamic-map and enabled ordinary-map cases, alongside the HUD and held-placement checks. This is not a claim that every route wins.

Includes the Preview 7 website refresh, placement-ghost recovery and installer improvements. Install **BloonsPlusSetup.exe** after the current replay ends. Internet access is required for dependencies; the installer remains unsigned. Production 1.0 and Pro are still in development.
