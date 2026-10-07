const assert = require('node:assert/strict');
const fs = require('node:fs'), vm = require('node:vm'), path = require('node:path');
const saveUpgradeNames = require('../data/catalogs/save-upgrade-names');
const normal = value => String(value).toLowerCase().replace(/[^a-z0-9]/g, '');
for (const [tower, display, saved] of [
  ['ice', 'cold snap', 'Metal Freeze'], ['boomerang', 'bionic boomerang', 'Bionc Boomerang'],
  ['mortar', 'faster reload', 'Mortar Faster Reload'], ['mortar', 'rapid reload', 'Mortar Rapid Reload'],
  ['mortar', 'shell shock', 'Shockwave'], ['skywarden', 'storm pulse', 'StormsPulse'],
  ['alchemist', 'faster throwing', 'Alchemist Faster Throwing'], ['sniper', 'full auto riffle', 'Full Auto Rifle'],
  ['spike', 'smart spikes', 'Directed Spikes'], ['druid', 'monarch of storms', 'Superstorm'],
  ['wizard', 'prince of darkness', 'Soulbind'], ['engineer', 'sentry champion', 'Sentry Paragon'],
  ['buccaneer', 'grape shot', 'Buccaneer-Grape Shot'],
]) {
  assert.equal(saveUpgradeNames.owns(new Set([normal(saved)]), tower, display), true, tower);
  assert.equal(saveUpgradeNames.owns(new Set(), tower, display), false);
}
assert.equal(saveUpgradeNames.owns(new Set([normal('Metal Freeze')]), 'sniper', 'cold snap'), false);
assert.equal(saveUpgradeNames.owns(new Set([normal('Mortar Faster Reload')]), 'dartling', 'faster reload'), false);
assert.equal(saveUpgradeNames.owns(new Set([normal('Shockwave')]), 'dart', 'shell shock'), false);
assert.equal(saveUpgradeNames.owns(new Set([normal('StormsPulse')]), 'druid', 'storm pulse'), false);
assert.equal(saveUpgradeNames.owns(new Set([normal('Grape Shot')]), 'Monkey Buccaneer', 'grape shot'), true);
// The browser loads this same resolver before app.js.
const browser = {};
vm.runInNewContext(fs.readFileSync('data/catalogs/save-upgrade-names.js', 'utf8'), browser);
assert.equal(browser.SaveUpgradeNames.owns(new Set([normal('Metal Freeze')]), 'Ice Monkey', 'cold snap'), true);
assert.equal(browser.SaveUpgradeNames.owns(new Set([normal('Bionc Boomerang')]), 'Boomerang Monkey', 'bionic boomerang'), true);
assert.equal(browser.SaveUpgradeNames.owns(new Set([normal('Shockwave')]), 'Mortar Monkey', 'shell shock'), true);
assert.equal(browser.SaveUpgradeNames.owns(new Set([normal('StormsPulse')]), 'Skywarden', 'storm pulse'), true);
const html = fs.readFileSync('index.html', 'utf8');
assert.ok(html.indexOf('data/catalogs/save-upgrade-names.js') < html.indexOf('assets/app/app.js'));
const source = fs.readFileSync('lib/automation.js','utf8');
const rankSource = source.slice(source.indexOf('function rankCandidatesForProfile('),source.indexOf('\nfunction restoreAttemptsLostToNavigation('));
const rank = acquired => vm.runInNewContext(rankSource+';rankCandidatesForProfile', {
  saveUpgradeNames, fs, path, PROJECT_ROOT: process.cwd(),
  readLocalProgress: () => ({available:true, acquiredUpgrades:acquired}),
});
const entry = {requirements:{towers:{ice:[2,0,0]}}};
assert.equal(rank(['Permafrost','Metal Freeze'])([entry])[0].profileReadiness.missing,0);
assert.equal(rank(['Permafrost'])([entry])[0].profileReadiness.missing,1, 'a genuinely locked upgrade remains blocked');
console.log('Shared save upgrade names: aliases, qualification, tower scope, browser parity and route readiness pass');

const endStart = source.indexOf('  const finalStatus = job.stopRequested');
const endStop = source.indexOf('\n}', endStart);
assert.ok(endStart >= 0 && endStop > endStart, 'locate sweep ending without depending on line endings');
const endCode = source.slice(endStart, endStop);
for (const [stopped, incomplete, unscanned, expected] of [
  [false,0,0,'complete'], [false,1,0,'incomplete'], [false,0,1,'incomplete'],
  [true,1,1,'stopped'], [true,0,0,'stopped'],
]) {
  const saved = [], logs = [];
  const status = vm.runInNewContext(endCode+';finalStatus', {
    job:{stopRequested:stopped}, counts:{incompleteMaps:incomplete,confirmed:0,failedRoutes:0},
    unscanned:Array(unscanned).fill('unknown'), passName:'black border sweep',
    saveSweepProgressFor:state=>saved.push(state), pushLog:(_,line)=>logs.push(line),
  });
  assert.equal(status, expected);
  assert.equal(saved[0].status, expected);
  if (expected === 'incomplete') {
    assert.match(saved[0].reason,/Missing medals/);
    assert.match(logs[0],/pass finished with missing medals remaining/);
    assert.ok(!logs[0].includes('sweep complete'));
  }
}
