const PROJECT_ROOT = require('node:path').resolve(__dirname, '..');
// Drives AutoBTD6 (vendored at ./autobtd6 â€” https://github.com/ANRAR4/AutoBTD6) as the real
// gameplay/map-completion engine instead of reimplementing tower-placement AI: it ships recorded
// playthroughs (exact click/placement sequences) for 70+ maps across every difficulty, including
// a full set at 2560x1440, plus built-in xp/mm farming modes. This module just orchestrates it â€”
// one job (a spawned `py replay.py ...`, or the achievements-sweep loop below) runs at a time,
// mirroring the "only one thing can drive the mouse/keyboard at once" reality already implicit
// in input.js/capture.js.
const fs = require('node:fs');
const path = require('node:path');
const { spawn, spawnSync } = require('node:child_process');
const { createHash } = require('node:crypto');
const engineLock = require('./engine-lock');
const { pushLog, afterCountdown, killProcessTree } = engineLock;
const { createLineReader, createReplayMonitor, canAttempt } = require('./replay-monitor');
const { recordMedalGain } = require('./scanner');
const { readLocalProgress, medalsFromMapRecord } = require('./btd6-save-progress');
const { getMapMechanics } = require('./map-mechanics');

function ensureOutcomeCount(job, outcome) {
  if (!job || !['victory', 'defeat'].includes(outcome) || job.lastOutcome === outcome) return;
  const key = outcome === 'victory' ? 'victories' : 'defeats';
  job[key] = (job[key] || 0) + 1;
  job.lastOutcome = outcome;
}

const AUTOBTD6_DIR = path.join(PROJECT_ROOT, 'autobtd6');
const PLAYTHROUGHS_DIR = path.join(AUTOBTD6_DIR, 'playthroughs');
const USERCONFIG_PATH = path.join(AUTOBTD6_DIR, 'userconfig.json');
const MAPS_PATH = path.join(AUTOBTD6_DIR, 'maps.json');
const PROGRESS_PATH = path.join(PROJECT_ROOT, 'automation-progress.json');
const ROUTE_VERIFICATION_PATH = path.join(PROJECT_ROOT, 'route-verification.json');
const ONLINE_GUIDE_SOURCES_PATH = path.join(PROJECT_ROOT, 'route-library', 'metadata', 'online-guide-sources.json');
const STATS_PATH = path.join(AUTOBTD6_DIR, 'playthrough_stats.json');
const ROUTE_CHECKPOINT_PATH = path.join(AUTOBTD6_DIR, 'route-checkpoint.json');
const MODE_ATTEMPTS_KEY = 'blackBorderRouteAttempts';
// The project policy only reuses CHIMPS recordings for the three standard medal modes.
// Impoppable has different cash/MK rules and must use a dedicated or locally verified route.
const CHIMPS_REUSE_MODES = ['easy', 'medium', 'hard', 'impoppable'];
// Hard's economy (starting cash, lives) is strictly tighter than Easy/Medium's, with no other
// restrictions added, so a route that wins Hard wins Easy/Medium too. Only a fallback: a map's own
// native Easy/Medium route (or a CHIMPS-reused one) still sorts first via the trust() comparator.
const HARD_REUSE_MODES = ['easy', 'medium'];
const REUSE_MODES_BY_SOURCE = { chimps: CHIMPS_REUSE_MODES, hard: HARD_REUSE_MODES };

function loadProgress() {
  try { return JSON.parse(fs.readFileSync(PROGRESS_PATH, 'utf8')); }
  catch { return { achievementsSweep: { completedFiles: [] } }; }
}
function saveProgress(progress) {
  const temporary = `${PROGRESS_PATH}.tmp`;
  fs.writeFileSync(temporary, JSON.stringify(progress, null, 2));
  fs.renameSync(temporary, PROGRESS_PATH);
}
function loadRouteCheckpoint() {
  try { return JSON.parse(fs.readFileSync(ROUTE_CHECKPOINT_PATH, 'utf8')); }
  catch { return null; }
}
function saveRouteCheckpoint(checkpoint) {
  const temporary = `${ROUTE_CHECKPOINT_PATH}.tmp`;
  fs.writeFileSync(temporary, JSON.stringify(checkpoint, null, 2));
  fs.renameSync(temporary, ROUTE_CHECKPOINT_PATH);
}

let runtimeCache = null;
function runtimeEnvironment() {
  const localAhk = path.join(PROJECT_ROOT, '.venv', 'Scripts', 'AutoHotkey.exe');
  // replay.py runs small Node helpers (hero and map-tile OCR). An installed Bloons+ has no separate
  // Node, so hand it this process's own runtime; Electron acts as plain Node with ELECTRON_RUN_AS_NODE.
  const nodeRuntime = process.versions.electron ? { BLOONS_NODE: process.execPath, ELECTRON_RUN_AS_NODE: '1' } : { BLOONS_NODE: process.execPath };
  return { ...process.env, ...nodeRuntime, PYTHONUNBUFFERED: '1', TF_CPP_MIN_LOG_LEVEL: '2', AHK_PATH: fs.existsSync(localAhk) ? localAhk : process.env.AHK_PATH };
}
function getRuntime() {
  if (runtimeCache && Date.now() - runtimeCache.checkedAt < 60_000) return runtimeCache;
  // Import the native packages as well as locating them. A package can be present while its Windows
  // runtime DLLs are missing; find_spec() alone reported that broken environment as ready.
  const probeCode = "import importlib; required=['ahk','keyboard','cv2','pyautogui','keras','tensorflow']; missing=[]\nfor name in required:\n try: importlib.import_module(name)\n except Exception as error: missing.append(name + ': ' + str(error).splitlines()[-1])\nprint(' | '.join(missing))";
  const candidates = [process.env.BLOONS_PYTHON, path.join(PROJECT_ROOT, '.venv', 'Scripts', 'python.exe'), 'py', 'python'].filter(Boolean);
  let missing = 'Python runtime';
  let executable = null;
  for (const candidate of candidates) {
    const probe = spawnSync(candidate, ['-c', probeCode], { cwd: AUTOBTD6_DIR, windowsHide: true, timeout: 10000, encoding: 'utf8', env: runtimeEnvironment() });
    if (probe.status !== 0) continue;
    missing = (probe.stdout || '').trim();
    executable = candidate;
    if (!missing) break;
  }
  runtimeCache = { available: !!executable && !missing, missing: missing || null, executable, checkedAt: Date.now() };
  return runtimeCache;
}

function parsePlaythroughFile(file) {
  const parts = file.replace(/\.btd6$/, '').split('#');
  // boss-route-generator.js names its output {bossType}#{normal|elite}#{map}#event-{id} â€”
  // a different shape from every other route's {map}#{gamemode}#{resolution}#{flags}.
  // Misreading a boss file with the standard split derives a fake map slug (the boss's
  // name) and made isMapUnlocked() reject it as "map not unlocked yet" even when the
  // real target map is unlocked; detect it up front instead.
  const isBossRoute = parts.slice(3).some(part => part.startsWith('event-'));
  if (isBossRoute) {
    const [bossType, bossVariant, map] = parts;
    return { file, isBossRoute: true, bossType, bossVariant, mapSlug: map, map: map.replace(/_/g, ' '),
      gamemodeSlug: bossVariant, gamemode: bossVariant, resolution: null, flags: parts.slice(3),
      generated: false, converted: false, generatedSourceGamemode: null };
  }
  const [map, gamemode, resolution, ...flags] = parts;
  const sourceFlag = flags.find(flag => flag.startsWith('source_'));
  return { file, isBossRoute: false, mapSlug: map, map: map.replace(/_/g, ' '), gamemodeSlug: gamemode || '', gamemode: (gamemode || '').replace(/_/g, ' '), resolution: resolution || null, flags, generated: flags.includes('generated'), converted: flags.includes('converted'), generatedSourceGamemode: sourceFlag ? sourceFlag.slice('source_'.length) : null };
}

function listPlaythroughs(resolutionFilter) {
  return fs.readdirSync(PLAYTHROUGHS_DIR)
    .filter(name => name.endsWith('.btd6'))
    .map(parsePlaythroughFile)
    .filter(pt => !resolutionFilter || pt.resolution === resolutionFilter);
}
function routeHash(filename) {
  return createHash('sha256').update(fs.readFileSync(path.join(PLAYTHROUGHS_DIR, filename))).digest('hex');
}
function loadVerifiedRoutes() {
  try { return JSON.parse(fs.readFileSync(ROUTE_VERIFICATION_PATH, 'utf8')); }
  catch { return {}; }
}
function routeWins(filename, mode) {
  try {
    const stats = JSON.parse(fs.readFileSync(STATS_PATH, 'utf8'));
    const byResolution = stats[`playthroughs/${filename}`] || {};
    return Object.entries(byResolution).filter(([key]) => /^\d+x\d+$/.test(key))
      .reduce((sum, [, value]) => sum + (value[mode]?.wins || 0), 0);
  } catch { return 0; }
}
function markRouteVerified(filename, mode) {
  const verified = loadVerifiedRoutes();
  verified[filename] ||= {};
  verified[filename][mode] = { hash: routeHash(filename), verifiedAt: new Date().toISOString() };
  const temporary = ROUTE_VERIFICATION_PATH + '.tmp';
  fs.writeFileSync(temporary, JSON.stringify(verified, null, 2));
  fs.renameSync(temporary, ROUTE_VERIFICATION_PATH);
}
// What a route needs unlocked: the hero it places and, per tower type, the highest tier it buys
// on each of the three paths (counted per placed instance, since tiers are per tower).
function routeRequirements(route, towerData, heroData) {
  const typeOf = {};
  let hero = null;
  const tiers = {};
  const perInstance = {};
  // BTD6bot routes often call the hero instance simply "hero" (without a numeric suffix),
  // while the local AutoBTD6 routes use "hero0". Accept both so prerequisite checks don't
  // silently miss a route's hero requirement.
  for (const [, kind, name] of route.matchAll(/^place\s+([a-z_]+)\s+(\w+)/gm)) {
    if (heroData[kind]) { hero = kind; continue; }
    if (!towerData[kind]) continue;
    typeOf[name] = kind;
    tiers[kind] ||= [0, 0, 0];
  }
  for (const [, name, pathIndex] of route.matchAll(/^upgrade\s+(\w+)\s+path\s+([0-2])/gm)) {
    const kind = typeOf[name];
    if (!kind) continue;
    const counts = perInstance[name] ||= [0, 0, 0];
    counts[pathIndex] += 1;
    tiers[kind][pathIndex] = Math.max(tiers[kind][pathIndex], counts[pathIndex]);
  }
  return { hero, towers: tiers };
}

