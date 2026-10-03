const { PNG } = require('pngjs');

function readPng(buffer) {
  const png = PNG.sync.read(buffer);
  return {
    width: png.width,
    height: png.height,
    get(x, y) {
      x = Math.max(0, Math.min(png.width - 1, Math.round(x)));
      y = Math.max(0, Math.min(png.height - 1, Math.round(y)));
      const i = (png.width * y + x) << 2;
      return [png.data[i], png.data[i + 1], png.data[i + 2], png.data[i + 3]];
    },
    averageColor(box) {
      let r = 0, g = 0, b = 0, n = 0;
      const x0 = Math.max(0, Math.round(box.x)), y0 = Math.max(0, Math.round(box.y));
      const x1 = Math.min(png.width, Math.round(box.x + box.w)), y1 = Math.min(png.height, Math.round(box.y + box.h));
      for (let y = y0; y < y1; y++) {
        for (let x = x0; x < x1; x++) {
          const i = (png.width * y + x) << 2;
          r += png.data[i]; g += png.data[i + 1]; b += png.data[i + 2]; n++;
        }
      }
      return n ? [Math.round(r / n), Math.round(g / n), Math.round(b / n)] : [0, 0, 0];
    },
  };
}

function colorDistance(a, b) {
  return Math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2);
}

module.exports = { readPng, colorDistance };
