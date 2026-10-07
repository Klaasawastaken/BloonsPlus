// Save identifiers can retain old names and spelling errors after upgrades are renamed.
// Shared by the UI and route preflight; matching is scoped to a tower.
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.SaveUpgradeNames = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const normal = value => String(value || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const groups = [
    [['ice', 'Ice Monkey'], { 'cold snap': 'Metal Freeze' }],
    [['boomerang', 'boomer', 'Boomerang Monkey'], { 'bionic boomerang': 'Bionc Boomerang' }],
    [['mortar', 'Mortar Monkey'], { 'faster reload': 'Mortar Faster Reload', 'rapid reload': 'Mortar Rapid Reload', 'shell shock': 'Shockwave' }],
    [['skywarden'], { 'storm pulse': 'StormsPulse' }],
    [['alchemist', 'alch'], { 'faster throwing': 'Alchemist Faster Throwing' }],
    [['sniper', 'Sniper Monkey'], { 'full auto riffle': 'Full Auto Rifle' }],
    [['spike', 'Spike Factory'], { 'smart spikes': 'Directed Spikes' }],
    [['druid'], { 'monarch of storms': 'Superstorm' }],
    [['wizard', 'Wizard Monkey'], { 'prince of darkness': 'Soulbind' }],
    [['engineer', 'Engineer Monkey'], { 'sentry champion': 'Sentry Paragon' }],
  ];
  const aliases = new Map();
  for (const [towers, upgrades] of groups) {
    const names = new Map(Object.entries(upgrades).map(([name, saved]) => [normal(name), saved]));
    for (const tower of towers) aliases.set(normal(tower), names);
  }
  const boats = new Set(['buccaneer', 'boat', 'Monkey Buccaneer'].map(normal));
  function candidates(tower, name) {
    if (!name) return [];
    const values = [name];
    if (boats.has(normal(tower))) values.push('Buccaneer-' + name);
    const alias = aliases.get(normal(tower))?.get(normal(name));
    if (alias) values.push(alias);
    return [...new Set(values.map(normal))];
  }
  function owns(owned, tower, name) {
    return candidates(tower, name).some(candidate => owned.has(candidate));
  }
  return Object.freeze({ candidates, owns });
});
