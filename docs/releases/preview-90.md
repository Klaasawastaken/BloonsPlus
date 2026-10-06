# Bloons+ Preview 90

## Prevent overlapping setup

- Give each native installation an exclusive file lock before changing app files or writing its result.
- Reject duplicate installers with a clear wait-and-retry message; they cannot overwrite the active installer's result.
- Keep the lock scoped to the installation folder, with no SSH-key, privilege or permission changes.
- Have VM setup wait for an active installer before staging another update or clearing its result.
- Use a unique task and result receipt for each VM setup request, preventing stale success and conflicting results. Remove only that attempt's task registration afterward.
- Reuse an identical completed update only after comparing the installed installer with the requested file's SHA-256 hash. Different updates run sequentially.
- Wait for installer ownership to be released before accepting success or failure, including app-launch requests during setup.
- Let the native installer recheck guest idleness before closing its controller. Remove the earlier unguarded remote app stop.

## Verification and limits

All 314 Python checks, ten VM setup transport checks and 50 JavaScript check files pass.

New checks exercise the actual compiled native installer lock across Windows processes, the PowerShell ownership probe against a held Windows file, isolated result receipts, uncertain ownership and repeated update requests. The compiled duplicate-install check also confirms its private failure result and preserves the owner's receipt.

Clean-machine installation and recovery of orphaned package processes remain open. VM installation requests refuse older installers without isolated receipt support rather than waiting for a result they cannot provide. This preview does not claim complete interrupted-install recovery or production v1.0 acceptance.

No game files, save files or original recordings changed. A healthy replay is not interrupted to apply this batch.
