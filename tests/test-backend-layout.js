const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');

(async () => {
  // Evaluate the same code at its previous root location, preserving its old
  // __dirname semantics, and compare the actual catalog from the new location.
  const old = new Module(path.join(root, 'automation.js'));
  old.filename = path.join(root, 'automation.js');
  old.paths = Module._nodeModulePaths(root);
  const backendRequire = Module.createRequire(path.join(root, 'lib', 'automation.js'));
  old.require = backendRequire;
  const source = fs.readFileSync(path.join(root, 'lib', 'automation.js'), 'utf8')
    .replace(/^const PROJECT_ROOT = .*?;\r?\n/, '')
    .replace(/PROJECT_ROOT/g, '__dirname');
  old._compile(source, old.filename);
  const expected = await old.exports.getAvailableCombos();
  const actual = await require('../lib/automation').getAvailableCombos();
  assert.equal(JSON.stringify(actual), JSON.stringify(expected), 'Route selection changed during the move');
  assert.ok(Object.keys(actual).length > 70, 'Catalog unexpectedly empty');
  const { strategySignature: signature } = require('../lib/route-validation');
  assert.equal(signature('place dart a at 1, 2\nupgrade a path 0'), signature('# alias\nplace dart z at 1,2\nupgrade z path 0'));
  assert.notEqual(signature('place dart a at 1,2'), signature('place dart a at 2,2'));
  console.log(`Backend layout and strategy identity passed; ${Object.keys(actual).length} maps preserved.`);
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
