const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { execFile } = require('node:child_process');
const { captureWindow } = require('./capture');
const { runScan } = require('./scanner');
const automation = require('./automation');
const engineLock = require('./engine-lock');
const root = __dirname;
const port = Number(process.env.PORT || 4173);
const calibrationFile = path.join(root, 'calibration.json');
const routeLibrary = path.join(root, 'route-library');
fs.mkdirSync(routeLibrary, { recursive: true });
const routeIdentity = route => `${String(route.map || '').toLowerCase().replace(/[^a-z0-9]/g, '')}|${String(route.gamemode || '').toLowerCase().replace(/[^a-z0-9]/g, '')}`;
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png' };
let gameRunning = false;
// Keep the last VM status briefly if the SSH tunnel drops between polls. Falling
// back to the host's idle engine state made the desktop UI report Idle while a
// sweep was still running in the guest.
let lastVmFarmStatus = null;
let lastVmFarmStatusAt = 0;
const { vmFetch, vmPost, vmFetchBuffer } = require('./vm-bridge');
const vmSetup = require('./vm-setup');
const { readSteamAchievements } = require('./steam-progress');
const { readLocalProgress } = require('./btd6-save-progress');
const { readActiveBossEvent } = require('./boss-events');
const bossRoutes = require('./boss-route-generator');
const experimentalAi = require('./experimental-ai');
let aiCollectionPending = false;
async function collectAiObservation() {
  if (aiCollectionPending || (!gameRunning && !engineLock.getCurrentJob())) return;
  aiCollectionPending = true;
  try {
    let state = null;
    const guestData = await vmFetch('/api/game-state', 1200);
    if (guestData) { try { state = JSON.parse(guestData); } catch { /* use local game-state below */ } }
    if (!state?.runId) {
      try { state = JSON.parse(fs.readFileSync(path.join(root, 'autobtd6', 'game-state.json'), 'utf8')); }
      catch { state = null; }
    }
    if (state?.runId) experimentalAi.ingestGameState(state);
  } catch (error) {
    console.warn('Passive AI data collection skipped:', error.message);
  } finally { aiCollectionPending = false; }
}
const setupIntentPath = path.join(process.env.LOCALAPPDATA || root, 'BloonsPlus', 'auto-setup.txt');
let automaticSetupStep = null;
let automaticSetupAttempt = 0;
async function continueInstallerSetup() {
  if (vmSetup.isGuest() || !fs.existsSync(setupIntentPath)) return;
  try {
    const status = await vmSetup.getStatus();
    if (status.allDone || status.job?.running || status.job?.error || !status.next?.button) return;
    const retryConnected = status.next.id === 'connected' && Date.now() - automaticSetupAttempt > 45000;
    if (status.next.id === automaticSetupStep && !retryConnected) return;
    automaticSetupStep = status.next.id;
    automaticSetupAttempt = Date.now();
    const isoPath = fs.readFileSync(setupIntentPath, 'utf8').trim();
    vmSetup.start(isoPath ? { isoPath } : {});
  } catch (error) { console.warn('First-run VM setup:', error.message); }
}
const pendingStartPath = path.join(process.env.LOCALAPPDATA || root, 'BloonsPlus', 'pending-automation.json');
let pendingStart = null;
try { pendingStart = JSON.parse(fs.readFileSync(pendingStartPath, 'utf8')); } catch { /* no queued job */ }
let lastSetupStepId = null;
let lastSetupAttempt = 0;
let pendingDispatch = false;
let lastGameLaunch = 0;
function savePendingStart(value) {
  pendingStart = value;
  if (value) { fs.mkdirSync(path.dirname(pendingStartPath), { recursive: true }); fs.writeFileSync(pendingStartPath, JSON.stringify(value)); }
  else { try { fs.unlinkSync(pendingStartPath); } catch { /* absent */ } }
}
async function dispatchPendingStart() {
  if (!pendingStart || pendingDispatch || vmSetup.isGuest()) return;
  pendingDispatch = true;
  try {
    // A sweep request is also the VM wake-up signal: make the guest display
    // visible and let setup repair/start any missing VM components first.
    vmSetup.ensureVmDisplay().catch(() => {});
    const text = await vmFetch('/api/game-status', 3000);
    let game = null;
    try { game = JSON.parse(text); } catch { /* VM or game unavailable */ }
    if (game?.game) {
      const relayed = await vmPost('/api/farm/start', JSON.stringify(pendingStart.body));
      if (relayed && relayed.status >= 200 && relayed.status < 300) savePendingStart(null);
      return;
    }
    const setup = await vmSetup.getStatus();
    if (!setup.allDone && !setup.job?.running && !setup.job?.error &&
        (setup.next?.id !== lastSetupStepId || (setup.next?.id === 'connected' && Date.now() - lastSetupAttempt > 30000))) {
      lastSetupStepId = setup.next?.id;
      lastSetupAttempt = Date.now();
      vmSetup.start();
    } else if (setup.allDone && Date.now() - lastGameLaunch > 60000) {
      lastGameLaunch = Date.now();
      await vmPost('/api/setup/launch-game', '{}');
    }
  } catch (error) { console.warn('Queued VM start:', error.message); }
  finally { pendingDispatch = false; }
}

