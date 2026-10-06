# Bloons+ Preview 89

## Clear setup states

- Report pending, checking, already ready, installing, validating, complete, retrying, restart required and failed states for VM setup steps.
- Show the current state beside each step in Settings and first-run setup, with distinct failure and restart styles in light and dark themes.
- Recheck readiness after an action finishes. Stop at an unvalidated step rather than repeatedly reinstalling it or advancing to later steps.
- Treat Steam sign-in and BTD6 installation as user steps; detect their readiness without collecting credentials.
- Preserve the failed step and expose the attempt number when it is retried.

## Verify remote updates

- Continue to require an explicitly idle guest before starting an update.
- After installation, allow a bounded reconnection window and require a live guest-app connection before reporting update completion.
- Explain when files were updated but the guest app did not reconnect.

## Verification and limits

All 301 Python checks, ten VM setup transport checks and 50 JavaScript check files pass. Offline checks exercise actual setup flow for successful, unvalidated, failed and retried steps, Windows restart requirements, Steam sign-in waiting, delayed reconnection and connection failure. UI checks cover state labels and action handling.

The installer is 246,305,639 bytes. Its payload passes 29 exact source comparisons, footer/length verification and the publication guard with zero findings. The setup-state Wiki table was inspected in the browser without console errors.

Clean-machine installation, interrupted-process recovery and wider live setup acceptance remain open. No gameplay or original route recordings changed in this batch. This is a preview, not production v1.0.
