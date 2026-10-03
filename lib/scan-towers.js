const PROJECT_ROOT = require('node:path').resolve(__dirname, '..');
// Tower XP scan — navigation and grid layout are confirmed live and correct; OCR reliability is
// NOT solved yet, so this does not persist results and isn't wired into anything. Read this before
// touching it again.
//
// Confirmed live (2026-09-26): the Towers screen (main menu's MONKEYS icon) is a grid overview per
// category tab (Primary/Military/Magic/Support) showing every tower's name AND XP simultaneously —
// not a per-tower detail view, not a scrolling list (Primary/Military/Magic have 7 towers, Support
// has 5; all fit on one screen per tab, confirmed no paging needed). The ROW1_X/ROW2_X/*_Y
// constants below are measured directly against a real capture (auto-detected via the cards' own
// light-blue fill color) and are correct.
//
// What's NOT solved: OCR of both the title and the XP number on this screen is unreliable with the
// same two-sided luminance threshold that works for achievements, for two DIFFERENT reasons unique
// to this screen:
//   - Card titles float over the busy photographic menu background (sky/buildings/foliage), not a
//     flat backdrop — that background's own bright/dark patches get misclassified as text, corrupting
//     both tightenBox's bounding box and the OCR result. Achievements' titles sit over a much flatter
//     background, which is why that same code works fine there.
//   - XP numbers are dark-green fill on a light-blue GRADIENT card background whose brightness varies
//     by position — bright enough in places to exceed the default highThreshold (190), so the
//     "bright fill" branch of the two-sided rule marks swaths of background as text too. A
//     single-sided dark-only classify (see ocr.js's new `classify` option) fixed some cases but was
//     still inconsistent card-to-card in testing (confirmed: correct on some towers, wrong digit
//     count on others) — not reliable enough to persist as real data.
// A wrong XP number is worse than no XP number, so this must not write plausible-looking wrong
// values. Don't re-enable persistence until OCR is actually verified accurate across all 26 towers,
// not just spot-checked.
const fs = require('node:fs');
const path = require('node:path');
const { moveMouseTo, click } = require('./input');
const { captureWindow, focusWindow } = require('./capture');
const { readTitle, readDigits } = require('./ocr');
const { readPng } = require('./pixels');
const { PNG } = require('pngjs');

const observationsPath = path.join(PROJECT_ROOT, 'game-observations.json');
const knownTowers = {
  primary: ['Dart Monkey', 'Boomerang Monkey', 'Bomb Shooter', 'Tack Shooter', 'Ice Monkey', 'Glue Gunner', 'Desperado'],
  military: ['Sniper Monkey', 'Monkey Sub', 'Monkey Buccaneer', 'Monkey Ace', 'Heli Pilot', 'Mortar Monkey', 'Dartling Gunner'],
  magic: ['Wizard Monkey', 'Super Monkey', 'Ninja Monkey', 'Alchemist', 'Druid', 'Mermonkey', 'Skywarden'],
  support: ['Banana Farm', 'Spike Factory', 'Monkey Village', 'Engineer Monkey', 'Beast Handler'],
};
const normalize = name => name.toLowerCase().replace(/[^a-z]/g, '');
function similarity(a, b) {
  a = normalize(a); b = normalize(b);
  const dp = Array.from({ length: a.length + 1 }, (_, i) => [i]);
  for (let j = 0; j <= b.length; j++) dp[0][j] = j;
  for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++) {
    dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
  }
  return 1 - dp[a.length][b.length] / Math.max(1, a.length, b.length);
}
function matchTower(readName, category, minScore = 0.72) {
  const candidates = category ? knownTowers[category] : Object.values(knownTowers).flat();
  const matches = candidates.map(name => ({ name, score: similarity(readName, name) })).sort((a, b) => b.score - a.score);
  return matches[0]?.score >= minScore && (!matches[1] || matches[0].score - matches[1].score >= 0.12) ? matches[0].name : null;
}
function scalePoint(point, size) { return { x: Math.round(point.x * size.width / 2560), y: Math.round(point.y * size.height / 1440) }; }
function scaleBox(box, size) { return { x: Math.round(box.x * size.width / 2560), y: Math.round(box.y * size.height / 1440), w: Math.round(box.w * size.width / 2560), h: Math.round(box.h * size.height / 1440) }; }

