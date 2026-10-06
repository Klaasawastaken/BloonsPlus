# Bloons+ Preview 85

## Replay checkpoint recovery

- Capture the resume map fingerprint after an evidenced tower placement, using a foreground in-game frame. The first mode-introduction overlay can no longer become a confirmed map fingerprint.
- Confirm the fingerprint once for the same run, map and mode. Failed checkpoint writes restore the provisional fingerprint.
- Keep older checkpoints and map-mismatch protection intact. A provisional fingerprint cannot authorize resume.
- Honor **Stop after this replay** when a resumed sweep earns its medal. A successful resumed replay no longer starts another sweep against that request.

## VM viewer freshness

- Reject future-dated replay frames and response caches after a clock rollback. Request a fresh foreground capture instead of showing an old frame indefinitely.
- Keep existing cache durations and capture coalescing.

## Verification and limits

All 287 Python checks pass. Viewer freshness checks cover recent frames, expired frames, future timestamps and clock rollback. Viewer focus and visibility lifecycle checks pass. Resumed-sweep continuation checks cover both stop flags, confirmed clears, failed resumes and the shared engine lock.

The 245,324,928-byte installer passed 25 exact packaged-source comparisons. The publication guard reported zero findings.

Preview 84's Play-receipt fix recovered the existing Bloody Puddles Impoppable run at round 14. Its old fingerprint required an explicit, backed-up correction to Bloons+'s application checkpoint after fresh captures matched the unchanged game. Game and save files were untouched. The run progressed beyond round 20; no new medal or victory is claimed by this release.

This release improves recovery and viewing. It does not establish universal route wins, clean-machine installation or production readiness.
