# Bloons+ Preview 99 — Installer Diagnostics Hotfix

## Additions

- Check native shared diagnostics with ten structured-field cases and three truncated credential cases.
- Document remaining failure-evidence gaps, including fields omitted from the detailed API and the bounded log tail.

## Changes

- Redact credential, account and session values in quoted JSON/Python diagnostics, including escaped quotes and incomplete strings.
- Preserve useful map and round context in the tested complete-field formats.
- Verify 401 Python tests and 65 approved JavaScript check files.
- Keep gameplay running without a guest reload for this native installer repair. Production clean-machine, physical reboot and accessibility gates remain open.

## Removed

- Remove the quoted-field gap in native installer Copy/Export details. The app's separate log-redaction repair remains pending.
