// Ráfaga: registro subpíxel (NCC + Lucas–Kanade), semejanza a partir de dos zonas y apilado con remuestreo ×2.
const test = require('node:test'), assert = require('node:assert/strict');
const C = require('../lib/extract-core.cjs');
let seed = 11; const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
const gauss = () => { let s = 0; for (let i = 0; i < 6; i++) s += rnd(); return (s - 3) * Math.SQRT2; };
const tex = (x, y) => 128 + 40 * Math.sin(x / 7.3 + y / 11.1) + 30 * Math.cos(x / 5.1 - y / 8.7) + 20 * Math.sin((x + 2 * y) / 3.7);
function grayImg(w, h, fn, noise = 0) { const g = new Float32Array(w * h); for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) g[y * w + x] = fn(x, y) + noise * gauss(); return { g, w, h, ox: 0, oy: 0 }; }

test('registro: desplazamiento subpíxel con error < 0,05 px (con ruido y cambio de brillo)', () => {
  const T = grayImg(240, 180, tex, 2);
  const rect = { x0: 60, y0: 50, x1: 180, y1: 130 };
  for (let t = 0; t < 6; t++) {
    const d = { x: (rnd() - 0.5) * 6, y: (rnd() - 0.5) * 6 };
    const I = grayImg(240, 180, (x, y) => tex(x - d.x, y - d.y) + 7, 2);
    const r = C.registerShift(T, I, rect, { x: d.x + (rnd() - 0.5) * 2, y: d.y + (rnd() - 0.5) * 2 });
    assert.ok(Math.hypot(r.x - d.x, r.y - d.y) < 0.05, `t${t}: (${r.x.toFixed(3)}, ${r.y.toFixed(3)}) vs (${d.x.toFixed(3)}, ${d.y.toFixed(3)})`);
    assert.ok(r.ncc > 0.95, 'NCC ' + r.ncc);
  }
});

test('semejanza a partir de dos zonas (giro 0,3°, escala 1,002 y traslación)', () => {
  const a = 0.3 * Math.PI / 180, s = 1.002, Tt = { ar: s * Math.cos(a), ai: s * Math.sin(a), br: 3.2, bi: -1.7 };
  const ap = q => ({ x: Tt.ar * q.x - Tt.ai * q.y + Tt.br, y: Tt.ar * q.y + Tt.ai * q.x + Tt.bi });
  const c1 = { x: 700, y: 520 }, c2 = { x: 1010, y: 530 }, p1 = ap(c1), p2 = ap(c2);
  const S = C.similarity2(c1, { x: p1.x - c1.x, y: p1.y - c1.y }, c2, { x: p2.x - c2.x, y: p2.y - c2.y });
  for (const k of ['ar', 'ai', 'br', 'bi']) assert.ok(Math.abs(S[k] - Tt[k]) < 1e-9, k);
});

test('apilado ×2: conserva la geometría (convenio de píxel) y reduce el ruido', () => {
  const w = 120, h = 90, X0 = 60.37, Y0 = 44.81, R = 18;
  const disk = (x, y) => { const d = Math.hypot(x - X0, y - Y0) - R; return 60 + 150 / (1 + Math.exp(d / 0.6)); };
  const N = 6, frames = [], maps = [];
  for (let k = 0; k < N; k++) {
    const d = k ? { x: (rnd() - 0.5) * 3, y: (rnd() - 0.5) * 3 } : { x: 0, y: 0 };
    const data = new Uint8ClampedArray(w * h * 4);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const v = disk(x - d.x, y - d.y) + 6 * gauss(), o = (y * w + x) * 4; data[o] = data[o + 1] = data[o + 2] = v; data[o + 3] = 255; }
    frames.push({ data, w, h, ox: 0, oy: 0 }); maps.push({ ar: 1, ai: 0, br: d.x, bi: d.y });
  }
  const roi = { x0: 10, y0: 10, x1: 110, y1: 80 };
  for (const up of [1, 2]) {
    const out = C.stackRGBA(frames, maps, roi, up);
    assert.equal(out.w, 101 * up); assert.equal(out.ox, 10 * up);
    // centroide del disco (umbral sobre el fondo) en coordenadas de la imagen original
    let sx = 0, sy = 0, sw = 0;
    for (let j = 0; j < out.h; j++) for (let i = 0; i < out.w; i++) { const v = out.data[(j * out.w + i) * 4] - 135; if (v <= 0) continue; const x = (out.ox + i + 0.5) / up - 0.5, y = (out.oy + j + 0.5) / up - 0.5; sx += x * v; sy += y * v; sw += v; }
    assert.ok(Math.hypot(sx / sw - X0, sy / sw - Y0) < 0.05, `up ${up}: centro (${(sx / sw).toFixed(3)}, ${(sy / sw).toFixed(3)})`);
    // ruido en una zona plana del fondo: debe bajar cerca de 1/√N respecto a un fotograma
    const sd = (get) => { let a = 0, a2 = 0, n = 0; for (let y = 14; y < 24; y++) for (let x = 14; x < 34; x++) { const v = get(x, y); a += v; a2 += v * v; n++; } return Math.sqrt(a2 / n - (a / n) ** 2); };
    const s1 = sd((x, y) => frames[0].data[(y * w + x) * 4]);
    const sN = sd((x, y) => out.data[(((y * up) - out.oy) * out.w + (x * up - out.ox)) * 4]);
    assert.ok(sN < 0.6 * s1, `up ${up}: ruido ${sN.toFixed(2)} vs ${s1.toFixed(2)}`);
  }
});
