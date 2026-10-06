# Bloons+ Preview 44

## Safer checkpoint recovery

Resume now validates unresolved-upgrade collections, action metadata and strictly integer offsets. Duplicate recorded queue positions are rejected so a malformed checkpoint cannot repeat a placement or purchase. These cases reach the existing explicit resume-refusal handler instead of an uncaught exception. Valid pending upgrades still rejoin the route and use observed ownership probes.

Eleven existing offline resume checks pass. Additional pure checks cover null entries, boolean offsets, malformed metadata and duplicate action positions. No gameplay was launched for validation.

Refreshed coverage: 509 eligible map/mode pairs and 695 gaps. Manual-round source plans require observed Auto Start control and remain unsupported. Original CHIMPS recordings and game saves remain unchanged.

Includes Preview 43 read-only upgrade ownership caps. Deployment remains batched at healthy replay boundaries. This is a preview, not completed V1.0.
