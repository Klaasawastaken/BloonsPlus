const PROJECT_ROOT = require('node:path').resolve(__dirname, '..');
const fs = require('node:fs');
const path = require('node:path');
const { captureWindow } = require('./capture');
const { readPng, colorDistance } = require('./pixels');
const { readDigits, readFraction } = require('./ocr');
const { scanVisibleTowerPage } = require('./scan-towers');
const { scanMapPage } = require('./map-order-scanner');

const calibrationPath = path.join(PROJECT_ROOT, 'data', 'config', 'calibration.json');
const observationsPath = path.join(PROJECT_ROOT, 'game-observations.json');

function loadJson(file, fallback) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return fallback; }
}

function isCalibrated() {
  return fs.existsSync(calibrationPath);
}

function scaleBox(box, referenceSize, image) {
  const sourceWidth = referenceSize?.width || image.width;
  const sourceHeight = referenceSize?.height || image.height;
  return {
    x: Math.round(box.x * image.width / sourceWidth),
    y: Math.round(box.y * image.height / sourceHeight),
    w: Math.max(1, Math.round(box.w * image.width / sourceWidth)),
    h: Math.max(1, Math.round(box.h * image.height / sourceHeight)),
  };
}

function fitsImage(box, image) {
  return box.x >= 0 && box.y >= 0 && box.x + box.w <= image.width && box.y + box.h <= image.height;
}

function classifyScreen(image, anchors, referenceSize) {
  let best = null;
  for (const [name, anchor] of Object.entries(anchors || {})) {
    const box = scaleBox(anchor.box, referenceSize, image);
    if (!fitsImage(box, image)) continue;
    const color = image.averageColor(box);
    const distance = colorDistance(color, anchor.expectedColor);
    if (distance <= (anchor.tolerance ?? 30) && (!best || distance < best.distance)) best = { name, distance };
  }
  return best?.name || 'unknown';
}

// XP needed to go from each BTD6 level to the next (bloonswiki.com/Level; matches live reads of
// 580,000 at level 94 and 590,000 at level 95). After 155, every 20M XP is a veteran level.
const VETERAN_XP = 20_000_000;
const EARLY_LEVEL_XP = [480, 1100, 620, 1150, 2500, 3000, 3500, 3500, 4000, 4250, 4500, 4500, 4900,
  7000, 8000, 9000, 10000, 12000, 12000, 13000, 14000, 15000, 16000, 17000, 18000, 19000, 20000, 21000, 25000];
function xpToNextLevel(level) {
  const next = level + 1;
  if (next > 155) return VETERAN_XP;
  if (next <= 30) return EARLY_LEVEL_XP[next - 2];
  if (next <= 49) return 30000 + 5000 * (next - 31);
  if (next <= 100) return 130000 + 10000 * (next - 50);
  if (next === 101) return 650000;
  if (next <= 149) return 700000 + 50000 * (next - 102);
  if (next === 150) return 8271000;
  return 10000000 + 1000000 * (next - 151);
}

// The level star's digits are a stylized font on a yellow star, so the badge read can drop or add
// a digit. The XP bar's total is exact and pins the level, so the badge only has to agree with it
// (or break a tie where two levels share a total). A total outside the table falls back to the
// badge, but only once two scans in a row read the same number.
let unconfirmedBadgeLevel = null;
function resolveLevel(badgeLevel, nextLevelXp) {
  const candidates = [];
  for (let level = 1; level <= 155; level++) if (xpToNextLevel(level) === nextLevelXp) candidates.push(level);
  if (candidates.includes(badgeLevel)) return badgeLevel;
  if (candidates.length === 1) return candidates[0];
  if (candidates.length || !Number.isInteger(badgeLevel) || badgeLevel < 1 || badgeLevel > 155) return null;
  const confirmed = unconfirmedBadgeLevel === badgeLevel;
  unconfirmedBadgeLevel = badgeLevel;
  return confirmed ? badgeLevel : null;
}
const isBadgeDigit = (r, g, b) => r > 200 && g > 200 && b > 200;

function nearestBorderLabel(color, palette) {
  let best = null;
  for (const [label, sample] of Object.entries(palette || {})) {
    const distance = colorDistance(color, sample);
    if (!best || distance < best.distance) best = { label, distance };
  }
  return best?.label ?? null;
}

