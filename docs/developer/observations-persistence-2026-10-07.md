# Observation cache persistence repair

## Incident and approved scope

A missing-medal sweep stopped after a confirmed Spring Spring Hard victory because replacing the secondary observation cache returned `EPERM`. Victory and the authoritative saved medal had already been confirmed. This was a persistence failure, not a strategy defeat.

The approved repair retries transient cache replacement errors, preserves the existing valid document and reports persistent errors without stopping other missing-medal targets. Game and save files remain read-only.

## Implementation

- Each update uses an exclusive, unique temporary file, flushes it and replaces the destination without deleting the destination first.
- `EPERM`, `EACCES` and `EBUSY` receive at most four attempts, with 50, 100 and 200 ms waits. Other errors return immediately.
- Every retry reads the latest document and reapplies the medal update. Missing files initialize a cache; malformed documents are preserved and reported.
- Updates through this writer queue per resolved path. Each read/merge/write/replace attempt remains synchronous, preventing existing in-process scanner callbacks from interleaving with it. Only retry waits yield to the event loop.
- Cache failure is caught after confirmed ownership has been preserved. The sweep continues, and already-owned medals remain skipped. Logs report the error code without a private file path.
- Individual replay completion also awaits the update and reports a cache failure.

## Offline evidence

The writer fixture covers transient and persistent failures, preservation of prior bytes, invalid documents, missing-file initialization, twelve queued updates, temporary-file cleanup and scanner changes during retries. The complete sweep fixture covers 29 scenarios, including continuation to another missing medal after cache failure and protection against replaying the confirmed medals afterward.

Independent review identified that an initial asynchronous implementation could overwrite a newer same-process scanner update. A deterministic regression reproduced the loss. Keeping each replacement attempt synchronous makes that regression pass without changing scanner behavior.

## Limits

This is not a cross-process locking protocol: separate legacy scanner processes can still race outside a failed replacement/retry. It does not repair unrelated progress-history writes, change route strategies, or establish a live recovery outcome. Guest deployment must wait for a replay boundary.
