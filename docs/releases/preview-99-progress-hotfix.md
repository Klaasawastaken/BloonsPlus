# Bloons+ Preview 99 — Installer Progress Hotfix

## Additions

- Add a joint check between the native installer client and the real setup coordinator for cancellation, resume, reconnect, restart deferral and validated completion.
- Check that completed installer milestones survive retries and reopening, while a new installation operation starts with fresh progress.

## Changes

- Retain completed work when setup rechecks an earlier local component or receives an earlier environment progress observation.
- Keep unknown current-stage work indeterminate and require fresh validation before declaring setup complete.
- Verify 400 Python tests and 65 approved JavaScript check files. Clean Windows, physical reboot, screen-reader and complete VM provisioning acceptance remain open; this is a preview, not production 1.0.

## Removed

- Remove progress resets that erased completed milestones during setup recovery.