// Tile medals read on the map-select screen (see map-order-scanner.js), keyed like the rest of
// observations.maps by lower-case map name.
function recordMedalGain(observations, map, mode) {
  observations.medalGains = [{ map, mode, at: new Date().toISOString() }, ...(observations.medalGains || [])].slice(0, 30);
}
function mergeMapMedals(observations, candidates = []) {
  let merged = 0;
  for (const { name, medals } of candidates) {
    if (!medals) continue;
    const key = name.toLowerCase();
    observations.maps ||= {};
    const previous = observations.maps[key] || {};
    // The scanner performs a stable double capture, so the current tile is the
    // authoritative state. Replace the prior values instead of OR-merging
    // forever; otherwise a stale false/true survives every later scan.
    const mergedMedals = { ...(medals || {}) };
    if (mergedMedals.alternate_bloons_rounds === false && mergedMedals.impoppable === true) {
      delete mergedMedals.impoppable;
      delete mergedMedals.chimps;
    }
    if (mergedMedals.impoppable === false && mergedMedals.chimps === true) delete mergedMedals.chimps;
    for (const [mode, earned] of Object.entries(mergedMedals)) {
      // A medal that appears after the map was already read once is a new gain for the Activity feed.
      if (earned === true && previous.medals && previous.medals[mode] !== true) recordMedalGain(observations, key, mode);
      mergedMedals[mode] = earned === true;
    }
    observations.maps[key] = { ...previous, medals: mergedMedals, medalsScannedAt: new Date().toISOString() };
    merged++;
  }
  return merged;
}
function saveMapMedals(candidates) {
  const observations = loadJson(observationsPath, { source: 'live-scan', maps: {}, towers: {}, achievements: {}, player: null });
  const merged = mergeMapMedals(observations, candidates);
  if (merged) fs.writeFileSync(observationsPath, JSON.stringify(observations, null, 2));
  return merged;
}

