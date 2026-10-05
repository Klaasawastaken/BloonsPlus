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
