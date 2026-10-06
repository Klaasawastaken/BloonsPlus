# Bloons+ Preview 99 — Package Identity Hotfix

## Additions

- Add an explicit `--release-version` installer build option for stable and preview release identities.
- Add offline staging, validation and fingerprint checks, plus a native welcome-view check for the installed preview version.

## Changes

- Stamp the staged app, package-lock root metadata and native file inventory with the selected release version. Installed controller and installer labels now describe that package, rather than the development checkout's fixed version.
- Validate the supplied identity before replacing staging. Leave source metadata and dependency versions unchanged; builds without the option retain their development version.
- Document release build commands and retain fingerprint-based update/repair detection.
- Verify all 378 Python tests and 62 JavaScript check files. Keep clean-machine, physical accessibility and full 1.0 acceptance open.
- Check the 246,882,191-byte installer against 126 runtime source files and all 1,694 inventory hashes. Verify seven exact app-icon frames in both executables, all four staged version labels and the embedded native inventory; source and payload privacy guards report zero findings.
- Retain the setup retry-status repair, approved HUD recovery, Magic shop placement repair and exact Spike targeting. Keep missing-medal gameplay running and apply runtime updates together after a replay finishes.

## Removed

- Remove the fixed development-version label from explicitly tagged release packages.
