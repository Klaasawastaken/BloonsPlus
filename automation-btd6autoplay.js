// Drives btd6_autoplay (vendored at ./btd6autoplay — https://github.com/Jazzmoon/btd6_autoplay), a Rust
// binary, as a third engine. Deliberately thin: it isn't built here (cargo + MSYS2 Tesseract setup
// per its README is a separate step), and it only ships configs for two maps.
//
// Two real limits read from its source, not the README:
//  - It never navigates menus. It plays whatever map BTD6 is already sitting on (pre-round screen),
//    so a multi-map sweep has to hand each map over to the player to open first.
//  - It picks its config folder from the game window's *outer* size (`./config/{w}x{h}`, from xcap).
//    A windowed game adds a title bar and borders, so that folder doesn't exist and it panics —
//    that's why it's documented as fullscreen-only. Fixed below in config space, no Rust rebuild:
//    read the geometry it reports itself, measure how far the client area is inset, and write a
//    shifted copy of the real-resolution config under the folder name it's looking for.
const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');
const engineLock = require('./engine-lock');
const { pushLog, afterCountdown } = engineLock;
const { getClientGeometry } = require('./capture');
const { mapCatalogOrder, categoryForMapSlug } = require('./automation');

const ROOT = path.join(__dirname, 'btd6autoplay');
const CONFIG_DIR = path.join(ROOT, 'config');
const BINARY = path.join(ROOT, 'target', 'release', 'btd6_autoplay.exe');
const GENERATED_NOTE = 'GENERATED-BY-BLOONS-PLUS.txt';
const HANDOFF_SECONDS = 20;

// Mirrors src/utils/parsing.rs map_config_name_to_map_name: "DarkCastle.yaml" -> "Dark Castle".
function mapNameFromFile(file) {
  let name = '';
  for (const [index, c] of [...file].entries()) {
    if (c === '.') break;
    if (c === '-') { name += ' '; continue; }
    if (index !== 0 && c >= 'A' && c <= 'Z') name += ' ';
    name += c;
  }
  return name;
}

// Resolution folders it actually ships (not ones generated for windowed mode).
function realResolutions() {
  if (!fs.existsSync(CONFIG_DIR)) return [];
  return fs.readdirSync(CONFIG_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory() && /^\d+x\d+$/.test(d.name) && !fs.existsSync(path.join(CONFIG_DIR, d.name, GENERATED_NOTE)))
    .map(d => d.name);
}

// Difficulty keys sit at column 0, gamemode keys are their direct children. Indent width varies
// between the shipped files (2 spaces in 1080p, 4 in 1440p), so it's taken from the first nested
// key under each difficulty rather than assumed; `round_counter_mode` is the only top-level scalar.
function combosInConfig(text) {
  const combos = [];
  let difficulty = null;
  let childIndent = null;
  for (const line of text.split(/\r?\n/)) {
    const top = line.match(/^([a-z_]+):\s*$/);
    if (top) { difficulty = top[1]; childIndent = null; continue; }
    const nested = line.match(/^( +)([a-z_]+):\s*$/);
    if (!nested || !difficulty) continue;
    childIndent ??= nested[1].length;
    if (nested[1].length === childIndent) combos.push({ difficulty, gamemode: nested[2] });
  }
  return combos;
}

function listMaps() {
  const seen = new Map();
  for (const resolution of realResolutions()) {
    const dir = path.join(CONFIG_DIR, resolution, 'maps');
    if (!fs.existsSync(dir)) continue;
    for (const file of fs.readdirSync(dir).filter(f => f.endsWith('.yaml'))) {
      const map = mapNameFromFile(file);
      for (const combo of combosInConfig(fs.readFileSync(path.join(dir, file), 'utf8'))) {
        const key = `${map}|${combo.difficulty}|${combo.gamemode}`;
        if (!seen.has(key)) seen.set(key, { map, file, category: categoryForMapSlug(map) || 'Other', ...combo, resolutions: [] });
        seen.get(key).resolutions.push(resolution);
      }
    }
  }
  return [...seen.values()].sort((a, b) => mapCatalogOrder(a.map) - mapCatalogOrder(b.map) || a.map.localeCompare(b.map));
}

function getRuntime() {
  return fs.existsSync(BINARY)
    ? { available: true, missing: null }
    : { available: false, missing: 'a built btd6_autoplay.exe (cargo build --release — see btd6autoplay/README.md)' };
}

