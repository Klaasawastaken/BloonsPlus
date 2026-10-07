const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'bloons-site-test-'));
const env = { ...process.env, BLOONS_RENDERER_TEST_PROFILE: profile };
delete env.ELECTRON_RUN_AS_NODE;
try {
  const run = spawnSync(require('electron'), [path.join(__dirname, 'fixtures/site-accessibility-renderer.cjs')], {
    cwd: path.resolve(__dirname, '..'), env, encoding: 'utf8', timeout: 60000, windowsHide: true,
  });
  assert.ifError(run.error);
  assert.equal(run.status, 0, run.stdout + run.stderr);
  const result = JSON.parse(run.stdout.trim().split(/\r?\n/).at(-1));
  assert.equal(result.pages, 12);
  assert.equal(result.contrasts, 60);
  assert.deepEqual(result.failures, []);
  assert.deepEqual(result.errors, []);
  console.log('Website: 12 rendered page cases, 60 secondary-text contrasts, mobile Escape focus and keyboard table scrolling pass.');
} finally {
  assert.equal(path.dirname(path.resolve(profile)), path.resolve(os.tmpdir()));
  assert.ok(path.basename(profile).startsWith('bloons-site-test-'));
  fs.rmSync(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
}
