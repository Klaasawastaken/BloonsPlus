const saveUpgradeNames = require('../data/catalogs/save-upgrade-names');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync('lib/automation.js', 'utf8');
const reqSource = source.slice(source.indexOf('function routeRequirements('), source.indexOf('\nfunction getRecordedCombos('));
const rankSource = source.slice(source.indexOf('function rankCandidatesForProfile('), source.indexOf('\nfunction restoreAttemptsLostToNavigation('));
const requirements = vm.runInNewContext(reqSource + ';routeRequirements');
assert.equal(requirements('change speed', {}, {}).roundStart, true, 'Relative speed requires Play/Fast Forward');
const {validateRoute} = require('../lib/route-validation');
const controlCatalog = {monkeys:{},heros:{}};
assert.deepEqual(validateRoute('change speed', 'hard', controlCatalog), []);
assert.ok(validateRoute('change speed turbo', 'hard', controlCatalog).length);
assert.deepEqual(validateRoute('move cursor to 20, 30', 'hard', controlCatalog), []);
for (const line of ['move cursor to -20, 30', 'move cursor to 20, 30 click', 'move cursor to 20']) assert.ok(validateRoute(line, 'hard', controlCatalog).length);
const req = requirements('ability 10 at 20, 30\nrepeat ability 3\nability 3 after 1 seconds\nstop ability 4\nstop all abilities\n# ability 1', {}, {});
assert.deepEqual(Array.from(req.abilities), [3, 10]);
assert.deepEqual(Array.from(requirements('stop ability 1', {}, {}).abilities), []);
function rank(gameplay, abilities = [3, 10], roundStart = false) {
  const profile = { available: true, gameHotkeys: { gameplay } };
  const fn = vm.runInNewContext(rankSource + ';rankCandidatesForProfile', {
    saveUpgradeNames, readLocalProgress: () => profile, fs: { readFileSync: () => '{}' }, path, PROJECT_ROOT: '.',
  });
  return fn([{ requirements: { towers: {}, abilities, roundStart } }, { requirements: { towers: {} } }]);
}
for (const binding of ['<Keyboard>/3', '<Keyboard>/F3', '<Keyboard>/PageDown', '<Keyboard>/Numpad3']) {
  const entries = rank({ 'Activated Ability 3': { path: binding }, 'Activated Ability 10': { path: '<Keyboard>/0' } });
  assert.equal(entries[0].profileReadiness.missing, 0);
}
for (const gameplay of [undefined, {}]) assert.equal(rank(gameplay)[0].profileReadiness.missing, 0, 'absent section retains replay defaults');
for (const binding of ['', '<Keyboard>/Escape', '<Mouse>/leftButton']) {
  const entries = rank({ 'Activated Ability 3': { path: binding }, 'Activated Ability 10': { path: '<Keyboard>/0' } });
  assert.equal(entries[0].requirements.abilities, undefined, 'compatible candidate is ranked first');
  const blocked = entries.find(entry => entry.requirements.abilities);
  assert.equal(blocked.profileReadiness.missingAbilityBindings, 1);
  assert.equal(blocked.profileReadiness.missing, 1);
  assert.match(blocked.profileReadiness.abilityIssues[0], /Ability 3/);
}
const absent = rank({ PlayFastForward: { path: '<Keyboard>/Space' } }).find(entry => entry.requirements.abilities);
assert.equal(absent.profileReadiness.missingAbilityBindings, 2);
assert.equal(rank({ PlayFastForward: { path: '<Keyboard>/Space' } }, [])[0].profileReadiness.missing, 0, 'unused slots do not block');
console.log('Ability prerequisites: commands, saved bindings, defaults, unsupported keys and alternatives pass');

const parseSource = source.slice(source.indexOf('function parsePlaythroughFile('), source.indexOf('\nfunction listPlaythroughs('));
const parse = vm.runInNewContext(parseSource + ';parsePlaythroughFile');
assert.ok(parse('glacial_trail#easy#1920x1080#converted#source_bloonsplayer#ability-preserved.btd6').flags.includes('lossy'), 'stale installed inferred-wait candidate remains a draft');
assert.ok(parse('glacial_trail#easy#1920x1080#converted#source_bloonsplayer#ability-preserved#lossy.btd6').flags.includes('lossy'));
assert.ok(!parse('glacial_trail#chimps#1920x1080.btd6').flags.includes('lossy'), 'original recordings retain their flags');

assert.equal(requirements('start round slow', {}, {}).roundStart, true);
const controlMissing = rank({ PlayFastForward: { path: '' } }, [], true).find(entry => entry.requirements.roundStart);
assert.equal(controlMissing.profileReadiness.missingControlBindings, 1);
assert.match(controlMissing.profileReadiness.controlIssues[0], /Play\/Fast Forward/);
assert.equal(rank({ PlayFastForward: { path: '<Keyboard>/Space' } }, [], true)[0].profileReadiness.missing, 0);

// Only upgrade paths actually required by the candidate affect readiness.
function rankPaths(monkeys, towers, hero = null) {
  const fn = vm.runInNewContext(rankSource + ';rankCandidatesForProfile', {
    saveUpgradeNames, readLocalProgress: () => ({ available: true, gameHotkeys: { monkeys: monkeys && Object.keys(monkeys).length ? { NinjaMonkey: { path: '<Keyboard>/n' }, ...monkeys } : monkeys } }),
    fs: { readFileSync: () => '{}' }, path, PROJECT_ROOT: '.',
  });
  return fn([{ requirements: { towers, hero } }])[0].profileReadiness;
}
for (const binding of ['', '<Keyboard>/Escape', '<Mouse>/leftButton']) {
  const readiness = rankPaths({ 'Upgrade Path 1': { path: binding } }, { ninja: [1, 0, 0] });
  assert.equal(readiness.missingControlBindings, 1);
  assert.match(readiness.controlIssues[0], /Upgrade Path 1/);
}
assert.equal(rankPaths({ 'Upgrade Path 1': { path: '<Keyboard>/1' } }, { ninja: [2, 0, 0] }).missingControlBindings, 0);
assert.equal(rankPaths({ 'Upgrade Path 1': { path: '' } }, { ninja: [0, 0, 0] }).missingControlBindings, 0);
assert.equal(rankPaths({}, { ninja: [5, 5, 5] }).missingControlBindings, 0, 'absent section retains legacy defaults');

assert.equal(rankPaths({ NinjaMonkey: { path: '' } }, { ninja: [0, 0, 0] }).missingControlBindings, 1);
assert.equal(rankPaths({ NinjaMonkey: { path: '<Mouse>/leftButton' } }, { ninja: [0, 0, 0] }).missingControlBindings, 1);
const heroBlocked = rankPaths({ Heroes: { path: '' } }, {}, 'sauda');
assert.equal(heroBlocked.missingControlBindings, 1);
assert.match(heroBlocked.controlIssues[0], /Hero placement/);
assert.equal(rankPaths({ Heroes: { path: '<Keyboard>/u' } }, {}, 'sauda').missingControlBindings, 0);