// menuOnly: a replay owns the game, so read only the main-menu profile (level, XP, Monkey Money)
// and merge it into the file fresh, leaving map/tower data the automation may be writing alone.
async function runScan({ menuOnly = false } = {}) {
  if (!isCalibrated()) return { skipped: 'not-calibrated' };
  const calibration = loadJson(calibrationPath, {});
  let capture;
  try { capture = await captureWindow(); }
  catch (error) { return { skipped: error.message }; }

  const image = readPng(capture.png);
  const screen = classifyScreen(image, calibration.screenAnchors, calibration.referenceSize);
  const observations = loadJson(observationsPath, { source: 'live-scan', maps: {}, towers: {}, achievements: {}, player: null });
  observations.source = 'live-scan';
  observations.lastCheckedAt = new Date().toISOString();
  observations.lastRecognizedScreen = screen;

  const fields = calibration.fields || {};
  if (fields.profileLevel && fields.profileXp) {
    const levelBox = scaleBox(fields.profileLevel, calibration.referenceSize, image);
    const xpBox = scaleBox(fields.profileXp, calibration.referenceSize, image);
    if (fitsImage(levelBox, image) && fitsImage(xpBox, image)) {
      const [xp, nextLevelXp] = await readFraction(capture.png, xpBox);
      const validXp = Number.isInteger(xp) && Number.isInteger(nextLevelXp) && nextLevelXp > 0 && xp >= 0 && xp <= nextLevelXp;
      const badgeLevel = validXp ? await readDigits(capture.png, levelBox, { classify: isBadgeDigit, tighten: true }) : null;
      const level = validXp ? resolveLevel(badgeLevel, nextLevelXp) : null;
      // A valid fraction in the profile's position is a stronger main-menu signal than a
      // sampled pixel. This lets the scanner follow resolution and UI color changes itself.
      if (validXp && level) {
        observations.lastRecognizedScreen = 'mainMenu';
        observations.capturedAt = new Date().toISOString();
        const previousPlayer = observations.player || {};
        const previousTime = Date.parse(previousPlayer.scannedAt || '');
        const currentTime = Date.parse(observations.capturedAt);
        const elapsedHours = Number.isFinite(previousTime) && currentTime > previousTime ? (currentTime - previousTime) / 3600000 : 0;
        const xpPerHour = elapsedHours >= 1 / 120 && Number.isFinite(previousPlayer.xp)
          ? Math.max(0, (xp - previousPlayer.xp) / elapsedHours) : previousPlayer.xpPerHour;
        observations.player = { ...previousPlayer, level, xp, nextLevelXp, xpPerHour, scannedAt: observations.capturedAt };
      }
    }
  }
  const moneyField = fields.profileMonkeyMoney || fields.monkeyMoney;
  if (menuOnly) {
    if (observations.lastRecognizedScreen !== 'mainMenu') return { screen };
  }
  if (moneyField) {
    const moneyBox = scaleBox(moneyField, calibration.referenceSize, image);
    if (fitsImage(moneyBox, image)) {
      const monkeyMoney = await readDigits(capture.png, moneyBox, { tighten: true });
      if (Number.isInteger(monkeyMoney) && monkeyMoney >= 0) {
        const previousPlayer = observations.player || {};
        const previousTime = Date.parse(previousPlayer.scannedAt || '');
        const currentTime = Date.parse(observations.capturedAt || observations.lastCheckedAt);
        const elapsedHours = Number.isFinite(previousTime) && currentTime > previousTime ? (currentTime - previousTime) / 3600000 : 0;
        const monkeyMoneyPerHour = elapsedHours >= 1 / 120 && Number.isFinite(previousPlayer.monkeyMoney)
          ? Math.max(0, (monkeyMoney - previousPlayer.monkeyMoney) / elapsedHours) : previousPlayer.monkeyMoneyPerHour;
        observations.player = { ...previousPlayer, monkeyMoney, monkeyMoneyPerHour, scannedAt: observations.capturedAt || observations.lastCheckedAt };
      }
    }
  }
  if (menuOnly) {
    const fresh = loadJson(observationsPath, observations);
    Object.assign(fresh, { source: 'live-scan', lastCheckedAt: observations.lastCheckedAt, capturedAt: observations.capturedAt,
      lastRecognizedScreen: 'mainMenu', player: observations.player });
    fs.writeFileSync(observationsPath, JSON.stringify(fresh, null, 2));
    return { screen: 'mainMenu' };
  }
  if (screen === 'mapSelect' && fields.mapTiles && Object.keys(calibration.borderPalette || {}).length) {
    for (const [mapName, box] of Object.entries(fields.mapTiles)) {
      const scaled = scaleBox(box, calibration.referenceSize, image);
      if (!fitsImage(scaled, image)) continue;
      const label = nearestBorderLabel(image.averageColor(scaled), calibration.borderPalette);
      if (!label) continue;
      const key = mapName.toLowerCase();
      observations.maps[key] = { ...(observations.maps[key] || {}), border: label, blackBorder: label === 'black', status: label === 'none' ? 'todo' : 'working', scannedAt: observations.lastCheckedAt };
      observations.capturedAt = observations.lastCheckedAt;
    }
  }
  let mapPage = null;
  if (observations.lastRecognizedScreen !== 'mainMenu') {
    mapPage = await scanMapPage(capture.png);
    if (mapPage) {
      observations.lastRecognizedScreen = 'mapSelect';
      if (mapPage.learned) observations.capturedAt = observations.lastCheckedAt;
      if (mergeMapMedals(observations, mapPage.candidates)) observations.capturedAt = observations.lastCheckedAt;
    }
  }
  if (observations.lastRecognizedScreen !== 'mainMenu' && !mapPage && screen !== 'mapSelect') {
    const cards = await scanVisibleTowerPage(capture.png, image);
    if (cards.length) {
      const confirmation = await captureWindow();
      const second = await scanVisibleTowerPage(confirmation.png, confirmation);
      const verified = cards.filter(card => second.some(other => other.index === card.index && other.name === card.name && other.xp === card.xp));
      if (verified.length >= 2) {
        observations.towers ||= {};
        for (const { name, xp } of verified) {
          observations.towers[name] = { ...(observations.towers[name] || {}), xp, xpVerifiedAt: observations.lastCheckedAt };
        }
        observations.lastRecognizedScreen = 'towerOverview';
        observations.capturedAt = observations.lastCheckedAt;
      }
    }
  }
  // Any screen not recognized, or fields not visible on the recognized screen, leave prior values
  // untouched. Tower XP is scanned separately by scan-towers.js (an agent-driven grid read of the
  // Towers screen's category tabs), not by this passive poll.

  fs.writeFileSync(observationsPath, JSON.stringify(observations, null, 2));
  return { screen: observations.lastRecognizedScreen };
}

module.exports = { runScan, isCalibrated, resolveLevel, saveMapMedals, recordMedalGain };
