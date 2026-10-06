const assert = require('node:assert/strict');
const { validateRoute } = require('../lib/route-validation');
const catalog = { monkeys: { dartling: { type: 'military' } }, heros: {} };
const text = 'place dartling gun at 100, 200\nspecial gun to 600, 700 at 300, 400\n';
assert.deepEqual(validateRoute(text, 'hard', catalog), []);
assert.ok(validateRoute(text.replace('600, 700', '600'), 'hard', catalog).length);
assert.ok(validateRoute('special missing to 600, 700\n', 'hard', catalog).length);
console.log('Targeted special route grammar checks passed');
