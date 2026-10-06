const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const decoder=require('../data/catalogs/medal-progress');
assert.equal(require('../lib/btd6-save-progress').medalsFromMapRecord,decoder.medalsFromMapRecord);
const browser={};vm.runInNewContext(fs.readFileSync('data/catalogs/medal-progress.js','utf8'),browser);
const modes={Easy:['Standard','PrimaryOnly','Deflation'],Medium:['Standard','MilitaryOnly','Reverse','Apopalypse'],Hard:['Standard','MagicOnly','DoubleMoabHealth','HalfCash','AlternateBloonsRounds','Impoppable','Clicks']};
for(const [difficulty,names] of Object.entries(modes)) for(const mode of names) {
 for(const value of [0,2,784,1049545,true,false,null,-1,0.5,'1049545',{}, {completed:true},{completed:false},{completed:'yes'}]) {
  const record={difficult:{[difficulty]:{modes:{[mode]:value}}}};
  const before=JSON.stringify(record);
  assert.deepEqual(JSON.parse(JSON.stringify(browser.BloonsMedals.medalsFromMapRecord(record))),decoder.medalsFromMapRecord(record));
  assert.equal(JSON.stringify(record),before);
 }
}
const html=fs.readFileSync('index.html','utf8');
assert.ok(html.indexOf('data/catalogs/medal-progress.js')<html.indexOf('assets/app/app.js'));
console.log('One shared decoder: browser/server parity for all 14 modes and 14 value schemas; input unchanged.');
