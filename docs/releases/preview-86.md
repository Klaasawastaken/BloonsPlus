# Bloons+ Preview 86

## Manual-route cash recovery

- Recover a paused income deadlock when a manual route's logical clock runs ahead of the actual round and its next placement or upgrade is unaffordable.
- Require ten seconds of repeated paused observations, a known cash amount, a bound Play key and exclusive foreground input ownership before starting one income round.
- Save a Play receipt before input and confirm it from a later observation. Preserve the queued purchase and both the observed and logical round values.
- Limit recovery to three distinct round starts for one queued purchase. Unknown screens, running games, busy input, ordinary automatic routes and Deflation do not authorize a recovery input.
- Restore pending receipts without repeating their key. Reject malformed clocks and mismatched purchase owners.

## Completed-round Play confirmation

- Accept a completed round after an issued speed command when BTD6 keeps the same round number on its paused HUD.
- Retain the one-second observation guard and reject regressed or unreadable rounds. Consume the saved command without another Play input.
- Reproduce the round-14 deadlock in a regression check. The VM module was deployed; continuation refused a changed map scene, so no resumed clear is claimed.

## Verified VM installer transfer

- Stage each VM update in a fresh Bloons+ application folder instead of overwriting the Desktop installer.
- Check the transferred file's size and SHA-256 against the host copy before launching it. A failed transfer or mismatched file cannot start installation.
- Remove only that attempt's staged installer and empty directory after confirmed installation. Preserve a file that remains in use.

## Website refresh

- Rebuild Features around four practical workflows, with varied official BTD6 monkey art and a smaller progress section.
- Simplify the homepage feature overview while retaining the app-preview hero and its floating card.
- Add Quincy, Sauda, Benjamin and Gwendolin hero portraits plus seven additional monkey types across the pages and README banner. Keep Engineer Monkey on the Wiki and Ninja Monkey consistent across every Discord banner. Preserve original character proportions and third-party attribution.

## Verification and limits

All 295 Python replay checks and ten setup-transport checks pass, including seven focused recovery checks and upload verification/rejection cases. Existing original recordings and game/save files are unchanged.

The installer staged, verified and completed in the existing VM. Before resuming the stopped game, a fresh screen showed defeat at round 40 instead of the saved round 34. Recovery refused that mismatch, so the bounded cash fix still lacks a confirmed live recovery. The missing-medal sweep has since restarted; no new clear is claimed.

Features and Home were inspected in the browser, including dark mode and a narrow Features layout. Site release lookup and reduced-motion/visibility checks pass. This release does not establish a clean-machine installation or guarantee route outcomes.
