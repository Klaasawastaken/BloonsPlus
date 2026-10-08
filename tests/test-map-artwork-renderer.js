const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'bloons-map-artwork-test-'));
const env = { ...process.env, BLOONS_RENDERER_TEST_PROFILE: profile };
delete env.ELECTRON_RUN_AS_NODE;
try {
  const run = spawnSync(require('electron'), [path.join(__dirname, 'fixtures/map-artwork-renderer.cjs')], {
    cwd: path.resolve(__dirname, '..'), env, encoding: 'utf8', timeout: 60000, windowsHide: true,
  });
  assert.ifError(run.error);
  assert.equal(run.status, 0, run.stdout + run.stderr);
  const result = JSON.parse(run.stdout.trim().split(/\r?\n/).at(-1));
  assert.equal(result.checks, 48);
  assert.deepEqual(result.failures, []);
  assert.deepEqual(result.errors, []);
  console.log('Map artwork: 48 actual renderer checks pass for scrolling, labels, filters, save refresh, observer cleanup and eager fallback in both themes.');
} finally {
  // Remove only the exact temporary profile created above, after Electron exits.
  assert.equal(path.dirname(path.resolve(profile)), path.resolve(os.tmpdir()));
  assert.ok(path.basename(profile).startsWith('bloons-map-artwork-test-'));
  fs.rmSync(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
}
