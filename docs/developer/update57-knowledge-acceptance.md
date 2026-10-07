# Update 57.0: Monkey Knowledge activation

7 October 2026. This bounded fix reads each account independently. It does not
include a player's knowledge allocation, stats, account identifier or save.

## Evidence

- A read-only schema inspection found a `disabledKnowledge` array alongside the
  existing acquired-point and global-switch fields. Only field shapes were used
  to design the change; no game/save files were modified.
- A synthetic route fixture first reproduced the defect: an owned but individually
  disabled Master Double Cross point incorrectly satisfied a route requirement.
- One shared policy now separates ownership from activation in the decoder,
  route checks, free Dart/Glue launch flags and app labels. Legacy saves without
  individual switches retain support; malformed ownership or switch values stay
  unknown. Free-placement flags require positively active knowledge, and replay
  retains its mode and live-placement checks.
- Independent review found an ownership coercion that hid malformed save data.
  A decoder-level failing test reproduced it before the correction; focused
  re-review found no remaining issue in this scope.
- All 67 JavaScript check files and 410 Python tests passed. Fixtures use
  synthetic points and balances, and launch no gameplay.
- Published `v0.1.16-preview.99`: one 246,955,888-byte installer; 127 matching
  runtime sources, 1,713 verified inventory hashes, four agreeing package
  identities, matching native embedded inventory and seven exact icon frames
  in both executables. Public-file checks report zero findings.
- The standard VM updater completed at an observed idle boundary. Installed
  inventory/controller versions agree with the release; six source hashes
  match, and the authoritative live profile exposes the new activation fields.

## Limits

The observed save's individual-switch list was empty. Populated and malformed
lists were exercised with synthetic fixtures; no user's points were toggled for
validation. This repair does not certify every game mechanic, fix Psi title
recognition, or complete Ship Capture/Sniper Paragon support. The sweep remains
stopped pending its separate picker repair. Full production acceptance is open.
