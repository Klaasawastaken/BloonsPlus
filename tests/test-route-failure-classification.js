const assert = require('node:assert/strict');
const { classifyRouteFailure, stateMatchesAttempt } = require('../lib/automation');

const startedAt = Date.parse('2026-10-05T09:00:00.500Z');
const endedAt = startedAt + 60_000;
const state = { map: 'skates', mode: 'chimps', startedAt: '2026-10-05T09:00:01Z' };
const matches = candidate => stateMatchesAttempt(candidate, 'skates', 'chimps', startedAt, endedAt);
assert.equal(matches(state), true);
assert.equal(matches({ ...state, mode: 'hard' }), false);
assert.equal(matches({ ...state, map: 'logs' }), false);
assert.equal(matches({ ...state, startedAt: '2026-10-04T09:00:01Z' }), false);
assert.equal(matches({ ...state, startedAt: '2026-10-06T09:00:01Z' }), false);
assert.equal(matches({ ...state, startedAt: undefined }), false);
assert.equal(matches(null), false);
// Python timestamps have whole-second precision.
assert.equal(matches({ ...state, startedAt: '2026-10-05T09:00:00Z' }), true);

const base = { lastRound: 24, finalRound: 80, sameRun: true, log: [] };
assert.equal(classifyRouteFailure(base), 'unconfirmed-outcome');
assert.equal(classifyRouteFailure({ ...base, defeatObserved: true }), 'gameplay-defeat');
assert.equal(classifyRouteFailure({ ...base, interrupted: true, log: ['screen DEFEAT!'] }), 'interrupted');
assert.equal(classifyRouteFailure({ ...base, interrupted: true, defeatObserved: true }), 'gameplay-defeat');
assert.equal(classifyRouteFailure({ ...base, sameRun: false, lastRound: null }), 'insufficient-data');
assert.equal(classifyRouteFailure({ ...base, log: ['ERROR hero selection was not confirmed'] }), 'navigation-bug');
assert.equal(classifyRouteFailure({ ...base, reason:'exit', sameRun:false, lastRound:null,
  defeatObserved:false, log:['ERROR hero obyn_greenfoot was not found in the picker'] }), 'navigation-bug');
assert.equal(classifyRouteFailure({ ...base, reason:'exit', sameRun:false, lastRound:null,
  defeatObserved:false, log:['DEBUG hero obyn_greenfoot found visually on page 0'] }), 'insufficient-data');
assert.equal(classifyRouteFailure({ ...base, log: ['RECOVERY upgrade_unconfirmed tower=heli1'] }), 'upgrade-unconfirmed');
assert.equal(classifyRouteFailure({ ...base, log: ['ERROR place of hero failed'] }), 'placement-bug');
for (const reason of ['game-unavailable', 'invalid-window', 'spawn-error', 'stop-failed']) {
  assert.equal(classifyRouteFailure({ ...base, reason, sameRun:false, lastRound:null }), 'technical-failure');
}
for (const line of ['BTD6 could not be focused', 'stopping before map click', 'map page is not visible', 'map tile did not open']) {
  assert.equal(classifyRouteFailure({ ...base, reason:'exit', sameRun:false, lastRound:null, log:[line] }), 'navigation-bug');
}
assert.equal(classifyRouteFailure({ ...base, log:['Traceback (most recent call last)'], sameRun:false, lastRound:null }), 'technical-failure');
assert.equal(classifyRouteFailure({ ...base, defeatObserved:true, log:['screen INGAME!', 'screen STARTMENU!'] }), 'gameplay-defeat', 'Ordinary screen transitions are not navigation failures');
console.log('Route failure classification checks passed.');

const { unresolvedUpgradeCount } = require('../lib/upgrade-failures');
const ambiguous = { type: 'upgrade', tower: 'heli1', path: 0, status: 'cash-ambiguous',
  upgradeObservation: { before: [3, 0, 2] } };
const confirmed = { type: 'upgrade', tower: 'heli1', path: 0, status: 'panel-tier-confirmed', upgradeLevel: 4 };
assert.equal(unresolvedUpgradeCount([ambiguous]), 1);
assert.equal(unresolvedUpgradeCount([ambiguous, confirmed]), 0);
assert.equal(unresolvedUpgradeCount([confirmed, ambiguous]), 1);
assert.equal(unresolvedUpgradeCount([ambiguous, { ...confirmed, upgradeLevel: 3 }]), 1);
assert.equal(unresolvedUpgradeCount([ambiguous, { ...confirmed, tower: 'heli0' }]), 1);
assert.equal(unresolvedUpgradeCount([ambiguous, { ...confirmed, path: 2 }]), 1);
assert.equal(unresolvedUpgradeCount([ambiguous, { ...confirmed, status: 'cash-confirmed' }]), 1);
assert.equal(unresolvedUpgradeCount([{ ...ambiguous, upgradeObservation: {} }, confirmed]), 1);
assert.equal(unresolvedUpgradeCount([{ ...ambiguous, upgradeObservation: {}, expectedUpgradeTiers: [4, 0, 2] }, confirmed]), 0);
assert.equal(unresolvedUpgradeCount([]), null);
assert.equal(classifyRouteFailure({ ...base, defeatObserved: true, unresolvedUpgrades: 0,
  log: ['RECOVERY upgrade_unconfirmed tower=heli1'] }), 'gameplay-defeat');
assert.equal(classifyRouteFailure({ ...base, defeatObserved: true, unresolvedUpgrades: 1,
  log: ['RECOVERY upgrade_unconfirmed tower=heli1'] }), 'upgrade-unconfirmed');

assert.equal(unresolvedUpgradeCount([ambiguous, { type: 'sell', tower: 'heli1' }, confirmed]), 1);
assert.equal(unresolvedUpgradeCount([ambiguous, { type: 'place', tower: 'heli1' }, confirmed]), 1);
assert.equal(unresolvedUpgradeCount([ambiguous, { ...confirmed, upgradeLevel: 779 }]), 1);

// A replacement can have its own ambiguous purchase followed by confirmation.
// That confirms only the replacement, never the retired tower's purchase.
for (const boundary of ['sell', 'place']) {
  assert.equal(unresolvedUpgradeCount([
    ambiguous, { type: boundary, tower: 'heli1' }, ambiguous,
  ]), 2, `${boundary}: old and replacement purchases are separate uncertainties`);
  assert.equal(unresolvedUpgradeCount([
    ambiguous, { type: boundary, tower: 'heli1' }, ambiguous, confirmed,
  ]), 1, `${boundary}: replacement confirmation must preserve the old ambiguity`);
}
assert.equal(unresolvedUpgradeCount([
  ambiguous, { type: 'sell', tower: 'heli1' }, { type: 'place', tower: 'heli1' },
  ambiguous, { type: 'sell', tower: 'heli1' }, { type: 'place', tower: 'heli1' },
  ambiguous, confirmed,
]), 2, 'Each retired instance retains its own unresolved purchase');
assert.equal(unresolvedUpgradeCount([
  ambiguous, { ...ambiguous, path: 2, expectedUpgradeTiers: [3, 0, 3] },
  { type: 'sell', tower: 'heli1' }, ambiguous, confirmed,
]), 2, 'Distinct unresolved paths survive replacement');
