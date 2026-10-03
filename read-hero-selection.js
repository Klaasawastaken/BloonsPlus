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
  const button = buttons.some(value => value.includes('selected')) ? 'selected'
    : buttons.some(value => value.includes('select')) ? 'select' : 'unknown';
  process.stdout.write(JSON.stringify({ title: normalize(title), button }));
})().catch(error => { process.stderr.write(error.message); process.exitCode = 2; })
  .finally(() => shutdown());
