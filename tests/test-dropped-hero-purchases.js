const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { validateRoute } = require('../lib/route-validation');
const catalog = require('../autobtd6/towers.json');
const header = '# dropped (timing only): hero level purchases (AutoBTD6 levels heroes by XP only)';
const action = 'place sauda hero0 at 821, 540';
assert.match(validateRoute(`${header}\n${action}`, 'chimps', catalog)[0].message, /paid hero levels/);
assert.deepEqual(validateRoute(`# normal hero level purchases explanation\n${action}`, 'chimps', catalog), []);
assert.deepEqual(validateRoute(`# dropped (timing only): speed toggle\n${action}`, 'chimps', catalog), []);
const directory = path.join(__dirname, '../autobtd6/playthroughs');
let affected = 0;
for (const name of fs.readdirSync(directory).filter(name => name.endsWith('.btd6'))) {
  const text = fs.readFileSync(path.join(directory, name), 'utf8');
  if (!text.includes(header)) continue;
  affected++;
  assert.ok(validateRoute(text, name.split('#')[1], catalog)
    .some(error => /paid hero levels/.test(error.message)), name);
}
assert.ok(affected > 0, 'Exercise real legacy conversions as well as synthetic input');
console.log(`Dropped hero purchase checks passed (${affected} existing conversions, no route files changed).`);
