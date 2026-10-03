const canvas = document.querySelector('#canvas');
const ctx = canvas.getContext('2d');
const statusEl = document.querySelector('#status');
let image = new Image();
let calibration = { referenceSize: null, screenAnchors: {}, fields: {}, borderPalette: {} };
let box = null; // current pending selection {x,y,w,h}
let dragStart = null;

function redraw() {
  if (!image.width) return;
  ctx.drawImage(image, 0, 0);
  ctx.lineWidth = 2;
  const drawBox = (b, color, label) => {
    ctx.strokeStyle = color; ctx.strokeRect(b.x, b.y, b.w, b.h);
    if (label) { ctx.fillStyle = color; ctx.font = '12px system-ui'; ctx.fillText(label, b.x + 2, Math.max(12, b.y - 4)); }
  };
  Object.entries(calibration.screenAnchors).forEach(([name, a]) => drawBox(a.box, '#7bd88f', name));
  Object.entries(calibration.fields).forEach(([name, value]) => {
    if (name === 'mapTiles') Object.entries(value).forEach(([mapName, b]) => drawBox(b, '#f4c261', mapName));
    else drawBox(value, '#88b4ff', name);
  });
  if (box) drawBox(box, '#ff6b81', 'selection');
}

async function loadCapture() {
  statusEl.textContent = 'Capturing…';
  try {
    const response = await fetch('/api/capture', { cache: 'no-store' });
    if (!response.ok) throw new Error((await response.json()).error || 'capture failed');
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    await new Promise((resolve, reject) => { image.onload = resolve; image.onerror = reject; image.src = url; });
    const reference = calibration.referenceSize || { width: image.width, height: image.height };
    if (reference.width !== image.width || reference.height !== image.height) {
      const scale = b => ({ x: b.x * image.width / reference.width, y: b.y * image.height / reference.height, w: b.w * image.width / reference.width, h: b.h * image.height / reference.height });
      Object.values(calibration.screenAnchors).forEach(anchor => { anchor.box = scale(anchor.box); });
      Object.entries(calibration.fields).forEach(([name, value]) => {
        if (name === 'mapTiles') Object.keys(value).forEach(map => { value[map] = scale(value[map]); });
        else calibration.fields[name] = scale(value);
      });
    }
    calibration.referenceSize = { width: image.width, height: image.height };
    canvas.width = image.width; canvas.height = image.height;
    URL.revokeObjectURL(url);
    statusEl.textContent = `Captured ${image.width}×${image.height}`;
    redraw();
  } catch (error) { statusEl.textContent = `Capture unavailable: ${error.message}. Open BTD6 and try Recapture.`; }
}

async function loadCalibration() {
  try {
    const response = await fetch('/api/calibration', { cache: 'no-store' });
    const data = await response.json();
    calibration = { referenceSize: { width: 2194, height: 1234 }, screenAnchors: {}, fields: {}, borderPalette: {}, ...data };
    if (!calibration.fields.mapTiles) calibration.fields.mapTiles = {};
    renderLists();
    redraw();
  } catch { /* start empty */ }
}

