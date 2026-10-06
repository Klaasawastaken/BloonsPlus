# Bloons+ Preview 99 — Achievement Source Hotfix

## Additions

- Add offline coverage for guest-local achievements, VM relay compatibility, genuine host fallback, missing caches, malformed responses and the displayed source label.

## Changes

- Identify the guest's own Steam cache correctly and label successful host relays as VM data, including responses from older guest versions.
- Show the VM source in the app while preserving achievement values, unlock timestamps and completion calculations.
- Verify all 387 Python checks and 64 JavaScript check files. Keep clean-machine, physical accessibility and full 1.0 acceptance open.
- Keep the healthy missing-medal replay running; activate controller updates in a later batch between replays.

## Removed

- Remove the misleading “this PC” fallback label when achievement data comes from the VM.
