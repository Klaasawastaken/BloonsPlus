# Bloons+ Preview 31

## Select towers behind an open panel

A live missing-medal run exposed a hero panel covering a tower's world position. Selection retries kept clicking the panel and could not confirm the upgrade.

Bloons+ now uses the existing independent HUD anchors to detect a covering panel, closes it with two centre clicks, and then selects the intended tower. This applies to upgrade selection, reselection, targeting and selling. It avoids opening the pause menu and preserves an uncovered tower click.

The captured game frame reproduced the issue offline. Scale/ownership checks and existing upgrade-observation/queue checks pass. Live deployment waits until the active replay finishes; the patch is not claimed to have earned a medal yet.

Includes Preview 30's repeating ability support and three new source candidates. Repeated ability input has now been observed during the natural missing-medal sweep. Original CHIMPS recordings are unchanged. V1.0 remains in development.
