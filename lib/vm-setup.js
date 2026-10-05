const PROJECT_ROOT = require('node:path').resolve(__dirname, '..');
// First-run setup of the Bloons+ VM, driven by the Setup bar (setup-bar.js) through
//   GET  /api/setup/status  -> every step with live done/pending state and what to do next
//   POST /api/setup/start   -> runs the next pending steps in the background ({ isoPath } optional)
//   GET  /api/setup/guest   -> (answered inside the VM) Steam sign-in + BTD6 install state
// Every step is detected from the machine itself, so re-running is always safe.
// Heavy VM work (create, SSH provisioning) is vm/setup-vm.py, shared with vm/setup-vm.cmd.
// Rules: admin rights only through Windows' own UAC prompt (Start-Process -Verb RunAs); never reboot,
// never collect Steam credentials (the user signs in inside Steam's window in the VM).
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { Readable, Transform } = require('node:stream');
const { pipeline } = require('node:stream/promises');
const { execFile, spawn } = require('node:child_process');
const { vmFetch, sandboxApi, retryTunnelSoon, APP_SANDBOX_DIR } = require('./vm-bridge');

const ROOT = PROJECT_ROOT;
const DATA_DIR = path.join(process.env.LOCALAPPDATA || path.join(require('node:os').homedir(), 'AppData', 'Local'), 'BloonsPlus');
const STATE_FILE = path.join(DATA_DIR, 'setup-state.json');
const OWN_SANDBOX = path.join(DATA_DIR, 'AppSandbox');
const LEGACY_SANDBOX = path.join(process.env.USERPROFILE || require('node:os').homedir(), 'Downloads', 'AppSandbox');
const PATCHED_ISO_PATCH = path.join(ROOT, 'vm', 'iso-patch.exe'); // fixes App Sandbox 0.1.9's bcdboot error (issue #62)
const SETUP_SCRIPT = path.join(ROOT, 'vm', 'setup-vm.py');
const GUEST_AGENT = 'C:\\Windows\\AppSandbox\\appsandbox-agent.exe'; // present only inside an App Sandbox VM
const APP_SANDBOX_ZIP_URL = 'https://github.com/jamesstringer90/appsandbox/releases/download/v0.1.9/AppSandbox-0.1.9-win-x64.zip';
const FIDO_URL = 'https://raw.githubusercontent.com/pbatard/Fido/v1.70/Fido.ps1'; // asks Microsoft for a fresh ISO link
const BTD6_APP_ID = 960090;
const VM_PREFIX = 'Bloons';

const STEPS = [
  { id: 'vmp', title: 'Virtual Machine Platform' },
  { id: 'appsandbox', title: 'App Sandbox' },
  { id: 'daemon', title: 'App Sandbox running' },
  { id: 'iso', title: 'Windows 11 ISO' },
  { id: 'vm', title: 'VM online' },
  { id: 'provision', title: 'Steam + Bloons+ in the VM' },
  { id: 'connected', title: 'Bloons+ in the VM connected' },
  { id: 'steam', title: 'Steam signed in + BTD6 installed' },
];

