# Bloons+ Preview 39

## One input owner per frame

Automatic Play/Fast Forward now waits when the replay has just issued a route action, still holds a placement, or already sent a play toggle. The old gate admitted automatic input from the pre-action screenshot, allowing it to compete with tower commands on the same frame.

The regression failed before the patch and passes afterward. Seven round-control, five relative-speed and four cursor checks pass offline. Normal idle-frame play controls remain available. This fixes a control race; it does not prove every historical defeat resolved.

Includes Preview 38 move-only cursor support and its separately named #Ouch ABR candidate. No original recordings were modified. New candidates are not claimed as victories; live play remains limited to missing medals.
