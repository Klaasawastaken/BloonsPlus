# Bloons+ Preview 28

## Live progress reliability

The app's two progress pollers now share an in-flight save read. When slower scanner or catalog requests finish, they use the newest completed save response instead of applying an older profile.

This prevents out-of-order refreshes from rolling back displayed unlocks or resetting the hourly-rate window. A newer VM-unavailable result also takes precedence over an older readable profile. Genuine guest clock corrections still reset sampling safely.

Deferred-response checks cover request sharing, response order, clock corrections, unavailable-state precedence and retry after malformed JSON. Existing profile-rate checks and JavaScript syntax pass. This release also includes Preview 27's Settings and dark-mode improvements.

The missing-medal replay remains uninterrupted. Guest updates will be applied between replays; a live multi-run rate check remains open. V1.0 is still in development.
