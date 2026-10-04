// Standalone local dashboard: polls the VM's own /api/farm/status and
// /api/game-status over SSH and serves a self-refreshing page on the HOST
// machine. Does not touch the screen, mouse, or keyboard. Open the URL it
// prints in your own browser to watch the sweep live.
const http = require('http');
const { execFile } = require('child_process');

const SSH_KEY = 'C:/ProgramData/AppSandbox/ssh/id_appsandbox';
let SSH_PORT = process.env.SWEEP_SSH_PORT || '62752';
const SSH_HOST = 'user@127.0.0.1';
const PORT = process.env.SWEEP_DASHBOARD_PORT || 5055;

let latest = { log: [], victories: 0, defeats: 0, running: false, fetchedAt: null, error: null };

function vmCurl(path) {
  return new Promise((resolve, reject) => {
    execFile('ssh', [
      '-i', SSH_KEY, '-p', SSH_PORT, '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=5',
      SSH_HOST, `curl -s http://127.0.0.1:4173${path}`,
    ], { timeout: 10000 }, (err, stdout) => {
      if (err) return reject(err);
      try { resolve(JSON.parse(stdout)); } catch (e) { reject(new Error('bad JSON: ' + stdout.slice(0, 200))); }
    });
  });
}

function vmPost(path, body = '{}') {
  return vmCurl(`${path} -X POST -m 20 -H "Content-Type: application/json" -d ${JSON.stringify(body)}`).catch(() => null);
}

// Self-heal: the sweep stops itself when BTD6 is unavailable (crash, error popup, focus lost).
// Relaunch the game and restart the sweep, at most every 10 minutes. A stop the user asked
// for is never undone.
const HEALABLE_STOP = /sweep stopped: (game-unavailable|invalid-window|BTD6 could not be brought)|BTD6 did not come back|could not be focused 3 times|resume refused: BTD6 is not on the in-game screen/;
let lastHealAt = 0;
let healing = false;
async function heal() {
  healing = true;
  lastHealAt = Date.now();
  console.log(new Date().toISOString(), 'self-heal: relaunching BTD6 and restarting the sweep');
  try {
    for (let i = 0; i < 30; i++) {
      const game = await vmCurl('/api/game-status').catch(() => null);
      if (game?.game) break;
      await vmPost('/api/setup/launch-game');
      await new Promise(resolve => setTimeout(resolve, 10000));
    }
    const started = await vmPost('/api/farm/start', '{"type":"black-border-sweep"}');
    console.log(new Date().toISOString(), 'self-heal: sweep start', JSON.stringify(started));
  } finally {
    healing = false;
  }
}

async function poll() {
  try {
    const status = await vmCurl('/api/farm/status');
    latest = { ...status, fetchedAt: new Date().toISOString(), error: null };
    const tail = (status.log || []).slice(-6).join('\n');
    if (!status.running && !status.busyWith && !healing && HEALABLE_STOP.test(tail)
        && !/stopped by user/.test(tail) && Date.now() - lastHealAt > 10 * 60 * 1000) {
      heal();
    }
  } catch (e) {
    latest = { ...latest, fetchedAt: new Date().toISOString(), error: e.message };
    refreshSshPort();   // a VM restart publishes a new SSH port
  }
  setTimeout(poll, 4000);
}
function refreshSshPort() {
  const dir = require('path').join(require('os').homedir(), 'Downloads', 'AppSandbox', 'headless-api').split('\\').join('/');
  execFile('py', ['-c', `import sys; sys.path.insert(0, r'${dir}'); import asb; print(asb.connect().status('BloonsPlusVM2').get('sshPort'))`],
    { timeout: 20000 }, (err, stdout) => {
      const port = String(stdout || '').trim();
      if (!err && /^\d+$/.test(port) && port !== SSH_PORT) { console.log('VM ssh port', SSH_PORT, '->', port); SSH_PORT = port; }
    });
}
poll();

// BTD6 dies without a crash dump when the VM's display closes; keep it open.
const ASB_DIR = require('path').join(require('os').homedir(), 'Downloads', 'AppSandbox', 'headless-api').replace(/\\/g, '/');
function ensureVmDisplay() {
  const script = `import sys; sys.path.insert(0, r'${ASB_DIR}'); import asb; c = asb.connect(); s = c.status('BloonsPlusVM2')\n`
    + `if s.get('running') and not s.get('displayOpen'): print('reopened', c.open_display('BloonsPlusVM2'))`;
  execFile('py', ['-c', script], { timeout: 30000 }, (err, stdout) => {
    if (stdout && stdout.trim()) console.log(new Date().toISOString(), 'VM display', stdout.trim());
  });
}
setInterval(ensureVmDisplay, 60000);
ensureVmDisplay();

http.createServer((req, res) => {
  if (req.url === '/data') {
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    return res.end(JSON.stringify(latest));
  }
  res.writeHead(200, { 'Content-Type': 'text/html' });
  res.end(`<!doctype html><html><head><meta charset="utf-8"><title>BTD6 Sweep Dashboard</title>
<style>
body{background:#111;color:#ddd;font:14px/1.4 Consolas,monospace;margin:0;padding:16px}
#stats{margin-bottom:10px}
#stats span{display:inline-block;margin-right:20px;font-size:15px}
.v{color:#6f6}.d{color:#f66}.r{color:#6cf}
#log{white-space:pre-wrap;background:#000;padding:10px;border-radius:6px;height:80vh;overflow-y:auto}
.hi-clear{color:#6f6}.hi-defeat{color:#f66}.hi-medal{color:#fc6}.hi-err{color:#f66;font-weight:bold}
</style></head><body>
<div id="stats">Loading...</div>
<div id="log"></div>
<script>
function cls(line){
  if(/INSTANT_LOSS|EMERGENCY_SPEND/.test(line)) return 'hi-err';
  if(/LATE_LOSS|LIVES_LOST/.test(line)) return 'hi-medal';
  if(/clear|VICTORY/i.test(line)) return 'hi-clear';
  if(/defeat|fail/i.test(line)) return 'hi-defeat';
  if(/MEDAL_ALREADY_EARNED/i.test(line)) return 'hi-medal';
  if(/error|not unlocked/i.test(line)) return 'hi-err';
  return '';
}
async function tick(){
  try{
    const r = await fetch('/data'); const d = await r.json();
    document.getElementById('stats').innerHTML =
      '<span class="r">running: ' + (d.running?'yes':'no') + '</span>' +
      '<span class="v">victories: ' + (d.victories||0) + '</span>' +
      '<span class="d">defeats: ' + (d.defeats||0) + '</span>' +
      (function(){ const c = d.lossCounts || {}; return '<span>instant: ' + (c.instant||0) + ' (prevented ' + (c['instant-prevented']||0) + ')</span><span>early: ' + (c.early||0) + '</span><span>mid: ' + (c.mid||0) + '</span><span>late: ' + (c.late||0) + '</span>'; })() +
      '<span>updated: ' + (d.fetchedAt||'-') + '</span>' +
      (d.error ? '<span class="hi-err">  SSH ERROR: '+d.error+'</span>' : '');
    const lines = (d.log||[]).slice(-300);
    document.getElementById('log').innerHTML = lines.map(l => '<div class="'+cls(l)+'">'+l.replace(/</g,'&lt;')+'</div>').join('');
    const logEl = document.getElementById('log');
    logEl.scrollTop = logEl.scrollHeight;
  }catch(e){}
  setTimeout(tick, 4000);
}
tick();
</script></body></html>`);
}).listen(PORT, '127.0.0.1', () => {
  console.log(`Sweep dashboard: http://127.0.0.1:${PORT}`);
});
