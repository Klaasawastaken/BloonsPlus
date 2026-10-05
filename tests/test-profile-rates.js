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
console.log('Profile rate freshness checks passed.');
