# Bloons+ Preview 78

## Replay recovery

- Auto Start commands now pass through the parser, recorder and replay controller as explicit on/off settings.
- Replay waits for observed confirmation, closes the pause menu, and saves completion before proceeding.
- Failed checkpoint saves retain the command. Resume rechecks the source setting instead of trusting a cached value.
- Purchase confirmation keeps its input slot, and automatic round control respects explicit manual settings.
- Resumed round OCR uses the selected mode's expected counter total.

## Cleaner Settings

- Appearance, Game & VM, and Support remain the main sections.
- Manual updates live under **App updates**, with clear main-PC-to-VM wording.
- Setup and ISO controls appear only when needed; mobile and keyboard presentation is improved.

## Verification and limits

91 focused Python checks passed, covering control phases, resume recovery, real parser/writer/replay branches, cursor preservation, timing and round counters. JavaScript syntax and route admission checks are also checked separately. These are offline checks, not proof of winning new routes.

Complete source `end_round` conversion remains in development. Routes declaring omitted manual-round controls remain excluded. Original recordings, including CHIMPS, are unchanged. The sweep continues to target missing medals only.
