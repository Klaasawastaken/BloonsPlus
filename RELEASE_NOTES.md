# Bloons+ 0.1.0 Preview 3

A cleaner desktop app, repaired setup checks and a live VM game preview.

## Changes

- Compact Automation page with map, difficulty, variation and route tools; removed Farm, Sweep and Tower Progress navigation clutter.
- Required hero and tower paths show save-file unlock checks through T5 using the included upgrade catalog.
- Live VM screen under Automation, refreshed every two seconds while open; no game input is sent by the viewer.
- Run Logs issue reporting prepares a redacted GitHub draft and downloadable log for review before submission.
- Boss Events shows Coming Soon while automated boss navigation remains unfinished.
- Preserve recorded round/action order: optional surplus upgrades run only after planned actions finish.
- Held clicks and title/menu diagnostics; explicit detection of a lower-privilege app trying to control elevated BTD6.
- Installer checks Microsoft C++ libraries, Python packages and actual native imports, repairs a broken private environment and preserves existing app data.
- Revised mint/coral setup layout, progress information, retry controls and a persistent installer log.
- Product website, Docs, searchable wiki, legal pages, BTD6 art, Discord banner and reduced-motion-aware animations.
- Removed unused reference-engine snapshots from the public tree while retaining needed data and license notices.

## Install

Download **BloonsPlusSetup.exe** and run it over your existing installation to update. Internet is required for dependency and VM setup downloads. Sign in to Steam inside the guest and install your owned BTD6 copy.

**SHA256SUMS.txt** contains the installer checksum. This preview is unsigned; Windows SmartScreen may warn about an unrecognized publisher. Signing requires a trusted certificate. Bloons+ does not disable Windows security protections.

## Verification and limits

JavaScript and Python syntax checks passed. The local Python native-import preflight passed. The installer compiled, and source/package privacy pattern checks reported no findings. A live VM startup test reached a match and executed tower placement and upgrades; a complete clear was not certified by this test.

The live viewer was checked against the guest and in the app. Wiki active-article navigation and the compact Automation layout were browser-checked. A clean-PC installation has not been verified.

Route availability is not a victory guarantee. Boss execution and the full automatic tower-unlock loop remain unfinished. Guest updates apply to future replays; existing administrator instances may need to be closed manually before launching an updated host app.

Saves, Steam credentials, SSH keys, temporary viewer frames, local progress and VM disks are excluded from publication. Pattern checks cannot identify every possible private detail, so review issue reports before submitting them. Third-party licenses and attribution are retained. Bloons+ is independent of Ninja Kiwi.
