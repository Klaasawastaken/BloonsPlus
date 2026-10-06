// Reaches the Bloons+ server that runs inside the App Sandbox VM through ONE long-lived SSH tunnel.
// A fresh SSH login per status poll trips OpenSSH's per-source penalties in the guest ("Not allowed at
// this time"): every host connection arrives from the same loopback proxy, so the host gets locked out.
const fs = require('node:fs');
const { spawn } = require('node:child_process');
const { execFile } = require('node:child_process');

const APP_SANDBOX_DIR = process.env.APPSANDBOX_DATA || 'C:\\ProgramData\\AppSandbox';
const LOCAL_KEY = `${process.env.LOCALAPPDATA || ''}\\BloonsPlus\\ssh\\id_appsandbox`;
const SANDBOX_KEY = `${APP_SANDBOX_DIR}\\ssh\\id_appsandbox`;
function readableKey(file) {
  try { fs.accessSync(file, fs.constants.R_OK); return true; } catch { return false; }
}
// A stale per-user copy can exist with an ACL that blocks the elevated controller. Prefer
// whichever configured key is actually readable instead of selecting by existence alone.
const SSH_KEY = readableKey(LOCAL_KEY) ? LOCAL_KEY : SANDBOX_KEY;
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

// A first installation has no HTTP app yet. Observe its exact owned processes
// and native dependency journal through read-only SSH; a failed observation is
// unknown, never idle. Keys, tasks and guest permissions are not changed here.
async function vmReplayState() {
  const remote = await vmFetch('/api/farm/status?view=ui', 4000);
  try { const value=JSON.parse(remote); if (typeof value?.running === 'boolean') return {running:value.running}; } catch { /* Try a fresh process observation. */ }
  let port;
  try { port=await vmSshPort(); } catch { return null; }
  if (!Number.isInteger(port) || port<1 || port>65535) return null;
  const script = `try {
    $ErrorActionPreference = 'Stop'
    $root = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'Programs\\Bloons+'
    $expected = @((Join-Path $root 'Bloons+.exe'), (Join-Path $root 'resources\\app\\node.exe'))
    $owned = @(Get-Process -Name 'Bloons+','node' -ErrorAction SilentlyContinue | Where-Object { $expected -contains $_.MainModule.FileName })
    if ($owned.Count -gt 0) { throw 'Controller status is unavailable' }
    $journal = Join-Path $root '.bloons-setup\\owned-process.json'
    if (Test-Path -LiteralPath $journal) {
      $assembly = [Reflection.Assembly]::LoadFile((Join-Path $root 'BloonsPlusSetup.exe'))
      $type = $assembly.GetType('OwnedProcess', $true)
      $observer = $type.GetConstructor(@([string])).Invoke(@([string]$root))
      try { if ($type.GetMethod('Observe').Invoke($observer,@()) -ne 'idle') { throw 'Setup ownership is unknown' } }
      finally { $observer.Dispose() }
    }
    $lock = Join-Path $root '.bloons-install.lock'
    if (Test-Path -LiteralPath $lock) { $handle = [IO.File]::Open($lock,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::None); $handle.Dispose() }
    @{running=$false} | ConvertTo-Json -Compress
  } catch { @{running=$null} | ConvertTo-Json -Compress }`;
  const encoded = Buffer.from(script,'utf16le').toString('base64');
  const args=['-i',SSH_KEY,'-p',String(port),'-o','StrictHostKeyChecking=no','-o','UserKnownHostsFile=NUL',
    '-o','IdentitiesOnly=yes','-o','PreferredAuthentications=publickey','-o','PasswordAuthentication=no',
    '-o','KbdInteractiveAuthentication=no','-o','ConnectTimeout=10','-o','BatchMode=yes','-o','LogLevel=ERROR',
    'user@127.0.0.1',`powershell.exe -NoProfile -NonInteractive -EncodedCommand ${encoded}`];
  return new Promise(resolve=>execFile('ssh.exe',args,{windowsHide:true,timeout:15000,maxBuffer:65536},(error,stdout)=>{
    if (error) return resolve(null);
    try { const value=JSON.parse(stdout.trim()); resolve(typeof value?.running === 'boolean' ? {running:value.running} : null); }
    catch { resolve(null); }
  }));
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

module.exports = { vmFetch, vmPost, vmFetchBuffer, vmReplayState, sandboxApi, retryTunnelSoon, APP_SANDBOX_DIR, SSH_KEY };
