// Validate a recording without loading TensorFlow or interacting with the game.
function validateRoute(text, mode, catalog) {
  const errors = [];
  const active = new Map();
  let round = 0;
  const allowed = { primary_only: 'primary', military_only: 'military', magic_monkeys_only: 'magic' }[mode];
  for (const [index, raw] of text.split(/\r?\n/).entries()) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    const report = message => errors.push({ line: index + 1, message });
    let match;
    if ((match = /^round\s+(\d+)\s*$/.exec(line))) {
      const next = Number(match[1]);
      if (next < round) report(`Round moved backwards from ${round} to ${next}`);
      round = next;
    } else if ((match = /^place\s+(\w+)\s+(\w+)\s+at\s+(\d+),\s*(\d+)/.exec(line))) {
      const [, type, name] = match;
      if (active.has(name)) report(`Tower ${name} placed twice without being sold`);
      const monkey = catalog.monkeys[type];
      const hero = catalog.heros[type];
      if (!monkey && !hero) report(`Unknown tower or hero ${type}`);
      if (allowed && monkey && monkey.type !== allowed) report(`${type} is forbidden in ${mode}`);
      if (mode === 'chimps' && type === 'farm') report('Banana Farms are forbidden in CHIMPS');
      active.set(name, { type, tiers: [0, 0, 0] });
    } else if ((match = /^upgrade\s+(\w+)\s+path\s+([0-2])\b/.exec(line))) {
      const tower = active.get(match[1]);
      if (!tower) { report(`Upgrade targets unplaced tower ${match[1]}`); continue; }
      tower.tiers[Number(match[2])]++;
      const tiers = [...tower.tiers].sort((a, b) => b - a);
      if (tiers[0] > 5 || tiers[1] > 2 || tiers[2] > 0) report(`Illegal crosspath ${tower.tiers.join('-')} for ${match[1]}`);
    } else if ((match = /^(sell|retarget|special)\s+(\w+)\b/.exec(line))) {
      if (!active.has(match[2])) report(`${match[1]} targets unplaced tower ${match[2]}`);
      if (match[1] === 'sell') {
        if (mode === 'chimps') report('Selling is forbidden in CHIMPS');
        active.delete(match[2]);
      }
    }
  }
  return errors;
}
// Compare executable actions, ignoring comments and arbitrary tower identifiers.
function strategySignature(text) {
  const names = new Map();
  return text.split(/\r?\n/).map(line => line.trim()).filter(line => line && !line.startsWith('#'))
    .map(line => {
      const placement = /^place\s+\w+\s+(\w+)\s+at\b/.exec(line);
      if (placement) names.set(placement[1], `tower${names.size}`);
      return line.replace(/\b\w+\b/g, token => names.get(token) || token).replace(/\s+/g, ' ').replace(/,\s*/g, ',');
    }).join('\n');
}
module.exports = { validateRoute, strategySignature };
