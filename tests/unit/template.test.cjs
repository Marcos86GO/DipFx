// Método montura: plantilla en pantalla (ancho exterior y cajas) como escala absoluta, con escenas proyectadas
// con el mismo modelo físico que el resto de pruebas (convergencia, Prentice, galbe de los bordes exteriores).
const test = require('node:test'), assert = require('node:assert/strict');
const C = require('../lib/extract-core.cjs');
const W = 1920, H = 1080, f = C.focalFromDfov(75, 16 / 9, W, H);
const XR = { od: -31.5, os: 32.5 };
function solveXL(XRt, Zm, rf, F) { let lo = -300, hi = 300; for (let i = 0; i < 200; i++) { const m = (lo + hi) / 2, v = m + rf * (m / Zm - (m - XRt) / 1000 * F); if (v < XRt) lo = m; else hi = m; } return (lo + hi) / 2; }
const near = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg}: ${a} vs ${b} (tol ${tol})`);

// Escena: plano de la lente a ZL; bordes exteriores (W = 131 mm) a 'off' mm por detrás de ese plano
function scene({ Rx = 0, v = 12, ZL = 420, wrap = 0, ss = 1 } = {}) {
  const p = { rx: { od: { s: Rx, c: 0, a: 0, base: '', t: '' }, os: { s: Rx, c: 0, a: 0, base: '', t: '' } }, index: 1.5, vertex: v, groove: 0, panto: 0, wrap, nearDist: 400, hvid: { od: 11.7, os: 11.7 }, mounting: 'rimless', outerOff: '', tpl: { W: 131, Aod: 52, Aos: 52, DBL: 18 } };
  const fs = f * ss, cxs = (W * ss - 1) / 2, cys = (H * ss - 1) / 2, L = C.lensData(p.rx.od, 1.5), rf = v + L.t / 2 + C.CR;
  const u = mm => mm * fs / ZL, off = (131 - 70) / 2 * Math.sin(wrap * Math.PI / 180);
  const iris = {}; for (const e of ['od', 'os']) iris[e] = { x: cxs + solveXL(XR[e], ZL, rf, L.h) * fs / ZL, y: cys + solveXL(0, ZL, rf, L.h) * fs / ZL, r: 20 * ss };
  const box = { od: { n: u(-9), t: u(-61), top: u(-16), bot: u(22) }, os: { n: u(9), t: u(61), top: u(-15), bot: u(23) } };
  const outer = { od: -65.5 * fs / (ZL + off), os: 65.5 * fs / (ZL + off) };
  const G = { id: 'G', W: W * ss, H: H * ss, f: fs, ss, iris, box, box0: box, outer, tau: 0, pose: { yaw: 0, pitch: 0 }, contourOK: { od: false, os: false } };
  return { M: { mode: 'frame', caps: [G] }, p, G };
}

test('plantilla: medidas a partir de las líneas (OD a la derecha de la pantalla)', () => {
  const t = C.tplFromLines({ oL: -66, tL: -61.5, nL: -9.2, nR: 8.8, tR: 61, oR: 65.4 });
  near(t.W, 131.4, 1e-9, 'W'); near(t.Aos, 52.3, 1e-9, 'A OI'); near(t.DBL, 18, 1e-9, 'DBL'); near(t.Aod, 52.2, 1e-9, 'A OD');
  assert.equal(C.tplFromLines({ oL: -65, oR: 65 }).Aod, undefined);
  near(C.tplDNC(t), 18 + 52.25, 1e-9, 'A + DBL'); assert.equal(C.tplDNC({ W: 130 }), null);
});

for (const sc of [{}, { Rx: -6, v: 14 }, { Rx: 3, v: 11, wrap: 10 }, { ss: 2 }]) {
  test(`método montura: ${JSON.stringify(sc)}`, () => {
    const { M, p } = scene(sc), R = C.solveAll(M, p);
    near(R.scale.ZL, 420, 0.02, 'Z (fusión)'); near(R.scale.outer.z, 420, 0.02, 'Z por ancho exterior'); near(R.scale.box.z, 420, 0.02, 'Z por cajas');
    assert.ok(!R.scale.flag, 'no debe marcar discrepancia');
    near(R.pdFar, 64, 0.02, 'DIP'); near(R.monoOD, 31.5, 0.02, 'mono OD'); near(R.monoOS, 32.5, 0.02, 'mono OI');
    near(R.hOD, 22, 0.02, 'altura OD'); near(R.DBL, 18, 0.02, 'DBL');
    near(R.frame.od.A * Math.cos((sc.wrap || 0) * Math.PI / 180), 52, 0.02, 'A proyectada');
  });
}

test('método montura: una sola referencia (solo ancho exterior o solo cajas)', () => {
  const a = scene(); a.p.tpl = { W: 131 };
  const Ra = C.solveAll(a.M, a.p); assert.equal(Ra.scale.box, null); near(Ra.pdFar, 64, 0.02, 'DIP solo ancho');
  const b = scene(); b.p.tpl = { Aod: 52, Aos: 52, DBL: 18 }; b.G.outer = null;
  const Rb = C.solveAll(b.M, b.p); assert.equal(Rb.scale.outer, null); near(Rb.pdFar, 64, 0.02, 'DIP solo cajas');
  const c = scene(); c.p.tpl = {}; assert.ok(C.solveAll(c.M, c.p).flags.length, 'sin plantilla debe avisar');
});

test('método montura: discrepancia entre referencias e incertidumbre', () => {
  const { M, p } = scene(); p.tpl = { ...p.tpl, W: 131 * 1.03 };
  const R = C.solveAll(M, p);
  assert.ok(R.scale.flag && R.flags.length, 'un 3 % de error en el ancho debe marcarse');
  const s2 = scene(), U = C.solveWithUnc(s2.M, s2.p, 0.15).u;
  assert.ok(U.pdFar > 0.2 && U.pdFar < 1.2, `± DIP ${U.pdFar}`);
  const s3 = scene(); s3.p.tpl = { W: 131 };
  assert.ok(C.solveWithUnc(s3.M, s3.p, 0.15).u.pdFar > U.pdFar, 'con una sola referencia el ± debe crecer');
});
