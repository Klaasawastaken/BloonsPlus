const assert = require('node:assert/strict');
const { createReplayMonitor } = require('../lib/replay-monitor');
let time = 0;
const monitor = createReplayMonitor({ now: () => time });
monitor.observe('screen INGAME!');
monitor.observe('DEBUG OCR values money=650 round=6');
monitor.observe('DEBUG OCR values money=650 round=6');
time = 1000;
monitor.setPaused(true);
time += 20 * 60_000;
assert.equal(monitor.stalled(), null, 'User pause must not kill the replay');
monitor.setPaused(false);
assert.equal(monitor.stalled(), null, 'Resume must preserve remaining active-time budget');
time += 480_000;
assert.match(monitor.stalled(), /no confirmed progress/);
console.log('Replay pause timer checks passed.');

time = 0;
const active = createReplayMonitor({ now: () => time, roundStallMs: 1000 });
active.observe('screen INGAME!');
active.observe('DEBUG OCR values money=100 round=44');
active.observe('DEBUG OCR values money=100 round=44');
for (const cash of [105, 110, 120]) {
  time += 400;
  active.observe(`DEBUG OCR values money=${cash} round=-1`);
}
assert.equal(active.stalled(), null, 'Sustained income is activity despite unreadable round');
time += 1001;
assert.match(active.stalled(), /no confirmed progress/, 'Frozen money still times out');

time = 0;
const noise = createReplayMonitor({ now: () => time, roundStallMs: 1000 });
noise.observe('screen INGAME!');
for (const cash of [100, 110, 100, 110, 100, 110]) {
  time += 200;
  noise.observe(`DEBUG OCR values money=${cash} round=-1`);
}
assert.match(noise.stalled(), /no confirmed progress/, 'Oscillating money is not sustained income');

time = 0;
const bounded = createReplayMonitor({ now: () => time, roundStallMs: 1000, maxRunMs: 1100 });
bounded.observe('screen INGAME!');
for (const cash of [100, 105, 110, 120]) {
  time += 300;
  bounded.observe(`DEBUG OCR values money=${cash} round=-1`);
}
assert.match(bounded.stalled(), /maximum route duration/, 'Activity cannot bypass the overall limit');
