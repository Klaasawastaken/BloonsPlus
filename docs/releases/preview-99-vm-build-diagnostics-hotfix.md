# Bloons+ Preview 99 — VM Build Diagnostics Hotfix

## Additions

- Add scoped VM-build diagnostics and regressions for fresh, stale, unrelated and replaced backend logs.

## Changes

- Report an observed Windows boot-file failure with its `bcdboot` exit code instead of a generic vanished-VM error.
- Stop automatically building more Windows images after that confirmed failure. Unknown disappearances keep their bounded retry behavior.
- Read only newly appended diagnostics for the requested VM, with a 64 KiB limit and no raw backend-log export.
- Check 407 Python tests and 65 approved JavaScript check files. Clean Windows provisioning remains incomplete: two separate fixtures failed before Bloons+ ran. This diagnostic repair does not fix the underlying boot-store error or require a healthy gameplay VM to reload.

## Removed

- Remove repeated image builds that concealed the confirmed boot-file failure.