const COORDINATE_ACTION = /("(?:[^"]*?\s)?(?:place \S+ \S+|ability|click|hover|obstacle|clear)\s+)(-?\d+)\s+(-?\d+)(")/g;
function shiftConfigText(text, dx, dy) {
  return text
    .replace(/^(\s*x:\s*)(-?\d+)/gm, (_, key, v) => `${key}${Number(v) + dx}`)
    .replace(/^(\s*y:\s*)(-?\d+)/gm, (_, key, v) => `${key}${Number(v) + dy}`)
    .replace(COORDINATE_ACTION, (_, head, x, y, tail) => `${head}${Number(x) + dx} ${Number(y) + dy}${tail}`);
}

// Writes config/{outerW}x{outerH} as the client-resolution config shifted by the client inset.
async function writeWindowedConfig(job, outer) {
  const client = await getClientGeometry();
  const source = path.join(CONFIG_DIR, `${client.width}x${client.height}`);
  if (!fs.existsSync(source)) throw new Error(`no shipped config for the game's ${client.width}x${client.height} content size`);
  const dx = client.x - outer.x, dy = client.y - outer.y;
  if (dx < 0 || dy < 0 || dx > 64 || dy > 128) throw new Error(`unexpected window inset ${dx},${dy} — not generating a config`);
  const target = path.join(CONFIG_DIR, `${outer.width}x${outer.height}`);
  fs.mkdirSync(path.join(target, 'maps'), { recursive: true });
  for (const rel of ['Settings.yaml', ...fs.readdirSync(path.join(source, 'maps')).map(f => path.join('maps', f))]) {
    fs.writeFileSync(path.join(target, rel), shiftConfigText(fs.readFileSync(path.join(source, rel), 'utf8'), dx, dy));
  }
  fs.writeFileSync(path.join(target, GENERATED_NOTE), `Shifted copy of ${client.width}x${client.height} by (${dx}, ${dy}) for windowed BTD6. Safe to delete.\n`);
  pushLog(job, `windowed mode: generated config ${outer.width}x${outer.height} (content inset ${dx},${dy})`);
}

function runOnce(job, combo) {
  return new Promise(resolve => {
    const proc = spawn(BINARY, ['--map', combo.map, '--difficulty', combo.difficulty, '--gamemode', combo.gamemode,
      '--number', '1', '--sleep', '0', '--log-level', 'info'], { cwd: ROOT, windowsHide: true });
    job.proc = proc;
    let output = '';
    const feed = prefix => chunk => {
      const text = chunk.toString('utf8');
      output += text;
      text.split(/\r?\n/).filter(Boolean).forEach(line => pushLog(job, prefix ? `[${prefix}] ${line}` : line));
    };
    proc.stdout.on('data', feed());
    proc.stderr.on('data', feed('stderr'));
    proc.on('error', error => { pushLog(job, `btd6_autoplay error: ${error.message}`); resolve({ code: null, output }); });
    proc.on('close', code => resolve({ code, output }));
  });
}

async function playCombo(job, combo) {
  let { code, output } = await runOnce(job, combo);
  const geometry = output.match(/Detected window geometry: x=(-?\d+), y=(-?\d+), width=(\d+), height=(\d+)/);
  if (!job.stopRequested && /directory does not exist/.test(output) && geometry) {
    const [, x, y, width, height] = geometry.map(Number);
    try {
      await writeWindowedConfig(job, { x, y, width, height });
      ({ code, output } = await runOnce(job, combo));
    } catch (error) { pushLog(job, `windowed mode: ${error.message}`); }
  }
  if (output.includes('The player has won')) return 'won';
  if (output.includes('The player has lost')) return 'lost';
  return code === 0 ? 'finished' : 'failed';
}

function waitWithStop(job, seconds) {
  return new Promise(resolve => {
    const tick = () => {
      if (job.stopRequested || seconds <= 0) return resolve();
      if (seconds % 5 === 0) pushLog(job, `starting in ${seconds}s...`);
      seconds--;
      setTimeout(tick, 1000);
    };
    tick();
  });
}

async function playCombos(job, combos) {
  for (const [i, combo] of combos.entries()) {
    if (job.stopRequested) return;
    if (combos.length > 1) {
      pushLog(job, `[${i + 1}/${combos.length}] open ${combo.map} — ${combo.difficulty} ${combo.gamemode} in BTD6 (pre-round screen); btd6_autoplay can't select maps itself`);
      await waitWithStop(job, HANDOFF_SECONDS);
      if (job.stopRequested) return;
    }
    pushLog(job, `→ ${await playCombo(job, combo)}`);
  }
}

function startJob(type, combos) {
  const busy = engineLock.getCurrentJob();
  if (busy) return { error: `already-running (${busy.engine})` };
  const runtime = getRuntime();
  if (!runtime.available) return { error: `btd6_autoplay needs ${runtime.missing}` };
  if (!combos.length) return { error: 'nothing to run' };
  const job = engineLock.beginJob('btd6autoplay', type);
  if (!job) return { error: 'already-running' };
  afterCountdown(job, () => {
    playCombos(job, combos)
      .catch(error => pushLog(job, `error: ${error.message}`))
      .finally(() => { if (engineLock.getCurrentJob() === job) engineLock.endJob(job); });
  });
  return { ok: true, queued: combos.length };
}

function runMap({ map, difficulty, gamemode }) {
  return startJob('map', listMaps().filter(c => c.map === map && c.difficulty === difficulty && c.gamemode === gamemode));
}

// Every configured map/difficulty/gamemode in in-game map order. Maps without a config simply
// aren't in the list, so they're skipped by construction.
function runBlackBorder({ maps } = {}) {
  const only = Array.isArray(maps) && maps.length ? new Set(maps) : null;
  return startJob(only ? 'black-border-maps' : 'black-border-all', listMaps().filter(c => !only || only.has(c.map)));
}

function getStatus() {
  const job = engineLock.getCurrentJob();
  const base = { runtime: getRuntime() };
  if (job?.engine === 'btd6autoplay') return { ...base, running: true, type: job.type, startedAt: job.startedAt, log: job.log.slice(-30) };
  const previous = engineLock.getLastJob('btd6autoplay');
  return { ...base, running: false, busyWith: job?.engine || null, type: previous?.type, endedAt: previous?.endedAt, log: previous?.log?.slice(-30) || [] };
}

module.exports = { listMaps, runMap, runBlackBorder, getStatus, shiftConfigText };
