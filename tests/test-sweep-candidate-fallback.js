const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

// Exercise the production selection block without starting a game.
const source = fs.readFileSync(require.resolve('../lib/automation'), 'utf8');
const block = source.slice(source.indexOf('      const candidatesToTry ='), source.indexOf('      if (!entry) {', source.indexOf('      const candidatesToTry =')));
const ready = { filename: 'ready', profileReadiness: { missing: 0, unknown: 0 } };
const unknown = { filename: 'unknown', profileReadiness: { missing: 0, unknown: 1 } };
function select(attempted, allowed) {
  return vm.runInNewContext(block + '\nentry?.filename', {
    profileReadyEntries: [ready], profileEligibleEntries: [ready, unknown],
    attemptedFiles: new Set(attempted), triedForMode: {},
    canAttempt: (_, hash) => allowed.includes(hash), routeAttemptHash: file => file,
  });
}
assert.equal(select([], ['ready', 'unknown']), 'ready');
assert.equal(select(['ready'], ['ready', 'unknown']), 'unknown', 'Try eligible unknown prerequisites after ready routes are exhausted');
assert.equal(select([], ['unknown']), 'unknown', 'Historical attempt limits must also allow fallback');
assert.equal(select(['ready', 'unknown'], ['ready', 'unknown']), undefined);
console.log('Sweep candidate fallback checks passed.');