const BACK_BUTTON = { x: 111, y: 115 };
const MONKEYS_ICON = { x: 390, y: 1245 };
const CATEGORY_TABS = {
  primary: { x: 725, y: 1320 },
  military: { x: 1050, y: 1320 },
  magic: { x: 1380, y: 1320 },
  support: { x: 1700, y: 1320 },
};

// Rough (not pixel-tuned) boxes — tightenBox (in ocr.js) crops to the actual text within each.
// Row 1 is 4 cards, row 2 is 3 cards centered under it (confirmed live, consistent across all
// four category tabs). Measured directly against a real 2560x1440 capture (auto-detected via the
// cards' own light-blue fill color, not eyeballed off a downscaled preview — an earlier eyeballed
// pass was off by exactly the preview's display-scale factor and produced garbled OCR).
const ROW1_X = [665, 1081, 1496, 1911];
const ROW2_X = [868, 1290, 1710];
const ROW1_NAME_BOX = { w: 320, h: 90 };
const ROW1_XP_BOX = { w: 280, h: 55 };
const ROW2_NAME_BOX = { w: 380, h: 90 };
const ROW2_XP_BOX = { w: 300, h: 55 };
const ROW1_NAME_Y = 170, ROW1_XP_Y = 565;
const ROW2_NAME_Y = 635, ROW2_XP_Y = 1030;

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

// A tower's own card art from the Towers screen, cropped once per tower (first confident read
// wins, like map-icons). Position-only crop: doesn't depend on the XP OCR this file's header says
// is unreliable, so it's safe to capture regardless of whether xp parsed on that pass.
const TOWER_ICON_DIR = path.join(PROJECT_ROOT, 'tower-icons');
const towerIconSlug = name => name.toLowerCase().replace(/[^a-z0-9]+/g, '-');
function saveTowerIcon(image, box, name) {
  const file = path.join(TOWER_ICON_DIR, `${towerIconSlug(name)}.png`);
  if (fs.existsSync(file)) return;
  fs.mkdirSync(TOWER_ICON_DIR, { recursive: true });
  const out = new PNG({ width: 220, height: Math.round(220 * box.h / box.w) });
  for (let y = 0; y < out.height; y++) {
    for (let x = 0; x < out.width; x++) {
      const [r, g, b] = image.get(box.x + x * box.w / out.width, box.y + y * box.h / out.height);
      const i = (out.width * y + x) << 2;
      out.data[i] = r; out.data[i + 1] = g; out.data[i + 2] = b; out.data[i + 3] = 255;
    }
  }
  fs.writeFileSync(file, PNG.sync.write(out));
}


function centeredBox(centerX, y, size) {
  return { x: centerX - size.w / 2, y, w: size.w, h: size.h };
}

function loadObservations() {
  try { return JSON.parse(fs.readFileSync(observationsPath, 'utf8')); }
  catch { return { source: 'live-scan', maps: {}, towers: {}, achievements: {}, player: null }; }
}

async function navigateToTowers(size) {
  const back = scalePoint(BACK_BUTTON, size);
  const monkeys = scalePoint(MONKEYS_ICON, size);
  for (let i = 0; i < 3; i++) {
    await moveMouseTo(back.x, back.y, { durationMs: 200 });
    await click();
    await sleep(400);
  }
  await moveMouseTo(monkeys.x, monkeys.y, { durationMs: 300 });
  await click();
  await sleep(700);
}

