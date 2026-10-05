# Bloons+ Preview 19

## Lighter live status polling

- Add an opt-in UI status view that omits historical run and candidate-attempt data unused by the app.
- Keep active sweep state, run controls, checkpoint details, counters and all 2,000 log lines.
- Preserve the full status API and persistent history. The host still caches full guest status.
- Switch app polling to the smaller view.

## Verification

Projection and actual server-handler checks pass offline. A current live status sample shrank from 562,687 to 231,888 bytes (59%) without reducing log length. This measures payload reduction, not a proven scroll-frame or timeout improvement. Browser/guest verification awaits the safe replay boundary.

## Install

Download **BloonsPlusSetup.exe**. Close Bloons+ before updating; apply VM updates between replays. This is a preview, not production 1.0.
