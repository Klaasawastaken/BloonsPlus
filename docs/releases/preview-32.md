# Bloons+ Preview 32

## Check route ability bindings before starting

Routes now list the ability slots they actually issue, including repeating abilities. When the saved game controls explicitly leave a required slot unbound or use a key the replay cannot send, the sweep chooses another compatible route or medal instead of starting an incomplete strategy.

Skip logs and direct-run errors identify the required slot. Unused slots and cancellation commands do not block a route. Accounts without saved gameplay bindings retain the replay's existing defaults.

Focused offline checks cover command extraction, slot 10, supported and unsupported saved keys, missing bindings, defaults, and alternative candidates. Original recordings and game/save files are unchanged. Deployment is queued for a healthy replay boundary. V1.0 remains in development.
