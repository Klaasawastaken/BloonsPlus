# Bloons+ Preview 12

## Route timing audit

- Newly converted strategies no longer label omitted delays, life thresholds, speed/autostart changes or manual-round controls harmless.
- Everything Macro's round-relative delays are flagged as incomplete rather than silently trusted.
- Developers can run `.venv/Scripts/python.exe tools/import-public-routes.py --audit-timing` for a read-only inventory. The current audit lists 48 legacy review candidates among 891 recordings; four have existing timing-preserved alternatives.
- Eight offline converter checks pass. Audit findings indicate missing source semantics, not proof that every listed route loses. No existing recording was rewritten and no game was launched only for validation.
- Includes Preview 11 runtime setup recovery and the Settings/dark-mode improvements.

## Install

Download **BloonsPlusSetup.exe** below. Close Bloons+ before updating. VM updates should apply between replays from Settings on the main PC.

This remains a preview. Faithful round-relative/manual-control execution and clean Windows installation verification are unfinished. Steam sign-in and ownership of BTD6 are required.