function renderLists() {
  const anchorList = document.querySelector('#anchor-list'); anchorList.replaceChildren();
  Object.keys(calibration.screenAnchors).forEach(name => {
    const row = document.createElement('div'); row.innerHTML = `<span>${name}</span>`;
    const del = document.createElement('button'); del.textContent = '×'; del.onclick = () => { delete calibration.screenAnchors[name]; renderLists(); redraw(); };
    row.append(del); anchorList.append(row);
  });
  const fieldList = document.querySelector('#field-list'); fieldList.replaceChildren();
  Object.keys(calibration.fields).filter(name => name !== 'mapTiles').forEach(name => {
    const row = document.createElement('div'); row.innerHTML = `<span>${name}</span>`;
    const del = document.createElement('button'); del.textContent = '×'; del.onclick = () => { delete calibration.fields[name]; renderLists(); redraw(); };
    row.append(del); fieldList.append(row);
  });
  const tileList = document.querySelector('#tile-list'); tileList.replaceChildren();
  Object.keys(calibration.fields.mapTiles || {}).forEach(name => {
    const row = document.createElement('div'); row.innerHTML = `<span>${name}</span>`;
    const del = document.createElement('button'); del.textContent = '×'; del.onclick = () => { delete calibration.fields.mapTiles[name]; renderLists(); redraw(); };
    row.append(del); tileList.append(row);
  });
  const borderList = document.querySelector('#border-list'); borderList.replaceChildren();
  Object.entries(calibration.borderPalette).forEach(([label, color]) => {
    const row = document.createElement('div');
    row.innerHTML = `<span><i class="swatch" style="background:rgb(${color.join(',')})"></i>${label}</span>`;
    const del = document.createElement('button'); del.textContent = '×'; del.onclick = () => { delete calibration.borderPalette[label]; renderLists(); redraw(); };
    row.append(del); borderList.append(row);
  });
}

function averageColorOf(b) {
  const data = ctx.getImageData(Math.round(b.x), Math.round(b.y), Math.max(1, Math.round(b.w)), Math.max(1, Math.round(b.h))).data;
  let r = 0, g = 0, bl = 0, n = data.length / 4;
  for (let i = 0; i < data.length; i += 4) { r += data[i]; g += data[i + 1]; bl += data[i + 2]; }
  return [Math.round(r / n), Math.round(g / n), Math.round(bl / n)];
}

canvas.addEventListener('mousedown', event => {
  const rect = canvas.getBoundingClientRect();
  dragStart = { x: event.clientX - rect.left, y: event.clientY - rect.top };
});
canvas.addEventListener('mousemove', event => {
  if (!dragStart) return;
  const rect = canvas.getBoundingClientRect();
  const x = event.clientX - rect.left, y = event.clientY - rect.top;
  box = { x: Math.min(dragStart.x, x), y: Math.min(dragStart.y, y), w: Math.abs(x - dragStart.x), h: Math.abs(y - dragStart.y) };
  redraw();
});
window.addEventListener('mouseup', () => { dragStart = null; });

document.querySelector('#recapture').addEventListener('click', loadCapture);
document.querySelector('#save-anchor').addEventListener('click', () => {
  if (!box || box.w < 2 || box.h < 2) return alert('Draw a box first.');
  const name = document.querySelector('#anchor-name').value;
  const tolerance = Number(document.querySelector('#anchor-tolerance').value) || 30;
  calibration.screenAnchors[name] = { box, expectedColor: averageColorOf(box), tolerance };
  box = null; renderLists(); redraw();
});
document.querySelector('#save-field').addEventListener('click', () => {
  if (!box || box.w < 2 || box.h < 2) return alert('Draw a box first.');
  calibration.fields[document.querySelector('#field-name').value] = box;
  box = null; renderLists(); redraw();
});
document.querySelector('#save-tile').addEventListener('click', () => {
  if (!box || box.w < 2 || box.h < 2) return alert('Draw a box first.');
  const name = document.querySelector('#map-name').value.trim();
  if (!name) return alert('Enter the map name.');
  calibration.fields.mapTiles[name] = box;
  box = null; renderLists(); redraw();
});
document.querySelector('#save-border').addEventListener('click', () => {
  if (!box || box.w < 2 || box.h < 2) return alert('Draw a box first.');
  calibration.borderPalette[document.querySelector('#border-label').value] = averageColorOf(box);
  box = null; renderLists(); redraw();
});
document.querySelector('#save-all').addEventListener('click', async () => {
  const response = await fetch('/api/calibration', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(calibration) });
  statusEl.textContent = response.ok ? 'Calibration saved.' : 'Save failed.';
});

loadCalibration().then(loadCapture);
