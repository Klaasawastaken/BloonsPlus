## Additions

- Offline checks exercise the app's issue preview, GitHub draft link and log download with synthetic account and credential fields.
- Native installer checks cover locked-file rollback, recovery in a fresh process and a successful retry while preserving unlisted data.

## Changes

- Fixed shared app diagnostics leaving values visible when JSON or Python logs quote account, password, session and setup-key field names.
- Redaction now consumes escaped quotes and truncated credential values, including incomplete private-key blocks.
- Fixed credential suffixes surviving plain Authorization headers and escaped line continuations.
- Preserved useful map and round context. Reports still require an explicit sharing action; no automatic upload was added.

## Removed

- No features removed. Original CHIMPS recordings, saved-medal protection and persistent route failures remain unchanged.
