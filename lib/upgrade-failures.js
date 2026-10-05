// Recovered retry warnings are history, not unresolved upgrade failures.
function unresolvedUpgradeCount(events) {
  if (!Array.isArray(events)) return null;
  const pending = new Map();
  let observedAmbiguity = false;
  for (const event of events) {
    if (!event?.tower) continue;
    if (event.type === 'sell' || event.type === 'place') {
      // Reused names are different tower instances. Never let the new tower
      // retrospectively confirm an old tower's unresolved purchase.
      for (const key of pending.keys()) {
        if (key.startsWith(`${event.tower}:`)) pending.set(key, null);
      }
      continue;
    }
    if (event.type !== 'upgrade' || !Number.isInteger(event.path) || event.path < 0 || event.path > 2) continue;
    const key = `${event.tower}:${event.path}`;
    if (event.status === 'cash-ambiguous') {
      observedAmbiguity = true;
      const target = event.expectedUpgradeTiers;
      const before = event.upgradeObservation?.before;
      const valid = tiers => Array.isArray(tiers) && tiers.length === 3
        && tiers.every(tier => Number.isInteger(tier) && tier >= 0 && tier <= 5);
      const level = valid(target) ? target[event.path]
        : valid(before) && before[event.path] < 5 ? before[event.path] + 1 : null;
      const previous = pending.get(key);
      // An unreadable earlier target remains uncertain; do not guess recovery.
      pending.set(key, pending.has(key) && (previous == null || level == null)
        ? null : Math.max(previous || 0, level || 0) || null);
    } else if (event.status === 'panel-tier-confirmed' && pending.has(key)) {
      const target = pending.get(key);
      if (target != null && Number.isInteger(event.upgradeLevel) && event.upgradeLevel <= 5 && event.upgradeLevel >= target)
        pending.delete(key);
    }
  }
  return observedAmbiguity ? pending.size : null;
}
module.exports = { unresolvedUpgradeCount };
