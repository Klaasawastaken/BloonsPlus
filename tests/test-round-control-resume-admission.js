// The explicit resume request may admit a stopped round-control receipt.
// Python still checks the receipt, route hash, scene, ledger and current round.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('lib/automation.js', 'utf8');
const start = source.indexOf("  if (type === 'resume') {", source.indexOf('function startFarm('));
const end = source.indexOf("  if (type === 'file') {", start);
assert.ok(start > 0 && end > start);
const admit = vm.runInNewContext(`(function(checkpoint) {
  const type = 'resume'; let file, gamemode;
  const loadRouteCheckpoint = () => checkpoint;
  ${source.slice(start, end)}
  return { file, gamemode };
})`);
const saved = { status: 'paused', filename: 'fixture.btd6', gamemode: 'impoppable',
  remainingSteps: [{ action: 'play_once', playOncePending: { from: 'fast', sentAt: 10, round: 13 } }] };
assert.equal(admit(saved).file, 'fixture.btd6');
assert.equal(admit(saved).gamemode, 'impoppable');
assert.ok(admit({ ...saved, remainingSteps: [{ action: 'upgrade' }] }).error);
assert.ok(admit({ ...saved, remainingSteps: [] }).error);
assert.ok(admit({ ...saved, status: 'victory' }).error);
assert.ok(admit({ ...saved, filename: null }).error);
assert.ok(admit(null).error);
assert.equal(admit({ ...saved, status: 'ready' }).file, 'fixture.btd6');
console.log('Explicit stopped round-control resume admission passes; purchases stay excluded.');
