// Read the displayed hero and Select/Selected button from a game-relative PNG on stdin.
const { readTitle, readNaturalText, shutdown } = require('./lib/ocr');

const normalize = value => String(value).toLowerCase().replace(/[^a-z]/g, '');
(async () => {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  const png = Buffer.concat(chunks);
  const { PNG } = require('pngjs');
  const image = PNG.sync.read(png);
  const sx = image.width / 2560, sy = image.height / 1440;
  const scale = box => ({ x: Math.round(box.x * sx), y: Math.round(box.y * sy),
    w: Math.round(box.w * sx), h: Math.round(box.h * sy) });
  const title = await readNaturalText(png, scale({ x: 900, y: 25, w: 450, h: 120 }));
  const buttonBox = scale({ x: 1300, y: 760, w: 430, h: 110 });
  const outlinedButton = await readTitle(png, buttonBox);
  const naturalButton = await readNaturalText(png, buttonBox);
  const buttons = [outlinedButton, naturalButton].map(normalize);
  // The current green Select button defeats text OCR on some resolutions.
  // A filled button covers most of this box; the small green SELECTED label
  // occupies much less. Both states were measured on live 960x540 VM frames.
  let green = 0, pixels = 0;
  const x0 = Math.max(0, buttonBox.x), y0 = Math.max(0, buttonBox.y);
  for (let y = y0; y < Math.min(image.height, y0 + buttonBox.h); y++) {
    for (let x = x0; x < Math.min(image.width, x0 + buttonBox.w); x++) {
      const i = (y * image.width + x) * 4;
      const r = image.data[i], g = image.data[i + 1], b = image.data[i + 2];
      if (g > 105 && g > r * 1.3 && g > b * 1.1) green++;
      pixels++;
    }
  }
  const greenFraction = pixels ? green / pixels : 0;
  const button = buttons.some(value => value.includes('selected')) ? 'selected'
    : buttons.some(value => value.includes('select')) ? 'select' : 'unknown';
  const visualButton = greenFraction > 0.42 ? 'select' : greenFraction > 0.05 ? 'selected' : 'unknown';
  process.stdout.write(JSON.stringify({ title: normalize(title), button: button === 'unknown' ? visualButton : button, greenFraction: Number(greenFraction.toFixed(3)) }));
})().catch(error => { process.stderr.write(error.message); process.exitCode = 2; })
  .finally(() => shutdown());
