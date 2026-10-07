// Read the displayed hero and Select/Selected button from a game-relative PNG on stdin.
const { readTitle, readNaturalText, shutdown } = require('../lib/ocr');

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
  // The old crop started inside the first glyph and ended before long names.
  // Include the full name banner, preserving its height so the subtitle stays out.
  const titleBox = scale({ x: 800, y: 25, w: 1050, h: 120 });
  const title = await readTitle(png, titleBox, { tighten: true,
    classify: (r, g, b) => g > 110 && b > 100 && r < g * 0.75 && r < b * 0.85 });
  // Hero name fills vary by hero: cyan-only processing erases yellow/orange
  // titles (evidenced by the live Admiral Brickell panel) and violet titles.
  // Keep separate masks so the red ribbon and white border do not merge into
  // the glyphs. Never turn an unreadable title into an inferred hero name.
  const warmTitle = await readTitle(png, titleBox, { tighten: true,
    classify: (r, g, b) => r > 180 && g > 65 && b < 125 && r > g * 1.05 });
  const violetTitle = await readTitle(png, titleBox, { tighten: true,
    classify: (r, g, b) => b > 145 && r > 100 && g > 70 && b > g * 1.15 && r > g * 0.9 });
  const magentaTitle = await readTitle(png, titleBox, { tighten: true,
    classify: (r, g, b) => r > 160 && b > 120 && g < 110 && r > g * 1.4 && b > g * 1.4 });
  // Rosalia's green name is absent from the cyan/warm/violet masks.
  // Keep the yellow ribbon and white border out; the OCR result must still
  // match the requested hero and the button must independently say Selected.
  const greenTitle = await readTitle(png, titleBox, { tighten: true,
    classify: (r, g, b) => g > 180 && r > 75 && b < 110 && g > r * 1.25 && g > b * 1.8 });
  const naturalTitle = await readNaturalText(png, titleBox);
  // Psi's three-letter yellow title merges with its yellow ribbon in the warm
  // mask. A narrow natural-color crop reads the letters without the ribbon tail.
  // Only accept the exact short name; partial reads of longer titles are ignored.
  const shortTitle = normalize(await readNaturalText(png, scale({ x: 860, y: 40, w: 260, h: 95 })));
  const shortPsiTitle = shortTitle === 'psi' ? shortTitle : '';
  const buttonBox = scale({ x: 1300, y: 760, w: 430, h: 110 });
  const outlinedButton = await readTitle(png, buttonBox);
  const naturalButton = await readNaturalText(png, buttonBox);
  // Isolate the bright label: green hero scenery otherwise turns SELECTED
  // into a supposed filled Select button. Density can corroborate text, but
  // cannot establish selection on its own.
  const isBrightLabel = (r, g, b) => g > 180 && r > 75 && b < 110 && g > r * 1.25 && g > b * 1.8;
  const labelButton = await readTitle(png, buttonBox, { tighten: true, classify: isBrightLabel });
  // Crop inside the white frame: including that frame merges Select's letters
  // into it at 1080p and produces readings such as "selecr".
  const whiteButton = await readTitle(png, scale({ x: 1390, y: 790, w: 230, h: 65 }),
    { tighten: true, classify: (r, g, b) => r > 200 && g > 200 && b > 200 });
  const buttons = [outlinedButton, naturalButton, labelButton, whiteButton].map(normalize);
  let green = 0, bright = 0, pixels = 0;
  const x0 = Math.max(0, buttonBox.x), y0 = Math.max(0, buttonBox.y);
  for (let y = y0; y < Math.min(image.height, y0 + buttonBox.h); y++) {
    for (let x = x0; x < Math.min(image.width, x0 + buttonBox.w); x++) {
      const i = (y * image.width + x) * 4;
      const r = image.data[i], g = image.data[i + 1], b = image.data[i + 2];
      if (g > 105 && g > r * 1.3 && g > b * 1.1) green++;
      if (isBrightLabel(r, g, b)) bright++;
      pixels++;
    }
  }
  const greenFraction = pixels ? green / pixels : 0;
  const brightFraction = pixels ? bright / pixels : 0;
  // These two narrow readings come from retained Selected frames. Do not fuzzy
  // match arbitrary words, infer ownership, or accept color without readable text.
  const label = normalize(labelButton);
  const repairedLabel = ['selecyeo', 'selecvep'].includes(label)
    && brightFraction >= 0.04 && brightFraction <= 0.22;
  const conflicting = buttons.some(value => /unlock|purchase|buy/.test(value));
  const resolvedButton = conflicting ? 'unknown'
    : buttons.includes('selected') || repairedLabel ? 'selected'
    : buttons.includes('select') ? 'select' : 'unknown';
  const titleCandidates = [...new Set([title, warmTitle, violetTitle, magentaTitle, greenTitle, naturalTitle, shortPsiTitle].map(normalize).filter(Boolean))];
  process.stdout.write(JSON.stringify({ title: titleCandidates[0] || '', titleCandidates,
    button: resolvedButton, buttonCandidates: [...new Set(buttons.filter(Boolean))],
    greenFraction: Number(greenFraction.toFixed(3)), brightFraction: Number(brightFraction.toFixed(3)) }));
})().catch(error => { process.stderr.write(error.message); process.exitCode = 2; })
  .finally(() => shutdown());
