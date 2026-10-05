const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { createReplayMonitor } = require('../lib/replay-monitor');
const monitor = createReplayMonitor();
monitor.observe('screen VICTORY!');
assert.equal(monitor.snapshot().victoryObserved, false, 'A stale victory menu before gameplay is not a new clear');
monitor.observe('screen INGAME!');
monitor.observe('screen VICTORY_SUMMARY!');
monitor.observe('screen STARTMENU!');
assert.equal(monitor.snapshot().victoryObserved, true, 'Victory evidence survives returning to the menu');

const source = fs.readFileSync(require.resolve('../lib/automation'), 'utf8');
const start = source.indexOf('function confirmClear(');
const end = source.indexOf('\n}\n', start) + 2;
function confirm(saved, result) {
  return vm.runInNewContext(source.slice(start, end) + '\nconfirmClear("map", "hard", result, () => {})', {
    result, savedMedalState: () => saved,
  });
}
assert.equal(confirm(true, {round:80}), false);
assert.equal(confirm(false, {victoryObserved:true, round:80}), false);
assert.equal(confirm(null, {victoryObserved:true}), false);
assert.equal(confirm(true, {victoryObserved:true, defeatObserved:true}), false);
assert.equal(confirm(true, {victoryObserved:true, round:null}), true, 'Save and victory evidence do not require reliable round OCR');
console.log('Victory and authoritative medal evidence checks passed.');
