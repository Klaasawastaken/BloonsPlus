// Replay sends one screenshot on stdin. Confirm the visible page and target tile before clicking.
// Exit 2 when OCR is uncertain so a stale map index cannot start the wrong recording.
const { scanMapPage } = require('./lib/map-order-scanner');
const { loadMapOrder } = require('./lib/map-order-scanner');
const { shutdown } = require('./lib/ocr');

const [expectedName, expectedCategory, expectedPage, expectedSlot] = process.argv.slice(2);
const normalize = value => String(value).toLowerCase().replace(/[^a-z0-9]/g, '');

(async () => {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  const result = await scanMapPage(Buffer.concat(chunks));
  const order = loadMapOrder();
  const liveTarget = order.maps?.[normalize(expectedName)];
  const catalogMaps = JSON.parse(require('node:fs').readFileSync(require('node:path').join(__dirname, 'autobtd6', 'maps.json'), 'utf8'));
  const catalogKnown = Object.values(catalogMaps).find(item => normalize(item.name) === normalize(expectedName));
  const known = order.maps?.[normalize(expectedName)] || catalogKnown;
  const catalogSource = require('node:fs').readFileSync(require('node:path').join(__dirname, '..', 'data', 'catalogs', 'map-catalog.js'), 'utf8');
  const catalogMatch = catalogSource.match(/\{([\s\S]*)\}/);
  const catalog = catalogMatch ? JSON.parse(`{${catalogMatch[1]}}`) : {};
  const catalogEntry = Object.values(catalog).flat().find(name => normalize(name) === normalize(expectedName));
  const catalogSupportsSlot = !!(catalogEntry && catalogKnown
    && catalogKnown.category?.toLowerCase() === expectedCategory?.toLowerCase()
    && Number(catalogKnown.page) === Number(expectedPage) && Number(catalogKnown.pos) === Number(expectedSlot));
  const expectedGlobalPage = Number.isInteger(known?.globalPage) ? known.globalPage
    : (catalogKnown && Number.isInteger(order.categoryStarts?.[expectedCategory]) && Number.isInteger(catalogKnown.page)
      ? order.categoryStarts[expectedCategory] + catalogKnown.page : null);
  const knownFinalExpert = normalize(expectedName) === 'ouch' && expectedCategory?.toLowerCase() === 'expert';
  // The category tab label can come back unreadable (null) during the same transition animation
  // that already makes individual tile labels unreliable elsewhere in this function. A uniquely
  // named tile found in the exact expected slot at high OCR confidence is strong enough evidence on
  // its own - don't let a blank category read block an otherwise-certain match.
  const categoryOk = result?.category ? result.category.toLowerCase() === expectedCategory?.toLowerCase() : true;
  const exactTile = !!(categoryOk && result?.candidates?.some(candidate => candidate.slot === Number(expectedSlot)
      && normalize(candidate.name) === normalize(expectedName) && candidate.score >= 0.84));
  // A unique map title in the expected slot is stronger evidence than the
  // animated page indicator, which can be unreadable during a page change.
  // If the target label is animated/unreadable, accept its catalog slot only when two
  // independently read map labels corroborate the same category/page/slot layout. One noisy
  // OCR label (especially on the last Expert page) is not enough to authorize a click.
  const matchingPageLabels = (result?.candidates || []).filter(candidate => {
    const entry = order.maps?.[normalize(candidate.name)];
    return entry && entry.category?.toLowerCase() === expectedCategory?.toLowerCase()
      && Number(entry.page) === Number(expectedPage) && Number(entry.pos) === Number(candidate.slot)
      && Number.isFinite(candidate.score) && candidate.score >= 0.84;
  });
  const targetSlotUnclaimed = !(result?.candidates || []).some(candidate => Number(candidate.slot) === Number(expectedSlot)
    && normalize(candidate.name) !== normalize(expectedName));
  const liveTargetConfirmsSlot = !!(liveTarget
    && liveTarget.category?.toLowerCase() === expectedCategory?.toLowerCase()
    && Number(liveTarget.page) === Number(expectedPage) && Number(liveTarget.pos) === Number(expectedSlot));
  const categoryAndPageMatch = result?.category?.toLowerCase() === expectedCategory?.toLowerCase()
    && expectedGlobalPage != null && result.page === expectedGlobalPage;
  const correct = exactTile || (categoryAndPageMatch && catalogSupportsSlot && liveTargetConfirmsSlot
    && targetSlotUnclaimed && matchingPageLabels.length >= 2
    && (knownFinalExpert ? result.page >= 16 : true));
  process.stdout.write(JSON.stringify({ correct: !!correct, page: result?.page ?? null,
    category: result?.category ?? null, visible: result?.candidates?.map(({ slot, name }) => ({ slot, name })) || [] }));
  if (!correct) process.exitCode = 2;
})().catch(error => { process.stderr.write(error.message); process.exitCode = 2; })
  .finally(() => shutdown());
