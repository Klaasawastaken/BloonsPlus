const PROJECT_ROOT = require('node:path').resolve(__dirname, '..');
const fs = require('node:fs');
const path = require('node:path');
const { execFile } = require('node:child_process');
const automation = require('./automation');
const directory = path.join(PROJECT_ROOT, 'autobtd6');
let pending = null;
let cached = null;
let capturedAt = 0;

async function getLiveScreen() {
  if (pending) return pending;
  if (cached && Date.now() - capturedAt < 1000) return cached;
  pending = (async () => {
    fs.writeFileSync(path.join(directory, 'viewer-request.json'), JSON.stringify({ expiresAt: Date.now() + 10000 }));
    const frame = path.join(directory, 'live-frame.jpg');
    try {
      if (Date.now() - fs.statSync(frame).mtimeMs < 3000) return fs.readFileSync(frame);
    } catch { /* No active replay frame yet. */ }
    const runtime = automation.getRuntime();
    if (!runtime.available) throw new Error('Game viewer needs the installed Python runtime.');
    return new Promise((resolve, reject) => execFile(runtime.executable, [path.join(directory, 'live_capture.py')],
      { cwd: directory, windowsHide: true, timeout: 8000, encoding: 'buffer', maxBuffer: 2 * 1024 * 1024 },
      (error, stdout) => error ? reject(new Error('Game screen unavailable. Open BTD6 in the VM desktop.')) : resolve(stdout)));
  })();
  try { cached = await pending; capturedAt = Date.now(); return cached; }
  finally { pending = null; }
}
module.exports = { getLiveScreen };
