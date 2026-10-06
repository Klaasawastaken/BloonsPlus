# Bloons+ Preview 80

## Settings cleanup

- Compact Light/Dark control with keyboard focus support.
- More room for game connection status; setup checklist and VM maintenance stay folded until needed.
- Clearer update and advanced ISO labels, with repeated descriptions removed.

## Recording timing groundwork

- Source logical-round markers have their own clock, separate from the observed game round.
- After-Play markers require a confirmed input receipt; missing or reused receipts hold the action.
- Ability timing follows the logical clock for these recordings. Save failures retain the queued marker, and resume rejects stale clock metadata.

## Verification and limits

104 focused Python checks, route validation and the existing Settings checks pass. Settings reviewed in both themes. This release does not admit incomplete manual-round plans, rewrite original CHIMPS recordings or claim new winning strategies. Full source loop and double-Play preservation remain in progress. Updates should apply between completed replays.
