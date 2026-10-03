// Drives BTD6bot (vendored at ./btd6bot — https://github.com/j-miet/BTD6bot) as a second automation
// engine. Unlike AutoBTD6 it runs as one persistent interactive process: `python btd6bot -nogui`
// from its repo root, then commands on stdin (`run <plan>`, `exit`), with its own REPL prompt on
// stdout marking "ready for the next command". Map selection goes through the in-game search box,
// so it doesn't suffer the map-grid drift that AutoBTD6's positional clicking does.
const fs = require('node:fs');
const path = require('node:path');
const { spawn, spawnSync } = require('node:child_process');
const engineLock = require('./engine-lock');
const { pushLog, afterCountdown } = engineLock;
const { mapCatalogOrder, categoryForMapSlug } = require('./automation');

const ROOT = path.join(__dirname, 'btd6bot');
const PACKAGE = path.join(ROOT, 'btd6bot');
const PLANS_DIR = path.join(PACKAGE, 'plans');
const BOT_VARS_PATH = path.join(PACKAGE, 'Files', 'bot_vars.json');
const PROGRESS_PATH = path.join(__dirname, 'btd6bot-progress.json');
const VENV_PYTHON = path.join(ROOT, '.venv', 'Scripts', 'python.exe');
const PROMPT = '[btd6bot]=>';

// In-game unlock order per difficulty: each mode's medal gates the next, so a sweep plays them in
// this order and later modes aren't attempted before the ones that unlock them.
const DIFFICULTY_ORDER = ['Easy', 'Medium', 'Hard'];
const MODE_ORDER = ['Standard', 'Primary', 'Deflation', 'Military', 'Apopalypse', 'Reverse',
  'Magic', 'Double_hp', 'Half_cash', 'Alternate', 'Impoppable', 'Chimps'];

function loadProgress() {
  try { return JSON.parse(fs.readFileSync(PROGRESS_PATH, 'utf8')); }
  catch { return { won: {} }; }
}
function saveProgress(progress) {
  const temporary = `${PROGRESS_PATH}.tmp`;
  fs.writeFileSync(temporary, JSON.stringify(progress, null, 2));
  fs.renameSync(temporary, PROGRESS_PATH);
}

// Mirrors btd6bot/utils/plan_data.py's own return_map/return_strategy exactly: the map is everything
// before the first capital, difficulty runs to the second capital, mode is the rest (an optional
// trailing 2-9 marks an alternate strategy for the same mode).
function parsePlanName(plan) {
  const first = [...plan].findIndex(c => c >= 'A' && c <= 'Z');
  if (first <= 0) return null;
  let second = -1;
  for (let i = first + 1; i < plan.length; i++) if (plan[i] >= 'A' && plan[i] <= 'Z') { second = i; break; }
  if (second === -1) return null;
  let mode = plan.slice(second);
  const variant = /[2-9]$/.test(mode) ? mode.slice(-1) : null;
  if (variant) mode = mode.slice(0, -1);
  const mapSlug = plan.slice(0, first);
  return { plan, mapSlug, map: mapSlug.replace(/_/g, ' '), difficulty: plan.slice(first, second), mode, variant };
}

function planRank(p) {
  const d = DIFFICULTY_ORDER.indexOf(p.difficulty);
  const m = MODE_ORDER.indexOf(p.mode);
  return (d === -1 ? 9 : d) * 100 + (m === -1 ? 50 : m) * 2 + (p.variant ? Number(p.variant) : 0);
}

function listPlans() {
  return fs.readdirSync(PLANS_DIR)
    .filter(f => f.endsWith('.py') && f !== '__init__.py' && f !== '_plan_imports.py')
    .map(f => {
      const p = parsePlanName(f.slice(0, -3));
      if (!p) return null;
      const header = fs.readFileSync(path.join(PLANS_DIR, f), 'utf8').slice(0, 400);
      return { ...p, category: categoryForMapSlug(p.mapSlug) || 'Other', fallbackOf: header.match(/\[Bloons\+ fallback of (.+?)\]/)?.[1] || null };
    })
    .filter(p => p && !p.fallbackOf)
    .sort((a, b) => mapCatalogOrder(a.mapSlug) - mapCatalogOrder(b.mapSlug) || a.map.localeCompare(b.map) || planRank(a) - planRank(b));
}

