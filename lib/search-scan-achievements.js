const PROJECT_ROOT = require('node:path').resolve(__dirname, '..');
// Fully automated achievement scan via the Achievements screen's own search box: for each
// catalog name, type it in (filters to exactly one result), read that result's status from a
// fixed position, move on. No scrolling, no grid/header-overlap issues, no fuzzy title matching
// needed (we searched the exact name) — far more reliable than scanning the scrolling grid, and
// needs no user interaction at all once positioned on the Achievements screen.
//
// A completed achievement can never become uncompleted, so once game-observations.json has one
// marked "completed" this skips searching it again on future runs — only in-progress/unknown
// ones get re-checked, making repeat runs much faster.
const fs = require('node:fs');
const path = require('node:path');
const { moveMouseTo, click, clearField, typeText } = require('./input');
const { captureWindow, focusWindow } = require('./capture');
const { readTitle, readPercent } = require('./ocr');
const { loadCatalog, similarityRatio } = require('./scan-achievements');

const observationsPath = path.join(PROJECT_ROOT, 'game-observations.json');

const SEARCH_BOX = { x: 1650, y: 346 };
const MAIN_MENU_ACHIEVEMENTS_ICON = { x: 144, y: 614 };
const BACK_BUTTON = { x: 163, y: 106 };
// A result card shows one of two layouts: an in-progress one with a reward icon + "NN%" on the
// right, or a completed one with just "COMPLETE" centered-left (no icon, no percentage at all —
// confirmed live). Rough (not pixel-tuned) boxes — tightenBox (in ocr.js) finds the actual text
// within each — but the two must stay separate: a box wide enough to span both would also catch
// the reward icon in the in-progress layout and confuse single-word percent reading.
const PERCENT_ROUGH_BOX = { x: 1480, y: 800, w: 350, h: 150 };
const COMPLETE_ROUGH_BOX = { x: 600, y: 800, w: 750, h: 150 };
const RESULT_TITLE_ROUGH_BOX = { x: 550, y: 470, w: 900, h: 110 };

// Every box above was measured against a 3840x2160 capture. Scale it against whatever the
// actual capture reports so the same layout still lands correctly on a different monitor/
// resolution (e.g. a 2560x1440 second monitor) without re-measuring anything by hand.
const REFERENCE = { w: 3840, h: 2160 };
function scaleBox(box, capW, capH) {
  const sx = capW / REFERENCE.w, sy = capH / REFERENCE.h;
  const scaled = { x: box.x * sx, y: box.y * sy };
  if (box.w != null) scaled.w = box.w * sx;
  if (box.h != null) scaled.h = box.h * sy;
  return scaled;
}

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

function idFor(name) { return `steam-${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`; }

// A couple of catalog names have a clause after " - " or ":" (e.g. "What did it cost? -
// Everything:") that either doesn't display well in the search box or just isn't needed —
// searching the part before it is still specific enough to find the one match.
function searchQueryFor(name) {
  const cut = name.search(/ - |:/);
  return (cut === -1 ? name : name.slice(0, cut)).trim();
}

function loadObservations() {
  try { return JSON.parse(fs.readFileSync(observationsPath, 'utf8')); }
  catch { return { source: 'live-scan', maps: {}, towers: {}, achievements: {}, player: null }; }
}

async function navigateToAchievements(points) {
  for (let i = 0; i < 3; i++) {
    await moveMouseTo(points.backButton.x, points.backButton.y, { durationMs: 200 });
    await click();
    await sleep(400);
  }
  await moveMouseTo(points.achievementsIcon.x, points.achievementsIcon.y, { durationMs: 300 });
  await click();
  await sleep(700);
  await moveMouseTo(points.searchBox.x, points.searchBox.y, { durationMs: 300 });
  await click();
  await sleep(200);
}

