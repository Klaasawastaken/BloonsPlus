## Additions

- Regression checks cover redaction of full route-log downloads, preservation of private source records and safe failure when the privacy helper is unavailable.
- Compiled native checks cover escaped line continuations in both JSON-style and Python-style diagnostics.

## Changes

- Full route-log downloads now use the shared privacy filter before creating a file.
- Fixed native installer exports leaving credential suffixes visible after escaped LF or CRLF line breaks.
- Preserved useful map/round context and the original private logs used for diagnosis.

## Removed

- No features removed. No automatic uploads, route changes or medal-history resets were introduced.