function getRecordedCombos() {
  const combos = {};
  const towerFile = JSON.parse(fs.readFileSync(path.join(AUTOBTD6_DIR, 'towers.json'), 'utf8'));
  const towerData = towerFile.monkeys;
  const verified = loadVerifiedRoutes();
  let onlineGuides = {};
  try { onlineGuides = JSON.parse(fs.readFileSync(ONLINE_GUIDE_SOURCES_PATH, 'utf8')); } catch { /* No guide routes yet. */ }
  for (const pt of listPlaythroughs()) {
    if (pt.generated) continue;
    const route = fs.readFileSync(path.join(PLAYTHROUGHS_DIR, pt.file), 'utf8');
    if (require('./route-validation').validateRoute(route, pt.gamemodeSlug, towerFile).length) continue;
    const groups = [...new Set([...route.matchAll(/^place\s+([a-z_]+)\s+/gm)]
      .map(match => towerData[match[1]]?.type).filter(Boolean))];
    const allowed = { primary_only: 'primary', military_only: 'military', magic_monkeys_only: 'magic' }[pt.gamemodeSlug];
    if (allowed && (groups.length === 0 || groups.some(group => group !== allowed))) continue;
    const confirmed = !!(verified[pt.file]?.[pt.gamemodeSlug]?.hash === routeHash(pt.file));
    // Renaming a CHIMPS recording does not adapt its opening to ABR, Half Cash,
    // tower restrictions or other rule changes. Only the explicitly supported
    // standard-mode reuse list may use unchanged CHIMPS actions without a target win.
    const renamedSource = pt.generatedSourceGamemode;
    if (!confirmed && renamedSource === 'chimps' && pt.gamemodeSlug !== 'chimps'
        && !CHIMPS_REUSE_MODES.includes(pt.gamemodeSlug)) continue;
    // Conversions that dropped actions are drafts until this exact file wins.
    if (pt.flags.includes('lossy') && !confirmed) continue;
    const guide = onlineGuides[pt.file];
    const sourceVerified = !!(guide?.sourceClaimsWin && guide?.sourceMode === pt.gamemodeSlug && guide?.routeHash === routeHash(pt.file));
    const entry = {
      filename: pt.file, gamemodeSlug: pt.gamemodeSlug, sourceGamemodeSlug: pt.gamemodeSlug,
      isOriginalGamemode: true, resolution: pt.resolution, towerGroups: groups,
      requirements: routeRequirements(route, towerData, towerFile.heros || {}),
      // Conversion preserves a plan; it does not prove its execution in this engine.
      converted: pt.converted, verifiedForTarget: confirmed || sourceVerified || (!pt.converted && !guide),
      sourceVerified,
      onlineGuideSource: guide?.source || null,
      localWinVerified: confirmed,
    };
    ((combos[pt.mapSlug] ||= {})[pt.gamemodeSlug] ||= []).push(entry);

    // User-approved reuse covers standard modes and Impoppable. It supplies a candidate,
    // not a guaranteed victory: starting rounds, prices and account unlocks still differ.
    // Used only as a fallback â€” a map's own dedicated route for the target mode sorts first via
    // the trust() comparator below. Opening tower actions have no round marker, so replay.py can
    // apply them in the target mode.
    const reuseTargets = REUSE_MODES_BY_SOURCE[pt.gamemodeSlug];
    if (reuseTargets) {
      for (const targetMode of reuseTargets) {
        const confirmedForTarget = !!(verified[pt.file]?.[targetMode]?.hash === routeHash(pt.file));
        ((combos[pt.mapSlug] ||= {})[targetMode] ||= []).push({
          ...entry,
          gamemodeSlug: targetMode,
          sourceGamemodeSlug: pt.gamemodeSlug,
          isOriginalGamemode: false,
          reusedFromChimps: pt.gamemodeSlug === 'chimps',
          reusedFromHard: pt.gamemodeSlug === 'hard',
          verifiedForTarget: true,
          localWinVerified: confirmedForTarget,
          sourceVerified: false,
        });
      }
    }
  }
  // Local wins first; then AutoBTD6's own recordings for the mode, then CHIMPS builds (recorded
  // before converted), then Hard-reused builds, then converted plans for the mode, then guides.
  const trust = entry => entry.reusedFromChimps ? (entry.converted ? 2 : 1)
    : entry.reusedFromHard ? (entry.converted ? 4 : 3)
    : entry.onlineGuideSource ? 6 : entry.converted ? 5 : 0;
  for (const modes of Object.values(combos)) for (const entries of Object.values(modes)) {
    entries.sort((a, b) => Number(b.localWinVerified) - Number(a.localWinVerified)
      || trust(a) - trust(b)
      || Number(b.resolution === '2560x1440') - Number(a.resolution === '2560x1440')
      || a.filename.localeCompare(b.filename));
    const seen = new Set();
    for (let index = 0; index < entries.length;) {
      const entry = entries[index];
      const signature = `${entry.resolution}:${require('./route-validation').strategySignature(
        fs.readFileSync(path.join(PLAYTHROUGHS_DIR, entry.filename), 'utf8'))}`;
      if (seen.has(signature)) entries.splice(index, 1);
      else { seen.add(signature); index++; }
    }
  }
  return combos;
}

// AutoBTD6 clicks through the map-select grid by a recorded (category, page, position) index, not
// by recognizing the map on screen â€” every time Ninja Kiwi adds a new map that grid shifts, and a
// recording made before that lands on the wrong tile (https://github.com/ANRAR4/AutoBTD6/issues/55).
// There's no per-map thumbnail image shipped to click by instead, so this can't be fixed blind â€”
// it needs a live recalibration against the current in-game map order.
//
// What we CAN check without the live game: whether the map is unlocked at all. `file` mode has no
// unlock gating of its own (only random/xp/mm do, via getAllAvailablePlaythroughs), so without this
// it would happily try to play a map you haven't unlocked yet.
function isMapUnlocked(mapSlug) {
  try {
    const cfg = JSON.parse(fs.readFileSync(USERCONFIG_PATH, 'utf8'));
    return cfg.unlocked_maps?.[mapSlug] === true;
  } catch { return true; } // fail open â€” don't block a run over a config read hiccup
}

// Same category ordering as the game's own map-select screen and the frontend's map picker
// (map-catalog.js, parsed the same regex way scanner.js/scan-achievements.js parse their catalogs).
const normalizeMapName = s => s.toLowerCase().replace(/[^a-z0-9]/g, '');
function levenshtein(a, b) {
  const rows = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
  for (let j = 0; j <= b.length; j++) rows[0][j] = j;
  for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++) {
    rows[i][j] = a[i - 1] === b[j - 1] ? rows[i - 1][j - 1]
      : 1 + Math.min(rows[i - 1][j], rows[i][j - 1], rows[i - 1][j - 1]);
  }
  return rows[a.length][b.length];
}
const CATEGORY_ORDER = ['Beginner', 'Intermediate', 'Advanced', 'Expert'];
// These modes change the rules enough that a copied placement sequence cannot be treated as a
// safe strategy. They require a dedicated recording or a prior confirmed clear under the target
// mode before unattended automation is allowed to run them.
const MODES_REQUIRING_VERIFIED_ROUTE = new Set([
  'primary_only', 'deflation', 'military_only', 'reverse', 'apopalypse',
  'magic_monkeys_only', 'double_hp_moabs', 'half_cash',
  'alternate_bloons_rounds', 'impoppable', 'chimps',
]);
function syncMapPositions() {
  const source = fs.readFileSync(path.join(PROJECT_ROOT, 'map-catalog.js'), 'utf8');
  const match = source.match(/\{([\s\S]*)\}/);
  if (!match) throw new Error('Map catalog is unreadable');
  const catalog = JSON.parse(`{${match[1]}}`);
  const catalogCategory = new Map(Object.entries(catalog).flatMap(([category, names]) => names.map(name => [normalizeMapName(name), category.toLowerCase()])));
  const maps = JSON.parse(fs.readFileSync(MAPS_PATH, 'utf8'));
  const byName = new Map(Object.entries(maps).map(([slug, entry]) => [normalizeMapName(entry.name || slug), slug]));
  let changed = false;
  for (const [category, names] of Object.entries(catalog)) {
    names.forEach((name, index) => {
      const normalized = normalizeMapName(name);
      let slug = byName.get(normalized);
      if (!slug) {
        slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
        if (maps[slug]) return; // A slug collision must be resolved explicitly.
        maps[slug] = { category: category.toLowerCase(), name, page: Math.floor(index / 6), pos: index % 6 };
        byName.set(normalized, slug);
        changed = true;
      }
      const entry = maps[slug];
      // Current Steam builds place #Ouch on the final Expert page after the
      // newer Expert tiles; keep this explicit until the live scanner confirms
      // the complete catalog.
      const page = name === '#Ouch' ? 2 : Math.floor(index / 6);
      const pos = name === '#Ouch' ? 0 : index % 6;
      if (entry.category !== category.toLowerCase() || entry.page !== page || entry.pos !== pos) {
        Object.assign(entry, { category: category.toLowerCase(), page, pos });
        changed = true;
      }
    });
  }
  // The curated catalog owns canonical map names/categories and sweep ordering. The rolling
  // OCR cache owns tile coordinates only when it agrees with that category; this keeps measured
  // screen positions while preventing a stale category from moving a map back after an update.
  try {
    const liveOrder = JSON.parse(fs.readFileSync(path.join(PROJECT_ROOT, 'map-order.json'), 'utf8'));
    for (const item of Object.values(liveOrder.maps || {})) {
      if (!CATEGORY_ORDER.includes(item.category) || !Number.isInteger(item.page) || !Number.isInteger(item.pos) || item.pos < 0 || item.pos > 5) continue;
      const normalized = normalizeMapName(item.name);
      let slug = byName.get(normalized);
      if (!slug && item.discovered) {
        // A single misread character (OCR "mushroom_grotton" vs the real "mushroom_grotto") missed
        // the exact-match lookup above and used to be treated as a genuine new map - permanently
        // creating a phantom maps.json/unlocked_maps entry from noise. Only trust a discovered name
        // as actually new when it isn't a near-miss (edit distance <=2) of an existing one; a
        // near-miss is logged and skipped so a later, cleaner OCR read can still match correctly.
        const nearMiss = [...byName.keys()].some(existing => levenshtein(normalized, existing) <= 2);
        if (nearMiss) continue;
        slug = item.name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
        if (maps[slug]) continue;
        maps[slug] = { name: item.name, category: item.category.toLowerCase(), page: item.page, pos: item.pos };
        byName.set(normalized, slug);
        changed = true;
      }
      if (!slug) continue;
      const entry = maps[slug];
      const canonicalCategory = catalogCategory.get(normalized);
      if (canonicalCategory && item.category.toLowerCase() !== canonicalCategory) continue;
      if (entry.category !== (canonicalCategory || item.category.toLowerCase()) || entry.page !== item.page || entry.pos !== item.pos) {
        Object.assign(entry, { category: canonicalCategory || item.category.toLowerCase(), page: item.page, pos: item.pos });
        changed = true;
      }
    }
  } catch { /* No live page has been learned yet. */ }
  if (changed) fs.writeFileSync(MAPS_PATH, JSON.stringify(maps, null, 2));
  registerMapsInUserconfig(Object.keys(maps));
  return changed;
}
// Like AutoBTD6's insert_new_map.py: a map added to maps.json also needs an unlocked_maps entry
// and a medal row, or every run on it is refused as "not unlocked" and the sweep never sees it.
function registerMapsInUserconfig(slugs) {
  const cfg = JSON.parse(fs.readFileSync(USERCONFIG_PATH, 'utf8'));
  cfg.unlocked_maps ||= {};
  cfg.medals ||= {};
  let changed = false;
  for (const slug of slugs) {
    if (!(slug in cfg.unlocked_maps)) { cfg.unlocked_maps[slug] = true; changed = true; }
    if (!(slug in cfg.medals)) { cfg.medals[slug] = Object.fromEntries(MEDAL_MODE_ORDER.map(mode => [mode, false])); changed = true; }
  }
  if (changed) fs.writeFileSync(USERCONFIG_PATH, JSON.stringify(cfg, null, 4));
}
let mapCategoryLookup = null;
let mapOrderLookup = null;
function loadCatalogLookups() {
  if (mapCategoryLookup) return;
  mapCategoryLookup = {};
  mapOrderLookup = {};
  const src = fs.readFileSync(path.join(PROJECT_ROOT, 'map-catalog.js'), 'utf8');
  const match = src.match(/\{([\s\S]*)\}/);
  const catalog = match ? JSON.parse(`{${match[1]}}`) : {};
  let order = 0;
  for (const [category, names] of Object.entries(catalog)) {
    for (const name of names) {
      mapCategoryLookup[normalizeMapName(name)] = category;
      mapOrderLookup[normalizeMapName(name)] = order++;
    }
  }
}
function categoryForMapSlug(mapSlug) {
  loadCatalogLookups();
  return mapCategoryLookup[normalizeMapName(mapSlug)] || null;
}
function mapCategoryRank(mapSlug) {
  const index = CATEGORY_ORDER.indexOf(categoryForMapSlug(mapSlug));
  return index === -1 ? CATEGORY_ORDER.length : index;
}
// Position in the game's own map-select order (Monkey Meadow first â€¦ #Ouch last); maps missing from
// the catalog sort after every known one.
function mapCatalogOrder(mapSlug) {
  loadCatalogLookups();
  return mapOrderLookup[normalizeMapName(mapSlug)] ?? Number.MAX_SAFE_INTEGER;
}

// The 14 medal keys are one flat list in the game's own data (see getMissingMedals below), but for
// ordering a sweep we still want difficulty tiers played before variations on the same map.
// https://github.com/ANRAR4/AutoBTD6/issues/40 â€” tree_stump's track entrance art overlaps the
// money-readout crop closely enough to misread cash regularly, which can stall or fail a game
// outright. Excluded from unattended runs (sweep/xp/mm's own random pick) until recalibrated;
// still selectable from "Run a specific map" since that's a deliberate one-off choice.
const UNRELIABLE_MAPS = new Set(['tree_stump']);

