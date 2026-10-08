const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'bloons-report-test-'));
const env = { ...process.env, BLOONS_RENDERER_TEST_PROFILE: profile };
delete env.ELECTRON_RUN_AS_NODE;
try {
  const run = spawnSync(require('electron'), [path.join(__dirname, 'fixtures/report-renderer.cjs')], {
    cwd: path.resolve(__dirname, '..'), env, encoding: 'utf8', timeout: 60000, windowsHide: true,
  });
  assert.ifError(run.error);
  assert.equal(run.status, 0, run.stdout + run.stderr);
  const result = JSON.parse(run.stdout.trim().split(/\r?\n/).at(-1));
  assert.equal(result.checks, 88);
  assert.deepEqual(result.failures, []);
  assert.deepEqual(result.errors, []);
  const negative = spawnSync(require('electron'), [path.join(__dirname, 'fixtures/report-renderer.cjs')], {
    cwd: path.resolve(__dirname, '..'), env: { ...env, BLOONS_REPORT_NEGATIVE: '1' },
    encoding: 'utf8', timeout: 60000, windowsHide: true,
  });
  assert.ifError(negative.error);
  assert.equal(negative.status, 1, 'Non-modal negative control must fail');
  assert.ok(negative.stdout.trim(), negative.stderr || 'Negative control returned no report');
  const rejected = JSON.parse(negative.stdout.trim().split(/\r?\n/).at(-1));
  assert.equal(rejected.checks, 88);
  assert.equal(rejected.failures.filter(f => f.kind === 'open-modal-focus').length, 8);
  assert.equal(rejected.failures.filter(f => f.kind === 'background-focus-blocked').length, 8);
  assert.deepEqual(rejected.errors, []);
  console.log('Issue report: 88 checks pass for observed version, keyboard focus, bounds, accessible names, redacted context and dismissal in both themes and entry points.');
} finally {
  // Remove only the exact temporary profile created above, after Electron exits.
  assert.equal(path.dirname(path.resolve(profile)), path.resolve(os.tmpdir()));
  assert.ok(path.basename(profile).startsWith('bloons-report-test-'));
  fs.rmSync(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
}