let runtimeCache = null;
function getRuntime() {
  if (runtimeCache && Date.now() - runtimeCache.checkedAt < 60_000) return runtimeCache;
  if (!fs.existsSync(VENV_PYTHON)) {
    runtimeCache = { available: false, missing: 'its Python 3.12+ environment (btd6bot/.venv)', checkedAt: Date.now() };
    return runtimeCache;
  }
  const probe = "import sys, importlib.util as i; required=['easyocr','pyautogui','pynput','mss','win32gui','numpy','PIL','matplotlib']; missing=[n for n in required if i.find_spec(n) is None]; print('python>=3.12' if sys.version_info < (3,12) else ', '.join(missing))";
  const result = spawnSync(VENV_PYTHON, ['-c', probe], { cwd: ROOT, windowsHide: true, timeout: 15000, encoding: 'utf8' });
  const missing = result.status === 0 ? (result.stdout || '').trim() : 'a working Python';
  runtimeCache = { available: !missing, missing: missing || null, checkedAt: Date.now() };
  return runtimeCache;
}

// BTD6bot's own windowed support: "auto" finds the "BloonsTD6" window and sizes itself from its
// rect, so a windowed game at any position/resolution works without hand-entered coordinates.
// Only the two keys it needs are changed; everything else in their settings file is preserved.
function configureWindowed() {
  const vars = JSON.parse(fs.readFileSync(BOT_VARS_PATH, 'utf8'));
  if (vars.windowed === true && vars.windowed_position === 'auto') return;
  vars.windowed = true;
  vars.windowed_position = 'auto';
  fs.writeFileSync(BOT_VARS_PATH, JSON.stringify(vars, null, 4));
}

function openSession(job) {
  const proc = spawn(VENV_PYTHON, ['btd6bot', '-nogui'], {
    cwd: ROOT, windowsHide: true,
    env: { ...process.env, PYTHONUNBUFFERED: '1', PYTHONIOENCODING: 'utf-8' },
  });
  job.proc = proc;
  let buffer = '';
  let waiter = null;
  const feed = prefix => chunk => {
    const text = chunk.toString('utf8');
    for (const line of text.split(/\r?\n/)) {
      const clean = line.split(PROMPT).join('').trim();
      if (clean) pushLog(job, prefix ? `[${prefix}] ${clean}` : clean);
    }
    if (prefix) return;
    buffer += text;
    if (waiter && buffer.includes(PROMPT)) { const done = waiter; waiter = null; const out = buffer; buffer = ''; done(out); }
  };
  proc.stdout.on('data', feed());
  proc.stderr.on('data', feed('stderr'));
  proc.on('error', error => pushLog(job, `btd6bot process error: ${error.message}`));
  const closed = new Promise(resolve => proc.on('close', code => {
    if (waiter) { const done = waiter; waiter = null; done(null); }
    resolve(code);
  }));
  // Resolves with everything printed since the last prompt, or null if the process died first.
  const untilPrompt = () => new Promise(resolve => {
    if (proc.exitCode != null) return resolve(null);
    if (buffer.includes(PROMPT)) { const out = buffer; buffer = ''; return resolve(out); }
    waiter = resolve;
  });
  const send = line => { if (proc.stdin.writable) proc.stdin.write(`${line}\n`); };
  return { untilPrompt, send, closed };
}

function classify(output) {
  if (output == null) return 'aborted';
  if (output.includes('Plan completed.')) return 'won';
  if (/Hero\/map selection failed|Plan not found|Couldn't initialize bot|Plan file .* doesn't exist/.test(output)) return 'not-found';
  if (/Plan failed\.|Defeat/.test(output)) return 'lost';
  return 'unknown';
}

