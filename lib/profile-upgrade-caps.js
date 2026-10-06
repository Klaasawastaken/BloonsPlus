// Read-only launch snapshot for optional spending; never modifies the profile.
const names = require('../data/catalogs/save-upgrade-names');
const normal = value => String(value || '').toLowerCase().replace(/[^a-z0-9]/g, '');
const aliases = { beasthandler: 'beast', buccaneer: 'boat', alchemist: 'alch', boomerang: 'boomer' };
function upgradeCaps(profile, catalog, towerTypes) {
  if (profile?.available !== true || !Array.isArray(profile.acquiredUpgrades)) return null;
  const acquired = new Set(profile.acquiredUpgrades.map(normal));
  const entries = new Map(Object.entries(catalog || {}).map(([key, value]) => [key.toLowerCase(), value]));
  return Object.fromEntries(towerTypes.map(type => {
    const slug = aliases[normal(type)] || normal(type);
    const caps = [0, 0, 0];
    for (let path = 0; path < 3; path++) {
      for (let tier = 1; tier <= 5; tier++) {
        const suffix = path === 0 ? `${tier}-x-x` : path === 1 ? `x-${tier}-x` : `x-x-${tier}`;
        const name = entries.get(`${slug} ${suffix}`)?.[0];
        // Unknown catalog names cannot authorize an optional purchase either.
        if (typeof name !== 'string' || !names.owns(acquired, type, name)) break;
        caps[path] = tier;
      }
    }
    return [type, caps];
  }));
}
module.exports = { upgradeCaps };
