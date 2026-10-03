const fs = require('node:fs');
const path = require('node:path');
const { readActiveBossEvent } = require('./boss-events');

const ROOT = __dirname;
const ROUTES = path.join(ROOT, 'route-library');
const GENERATED = path.join(ROUTES, 'generated-boss');
const slug = value => String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');

function findBaseRoute(map) {
  const wanted = slug(map);
  const files = [];
  function walk(dir) { for (const item of fs.readdirSync(dir, { withFileTypes: true })) { const full = path.join(dir, item.name); if (item.isDirectory()) walk(full); else if (/\.btd6$/i.test(item.name)) files.push(full); } }
  walk(ROUTES);
  return files.find(file => slug(path.basename(file).split('#')[0]) === wanted) || null;
}

function generate({ elite = false } = {}) {
  return readActiveBossEvent().then(event => {
    if (!event.available || !event.active) return { available: false, reason: 'No active boss event.' };
    const metadata = event.metadata?.[elite ? 'elite' : 'normal'];
    if (!metadata?.map) return { available: false, reason: 'Active event metadata has no map.' };
    const base = findBaseRoute(metadata.map);
    if (!base) return { available: false, reason: `No base route exists for ${metadata.map}.` };
    const blocked = new Map((metadata.limitedTowers || []).map(item => [slug(item.tower), item]));
    const lines = fs.readFileSync(base, 'utf8').split(/\r?\n/);
    const filtered = lines.filter(line => {
      const match = line.match(/^place\s+(\S+)/i); if (!match) return true;
      const tower = blocked.get(slug(match[1]));
      return !tower || tower.max !== 0;
    });
    fs.mkdirSync(GENERATED, { recursive: true });
    const filename = `${slug(event.bossType)}#${elite ? 'elite' : 'normal'}#${slug(metadata.map)}#event-${event.id}.btd6`;
    const target = path.join(GENERATED, filename);
    const header = `# EXPERIMENTAL BOSS ROUTE\n# event=${event.id} boss=${event.bossType} variant=${elite ? 'elite' : 'normal'}\n# map=${metadata.map} difficulty=${metadata.difficulty} mode=${metadata.mode}\n# modifiers speed=${metadata.bossSpeed} health=${metadata.bossHealth} disableMK=${metadata.disableMK}\n`;
    fs.writeFileSync(target, header + filtered.join('\n'));
    return { available: true, experimental: true, eventId: event.id, bossType: event.bossType, variant: elite ? 'elite' : 'normal', map: metadata.map, route: path.relative(ROOT, target), baseRoute: path.relative(ROOT, base), filteredRestrictions: [...blocked.keys()] };
  });
}

module.exports = { generate };
