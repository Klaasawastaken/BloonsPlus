// Writes route-coverage.json: for every map in map-catalog.js and each of the 14 medal modes, the
// routes the black-border sweep would actually pick. The route logic is not reimplemented: the
// functions getRecordedCombos/sweepCandidates (and their helpers/constants) are cut out of
// automation.js at run time and evaluated in a sandbox, so this report follows automation.js even
// when it changes. Usage: node route-coverage-report.js [--out file] [--quiet]
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { createHash } = require('node:crypto');

const ROOT = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(ROOT, 'lib', 'automation.js'), 'utf8');

// Extracts one top-level declaration by counting braces/brackets/parens from its first opener,
// skipping over string/template/regex literals and comments so characters inside them (e.g. a
// '}' in a template string) don't throw off the depth count.
function cut(startPattern) {
  const start = source.search(startPattern);
  if (start < 0) throw new Error(`automation.js no longer contains ${startPattern}`);
  // "function f(params) { body }" has two sibling groups at depth 0 (the param list, then the
  // body); a plain depth counter would stop after the param list's closing ")". Track the stack
  // of opener kinds instead, and only finish on a "}" that closes a top-level "{" body, or on a
  // top-level ";" (for "const X = ...;" declarations).
  let i = start;
  const stack = [];
  for (; i < source.length; i++) {
    const c = source[i];
    if (c === '/' && source[i + 1] === '/') { i = source.indexOf('\n', i); if (i < 0) break; continue; }
    if (c === '/' && source[i + 1] === '*') { i = source.indexOf('*/', i) + 1; continue; }
    if (c === '"' || c === "'" || c === '`') {
      const quote = c;
      for (i++; i < source.length; i++) {
        if (source[i] === '\\') { i++; continue; }
        if (source[i] === quote) break;
      }
      continue;
    }
    if (c === '{' || c === '(' || c === '[') stack.push(c);
    else if (c === '}' || c === ')' || c === ']') {
      const opener = stack.pop();
      if (stack.length === 0) {
        i++;
        if (opener === '{') break;   // end of a function/object body at top level
        // else: end of a top-level (...) or [...] — a param list or array; keep scanning for
        // the body/statement terminator that follows.
      }
    } else if (c === ';' && stack.length === 0) { i++; break; }
  }
  return source.slice(start, i);
}
const pieces = [
  /^const AUTOBTD6_DIR = /m, /^const PLAYTHROUGHS_DIR = /m, /^const ROUTE_VERIFICATION_PATH = /m,
  /^const ONLINE_GUIDE_SOURCES_PATH = /m, /^const STATS_PATH = /m, /^const CHIMPS_REUSE_MODES = /m,
  /^const HARD_REUSE_MODES = /m, /^const REUSE_MODES_BY_SOURCE = /m,
].map(pattern => source.slice(source.search(pattern)).split('\n')[0]);
const functions = [
  /^function parsePlaythroughFile\(/m, /^function listPlaythroughs\(/m, /^function routeHash\(/m,
  /^function loadVerifiedRoutes\(/m, /^function routeRequirements\(/m, /^function getRecordedCombos\(/m,
  /^const MODES_REQUIRING_VERIFIED_ROUTE = /m, /^function sweepCandidates\(/m,
].map(cut);
const sandbox = { require: require('node:module').createRequire(path.join(ROOT, 'lib', 'automation.js')), __dirname: ROOT, PROJECT_ROOT: ROOT, fs, path, createHash, result: null };
vm.createContext(sandbox);
vm.runInContext(`${pieces.join('\n')}\n${functions.join('\n')}\n
result = { getRecordedCombos, sweepCandidates, MODES_REQUIRING_VERIFIED_ROUTE: [...MODES_REQUIRING_VERIFIED_ROUTE], listPlaythroughs };`, sandbox);
const { getRecordedCombos, sweepCandidates, MODES_REQUIRING_VERIFIED_ROUTE, listPlaythroughs } = sandbox.result;

const MODES = ['easy', 'primary_only', 'deflation', 'medium', 'military_only', 'reverse', 'apopalypse',
  'hard', 'magic_monkeys_only', 'double_hp_moabs', 'half_cash', 'alternate_bloons_rounds', 'impoppable', 'chimps'];
const normalize = s => s.toLowerCase().replace(/[^a-z0-9]/g, '');
const catalogSource = fs.readFileSync(path.join(ROOT, 'data', 'catalogs', 'map-catalog.js'), 'utf8');
const catalog = JSON.parse(`{${catalogSource.match(/\{([\s\S]*)\}/)[1]}}`);
const maps = JSON.parse(fs.readFileSync(path.join(ROOT, 'autobtd6', 'maps.json'), 'utf8'));
const slugByName = new Map(Object.entries(maps).map(([slug, entry]) => [normalize(entry.name || slug), slug]));

const combos = getRecordedCombos();
const drafts = listPlaythroughs().filter(pt => pt.generated);
const report = { generatedAt: new Date().toISOString(), modes: MODES,
  rules: 'Routes counted exactly as automation.js getRecordedCombos() + sweepCandidates() select them: '
    + 'non-generated files in autobtd6/playthroughs, class-only modes need class-only towers, CHIMPS routes '
    + 'are reused for easy/medium/hard standard and impoppable, Hard routes are further reused for '
    + `easy/medium, and modes ${MODES_REQUIRING_VERIFIED_ROUTE.join(', ')} `
    + 'accept only dedicated or CHIMPS-reused routes that are not unverified guide adaptations. Generated drafts are listed separately and never count. Runtime additionally preflights each candidate against saved hero, tower, and upgrade unlocks; routes with missing or unknown prerequisites are skipped before launch.',
  summary: {}, maps: {} };
let covered = 0, total = 0;
const perMode = Object.fromEntries(MODES.map(mode => [mode, 0]));
for (const [category, names] of Object.entries(catalog)) {
  for (const name of names) {
    const slug = slugByName.get(normalize(name)) || name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
    const entry = { name, category, slug, inMapsJson: !!maps[slug], modes: {} };
    for (const mode of MODES) {
      total++;
      const candidates = sweepCandidates(combos, slug, mode);
      const draftFiles = drafts.filter(pt => pt.mapSlug === slug && pt.gamemodeSlug === mode).map(pt => pt.file);
      if (candidates.length) {
        covered++; perMode[mode]++;
        entry.modes[mode] = candidates.map(c => c.reusedFromChimps ? `${c.filename} (CHIMPS reuse)` : c.filename);
      } else entry.modes[mode] = draftFiles.length ? { status: 'missing', draftsOnly: draftFiles } : 'missing';
    }
    report.maps[slug] = entry;
  }
}
const mapsFull = Object.values(report.maps).filter(m => Object.values(m.modes).every(v => Array.isArray(v))).length;
const mapsNone = Object.values(report.maps).filter(m => Object.values(m.modes).every(v => !Array.isArray(v))).length;
report.summary = { maps: Object.keys(report.maps).length, mapModePairs: total, covered, missing: total - covered,
  mapsFullyCovered: mapsFull, mapsWithNoRoute: mapsNone, coveredPerMode: perMode };
const outIndex = process.argv.indexOf('--out');
const out = outIndex > 0 ? process.argv[outIndex + 1] : path.join(ROOT, 'route-coverage.json');
fs.writeFileSync(out, JSON.stringify(report, null, 2));
if (!process.argv.includes('--quiet')) console.log(JSON.stringify(report.summary, null, 2));
