// Reaches the Bloons+ server that runs inside the App Sandbox VM through ONE long-lived SSH tunnel.
// A fresh SSH login per status poll trips OpenSSH's per-source penalties in the guest ("Not allowed at
// this time"): every host connection arrives from the same loopback proxy, so the host gets locked out.
const fs = require('node:fs');
const { spawn } = require('node:child_process');

const APP_SANDBOX_DIR = process.env.APPSANDBOX_DATA || 'C:\\ProgramData\\AppSandbox';
const LOCAL_KEY = `${process.env.LOCALAPPDATA || ''}\\BloonsPlus\\ssh\\id_appsandbox`;
const SSH_KEY = fs.existsSync(LOCAL_KEY) ? LOCAL_KEY : `${APP_SANDBOX_DIR}\\ssh\\id_appsandbox`;
const LOCAL_PORT = 14173;
const RETRY_MS = 15_000;

let tunnel = null;
let nextAttemptAt = 0;

// Authenticated call to the App Sandbox daemon's local API (host.json holds its endpoint + token).
// Throws when the daemon is not running. vm-setup.js drives VM setup through the same helper.
async function sandboxApi(method, apiPath, body, timeoutMs = 3000) {
  const { endpoint, token } = JSON.parse(fs.readFileSync(`${APP_SANDBOX_DIR}\\host.json`, 'utf8'));
  const response = await fetch(`${endpoint.replace(/\/$/, '')}/v1${apiPath}`, {
    method, headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: body === undefined ? (method === 'GET' ? undefined : '{}') : JSON.stringify(body),
    signal: AbortSignal.timeout(timeoutMs),
  });
  const text = await response.text();
  return { status: response.status, body: text ? JSON.parse(text) : {} };
}

// The guest's SSH port changes when App Sandbox restarts, so ask its API instead of hardcoding it.
async function vmSshPort() {
  const vm = (await sandboxApi('GET', '/vms')).body.vms?.find(entry => entry.name.startsWith('Bloons') && entry.state === 'online');
  return vm?.sshPort || null;
}

async function ensureTunnel() {
  if (tunnel || Date.now() < nextAttemptAt || !fs.existsSync(SSH_KEY)) return;
  nextAttemptAt = Date.now() + RETRY_MS;
  let port;
  // Another Bloons+ process may already hold the tunnel; reuse it instead of logging in again.
  try { if ((await fetch(`http://127.0.0.1:${LOCAL_PORT}/api/game-status`, { signal: AbortSignal.timeout(4000) })).ok) return; } catch { /* not held */ }
  try { port = await vmSshPort(); } catch { return; }
  if (!port || tunnel) return;
  tunnel = spawn('ssh.exe', ['-N', '-i', SSH_KEY, '-p', String(port),
    '-L', `${LOCAL_PORT}:127.0.0.1:4173`, '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=NUL',
    '-o', 'IdentitiesOnly=yes', '-o', 'PreferredAuthentications=publickey', '-o', 'PasswordAuthentication=no',
    '-o', 'KbdInteractiveAuthentication=no', '-o', 'ConnectTimeout=15',
    '-o', 'BatchMode=yes', '-o', 'ExitOnForwardFailure=yes', '-o', 'ServerAliveInterval=30', 'user@127.0.0.1'],
  { windowsHide: true, stdio: ['ignore', 'ignore', 'pipe'] });
  // App Sandbox can publish the VM port a few seconds before sshd has loaded
  // its authorized key. Treat that transient rejection as reconnectable and
  // retry with a fresh tunnel instead of exposing the raw OpenSSH error.
  tunnel.stderr?.on('data', chunk => {
    const text = String(chunk);
    if (/permission denied|connection refused|could not resolve/i.test(text)) {
      try { tunnel.kill(); } catch { /* already exiting */ }
    }
  });
  tunnel.on('exit', () => { tunnel = null; nextAttemptAt = Date.now() + RETRY_MS; });
  tunnel.on('error', () => { tunnel = null; nextAttemptAt = Date.now() + RETRY_MS; });
}

// Text of a GET on the VM's Bloons+ server, or null when the VM (or tunnel) isn't there.
async function vmFetch(apiPath, timeoutMs = 5000) {
  await ensureTunnel();
  try {
    const response = await fetch(`http://127.0.0.1:${LOCAL_PORT}${apiPath}`, { signal: AbortSignal.timeout(timeoutMs) });
    return response.ok ? await response.text() : null;
  } catch { return null; }
}

// Bytes of a GET on the VM's Bloons+ server (images), or null.
async function vmFetchBuffer(apiPath, timeoutMs = 5000) {
  await ensureTunnel();
  try {
    const response = await fetch(`http://127.0.0.1:${LOCAL_PORT}${apiPath}`, { signal: AbortSignal.timeout(timeoutMs) });
    return response.ok ? Buffer.from(await response.arrayBuffer()) : null;
  } catch { return null; }
}

// POST to the VM's Bloons+ server: {status, text}, or null when the VM (or tunnel) isn't there.
async function vmPost(apiPath, body, timeoutMs = 10000) {
  await ensureTunnel();
  try {
    const response = await fetch(`http://127.0.0.1:${LOCAL_PORT}${apiPath}`, { method: 'POST', body,
      headers: { 'Content-Type': 'application/json' }, signal: AbortSignal.timeout(timeoutMs) });
    return { status: response.status, text: await response.text() };
  } catch { return null; }
}

function closeTunnel() { tunnel?.kill(); }
// Called by setup once the VM has just come online, so the tunnel does not wait out its retry delay.
function retryTunnelSoon() { if (!tunnel) nextAttemptAt = 0; }
process.on('exit', closeTunnel);

module.exports = { vmFetch, vmPost, vmFetchBuffer, sandboxApi, retryTunnelSoon, APP_SANDBOX_DIR, SSH_KEY };
