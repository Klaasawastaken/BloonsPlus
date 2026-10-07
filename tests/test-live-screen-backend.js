const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const { execFile } = require('node:child_process');

// Exercise real file timestamps, lease writes and child-process completion.
// The capture child emits synthetic bytes; no Python/game capture is launched.
const source = fs.readFileSync(path.join(__dirname, '../lib/live-screen.js'), 'utf8');
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'bloons-viewer-backend-'));
const directory = path.join(root, 'autobtd6');
fs.mkdirSync(directory);
const controlFile = path.join(directory, 'fixture-control.json');
const frame = path.join(directory, 'live-frame.jpg');
const request = path.join(directory, 'viewer-request.json');
const child = path.join(directory, 'synthetic-capture.cjs');
fs.writeFileSync(child, `
const fs = require('node:fs');
const control = JSON.parse(fs.readFileSync('fixture-control.json', 'utf8'));
if (control.fail) process.exit(3);
setTimeout(() => process.stdout.write(Buffer.from(control.bytes)), 50);
`);

function backend() {
  const state = { now: Date.now(), captures: 0, available: true };
  const context = {
    __dirname: path.join(root, 'lib'), module: { exports: {} },
    Date: { now: () => state.now },
    require(name) {
      if (name === 'node:path') return path;
      if (name === 'node:fs') return fs;
      if (name === './automation') return {
        getRuntime: () => ({ available: state.available, executable: process.execPath }),
      };
      if (name === 'node:child_process') return {
        execFile(command, args, options, callback) {
          assert.equal(command, process.execPath);
          assert.deepEqual(Array.from(args), [path.join(directory, 'live_capture.py')]);
          assert.equal(options.cwd, directory);
          assert.equal(options.windowsHide, true);
          assert.equal(options.timeout, 8000);
          assert.equal(options.encoding, 'buffer');
          assert.equal(options.maxBuffer, 2 * 1024 * 1024);
          state.captures++;
          return execFile(command, [child], options, callback);
        },
      };
      throw new Error(`Unexpected dependency: ${name}`);
    },
  };
  vm.runInNewContext(source, context, { filename: 'lib/live-screen.js' });
  return { state, get: context.module.exports.getLiveScreen };
}

function setCapture(control) { fs.writeFileSync(controlFile, JSON.stringify(control)); }
function setFrame(now, age, bytes = 'synthetic-replay-frame') {
  fs.writeFileSync(frame, bytes);
  fs.utimesSync(frame, (now - age) / 1000, (now - age) / 1000);
}

(async () => {
  let cases = 0;
  const recent = backend();
  setFrame(recent.state.now, 500);
  assert.equal(String(await recent.get()), 'synthetic-replay-frame');
  assert.equal(recent.state.captures, 0);
  assert.equal(JSON.parse(fs.readFileSync(request)).expiresAt, recent.state.now + 10000);
  cases++;

  const lease = fs.readFileSync(request, 'utf8');
  recent.state.now += 999;
  await recent.get();
  assert.equal(fs.readFileSync(request, 'utf8'), lease, 'Cache reads must not extend the lease');
  recent.state.now += 1;
  await recent.get();
  assert.equal(JSON.parse(fs.readFileSync(request)).expiresAt, recent.state.now + 10000);
  cases++;

  fs.unlinkSync(frame);
  const concurrent = backend();
  setCapture({ bytes: 'synthetic-child-frame' });
  const frames = await Promise.all(Array.from({ length: 8 }, () => concurrent.get()));
  assert.equal(concurrent.state.captures, 1, 'Concurrent viewers share one capture process');
  assert.ok(frames.every(value => Buffer.isBuffer(value) && String(value) === 'synthetic-child-frame'));
  cases++;

  const retry = backend();
  setCapture({ fail: true });
  await assert.rejects(retry.get(), /Game screen unavailable/);
  setCapture({ bytes: 'recovered-frame' });
  assert.equal(String(await retry.get()), 'recovered-frame');
  assert.equal(retry.state.captures, 2, 'A failed child must release the pending request');
  cases++;

  const unavailable = backend();
  unavailable.state.available = false;
  await assert.rejects(unavailable.get(), /installed Python runtime/);
  unavailable.state.available = true;
  assert.equal(String(await unavailable.get()), 'recovered-frame');
  cases++;

  for (const age of [4000, -4000]) {
    const stale = backend();
    setFrame(stale.state.now, age, 'do-not-serve');
    assert.equal(String(await stale.get()), 'recovered-frame');
    assert.equal(stale.state.captures, 1);
    cases++;
  }
  console.log(`Viewer backend: ${cases} real-file/process scenarios pass; synthetic frame bytes only.`);
})().catch(error => { console.error(error); process.exitCode = 1; }).finally(() => {
  assert.equal(path.dirname(path.resolve(root)), path.resolve(os.tmpdir()));
  assert.ok(path.basename(root).startsWith('bloons-viewer-backend-'));
  fs.rmSync(root, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
});