// Read recordings at both supported resolutions and mirror the vendored compatibility rules.
// This keeps the picker complete even if Python is not installed yet; a route still has to be
// available and a game mode unlocked before the replay can actually start it.
function getAvailableCombos() {
  return new Promise((resolve, reject) => {
    try { syncMapPositions(); } catch (error) { reject(error); return; }
    resolve(getRecordedCombos());
  });
}

// AutoBTD6's own gating: userconfig.json's "heros" map controls which recorded playthroughs it
// will pick for xp/mm/random farming (a playthrough recorded with a hero the config marks false
// is skipped). This is the real mechanism â€” far more honest than trying to swap a hero mid-replay,
// which isn't possible once a playthrough's actions are already recorded.
function getHeroes() {
  const cfg = JSON.parse(fs.readFileSync(USERCONFIG_PATH, 'utf8'));
  return cfg.heros || {};
}

function setHeroes(heros) {
  const cfg = JSON.parse(fs.readFileSync(USERCONFIG_PATH, 'utf8'));
  cfg.heros = { ...cfg.heros, ...heros };
  fs.writeFileSync(USERCONFIG_PATH, JSON.stringify(cfg, null, 4));
  return cfg.heros;
}

function spawnReplay(args, job = null) {
  syncMapPositions();
  // Profile.Save's primaryHero is BTD6's currently equipped hero. Pass it read-only so
  // replay.py can stay on map selection when that hero already matches the route.
  const profile = readLocalProgress();
  const activeHero = profile.available ? profile.heroes?.primary || '' : '';
  const bonusMonkeyEnabled = profile.available
    && profile.monkeyKnowledge?.bonusMonkey === true
    && profile.monkeyKnowledge?.enabled !== false;
  const bonusGlueEnabled = profile.available
    && profile.monkeyKnowledge?.bonusGlueGunner === true
    && profile.monkeyKnowledge?.enabled !== false;
  // map-mechanics.js's status field tags maps whose placement surfaces or tower access
  // change over time (moving covers, toggled objects, phase/round-gated states, etc).
  // replay.py already refuses a blind nearby-coordinate retry on a small hardcoded set of
  // such maps (dynamicPlacementMaps) â€” this supplements that set from the fuller catalog
  // instead of requiring every new dynamic map to be added to both places.
  const targetFile = args[0] === 'file' ? args[1] : null;
  const targetMapSlug = targetFile ? parsePlaythroughFile(targetFile).mapSlug : null;
  const mechanicsStatus = targetMapSlug ? getMapMechanics(targetMapSlug).status : null;
  const dynamicPlacement = !!mechanicsStatus && /dynamic|stateful|phase-aware|cycle-aware|round-gated|erosion-checkpoint|variant-detection/.test(mechanicsStatus);
  return spawn(getRuntime().executable || 'py', ['replay.py', ...args], {
    cwd: AUTOBTD6_DIR, windowsHide: true,
    env: { ...runtimeEnvironment(), BLOONS_PARENT_JOB: job?.type || '', BLOONS_ACTIVE_HERO: activeHero,
      BLOONS_MEDALS_FROM_SAVE: profile.available && profile.mapProgress ? '1' : '0',
      // Read fresh per replay, so a keybind change in BTD6 applies from the next route on.
      BLOONS_HOTKEYS: profile.available && profile.gameHotkeys ? JSON.stringify(profile.gameHotkeys) : '',
      BLOONS_BONUS_MONKEY_FREE: bonusMonkeyEnabled ? '1' : '0',
      BLOONS_BONUS_GLUE_FREE: bonusGlueEnabled ? '1' : '0',
      BLOONS_BONUS_MONKEY_SOURCE: profile.available ? 'Profile.Save' : 'unavailable',
      BLOONS_DYNAMIC_PLACEMENT: dynamicPlacement ? '1' : '0' },
  });
}

function wireProcess(job, proc, observe = () => {}) {
  job.proc = proc;
  for (const [stream, prefix] of [[proc.stdout, ''], [proc.stderr, '[stderr] ']]) {
    const reader = createLineReader(line => {
      observe(line);
      pushLog(job, prefix + line);
      if (job.stopAfterReplay && ['xp', 'mm', 'max-towers', 'random'].includes(job.type)
          && /VICTORY_CONFIRMED\b|screen (?:VICTORY|VICTORY_SUMMARY|DEFEAT)!/.test(line)
          && !job.stopAfterTimer) {
        pushLog(job, 'current replay finished; stopping before another replay starts');
        job.stopAfterTimer = setTimeout(() => {
          job.stopRequested = true;
          killProcessTree(proc).catch(error => pushLog(job, `deferred stop failed: ${error.message}`));
        }, 1500);
      }
    });
    stream.on('data', reader.write);
    stream.on('end', reader.end);
  }
  proc.on('error', error => {
    pushLog(job, `replay process error: ${error.message}`);
    job.exitCode = null;
  });
}

// Runs one `file` playthrough to completion (it exits on its own after a single game, win or
// lose, since no -r flag is passed) â€” used by the achievements sweep below.
const NOTABLE_REPLAY_LINE = /WARNING|ERROR|Traceback|Exception|\[stderr\]|failed|not confirmed|recognition error|screen [A-Z_]+!|new state|failsafe|performing action|FAILURE_SHOT|MEDAL_ALREADY_EARNED|SURPLUS_|PLACE_SEARCH|stale match|mode intro|LIVES_LOST|EMERGENCY_SPEND|INSTANT_LOSS_PREVENTED|GAME_ERROR|could not be focused|mode badge|round \d+ reached|objective|stopping before map click|map page is not visible|map tile did not open/i;
function runOne(job, args, limits = {}) {
  return new Promise(resolve => {
    const monitor = createReplayMonitor(limits);
    job.replayMonitor = monitor;
    const proc = spawnReplay(args, job);
    // The job log is a short rolling tail full of cash reads; keep this route's meaningful lines
    // (warnings, failed actions, screen changes, errors) for the failure report instead.
    const notable = [];
    // notable's regex filter drops plain DEBUG lines (OCR reads, per-action detail) that matter for
    // a real post-mortem. Keep every line for this one run too, capped generously so a stuck/looping
    // replay can't grow it without bound - recordRouteFailure attaches this in full on a failure.
    const raw = [];
    const RAW_LOG_CAP = 4000;
    wireProcess(job, proc, line => {
      monitor.observe(line);
      if (NOTABLE_REPLAY_LINE.test(line)) { notable.push(line); if (notable.length > 150) notable.shift(); }
      raw.push(line);
      if (raw.length > RAW_LOG_CAP) raw.shift();
    });
    let settled = false;
    let reason = 'exit';
    let stallReason = null;
    const finish = exitCode => {
      if (settled) return;
      settled = true;
      clearInterval(watchdog);
      if (job.replayMonitor === monitor) delete job.replayMonitor;
      if (job.proc === proc && (proc.exitCode !== null || proc.signalCode !== null || !proc.pid)) job.proc = null;
      const observed = monitor.snapshot();
      job.replay = { ...observed, reason: observed.fatal || reason, stallReason };
      resolve({ exitCode, ...job.replay, notable, raw });
    };
    const watchdog = setInterval(() => {
      monitor.setPaused(!!job.paused);
      job.replay = monitor.snapshot();
      stallReason = monitor.stalled();
      if (!stallReason || job.stopRequested) return;
      reason = 'stalled';
      pushLog(job, `failsafe: ${stallReason}; stopping this replay before another route can start`);
      clearInterval(watchdog);
      killProcessTree(proc).catch(error => {
        reason = 'stop-failed';
        job.stopRequested = true;
        pushLog(job, `could not stop replay: ${error.message}; the input lock stays held`);
        finish(null);
      });
    }, 10_000);
    watchdog.unref?.();
    proc.on('close', code => finish(code));
    proc.on('error', error => { reason = 'spawn-error'; pushLog(job, `error: ${error.message}`); finish(null); });
  });
}

// AutoBTD6's own "achievements" CLI mode is an unimplemented stub in the vendored copy, so this
// drives the same outcome from outside: run every shipped map+difficulty once, then re-run our
// own search-box achievement scanner (search-scan-achievements.js) to pick up whatever unlocked.
// This is deliberately not achievement-name-to-map matching (BTD6 achievement names rarely match
// map names) â€” beating every recorded map/difficulty is the reliable way to unlock map-completion
// achievements without needing to know which is which upfront.
async function runAchievementsSweep(job) {
  const all = listPlaythroughs('2560x1440');
  const playthroughs = all.filter(pt => isMapUnlocked(pt.mapSlug) && !UNRELIABLE_MAPS.has(pt.mapSlug));
  const skipped = all.length - playthroughs.length;
  const progress = loadProgress();
  progress.achievementsSweep ||= { completedFiles: [] };
  const completedFiles = new Set(progress.achievementsSweep.completedFiles || []);
  const remaining = playthroughs.filter(pt => !completedFiles.has(pt.file));
  pushLog(job, `achievements sweep: ${remaining.length} recordings left (${completedFiles.size} previous attempts saved, ${skipped} unavailable)`);
  for (let i = 0; i < remaining.length; i++) {
    if (job.stopRequested) { pushLog(job, 'sweep stopped'); return; }
    const pt = remaining[i];
    pushLog(job, `[${i + 1}/${remaining.length}] running ${pt.map} - ${pt.gamemode}`);
    const result = await runOne(job, ['file', pt.file, '-mk']);
    if (job.stopRequested) { pushLog(job, 'sweep stopped'); return; }
    if (['game-unavailable', 'invalid-window', 'spawn-error', 'stop-failed'].includes(result.reason)) {
      job.exitCode = 1;
      pushLog(job, `sweep stopped: ${result.reason}; remaining recordings are saved`);
      return;
    }
    const medals = JSON.parse(fs.readFileSync(USERCONFIG_PATH, 'utf8')).medals || {};
    if (result.exitCode !== 0 || medals[pt.mapSlug]?.[pt.gamemodeSlug] !== true) {
      if ((result.notable || []).some(line => /screen DEFEAT!/i.test(line))) ensureOutcomeCount(job, 'defeat');
      pushLog(job, `recording did not confirm a victory; leaving it in the queue`);
      if (job.stopAfterReplay) {
        job.stopRequested = true;
        pushLog(job, 'current replay finished; stopping before the next replay');
        return;
      }
      continue;
    }
    // The replay confirmed a win. This still does not claim any achievement unlocked.
    ensureOutcomeCount(job, 'victory');
    completedFiles.add(pt.file);
    progress.achievementsSweep.completedFiles = [...completedFiles];
    progress.achievementsSweep.updatedAt = new Date().toISOString();
    saveProgress(progress);
    pushLog(job, 'rescanning achievements...');
    try {
      const { searchScanAchievements } = require('./search-scan-achievements');
      const result = await searchScanAchievements({});
      pushLog(job, `achievements: ${result.completedTotal}/${result.total} completed`);
    } catch (error) {
      pushLog(job, `achievement rescan failed: ${error.message}`);
    }
    if (job.stopAfterReplay) {
      job.stopRequested = true;
      pushLog(job, 'current replay finished; stopping before the next replay');
      return;
    }
  }
  pushLog(job, 'sweep complete');
}

