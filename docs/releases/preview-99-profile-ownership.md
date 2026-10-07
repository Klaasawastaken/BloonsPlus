## Additions

- Regression coverage for profile disconnects, account changes, late scanner responses and unavailable readers.

## Changes

- Show hero, upgrade and knowledge requirements as unknown when the VM profile is unavailable.
- Preserve known map medals through temporary disconnections while clearing stale tower XP.
- Prevent another account's absent map medals and tower XP from carrying over into the current profile.
- Reset hourly-rate samples when the account changes, including accounts using the same save path.
- Recognize the saved names for Mortar Shell Shock and Skywarden Storm Pulse.

## Removed

- Stale ownership checkmarks after disconnected or unreadable profile responses.
