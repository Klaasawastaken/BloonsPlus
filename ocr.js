const path = require('node:path');
const fs = require('node:fs');
const { createWorker, PSM } = require('tesseract.js');
const { PNG } = require('pngjs');

const tessdataDir = path.join(__dirname, 'tessdata');
let workerPromise;
let textWorkerPromise;

function hasLocalTessdata() {
  const has = fs.existsSync(path.join(tessdataDir, 'eng.traineddata.gz')) || fs.existsSync(path.join(tessdataDir, 'eng.traineddata'));
  if (!has) console.warn('tessdata/eng.traineddata(.gz) not found locally; OCR will try to fetch it once from the network. See README.');
  return has;
}

function getWorker() {
  if (!workerPromise) {
    const hasLocalData = hasLocalTessdata();
    workerPromise = createWorker('eng', 1, hasLocalData ? { langPath: tessdataDir, cachePath: tessdataDir, gzip: fs.existsSync(path.join(tessdataDir, 'eng.traineddata.gz')) } : {})
      .then(async worker => { await worker.setParameters({ tessedit_char_whitelist: '0123456789,/', tessedit_pageseg_mode: PSM.SINGLE_LINE }); return worker; });
  }
  return workerPromise;
}

// A second, unrestricted worker for general text (achievement/tower names) — the digit-only
// worker above can't read letters at all.
function getTextWorker() {
  if (!textWorkerPromise) {
    const hasLocalData = hasLocalTessdata();
    textWorkerPromise = createWorker('eng', 1, hasLocalData ? { langPath: tessdataDir, cachePath: tessdataDir, gzip: fs.existsSync(path.join(tessdataDir, 'eng.traineddata.gz')) } : {})
      .then(async worker => { await worker.setParameters({ tessedit_pageseg_mode: PSM.SINGLE_LINE }); return worker; });
  }
  return textWorkerPromise;
}

// BTD6's UI text is consistently a bubble font: a light fill (white, or a bright color) with a
// heavy dark outline, over a mid-luminance background — whatever the fill/outline colors are,
// the background sits between them. So instead of guessing a single "bright = text" cutoff (which
// only worked for white-fill HUD digits and erased colored achievement text/percentages), mark
// BOTH extremes — very bright (fill) and very dark (outline) — as text, and only the mid-range
// background as background. Verified against both the white-fill HUD numbers and colored
// (teal/green) achievement text/percentages: this one rule reads all of them.
//
// One real exception found (the Towers screen's dark-green-on-medium-blue XP text): fill and
// background sit at nearly the same luminance, so no luminance cutoff separates them without
// fusing every glyph into a solid blob. There the fill is still a clearly different *hue* from the
// background even though luminance can't tell them apart — pass a custom `classify(r,g,b)` to
// override the default luminance rule for exactly that case; every other caller is unaffected.
function defaultClassify(lowThreshold, highThreshold) {
  return (r, g, b) => {
    const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
    return luminance < lowThreshold || luminance > highThreshold;
  };
}

function preprocess(pngBuffer, box, { lowThreshold = 70, highThreshold = 190, pad = 16, scale = 3, classify } = {}) {
  const isText = classify || defaultClassify(lowThreshold, highThreshold);
  const src = PNG.sync.read(pngBuffer);
  const w = Math.max(1, Math.round(box.w)), h = Math.max(1, Math.round(box.h));
  const x0 = Math.round(box.x), y0 = Math.round(box.y);
  const outW = (w + pad * 2) * scale, outH = (h + pad * 2) * scale;
  const out = new PNG({ width: outW, height: outH });
  out.data.fill(255);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const si = (src.width * (y0 + y) + (x0 + x)) << 2;
      const value = isText(src.data[si], src.data[si + 1], src.data[si + 2]) ? 0 : 255;
      for (let dy = 0; dy < scale; dy++) {
        for (let dx = 0; dx < scale; dx++) {
          const oi = (outW * ((y + pad) * scale + dy) + ((x + pad) * scale + dx)) << 2;
          out.data[oi] = value; out.data[oi + 1] = value; out.data[oi + 2] = value; out.data[oi + 3] = 255;
        }
      }
    }
  }
  return PNG.sync.write(out);
}

// Tesseract on this bubble font turned out very sensitive to exact crop framing — a few pixels
// of extra margin or a slightly-off box reliably produces empty/wrong reads even on clean text
// (confirmed repeatedly). Rather than hand-tuning pixel-perfect boxes everywhere (fragile, breaks
// again the moment a layout shifts), auto-tighten: given a generous rough box that just needs to
// CONTAIN the text somewhere inside it, find the actual text-colored pixels' bounding box (same
// classify rule as preprocess) and crop to that instead.
function tightenBox(pngBuffer, roughBox, { lowThreshold = 70, highThreshold = 190, pad = 6, classify } = {}) {
  const isText = classify || defaultClassify(lowThreshold, highThreshold);
  const src = PNG.sync.read(pngBuffer);
  const x0 = Math.round(roughBox.x), y0 = Math.round(roughBox.y);
  const w = Math.round(roughBox.w), h = Math.round(roughBox.h);
  let minX = w, minY = h, maxX = -1, maxY = -1;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const si = (src.width * (y0 + y) + (x0 + x)) << 2;
      if (isText(src.data[si], src.data[si + 1], src.data[si + 2])) {
        if (x < minX) minX = x; if (x > maxX) maxX = x;
        if (y < minY) minY = y; if (y > maxY) maxY = y;
      }
    }
  }
  if (maxX < 0) return roughBox; // nothing found — fall back to the rough box as-is
  return {
    x: Math.max(0, x0 + minX - pad), y: Math.max(0, y0 + minY - pad),
    w: (maxX - minX + 1) + pad * 2, h: (maxY - minY + 1) + pad * 2,
  };
}

