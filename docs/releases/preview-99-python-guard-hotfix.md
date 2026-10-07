# Bloons+ Preview 99 — Installer Runtime Safety Hotfix

## Additions

- Installer checks for active Python and Pythonw work in Bloons+’s private environment and bundled runtime before replacing installed files.

## Changes

- Update, repair and uninstall wait for installed Python work to finish, including work that outlives its controller.
- Recheck after the idle controller closes, preventing newly started Python work from being overlooked during shutdown.
- Preserve running Python processes and unrelated installations. Unknown process state remains a blocking error.
- This installer-only repair requires no VM reload and does not interrupt healthy replays. Clean-machine and complete interruption-recovery acceptance remain open; this is a preview release.

## Removed

- None.
