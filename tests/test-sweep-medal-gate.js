const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { medalsFromMapRecord } = require('../lib/btd6-save-progress');
const source = fs.readFileSync(require.resolve('../lib/automation'), 'utf8').replace(/\r\n/g, '\n');
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
for (const value of [null, '1049864', {}, {completed:'yes'}, -1, NaN, Infinity, 0.5]) {
  assert.equal(check({available:true,mapProgress:{AnotherBrick:{difficult:{Hard:{modes:{Standard:value}}}}}}), null,
    'Unrecognized medal values cannot authorize a new replay');
}
for (const value of [true, {completed:true}]) {
  assert.equal(check({available:true,mapProgress:{AnotherBrick:{difficult:{Hard:{modes:{Standard:value}}}}}}), true);
}
console.log('Authoritative sweep medal checks passed.');

const ui = fs.readFileSync('assets/app/app.js', 'utf8').replace(/\r\n/g, '\n');
const uiStart = ui.indexOf('function medalsFromLocalRecord(');
const uiFn = ui.slice(uiStart, ui.indexOf('\nfunction renderMaps()', uiStart));
const browser = {};
vm.runInNewContext(fs.readFileSync('data/catalogs/medal-progress.js','utf8'),browser);
for (const modes of [{Clicks:2,SuperChimps:1050185}, {SuperChimps:1050185,Clicks:2}]) {
  const record = {difficult:{Hard:{modes}}};
  assert.equal(medalsFromMapRecord(record).chimps, false, 'SuperChimps cannot grant the ordinary CHIMPS medal');
  assert.equal(vm.runInNewContext(uiFn + '\nmedalsFromLocalRecord(record).chimps', {record, BloonsMedals:browser.BloonsMedals}), false);
}
for (const difficult of [
  {Hard:{modes:{Clicks:1050185,SuperChimps:2}}, Medium:{modes:{Clicks:2}}},
  {Medium:{modes:{Clicks:2}}, Hard:{modes:{Clicks:1050185,SuperChimps:2}}},
]) {
  const record = {difficult};
  assert.equal(medalsFromMapRecord(record).chimps, true, 'Only Hard supplies the CHIMPS medal');
  assert.equal(vm.runInNewContext(uiFn + '\nmedalsFromLocalRecord(record).chimps', {record, BloonsMedals:browser.BloonsMedals}), true);
}
for (const value of [0, 784, 1049864, true, false, null, '1049864', -1, 0.5, {}]) {
  const record = {difficult:{Hard:{modes:{Standard:value}}}};
  const actual = vm.runInNewContext(uiFn + '\nmedalsFromLocalRecord(record).hard', {record, BloonsMedals:browser.BloonsMedals});
  assert.equal(actual, medalsFromMapRecord(record).hard, 'UI and sweep must agree on unknown values');
}
async function checkUnknownMode(available) {
  const first = source.indexOf('      if (savedMedal === null)');
  const block = source.slice(first, source.indexOf('      attemptedFiles.add(entry.filename);', first));
  const attempted = new Set(), waits = [];
  const context = {savedMedal:null, readLocalProgress:()=>({available}), attempted, gamemode:'hard', map:'test',
    counts:{skippedModes:0}, job:{}, saveSweepProgressFor:()=>{}, pushLog:()=>{},
    setTimeout:(fn, ms)=>{waits.push(ms);fn();}};
  await vm.runInNewContext(`(async()=>{for(let once=0;once<1;once++){${block}}})()`, context);
  assert.equal(attempted.has('hard'), available, 'Readable profile with unknown mode must not block other modes');
  assert.equal(waits.length, available ? 0 : 1, 'An unavailable whole profile still waits safely');
}
Promise.all([checkUnknownMode(true), checkUnknownMode(false)])
  .then(()=>console.log('Unknown medals preserve UI parity and let other readable modes continue.'))
  .catch(error=>{console.error(error);process.exitCode=1;});
