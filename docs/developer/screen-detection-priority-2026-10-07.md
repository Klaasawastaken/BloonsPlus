# Screen detection priority — 7 October 2026

## Evidence and repair

Town Center Reverse reached round 24 with a confirmed Sniper upgrade. The retained terminal frame showed gameplay and the open upgrade panel. Running that exact frame through the unchanged precise reference detector returned `INGAME`; the broad menu-color check returned true, causing the previous wrapper to return `MAP_SELECTION`.

The wrapper now asks the precise detector first and applies menu colors only to `UNKNOWN`. Focus and existing home Play detection are unchanged. No thresholds or click coordinates were guessed.

## Verification

- Three synthetic regression tests pass, including 36 positive-screen cases across 1080p and 1440p, UNKNOWN fallback, focus and home precedence. Before the change, the 36 positive-screen cases failed.
- The repaired wrapper correctly classifies the exact retained terminal frame as `INGAME`, while its menu-color collision still reproduces.
- An independent reviewer reran the checks and found no actionable issues.
- Private screenshots and account data remain outside published sources and installers.

## Deployment and recovery

Fresh process and controller logs showed the watchdog had already left the failed Reverse run and reached Military Only selection before the agent pause. The round-24 checkpoint was therefore stale and was not resumed. The already-paused navigation process was stopped through the existing controller. The repaired Python file was installed only after both controller-idle and no-surviving-replay checks, with an exact-byte backup and SHA-256 verification. No controller privilege or credential changes were made.

The missing-medal sweep restarted with its failures and earned medals retained, selecting Bazaar Easy. This proves deployment and restart, not a new clear. The five-minute monitor continues checking actual progression.