// A map's full black border is 14 medals (userconfig.json's medals[map] â€” easy/medium/hard plus
// every variation: primary_only, deflation, military_only, reverse, apopalypse,
// magic_monkeys_only, double_hp_moabs, half_cash, alternate_bloons_rounds, impoppable, chimps).
// AutoBTD6 already records a win against this list itself (helper.py's updateMedalStatus, called
// from replay.py on VICTORY_SUMMARY) â€” but it ships with every medal marked true (the
// maintainer's own maxed save). That's wrong for an active player, so reconcile it once against
// what our own achievement/map scanner already knows before trusting any of it: a map we've
// confirmed has its black border keeps all medals true; anything else starts from "not done" so a
// sweep actually plays what's missing instead of skipping everything.
const OBSERVATIONS_PATH = path.join(PROJECT_ROOT, 'game-observations.json');
function syncMedalsFromObservations() {
  const cfg = JSON.parse(fs.readFileSync(USERCONFIG_PATH, 'utf8'));
  let observations;
  try { observations = JSON.parse(fs.readFileSync(OBSERVATIONS_PATH, 'utf8')); } catch { observations = { maps: {} }; }
  // The vendored config ships with the maintainer's medals. Initialize once, then preserve
  // medals that AutoBTD6 records on victory across every subsequent sweep and app restart.
  if (!cfg.bloonsPlusMedalsInitialized) {
    for (const medals of Object.values(cfg.medals || {})) {
      for (const mode of Object.keys(medals)) medals[mode] = false;
    }
    cfg.bloonsPlusMedalsInitialized = true;
  }
  // Older badge checks sampled map art at 1080p and could mark medals earned
  // without a victory. Rebuild those assumptions once from confirmed local
  // clears; subsequent live mode screens can restore genuinely earned medals.
  if (!cfg.bloonsPlusMedalsVerifiedV2) {
    for (const medals of Object.values(cfg.medals || {})) {
      for (const mode of Object.keys(medals)) medals[mode] = false;
    }
    cfg.bloonsPlusMedalsVerifiedV2 = true;
  }
  const observedByMap = new Map(Object.entries(observations.maps || {}).map(([name, entry]) => [normalizeMapName(name), entry]));
  const mapNames = JSON.parse(fs.readFileSync(MAPS_PATH, 'utf8'));
  for (const mapSlug of Object.keys(cfg.medals || {})) {
    const observed = observedByMap.get(normalizeMapName(mapNames[mapSlug]?.name || mapSlug));
    // completedModes is written only after a victory and a saved medal. The live
    // mode-badge check (markMedalSeen, via MEDAL_ALREADY_EARNED) only ever writes
    // to .medals, not .completedModes - and since that skip path never re-plays
    // the route to re-confirm it, a medal seen only via badge used to sit here
    // forever and could never unlock its prerequisite-gated next tier (impoppable,
    // chimps). The live badge is the same signal the skip path already trusts
    // enough to not waste time re-playing it, so trust it here too for gating.
    const medalKeys = Object.entries(observed?.medals || {})
      .filter(([, earned]) => earned === true).map(([mode]) => mode);
    const earned = [...new Set([...(observed?.completedModes || []), ...medalKeys])];
    while (earned.length) {
      const mode = earned.pop();
      cfg.medals[mapSlug][mode] = true;
      earned.push(...(MEDAL_MODE_PREREQUISITES[mode] || []));
    }
  }
  // Profile.Save is the source of truth for map clears. Its mode values are
  // numbers, so merge these decoded states after screen observations to correct
  // old badge/OCR false positives and bring newly earned medals into the sweep.
  const profile = readLocalProgress();
  if (profile.available && profile.mapProgress) {
    const localMaps = new Map(Object.entries(profile.mapProgress).map(([name, record]) => [normalizeMapName(name), record]));
    for (const mapSlug of Object.keys(cfg.medals || {})) {
      const record = localMaps.get(normalizeMapName(mapNames[mapSlug]?.name || mapSlug));
      if (record) Object.assign(cfg.medals[mapSlug], medalsFromMapRecord(record));
    }
  }
  fs.writeFileSync(USERCONFIG_PATH, JSON.stringify(cfg, null, 4));
  return cfg.medals;
}

// BTD6 locks medal modes behind prerequisites. Keep the sweep in the game's actual order; having a
// candidate route does not mean that the current profile can select its mode yet.
// Last round of each mode. A victory only counts when the replay also saw the round counter get
// close to it: a victory screen matched on a few pixels mid-game must not save a medal for good.
const FINAL_ROUND = {
  easy: 40, primary_only: 40, deflation: 60, medium: 60, military_only: 60, reverse: 60, apopalypse: 60,
  hard: 80, magic_monkeys_only: 80, double_hp_moabs: 80, half_cash: 80, alternate_bloons_rounds: 80,
  impoppable: 100, chimps: 100,
};
function confirmClear(map, gamemode, result, log) {
  let cfg;
  try { cfg = JSON.parse(fs.readFileSync(USERCONFIG_PATH, 'utf8')); } catch { return false; }
  if (cfg.medals?.[map]?.[gamemode] !== true) return false;
  const reached = Number(result.round) || 0;
  if (reached >= FINAL_ROUND[gamemode] - 3) return true;
  cfg.medals[map][gamemode] = false;
  fs.writeFileSync(USERCONFIG_PATH, JSON.stringify(cfg, null, 4));
  log(`${map} - ${gamemode}: victory reported but the last confirmed round was ${reached || 'unread'} of ${FINAL_ROUND[gamemode]}; not counting it`);
  return false;
}

// A medal read off the game (not won by this run): saved for the Maps page without an Activity entry.
function markMedalSeen(map, gamemode) {
  const observations = JSON.parse(fs.readFileSync(OBSERVATIONS_PATH, 'utf8'));
  const mapNames = JSON.parse(fs.readFileSync(MAPS_PATH, 'utf8'));
  const name = (mapNames[map]?.name || map).toLowerCase();
  const entry = (observations.maps ||= {})[name] || {};
  observations.maps[name] = { ...entry, medals: { ...(entry.medals || {}), [gamemode]: true }, medalsScannedAt: new Date().toISOString() };
  const temporary = `${OBSERVATIONS_PATH}.tmp`;
  fs.writeFileSync(temporary, JSON.stringify(observations, null, 2));
  fs.renameSync(temporary, OBSERVATIONS_PATH);
}

function recordObservedClear(map, gamemode) {
  let observations;
  try { observations = JSON.parse(fs.readFileSync(OBSERVATIONS_PATH, 'utf8')); }
  catch { observations = { source: 'live-scan', maps: {} }; }
  observations.maps ||= {};
  const mapNames = JSON.parse(fs.readFileSync(MAPS_PATH, 'utf8'));
  const name = (mapNames[map]?.name || map).toLowerCase();
  const entry = observations.maps[name] || {};
  const medals = { ...(entry.medals || {}), [gamemode]: true };
  const config = JSON.parse(fs.readFileSync(USERCONFIG_PATH, 'utf8'));
  const blackBorder = entry.blackBorder === true
    || MEDAL_MODE_ORDER.every(mode => config.medals?.[map]?.[mode] === true);
  const completedModes = [...new Set([...(entry.completedModes || []), gamemode])];
  if (entry.medals?.[gamemode] !== true) recordMedalGain(observations, name, gamemode);
  observations.maps[name] = { ...entry, medals, completedModes, blackBorder,
    status: blackBorder ? 'completed' : 'working', medalsUpdatedAt: new Date().toISOString(),
    completedAt: blackBorder ? (entry.completedAt || new Date().toISOString()) : entry.completedAt };
  const temporary = `${OBSERVATIONS_PATH}.tmp`;
  fs.writeFileSync(temporary, JSON.stringify(observations, null, 2));
  fs.renameSync(temporary, OBSERVATIONS_PATH);
}

// Every failed route attempt is kept for later route fixes: what was placed and upgraded, how far
// the game got and how many lives were left. game-state.json is the replay's own live record.
const FAILURES_PATH = path.join(PROJECT_ROOT, 'route-failures.json');
// A plain-text companion to route-failures.json: one line per failure, meant to be opened,
// tailed, or grepped directly instead of parsed â€” the JSON keeps the full forensic detail.
const FAILURES_LOG_PATH = path.join(PROJECT_ROOT, 'route-failures.log');
// Sort a recorded failure into what kind of action it actually calls for, so the list isn't a flat
// mix of real bugs and ordinary lost games:
//  - route-corruption: the route file itself is broken (duplicate/invalid placement) - fix the file.
//  - navigation-bug: the game never got a fair run at all (menu/map-select stuck) - fix the code.
//  - ocr-stall: round OCR read a stable, impossible value (e.g. 753) instead of drifting/erroring -
//    a real screen-region calibration bug for that map, not a lost game - the run never had a
//    chance since await_round conditions could never be satisfied.
//  - insufficient-data: game-state.json didn't match this run, so there's nothing to diagnose from.
//  - gameplay-defeat: a real, clean attempt that still lost - the strategy needs improving, not code.
function classifyRouteFailure({ reason, lastRound, rawLastRound, finalRound, sameRun, log }) {
  const text = (log || []).join('\n');
  if (/placed twice|unknown type|unplaced/i.test(text)) return 'route-corruption';
  // A failed hero picker never reached a playable route. A stale game-state
  // file may still contain this map's last round, so classify from the log.
  if (/ERROR hero picker shows|ERROR hero Select button is unconfirmed|ERROR hero selection was not confirmed/i.test(text)) return 'navigation-bug';
  if (/INSTANT_LOSS_PREVENTED|ERROR place of|ERROR dynamic-map placement|recorded spot is on moving terrain/i.test(text)) return 'placement-bug';
  if (/upgrade_unconfirmed|upgrade cash result remains ambiguous/i.test(text)) return 'upgrade-unconfirmed';
  if (/stalled|STARTMENU|GAMEMODE_SELECTION|map click|map page|map tile/i.test(reason || '')) return 'navigation-bug';
  if (/made no confirmed progress/i.test(reason || '') && lastRound == null && rawLastRound != null) return 'ocr-stall';
  if (!sameRun && lastRound == null) return 'insufficient-data';
  if (Number.isInteger(lastRound) && Number.isInteger(finalRound) && (lastRound < 0 || lastRound > finalRound + 5)) return 'insufficient-data';
  return 'gameplay-defeat';
}
function recordRouteFailure(map, gamemode, filename, result) {
  let state = {};
  try { state = JSON.parse(fs.readFileSync(path.join(AUTOBTD6_DIR, 'game-state.json'), 'utf8')); } catch { /* no live record */ }
  const sameRun = state.map === map;
  let failures = [];
  try { failures = JSON.parse(fs.readFileSync(FAILURES_PATH, 'utf8')); } catch { /* first failure */ }
  const reason = result.stallReason || result.reason;
  // game-state.json's round can carry a raw, un-sanity-checked OCR value (unlike the stall
  // monitor's own 0-200-clamped reading) - an impossible round means this run's state data is
  // noise, not a real result; treat it the same as no data rather than reporting a fake round.
  const rawLastRound = sameRun ? state.round : result.round ?? null;
  const finalRound = FINAL_ROUND[gamemode];
  const lastRound = Number.isInteger(rawLastRound) && rawLastRound >= 0 && rawLastRound <= (finalRound || 100) + 5
    ? rawLastRound : null;
  const entry = {
    at: new Date().toISOString(), map, gamemode, route: filename,
    reason, exitCode: result.exitCode,
    lastRound, finalRound,
    // Kept only when the sanity clamp rejected it, so an ocr-stall entry still shows the exact
    // bogus value that was actually read (e.g. 753) instead of just "null".
    rawRoundOcr: lastRound === null && rawLastRound != null ? rawLastRound : undefined,
    livesLeft: sameRun ? state.lives : null, cash: sameRun ? state.cash : null, result: sameRun ? state.result : null,
    observations: sameRun ? (state.observations || []).slice(-240) : [],
    screenshot: (result.notable || []).map(line => line.match(/FAILURE_SHOT (\S+)/)?.[1]).filter(Boolean).pop() || null,
    log: result.notable || [],
    // Full, unfiltered stdout/stderr for this one run (see runOne's `raw`) - notable's regex drops
    // plain DEBUG lines that matter for a real post-mortem (every OCR read, every action attempt).
    fullLog: result.raw || [],
    actions: sameRun ? (state.events || []).filter(event => ['place', 'upgrade', 'sell'].includes(event.type))
      .map(event => ({ type: event.type, tower: event.tower, towerType: event.towerType, path: event.path, round: event.round, position: event.position, status: event.status })) : [],
  };
  entry.category = classifyRouteFailure({ reason, lastRound, rawLastRound, finalRound, sameRun, log: entry.log });
  entry.actionable = entry.category !== 'gameplay-defeat';
  entry.lossType = classifyLoss(entry);
  failures.push(entry);
  const temporary = FAILURES_PATH + '.tmp';
  fs.writeFileSync(temporary, JSON.stringify(failures, null, 2));
  fs.renameSync(temporary, FAILURES_PATH);
  const line = `${entry.at} | ${entry.map} | ${entry.gamemode} | ${entry.route} | [${entry.category}] `
    + `round ${entry.lastRound ?? '?'}/${entry.finalRound ?? '?'} | lives ${entry.livesLeft ?? '?'} | `
    + `${entry.reason || 'unknown reason'}\n`;
  try { fs.appendFileSync(FAILURES_LOG_PATH, line); } catch { /* best-effort; the JSON record above is authoritative */ }
  return entry;
}

