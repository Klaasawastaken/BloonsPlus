# Bloons+ Preview 22

## Glacial Trail upgrade recovery

- Retain an unavailable planned upgrade when confirmed tower placement history predicts the map's two-round freeze window.
- Wait for predicted thaw without blocking game observation, then reselect and read the exact owned tiers before purchase.
- Keep dependent upgrades behind the unresolved tier; preserve deferral in checkpoints across restarts.
- Unknown placement history and unrelated maps do not invent freeze predictions.

Includes Preview 20 Settings and Preview 21 VM clock-aware activity fixes.

## Checks and limits

Seven offline availability checks cover per-tower cycles, immune/unknown towers, sale/replacement, deferral gates, checkpoint restoration and the actual replay retry branch. The 10 resume and 18 timing checks also pass. Original CHIMPS recordings and game/save files are unchanged.

This predicts a freeze window from history and reconciles live availability; visual freeze recognition and a subsequent Glacial Trail victory remain unverified. Gameplay is reserved for missing medals.

Preview release: clean-install validation and other V1.0 requirements remain in progress.