async function readRaw(pngBuffer, box, thresholds) {
  const worker = await getWorker();
  const { data } = await worker.recognize(preprocess(pngBuffer, box, thresholds));
  return data.text || '';
}

// Reads a short line of general text (e.g. a card title). Pass `tighten: true` when `box` is a
// generous rough area rather than a pixel-tuned one (see tightenBox above). `lowThreshold`/
// `highThreshold` override preprocess()'s defaults — needed for text whose fill luminance doesn't
// cleanly land in the default dark/bright bands (confirmed: the Towers screen's dark-green XP
// text sits right on the default low threshold and reads unreliably without raising it).
async function readTitle(pngBuffer, box, { tighten = false, lowThreshold, highThreshold, classify } = {}) {
  const worker = await getTextWorker();
  await worker.setParameters({ tessedit_pageseg_mode: PSM.SINGLE_LINE });
  const thresholds = { lowThreshold, highThreshold, classify };
  const actualBox = tighten ? tightenBox(pngBuffer, box, thresholds) : box;
  const { data } = await worker.recognize(preprocess(pngBuffer, actualBox, thresholds));
  return (data.text || '').trim();
}

async function readNaturalText(pngBuffer, box) {
  const worker = await getTextWorker();
  await worker.setParameters({ tessedit_pageseg_mode: PSM.SINGLE_LINE });
  const source = PNG.sync.read(pngBuffer);
  const cropWidth = Math.round(box.w), cropHeight = Math.round(box.h);
  if (cropWidth < 3 || cropHeight < 3) return '';
  const crop = new PNG({ width: cropWidth, height: cropHeight });
  PNG.bitblt(source, crop, Math.round(box.x), Math.round(box.y), crop.width, crop.height, 0, 0);
  const { data } = await worker.recognize(PNG.sync.write(crop));
  return (data.text || '').trim();
}

// box: {x, y, w, h} in source-image pixel coordinates. Reads the first run of digits — not
// "strip all non-digits and concatenate", since stray symbols (e.g. a '%' sign) can misread as
// extra trailing digits and corrupt the result (confirmed: "95%" → "95°45" → must take "95").
function firstDigitRun(text) {
  const match = text.match(/(\d+)/);
  return match ? Number(match[1].replace(/,/g, '')) : null;
}

async function readDigits(pngBuffer, box, { tighten = false, lowThreshold, highThreshold, classify } = {}) {
  const thresholds = { lowThreshold, highThreshold, classify };
  const actualBox = tighten ? tightenBox(pngBuffer, box, thresholds) : box;
  return firstDigitRun((await readRaw(pngBuffer, actualBox, thresholds)).replace(/,/g, ''));
}

// Same digit reading, for colored (non-HUD) percentage/count text. Deliberately uses the
// unrestricted text worker, not the digit-only one: forcing a '%' glyph into the digit whitelist
// misreads it as more digits with no separator (corrupting the real number, e.g. "95%" -> "9525"),
// while the unrestricted worker at least inserts a non-digit character there ("95%" -> "95°45"),
// letting firstDigitRun stop at the real number.
async function readPercent(pngBuffer, box, { tighten = false, lowThreshold, highThreshold, classify } = {}) {
  const worker = await getTextWorker();
  // SINGLE_LINE (used for titles) intermittently found zero text on these short number+symbol
  // crops, even when clean (confirmed: an unambiguous "80%" crop returned nothing under
  // SINGLE_LINE but read correctly under SINGLE_WORD) — a short isolated "word" needs this mode.
  await worker.setParameters({ tessedit_pageseg_mode: PSM.SINGLE_WORD });
  const thresholds = { lowThreshold, highThreshold, classify };
  const actualBox = tighten ? tightenBox(pngBuffer, box, thresholds) : box;
  const { data } = await worker.recognize(preprocess(pngBuffer, actualBox, thresholds));
  return firstDigitRun(data.text || '');
}

// Reads a "current/total" style field (e.g. an XP bar's "545,984/580,000") into [current, total].
async function readFraction(pngBuffer, box) {
  const text = await readRaw(pngBuffer, box);
  const match = text.match(/([0-9][0-9,]*)\s*\/\s*([0-9][0-9,]*)/);
  if (!match) return [null, null];
  return [Number(match[1].replace(/,/g, '')), Number(match[2].replace(/,/g, ''))];
}

async function shutdown() {
  if (workerPromise) { (await workerPromise).terminate(); workerPromise = null; }
  if (textWorkerPromise) { (await textWorkerPromise).terminate(); textWorkerPromise = null; }
}

module.exports = { readDigits, readFraction, readTitle, readNaturalText, readPercent, shutdown };
