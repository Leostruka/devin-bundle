/* themes.js - dual-theme registry: medieval (RTS) vs office (tycoon).
   A theme = palette + sky + lights + building look params + foley verbs.
   Geometry builders live in buildings.js/units.js keyed off these. */

export const THEMES = {
  medieval: {
    id: "medieval", label: "Medieval Realm",
    sky: { top: 0x8fb6e8, horizon: 0xf3d9a4, night: 0x0a1020 },
    sun: { color: 0xffe8c0, intensity: 2.6, pos: [-34, 46, 22] },
    hemi: { sky: 0xa8c8ff, ground: 0x2a2018, intensity: 0.55 },
    terrain: {
      root: "#4a6741", ".devin": "#5d6e4a", agents: "#67744a",
      scripts: "#4d5f45", docs: "#5f6b52", tests: "#52664a",
      extensions: "#586b50", data: "#4f6449", skills: "#647150",
      hooks: "#4a6046", "_": "#4a6741",
    },
    road: "#7a6a4f", water: "#2e5a7a",
    building: { wall: 0x9b8a70, trim: 0x6e5a41, roof: 0x7a4a33,
                stone: 0x8f8d84, glow: 0xffb347 },
    unitBody: 0xb8c8e0, unitTrim: 0xd4af37, worker: 0xc9b896,
    accent: 0xd4af37, panel: "#141c14", hp: "#6fe39a",
    verbs: { order: "horn", work: "anvil", arrive: "boots",
             alert: "war-drum" },
  },
  office: {
    id: "office", label: "Office Tycoon",
    sky: { top: 0xbfd4e8, horizon: 0xe8eef4, night: 0x10141c },
    sun: { color: 0xf4f6ff, intensity: 2.0, pos: [30, 42, 28] },
    hemi: { sky: 0xdfeaf8, ground: 0x33302e, intensity: 0.8 },
    terrain: {
      root: "#7a8a94", ".devin": "#8a94a0", agents: "#94a0aa",
      scripts: "#7d8b96", docs: "#8f9aa5", tests: "#82909c",
      extensions: "#8895a1", data: "#7e8c97", skills: "#92a0ab",
      hooks: "#7a8894", "_": "#7a8a94",
    },
    road: "#b9c2c9", water: "#6fa8c8",
    building: { wall: 0xc8d2dc, trim: 0x5a6c7c, roof: 0x3c4c5e,
                stone: 0xaab4be, glow: 0x9fd8ff },
    unitBody: 0xd8e4ee, unitTrim: 0x4a9fd8, worker: 0xb8c4d0,
    accent: 0x4a9fd8, panel: "#101820", hp: "#4ad8a0",
    verbs: { order: "ding", work: "keys", arrive: "chair",
             alert: "alarm" },
  },
};

export function themeOf(name) {
  return THEMES[name] || THEMES.medieval;
}

/* Procedural canvas texture helpers (PBR maps without downloads). */
export function noiseCanvas(size, base, vary, scale = 8) {
  const c = document.createElement("canvas");
  c.width = c.height = size;
  const ctx = c.getContext("2d");
  ctx.fillStyle = base; ctx.fillRect(0, 0, size, size);
  const img = ctx.getImageData(0, 0, size, size);
  const rnd = mulberry(1337);
  for (let y = 0; y < size; y++)
    for (let x = 0; x < size; x++) {
      const n = vnoise(x / scale, y / scale, rnd);
      const i = (y * size + x) * 4;
      const k = 1 + (n - 0.5) * vary;
      img.data[i] *= k; img.data[i + 1] *= k; img.data[i + 2] *= k;
    }
  ctx.putImageData(img, 0, 0);
  return c;
}

export function normalFromHeight(src, strength = 2.0) {
  const size = src.width;
  const c = document.createElement("canvas");
  c.width = c.height = size;
  const ctx = c.getContext("2d");
  const sctx = src.getContext("2d");
  const sd = sctx.getImageData(0, 0, size, size).data;
  const img = ctx.createImageData(size, size);
  const h = (x, y) => sd[(((y + size) % size) * size +
    ((x + size) % size)) * 4] / 255;
  for (let y = 0; y < size; y++)
    for (let x = 0; x < size; x++) {
      const dx = (h(x + 1, y) - h(x - 1, y)) * strength;
      const dy = (h(x, y + 1) - h(x, y - 1)) * strength;
      const inv = 1 / Math.hypot(dx, dy, 1);
      const i = (y * size + x) * 4;
      img.data[i] = (-dx * inv * 0.5 + 0.5) * 255;
      img.data[i + 1] = (-dy * inv * 0.5 + 0.5) * 255;
      img.data[i + 2] = inv * 255;
      img.data[i + 3] = 255;
    }
  ctx.putImageData(img, 0, 0);
  return c;
}

function mulberry(a) {
  return function () {
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
function vnoise(x, y, rnd) {
  const xi = Math.floor(x), yi = Math.floor(y);
  const xf = x - xi, yf = y - yi;
  const h = (a, b) => {
    const v = Math.sin(a * 127.1 + b * 311.7) * 43758.5453;
    return v - Math.floor(v);
  };
  const s = (t) => t * t * (3 - 2 * t);
  return h(xi, yi) * (1 - s(xf)) * (1 - s(yf)) +
         h(xi + 1, yi) * s(xf) * (1 - s(yf)) +
         h(xi, yi + 1) * (1 - s(xf)) * s(yf) +
         h(xi + 1, yi + 1) * s(xf) * s(yf);
}
