const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'bloons-site-test-'));
const env = { ...process.env, BLOONS_RENDERER_TEST_PROFILE: profile };
delete env.ELECTRON_RUN_AS_NODE;
try {
  const run = spawnSync(require('electron'), [path.join(__dirname, 'fixtures/site-textscale-renderer.cjs')], {
    cwd: path.resolve(__dirname, '..'), env, encoding: 'utf8', timeout: 90000, windowsHide: true,
  });
  assert.ifError(run.error);
  assert.equal(run.status, 0, run.stdout + run.stderr);
  const result = JSON.parse(run.stdout.trim().split(/\r?\n/).at(-1));
  assert.equal(result.contentPages, 17);
  assert.equal(result.pages, 68);
  assert.deepEqual(result.failures, []);
  assert.deepEqual(result.errors, []);
  console.log('Website: all 17 content pages in both themes at 1280/390 px preserve document and heading bounds with doubled text sizes (68 cases).');
} finally {
  assert.equal(path.dirname(path.resolve(profile)), path.resolve(os.tmpdir()));
  assert.ok(path.basename(profile).startsWith('bloons-site-test-'));
  fs.rmSync(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
}
