# Bloons+ Preview 23

## More accurate failure reports

- Separate recovered upgrade retry warnings from upgrades still unresolved at the end of a run.
- Require later panel-tier confirmation for the same tower, path and requested tier before clearing uncertainty.
- Preserve uncertainty when evidence is missing, a target is unknown, or a tower name was sold/reused.
- Keep exact requested tiers in new action events and include unresolved counts in failure reports.
- Existing failure history remains intact; older logs retain conservative classification.

Includes Preview 22 Glacial Trail deferral, Preview 21 clock-aware activity, and Preview 20 Settings improvements.

## Checks and limits

Focused offline failure-classification checks pass and the Python action ledger compiles. This improves diagnostic attribution, not strategy strength or damage output. Live deployment awaits the current replay boundary. No game/save files or original CHIMPS recordings were edited.

Preview release: V1.0 requirements remain unfinished.
