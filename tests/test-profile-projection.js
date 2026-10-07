const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { medalsFromMapRecord } = require('../data/catalogs/medal-progress');
const source = fs.readFileSync(require.resolve('../assets/app/app.js'), 'utf8');
const code = source.slice(source.indexOf('let lastReadableLocalProfile'), source.indexOf('// Both progress pollers'));
assert.ok(code.includes('function applyLocalSaveProgress'), 'Readable profile projection must be present');
const calls = [];
const initial = () => ({maps:{Example:{medals:{hard:true},blackBorder:true,status:'completed',art:'keep'}},
  towers:{'Dart Monkey':{xp:9},'Sniper Monkey':{xp:88,art:'keep'}},player:{monkeyMoney:100},heroes:{unlocked:['Sauda']}});
const context = vm.createContext({detectedProgress:initial(), TOWER_NAMES:{dart:'Dart Monkey',sniper:'Sniper Monkey'},
  MEDAL_SLOTS:[['easy'],['hard']], medalsFromLocalRecord:medalsFromMapRecord,
  observeProfileRates:()=>{},renderProfileUnlocks:()=>calls.push('unlocks'),render:()=>calls.push('render'),renderSpecificMapRequirements:()=>calls.push('requirements')});
vm.runInContext(code,context);
const record = mode => ({difficult:{Easy:{modes:{Standard:mode}},Hard:{modes:{Standard:mode}}}});
const a={available:true,source:'btd6-profile-save',file:'shared',accountIdentity:'a',mapProgress:{Example:record(true)},towerXp:{DartMonkey:23,SniperMonkey:40},heroes:{unlocked:['Sauda']},monkeyMoney:100};
const b={...a,accountIdentity:'b',mapProgress:{Logs:record(false)},towerXp:{DartMonkey:7},heroes:{unlocked:['Quincy']},monkeyMoney:10};
context.applyLocalSaveProgress(a);
assert.equal(context.detectedProgress.maps.example.medals.hard,true);
context.markVmSaveUnavailable();
assert.equal(context.detectedProgress.localProfile.available,false);
assert.equal(context.detectedProgress.maps.example.medals.hard,true,'Temporary disconnect preserves last known ownership');
assert.equal(context.detectedProgress.heroes.unlocked,undefined);
assert.deepEqual(calls.slice(-3),['unlocks','render','requirements']);
context.applyLocalSaveProgress(b);
assert.equal(context.detectedProgress.maps.example.medals,undefined);
assert.equal(context.detectedProgress.maps.Example.medals,undefined,'Visual aliases cannot retain another owner');
assert.equal(context.detectedProgress.maps.Example.status,undefined);
assert.equal(context.detectedProgress.maps.Example.art,'keep');
assert.equal(context.detectedProgress.towers['Sniper Monkey'].xp,undefined);
assert.equal(context.detectedProgress.towers['Sniper Monkey'].art,'keep');
assert.equal(context.detectedProgress.towers['Dart Monkey'].xp,7);
context.detectedProgress=initial(); // A later unscoped scanner snapshot cannot undo the source switch.
context.applyLocalSaveProgress(b);
assert.equal(context.detectedProgress.maps.Example.medals,undefined);
assert.equal(context.detectedProgress.towers['Sniper Monkey'].xp,undefined);
context.detectedProgress=initial();
context.markVmSaveUnavailable();
assert.equal(context.detectedProgress.maps.Example.medals,undefined,'Disconnected scanner cannot revive prior-account medals');
assert.equal(context.detectedProgress.towers['Sniper Monkey'].xp,undefined,'Disconnected scanner cannot revive prior-account XP');
assert.equal(context.detectedProgress.maps.logs.medals.easy,false);
context.applyLocalSaveProgress(a);
assert.equal(context.detectedProgress.maps.example.medals.hard,true);
assert.equal(context.detectedProgress.towers['Sniper Monkey'].xp,40);
console.log('Profile projection: account changes, late scans, disconnect ownership protection, redraw and reconnect pass.');
