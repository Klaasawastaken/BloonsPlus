# Bloons+ Preview 99 — Installer Accessibility Hotfix

## Additions

- Add native accessibility checks for setup status, measured and unknown progress, recovery text and validated completion in both themes.

## Changes

- Expose the current friendly setup status to assistive tools, rather than only the fixed label “Setup status”.
- Send a native status-change notification when the status text changes. Progress-only observations do not repeat that notification or move focus.
- Describe whether current-step progress is measured or unavailable through the native accessibility object.
- Update the developer wiki's installer boundaries and extend offline MM/hour and XP/hour acceptance.
- Verify 396 Python tests and 64 JavaScript check files. Actual screen-reader, clean-Windows, reboot and complete VM provisioning acceptance remain open; this release does not certify production 1.0.

## Removed

- Remove the static accessible status name that hid changing installation and recovery text.
