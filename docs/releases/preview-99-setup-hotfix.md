# Bloons+ Preview 99 — Setup Status Hotfix

## Additions

- Add offline checks for consecutive updates, consecutive environment setup operations, genuine retries, changes between operators and duplicate requests during active work.

## Changes

- Start each independent completed setup or VM update operation with a fresh attempt counter. A new update no longer appears to be retrying an earlier successful update.
- Retain attempt counts when retrying unfinished work of the same kind. Preserve existing replay ownership checks, readiness validation and durable setup receipts.
- Verify all 62 JavaScript check files and 373 Python tests. Two isolated Electron checks required execution outside the sandbox to launch their hidden renderers; both passed.
- Package the 246,879,856-byte online installer. All 126 runtime comparisons, 1,693 inventory hashes and seven exact icon frames in both executables pass; source and payload privacy checks report no findings.
- Retain the approved HUD recovery, Magic shop placement repair and separate Spike targeting candidates. Deployment waits for the current healthy replay to finish.

## Removed

- Remove stale retry counters inherited from completed or different setup operations.
