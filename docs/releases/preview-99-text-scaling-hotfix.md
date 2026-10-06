# Bloons+ Preview 99 — Installer Text Scaling Hotfix

## Additions

- Add native layout checks for 100%, 125%, 150% and 200% text-only scaling in light and dark themes, at the default and minimum window sizes.
- Check welcome, options, download, failure, restart and completion screens with actual WinForms controls.

## Changes

- Size the installer footer and action buttons to their text, and wrap the footer note within the window.
- Keep the application icon, setup choices, recovery commands and installation engine unchanged.
- Verify 397 Python tests and 64 approved JavaScript check files. Physical screen-reader, Windows DPI/text-scale, clean-Windows, reboot and complete VM provisioning acceptance remain open; this preview does not certify production 1.0.

## Removed

- Remove the fixed footer and action-row heights that clipped enlarged text.