async function detectVmGame(callback) {
  const text = await vmFetch('/api/game-status');
  try { callback(text ? { ...JSON.parse(text), vm: true } : null); } catch { callback(null); }
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => { body += chunk; if (body.length > 2_000_000) req.destroy(); });
    req.on('end', () => resolve(body));
    req.on('error', reject);
  });
}

http.createServer((req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, `http://${req.headers.host}`).pathname);
  if (pathname === '/api/boss-event') {
    if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
    readActiveBossEvent().then(result => {
      res.writeHead(result.available ? 200 : 503, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify(result));
    });
    return;
  }
  if (pathname === '/api/boss-route/generate' && req.method === 'POST') {
    readBody(req).then(body => bossRoutes.generate({ elite: JSON.parse(body || '{}').elite === true })
      .then(result => { res.writeHead(result.available ? 200 : 409, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }); res.end(JSON.stringify(result)); }))
      .catch(error => { res.writeHead(500, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ error: error.message })); });
    return;
  }
  // First-run VM setup (the Setup bar); the handlers live in vm-setup.js.
  if (pathname.startsWith('/api/setup/')) return vmSetup.handle(req, res, pathname);
  // Achievement completion/progress read straight from Steam's own local achievement cache (see
  // steam-progress.js) - no OCR of the in-game achievements screen needed. BTD6 actually runs
  // inside the VM, so the VM's own Steam cache is the one that reflects real progress; this host's
  // copy of Steam (if any) is only a last-resort fallback when the VM can't be reached at all.
  if (pathname === '/api/achievements/steam') {
    if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
    vmFetch('/api/achievements/steam').then(vmData => {
      let vmResult = null;
      if (vmData) { try { vmResult = JSON.parse(vmData); } catch { /* fall through to local */ } }
      if (vmResult?.available) {
        res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
        return res.end(JSON.stringify(vmResult));
      }
      let result;
      try { result = readSteamAchievements(); } catch (error) { result = { available: false, reason: error.message }; }
      res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify({ ...result, hostFallback: true, source: result.available ? 'steam-local-host' : result.source }));
    });
    return;
  }
  if (pathname === '/api/progress') {
    if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
    fs.readFile(path.join(root, 'game-observations.json'), 'utf8', (error, data) => {
      const local = error ? JSON.stringify({ error: 'No game observations available' }) : data;
      vmFetch('/api/progress').then(vmData => {
        res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
        res.end(vmData && vmData.trim().startsWith('{') ? vmData : local);
      });
    });
    return;
  }
  if (pathname === '/api/experimental-ai/status') {
    if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    return res.end(JSON.stringify(experimentalAi.status()));
  }
  if (pathname === '/api/experimental-ai/ingest-route') {
    if (req.method !== 'POST') { res.writeHead(405); return res.end(); }
    readBody(req).then(body => {
      const route = JSON.parse(body || '{}');
      const result = experimentalAi.ingestRoute(route);
      res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify({ ok: true, ...experimentalAi.status(), routeId: result.routes.at(-1)?.id || null }));
    }).catch(error => { res.writeHead(400, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ error: error.message })); });
    return;
  }
  if (pathname === '/api/experimental-ai/suggest') {
    if (req.method !== 'POST') { res.writeHead(405); return res.end(); }
    readBody(req).then(body => {
      const context = JSON.parse(body || '{}');
      res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify(experimentalAi.suggest(context)));
    }).catch(error => { res.writeHead(400, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ error: error.message })); });
    return;
  }
  if (pathname === '/api/experimental-ai/decision') {
    if (req.method !== 'POST') { res.writeHead(405); return res.end(); }
    readBody(req).then(body => {
      const result = experimentalAi.recordDecision(JSON.parse(body || '{}'));
      res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(result));
    }).catch(error => { res.writeHead(400, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ error: error.message })); });
    return;
  }
  if (pathname === '/api/progress/local-save') {
    if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
    if (vmSetup.isGuest()) {
      const result = readLocalProgress();
      res.writeHead(result.available ? 200 : 503, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify({ ...result, sourceTransport: 'vm' }));
      return;
    }
    vmFetch('/api/progress/local-save').then(vmData => {
      let result = null;
      if (vmData) { try { result = JSON.parse(vmData); } catch { /* report unavailable below */ } }
      // This endpoint represents the game inside the VM. Never substitute the host's Steam
      // profile: doing so made the desktop show unrelated Monkey Money/medals as VM progress.
      if (result) {
        result = { ...result, source: result.available ? 'vm-profile-save' : (result.source || 'vm-profile-save-unavailable'), sourceTransport: 'vm' };
        res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
        return res.end(JSON.stringify(result));
      }
      res.writeHead(503, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify({ available: false, source: 'vm-unavailable', sourceTransport: 'vm', reason: 'VM profile-save reader is unavailable or the VM connection is offline' }));
    });
    return;
  }
  if (pathname === '/api/route-failures') {
    if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
    const readLocalFailures = () => {
      let failures = [];
      try { failures = JSON.parse(fs.readFileSync(path.join(root, 'route-failures.json'), 'utf8')); } catch { /* none yet */ }
      return failures.slice(-100).reverse().map(f => ({
        at: f.at, map: f.map, gamemode: f.gamemode, route: f.route, reason: f.reason,
        lastRound: f.lastRound, finalRound: f.finalRound, rawRoundOcr: f.rawRoundOcr, livesLeft: f.livesLeft, result: f.result,
        cash: f.cash, screenshot: f.screenshot, observations: f.observations, actions: f.actions,
        // category/actionable (from classifyRouteFailure): whether this is a real bug worth fixing
        // (route-corruption, navigation-bug), just missing diagnostic data (insufficient-data), or an
        // honest gameplay loss that needs a better strategy, not a code fix (gameplay-defeat).
        category: f.category || null, actionable: f.actionable !== false,
        // The notable-filtered summary and the full unfiltered run output - both were being
        // computed by recordRouteFailure and then silently dropped before ever reaching the app.
        log: f.log, fullLog: f.fullLog,
      }));
    };
    if (vmSetup.isGuest()) {
      res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify({ available: true, sourceTransport: 'vm', failures: readLocalFailures() }));
      return;
    }
    // Route failures only happen where the replay actually runs, inside the VM. The host's own
    // route-failures.json (if any exists from earlier local testing) is never a substitute.
    vmFetch('/api/route-failures').then(vmData => {
      let result = null;
      if (vmData) { try { result = JSON.parse(vmData); } catch { /* report unavailable below */ } }
      if (result?.available) {
        res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
        return res.end(JSON.stringify({ ...result, sourceTransport: 'vm' }));
      }
      res.writeHead(503, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify({ available: false, sourceTransport: 'vm', failures: [], reason: 'VM is unavailable or has not recorded any route failures yet' }));
    });
    return;
  }
  if (pathname === '/api/upgrade-memory') {
    if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
    const localUpgradeMemory = () => new Promise(resolve => fs.readFile(path.join(root, 'autobtd6', 'upgrade-memory.json'), 'utf8',
      (error, data) => resolve(error ? JSON.stringify({ runs: {} }) : data)));
    vmFetch('/api/upgrade-memory').then(async vmData => {
      let payload = null;
      if (vmData) { try { const parsed = JSON.parse(vmData); if (parsed && parsed.runs && typeof parsed.runs === 'object') payload = JSON.stringify(parsed); } catch { /* use host ledger */ } }
      if (!payload) payload = await localUpgradeMemory();
      res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(payload);
    });
    return;
  }
  if (pathname === '/api/tower-upgrade-catalog') {
    if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
    const file = path.join(root, 'btd6bot', 'btd6bot', 'Files', 'upgrades_current.json');
    fs.readFile(file, 'utf8', (error, data) => {
      if (error) {
        res.writeHead(404, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
        return res.end(JSON.stringify({ error: 'upgrade catalog unavailable' }));
      }
      try {
        const catalog = JSON.parse(data);
        // Supplement the bundled older tower catalog with newer public upgrade names.
        // Kept in a separate file so upstream catalog updates remain easy to merge.
        const overrides = JSON.parse(fs.readFileSync(path.join(root, 'tower-upgrade-overrides.json'), 'utf8'));
        Object.assign(catalog, overrides);
        res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
        res.end(JSON.stringify(catalog));
      } catch (parseError) {
        res.writeHead(500, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
        res.end(JSON.stringify({ error: `tower upgrade catalog invalid: ${parseError.message}` }));
      }
    });
    return;
  }
  if (pathname === '/api/game-state') {
    if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
    fs.readFile(path.join(root, 'autobtd6', 'game-state.json'), 'utf8', (error, data) => {
      const local = error ? null : data;
      vmFetch('/api/game-state').then(vmData => {
        res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
        res.end(vmData && vmData.trim().startsWith('{') ? vmData : (local || JSON.stringify({ state: null })));
      });
    });
    return;
  }
  if (pathname === '/api/game-status') {
    if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
    if (process.platform !== 'win32') {
      res.writeHead(501); return res.end('Windows is required for game detection');
    }
    execFile('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', "$game = Get-Process -Name BloonsTD6,BloonsTD6-Epic -ErrorAction SilentlyContinue | Select-Object -First 1; $automation = Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'replay[.]py' } | Select-Object -First 1; @{ running = [bool]$game -or [bool]$automation; game = [bool]$game; automation = [bool]$automation; vm = $false } | ConvertTo-Json -Compress"], { windowsHide: true, timeout: 7000 }, (error, stdout) => {
      if (!error) { try { const local = JSON.parse(stdout.trim()); gameRunning = local.running === true; if (gameRunning) { res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }); return res.end(JSON.stringify(local)); } } catch { /* try VM */ } }
      detectVmGame(vm => {
        if (vm) { gameRunning = vm.running === true; res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }); return res.end(JSON.stringify(vm)); }
        res.writeHead(503, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
        res.end(JSON.stringify({ error: 'BTD6 was not found locally or in the VM', running: false }));
      });
    });
    return;
  }
  if (pathname === '/api/capture') {
    if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
    captureWindow().then(result => {
      res.writeHead(200, { 'Content-Type': 'image/png', 'Cache-Control': 'no-store' });
      res.end(result.png);
    }).catch(error => {
      res.writeHead(503, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify({ error: error.message }));
    });
    return;
  }
  if (pathname === '/api/calibration') {
    if (req.method === 'GET') {
      fs.readFile(calibrationFile, 'utf8', (error, data) => {
        res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
        res.end(error ? JSON.stringify({}) : data);
      });
      return;
    }
    if (req.method === 'POST') {
      readBody(req).then(body => {
        JSON.parse(body); // validate before writing
        fs.writeFileSync(calibrationFile, body);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true }));
      }).catch(() => { res.writeHead(400); res.end(JSON.stringify({ error: 'Invalid calibration JSON' })); });
      return;
    }
    res.writeHead(405); return res.end();
  }
  if (pathname === '/api/playthroughs') {
    if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
    try {
      const resolution = new URL(req.url, `http://${req.headers.host}`).searchParams.get('resolution');
      const list = automation.listPlaythroughs(resolution || undefined);
      res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify(list));
    } catch (error) {
      res.writeHead(503, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: error.message }));
    }
    return;
  }
  if (pathname === '/api/playthroughs/content') {
    const file = new URL(req.url, `http://${req.headers.host}`).searchParams.get('file');
    if (req.method === 'GET') {
      try {
        res.writeHead(200, { 'Content-Type': 'text/plain', 'Cache-Control': 'no-store' });
        res.end(automation.getPlaythroughContent(file));
      } catch (error) {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
      }
      return;
    }
    if (req.method === 'PUT' || req.method === 'POST') {
      readBody(req).then(content => {
        const result = automation.savePlaythroughContent(file, content);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(result));
      }).catch(error => { res.writeHead(400, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ error: error.message })); });
      return;
    }
    res.writeHead(405); return res.end();
  }
  if (pathname === '/api/routes') {
    if (req.method === 'GET') {
      const loaded = fs.readdirSync(routeLibrary).filter(name => name.endsWith('.json')).map(name => {
        try { return JSON.parse(fs.readFileSync(path.join(routeLibrary, name), 'utf8')); } catch { return null; }
      }).filter(Boolean);
      const byIdentity = new Map();
      for (const route of loaded) {
        const key = routeIdentity(route), previous = byIdentity.get(key);
        const score = item => (Array.isArray(item.actions) ? item.actions.length : 0) * 1e12 + (Date.parse(item.updatedAt) || 0);
        if (!previous || score(route) > score(previous)) byIdentity.set(key, route);
      }
      const routes = [...byIdentity.values()];
      res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify(routes));
      return;
    }
    if (req.method === 'POST') {
      readBody(req).then(body => {
        const route = JSON.parse(body);
        if (!route.name || !route.map || !route.gamemode || !Array.isArray(route.actions)) throw new Error('Route needs name, map, gamemode, and actions');
        const safe = String(route.name).toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/^-|-$/g, '') || `route-${Date.now()}`;
        const duplicate = fs.readdirSync(routeLibrary).filter(name => name.endsWith('.json')).map(name => {
          try { return { file: name, route: JSON.parse(fs.readFileSync(path.join(routeLibrary, name), 'utf8')) }; } catch { return null; }
        }).filter(item => item?.route && routeIdentity(item.route) === routeIdentity(route) && item.file !== `${safe}.json`)[0];
        if (duplicate) throw new Error(`A route already exists for ${route.map} · ${route.gamemode}: ${duplicate.route.name || duplicate.file}`);
        const saved = { ...route, format: 1, updatedAt: new Date().toISOString() };
        fs.writeFileSync(path.join(routeLibrary, `${safe}.json`), JSON.stringify(saved, null, 2));
        res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(saved));
      }).catch(error => { res.writeHead(400); res.end(JSON.stringify({ error: error.message })); });
      return;
    }
    res.writeHead(405); return res.end();
  }
  if (pathname === '/api/routes/export') {
    if (req.method !== 'POST') { res.writeHead(405); return res.end(); }
    readBody(req).then(body => {
      const route = JSON.parse(body);
      res.writeHead(200, { 'Content-Type': 'application/json', 'Content-Disposition': 'attachment; filename="bloons-plus-route.json"' });
      res.end(JSON.stringify(route, null, 2));
    }).catch(() => { res.writeHead(400); res.end(JSON.stringify({ error: 'Invalid route JSON' })); });
    return;
  }
  if (pathname === '/api/playthrough-combos') {
    if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
    automation.getAvailableCombos().then(combos => {
      res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify(combos));
    }).catch(error => {
      res.writeHead(503, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: error.message }));
    });
    return;
  }
  if (pathname === '/api/map-order') {
    if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
    fs.readFile(path.join(root, 'map-order.json'), 'utf8', (error, data) => {
      res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(error ? JSON.stringify({ maps: {}, updatedAt: null }) : data);
    });
    return;
  }
  if (pathname === '/api/map-selection') {
    if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
    captureWindow().then(async result => {
      const { scanMapPage, currentPage } = require('./map-order-scanner');
      const { readPng } = require('./pixels');
      const scanBuffer = result.png;
      const indicator = currentPage(readPng(scanBuffer));
      const page = indicator ? await scanMapPage(scanBuffer) : null;
      if (!indicator) {
        const image = readPng(scanBuffer);
        const tab = image.get(Math.round(image.width * 0.43), Math.round(image.height * 0.92));
        let greenPixels = 0;
        for (let y = Math.round(image.height * 0.72); y < Math.round(image.height * 0.98); y += 4) {
          for (let x = Math.round(image.width * 0.42); x < Math.round(image.width * 0.58); x += 4) {
            const [r, g, b] = image.get(x, y);
            if (g > 170 && g > r * 1.25 && g > b * 1.15) greenPixels++;
          }
        }
        const greenPlay = greenPixels > 80;
        const blueTabs = tab[2] > 130 && tab[2] > tab[0] * 1.3 && tab[2] > tab[1] * 1.05;
        // The route tool only polls while preparing a map route. Any non-menu
        // BTD6 screen is therefore treated as the map-selection handoff until
        // the page indicator becomes readable.
        const screen = greenPlay ? 'STARTMENU' : (blueTabs ? 'MAP_SELECTION' : 'MAP_SELECTION');
        res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
        res.end(JSON.stringify({ screen, page: null, category: null, candidates: [] }));
        return;
      }
      if (indicator && (!page || !Number.isInteger(page.page))) {
        res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
        res.end(JSON.stringify({ page: indicator.index, indicatorCount: indicator.count, category: null, candidates: [] }));
        return;
      }
      res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify(page || { page: null, category: null, candidates: [] }));
    }).catch(error => { res.writeHead(503, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ error: error.message })); });
    return;
  }
  // With the VM up, automation runs there (the game is there); the host only relays.
  if (pathname === '/api/farm/start' || pathname === '/api/farm/stop' || pathname === '/api/farm/pause' || pathname === '/api/farm/stop-after') {
    if (req.method !== 'POST') { res.writeHead(405); return res.end(); }
    readBody(req).then(async body => {
      if (!vmSetup.isGuest()) {
        if (pathname === '/api/farm/stop' && pendingStart) {
          savePendingStart(null);
          res.writeHead(200, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ stopped: true, queued: false }));
        }
        if (pathname === '/api/farm/start') {
          const request = body ? JSON.parse(body) : {};
          const remote = await vmFetch('/api/game-status', 3000);
          let game = null;
          try { game = JSON.parse(remote); } catch { /* VM unavailable */ }
          if (!game?.game) {
            savePendingStart({ body: request, createdAt: new Date().toISOString() });
            lastSetupStepId = null;
            dispatchPendingStart();
            res.writeHead(202, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify({ queued: true, message: 'VM setup or game startup is in progress. This run will start when BTD6 is ready.' }));
          }
        }
      }
      const vmUp = !automation.getStatus().running && (await vmFetch('/api/game-status', 3000)) !== null;
      if (vmUp) {
        const relayed = await vmPost(pathname, body || '{}');
        if (relayed) { res.writeHead(relayed.status, { 'Content-Type': 'application/json' }); return res.end(relayed.text); }
      }
      if (!vmSetup.isGuest()) {
        if (pathname === '/api/farm/start') {
          savePendingStart({ body: body ? JSON.parse(body) : {}, createdAt: new Date().toISOString() });
          lastSetupStepId = null;
          dispatchPendingStart();
          res.writeHead(202, { 'Content-Type': 'application/json' });
          return res.end(JSON.stringify({ queued: true, message: 'VM connection lost. Run queued until the VM is ready.' }));
        }
        res.writeHead(503, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ error: 'Could not reach the VM to stop the active run.' }));
      }
      const result = pathname === '/api/farm/start'
        ? automation.startFarm(body ? JSON.parse(body) : {})
        : pathname === '/api/farm/pause' ? automation.togglePause()
        : pathname === '/api/farm/stop-after' ? automation.stopAfterReplay()
        : await automation.stopFarm();
      res.writeHead(result.error ? 409 : 200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result));
    }).catch(() => { res.writeHead(400); res.end(JSON.stringify({ error: 'Invalid request body' })); });
    return;
  }
  if (pathname === '/api/farm/status') {
    if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
    const local = automation.getStatus();
    vmFetch('/api/farm/status').then(text => {
      let remote = null;
      if (text) { try { remote = JSON.parse(text); } catch {} }
      // When the VM API responds it is authoritative even when idle. Requiring
      // remote.running here let an unrelated stale host job override the VM's
      // live status, logs, and queue state on the main PC.
      let result;
      if (remote && typeof remote === 'object' && typeof remote.running === 'boolean') {
        lastVmFarmStatus = remote;
        lastVmFarmStatusAt = Date.now();
        result = { ...remote, vm: true, statusStale: false };
      } else if (lastVmFarmStatus?.running && Date.now() - lastVmFarmStatusAt < 90_000) {
        result = { ...lastVmFarmStatus, vm: true, statusStale: true,
          statusAgeMs: Date.now() - lastVmFarmStatusAt,
          log: [...(lastVmFarmStatus.log || []), 'VM status bridge is reconnecting; showing the last confirmed active run.'] };
      } else if (!vmSetup.isGuest()) {
        // Unknown is safer and clearer than reporting the host's idle state while
        // the VM cannot be reached. Keep start controls locked until status returns.
        result = { ...local, vm: true, statusUnavailable: true, busyWith: local.busyWith || 'VM status unavailable' };
      } else {
        result = { ...local, vm: false };
      }
      if (pendingStart && !result.running) {
        result.queued = true;
        result.type = pendingStart.body?.type || null;
        result.log = [...(result.log || []), 'Waiting for the VM and BTD6 to become ready; setup starts automatically.'];
      }
      res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify(result));
    });
    return;
  }
  if (pathname === '/api/heroes') {
    if (req.method === 'GET') {
      try {
        res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
        res.end(JSON.stringify(automation.getHeroes()));
      } catch (error) { res.writeHead(503); res.end(JSON.stringify({ error: error.message })); }
      return;
    }
    if (req.method === 'POST') {
      readBody(req).then(body => {
        const parsed = JSON.parse(body);
        const heroes = automation.setHeroes(parsed.heros || parsed);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(heroes));
      }).catch(() => { res.writeHead(400); res.end(JSON.stringify({ error: 'Invalid heroes JSON' })); });
      return;
    }
    res.writeHead(405); return res.end();
  }
  const requested = pathname === '/' ? 'index.html' : pathname.replace(/^\/+/, '');
  const file = path.resolve(root, requested);
  if (!file.startsWith(root + path.sep) && file !== path.join(root, 'index.html')) {
    res.writeHead(403); return res.end('Forbidden');
  }
  fs.readFile(file, async (error, data) => {
    // Map thumbnails are cut in the VM (where the game runs); copy any the host lacks on first use.
    if (error && /^(map-icons|tower-icons)\/[a-z0-9-]+\.png$/.test(requested)) {
      const fetched = await vmFetchBuffer(`/${requested}`);
      if (fetched) {
        fs.mkdirSync(path.dirname(file), { recursive: true });
        fs.writeFile(file, fetched, () => {});
        data = fetched; error = null;
      }
    }
    if (error) { res.writeHead(404); return res.end('Not found'); }
    res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    res.end(data);
  });
}).listen(port, '127.0.0.1', () => {
  console.log(`BTD6 Companion ready at http://127.0.0.1:${port}`);
  // Passive strategy collection runs while the game is active. It reads only the
  // automation's observed game-state ledger; it never captures extra screenshots,
  // sends input, or modifies BTD6 files.
  setInterval(collectAiObservation, 2000).unref();
  // The desktop installer records the user's checked "set up VM" choice. Only
  // that explicit first-run choice starts downloads/UAC automatically.
  setTimeout(continueInstallerSetup, 1500);
  setInterval(continueInstallerSetup, 15000).unref();
  // Only the process that owns the port may resume. The replay validates its
  // saved route, in-game screen, and round before sending any game input.
  setTimeout(() => automation.resumePendingReplay(), 8000);
  if (pendingStart && !vmSetup.isGuest()) dispatchPendingStart();
  setInterval(dispatchPendingStart, 8000).unref();
  // Keep the VM display available for the desktop controller. App Sandbox can
  // leave a running VM headless after a reboot, which makes the bridge appear
  // disconnected even though the guest is healthy.
  if (!vmSetup.isGuest()) setInterval(() => vmSetup.ensureVmDisplay().catch(() => {}), 15000).unref();
  // Only the instance that owns the port scans; a second copy must not write observations too.
  // Every 10 s, or every 3 s while the main menu is up (level, XP and Monkey Money live there). While
  // a job drives the game the scan stays read-only on the main menu so it never races the job's saves.
  const scheduleScan = delay => setTimeout(async () => {
    let screen = null;
    if (gameRunning) {
      try { ({ screen } = await runScan({ menuOnly: !!engineLock.getCurrentJob() })); }
      catch (error) { console.warn('Scan failed:', error.message); }
    }
    scheduleScan(screen === 'mainMenu' ? 3000 : 10000);
  }, delay);
  scheduleScan(3000);
}).on('error', error => {
  if (error.code === 'EADDRINUSE') console.error(`Port ${port} is already in use — is Bloons+ already running?`);
  else console.error('Server failed to start:', error.message);
  process.exitCode = 1;
});
