const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { getMapMechanics } = require('../lib/map-mechanics');

// Exercise the actual replay launch policy without creating a gameplay process.
// Restoring Chutes' phase-aware status must fail the spatial-retry assertion.
const source = fs.readFileSync(require.resolve('../lib/automation'), 'utf8').replace(/\r\n/g, '\n');
function functionSource(name) {
  const start = source.indexOf(`function ${name}(`);
  assert.notEqual(start, -1);
  const end = source.indexOf('\n}\n', start);
  assert.notEqual(end, -1);
  return source.slice(start, end + 2);
}
const launch = vm.runInNewContext(
  `${functionSource('parsePlaythroughFile')}\n${functionSource('spawnReplay')}\nspawnReplay`,
  {
    fs, path, getMapMechanics,
    PROJECT_ROOT: path.resolve(__dirname, '..'),
    AUTOBTD6_DIR: path.resolve(__dirname, '../autobtd6'),
    readLocalProgress: () => ({ available: false }),
    upgradeCaps: () => null,
    getRuntime: () => ({ executable: 'offline-python' }),
    runtimeEnvironment: () => ({}),
    // Map-order persistence is unrelated to placement policy; keep the fixture read-only.
    syncMapPositions: () => {},
    spawn: (executable, args, options) => ({ executable, args, options }),
  },
);
function policy(map, boss = false) {
  const filename = boss ? `bloonarius#normal#${map}#event-offline.btd6` : `${map}#hard#1920x1080.btd6`;
  return launch(['file', filename], { type: 'black-border-sweep' }).options.env;
}

for (const boss of [false, true]) {
  assert.equal(policy('chutes', boss).BLOONS_DYNAMIC_PLACEMENT, '0',
    'Alternating Chutes lanes must not force thirteen retries at the same illegal point');
  assert.equal(policy('chutes', boss).BLOONS_MOVING_PLATFORMS, '0',
    'Alternating lanes cannot move stationary tower selection coordinates');
}
assert.match(getMapMechanics('chutes').rules.join(' '), /both paths.*alternates/,
  'Spatial retries do not remove the alternating-lane coverage requirement');

for (const map of ['covered_garden', 'geared', 'sanctuary', 'erosion', 'polyphemus',
  'glacial_trail', 'bloonarius_prime', 'muddy_puddles', 'x_factor', 'tricky_tracks']) {
  assert.equal(policy(map).BLOONS_DYNAMIC_PLACEMENT, '1', `${map} must retain its existing spatial guard`);
}
for (const map of ['geared', 'sanctuary']) {
  assert.equal(policy(map).BLOONS_MOVING_PLATFORMS, '1', `${map} must retain moving-platform tracking`);
}
assert.equal(policy('monkey_meadow').BLOONS_DYNAMIC_PLACEMENT, '0');
console.log('Chutes replay launch allows existing spatial retries; other dynamic-map guards remain intact.');
