const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../lib/live-screen.js'), 'utf8');

function viewer({ now = 10000, frameTime = 9000 } = {}) {
  const state = { now, frameTime, captures: 0, reads: 0, requests: 0 };
  const context = {
    __dirname: path.join(__dirname, '../lib'), module: { exports: {} },
    Date: { now: () => state.now },
    require(name) {
      if (name === 'node:path') return path;
      if (name === 'node:fs') return {
        writeFileSync() { state.requests++; },
        statSync() { return { mtimeMs: state.frameTime }; },
        readFileSync() { state.reads++; return Buffer.from('replay-frame'); },
      };
      if (name === './automation') return { getRuntime: () => ({ available: true, executable: 'python' }) };
      if (name === 'node:child_process') return { execFile(command, args, options, callback) {
        state.captures++;
        callback(null, Buffer.from('foreground-capture'));
      } };
      throw new Error(`Unexpected dependency: ${name}`);
    },
  };
  vm.runInNewContext(source, context, { filename: 'lib/live-screen.js' });
  return { state, get: context.module.exports.getLiveScreen };
}

(async () => {
  const recent = viewer();
  assert.equal(String(await recent.get()), 'replay-frame');
  recent.state.now += 500;
  await recent.get();
  assert.equal(recent.state.requests, 1, 'Use response cache within its one-second lifetime');
  assert.equal(recent.state.captures, 0, 'Reuse a genuinely recent replay frame');

  const stale = viewer({ frameTime: 7000 });
  assert.equal(String(await stale.get()), 'foreground-capture');
  assert.equal(stale.state.captures, 1, 'Exactly three seconds is expired');

  const future = viewer({ frameTime: 20000 });
  assert.equal(String(await future.get()), 'foreground-capture', 'Never reuse a future-dated replay frame');
  assert.equal(future.state.reads, 0);

  const rollback = viewer();
  await rollback.get();
  rollback.state.now = 5000;
  assert.equal(String(await rollback.get()), 'foreground-capture', 'Clock rollback expires both caches');
  assert.equal(rollback.state.captures, 1);
  console.log('Live viewer freshness: recent, stale, future-dated and clock rollback checks pass.');
})().catch(error => { console.error(error); process.exitCode = 1; });
