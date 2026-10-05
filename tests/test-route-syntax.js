const assert = require('node:assert/strict');
const { validateRoute } = require('../lib/route-validation');
const catalog = { monkeys: { dart: { type: 'primary' } }, heros: {} };
for (const bad of ['upgrdae dart0 path 0', 'place dart dart0 at 10, 20 nonsense',
  'upgrade dart0 path 3', 'ability 11', 'click map at x, y']) {
  assert.ok(validateRoute(bad, 'hard', catalog).some(e => /Unsupported|Malformed/.test(e.message)), bad);
}
for (const good of ['round 10', 'speed fast', 'cash 2000', 'ability 10 after 1.5 seconds at 20, 30 move after 0.2 seconds',
  'click map at 20, 30', 'remove obstacle at 20, 30 for 500',
  'place dart dart0 at 10, 20 with 10% discount\nupgrade dart0 path 0 for 100']) {
  assert.deepEqual(validateRoute(good, 'hard', catalog), [], good);
}
console.log('Strict route syntax checks passed.');
