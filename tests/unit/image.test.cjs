// Visión: bordes de la tarjeta y ajuste del iris sobre imágenes sintéticas (convenio: píxel i ↔ coordenada i).
const test = require('node:test'), assert = require('node:assert/strict');
const C = require('../lib/extract-core.cjs');
let seed = 7; const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
const W = 1920, H = 1080;
function mkImg() { const g = new Float32Array(W * H); for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) g[y * W + x] = 140 + 20 * Math.sin(x / 37) * Math.cos(y / 53) + (rnd() - 0.5) * 16; return { g, w: W, h: H, ox: 0, oy: 0 }; }
function cover(img, x0, x1, y0, y1, inside, val) { for (let y = Math.floor(y0); y < y1; y++) for (let x = Math.floor(x0); x < x1; x++) { let acc = 0; for (let sy = 0; sy < 4; sy++) for (let sx = 0; sx < 4; sx++) if (inside(x + (sx + .5) / 4 - .5, y + (sy + .5) / 4 - .5)) acc++; const a = acc / 16; img.g[y * W + x] = img.g[y * W + x] * (1 - a) + (val + (rnd() - .5) * 10) * a; } }

test('tarjeta: anchura con error < 0,6 px (inclinación ±3°, distractor de pelo)', () => {
  for (let t = 0; t < 10; t++) {
    const img = mkImg(), cw = 300 + rnd() * 80, ch = cw * 53.98 / 85.6, ang = (rnd() - 0.5) * 6 * Math.PI / 180, cxx = 960 + (rnd() - .5) * 60, cyy = 330;
    const c = Math.cos(ang), s = Math.sin(ang);
    cover(img, cxx - cw, cxx + cw, cyy - ch, cyy + ch, (X, Y) => { const u = (X - cxx) * c + (Y - cyy) * s, v = -(X - cxx) * s + (Y - cyy) * c; return Math.abs(u) <= cw / 2 && Math.abs(v) <= ch / 2; }, rnd() < 0.5 ? 230 : 60);
    for (let y = 150; y < 520; y++) for (let x = 600; x < 640; x++) img.g[y * W + x] = 50;
    const yTop = cyy - ch * 0.35, yBot = cyy + ch * 0.3;
    const det = C.detectCard(img, { xMid: 960 + (rnd() - .5) * 30, wExp: cw * (0.85 + rnd() * 0.3), yTop, yBot });
    assert.ok(det, 'tarjeta no detectada');
    const w = C.cardWidthPx(C.refineEdge(img, det.xl, yTop, yBot), C.refineEdge(img, det.xr, yTop, yBot)).w;
    assert.ok(Math.abs(w - cw) < 0.6, `t${t}: ${w} vs ${cw}`);
  }
});

test('iris: centro con error < 0,15 px (párpado ocultando la parte superior)', () => {
  for (let t = 0; t < 8; t++) {
    const img = { g: new Float32Array(400 * 300).fill(215), w: 400, h: 300, ox: 0, oy: 0 };
    for (let i = 0; i < img.g.length; i++) img.g[i] += (rnd() - .5) * 16;
    const cxx = 200.3 + rnd() * 3, cyy = 150.2 + rnd() * 3, r = 19;
    for (let y = 0; y < 300; y++) for (let x = 0; x < 400; x++) { let acc = 0; for (let sy = 0; sy < 4; sy++) for (let sx = 0; sx < 4; sx++) { const X = x + (sx + .5) / 4 - .5 - cxx, Y = y + (sy + .5) / 4 - .5 - cyy; if (X * X + Y * Y <= r * r) acc++; } const a = acc / 16; img.g[y * 400 + x] = img.g[y * 400 + x] * (1 - a) + 70 * a; }
    for (let y = 0; y < cyy - 0.7 * r; y++) for (let x = 0; x < 400; x++) img.g[y * 400 + x] = 150;
    const fit = C.refineIris(img, { x: cxx + 1.5, y: cyy - 1 }, r);
    assert.ok(fit, 'sin ajuste');
    assert.ok(Math.hypot(fit.x - cxx, fit.y - cyy) < 0.15, `t${t}`);
    assert.ok(Math.abs(fit.r - r) < 0.3);
  }
});