// instant: died within three rounds of the first observed round (or the replay aborted a doomed
// opening) - almost always a bot fault (placement, timing), not the route's strength.
// late: reached 75% of the mode - the route nearly works and needs strengthening.
function classifyLoss(entry) {
  const log = entry.log || [];
  if (log.some(line => /INSTANT_LOSS_PREVENTED/.test(line))) return 'instant-prevented';
  if (entry.result !== 'defeat' && !log.some(line => /screen DEFEAT!/i.test(line))) return null;
  const { lastRound, finalRound } = entry;
  if (!Number.isInteger(lastRound) || !Number.isInteger(finalRound)) return 'unknown';
  const rounds = (entry.observations || []).map(o => o.round).filter(r => Number.isInteger(r) && r > 0 && r <= finalRound);
  const startRound = rounds.length ? Math.min(...rounds) : null;
  if (startRound != null && lastRound - startRound <= 3) return 'instant';
  if (lastRound >= finalRound * 0.75) return 'late';
  if (lastRound < finalRound * 0.4) return 'early';
  return 'mid';
}
const STRENGTHEN_QUEUE_PATH = path.join(PROJECT_ROOT, 'route-strengthen-queue.json');
function queueRouteStrengthening(entry) {
  let queue = [];
  try { queue = JSON.parse(fs.readFileSync(STRENGTHEN_QUEUE_PATH, 'utf8')); } catch { /* new queue */ }
  queue = queue.filter(item => item.route !== entry.route);
  queue.push({ route: entry.route, map: entry.map, gamemode: entry.gamemode, lastRound: entry.lastRound,
    finalRound: entry.finalRound, cash: entry.cash, at: entry.at });
  fs.writeFileSync(STRENGTHEN_QUEUE_PATH, JSON.stringify(queue, null, 2));
}

// getMissingMedals() below picks a map's next mode from this list, taking the first one that's
// both missing and unlocked, so this order is the sweep's real per-map priority. CHIMPS's own
// unlock chain (hard -> alternate_bloons_rounds -> impoppable -> chimps, per
// MEDAL_MODE_PREREQUISITES) is fixed first so a map reaches and attempts CHIMPS as soon as the
// game allows it. The remaining side-branch modes (none of them gate CHIMPS) are shuffled on each
// call instead of always following the same fixed sequence, per the user's "chimps first, the
// rest random" instruction.
const CHIMPS_CRITICAL_PATH = ['easy', 'medium', 'hard', 'alternate_bloons_rounds', 'impoppable', 'chimps'];
const CHIMPS_SIDE_BRANCHES = ['primary_only', 'deflation', 'military_only', 'reverse', 'apopalypse',
  'magic_monkeys_only', 'double_hp_moabs', 'half_cash'];
const MEDAL_MODE_ORDER = [...CHIMPS_CRITICAL_PATH, ...CHIMPS_SIDE_BRANCHES];
function shuffled(list) {
  const result = list.slice();
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}
const MEDAL_MODE_PREREQUISITES = {
  primary_only: ['easy'], deflation: ['primary_only'],
  military_only: ['medium'], reverse: ['medium'], apopalypse: ['military_only'],
  magic_monkeys_only: ['hard'], double_hp_moabs: ['magic_monkeys_only'],
  half_cash: ['double_hp_moabs'], alternate_bloons_rounds: ['hard'],
  impoppable: ['alternate_bloons_rounds'], chimps: ['impoppable'],
};
function getMissingMedals(mapSlug, combos) {
  const cfg = JSON.parse(fs.readFileSync(USERCONFIG_PATH, 'utf8'));
  const medals = cfg.medals?.[mapSlug] || {};
  const order = [...CHIMPS_CRITICAL_PATH, ...shuffled(CHIMPS_SIDE_BRANCHES)];
  return order.filter(gamemode => {
    const candidates = sweepCandidates(combos, mapSlug, gamemode);
    if (!candidates.length || medals[gamemode] === true) return false;
    return (MEDAL_MODE_PREREQUISITES[gamemode] || []).every(prerequisite => medals[prerequisite] === true);
  });
}

function sweepCandidates(combos, map, mode) {
  return (combos[map]?.[mode] || []).filter(entry => !MODES_REQUIRING_VERIFIED_ROUTE.has(mode)
    || (entry.verifiedForTarget !== false && (entry.isOriginalGamemode || entry.reusedFromChimps))
    // A complete published conversion for its own mode may be attempted, but remains
    // unverified until this engine confirms its victory. Lossy and incompatible mode
    // copies have already been removed by getRecordedCombos().
    || (entry.converted && entry.isOriginalGamemode));
}

function saveSweepProgress(key, update) {
  const progress = loadProgress();
  progress[key] = { ...progress[key], ...update, updatedAt: new Date().toISOString() };
  saveProgress(progress);
}

function getRouteAttempts() {
  try { return JSON.parse(fs.readFileSync(PROGRESS_PATH, 'utf8'))[MODE_ATTEMPTS_KEY] || {}; }
  catch { return {}; }
}

