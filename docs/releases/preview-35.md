# Bloons+ Preview 35

## Required controls are checked before a run

Routes now check the saved keys for their required tower placements, hero placement and upgrade paths. Empty or unsupported bindings show a specific readiness reason rather than allowing a replay to issue a guessed input. Only paths used by the route are required.

When BTD6 supplies saved tower controls, an unbound upgrade path no longer keeps the old default key. Absent or empty saved sections retain the existing default behavior. Focused Python and JavaScript checks cover bound, unbound, unsupported and unused controls; this does not claim that all routes have been proven in game.

Original recordings and game/save files are unchanged. Guest deployment waits for a replay boundary. V1.0 route coverage, manual controls and clean-install verification remain unfinished.

## Correct false locked-upgrade skips

The sweep and UI now share save-name matching, including Metal Freeze/Cold Snap, Bionc Boomerang/Bionic Boomerang and qualified Buccaneer upgrade names. These aliases are scoped to the tower. A read-only check against the current VM save changed Quad ABR and Infernal Hard from one false missing prerequisite to fully ready, without altering unlock data or clearing failures. Genuine locked upgrades remain blocked.

Skip logs name missing tiers. A pass with missing medals or unreadable medal records is saved as incomplete, rather than labelled complete. The sweep still does not retry owned medals or erase persistent route attempts.

## Simpler Settings

Appearance and game connection remain the main controls. Removed duplicate introductory and category labels; installation details stay collapsed, and the reset section is named for its actual action. Existing setup, update, theme and reset handlers remain connected.
