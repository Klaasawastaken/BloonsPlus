// Validate a recording without loading TensorFlow or interacting with the game.
function validateRoute(text, mode, catalog) {
  const errors = [];
  const active = new Map();
  let round = 0;
  const allowed = { primary_only: 'primary', military_only: 'military', magic_monkeys_only: 'magic' }[mode];
  for (const [index, raw] of text.split(/\r?\n/).entries()) {
    const rawLine = raw.trim();
    const selection = /^((?:upgrade|retarget|special|sell)\s.+) at (\d+), (\d+)$/.exec(rawLine);
    const line = selection ? selection[1] : rawLine;
    // Older conversions called paid hero levels harmless and omitted them.
    // Syntax-valid remaining actions are not a faithful version of that strategy.
    if (/^#\s*dropped\b.*\bhero level purchases\b/i.test(line)) {
      errors.push({ line: index + 1, message: 'Conversion omitted required paid hero levels; restore purchase support before using this route' });
    }
    if (/^#\s*dropped\b.*\b(?:change_autostart|end_round)\s*\(/i.test(line)) {
      errors.push({ line: index + 1, message: 'Conversion omitted manual-round controls; restore autostart and end-round semantics before using this route' });
    }
    if (!line || line.startsWith('#')) continue;
    const report = message => errors.push({ line: index + 1, message });
    // Match the replay parser's complete command grammar. Partial matches used
    // to accept typos/trailing garbage that Python silently skipped at runtime.
    const executable = /^place [a-z_]+ \w+ at \d+, \d+(?: for (?:\d+|\?\?\?))?(?: with (?:\d{1,2}|100)% discount)?$/.test(line)
      || /^upgrade \w+ path [0-2](?: for (?:\d+|\?\?\?))?(?: with (?:\d{1,2}|100)% discount)?$/.test(line)
      || /^retarget \w+(?: to \d+, \d+)?$/.test(line)
      || /^special \w+(?: to \d+, \d+)?$/.test(line)
      || /^sell \w+$/.test(line)
      || /^remove obstacle at \d+, \d+ for \d+$/.test(line)
      || /^round [1-9]\d*(?: after \d+(?:\.\d+)? seconds)?$/.test(line)
      || /^cash \d+$/.test(line)
      || /^wait \d+(?:\.\d+)? seconds$/.test(line)
      || /^speed (?:fast|slow)$/.test(line)
      || /^start round (?:fast|slow)$/.test(line)
      || line === 'change speed'
      || /^ability (10|[1-9])(?: after \d+(?:\.\d+)? seconds)?(?: at \d+, \d+(?: move after \d+(?:\.\d+)? seconds)?)?$/.test(line)
      || /^(?:repeat|stop) ability (?:10|[1-9])$/.test(line)
      || line === 'stop all abilities'
      || /^move cursor to \d+, \d+$/.test(line)
      || /^click map at \d+, \d+$/.test(line);
    if (!executable) { report('Unsupported or malformed route command'); continue; }
    let match;
    if ((match = /^round\s+(\d+)(?: after \d+(?:\.\d+)? seconds)?\s*$/.exec(line))) {
      const next = Number(match[1]);
      if (next < round) report(`Round moved backwards from ${round} to ${next}`);
      round = next;
    } else if ((match = /^place\s+(\w+)\s+(\w+)\s+at\s+(\d+),\s*(\d+)/.exec(line))) {
      const [, type, name] = match;
      if (active.has(name)) report(`Tower ${name} placed twice without being sold`);
      const monkey = catalog.monkeys[type];
      const hero = catalog.heros[type];
      if (!monkey && !hero) report(`Unknown tower or hero ${type}`);
      if (hero && [...active.values()].some(tower => tower.hero)) report('Only one active hero is allowed in a solo route');
      if (allowed && monkey && monkey.type !== allowed) report(`${type} is forbidden in ${mode}`);
      if (mode === 'chimps' && type === 'farm') report('Banana Farms are forbidden in CHIMPS');
      active.set(name, { type, hero: !!hero, tiers: [0, 0, 0] });
    } else if ((match = /^upgrade\s+(\w+)\s+path\s+([0-2])\b/.exec(line))) {
      const tower = active.get(match[1]);
      if (!tower) { report(`Upgrade targets unplaced tower ${match[1]}`); continue; }
      if (tower.hero) { report('Hero levels cannot be purchased with ordinary tower-path upgrade commands'); continue; }
      tower.tiers[Number(match[2])]++;
      const upgradedPath = Number(match[2]);
      // A second Crossbow Master can depend on Monkey Knowledge; CHIMPS never
      // permits that exception. Account readiness must check it in other modes.
      const knowledgeException = tower.type === 'dart' && upgradedPath === 2 && mode !== 'chimps';
      const otherTierFives = [...active.entries()].filter(([name, other]) => name !== match[1]
        && other.type === tower.type && other.tiers[upgradedPath] === 5).length;
      if (tower.tiers[upgradedPath] === 5 && otherTierFives >= (knowledgeException ? 2 : 1)) {
        report(`Duplicate active tier-five ${tower.type} path ${upgradedPath}`);
      }
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
      const placement = /^place\s+(\w+)\s+(\w+)(\s+at\b.*)$/.exec(line);
      if (placement) {
        names.set(placement[2], `tower${names.size}`);
        line = `place ${placement[1]} ${names.get(placement[2])}${placement[3]}`;
      } else {
        line = line.replace(/^(upgrade|retarget|sell|special)\s+(\w+)\b/, (_, action, name) => `${action} ${names.get(name) || name}`);
      }
      return line.replace(/\s+/g, ' ').replace(/,\s*/g, ',');
    }).join('\n');
}
module.exports = { validateRoute, strategySignature };
