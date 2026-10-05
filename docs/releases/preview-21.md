# Bloons+ Preview 21

## Activity and run timing

- Calculate event ages using the game's VM clock, even when it differs from this PC's clock.
- Correct run duration, profile freshness and recent result freshness with the same source-clock offset.
- Keep historical activity ages across page reloads instead of treating future-dated events as newly completed.
- Stale bridge responses do not recalibrate the clock. Unknown timestamps display as unavailable.

Also includes the cleaner Settings layout from Preview 20.

## Checks and limits

Live evidence showed the guest clock nine hours ahead. JavaScript syntax and whitespace checks passed. Runtime UI confirmation awaits deployment at a healthy replay boundary. No game or save files were edited; neither OS clock was changed. No new route victory is claimed.

Preview release: production readiness and clean-machine installer validation remain in progress.
