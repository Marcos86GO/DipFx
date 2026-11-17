// Modelo óptico: aumento aparente del iris a través de una lente gruesa y despeje del vértice.
const test = require('node:test'), assert = require('node:assert/strict');
const C = require('../lib/extract-core.cjs');

test('lente plana: aumento ~1 (solo factor de forma y desplazamiento de imagen)', () => {
  const L = C.lensData({ s: 0, c: 0, a: 0 }, 1.5);
  const A = C.apparentMag(15, 435 - 15 - L.t, 0, L.F1, L.t, L.n);
  assert.ok(A > 1.0 && A < 1.02, `A=${A}`);
});

test('el vértice se recupera exactamente a partir del aumento (|F| >= 1 D)', () => {
  for (const F of [-8, -6, -4, -2, -1, 1, 2, 4, 6]) {
    const L = C.lensData({ s: F, c: 0, a: 0 }, 1.5);
    const A = C.apparentMag(15, 435 - 15 - L.t, F, L.F1, L.t, L.n);
    const sol = C.solveVertexH(A, 435, L, F);
    assert.ok(sol.ok, `F=${F}`);
    assert.ok(Math.abs(sol.h - 15) < 0.01, `F=${F} h=${sol.h}`);
  }
});

test('graduación baja: no se intenta despejar el vértice', () => {
  const L = C.lensData({ s: 0.25, c: 0, a: 0 }, 1.5);
  assert.equal(C.solveVertexH(1.01, 435, L, 0.25).ok, false);
});

test('potencias por meridiano (cil. negativo)', () => {
  assert.deepEqual(C.meridianPowers({ s: -1, c: -3, a: 180 }), { h: -1, v: -4 });
  const m = C.meridianPowers({ s: -1, c: -3, a: 90 });
  assert.ok(Math.abs(m.h + 4) < 1e-9 && Math.abs(m.v + 1) < 1e-9);
});

test('fusión del vértice con el valor previo', () => {
  const fz = C.fuseVertex([{ ok: true, v: 16, sd: 0.5 }, { ok: false }], 12, 2.5);
  assert.ok(fz.v > 15.5 && fz.v < 16, `v=${fz.v}`);
  assert.equal(C.fuseVertex([{ ok: false }, { ok: false }], 12, 2.5).v, 12);
});
