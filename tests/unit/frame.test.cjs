// Detección del contorno de lente y clasificación de la montura sobre fixtures sintéticos.
// Requiere: python3 tests/fixtures/gen_frames.py  (si faltan, la prueba se omite)
const test = require('node:test'), assert = require('node:assert/strict');
const fs = require('fs'), path = require('path');
const C = require('../lib/extract-core.cjs');
const OUT = path.join(__dirname, '..', 'fixtures', 'out');
const have = fs.existsSync(path.join(OUT, 'fr_metal.gray'));
const EXPECT = { acetate: 'full-acetate', metal: 'full-metal', nylor: 'nylor', rimless: 'rimless' };
const PADS = { acetate: false, metal: true };
for (const kind of Object.keys(EXPECT)) {
  test(`montura ${kind}`, { skip: !have && 'faltan fixtures (python3 tests/fixtures/gen_frames.py)' }, () => {
    const meta = JSON.parse(fs.readFileSync(path.join(OUT, `fr_${kind}.json`)));
    const buf = fs.readFileSync(path.join(OUT, `fr_${kind}.gray`)), g = new Float32Array(buf.length);
    for (let i = 0; i < buf.length; i++) g[i] = buf[i];
    const img = { g, w: meta.W, h: meta.H, ox: 0, oy: 0 }, s = meta.s, c = { x: (meta.W - 1) / 2, y: (meta.H - 1) / 2 };
    const cap = { W: meta.W, H: meta.H, tau: 0, iris: {}, box: {} }, det = {}, rim = {};
    for (const e of ['od', 'os']) {
      const t = meta.truth[e], ctr = { x: t.pupil[0], y: t.pupil[1] }; cap.iris[e] = ctr;
      det[e] = C.detectLensContour(img, ctr, s);
      const pts = det[e].inner.map(p => C.rotRel(p, c, 0)), us = pts.map(p => p.x), vs = pts.map(p => p.y);
      cap.box[e] = e === 'od' ? { n: Math.max(...us), t: Math.min(...us), top: Math.min(...vs), bot: Math.max(...vs) } : { n: Math.min(...us), t: Math.max(...us), top: Math.min(...vs), bot: Math.max(...vs) };
      if (kind === 'acetate' || kind === 'metal') {
        const xs = det[e].inner.map(p => p.x), ys = det[e].inner.map(p => p.y);
        const box = [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
        box.forEach((v, i) => assert.ok(Math.abs(v - t.box[i]) * s < 0.3, `${e} lado ${i}: ${((v - t.box[i]) * s).toFixed(2)} mm`));
      }
      if (kind === 'nylor') assert.ok(det[e].bottomWeak, 'nylon: el borde inferior debe marcarse como débil');
      rim[e] = C.rimAnalysis(img, ctr, det[e].inner, det[e].outer, s);
    }
    const fa = C.classifyFrame(rim.od, rim.os, det.od, det.os);
    assert.equal(fa.mounting, EXPECT[kind]);
    if (kind in PADS) assert.equal(C.padAnalysis(img, cap, s, fa, rim.od, rim.os).pads, PADS[kind]);
  });
}
