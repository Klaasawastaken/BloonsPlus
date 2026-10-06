# Bloons+ Preview 48

## Replay reliability

- Unsupported saved hotkey modifiers no longer silently send a different bare key.
- Malformed binding entries no longer crash startup.
- Candidate readiness and replay decoding agree on supported keyboard modifiers.

## Medal-first cleanup

- Removed the legacy achievement sweep backend, which could replay already-owned modes.
- Run status now displays the current job's victories and defeats rather than the legacy recording count.

## Verification limits

Existing round-start, route-binding and UI-status checks pass. Additional offline probes preserve supported scan codes and reject malformed modifiers/device paths. Publication guard reports no findings. Deployment stays between replays; full route coverage and clean-PC installation remain in progress.
