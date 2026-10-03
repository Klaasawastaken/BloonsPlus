// Full achievement scan: navigates to the Achievements screen, scrolls through every page, and
// OCRs each visible card's title + percentage, matching titles against the Steam achievement
// catalog (achievements.js). Wired as its own script (not the 5s scanner loop) because it takes
// over the mouse for several seconds — call it on demand, not on a timer.
const fs = require('node:fs');
const path = require('node:path');
const { moveMouseTo, click, scroll } = require('./input');
const { captureWindow, focusWindow } = require('./capture');
const { readPng } = require('./pixels');
const { readPercent, readTitle } = require('./ocr');

const observationsPath = path.join(__dirname, 'game-observations.json');

// Loaded from achievements.js's browser-global assignment without needing a DOM.
function loadCatalog() {
  const src = fs.readFileSync(path.join(__dirname, 'achievements.js'), 'utf8');
  const match = src.match(/`([\s\S]*?)`/);
  if (!match) throw new Error('Could not find achievement list in achievements.js');
  return match[1].split('\n').map(name => name.trim()).filter(Boolean);
}

// BTD6's achievements grid, measured against a 3840x2160 capture (2 columns), from the list's
// top (unscrolled) position — navigateToAchievements() always resets scroll to top first.
const GRID = { col1X: 420, col2X: 1980, cardWidth: 1500, row1Y: 495, rowHeight: 635 };
const TITLE_OFFSET = { x: 300, y: 0, w: 1000, h: 90 };
const PERCENT_OFFSET = { x: 1200, y: 335, w: 140, h: 55 };
const MAIN_MENU_ACHIEVEMENTS_ICON = { x: 144, y: 614 };
const BACK_BUTTON = { x: 163, y: 106 };

function normalize(s) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '');
}

// OCR of these stylized titles is imperfect (e.g. "ACOLYTE" -> "acolyre", a leading letter
// dropped from "TOOLS TO DARWIN"), so exact/substring matching misses too often — edit distance
// tolerates a couple of misread characters while still rejecting genuinely different titles.
function levenshtein(a, b) {
  const dp = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
  for (let j = 0; j <= b.length; j++) dp[0][j] = j;
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      dp[i][j] = a[i - 1] === b[j - 1] ? dp[i - 1][j - 1] : 1 + Math.min(dp[i - 1][j - 1], dp[i - 1][j], dp[i][j - 1]);
    }
  }
  return dp[a.length][b.length];
}

function similarityRatio(a, b) {
  const normA = normalize(a), normB = normalize(b);
  if (!normA || !normB) return 0;
  return 1 - levenshtein(normA, normB) / Math.max(normA.length, normB.length);
}

function bestCatalogMatch(ocrText, catalog) {
  const norm = normalize(ocrText);
  if (norm.length < 3) return null;
  let best = null, bestRatio = 0;
  for (const name of catalog) {
    const ratio = similarityRatio(ocrText, name);
    if (ratio > bestRatio) { bestRatio = ratio; best = name; }
  }
  return bestRatio >= 0.65 ? best : null;
}

// Backs out of whatever screen we might currently be on (unknown starting state — a previous
// run, a manual test, or the user's own navigation) before going to Achievements. Clicking the
// back-button spot when already on the main menu just clicks empty background, which is harmless.
async function navigateToAchievements() {
  for (let i = 0; i < 3; i++) {
    await moveMouseTo(BACK_BUTTON.x, BACK_BUTTON.y, { durationMs: 200 });
    await click();
    await new Promise(r => setTimeout(r, 400));
  }
  await moveMouseTo(MAIN_MENU_ACHIEVEMENTS_ICON.x, MAIN_MENU_ACHIEVEMENTS_ICON.y, { durationMs: 300 });
  await click();
  await new Promise(r => setTimeout(r, 700));
}

// BTD6 shows a locked/unrevealed hidden achievement's card as "???" for both title and
// description — can't attribute it to a specific catalog name, but it should still count toward
// overall progress instead of silently vanishing (normalize() would otherwise reduce "???" to an
// empty string indistinguishable from any other unreadable crop).
function isHiddenPlaceholder(rawTitle) {
  return /^\?{2,}$/.test(rawTitle.replace(/\s+/g, ''));
}

// `alreadySeen` (a Set of catalog names already confirmed) lets repeat cards skip the percent
// OCR entirely — the expensive half of each card once the title is already known — since most
// polls during a scroll re-see cards from the previous poll.
async function scanVisibleCards(pngBuffer, catalog, alreadySeen = new Set()) {
  const results = [];
  for (const [colIndex, colX] of [GRID.col1X, GRID.col2X].entries()) {
    for (let row = 0; row < 3; row++) {
      const cardY = GRID.row1Y + row * GRID.rowHeight;
      const titleBox = { x: colX + TITLE_OFFSET.x, y: cardY + TITLE_OFFSET.y, w: TITLE_OFFSET.w, h: TITLE_OFFSET.h };
      const position = `${colIndex},${row}`;
      const rawTitle = await readTitle(pngBuffer, titleBox);
      if (!rawTitle) continue;
      if (isHiddenPlaceholder(rawTitle)) { results.push({ name: null, hidden: true, position, rawTitle }); continue; }
      const matched = bestCatalogMatch(rawTitle, catalog);
      if (!matched) continue;
      if (alreadySeen.has(matched)) { results.push({ name: matched, rawTitle, percent: undefined }); continue; }
      const percentBox = { x: colX + PERCENT_OFFSET.x, y: cardY + PERCENT_OFFSET.y, w: PERCENT_OFFSET.w, h: PERCENT_OFFSET.h };
      const percent = await readPercent(pngBuffer, percentBox);
      results.push({ name: matched, rawTitle, percent });
    }
  }
  return results;
}

async function scanAllAchievements({ maxScrolls = 60, scrollTicks = 6 } = {}) {
  const catalog = loadCatalog();
  await focusWindow();
  await navigateToAchievements();

  const seen = new Map(); // name -> {percent}
  let staleRounds = 0;
  for (let i = 0; i < maxScrolls && staleRounds < 3; i++) {
    const { png } = await captureWindow();
    const visible = await scanVisibleCards(png, catalog);
    let newCount = 0;
    for (const { name, percent } of visible) {
      if (!seen.has(name)) newCount++;
      seen.set(name, { percent });
    }
    staleRounds = newCount === 0 ? staleRounds + 1 : 0;
    await moveMouseTo(GRID.col1X + 700, GRID.row1Y + 300, { durationMs: 150 });
    await scroll(scrollTicks, 'down');
    await new Promise(r => setTimeout(r, 400));
  }

  const observations = JSON.parse(fs.readFileSync(observationsPath, 'utf8'));
  observations.achievements = observations.achievements || {};
  for (const [name, { percent }] of seen) {
    const id = `steam-${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`;
    const status = percent == null ? 'unknown' : percent >= 100 ? 'completed' : percent > 0 ? 'working' : 'todo';
    observations.achievements[id] = { name, percent, status };
  }
  observations.capturedAt = new Date().toISOString();
  fs.writeFileSync(observationsPath, JSON.stringify(observations, null, 2));
  return { scanned: seen.size, total: catalog.length };
}

module.exports = { scanAllAchievements, scanVisibleCards, loadCatalog, bestCatalogMatch, similarityRatio, GRID };