// Reads whichever of the two result-card layouts is showing. Tries the percent spot first (the
// common case for an in-progress achievement); only checks the separate COMPLETE spot if that
// finds nothing, since a completed card has no percentage there at all.
async function readResultValue(pngBuffer, boxes) {
  const percent = await readPercent(pngBuffer, boxes.percent, { tighten: true });
  // A percentage can't exceed 100 — a value above that is OCR noise (a stray nearby pixel
  // pulled into the auto-tightened box), not a misread digit worth keeping. Treat as not-found
  // rather than store an impossible number.
  if (percent != null && percent <= 100) return percent;
  const text = await readTitle(pngBuffer, boxes.complete, { tighten: true });
  return /complete/i.test(text) ? 100 : null;
}

function persistOne(observations, name, percent, ambiguousTitle) {
  if (!Number.isInteger(percent) || percent < 0 || percent > 100) percent = null;
  const status = ambiguousTitle ? 'ambiguous' : percent == null ? 'unknown' : percent >= 100 ? 'completed' : percent > 0 ? 'working' : 'todo';
  const entry = { name, percent: ambiguousTitle ? null : percent, status };
  if (ambiguousTitle) entry.foundTitle = ambiguousTitle; // what the search actually showed, for manual follow-up
  observations.achievements[idFor(name)] = entry;
  observations.capturedAt = new Date().toISOString();
  fs.writeFileSync(observationsPath, JSON.stringify(observations, null, 2));
}

async function searchScanAchievements({ onProgress, rescanCompleted = false } = {}) {
  const catalog = loadCatalog();
  const observations = loadObservations();
  observations.achievements = observations.achievements || {};

  const toScan = rescanCompleted ? catalog : catalog.filter(name => {
    const result = observations.achievements[idFor(name)];
    return result?.status !== 'completed' || result.percent !== 100;
  });
  const skipped = catalog.length - toScan.length;

  await focusWindow();
  const { width, height } = await captureWindow();
  const points = {
    backButton: scaleBox(BACK_BUTTON, width, height),
    achievementsIcon: scaleBox(MAIN_MENU_ACHIEVEMENTS_ICON, width, height),
    searchBox: scaleBox(SEARCH_BOX, width, height),
  };
  const boxes = {
    percent: scaleBox(PERCENT_ROUGH_BOX, width, height),
    complete: scaleBox(COMPLETE_ROUGH_BOX, width, height),
    resultTitle: scaleBox(RESULT_TITLE_ROUGH_BOX, width, height),
  };
  await navigateToAchievements(points);

  let scanned = 0, foundCompleted = 0;
  for (const name of toScan) {
    const query = searchQueryFor(name);
    await clearField();
    await sleep(150);
    await typeText(query);
    await sleep(450);
    const { png } = await captureWindow();
    const percent = await readResultValue(png, boxes);
    // A truncated/short query, or two names sharing a common prefix (e.g. "Student" is a
    // substring of "Student Loans"), can surface the wrong card — verify the result's own title
    // actually matches the name we searched for before trusting its value.
    const foundTitle = await readTitle(png, boxes.resultTitle, { tighten: true });
    const isMatch = Boolean(foundTitle) && (similarityRatio(foundTitle, name) >= 0.55 || similarityRatio(foundTitle, query) >= 0.55);
    persistOne(observations, name, percent, isMatch ? null : (foundTitle || 'Title not verified'));
    scanned++;
    if (isMatch && percent >= 100) foundCompleted++;
    onProgress?.(scanned, toScan.length, name, isMatch ? percent : `ambiguous (found "${foundTitle}")`, skipped);
  }

  await clearField();
  const completedTotal = Object.values(observations.achievements).filter(a => a.status === 'completed').length;
  return { scanned, skipped, total: catalog.length, completedTotal };
}

module.exports = { searchScanAchievements, idFor };

if (require.main === module) {
  searchScanAchievements({
    onProgress: (i, total, name, percent, skipped) => console.log(`[${i}/${total}, ${skipped} already-completed skipped] ${name}: ${percent == null ? 'not found/hidden' : percent + '%'}`),
  }).then(r => console.log('done:', JSON.stringify(r))).catch(e => { console.error('ERROR:', e.stack); process.exit(1); });
}