// ---------- small helpers ----------
function readState() { try { return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')); } catch { return {}; } }
function writeState(patch) {
  const next = { ...readState(), ...patch };
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.writeFileSync(STATE_FILE, JSON.stringify(next, null, 2));
  return next;
}
const psQuote = value => `'${String(value).replace(/'/g, "''")}'`;
function powershell(command, timeout = 20000) {
  return new Promise((resolve, reject) => execFile('powershell.exe', ['-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-Command', command],
    { windowsHide: true, timeout, maxBuffer: 4 * 1024 * 1024 }, (error, stdout, stderr) => {
      if (!error) return resolve(stdout.trim());
      reject(Object.assign(new Error((stderr || error.message).trim()), { exitCode: error.code }));
    }));
}
// Runs a program elevated through Windows' own UAC prompt; rejects if the user declines it.
async function runElevated(file, args, { wait = false, hidden = true } = {}) {
  const command = `$p = Start-Process -FilePath ${psQuote(file)}${args ? ` -ArgumentList ${psQuote(args)}` : ''} -WorkingDirectory ${psQuote(path.dirname(file))} -Verb RunAs${hidden ? ' -WindowStyle Hidden' : ''} -PassThru${wait ? ' -Wait' : ''}; ${wait ? 'exit $p.ExitCode' : 'exit 0'}`;
  try { await powershell(command, wait ? 30 * 60_000 : 120_000); }
  catch (error) {
    if (/cancel/i.test(error.message)) throw new Error('Windows asked for administrator permission and it was declined. Click the button again and choose Yes.');
    if (wait && error.exitCode === 3010) return; // dism: "success, restart required"
    throw error;
  }
}
const fileExists = file => { try { return fs.statSync(file).isFile(); } catch { return false; } };
const hashCache = new Map();
function sha256(file) {
  const stat = fs.statSync(file), key = `${file}|${stat.size}|${stat.mtimeMs}`;
  if (!hashCache.has(key)) hashCache.set(key, crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'));
  return hashCache.get(key);
}
const gb = bytes => (bytes / 1024 ** 3).toFixed(1);

// ---------- detection ----------
const isGuest = () => fileExists(GUEST_AGENT);

function sandboxDir() {
  const state = readState();
  const valid = dir => dir && fileExists(path.join(dir, 'AppSandbox.exe')) && fileExists(path.join(dir, 'headless-api', 'asb.py'));
  return [state.appSandboxDir, OWN_SANDBOX, LEGACY_SANDBOX].find(valid) || null;
}
function isoPatched(dir) {
  const target = path.join(dir, 'iso-patch.exe');
  return fileExists(target) && fileExists(PATCHED_ISO_PATCH) && sha256(target) === sha256(PATCHED_ISO_PATCH);
}

let vmpCache = null;
async function checkVmp() {
  if (vmpCache?.done || (vmpCache && Date.now() - vmpCache.at < 15000)) return vmpCache;
  // Non-admin readable: the feature's install state and whether the hypervisor actually runs.
  const out = await powershell("$f = Get-CimInstance Win32_OptionalFeature -Filter \"Name='VirtualMachinePlatform'\"; $h = (Get-CimInstance Win32_ComputerSystem).HypervisorPresent; @{ state = [int]$f.InstallState; hypervisor = [bool]$h } | ConvertTo-Json -Compress").catch(() => '{}');
  let parsed = {};
  try { parsed = JSON.parse(out); } catch { /* unknown */ }
  const enabled = parsed.state === 1;
  vmpCache = { at: Date.now(), enabled, hypervisor: parsed.hypervisor === true, done: enabled && parsed.hypervisor === true };
  return vmpCache;
}

// vms.cfg is readable without the daemon, so a stopped daemon still tells us whether the VM exists.
function configuredVms() {
  try {
    const text = fs.readFileSync(path.join(APP_SANDBOX_DIR, 'vms.cfg'), 'utf8');
    return { names: [...text.matchAll(/^Name=(.+)$/gm)].map(m => m[1].trim()), lastIso: (text.match(/^LastIsoPath=(.+)$/m) || [])[1]?.trim() };
  } catch { return { names: [], lastIso: null }; }
}

function findIso(dir) {
  const big = file => { try { return fs.statSync(file).size > 3 * 1024 ** 3 && /\.iso$/i.test(file); } catch { return false; } };
  const candidates = [readState().isoPath, configuredVms().lastIso];
  for (const folder of [dir, OWN_SANDBOX, LEGACY_SANDBOX].filter(Boolean)) {
    try { for (const name of fs.readdirSync(folder)) if (/win.?11/i.test(name) && /\.iso$/i.test(name)) candidates.push(path.join(folder, name)); } catch { /* missing folder */ }
  }
  return candidates.find(big) || null;
}

async function daemonState() {
  try {
    const version = (await sandboxApi('GET', '/version')).body;
    if (version.product !== 'AppSandbox') return { running: false };
    const vms = (await sandboxApi('GET', '/vms')).body.vms || [];
    return { running: true, version: version.version, vm: vms.find(vm => vm.name.startsWith(VM_PREFIX)) || null };
  } catch { return { running: false }; }
}

async function guestState() {
  const text = await vmFetch('/api/setup/guest', 4000);
  if (text) { try { return JSON.parse(text); } catch { /* older build */ } }
  // A Bloons+ build without /api/setup/guest: a running BTD6 proves Steam is signed in and BTD6 installed.
  const game = await vmFetch('/api/game-status', 4000);
  try { return game ? { legacy: true, gameRunning: JSON.parse(game).game === true } : null; } catch { return null; }
}

// ---------- background job ----------
const job = { running: false, activity: '', log: [], error: null, finishedAt: 0, progress: null };
function note(line) {
  const text = String(line).trim();
  if (!text) return;
  job.activity = text.replace(/^\[\d\d:\d\d:\d\d\]\s*/, '');
  job.log.push(`${new Date().toLocaleTimeString()}  ${job.activity}`);
  if (job.log.length > 60) job.log.splice(0, job.log.length - 60);
}

function pythonExe() {
  return [process.env.BLOONS_PYTHON, path.join(ROOT, '.venv', 'Scripts', 'python.exe'), path.join(ROOT, 'python', 'python.exe')].filter(Boolean).find(fileExists) || 'python';
}
function installerCopy() {
  // Developer checkout: dist/. Installed app: the installer keeps a copy of itself next to Bloons+.exe.
  return [path.join(ROOT, 'dist', 'BloonsPlusSetup.exe'), path.resolve(ROOT, '..', '..', 'BloonsPlusSetup.exe')].find(fileExists) || null;
}

function runSetupScript(action, extra = []) {
  const dir = sandboxDir();
  const args = ['-u', SETUP_SCRIPT, action, '--appsandbox-dir', dir, '--cache-dir', DATA_DIR, ...extra];
  return new Promise((resolve, reject) => {
    const child = spawn(pythonExe(), args, { cwd: ROOT, windowsHide: true, env: { ...process.env, PYTHONUNBUFFERED: '1', PYTHONIOENCODING: 'utf-8' } });
    const deadline = setTimeout(() => {
      child.kill();
      reject(new Error(`${action} timed out. The VM was left running; retry setup to continue the missing steps.`));
    }, action === 'provision' ? 60 * 60 * 1000 : 12 * 60 * 1000);
    let tail = '';
    const onData = chunk => { for (const line of String(chunk).split(/\r?\n/)) { if (line.trim()) { tail = line; if (!/^Warning: Permanently added/.test(line)) note(line); } } };
    child.stdout.on('data', onData);
    child.stderr.on('data', onData);
    child.on('error', error => { clearTimeout(deadline); reject(error); });
    child.on('exit', code => { clearTimeout(deadline); code === 0 ? resolve() : reject(new Error(tail || `setup-vm.py ${action} exited with code ${code}`)); });
  });
}

async function download(url, target, label) {
  fs.mkdirSync(path.dirname(target), { recursive: true });
  const part = `${target}.part`;
  const have = fileExists(part) ? fs.statSync(part).size : 0;
  const signal = AbortSignal.timeout(2 * 60 * 60 * 1000);
  let response = await fetch(url, { headers: have ? { Range: `bytes=${have}-` } : {}, signal });
  if (response.status === 416 && have) {
    // A stale .part may already equal the remote file (common for tiny Fido.ps1),
    // or the remote file may have changed. Never keep retrying an invalid range.
    const remoteSize = Number((response.headers.get('content-range') || '').match(/\*\/(\d+)$/)?.[1]);
    await response.body?.cancel();
    if (have > 10 * 1024 * 1024 && remoteSize === have) {
      fs.renameSync(part, target);
      job.progress = null;
      note(`${label}: completed saved download.`);
      return;
    }
    note(`${label}: saved partial download cannot resume; downloading it again.`);
    response = await fetch(url, { signal }); // Replace stale partial only after this succeeds.
  }
  if (!response.ok) throw new Error(`${label}: download failed (HTTP ${response.status})`);
  const resumed = response.status === 206;
  const range = resumed ? /^bytes (\d+)-(\d+)\/(\d+)$/.exec(response.headers.get('content-range') || '') : null;
  const lengthHeader = response.headers.get('content-length');
  const responseLength = lengthHeader === null ? null : Number(lengthHeader);
  if (resumed && (!range || !range.slice(1).every(value => Number.isSafeInteger(Number(value)))
      || Number(range[1]) !== have || Number(range[2]) < have || Number(range[2]) >= Number(range[3])
      || (responseLength !== null && responseLength !== Number(range[2]) - have + 1))) {
    await response.body?.cancel();
    throw new Error(`${label}: server returned an invalid resume range or length. No files were appended; retry the download.`);
  }
  // A server may cap the returned range. Content-Length describes that chunk,
  // not the complete file; only Content-Range supplies the full resumed size.
  const total = resumed ? Number(range[3]) : (responseLength || 0);
  let written = resumed ? have : 0, lastNote = 0;
  const out = fs.createWriteStream(part, { flags: resumed ? 'a' : 'w' });
  const meter = new Transform({ transform(chunk, encoding, callback) {
      written += chunk.length;
      job.progress = total ? written / total : null;
      if (Date.now() - lastNote > 2000) { lastNote = Date.now(); job.activity = `${label}: ${gb(written)} of ${total ? gb(total) : '?'} GB`; }
      callback(null, chunk);
  }});
  try { await pipeline(Readable.fromWeb(response.body), meter, out); }
  catch (error) {
    job.progress = null;
    throw new Error(`${label}: ${error.code === 'ENOSPC' ? 'Not enough disk space. Free space on the download drive.' : error.message} The partial download is saved; retry to resume.`);
  }
  if (resumed && written !== Number(range[2]) + 1) {
    job.progress = null;
    fs.truncateSync(part, have);
    throw new Error(`${label}: downloaded bytes did not match the resume range; previous partial retained.`);
  }
  if (total && written !== total) {
    job.progress = null;
    throw new Error(`${label}: download ended early; click again to resume`);
  }
  fs.renameSync(part, target);
  job.progress = null;
}

// ---------- step actions ----------
async function enableVmp() {
  note('Turning on Virtual Machine Platform (Windows asks for permission)…');
  await runElevated(path.join(process.env.WINDIR || 'C:\\Windows', 'System32', 'dism.exe'), '/online /enable-feature /featurename:VirtualMachinePlatform /all /norestart', { wait: true });
  vmpCache = null;
  note('Virtual Machine Platform is turned on. Restart your PC to finish, then open Bloons+ again.');
}

async function installAppSandbox() {
  let dir = sandboxDir();
  if (!dir) {
    const zip = path.join(DATA_DIR, 'AppSandbox-0.1.9-win-x64.zip');
    note('Downloading App Sandbox 0.1.9 from GitHub…');
    if (!fileExists(zip)) await download(APP_SANDBOX_ZIP_URL, zip, 'App Sandbox');
    fs.mkdirSync(OWN_SANDBOX, { recursive: true });
    note('Extracting App Sandbox…');
    await new Promise((resolve, reject) => execFile(path.join(process.env.WINDIR || 'C:\\Windows', 'System32', 'tar.exe'), ['-xf', zip, '-C', OWN_SANDBOX], { windowsHide: true },
      error => (error ? reject(new Error(`Could not extract App Sandbox: ${error.message}`)) : resolve())));
    dir = OWN_SANDBOX;
    writeState({ appSandboxDir: dir });
  }
  if (!isoPatched(dir)) {
    note('Installing the patched iso-patch.exe (fixes App Sandbox issue #62)…');
    const target = path.join(dir, 'iso-patch.exe');
    if (fileExists(target) && !fileExists(`${target}.orig`)) fs.copyFileSync(target, `${target}.orig`);
    fs.copyFileSync(PATCHED_ISO_PATCH, target);
  }
  note('App Sandbox is ready.');
}

async function startDaemon() {
  const dir = sandboxDir();
  if ((await daemonState()).running) { note('Reusing the running App Sandbox.'); return; }
  note('Starting App Sandbox (Windows asks for permission; it needs administrator rights to run the VM)…');
  // The VM bridge uses App Sandbox's authenticated HTTP API, which is hosted only by the
  // --headless owner. Its /display endpoint still opens the normal visible VM window, so the
  // guest remains visible while setup and automation retain a working control plane.
  await runElevated(path.join(dir, 'AppSandbox.exe'), '--headless');
  for (let i = 0; i < 60; i++) {
    if ((await daemonState()).running) { note('App Sandbox is running.'); return; }
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  // Recover an orphaned elevated shell only when Windows reports no active VM worker. A stale
  // AppSandbox process can have no window at all, so CloseMainWindow() alone can never repair it.
  const repaired = await powershell("if (Get-Process vmwp,vmmem,vmmemWSL -ErrorAction SilentlyContinue) { 'busy'; exit }; $p = @(Get-Process AppSandbox -ErrorAction SilentlyContinue); if (!$p.Count) { 'none'; exit }; $closed = $false; $p | ForEach-Object { if ($_.MainWindowHandle -ne 0) { $closed = $_.CloseMainWindow() -or $closed } }; if ($closed) { 'closed' } else { 'orphaned:' + (($p | Select-Object -ExpandProperty Id) -join ',') }").catch(() => '');
  if (repaired.trim().startsWith('orphaned:')) {
    const pids = repaired.trim().slice('orphaned:'.length).split(',').map(Number).filter(Number.isInteger);
    for (const pid of pids) {
      await runElevated(path.join(process.env.WINDIR || 'C:\\Windows', 'System32', 'taskkill.exe'), `/PID ${pid} /T /F`, { wait: true });
    }
    note(`Removed ${pids.length} orphaned App Sandbox process${pids.length === 1 ? '' : 'es'}; retrying once…`);
  }
  if (repaired.trim() === 'closed' || repaired.trim().startsWith('orphaned:')) {
    if (repaired.trim() === 'closed') note('Closed an unresponsive App Sandbox window; retrying once…');
    await new Promise(resolve => setTimeout(resolve, 3000));
    await runElevated(path.join(dir, 'AppSandbox.exe'), '--headless');
    for (let i = 0; i < 30; i++) {
      if ((await daemonState()).running) { note('App Sandbox connection recovered.'); return; }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  throw new Error('App Sandbox did not respond. A running VM was left untouched. Check its window and retry setup.');
}

async function obtainIso(isoPath) {
  if (isoPath) {
    const file = path.resolve(String(isoPath).replace(/^"|"$/g, ''));
    if (!/\.iso$/i.test(file) || !fileExists(file) || fs.statSync(file).size < 3 * 1024 ** 3) throw new Error(`That is not a Windows 11 ISO file: ${file}`);
    writeState({ isoPath: file });
    note(`Using the Windows 11 ISO at ${file}`);
    return;
  }
  const fido = path.join(DATA_DIR, 'Fido.ps1');
  note('Asking Microsoft for a Windows 11 download link (Fido)…');
  if (!fileExists(fido)) await download(FIDO_URL, fido, 'Fido');
  const out = await powershell(`& ${psQuote(fido)} -Win 11 -Rel Latest -Ed Pro -Lang English -Arch x64 -GetUrl`, 120_000)
    .catch(error => { throw new Error(`Microsoft did not give a download link (${error.message.split('\n')[0]}). Download Windows 11 (English, x64) from microsoft.com/software-download/windows11 and enter the ISO path here.`); });
  const url = out.split(/\r?\n/).map(line => line.trim()).reverse().find(line => /^https:\/\/\S+\.iso(\?|$)/i.test(line));
  if (!url) throw new Error('Microsoft did not give a download link. Download Windows 11 (English, x64) from microsoft.com/software-download/windows11 and enter the ISO path here.');
  const target = path.join(sandboxDir() || OWN_SANDBOX, decodeURIComponent(new URL(url).pathname.split('/').pop()));
  await download(url, target, 'Downloading Windows 11');
  writeState({ isoPath: target });
  note('Windows 11 ISO downloaded.');
}

async function startVm(name) {
  note(`Starting the VM ${name}…`);
  if ((await daemonState()).vm?.state !== 'online') {
    const response = await sandboxApi('POST', `/vms/${encodeURIComponent(name)}/start`);
    if (response.status >= 400 && response.status !== 409) throw new Error(response.body?.error || `VM start failed (${response.status})`);
  }
  for (let i = 0; i < 180; i++) {
    const vm = (await daemonState()).vm;
    if (vm?.state === 'online') { retryTunnelSoon(); note('The VM is online.'); return; }
    if (i % 6 === 0) note(`Waiting for VM startup · ${vm?.state || 'connecting'} · ${Math.floor(i * 5 / 60)} min elapsed`);
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
  throw new Error('The VM did not come online within 15 minutes.');
}

async function provisionVm({ reinstall = false } = {}) {
  const installer = installerCopy();
  if (!installer) throw new Error('The Bloons+ installer copy (BloonsPlusSetup.exe) is missing from the Bloons+ folder. Run BloonsPlusSetup.exe again to repair it.');
  const extra = ['--installer', installer];
  if (reinstall) extra.push('--reinstall');
  const iso = findIso(sandboxDir());
  if (iso) extra.push('--iso', iso);
  await runSetupScript('provision', extra);
  const vm = (await daemonState()).vm;
  if (vm) writeState({ provisioned: { ...(readState().provisioned || {}), [vm.name]: new Date().toISOString() } });
  retryTunnelSoon();
}

async function updateGuest() {
  if (isGuest()) throw new Error('Remote VM updates must be started from the desktop copy of Bloons+.');
  if (job.running) return publicJob();
  const remote = await vmFetch('/api/farm/status', 4000);
  if (!remote) throw new Error('The VM is offline or Bloons+ is not connected. Start the VM first.');
  let status;
  try { status = JSON.parse(remote); } catch { status = {}; }
  if (status.running) throw new Error('A replay is active. Stop or finish it before updating the VM.');
  Object.assign(job, { running: true, error: null, progress: null });
  note('Updating Bloons+ in the VM…');
  provisionVm({ reinstall: true })
    .then(() => note('VM update installed.'))
    .catch(error => { job.error = error.message; note(`Update stopped: ${error.message}`); })
    .finally(() => { job.running = false; job.progress = null; job.finishedAt = Date.now(); statusCache = null; });
  return publicJob();
}

async function openVmWindow(name) {
  const { status } = await sandboxApi('POST', `/vms/${encodeURIComponent(name)}/display`).catch(() => ({ status: 0 }));
  if (status >= 200 && status < 300) note('The VM window is open.');
}
async function ensureVmDisplay() {
  if (isGuest()) return false;
  const status = await getStatus(true);
  if (status.vm?.state === 'online' && !status.vm.displayOpen) {
    await openVmWindow(status.vm.name);
    return true;
  }
  return false;
}

// ---------- status ----------
let statusCache = null;
async function computeStatus() {
  if (isGuest()) return { applicable: false, reason: 'This copy of Bloons+ runs inside the VM.', steps: [], allDone: true, job: publicJob() };
  const state = readState();
  const [vmp, daemon] = await Promise.all([checkVmp(), daemonState()]);
  const dir = sandboxDir();
  const vm = daemon.vm;
  const vmExists = !!vm || configuredVms().names.some(name => name.startsWith(VM_PREFIX));
  const online = vm?.state === 'online';
  const guest = online ? await guestState() : null;
  // The guest app is connected even before BTD6 is launched; checking game-status
  // here made first-run setup loop on "connected" and never reach Steam install.
  const connected = online && !!guest;
  const provisioned = connected || !!(vm && state.provisioned?.[vm.name]);
  const steamDone = !!guest && (guest.legacy ? guest.gameRunning : guest.steamSignedIn && guest.btd6Installed);
  const iso = vmExists ? null : findIso(dir);

  const done = {
    vmp: vmp.done || online, appsandbox: !!dir && isoPatched(dir), daemon: daemon.running,
    iso: vmExists || !!iso, vm: online, provision: provisioned, connected, steam: steamDone,
  };
  const detail = {
    vmp: vmp.done || online ? 'On' : vmp.enabled ? 'Turned on, restart needed' : 'Off',
    appsandbox: dir ? (isoPatched(dir) ? dir : 'Needs the patched iso-patch.exe') : 'Not downloaded (about 6 MB)',
    daemon: daemon.running ? `Version ${daemon.version}` : 'Not running',
    iso: vmExists ? 'Not needed, the VM exists' : iso || 'Not downloaded (about 8 GB)',
    vm: vm ? `${vm.name}: ${vm.state}${vm.building || (vm.progress && vm.progress < 100) ? ` ${vm.progress}%` : ''}${online && !guest ? ' · waiting for Bloons+ connection' : ''}` : (vmExists ? 'Stopped' : 'Not created'),
    provision: provisioned ? 'Done' : 'Pending',
    connected: connected ? 'Connected' : 'Waiting',
    steam: steamDone ? 'Ready' : guest && !guest.legacy ? `${guest.steamSignedIn ? 'Signed in' : 'Not signed in'}, BTD6 ${guest.btd6Installed ? 'installed' : 'not installed'}` : 'Waiting',
  };
  const steps = STEPS.map(step => ({ ...step, done: !!done[step.id], detail: detail[step.id] }));
  const next = steps.find(step => !step.done) || null;
  const plan = {
    vmp: vmp.enabled ? { message: 'Restart your PC to finish turning on Virtual Machine Platform, then open Bloons+ again.', button: null }
      : { message: 'Bloons+ runs BTD6 inside a virtual machine so your PC stays free. Click Set up: Windows asks for permission to turn on Virtual Machine Platform.', button: 'Set up' },
    appsandbox: { message: 'Click Continue to download App Sandbox (about 6 MB), the free tool that runs the VM.', button: 'Continue' },
    daemon: { message: 'Click Start App Sandbox. Windows asks for permission because it runs the VM.', button: 'Start App Sandbox' },
    iso: { message: 'The VM needs Windows 11. Click Download to get it from Microsoft (about 8 GB), or enter the path of a Windows 11 ISO you already have.', button: 'Download Windows 11', isoInput: true },
    vm: vmExists ? { message: 'The VM is not running. Click Start VM.', button: 'Start VM' }
      : { message: 'Click Create VM. Windows installs itself in the VM on its own (about 15-20 minutes).', button: 'Create VM' },
    provision: { message: 'Click Continue to install Steam and Bloons+ in the VM.', button: 'Continue' },
    connected: { message: 'Bloons+ is starting in the VM (the first start downloads its Python packages and can take a while). Meanwhile, sign in to Steam in the VM window.', button: 'Start Bloons+ in the VM' },
    steam: { message: 'Sign in to Steam in the VM window (your login stays inside Steam), then let it install Bloons TD 6. Bloons+ connects on its own.', button: 'Open VM window' },
  };
  return {
    applicable: true, allDone: !next, steps, next: next ? { id: next.id, ...plan[next.id] } : null,
    vm: vm ? { name: vm.name, state: vm.state, displayOpen: !!vm.displayOpen } : null,
    job: publicJob(),
  };
}
function publicJob() {
  return { running: job.running, activity: job.activity, error: job.error, progress: job.progress, log: job.log.slice(-12) };
}
async function getStatus(fresh = false) {
  if (!fresh && statusCache && Date.now() - statusCache.at < 2500) return { ...statusCache.value, job: publicJob() };
  const value = await computeStatus();
  statusCache = { at: Date.now(), value };
  return value;
}

// Runs pending steps in order until one needs the user (permission prompt declined, restart, sign-in).
async function runSetup(options) {
  for (let round = 0; round < 10; round++) {
    const status = await getStatus(true);
    const next = status.next;
    if (!status.applicable || !next) { note('Setup is complete. Bloons+ runs BTD6 in the VM.'); return; }
    if (next.id === 'vmp') {
      if ((await checkVmp()).enabled) { note('Restart your PC to finish turning on Virtual Machine Platform.'); return; }
      await enableVmp(); return; // a restart is always needed after this
    }
    if (next.id === 'appsandbox') await installAppSandbox();
    else if (next.id === 'daemon') await startDaemon();
    else if (next.id === 'iso') await obtainIso(options.isoPath);
    else if (next.id === 'vm') {
      const provisioned = status.vm && readState().provisioned?.[status.vm.name];
      if (status.vm && provisioned) await startVm(status.vm.name);
      else await provisionVm(); // creates or starts the VM, then installs Steam + Bloons+
    } else if (next.id === 'provision') await provisionVm();
    else if (next.id === 'connected') {
      await runSetupScript('launch-app');
      retryTunnelSoon();
      let connected = false;
      for (let i = 0; i < 60; i++) {
        if (await guestState()) { connected = true; note('The VM app is connected.'); break; }
        if (i % 6 === 0) note(`Waiting for the VM app · ${i * 5}s elapsed. First launch may install Python packages.`);
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
      if (!connected) throw new Error('The VM is online, but Bloons+ did not connect within 5 minutes. Check the app dependency setup in the VM window, then retry.');
    } else if (next.id === 'steam') {
      if (status.vm && !status.vm.displayOpen) await openVmWindow(status.vm.name);
      await runSetupScript('steam-install');
      return; // the user signs in inside Steam's window
    }
  }
}

function start(options = {}) {
  if (job.running) return publicJob();
  Object.assign(job, { running: true, error: null, progress: null });
  note('Setup started.');
  runSetup(options)
    .catch(error => { job.error = error.message; note(`Stopped: ${error.message}`); })
    .finally(() => { job.running = false; job.progress = null; job.finishedAt = Date.now(); statusCache = null; });
  return publicJob();
}

// ---------- inside the VM: local Steam state for the host's Setup bar ----------
async function guestSteam() {
  const out = await powershell("$s = Get-ItemProperty 'HKCU:\\Software\\Valve\\Steam' -ErrorAction SilentlyContinue; $a = Get-ItemProperty 'HKCU:\\Software\\Valve\\Steam\\ActiveProcess' -ErrorAction SilentlyContinue; @{ steamPath = [string]$s.SteamPath; activeUser = [int64]$a.ActiveUser; running = [bool](Get-Process steam -ErrorAction SilentlyContinue) } | ConvertTo-Json -Compress").catch(() => '{}');
  let info = {};
  try { info = JSON.parse(out); } catch { /* no Steam */ }
  const steamPath = info.steamPath || 'C:/Program Files (x86)/Steam';
  const libraries = [path.join(steamPath, 'steamapps')];
  try {
    const vdf = fs.readFileSync(path.join(steamPath, 'steamapps', 'libraryfolders.vdf'), 'utf8');
    for (const match of vdf.matchAll(/"path"\s+"([^"]+)"/g)) libraries.push(path.join(match[1].replace(/\\\\/g, '\\'), 'steamapps'));
  } catch { /* default library only */ }
  let btd6Installed = false;
  for (const library of libraries) {
    try {
      const manifest = fs.readFileSync(path.join(library, `appmanifest_${BTD6_APP_ID}.acf`), 'utf8');
      const flags = Number((manifest.match(/"StateFlags"\s+"(\d+)"/) || [])[1] || 0);
      if (flags & 4) { btd6Installed = true; break; } // 4 = fully installed
    } catch { /* not in this library */ }
  }
  return { steamInstalled: fileExists(path.join(steamPath, 'steam.exe')), steamRunning: !!info.running, steamSignedIn: !!info.running && Number(info.activeUser) > 0, btd6Installed };
}

// ---------- HTTP ----------
function send(res, code, body) {
  res.writeHead(code, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
  res.end(JSON.stringify(body));
}
function handle(req, res, pathname) {
  if (pathname === '/api/setup/status' && req.method === 'GET') {
    getStatus().then(status => send(res, 200, status)).catch(error => send(res, 500, { error: error.message }));
  } else if (pathname === '/api/setup/start' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; if (body.length > 10000) req.destroy(); });
    req.on('end', () => {
      let options = {};
      try { options = body ? JSON.parse(body) : {}; } catch { return send(res, 400, { error: 'Invalid JSON' }); }
      send(res, 202, start({ isoPath: typeof options.isoPath === 'string' && options.isoPath.trim() ? options.isoPath.trim() : null }));
    });
  } else if (pathname === '/api/setup/update' && req.method === 'POST') {
    updateGuest().then(result => send(res, 202, result)).catch(error => send(res, /active|offline|connected|desktop/i.test(error.message) ? 409 : 500, { error: error.message }));
  } else if (pathname === '/api/setup/guest' && req.method === 'GET') {
    guestSteam().then(info => send(res, 200, info)).catch(error => send(res, 500, { error: error.message }));
  } else if (pathname === '/api/setup/launch-game' && req.method === 'POST') {
    if (!isGuest()) return send(res, 403, { error: 'Game launch is available only inside the VM.' });
    guestSteam().then(async info => {
      if (!info.steamSignedIn || !info.btd6Installed) return send(res, 409, { error: 'Sign in to Steam and finish installing BTD6 first.' });
      await powershell("Start-Process 'steam://rungameid/960090'");
      send(res, 202, { starting: true });
    }).catch(error => send(res, 500, { error: error.message }));
  } else send(res, req.method === 'GET' || req.method === 'POST' ? 404 : 405, { error: 'Unknown setup endpoint' });
}

module.exports = { handle, getStatus, start, updateGuest, ensureVmDisplay, guestSteam, isGuest };
