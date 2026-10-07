## Additions

- Offline coverage for temporary cache conflicts, persistent failures, scanner updates and continued missing-medal sweeps.

## Changes

- Retry temporary observation-cache errors with bounded waits and unique temporary files.
- Preserve the prior cache when replacement fails or its contents cannot be read safely.
- Continue to other missing medals when the secondary cache cannot be updated after a confirmed clear.
- Keep confirmed ownership and failed-route history intact; report cache errors without exposing local file paths.

## Removed

- The shared temporary filename used by sweep observation updates.
