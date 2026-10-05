const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { medalsFromMapRecord } = require('../lib/btd6-save-progress');
const source = fs.readFileSync(require.resolve('../lib/automation'), 'utf8');
const start = source.indexOf('function savedMedalState(');
const end = source.indexOf('\n}\n', start) + 2;
function check(profile) {
  return vm.runInNewContext(source.slice(start, end) + '\nsavedMedalState("another_brick", "hard")', {
    readLocalProgress: () => profile,
    fs: { readFileSync: () => JSON.stringify({another_brick: {name: 'Another Brick'}}) },
    MAPS_PATH: 'unused', medalsFromMapRecord,
    normalizeMapName: name => name.toLowerCase().replace(/[^a-z0-9]/g, ''),
  });
}
assert.equal(check({available:false}), null);
assert.equal(check({available:true,mapProgress:{}}), null);
assert.equal(check({available:true,mapProgress:{AnotherBrick:{}}}), null);
assert.equal(check({available:true,mapProgress:{AnotherBrick:{difficult:{Hard:{modes:{Standard:784}}}}}}), false);
assert.equal(check({available:true,mapProgress:{AnotherBrick:{difficult:{Hard:{modes:{Standard:1049864}}}}}}), true);
console.log('Authoritative sweep medal checks passed.');
