const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync('lib/automation.js', 'utf8');
const reqSource = source.slice(source.indexOf('function routeRequirements('), source.indexOf('\nfunction getRecordedCombos('));
const rankSource = source.slice(source.indexOf('function rankCandidatesForProfile('), source.indexOf('\nfunction restoreAttemptsLostToNavigation('));
const requirements = vm.runInNewContext(reqSource + ';routeRequirements');
const req = requirements('ability 10 at 20, 30\nrepeat ability 3\nability 3 after 1 seconds\nstop ability 4\nstop all abilities\n# ability 1', {}, {});
assert.deepEqual(Array.from(req.abilities), [3, 10]);
assert.deepEqual(Array.from(requirements('stop ability 1', {}, {}).abilities), []);
function rank(gameplay, abilities = [3, 10]) {
  const profile = { available: true, gameHotkeys: { gameplay } };
  const fn = vm.runInNewContext(rankSource + ';rankCandidatesForProfile', {
    readLocalProgress: () => profile, fs: { readFileSync: () => '{}' }, path, PROJECT_ROOT: '.',
  });
  return fn([{ requirements: { towers: {}, abilities } }, { requirements: { towers: {} } }]);
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
