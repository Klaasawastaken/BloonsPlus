## Additions

- Native checkpoint checks covering long handoff paths, long directories, temporary filename collisions and locked files.
- Fresh-session checks that preserve explicit setup flags through JSON serialization.

## Changes

- Fit temporary checkpoint filenames within the available Windows path length, while retaining atomic replacement and durable writes.
- Retry temporary filename collisions within a fixed limit and preserve files owned by other writers.
- Return explicit false flags for a fresh setup session so the native installer can read its initial status.

## Removed

- The oversized temporary filename suffix that could prevent a valid checkpoint path from being written.
- Null or omitted operation flags in fresh setup snapshots.
