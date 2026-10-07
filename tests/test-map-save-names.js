const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const mapNames = require('../data/catalogs/map-names');
const {medalsFromMapRecord} = require('../lib/btd6-save-progress');
for (const [save, display] of [['TownCentre','Town Center'],['ThreeMinesAround',"Three Mines 'Round"],['#Ouch','ouch'],['Cubism','cubism']]) {
  assert.equal(mapNames.normalize(save),mapNames.normalize(display));
}
assert.notEqual(mapNames.normalize('Town Central'),mapNames.normalize('Town Center'));
assert.notEqual(mapNames.normalize('Three Mines'),mapNames.normalize("Three Mines 'Round"));
const browser = {};
vm.runInNewContext(fs.readFileSync('data/catalogs/map-names.js','utf8'),browser);
assert.equal(browser.BloonsMapNames.normalize('TownCentre'),'towncenter');
const source = fs.readFileSync('lib/automation.js','utf8').replace(/\r\n/g,'\n');
function extract(name) {
  const start=source.indexOf(`function ${name}(`);
  assert.ok(start>=0);
  return source.slice(start,source.indexOf('\n}\n',start)+2);
}
const catalogs = {town_center:{name:'Town Center'},three_mines_round:{name:"Three Mines 'Round"}};
for (const [slug, saved] of [['town_center','TownCentre'],['three_mines_round','ThreeMinesAround']]) {
  for (const [value, expected] of [[1049864,true],[784,false],[null,null]]) {
    const profile = {available:true,mapProgress:{[saved]:{difficult:{Hard:{modes:{Standard:value}}}}}};
    const context = {readLocalProgress:()=>profile,fs:{readFileSync:()=>JSON.stringify(catalogs)},MAPS_PATH:'unused',
      medalProfileIdentity:()=>"fixture", normalizeMapName:mapNames.normalize,medalsFromMapRecord,syncMedalsFromObservations:()=>{},pushLog:()=>{}};
    assert.equal(vm.runInNewContext(extract('savedMedalState')+`;savedMedalState('${slug}','hard')`,context),expected);
    const scanned = vm.runInNewContext(extract('loadMedalsFromProfileSave')+';loadMedalsFromProfileSave({})',context);
    assert.ok(scanned.has(mapNames.normalize(catalogs[slug].name)));
  }
}
const html=fs.readFileSync('index.html','utf8');
assert.ok(html.indexOf('data/catalogs/map-names.js')<html.indexOf('assets/app/app.js'));
const ui=fs.readFileSync('assets/app/app.js','utf8');
assert.match(ui,/const mapProgressKey = BloonsMapNames\.normalize;/);
assert.match(source,/const normalizeMapName = mapNamesContract\.normalize;/);
const poolStart=source.indexOf('  const configuredMaps =');
const poolEnd=source.indexOf('  const savedCompleted =',poolStart);
const config={unlocked_maps:{town_center:true,sw_esalping_run:true}};
const logs=[];
const pool=vm.runInNewContext(source.slice(poolStart,poolEnd)+';allMaps',{
  cfg:config,combos:{three_mines_round:{},wy_a:{}},mapNames:catalogs,job:{},pushLog:(_,line)=>logs.push(line),
});
assert.deepEqual(Array.from(pool),['three_mines_round','town_center']);
assert.equal(config.unlocked_maps.sw_esalping_run,true,'Ignore legacy OCR IDs without deleting saved data');
assert.match(logs[0],/2 unknown map ID/);
console.log('Exact map-save aliases: owned/missing/unknown medals, sweep pool and browser parity pass.');
