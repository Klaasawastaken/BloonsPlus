# Bloons+ Preview 40

## Net Monkey Money per hour

The rate now shows signed balance changes. Spending can produce a negative value; it is no longer clamped to zero or presented as farming income. The app labels it Net MM/hr and explains the sampling window, and the account-progress wiki documents it.

Invalid negative save balances are rejected. Small negative changes round cleanly to zero. Existing source-switch, clock-reset, missing-data and XP counter guards remain in place. The spending regression failed before the patch and now passes.

Includes the earlier cursor and automatic-input fixes. This preview does not establish clean-install readiness, universal route victories or complete V1.0 coverage. Live automation remains limited to missing medals.
