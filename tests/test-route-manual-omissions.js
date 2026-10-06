const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { validateRoute } = require('../lib/route-validation');
const catalog = JSON.parse(fs.readFileSync('autobtd6/towers.json', 'utf8'));
const body = 'place dart dart0 at 100, 200\n';
for (const command of ['change_autostart()', 'end_round()', 'end_round(10)']) {
  const errors = validateRoute('# dropped (timing only): '+command+'\n'+body, 'hard', catalog);
  assert.ok(errors.some(item => /manual-round controls/.test(item.message)), command);
}
assert.deepEqual(validateRoute('# source used end_round(), fully preserved by recording\n'+body, 'hard', catalog), []);
const filename = 'midnight_mansion#chimps#1920x1080#converted#source_btd6bot.btd6';
const errors = validateRoute(fs.readFileSync(path.join('autobtd6/playthroughs', filename),'utf8'), 'chimps', catalog);
assert.ok(errors.some(item => /manual-round controls/.test(item.message)), 'missing lossy filename flag must not bypass content validation');
console.log('Declared manual-round omissions rejected, ordinary comments retained');