function rankCandidatesForProfile(entries) {
  if (!entries.length) return entries;
  const profile = readLocalProgress();
  if (!profile.available) return entries;
  const normal = value => String(value || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const acquired = new Set((profile.acquiredUpgrades || []).map(normal));
  const towers = new Set((profile.unlockedTowers || []).map(normal));
  // Replays select towers by hotkey; one with no hotkey bound in BTD6 (e.g. Super Monkey,
  // Mermonkey here) can never be placed, which aborted mushroom_grotto openings over and over.
  const hotkeys = profile.towerHotkeys && Object.keys(profile.towerHotkeys).length
    ? new Map(Object.entries(profile.towerHotkeys).map(([name, bind]) => [normal(name), bind])) : null;
  const hasHotkey = saveName => !hotkeys || !!hotkeys.get(saveName);
  const heroes = new Set((profile.heroes?.unlocked || []).map(normal));
  let catalog = {};
  try { catalog = JSON.parse(fs.readFileSync(path.join(PROJECT_ROOT, 'data', 'tower-upgrades.json'), 'utf8')); } catch {}
  // The upgrade catalog abbreviates some tower ids; unmatched ones counted as "unknown" upgrades
  // and blocked every buccaneer/alchemist/boomerang route from launching.
  const catalogSlug = { beasthandler: 'beast', buccaneer: 'boat', alchemist: 'alch', boomerang: 'boomer' };
  const savedTowerNames = {
    dart: 'dartmonkey', boomerang: 'boomerangmonkey', bomb: 'bombshooter', tack: 'tackshooter',
    ice: 'icemonkey', glue: 'gluegunner', sniper: 'snipermonkey', sub: 'monkeysub',
    buccaneer: 'monkeybuccaneer', ace: 'monkeyace', heli: 'helipilot', mortar: 'mortarmonkey',
    dartling: 'dartlinggunner', wizard: 'wizardmonkey', super: 'supermonkey', ninja: 'ninjamonkey',
    alchemist: 'alchemist', druid: 'druid', farm: 'bananafarm', spike: 'spikefactory',
    village: 'monkeyvillage', engineer: 'engineermonkey', beasthandler: 'beasthandler',
    mermonkey: 'mermonkey', desperado: 'desperado', skywarden: 'skywarden',
  };
  return entries.map((entry, index) => {
    const requirements = entry.requirements || { towers: {} };
    let missing = 0, unknown = 0, missingTowerUnlocks = 0, missingHero = 0;
    if (requirements.hero && heroes.size && !heroes.has(normal(requirements.hero))) { missing++; missingHero = 1; }
    for (const [rawSlug, tiers] of Object.entries(requirements.towers || {})) {
      const slug = catalogSlug[normal(rawSlug)] || normal(rawSlug);
      const saveName = savedTowerNames[normal(rawSlug)] || normal(rawSlug);
      if ((towers.size && !towers.has(normal(rawSlug)) && !towers.has(slug) && !towers.has(saveName))
          || !hasHotkey(saveName)) {
        missing++; missingTowerUnlocks++;
      }
      for (let pathIndex = 0; pathIndex < 3; pathIndex++) {
        const maximum = Number(tiers[pathIndex]) || 0;
        for (let tier = 1; tier <= maximum; tier++) {
          const suffix = pathIndex === 0 ? `${tier}-x-x` : pathIndex === 1 ? `x-${tier}-x` : `x-x-${tier}`;
          const upgrade = Object.entries(catalog).find(([id]) => id.toLowerCase() === `${slug} ${suffix}`.toLowerCase())?.[1]?.[0];
          if (typeof upgrade !== 'string') unknown++;
          else if (!acquired.has(normal(upgrade))) missing++;
        }
      }
    }
    return { entry, index, missing, unknown, missingHero, missingTowerUnlocks };
  }).sort((a, b) => Number(a.missingHero + a.missingTowerUnlocks > 0) - Number(b.missingHero + b.missingTowerUnlocks > 0)
    || Number(b.entry.localWinVerified) - Number(a.entry.localWinVerified)
    || a.missing - b.missing || a.unknown - b.unknown || a.index - b.index)
    .map(({ entry, missing, unknown, missingHero, missingTowerUnlocks }) => ({
      ...entry, profileReadiness: { missing, unknown, missingHero, missingTowerUnlocks },
    }));
}
function restoreAttemptsLostToNavigation() {
  const progress = loadProgress();
  const attempts = progress[MODE_ATTEMPTS_KEY] || {};
  let failures = [];
  try { failures = JSON.parse(fs.readFileSync(FAILURES_PATH, 'utf8')); } catch { return attempts; }
  let restored = 0;
  for (const failure of failures) {
    const navigationLog = (failure.log || []).some(line => /stopping before map click|map page is not visible|map tile did not open/i.test(line));
    const exitedBeforeGame = (failure.exitCode === 2 || (failure.exitCode !== 0 && (failure.log || []).some(line => /Traceback \(most recent call last\)/i.test(line))))
      && !(failure.log || []).some(line => /goal GOTO_INGAME|screen INGAME!/i.test(line))
      && !(failure.actions || []).length;
    // Stalls before the match ever started (e.g. the reverse/deflation mode-intro pause loop)
    // never tested the route either.
    const focusFailed = [...(failure.log || []), ...(failure.fullLog || [])].some(line => /could not be focused/.test(line))
      && !(failure.actions || []).length;
    const stalledBeforeGame = /navigation or recovery stalled/i.test(String(failure.reason || ''))
      && !(failure.log || []).some(line => /goal GOTO_INGAME/i.test(line))
      && !(failure.actions || []).length;
    if (!navigationLog && !exitedBeforeGame && !stalledBeforeGame && !focusFailed) continue;
    const prior = attempts[failure.map]?.[failure.gamemode]?.[failure.route];
    if (!prior || prior.outcome === 'cleared') continue;
    if (Math.abs(Date.parse(prior.attemptedAt) - Date.parse(failure.at)) > 10000) continue;
    delete attempts[failure.map][failure.gamemode][failure.route];
    restored++;
  }
  if (restored) { progress[MODE_ATTEMPTS_KEY] = attempts; saveProgress(progress); }
  return attempts;
}
function saveRouteAttempt(mapSlug, gamemode, filename, outcome, attempts, hash, reason, extra = {}) {
  const progress = loadProgress();
  progress[MODE_ATTEMPTS_KEY] ||= {};
  progress[MODE_ATTEMPTS_KEY][mapSlug] ||= {};
  progress[MODE_ATTEMPTS_KEY][mapSlug][gamemode] ||= {};
  progress[MODE_ATTEMPTS_KEY][mapSlug][gamemode][filename] = {
    outcome,
    attempts,
    hash,
    reason,
    ...extra,
    attemptedAt: new Date().toISOString(),
  };
  saveProgress(progress);
  return progress[MODE_ATTEMPTS_KEY][mapSlug][gamemode][filename];
}

// BTD6 occasionally crashes during long unattended passes. Start it again through Steam and press
// START on its title screen, so the pass continues instead of stopping.
const MAX_GAME_RELAUNCHES = 3;
async function relaunchGame(job, { afterGameError = false } = {}) {
  const { captureWindow, focusWindow } = require('./capture');
  const { moveAndClick } = require('./input');
  const { readPng } = require('./pixels');
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  // A crash leaves a dump; a player closing the game doesn't, and then the pass should just stop.
  const crashDir = path.join(process.env.LOCALAPPDATA || '', 'Temp', 'Ninja Kiwi', 'BloonsTD6', 'Crashes');
  let crashed = false;
  try { crashed = fs.readdirSync(crashDir).some(name => fs.statSync(path.join(crashDir, name)).mtimeMs > job.startedAt); } catch { /* no dumps */ }
  // BTD6's own exception popup only offers EXIT, which closes the game: that's a crash too.
  if (!crashed && afterGameError) { crashed = true; pushLog(job, 'BTD6 closed after its own error popup'); }
  if (!crashed) { pushLog(job, 'BTD6 was closed without crashing; not reopening it'); return false; }
  pushLog(job, 'BTD6 crashed; relaunching it through Steam');
  spawn('cmd', ['/c', 'start', '', 'steam://rungameid/960090'], { windowsHide: true, detached: true }).unref();
  const deadline = Date.now() + 240_000;
  while (Date.now() < deadline && !job.stopRequested) {
    await sleep(3000);
    let capture;
    try { capture = await captureWindow(); } catch { continue; }
    if (capture.width < 1280) continue;   // still on the small startup splash
    const image = readPng(capture.png);
    const scale = capture.width / 1920;
    // Title screen's green START button. A single pixel landed on the grey "START" lettering
    // and the relaunch never saw the button (the game sat on the title screen all night);
    // measure the green share of the whole button instead, like replay.py's title check.
    let green = 0, total = 0;
    for (let y = Math.round(925 * scale); y < Math.round(1015 * scale); y += 3) {
      for (let x = Math.round(830 * scale); x < Math.round(1090 * scale); x += 3) {
        const [r, g, b] = image.get(x, y);
        total++;
        if (g > 90 && g > r * 1.5 && g > b * 1.5) green++;
      }
    }
    if (!total || green / total < 0.4) continue;
    await focusWindow();
    await moveAndClick(Math.round(960 * scale), Math.round(970 * scale));
    await sleep(8000);
    pushLog(job, 'BTD6 restarted; retrying the interrupted route');
    return true;
  }
  pushLog(job, 'BTD6 did not come back within 4 minutes');
  return false;
}

function loadMedalsFromProfileSave(job) {
  const profile = readLocalProgress();
  if (!profile.available || !profile.mapProgress || typeof profile.mapProgress !== 'object') {
    throw new Error(profile.reason || 'Profile.Save is unavailable');
  }
  const mapNames = JSON.parse(fs.readFileSync(MAPS_PATH, 'utf8'));
  const scannedMaps = new Set(Object.keys(profile.mapProgress)
    .map(name => normalizeMapName(mapNames[name]?.name || name)));
  syncMedalsFromObservations();
  pushLog(job, `medals: loaded ${scannedMaps.size} map records from Profile.Save`);
  return scannedMaps;
}

// Build a stable difficulty-first queue for new sweeps.  Keep maps within each
// difficulty shuffled so repeated passes do not always start at the same tile.
function expertFirstMapOrder(maps) {
  const groups = new Map();
  for (const map of maps) {
    const rank = sweepMapRank(map);
    if (!groups.has(rank)) groups.set(rank, []);
    groups.get(rank).push(map);
  }
  const shuffle = list => {
    const result = list.slice();
    for (let i = result.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [result[i], result[j]] = [result[j], result[i]];
    }
    return result;
  };
  return [...groups.keys()].sort((a, b) => b - a).flatMap(rank => shuffle(groups.get(rank)));
}

function sweepMapRank(map) {
  const rank = mapCategoryRank(map);
  return rank < CATEGORY_ORDER.length ? rank : -1;
}

function buildSweepMapOrder(eligibleMaps, savedOrder, hasConfirmedRemaining) {
  const eligibleSet = new Set(eligibleMaps);
  const reusable = savedOrder.length === eligibleMaps.length
    && new Set(savedOrder).size === savedOrder.length
    && savedOrder.every(map => eligibleSet.has(map));
  // Preserve within-category resume order; repair older queues that put an
  // easier confirmed strategy ahead of every Expert map.
  if (reusable) return savedOrder.slice().sort((a, b) => sweepMapRank(b) - sweepMapRank(a));
  return expertFirstMapOrder(eligibleMaps).sort((a, b) => sweepMapRank(b) - sweepMapRank(a)
    || Number(hasConfirmedRemaining(b)) - Number(hasConfirmedRemaining(a)));
}

// onePerMap is the verification pass: every map without a locally confirmed route gets exactly one
// attempt at its first missing medal, then the pass moves on.
async function runBlackBorderSweep(job, { onePerMap = false } = {}) {
  const progressKey = onePerMap ? 'routeVerification' : 'blackBorderSweep';
  const passName = onePerMap ? 'route verification' : 'black border sweep';
  const saveSweepProgressFor = update => saveSweepProgress(progressKey, update);
  let scannedMaps;
  try { scannedMaps = loadMedalsFromProfileSave(job); }
  catch (error) {
    // Medal data is useful for skipping work, but it must never prevent a
    // sweep from starting. Continue with the route catalog when the save is
    // temporarily unavailable and let each replay verify its own result.
    scannedMaps = null;
    pushLog(job, `Profile.Save unavailable; continuing without medal prefilter (${error.message})`);
  }
  if (job.stopRequested) return;
  const initialMedals = syncMedalsFromObservations();
  const combos = await getAvailableCombos();
  const cfg = JSON.parse(fs.readFileSync(USERCONFIG_PATH, 'utf8'));
  const mapNames = JSON.parse(fs.readFileSync(MAPS_PATH, 'utf8'));
  const allMaps = [...new Set([...Object.keys(combos), ...Object.keys(cfg.unlocked_maps || {})])];
  const savedCompleted = new Set((loadProgress().completedMaps || []).filter(map =>
    MEDAL_MODE_ORDER.every(mode => initialMedals[map]?.[mode] === true)));
  const eligibleMaps = allMaps
    .filter(map => !savedCompleted.has(map))
    .filter(map => !scannedMaps || scannedMaps.has(normalizeMapName(mapNames[map]?.name || map)))
    .filter(map => isMapUnlocked(map) && MEDAL_MODE_ORDER.some(mode => initialMedals[map]?.[mode] !== true))
    .filter(map => !onePerMap || !Object.values(combos[map] || {}).some(entries => entries.some(entry => entry.localWinVerified)))
    ;
  const savedSweep = loadProgress()[progressKey];
  const savedOrder = Array.isArray(savedSweep?.mapOrder) ? savedSweep.mapOrder : [];
  // Prefer confirmed strategies within each category, while keeping the user's
  // Expert-to-Beginner order above route confidence. Both still require a full game.
  const hasConfirmedRemaining = map => getMissingMedals(map, combos)
    .some(mode => sweepCandidates(combos, map, mode).some(entry => entry.localWinVerified));
  const maps = buildSweepMapOrder(eligibleMaps, savedOrder, hasConfirmedRemaining);
  const unscanned = scannedMaps ? allMaps.filter(map => isMapUnlocked(map)
    && MEDAL_MODE_ORDER.some(mode => initialMedals[map]?.[mode] !== true)
    && !scannedMaps.has(normalizeMapName(mapNames[map]?.name || map))) : [];
  if (unscanned.length) pushLog(job, `medal scan did not confirm ${unscanned.length} map tile(s); skipping those maps until a later scan: ${unscanned.join(', ')}`);
  const totalAvailable = maps.reduce((sum, map) => sum + getMissingMedals(map, combos).length, 0);
  const routeAttempts = restoreAttemptsLostToNavigation();
  const counts = { confirmed: 0, failedRoutes: 0, skippedModes: 0, incompleteMaps: 0 };
  let relaunches = 0;
  let focusFailures = 0;
  saveSweepProgressFor({ status: 'running', currentMap: null, gamemode: null, filename: null,
    mapIndex: 0, mapsTotal: maps.length, mapOrder: maps, counts, reason: null, order: 'expert-first' });
  pushLog(job, `${passName}: ${maps.length} maps (Expert â†’ Beginner, shuffled within category), ${totalAvailable} currently unlocked medals queued${onePerMap ? '; one attempt per map' : '; later modes wait for prerequisites'}`);
  pushLog(job, 'sweep engine profile-fallback-2026-10-04: profile readiness ranks routes; live fallback enabled');

  for (const [mapIndex, map] of maps.entries()) {
    if (job.stopRequested) break;
    saveSweepProgressFor({ currentMap: map, mapIndex: mapIndex + 1, gamemode: null, filename: null });
    pushLog(job, `[map ${mapIndex + 1}/${maps.length}] ${map} (${categoryForMapSlug(map) || 'uncategorized'})`);
    const mechanics = getMapMechanics(map);
    if (mechanics.status !== 'standard-visual-check') {
      pushLog(job, `${map} mechanics: ${mechanics.cycle} Â· ${mechanics.status}`);
      for (const rule of mechanics.rules) pushLog(job, `${map} safety: ${rule}`);
      for (const advantage of mechanics.advantages || []) pushLog(job, `${map} opportunity: ${advantage}`);
    }
    if (UNRELIABLE_MAPS.has(map)) {
      counts.incompleteMaps++;
      saveSweepProgressFor({ counts, reason: 'known capture issue' });
      pushLog(job, `${map}: skipping known cash-reading issue; moving to the next map`);
      continue;
    }
    const attempted = new Set();
    const attemptedFilesByMode = {};
    while (!job.stopRequested) {
      syncMedalsFromObservations();
      const gamemode = getMissingMedals(map, combos).find(mode => !attempted.has(mode));
      if (!gamemode) break;
      const entries = rankCandidatesForProfile(sweepCandidates(combos, map, gamemode));
      // A lower difficulty does not make locked route upgrades executable.
      const profileReadyEntries = entries.filter(candidate => !candidate.profileReadiness
        || (candidate.profileReadiness.missing === 0 && candidate.profileReadiness.unknown === 0));
      const triedForMode = routeAttempts[map]?.[gamemode] || {};
      const attemptedFiles = (attemptedFilesByMode[gamemode] ||= new Set());
      // Profile.Save names and upgrade catalogs can differ between game versions. Never turn
      // incomplete profile metadata into an empty sweep: use the best ranked route as a
      // compatibility fallback and let the live replay confirm whether its purchases work.
      const candidatesToTry = profileReadyEntries.length ? profileReadyEntries : entries;
      const entry = candidatesToTry.find(candidate => !attemptedFiles.has(candidate.filename)
        && canAttempt(triedForMode[candidate.filename], routeHash(candidate.filename)));
      if (!entry) {
        counts.skippedModes++;
        attempted.add(gamemode);
        saveSweepProgressFor({ counts });
        if (entries.length && !profileReadyEntries.length) {
          const missing = Math.min(...entries.map(candidate => candidate.profileReadiness?.missing ?? Infinity));
          const unknown = Math.min(...entries.map(candidate => candidate.profileReadiness?.unknown ?? Infinity));
          pushLog(job, `${map} - ${gamemode}: profile metadata is incomplete (best candidate: ${missing} unavailable, ${unknown} unknown); retrying with live route fallback`);
        } else pushLog(job, `${map} - ${gamemode}: exhausted ${entries.length} route candidate(s); skipping this mode for now`);
        continue;
      }
      const fallbackNote = entry.fallbackFor
        ? ` using ${entry.fallbackSource.replace(/_/g, ' ')} route (unverified for ${gamemode.replace(/_/g, ' ')})`
        : '';
      pushLog(job, `running ${map} - ${gamemode} via ${entry.filename}${fallbackNote}`);
      if (entry.profileReadiness) {
        const readiness = entry.profileReadiness;
        pushLog(job, `starter route planner: ranked from Profile.Save â€” ${readiness.missingHero ? 'required hero not unlocked; ' : ''}${readiness.missingTowerUnlocks ? `${readiness.missingTowerUnlocks} required tower unlock(s) missing; ` : ''}${readiness.missing - readiness.missingHero - readiness.missingTowerUnlocks} required upgrade(s) missing; ${readiness.unknown} upgrade name(s) unknown`);
      }
      attemptedFiles.add(entry.filename);
      const hash = routeHash(entry.filename);
      const prior = triedForMode[entry.filename];
      const priorAttempts = prior?.hash === hash ? Number(prior.attempts) || 1 : 0;
      const attemptNumber = priorAttempts + 1;
      saveSweepProgressFor({ gamemode, filename: entry.filename, reason: null });
      const result = await runOne(job, ['file', entry.filename, gamemode, '-mk']);
      if (['game-unavailable', 'invalid-window'].includes(result.reason) && !job.stopRequested
          && relaunches < MAX_GAME_RELAUNCHES
          && await relaunchGame(job, { afterGameError: (result.notable || []).some(line => /GAME_ERROR/.test(line)) })) {
        relaunches++;
        attemptedFiles.delete(entry.filename);   // the crash didn't test the route: run it again
        continue;
      }
      if (['game-unavailable', 'invalid-window', 'spawn-error', 'stop-failed'].includes(result.reason)) {
        job.exitCode = 1;
        saveSweepProgressFor({ status: 'blocked', reason: result.reason, counts });
        pushLog(job, `sweep stopped: ${result.reason}; this interruption did not consume a route attempt. Saved medals remain ready to resume`);
        return;
      }
      if (job.stopRequested) {
        // Whether the user pressed Stop or the stall watchdog (line ~495) killed a hung replay,
        // the route already launched and didn't confirm a clear here - record it the same way the
        // normal failure path below does, or an interrupted/stalled attempt (like a real stuck-menu
        // loop) silently vanishes instead of showing up in the route-failures log.
        if (!confirmClear(map, gamemode, result, line => pushLog(job, line))) {
          recordRouteFailure(map, gamemode, entry.filename, result);
        }
        saveSweepProgressFor({ status: 'stopped', reason: 'stopped by user', counts });
        pushLog(job, 'sweep stopped; unfinished route remains available');
        return;
      }
      if ((result.notable || []).some(line => line.includes('could not be focused'))) {
        // Another window held the foreground (after a VM restart Steam's store sat on top) and
        // every route bailed before playing - 77 attempts burned in one night. A focus failure
        // never tests the route: keep it untried, wait, retry, and stop the sweep if it persists.
        attemptedFiles.delete(entry.filename);
        focusFailures++;
        if (focusFailures >= 3) {
          job.exitCode = 1;
          saveSweepProgressFor({ status: 'blocked', reason: 'BTD6 could not be focused', counts });
          pushLog(job, 'sweep stopped: BTD6 could not be brought to the foreground 3 times; no route attempts were consumed');
          return;
        }
        pushLog(job, `BTD6 could not be focused (${focusFailures}/3); retrying the same route in 15s without consuming an attempt`);
        await new Promise(resolve => setTimeout(resolve, 15000));
        continue;
      }
      focusFailures = 0;
      if ((result.notable || []).some(line => line.includes('MEDAL_ALREADY_EARNED'))) {
        // The mode-select screen shows this medal is already earned: nothing was played, nothing tried.
        attemptedFiles.delete(entry.filename);
        attempted.add(gamemode);
        counts.skippedModes++;
        markMedalSeen(map, gamemode);
        pushLog(job, `${map} - ${gamemode}: medal already earned in game; skipped`);
        saveSweepProgressFor({ counts });
        continue;
      }
      if (result.exitCode !== 0 && (result.notable || []).some(line => /Traceback \(most recent call last\)/i.test(line))
          && !(result.notable || []).some(line => /goal GOTO_INGAME|screen INGAME!/i.test(line))) {
        job.exitCode = result.exitCode || 1;
        saveSweepProgressFor({ status: 'blocked', reason: 'replay crashed before gameplay', counts });
        pushLog(job, `${map}: replay crashed before gameplay; route attempt preserved and sweep paused for repair`);
        return;
      }
      if ((result.notable || []).some(line => /stopping before map click|map page is not visible|map tile did not open/i.test(line))) {
        attemptedFiles.delete(entry.filename);
        pushLog(job, `${map}: map navigation failed before gameplay; keeping route retryable and moving to the next map`);
        saveSweepProgressFor({ reason: 'map navigation failed before gameplay' });
        break;
      }
      const cleared = confirmClear(map, gamemode, result, line => pushLog(job, line));
      routeAttempts[map] ||= {};
      routeAttempts[map][gamemode] ||= {};
      routeAttempts[map][gamemode][entry.filename] = saveRouteAttempt(map, gamemode, entry.filename,
        cleared ? 'cleared' : 'unconfirmed', attemptNumber, hash, result.stallReason || result.reason);
      if (cleared) {
        ensureOutcomeCount(job, 'victory');
        counts.confirmed++;
        attempted.add(gamemode);
        recordObservedClear(map, gamemode);
        markRouteVerified(entry.filename, gamemode);
        pushLog(job, `${map} - ${gamemode} clear confirmed${result.exitCode === 0 ? '' : ` despite replay exit ${result.exitCode}`}`);
      } else {
        if ((result.notable || []).some(line => /screen DEFEAT!/i.test(line))) ensureOutcomeCount(job, 'defeat');
        counts.failedRoutes++;
        pushLog(job, `${map} - ${gamemode} did not confirm a clear on this route; trying the next candidate before skipping the mode`);
        const failure = recordRouteFailure(map, gamemode, entry.filename, result);
        const lossType = failure?.lossType;
        if (lossType) {
          job.lossCounts ||= {};
          job.lossCounts[lossType] = (job.lossCounts[lossType] || 0) + 1;
        }
        const roundText = `${failure?.lastRound ?? '?'}/${failure?.finalRound ?? '?'}`;
        if (lossType === 'instant' || lossType === 'instant-prevented') {
          // A bot-side failure didn't test the route. Give the attempt back (twice per route
          // version) and retry right away; repeated instant losses do count.
          const instantLosses = (prior?.hash === hash ? Number(prior.instantLosses) || 0 : 0) + 1;
          const hints = (result.notable || []).filter(line => /failed at every nearby spot|spent nothing|PLACE_SEARCH .*no legal|INSTANT_LOSS_PREVENTED|recognition error/.test(line)).length;
          if (instantLosses <= 2) {
            routeAttempts[map][gamemode][entry.filename] = saveRouteAttempt(map, gamemode, entry.filename,
              'unconfirmed', priorAttempts, hash, result.stallReason || result.reason, { instantLosses });
            attemptedFiles.delete(entry.filename);
          } else {
            routeAttempts[map][gamemode][entry.filename] = saveRouteAttempt(map, gamemode, entry.filename,
              'unconfirmed', attemptNumber, hash, result.stallReason || result.reason, { instantLosses });
          }
          pushLog(job, `INSTANT_LOSS ${map} - ${gamemode} (${lossType}) round ${roundText}; ${hints} placement/OCR warning(s); `
            + (instantLosses <= 2 ? `attempt not consumed (${instantLosses}/2), retrying` : 'repeated instant loss, attempt counted'));
        } else if (lossType === 'late') {
          queueRouteStrengthening(failure);
          pushLog(job, `LATE_LOSS ${map} - ${gamemode} reached round ${roundText} with $${failure?.cash ?? '?'}; route queued for strengthening`);
        } else if (lossType) {
          pushLog(job, `${lossType.toUpperCase()}_LOSS ${map} - ${gamemode} at round ${roundText} with $${failure?.cash ?? '?'}`);
        }
        const endedAtMenuWithoutResult = result.exitCode === 0 && result.screen === 'STARTMENU'
          && !(result.notable || []).some(line => /screen (DEFEAT|VICTORY|VICTORY_SUMMARY)!/i.test(line));
        if (endedAtMenuWithoutResult && attemptNumber < 2) {
          attemptedFiles.delete(entry.filename);
          pushLog(job, `${map} - ${gamemode}: replay returned to the menu without a result; retrying this route once before switching strategies`);
        }
      }
      saveSweepProgressFor({ counts });
      if (job.stopAfterReplay) {
        job.stopRequested = true;
        saveSweepProgressFor({ status: 'stopped', reason: 'stop after replay', counts });
        pushLog(job, 'current replay result saved; sweep stopped before the next replay');
        return;
      }
      if (onePerMap) break;
    }
    if (job.stopRequested) break;
    const medals = JSON.parse(fs.readFileSync(USERCONFIG_PATH, 'utf8')).medals?.[map] || {};
    const remaining = MEDAL_MODE_ORDER.filter(mode => medals[mode] !== true);
    if (remaining.length) {
      counts.incompleteMaps++;
      pushLog(job, `${map}: ${remaining.length} medal(s) remain without an eligible untried route or with locked prerequisites; moving to the next map`);
    } else {
      savedCompleted.add(map);
      const current = loadProgress();
      current.completedMaps = [...savedCompleted];
      saveProgress(current);
      pushLog(job, `${map}: all medal clears confirmed; removed from future sweep pool`);
    }
    saveSweepProgressFor({ counts });
  }
  saveSweepProgressFor({ status: job.stopRequested ? 'stopped' : 'complete', counts, gamemode: null, filename: null });
  pushLog(job, `${passName} ${job.stopRequested ? 'stopped' : 'complete'} (Expert â†’ Beginner): ${counts.confirmed} clears, ${counts.failedRoutes} failed route attempts, ${counts.incompleteMaps} maps still incomplete`);
}

const SWEEP_ENGINE_VERSION = 'profile-fallback-2026-10-04';
const FARM_TYPES = ['xp', 'mm', 'max-towers', 'random', 'file', 'resume', 'achievements-sweep', 'black-border-sweep', 'verify-routes', 'medal-scan'];
const SWEEP_PROGRESS_KEYS = { 'black-border-sweep': 'blackBorderSweep', 'verify-routes': 'routeVerification' };
function startFarm({ type, n, file, gamemode } = {}) {
  const busy = engineLock.getCurrentJob();
  if (busy) return { error: `already-running (${busy.engine})` };
  if (!FARM_TYPES.includes(type)) return { error: 'unknown type' };
  const runtime = getRuntime();
  if (!runtime.available) {
    const detail = runtime.missing || 'Python runtime unavailable';
    const vcMissing = /msvcp140(?:_1)?\.dll|Microsoft Visual C\+\+|DLL/i.test(detail);
    return { error: vcMissing
      ? 'AutoBTD6 needs the Microsoft C++ runtime. Run the latest BloonsPlusSetup.exe over this installation, then restart Bloons+.'
      : `AutoBTD6 needs ${detail}` };
  }
  if (type === 'file' && !file) return { error: 'file required' };
  if (type === 'resume') {
    const checkpoint = loadRouteCheckpoint();
    if (checkpoint?.status !== 'ready' || !checkpoint.filename) {
      return { error: 'no unambiguous replay checkpoint to resume' };
    }
    file = checkpoint.filename;
    gamemode = checkpoint.gamemode;
  }
  if (type === 'file') {
    const pt = parsePlaythroughFile(file);
    if (pt.isBossRoute) {
      // Real, honest limitation (not a map-unlock problem): the replay engine has no
      // screen recognizer for BTD6's Boss Events menu yet, so it can't navigate there
      // on its own. Say so plainly instead of either a misleading "not unlocked" error
      // or silently attempting a run that would fail deep inside replay.py.
      const bossName = pt.bossType.charAt(0).toUpperCase() + pt.bossType.slice(1);
      return { error: `Boss Events navigation isn't automated yet â€” the route for ${bossName} (${pt.bossVariant}) on ${pt.map} was generated, but running it needs the Boss Events menu recognizer built first.` };
    }
    if (MODES_REQUIRING_VERIFIED_ROUTE.has(gamemode || pt.gamemodeSlug) && pt.generated) {
      return { error: `generated route is draft-only for ${gamemode || pt.gamemodeSlug}; use a dedicated or previously verified route` };
    }
    if (!isMapUnlocked(pt.mapSlug)) return { error: `map not unlocked yet: ${pt.map}` };
    const mode = gamemode || pt.gamemodeSlug;
    const route = getRecordedCombos()[pt.mapSlug]?.[mode]?.find(candidate => candidate.filename === file);
    if (route) {
      const readiness = rankCandidatesForProfile([route])[0]?.profileReadiness;
      if (readLocalProgress().available && readiness && (readiness.missing > 0 || readiness.unknown > 0)) {
        return { error: `route prerequisites do not match the saved profile (${readiness.missing} unavailable upgrade/tower/hero requirement(s), ${readiness.unknown} unknown upgrade(s)); choose a compatible route` };
      }
    }
  }

  const job = engineLock.beginJob('autobtd6', type);
  if (!job) return { error: 'already-running' };
  // Runs on every way a job can end â€” natural exit or the shared Stop â€” so the last run is always
  // saved for the status panel even across restarts.
  job.onEnd = ended => {
    const progress = loadProgress();
    const sweep = progress[SWEEP_PROGRESS_KEYS[ended.type]];
    if (sweep?.status === 'running') {
      Object.assign(sweep, { status: ended.stopRequested ? 'stopped' : 'failed', updatedAt: new Date().toISOString() });
    }
    progress.lastRun = { type: ended.type, startedAt: ended.startedAt, endedAt: ended.endedAt,
      exitCode: ended.exitCode ?? null, victories: ended.victories || 0, defeats: ended.defeats || 0,
      stopAfterReplay: !!ended.stopAfterReplay, log: ended.log.slice(-2000) };
    saveProgress(progress);
  };

  const clearOnClose = (code = 0) => {
    try { const pauseFile = path.join(AUTOBTD6_DIR, 'pause.flag'); if (fs.existsSync(pauseFile)) fs.unlinkSync(pauseFile); } catch {}
    job.exitCode = Number.isInteger(code) ? code : null;
    if (job.exitCode !== 0 && !job.stopRequested) pushLog(job, `replay ended with exit code ${job.exitCode ?? 'unknown'}; see the lines above for the cause`);
    engineLock.endJob(job);
  };
  if (type === 'xp' || type === 'mm') {
    afterCountdown(job, () => { wireProcess(job, spawnReplay([type, String(n || 5), '-mk', '-r'])); job.proc.on('close', clearOnClose); });
  } else if (type === 'max-towers') {
    afterCountdown(job, () => {
      // Prefer the read-only Steam save over OCR observations. This gives a stable,
      // complete inventory before the loop and avoids buying upgrades blindly.
      const local = readLocalProgress();
      const xp = local.available && local.towerXp && typeof local.towerXp === 'object' ? local.towerXp : {};
      const names = Object.keys(xp);
      const missing = local.available ? (local.unlockedTowers || []).filter(name => !(name in xp)) : [];
      pushLog(job, `max towers: save scan ${local.available ? 'ok' : 'unavailable'} Â· ${names.length} XP records Â· ${missing.length} unlocked towers without a record`);
      if (local.available) {
        const ordered = names.map(name => [name, Number(xp[name]) || 0]).sort((a, b) => a[1] - b[1]);
        ordered.slice(0, 8).forEach(([name, value]) => pushLog(job, `max towers target: ${name} Â· XP ${value.toLocaleString()}`));
        pushLog(job, `max towers: ${local.acquiredUpgrades?.length || 0} upgrades recorded Â· ${local.paragonUpgradesPurchased?.length || 0} paragon upgrades`);
      }
      pushLog(job, 'max towers: starting Monkey Meadows XP loop; progress is re-read after each run');
      wireProcess(job, spawnReplay(['xp', '1', '-mk', '-r']));
      job.proc.on('close', code => {
        const after = readLocalProgress();
        if (after.available) {
          const values = Object.values(after.towerXp || {}).map(Number).filter(Number.isFinite);
          pushLog(job, `max towers: post-run save refresh Â· ${values.length} tower XP records Â· ${after.acquiredUpgrades?.length || 0} upgrades recorded`);
        } else pushLog(job, `max towers: post-run save refresh unavailable (${after.reason || 'unknown reason'})`);
        clearOnClose(code);
      });
    });
  } else if (type === 'random') {
    afterCountdown(job, () => { wireProcess(job, spawnReplay(['random', '-mk', '-r'])); job.proc.on('close', clearOnClose); });
  } else if (type === 'file' || type === 'resume') {
    const targetMode = gamemode || parsePlaythroughFile(file).gamemodeSlug;
    const mapSlug = parsePlaythroughFile(file).mapSlug;
    const winsBefore = routeWins(file, targetMode);
    const hadMedal = JSON.parse(fs.readFileSync(USERCONFIG_PATH, 'utf8')).medals?.[mapSlug]?.[targetMode] === true;
    const args = ['file', file, targetMode, ...(type === 'resume' ? ['resume'] : []), '-mk'];
    afterCountdown(job, () => {
      runOne(job, args).then(result => {
        const plausible = hadMedal || confirmClear(mapSlug, targetMode, result, line => pushLog(job, line));
        if (!plausible && !job.stopRequested) {
          try { recordRouteFailure(mapSlug, targetMode, file, result); } catch (error) { pushLog(job, `could not record route failure: ${error.message}`); }
        }
        const checkpoint = loadRouteCheckpoint();
        const checkpointWon = type === 'resume' && checkpoint?.status === 'victory';
        if (plausible && result.exitCode === 0 && (!hadMedal || checkpointWon)) {
          ensureOutcomeCount(job, 'victory');
          try {
            recordObservedClear(mapSlug, targetMode);
            pushLog(job, `medal saved: ${mapSlug} - ${targetMode}`);
          } catch (error) { pushLog(job, `could not save observed medal: ${error.message}`); }
        }
        if (!plausible && (result.notable || []).some(line => /screen DEFEAT!/i.test(line))) ensureOutcomeCount(job, 'defeat');
        if (plausible && (routeWins(file, targetMode) > winsBefore || checkpointWon)) {
          try {
            markRouteVerified(file, targetMode);
            pushLog(job, `route verified by a recorded victory: ${file} on ${targetMode}`);
          } catch (error) { pushLog(job, `could not save route verification: ${error.message}`); }
        }
        clearOnClose(result.exitCode);
        const interruptedSweep = checkpoint?.parentJob === 'black-border-sweep'
          || loadProgress().blackBorderSweep?.status === 'running';
        if (type === 'resume' && result.exitCode === 0 && checkpointWon && plausible && interruptedSweep) {
          setTimeout(() => {
            if (!engineLock.getCurrentJob()) startFarm({ type: 'black-border-sweep' });
          }, 1000);
        }
      }, error => { pushLog(job, `replay failed: ${error.message}`); clearOnClose(1); });
    });
  } else if (type === 'achievements-sweep') {
    afterCountdown(job, () => {
      runAchievementsSweep(job).then(() => clearOnClose(job.exitCode ?? 0),
        error => { pushLog(job, `sweep failed: ${error.message}`); clearOnClose(1); });
    });
  } else if (type === 'black-border-sweep' || type === 'verify-routes') {
    afterCountdown(job, () => {
      runBlackBorderSweep(job, { onePerMap: type === 'verify-routes' }).then(
        () => clearOnClose(Number.isInteger(job.exitCode) ? job.exitCode : 0),
        error => { pushLog(job, `sweep failed safely: ${error.message}`); clearOnClose(1); },
      );
    });
  } else if (type === 'medal-scan') {
    afterCountdown(job, () => {
      try { loadMedalsFromProfileSave(job); clearOnClose(0); }
      catch (error) { pushLog(job, `Profile.Save medal refresh failed: ${error.message}`); clearOnClose(1); }
    });
  }
  return { ok: true };
}

function togglePause() {
  const job = engineLock.getCurrentJob();
  if (!job || job.engine !== 'autobtd6') return { error: 'no running automation' };
  job.paused = !job.paused;
  job.replayMonitor?.setPaused(job.paused);
  const pauseFile = path.join(AUTOBTD6_DIR, 'pause.flag');
  try { if (job.paused) fs.writeFileSync(pauseFile, new Date().toISOString()); else if (fs.existsSync(pauseFile)) fs.unlinkSync(pauseFile); } catch (error) { pushLog(job, `pause flag update failed: ${error.message}`); }
  pushLog(job, job.paused ? 'PAUSED by user; checkpoint preserved' : 'RESUMED by user');
  return { ok: true, paused: job.paused };
}

function stopAfterReplay() {
  const job = engineLock.getCurrentJob();
  if (!job || job.engine !== 'autobtd6') return { error: 'no running automation' };
  job.stopAfterReplay = true;
  pushLog(job, 'STOP AFTER REPLAY requested; the current replay will finish normally');
  return { ok: true, stopAfterReplay: true };
}

// Stop is shared across every engine â€” only one can ever be running.
async function stopFarm() {
  const job = engineLock.getCurrentJob();
  const result = await engineLock.stopCurrent();
  if (result.ok && job?.engine === 'autobtd6' && job.type !== 'medal-scan') {
    const checkpoint = loadRouteCheckpoint();
    if (checkpoint && ['ready', 'pending'].includes(checkpoint.status)) {
      checkpoint.status = 'paused';
      checkpoint.pausedAt = new Date().toISOString();
      saveRouteCheckpoint(checkpoint);
    }
  }
  return result;
}

function resumePendingReplay() {
  const checkpoint = loadRouteCheckpoint();
  if (checkpoint?.status !== 'ready' || engineLock.getCurrentJob()) return;
  // A surviving child may still be controlling the game after the UI closes.
  const probe = spawnSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command',
    "$p = Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'replay[.]py' }; if ($p) { 'busy' }"],
    { windowsHide: true, timeout: 5000, encoding: 'utf8' });
  if (probe.error || probe.status !== 0 || probe.stdout.includes('busy')) return;
  console.log(`Resuming interrupted replay: ${checkpoint.map} ${checkpoint.gamemode} step ${checkpoint.nextStep}`);
  const result = startFarm({ type: 'resume' });
  if (result.error) console.warn('Replay resume deferred:', result.error);
}

