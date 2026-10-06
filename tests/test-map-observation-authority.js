const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const mapNames = require('../data/catalogs/map-names');
const source = fs.readFileSync('assets/app/app.js', 'utf8');
const helper = source.slice(source.indexOf('const mapObservationFor ='), source.indexOf('function medalsFromLocalRecord'));
function read(maps, name='skulltweak') {
  return vm.runInNewContext(helper + ';mapObservationFor(name)', {
    detectedProgress: {maps}, mapProgressKey: mapNames.normalize, name,
  });
}
const save = {localSaveSource:'btd6-profile-save', localSaveReadAt:'2026-10-06T12:00:00Z',
  medals:{chimps:false, impoppable:false, easy:true}};
const scan = {scannedAt:'2026-10-07T12:00:00Z', medals:{chimps:true, impoppable:true}};
for (const maps of [{skulltweak:save, Skulltweak:scan}, {Skulltweak:scan, skulltweak:save}]) {
  const result = read(maps);
  assert.equal(result.medals.chimps, false);
  assert.equal(result.medals.impoppable, false);
  assert.equal(result.medals.easy, true);
}
assert.equal(read({Skulltweak:scan, skulltweak:{...save,localSaveReadAt:null}}).medals.chimps,false);
assert.equal(read({skulltweak:{...save,localSaveReadAt:'bad'},Skulltweak:scan}).medals.impoppable,false);
assert.equal(read({skulltweak:save,Skulltweak:{...save,localSaveReadAt:'2026-10-06T13:00:00Z',medals:{chimps:true}}}).medals.chimps,true);
assert.equal(read({Skulltweak:scan,skulltweak:{scannedAt:'2026-10-08T12:00:00Z',medals:{chimps:false}}}).medals.chimps,false);
assert.equal(read({towncentre:{...save}, 'Town Center':scan},'town_center').medals.chimps,false);
assert.equal(Object.keys(read({},'unknown')).length,0);
console.log('Map observations: save authority, alias order, fresh reads and unknown maps pass.');
