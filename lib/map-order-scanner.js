const PROJECT_ROOT = require('node:path').resolve(__dirname, '..');
// Learns the actual tile order from the visible map-selection page. This is read-only: the user
// can visit pages normally and Bloons+ records only labels that OCR matches confidently.
const fs = require('node:fs');
const path = require('node:path');
const { readNaturalText, readTitle } = require('./ocr');
const isTitleFill = (r, g, b) => r > 225 && g > 225 && b > 225;
const { readPng } = require('./pixels');
const { PNG } = require('pngjs');

const ORDER_PATH = path.join(PROJECT_ROOT, 'map-order.json');
const REFERENCE = { width: 2048, height: 1122 };
const CENTERS = [570, 1025, 1480];
const TITLE_ROWS = [{ y: 112, h: 60 }, { y: 452, h: 65 }];
const normalize = value => String(value).toLowerCase().replace(/[^a-z0-9]/g, '');

function loadCatalog() {
  const source = fs.readFileSync(path.join(PROJECT_ROOT, 'map-catalog.js'), 'utf8');
  const match = source.match(/\{([\s\S]*)\}/);
  if (!match) throw new Error('Map catalog cannot be read');
  return JSON.parse(`{${match[1]}}`);
}
function loadMapOrder() {
  try { return JSON.parse(fs.readFileSync(ORDER_PATH, 'utf8')); }
  catch { return { maps: {}, updatedAt: null }; }
}
function scaledBox(box, image) {
  const scale = image.width / REFERENCE.width;
  return {
    x: Math.round(box.x * scale),
    y: Math.round(box.y * scale),
    w: Math.round(box.w * scale),
    h: Math.round(box.h * scale),
  };
}
function similarity(a, b) {
  a = normalize(a); b = normalize(b);
  const prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    const row = [i];
    for (let j = 1; j <= b.length; j++) row[j] = Math.min(row[j - 1] + 1, prev[j] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    prev.splice(0, prev.length, ...row);
  }
  return 1 - prev[b.length] / Math.max(1, a.length, b.length);
}
function matchName(text, catalog) {
  if (!text || normalize(text).length < 4) return null;
  const ranked = Object.entries(catalog).flatMap(([category, names]) => names.map(name => ({ category, name, score: similarity(text, name) }))).sort((a, b) => b.score - a.score);
  return ranked[0]?.score >= 0.84 && (!ranked[1] || ranked[0].score - ranked[1].score >= 0.1) ? ranked[0] : null;
}
function newMapName(text, catalog) {
  const name = String(text).replace(/\s+/g, ' ').trim();
  if (!/^[A-Za-z#][A-Za-z0-9 '#&.!-]{3,39}$/.test(name)) return null;
  if (name.split(' ').length > 5) return null;
  const closest = Math.max(...Object.values(catalog).flat().map(known => similarity(name, known)));
  // An almost-known label is probably a damaged OCR read, not a new map.
  return closest < 0.68 ? name : null;
}
function currentPage(image) {
  // BTD6 adds page indicators as maps are added. The bundled screenshot has 12;
  // the current game has 17. Their pitch stays the same and the row is centered.
  for (const count of [17, 16, 15, 14, 13, 12]) {
    const start = 1024 - (count - 1) * 39.4 / 2;
    const active = [];
    let dark = 0;
    for (let index = 0; index < count; index++) {
      const x = Math.round((start + index * 39.4) * image.width / REFERENCE.width);
      const y = Math.round(809 * image.width / REFERENCE.width);
      const [r, g, b] = image.get(x, y);
      if (b > 105 && b > r * 1.35 && b > g * 1.12) active.push(index);
      if (r < 65 && g < 85 && b < 110) dark++;
    }
    if (active.length === 1 && dark >= count - 2) return { index: active[0], count };
  }
  return null;
}

// Medals earned on a map show as saturated icons along the bottom of its tile; missing ones are
// beige outlines (measured live at 2560x1440: earned slots 0.42-0.98 strongly colored, missing 0).
// Only the tile's four large medals, the CHIMPS skull and the Alternate Bloons Rounds badge have
// positions that no neighbouring medal overlaps, so only those are read.
const MEDAL_SLOTS = {
  easy: [-181, 330, 12], medium: [-60, 330, 12], hard: [51, 330, 12],
  alternate_bloons_rounds: [113, 322, 8], impoppable: [171, 330, 12], chimps: [208, 362, 10],
};
const CARD_CENTERS_2560 = [713, 1284, 1848];
const CARD_TOPS_2560 = [169, 589];
const MEDAL_PREREQUISITES = {
  primary_only: ['easy'], deflation: ['primary_only'], military_only: ['medium'], reverse: ['medium'],
  apopalypse: ['military_only'], magic_monkeys_only: ['hard'], double_hp_moabs: ['magic_monkeys_only'],
  half_cash: ['double_hp_moabs'], alternate_bloons_rounds: ['hard'], impoppable: ['alternate_bloons_rounds'],
  chimps: ['impoppable'],
};
const HUE_BANDS = { green: [85, 160], blue: [205, 245], purple: [260, 305] };
const VARIATION_MEDALS = {
  primary_only: [-212, 354, 'green'], deflation: [-140, 349, 'purple'],
  military_only: [-93, 344, 'green'], reverse: [-58, 362, 'blue'], apopalypse: [-23, 336, 'purple'],
  magic_monkeys_only: [18, 319, 'green'], double_hp_moabs: [102, 315, 'purple'], half_cash: [32, 359, 'blue'],
};
function hueShare(image, cx, cy, radius, [low, high]) {
  let hit = 0, total = 0;
  for (let y = cy - radius; y <= cy + radius; y++) {
    for (let x = cx - radius; x <= cx + radius; x++) {
      const [r, g, b] = image.get(x, y);
      const max = Math.max(r, g, b), spread = max - Math.min(r, g, b);
      total++;
      if (!spread || max < 80 || spread / max < 0.45) continue;
      let hue = max === r ? ((g - b) / spread) % 6 : max === g ? (b - r) / spread + 2 : (r - g) / spread + 4;
      hue = (hue * 60 + 360) % 360;
      if (hue >= low && hue <= high) hit++;
    }
  }
  return hit / total;
}
function readCardMedals(image, slot) {
  const scale = image.width / 2560;
  const cx = CARD_CENTERS_2560[slot % 3], top = CARD_TOPS_2560[Math.floor(slot / 3)];
  const medals = {};
  for (const [mode, [dx, dy, r]] of Object.entries(MEDAL_SLOTS)) {
    let colored = 0, total = 0;
    for (let y = top + dy - r; y <= top + dy + r; y++) {
      for (let x = cx + dx - r; x <= cx + dx + r; x++) {
        const [red, green, blue] = image.get(Math.round(x * scale), Math.round(y * scale));
        const max = Math.max(red, green, blue), min = Math.min(red, green, blue);
        if (max > 90 && (max - min) / max > 0.55) colored++;
        total++;
      }
    }
    medals[mode] = colored / total > 0.2;
  }
  // Variation medals are small badges below the map art, told apart by their ribbon colour. Offsets
  // and colours measured on a tile with all 14 medals; an empty tile scores 0, an earned badge 0.25+.
  for (const [mode, [dx, dy, band]] of Object.entries(VARIATION_MEDALS)) {
    medals[mode] = hueShare(image, (cx + dx) * scale, (top + dy) * scale, 11 * scale, HUE_BANDS[band]) > 0.12;
  }
  // BTD6 unlocks each variation by winning the one before it, so a medal whose prerequisite is
  // missing is a misread (the lone Hard medal's ribbon sits where Double HP would be).
  for (const [mode, requires] of Object.entries(MEDAL_PREREQUISITES)) {
    if (mode in VARIATION_MEDALS && medals[mode] && !requires.every(prior => medals[prior])) medals[mode] = false;
  }
  return medals;
}

// A small thumbnail of each map's tile art, cut from the player's own map-select screen the first
// time the map is read confidently. The Maps page shows it; nothing else depends on it.
const ICON_DIR = path.join(PROJECT_ROOT, 'map-icons');
const ICON_WIDTH = 180;
function saveMapIcon(image, slot, name) {
  const file = path.join(ICON_DIR, `${normalize(name)}.png`);
  if (fs.existsSync(file)) return;
  const scale = image.width / 2560;
  const cx = CARD_CENTERS_2560[slot % 3], top = CARD_TOPS_2560[Math.floor(slot / 3)];
  // Art only: below the title, above the medal row, left of the hero badge.
  const x0 = (cx - 230) * scale, y0 = (top + 45) * scale, w = 380 * scale, h = 200 * scale;
  const out = new PNG({ width: ICON_WIDTH, height: Math.round(ICON_WIDTH * h / w) });
  for (let y = 0; y < out.height; y++) {
    for (let x = 0; x < out.width; x++) {
      const [r, g, b] = image.get(x0 + x * w / out.width, y0 + y * h / out.height);
      const i = (out.width * y + x) << 2;
      out.data[i] = r; out.data[i + 1] = g; out.data[i + 2] = b; out.data[i + 3] = 255;
    }
  }
  fs.mkdirSync(ICON_DIR, { recursive: true });
  fs.writeFileSync(file, PNG.sync.write(out));
}

async function scanMapPage(pngBuffer) {
  const image = readPng(pngBuffer);
  const indicator = currentPage(image);
  const page = indicator ? indicator.index : null;
  const catalog = loadCatalog();
  const candidates = [];
  const unknown = [];
  for (let slot = 0; slot < 6; slot++) {
    const row = TITLE_ROWS[Math.floor(slot / 3)];
    const center = CENTERS[slot % 3];
    const box = scaledBox({ x: center - 200, y: row.y, w: 400, h: row.h }, image);
    let readName = await readNaturalText(pngBuffer, box);
    let match = matchName(readName, catalog);
    if (!match) {
      // Busy tile art defeats the raw read; the title's white fill alone reads far more reliably.
      const titleOnly = await readTitle(pngBuffer, box, { tighten: true, classify: isTitleFill });
      const cleaned = titleOnly.split(/\s+/).filter(token => /[a-z0-9]{2,}/i.test(token)).join(' ');
      match = matchName(cleaned, catalog);
      if (match) readName = cleaned;
    }
    if (match) candidates.push({ slot, ...match, ...(indicator ? { medals: readCardMedals(image, slot) } : {}) });
    if (match && indicator) { try { saveMapIcon(image, slot, match.name); } catch { /* thumbnails are optional */ } }
    else {
      const name = newMapName(readName, catalog);
      if (name) unknown.push({ slot, name });
    }
  }
  // A stylized title can fail OCR even when the rest of the page is unmistakable.
  // Infer only empty slots whose shipped position is corroborated by at least four
  // independently read titles on this same page. This also lets that tile's medal
  // row and thumbnail be captured instead of leaving it permanently unscanned.
  if (indicator) {
    const mapsConfig = JSON.parse(fs.readFileSync(path.join(PROJECT_ROOT, 'autobtd6', 'maps.json'), 'utf8'));
    const order = loadMapOrder();
    const starts = order.categoryStarts || { Beginner: 0 };
    for (const [category, start] of Object.entries(starts)) {
      const localPage = page - start;
      const expected = Object.values(mapsConfig).filter(item => item.category === category.toLowerCase() && item.page === localPage);
      const anchors = candidates.filter(item => item.category === category && expected.some(known => known.pos === item.slot && normalize(known.name) === normalize(item.name)));
      if (anchors.length < 4) continue;
      for (const known of expected) {
        if (candidates.some(item => item.slot === known.pos) || known.pos < 0 || known.pos > 5) continue;
        const catalogName = catalog[category]?.find(name => normalize(name) === normalize(known.name));
        if (!catalogName) continue;
        candidates.push({ slot: known.pos, category, name: catalogName, score: 1, inferred: true,
          medals: readCardMedals(image, known.pos) });
        try { saveMapIcon(image, known.pos, catalogName); } catch { /* optional art */ }
      }
      break;
    }
  }
  const votes = {};
  for (const candidate of candidates) votes[candidate.category] = (votes[candidate.category] || 0) + 1;
  const category = Object.keys(votes).sort((a, b) => votes[b] - votes[a])[0];
  if (!indicator) return { page: null, indicatorCount: 0, category: category || null, learned: 0, candidates };
  if (!category || votes[category] < 2) return { page, indicatorCount: indicator.count, category: null, learned: 0, candidates };
  const order = loadMapOrder();
  order.maps ||= {};
  order.pending ||= {};
  order.categoryStarts ||= { Beginner: 0 };
  const mapsConfig = JSON.parse(fs.readFileSync(path.join(PROJECT_ROOT, 'autobtd6', 'maps.json'), 'utf8'));
  const existing = new Map(Object.values(mapsConfig).map(item => [normalize(item.name), item]));
  const starts = {};
  for (const candidate of candidates.filter(item => item.category === category)) {
    const previous = existing.get(normalize(candidate.name));
    if (previous && previous.category === category.toLowerCase() && Number.isInteger(previous.page)) {
      const start = page - previous.page;
      if (start >= 0) starts[start] = (starts[start] || 0) + 1;
    }
  }
  const bestStart = Object.entries(starts).sort((a, b) => b[1] - a[1])[0];
  if (bestStart && bestStart[1] >= 2) order.categoryStarts[category] = Number(bestStart[0]);
  const localPage = Number.isInteger(order.categoryStarts[category]) ? page - order.categoryStarts[category] : null;
  let learned = 0;
  for (const candidate of candidates.filter(item => item.category === category)) {
    const positionKey = `${category}:${page}:${candidate.slot}`;
    delete order.pending[positionKey];
    for (const [key, entry] of Object.entries(order.maps)) {
      if (key !== normalize(candidate.name) && entry.discovered && entry.category === category && entry.page === page && entry.pos === candidate.slot) delete order.maps[key];
    }
    order.maps[normalize(candidate.name)] = { name: candidate.name, category, globalPage: page,
      ...(localPage >= 0 ? { page: localPage } : {}), pos: candidate.slot,
      confidence: candidate.score, seenAt: new Date().toISOString() };
    learned++;
  }
  for (const item of unknown) {
    const key = `${category}:${page}:${item.slot}`;
    const previous = order.pending[key];
    const seenCount = previous && normalize(previous.name) === normalize(item.name) ? previous.seenCount + 1 : 1;
    order.pending[key] = { name: item.name, seenCount };
    if (seenCount >= 3) {
      for (const [knownKey, entry] of Object.entries(order.maps)) {
        if (knownKey !== normalize(item.name) && entry.discovered && entry.category === category && entry.page === page && entry.pos === item.slot) delete order.maps[knownKey];
      }
      order.maps[normalize(item.name)] = { name: item.name, category, globalPage: page,
        ...(localPage >= 0 ? { page: localPage } : {}), pos: item.slot,
        confidence: 'repeated-ocr', discovered: true, seenAt: new Date().toISOString() };
      learned++;
    }
  }
  // A tile whose title didn't read this time still gets its thumbnail when the learned page order
  // already says which map sits in that slot.
  for (let slot = 0; slot < 6; slot++) {
    if (candidates.some(item => item.slot === slot)) continue;
    const known = Object.values(order.maps).find(entry => entry.globalPage === page && entry.pos === slot && entry.category === category);
    if (known) { try { saveMapIcon(image, slot, known.name); } catch { /* thumbnails are optional */ } }
  }
  if (learned || unknown.length) {
    order.updatedAt = new Date().toISOString();
    const temporary = `${ORDER_PATH}.tmp`;
    fs.writeFileSync(temporary, JSON.stringify(order, null, 2));
    fs.renameSync(temporary, ORDER_PATH);
  }
  return { page, indicatorCount: indicator.count, category, learned, candidates };
}

module.exports = { scanMapPage, loadMapOrder, currentPage };
