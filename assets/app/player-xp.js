(function (root) {
  'use strict';
// XP needed to go from each BTD6 level to the next (bloonswiki.com/Level; matches live reads of
// 580,000 at level 94 and 590,000 at level 95). After 155, every 20M XP is a veteran level.
const VETERAN_XP = 20_000_000;
const EARLY_LEVEL_XP = [480, 1100, 620, 1150, 2500, 3000, 3500, 3500, 4000, 4250, 4500, 4500, 4900,
  7000, 8000, 9000, 10000, 12000, 12000, 13000, 14000, 15000, 16000, 17000, 18000, 19000, 20000, 21000, 25000];
function xpToNextLevel(level) {
  const next = level + 1;
  if (next > 155) return VETERAN_XP;
  if (next <= 30) return EARLY_LEVEL_XP[next - 2];
  if (next <= 49) return 30000 + 5000 * (next - 31);
  if (next <= 100) return 130000 + 10000 * (next - 50);
  if (next === 101) return 650000;
  if (next <= 149) return 700000 + 50000 * (next - 102);
  if (next === 150) return 8271000;
  return 10000000 + 1000000 * (next - 151);
}


function saveLevelProgress(profile) {
  const rank = profile?.rank, total = profile?.xp;
  if (!Number.isInteger(rank) || rank < 1 || rank > 155 || !Number.isFinite(total) || total < 0) return null;
  let threshold = 0;
  for (let level = 1; level < rank; level++) threshold += xpToNextLevel(level);
  if (rank === 155) return total >= threshold ? { capped: true, rank, total } : null;
  const nextLevelXp = xpToNextLevel(rank), xp = total - threshold;
  // Save fields must agree. A stale/malformed rank cannot fabricate a filled bar.
  if (xp < 0 || xp >= nextLevelXp) return null;
  return { capped: false, rank, xp, nextLevelXp, remaining: nextLevelXp - xp };
}
const api = { xpToNextLevel, saveLevelProgress };
if (typeof module !== 'undefined' && module.exports) module.exports = api;
else root.BloonsPlayerXp = api;
})(typeof window === 'undefined' ? globalThis : window);