// Reads every card on the currently-visible category tab. A slot with no card (Support's row 2
// only has 2, not 3) reads empty/garbage from tightenBox finding nothing meaningful — skipped by
// requiring a non-empty name.
async function scanVisibleCategory(png, size, category, minScore = 0.72) {
  const results = [];
  const slots = [
    ...ROW1_X.map(x => ({ name: centeredBox(x, ROW1_NAME_Y, ROW1_NAME_BOX), xp: centeredBox(x, ROW1_XP_Y, ROW1_XP_BOX),
      art: { x: x - ROW1_NAME_BOX.w / 2, y: ROW1_NAME_Y + ROW1_NAME_BOX.h, w: ROW1_NAME_BOX.w, h: ROW1_XP_Y - (ROW1_NAME_Y + ROW1_NAME_BOX.h) } })),
    ...ROW2_X.map(x => ({ name: centeredBox(x, ROW2_NAME_Y, ROW2_NAME_BOX), xp: centeredBox(x, ROW2_XP_Y, ROW2_XP_BOX),
      art: { x: x - ROW2_NAME_BOX.w / 2, y: ROW2_NAME_Y + ROW2_NAME_BOX.h, w: ROW2_NAME_BOX.w, h: ROW2_XP_Y - (ROW2_NAME_Y + ROW2_NAME_BOX.h) } })),
  ];
  let image = null;
  for (let index = 0; index < slots.length; index++) {
    const slot = slots[index];
    const readName = (await readTitle(png, scaleBox(slot.name, size), { tighten: true })).trim();
    const name = readName.length >= 3 ? matchTower(readName, category, minScore) : null;
    if (!name) continue;
    if (minScore >= 0.85) {
      try { image ||= readPng(png); saveTowerIcon(image, scaleBox(slot.art, size), name); } catch { /* thumbnails are optional */ }
    }
    const xp = await readDigits(png, scaleBox(slot.xp, size));
    if (!Number.isInteger(xp) || xp < 0) continue;
    results.push({ index, name, xp });
  }
  return results;
}

// Passive reader: only inspects the screenshot already captured by scanner.js. No clicks,
// category changes, or movement. Requires two distinct, clearly recognized tower cards.
async function scanVisibleTowerPage(png, size) {
  const cards = await scanVisibleCategory(png, size, null, 0.88);
  const unique = cards.filter((card, index) => cards.findIndex(other => other.name === card.name) === index);
  return unique.length >= 2 ? unique : [];
}

// Does NOT persist to game-observations.json — see the file header. `persist: true` is a manual
// override for testing, only, once OCR is actually fixed; the default is read-only so this can be
// safely re-run to check progress without risking corrupting real tower data with a wrong number.
async function scanTowers({ onProgress, persist = false } = {}) {
  await focusWindow();
  const initial = await captureWindow();
  await navigateToTowers(initial);

  const observations = loadObservations();
  observations.towers = observations.towers || {};

  let scanned = 0;
  for (const [category, tab] of Object.entries(CATEGORY_TABS)) {
    const point = scalePoint(tab, initial);
    await moveMouseTo(point.x, point.y, { durationMs: 250 });
    await click();
    await sleep(500);
    const first = await captureWindow();
    const cards = await scanVisibleCategory(first.png, first, category);
    await sleep(200);
    const second = await captureWindow();
    const verification = await scanVisibleCategory(second.png, second, category);
    const verified = cards.filter(card => verification.some(other => other.index === card.index && other.name === card.name && other.xp === card.xp));
    for (const { name, xp } of verified) {
      observations.towers[name] = { ...(observations.towers[name] || {}), xp, category, xpVerifiedAt: new Date().toISOString() };
      scanned++;
    }
    onProgress?.(category, verified);
  }

  if (persist) {
    observations.capturedAt = new Date().toISOString();
    fs.writeFileSync(observationsPath, JSON.stringify(observations, null, 2));
  }
  return { scanned, towers: observations.towers };
}

module.exports = { scanTowers, scanVisibleTowerPage };

if (require.main === module) {
  scanTowers({
    onProgress: (category, cards) => console.log(`${category}: ${cards.map(c => `${c.name}=${c.xp}`).join(', ')}`),
  }).then(r => console.log('done (not saved — see file header):', JSON.stringify({ scanned: r.scanned }))).catch(e => { console.error('ERROR:', e.stack); process.exit(1); });
}