async function closeSession(job, session) {
  session.send('exit');
  const timeout = new Promise(resolve => setTimeout(() => resolve('timeout'), 10000));
  if (await Promise.race([session.closed, timeout]) === 'timeout') await engineLock.killProcessTree(job.proc);
}

// Runs plans in order in one bot process. A map the game can't find (not unlocked, renamed, or
// removed) skips every remaining plan for that map instead of retrying each mode.
async function runPlans(job, plans) {
  const progress = loadProgress();
  progress.won ||= {};
  const session = openSession(job);
  if (await session.untilPrompt() == null) { pushLog(job, 'btd6bot exited before it was ready'); return; }
  const missingMaps = new Set();
  let index = 0;
  for (const p of plans) {
    index++;
    if (job.stopRequested) return;
    if (missingMaps.has(p.mapSlug)) continue;
    pushLog(job, `[${index}/${plans.length}] ${p.map} — ${p.difficulty} ${p.mode.replace('_', ' ')}${p.fallbackOf ? ' (CHIMPS strategy)' : ''}`);
    session.send(`run ${p.plan}`);
    const result = classify(await session.untilPrompt());
    if (result === 'aborted') return;
    if (result === 'won') {
      progress.won[p.plan] = new Date().toISOString();
      saveProgress(progress);
    } else if (result === 'not-found') {
      missingMaps.add(p.mapSlug);
      pushLog(job, `couldn't find ${p.map} in-game — skipping its remaining plans`);
    }
    pushLog(job, `→ ${result}`);
  }
  await closeSession(job, session);
}

function startJob(type, pickPlans) {
  const busy = engineLock.getCurrentJob();
  if (busy) return { error: `already-running (${busy.engine})` };
  const runtime = getRuntime();
  if (!runtime.available) return { error: `BTD6bot needs ${runtime.missing}` };
  let plans;
  try { configureWindowed(); plans = pickPlans(listPlans()); }
  catch (error) { return { error: error.message }; }
  if (!plans.length) return { error: 'nothing to run' };
  const job = engineLock.beginJob('btd6bot', type);
  if (!job) return { error: 'already-running' };
  job.onEnd = ended => {
    const progress = loadProgress();
    progress.lastRun = { type: ended.type, endedAt: ended.endedAt, log: ended.log.slice(-30) };
    saveProgress(progress);
  };
  afterCountdown(job, () => {
    runPlans(job, plans)
      .catch(error => pushLog(job, `error: ${error.message}`))
      .finally(() => { if (engineLock.getCurrentJob() === job) engineLock.endJob(job); });
  });
  return { ok: true, queued: plans.length };
}

function runPlan(plan) {
  return startJob('plan', plans => plans.filter(p => p.plan === plan));
}

// `maps` (list of map slugs) limits the sweep to those maps; omitted means every map. Plans already
// won in an earlier sweep are skipped, so a stopped or restarted sweep picks up where it left off.
function runBlackBorder({ maps } = {}) {
  const won = loadProgress().won || {};
  const only = Array.isArray(maps) && maps.length ? new Set(maps) : null;
  return startJob(only ? 'black-border-maps' : 'black-border-all',
    plans => plans.filter(p => !won[p.plan] && (!only || only.has(p.mapSlug))));
}

function getStatus() {
  const progress = loadProgress();
  const job = engineLock.getCurrentJob();
  const base = { runtime: getRuntime(), wonCount: Object.keys(progress.won || {}).length };
  if (job?.engine === 'btd6bot') return { ...base, running: true, type: job.type, startedAt: job.startedAt, log: job.log.slice(-30) };
  const previous = engineLock.getLastJob('btd6bot') || progress.lastRun;
  return { ...base, running: false, busyWith: job?.engine || null, type: previous?.type, endedAt: previous?.endedAt, log: previous?.log?.slice(-30) || [] };
}

module.exports = { listPlans, runPlan, runBlackBorder, getStatus };
