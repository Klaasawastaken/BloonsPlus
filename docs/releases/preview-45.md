# Bloons+ Preview 45

## Recover held placement before tower actions

A live Flooded Valley Reverse screenshot showed a held Sniper ghost while upgrades repeatedly reported an unselected panel. The previous detector required a nudge-mode cancel control that this ordinary placement layout did not display.

Detection now requires the placement-only close anchor plus either the nudge cancel control or multiple cyan shop-card rows. Tower selection cancels a detected held placement first, waits for a fresh frame, then selects the recorded tower. If placement remains held, the replay queues the tower action again and sends no dependent action input in that iteration.

The captured private frame is recognized. Pure call-order checks confirm cancel-before-selection and withholding the target click when held state persists. Three existing placement checks and 20 upgrade checks pass; live recovery with this patch remains pending deployment. No screenshot/profile information is published.

Flooded Valley Reverse subsequently finished at round 60 and its saved medal was confirmed, using the earlier runtime. Never replay that earned medal for validation. Original CHIMPS recordings and game saves remain unchanged.

Includes checkpoint validation and saved unlock caps. Preview release; V1.0 remains incomplete.
