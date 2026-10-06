// Shared read-only medal decoder for the browser and sweep.
(function (root) {
const MEDAL_MODES = ['easy', 'primary_only', 'deflation', 'medium', 'military_only', 'reverse', 'apopalypse', 'hard',
  'magic_monkeys_only', 'double_hp_moabs', 'half_cash', 'alternate_bloons_rounds', 'impoppable', 'chimps'];
// CHIMPS uses the internal mode ID 'Clicks'. Moon Landing's observed CHIMPS
// victory saved Hard/Clicks=1050185 while SuperChimps remained 2. The generated
// BTD-Mod-Helper GameModeType enum also lists Clicks as a game mode.
const SAVE_MODE_NAMES = { PrimaryOnly: 'primary_only', Deflation: 'deflation', MilitaryOnly: 'military_only',
  Apopalypse: 'apopalypse', Reverse: 'reverse', MagicOnly: 'magic_monkeys_only', DoubleMoabHealth: 'double_hp_moabs',
  HalfCash: 'half_cash', AlternateBloonsRounds: 'alternate_bloons_rounds', Impoppable: 'impoppable', Clicks: 'chimps' };
// Derived empirically from saved medals and confirmed victories: every observed value falls cleanly below ~1,200 (an in-progress
// attempt counter) or above ~1,049,000 (medal earned, with the 0x100000 bit set) — never
// in between. The old `value > 2` threshold wrongly treated any in-progress attempt as earned.
const MEDAL_VALUE_THRESHOLD = 0x100000;
function medalsFromMapRecord(record) {
  const medals = Object.fromEntries(MEDAL_MODES.map(mode => [mode, false]));
  for (const [difficulty, data] of Object.entries(record?.difficult || {})) {
    for (const [mode, value] of Object.entries(data?.modes || {})) {
      const key = mode === 'Standard' ? difficulty.toLowerCase() : SAVE_MODE_NAMES[mode];
      if (!key || !(key in medals)) continue;
      const expectedDifficulty = ['easy', 'primary_only', 'deflation'].includes(key) ? 'easy'
        : ['medium', 'military_only', 'reverse', 'apopalypse'].includes(key) ? 'medium' : 'hard';
      // Saves can contain mode placeholders under unrelated difficulties.
      if (difficulty.toLowerCase() !== expectedDifficulty) continue;
      medals[key] = typeof value === 'boolean' ? value
        : Number.isSafeInteger(value) && value >= 0 ? value >= MEDAL_VALUE_THRESHOLD
          : value && typeof value === 'object' && typeof value.completed === 'boolean' ? value.completed
            : null; // Unknown schema/value must never mean permission to replay.
    }
  }
  return medals;
}
const api = Object.freeze({medalsFromMapRecord});
if (typeof module !== 'undefined' && module.exports) module.exports = api;
else root.BloonsMedals = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
