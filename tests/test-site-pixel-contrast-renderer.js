const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'bloons-site-test-'));
const env = { ...process.env, BLOONS_RENDERER_TEST_PROFILE: profile };
delete env.ELECTRON_RUN_AS_NODE;
try {
  const run = spawnSync(require('electron'), [path.join(__dirname, 'fixtures/site-pixel-contrast-renderer.cjs')], {
    cwd: path.resolve(__dirname, '..'), env, encoding: 'utf8', timeout: 180000, windowsHide: true,
  });
  assert.ifError(run.error);
  assert.equal(run.status, 0, run.stdout + run.stderr);
  const result = JSON.parse(run.stdout.trim().split(/\r?\n/).at(-1));
  assert.equal(result.pages, 34);
  assert.ok(result.checks >= 2000, `Only ${result.checks} pixel contrast observations`);
  assert.deepEqual(result.failures, []);
  assert.deepEqual(result.errors, []);
  const negative = spawnSync(require('electron'), [path.join(__dirname, 'fixtures/site-pixel-contrast-renderer.cjs')], {
    cwd: path.resolve(__dirname, '..'), env: { ...env, BLOONS_CONTRAST_NEGATIVE_CONTROL: '1' },
    encoding: 'utf8', timeout: 30000, windowsHide: true,
  });
  assert.ifError(negative.error);
  assert.equal(negative.status, 0, negative.stdout + negative.stderr);
  const control = JSON.parse(negative.stdout.trim().split(/\r?\n/).at(-1));
  assert.ok(control.failures.some(item => item.text.startsWith('Explore the features') && item.ratio === 1),
    'Invisible foreground/background control was silently excluded');
  console.log(`Website: ${result.pages} page/theme cases and ${result.checks} rendered text contrast observations pass; invisible-text negative control is detected.`);
} finally {
  assert.equal(path.dirname(path.resolve(profile)), path.resolve(os.tmpdir()));
  assert.ok(path.basename(profile).startsWith('bloons-site-test-'));
  fs.rmSync(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
}
