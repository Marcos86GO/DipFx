// Geometría completa con escenas sintéticas proyectadas con el mismo modelo físico:
// convergencia hacia la cámara, prisma de Prentice, aumento del iris, cambio de distancia entre fotos.
const test = require('node:test'), assert = require('node:assert/strict');
const C = require('../lib/extract-core.cjs');
const W = 1920, H = 1080, f = C.focalFromDfov(75, 16 / 9, W, H), cx = (W - 1) / 2, cy = (H - 1) / 2;
const XR = { od: -31.5, os: 32.5 };   // centros de rotación (mm) respecto al centro de la montura
// Encuentra el punto del plano de la lente por el que pasa la línea de mirada hacia la cámara
function solveXL(XRt, Zm, rf, F) { let lo = -300, hi = 300; for (let i = 0; i < 200; i++) { const m = (lo + hi) / 2, v = m + rf * (m / Zm - (m - XRt) / 1000 * F); if (v < XRt) lo = m; else hi = m; } return (lo + hi) / 2; }
const near = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg}: ${a} vs ${b} (tol ${tol})`);

for (const [Rx, v, off] of [[0, 12, 1.5], [-6, 14, 1.5], [3, 11, 2]]) {
  test(`método tarjeta: Rx ${Rx}, vértice ${v}`, () => {
    const p = { rx: { od: { s: Rx, c: 0, a: 0, base: '', t: '' }, os: { s: Rx, c: 0, a: 0, base: '', t: '' } }, index: 1.5, vertex: v, cardOffset: off, groove: 0, panto: 0, wrap: 0, nearDist: 400, hvid: { od: 11.7, os: 11.7 }, mounting: 'rimless' };
    const L = C.lensData(p.rx.od, 1.5), ZL = 420, rf = v + L.t / 2 + C.CR, Zc = ZL - off;
    const iris = {}; for (const e of ['od', 'os']) iris[e] = { x: cx + solveXL(XR[e], ZL, rf, L.h) * f / ZL, y: cy + solveXL(0, ZL, rf, L.h) * f / ZL, r: 20 };
    const cw = C.CARD_W / 2 * f / Zc, card = { L: { x1: cx - cw, y1: 300, x2: cx - cw, y2: 400 }, R: { x1: cx + cw, y1: 300, x2: cx + cw, y2: 400 } };
    const u = mm => mm * f / ZL;
    const box = { od: { n: u(-9), t: u(-61), top: u(-16), bot: u(22) }, os: { n: u(9), t: u(61), top: u(-15), bot: u(23) } };
    const G = { id: 'G', W, H, f, iris, card, box, box0: box, tau: 0, pose: { yaw: 0, pitch: 0 }, contourOK: { od: false, os: false } };
    const R = C.solveAll({ mode: 'card', caps: [G] }, p);
    near(R.pdFar, 64, 0.02, 'DIP'); near(R.monoOD, 31.5, 0.02, 'mono OD'); near(R.monoOS, 32.5, 0.02, 'mono OI');
    near(R.hOD, 22, 0.02, 'altura OD'); near(R.hOS, 23, 0.02, 'altura OI');
    near(R.frame.od.A, 52, 0.02, 'A'); near(R.DBL, 18, 0.02, 'DBL');
  });
}

function irisScene({ vTrue = 13, Rx = { od: -5, os: -4 }, k = 1.02, hv = 11.7, ZN = 430, shift = [0, 0] }) {
  const rfp = C.CR - C.E_L, irisN = {};
  for (const e of ['od', 'os']) { const xp = (XR[e] - shift[0]) * ZN / (ZN + rfp); irisN[e] = { x: cx + xp * f / ZN, y: cy - shift[1] * ZN / (ZN + rfp) * f / ZN, r: hv / 2 * f / ZN }; }
  const lmkN = Array.from({ length: 478 }, (_, i) => ({ x: cx + 300 * Math.cos(i), y: cy + 300 * Math.sin(i * 1.3) }));
  const N = { id: 'N', W, H, f, iris: irisN, bridge: { x: cx - shift[0] * f / ZN, y: cy }, lmk: lmkN, pose: { yaw: 0, pitch: 0 } };
  const Z2 = ZN / k, p0 = { rx: { od: { s: Rx.od, c: 0, a: 0, base: '', t: '' }, os: { s: Rx.os, c: 0, a: 0, base: '', t: '' } }, index: 1.5 };
  const lens = { od: C.lensData(p0.rx.od, 1.5), os: C.lensData(p0.rx.os, 1.5) };
  const Zm = Z2 - C.E_L - vTrue - (lens.od.t + lens.os.t) / 4, irisG = {};
  for (const e of ['od', 'os']) {
    const L = lens[e], rf = vTrue + L.t / 2 + C.CR;
    const A = C.apparentMag(vTrue + C.E_L, Z2 - (vTrue + C.E_L) - L.t, L.h, L.F1, L.t, L.n);
    irisG[e] = { x: cx + solveXL(XR[e] - shift[0], Zm, rf, L.h) * f / Zm, y: cy + solveXL(-shift[1], Zm, rf, L.h) * f / Zm, r: hv / 2 * f / Z2 * A };
  }
  const u = mm => mm * f / Zm;
  const box = { od: { n: u(-9 - shift[0]), t: u(-61 - shift[0]), top: u(-16 - shift[1]), bot: u(22 - shift[1]) }, os: { n: u(9 - shift[0]), t: u(61 - shift[0]), top: u(-15 - shift[1]), bot: u(23 - shift[1]) } };
  const G = { id: 'G', W, H, f, iris: irisG, box, box0: JSON.parse(JSON.stringify(box)), tau: 0, lmk: lmkN.map(q => ({ x: cx + (q.x - cx) * k, y: cy + (q.y - cy) * k })), pose: { yaw: 0, pitch: 0 }, contourOK: { od: false, os: false } };
  const p = { ...p0, vertex: 12, groove: 0, panto: 0, wrap: 0, nearDist: 400, hvid: { od: hv, os: hv }, hvidUser: false, mounting: 'rimless' };
  return { M: { mode: 'iris', caps: [N, G] }, p };
}
for (const sc of [{}, { vTrue: 16, Rx: { od: -7, os: -6.5 } }, { vTrue: 10, Rx: { od: 4, os: 3.5 }, k: 0.985 }, { shift: [5, -6] }]) {
  test(`método iris (2 fotos): ${JSON.stringify(sc)}`, () => {
    const { M, p } = irisScene(sc), R = C.solveAll(M, p);
    near(R.pdFar, 64, 0.02, 'DIP (foto sin gafas)');
    near(R.k, sc.k || 1.02, 1e-6, 'escala entre fotos');
    for (const e of ['od', 'os']) { assert.ok(R.eyes[e].ok, 'vértice ' + e); near(R.eyes[e].v, sc.vTrue || 13, 0.05, 'vértice ' + e); }
    near(R.monoOD, 31.5, 0.1, 'mono OD'); near(R.monoOS, 32.5, 0.1, 'mono OI');
    near(R.hOD, 22, 0.15, 'altura OD'); near(R.hOS, 23, 0.15, 'altura OI');
    near(R.frame.od.A, 52, 0.3, 'A'); near(R.DBL, 18, 0.15, 'DBL');
  });
}
test('incertidumbre: blanco-blanco introducido reduce el ± de la DIP', () => {
  const { M, p } = irisScene({});
  const u0 = C.solveWithUnc(M, p, 0.15).u.pdFar, u1 = C.solveWithUnc(M, { ...p, hvidUser: true }, 0.15).u.pdFar;
  assert.ok(u0 > 2 && u1 < 1, `${u0} -> ${u1}`);
});