function getStatus() {
  const saved = loadProgress();
  const job = engineLock.getCurrentJob();
  if (job?.engine === 'autobtd6') {
    return { running: true, stopping: job.stopRequested, stopAfterReplay: !!job.stopAfterReplay, paused: !!job.paused, replay: job.replay,
      type: job.type, startedAt: job.startedAt, log: job.log.slice(-2000), victories: job.victories || 0, defeats: job.defeats || 0,
      lossCounts: job.lossCounts || {},
      progress: saved, runtime: getRuntime(), checkpoint: loadRouteCheckpoint() };
  }
  const previous = engineLock.getLastJob('autobtd6') || saved.lastRun;
  return { running: false, busyWith: job?.engine || null, type: previous?.type, endedAt: previous?.endedAt,
    exitCode: previous?.exitCode, log: previous?.log?.slice(-2000) || [], victories: previous?.victories || 0, defeats: previous?.defeats || 0,
    progress: saved, runtime: getRuntime(), checkpoint: loadRouteCheckpoint() };
}

// Live route editing: replay.py re-reads the .btd6 file fresh on every run (no
// VM/app restart needed), so a route can be patched between sweep passes while
// the sweep itself keeps going. Filename is restricted to the exact set the
// sweep itself produces/consumes - no path separators, no traversal.
function safePlaythroughPath(file) {
  if (typeof file !== 'string' || !/^[a-zA-Z0-9_#.-]+\.btd6$/.test(file) || file.includes('..')) {
    throw new Error('Invalid playthrough filename');
  }
  return path.join(PLAYTHROUGHS_DIR, file);
}
function getPlaythroughContent(file) {
  return fs.readFileSync(safePlaythroughPath(file), 'utf8');
}
function savePlaythroughContent(file, content) {
  const target = safePlaythroughPath(file);
  if (!fs.existsSync(target)) throw new Error(`No such playthrough: ${file}`);
  const backupDir = path.join(PLAYTHROUGHS_DIR, '..', 'playthroughs_live_edit_backups');
  fs.mkdirSync(backupDir, { recursive: true });
  fs.writeFileSync(path.join(backupDir, `${file}.${Date.now()}.bak`), fs.readFileSync(target));
  fs.writeFileSync(target, content, 'utf8');
  return { file, bytes: Buffer.byteLength(content, 'utf8') };
}

module.exports = { getRuntime, listPlaythroughs, getAvailableCombos, startFarm, stopFarm, stopAfterReplay, togglePause, getStatus, resumePendingReplay, getHeroes, setHeroes, mapCategoryRank, mapCatalogOrder, categoryForMapSlug, buildSweepMapOrder, getPlaythroughContent, savePlaythroughContent };
