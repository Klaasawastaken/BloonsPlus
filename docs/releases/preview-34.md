# Bloons+ Preview 34

## Observe recorded round starts

New `start round fast` and `start round slow` commands wait for a confidently observed play state. Input is serialized with the replay loop and saved before sending; later frames confirm the requested speed before the route advances. Busy or uncertain frames do not authorize input. Resume keeps pending intent and uses current bindings instead of blindly repeating a Space press.

The automatic round controller waits while the startup command is pending. Required Play/Fast Forward bindings now appear in route readiness diagnostics. This is observed startup intent, not a claim of identical timing to an upstream double-Space sequence.

Six separate offline-checked candidates were added: Balance CHIMPS, Quarry CHIMPS, Dark Castle Deflation, #Ouch Hard, Ravine Hard and Workshop Hard. Recorded source placements and upgrades are retained; original recordings were not replaced. These candidates have no new local victory claim and are eligible only for missing medals.

Focused round-start, timing, repeating-ability, importer and route gates pass offline. Live deployment waits for a healthy replay boundary. Explicit autostart settings, relative speed toggles, paid hero levels and wider route coverage remain unfinished; V1.0 is still in development.

## Cleaner preferences and readiness

Appearance and game connection now use compact responsive cards. Installation details and reset stay behind disclosures. Required tower paths are labelled as unlock requirements rather than a single legal build. A pending round-start checkpoint can resume through fresh play-state observation; ambiguous pending purchases remain refused.
