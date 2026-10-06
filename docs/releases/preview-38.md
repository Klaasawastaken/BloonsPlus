# Bloons+ Preview 38

## Preserve explicit cursor targets

BTD6bot move_cursor operations now become move-only route commands. Positions are validated, recorded and executed within the replay input sequence; the action does not click or claim an observed gameplay effect.

A separate #Ouch Alternate Bloons Rounds candidate preserves the two source cursor targets and all 103 executable commands. The full Python parser and JavaScript mode/legality validator pass. Original recordings remain unchanged; no new candidate win is claimed.

Malformed cursor calls are rejected. Other unsupported operations remain explicit, including manual rounds, autostart and positional hero/special actions. A source Sniper path regression remains rejected rather than guessed.

Four cursor regressions and fourteen importer checks pass offline. Live use is limited to missing medals. V1.0 coverage, clean-install readiness and universal route success remain unproven.
