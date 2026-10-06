const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require.resolve('../assets/app/app.js'), 'utf8');
function tracker() {
  const context = vm.createContext({});
  vm.runInContext(source.slice(source.indexOf('let profileRateSamples'), source.indexOf('let activeBossEvent')), context);
  return data => { context.data = data; return vm.runInContext('observeProfileRates(data); ({...profileRates})', context); };
}
const sample = (seconds, extra = {}) => ({readAt:new Date(1700000000000 + seconds * 1000).toISOString(), rank:155, veteranRank:1, veteranXp:100, xp:100, monkeyMoney:100, ...extra});
let observe = tracker();
observe(sample(0));
assert.equal(observe(sample(60, {monkeyMoney:200, veteranXp:200})).xpPerHour, 6000);
assert.equal(observe(sample(61, {veteranRank:2, veteranXp:20})).xpPerHour, null, 'Do not compare XP counters across veteran ranks');
observe = tracker();
observe(sample(0)); observe(sample(60, {monkeyMoney:200}));
assert.equal(observe(sample(61, {monkeyMoney:null})).monkeyMoneyPerHour, null, 'Missing money must clear stale rates');
assert.equal(observe(sample(1000)).monkeyMoneyPerHour, null, 'An expired window needs fresh samples');
observe = tracker();
observe(sample(0, {source:'btd6-profile-save',file:'account-a/Profile.Save'}));
observe(sample(60, {source:'btd6-profile-save',file:'account-a/Profile.Save',monkeyMoney:200}));
let changed = observe(sample(120, {source:'btd6-profile-save',file:'account-b/Profile.Save',monkeyMoney:50000,veteranXp:50000}));
assert.equal(changed.monkeyMoneyPerHour, null, 'Never compare balances across save sources');
assert.equal(changed.xpPerHour, null, 'Never compare XP across save sources');
assert.equal(observe(sample(180, {source:'btd6-profile-save',file:'account-b/Profile.Save',monkeyMoney:50100,veteranXp:50100})).monkeyMoneyPerHour, 6000);
observe = tracker();
observe(sample(100)); observe(sample(160, {monkeyMoney:200}));
assert.equal(observe(sample(90)).monkeyMoneyPerHour, null, 'A backward guest clock resets stale rates');
assert.equal(observe(sample(150, {monkeyMoney:200})).monkeyMoneyPerHour, 6000, 'New clock sequence can recover');
observe = tracker();
observe(sample(0, {monkeyMoney:500}));
assert.equal(observe(sample(60, {monkeyMoney:400})).monkeyMoneyPerHour, -6000, 'Spending is a negative net balance change, not zero earnings');
assert.equal(observe(sample(120, {monkeyMoney:-1})).monkeyMoneyPerHour, null, 'A negative saved balance is invalid');
observe = tracker();
observe(sample(0, {rank:130, veteranRank:0, xp:1000}));
assert.equal(observe(sample(60, {rank:131, veteranRank:0, xp:1600})).xpPerHour, 36000,
  'Ordinary rank changes must retain cumulative player XP');
assert.equal(observe(sample(120, {rank:131, veteranRank:0, xp:900})).xpPerHour, null,
  'A regressed XP counter must not create negative earnings');
observe = tracker();
observe(sample(0, {rank:154, veteranRank:0, xp:1000}));
assert.equal(observe(sample(60, {rank:155, veteranRank:0, xp:1600})).xpPerHour, null,
  'Entering the level cap must not compare an unverified veteran counter');
assert.equal(observe(sample(120, {rank:155, veteranRank:1, veteranXp:0})).xpPerHour, null,
  'The first veteran observation needs its own baseline');
assert.equal(observe(sample(180, {rank:155, veteranRank:1, veteranXp:600})).xpPerHour, 36000,
  'A fresh veteran baseline can recover after entering the level cap');
const format = vm.runInNewContext(source.match(/const formatRate = value => (.*);/)[0] + ';formatRate');
assert.equal(format(-6000), (-6000).toLocaleString(), 'Display signed net balance rates');
assert.equal(format(-0.1), '0', 'Do not display negative zero');
console.log('Profile rate freshness and signed balance checks passed.');
