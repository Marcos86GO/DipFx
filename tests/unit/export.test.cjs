// Exportación de una medida: OMA (DCS) y JSON.
const test = require('node:test'), assert = require('node:assert/strict');
const C = require('../lib/extract-core.cjs');
const R = { mode: 'frame', pdFar: 64.04, monoOD: 31.5, monoOS: 32.54, hOD: 22.6, hOS: 22.4, pdNear: 60.1, monoNearOD: 29.6, monoNearOS: 30.5, DBL: 17.1, DNC: 70.2, vertex: 12, mounting: 'full-acetate', flags: [], flagsEn: [],
  frame: { od: { A: 52.8, B: 39.2, ED: 58.6, decH: 3.5, decV: 3, MBS: 68 }, os: { A: 52.9, B: 39.1, ED: 58.8, decH: 2.5, decV: 3, MBS: 66 } } };
const u = { pdFar: 0.7, monoOD: 0.4, monoOS: 0.5, hOD: 0.5, hOS: 0.5 };
const p = { rx: { od: { s: -2.25, c: -0.5, a: 175 }, os: { s: -2, c: 0, a: 0 } }, index: 1.6, vertex: 12, wrap: 0, panto: 0, nearDist: 400, tpl: {} };
const lines = t => t.split('\r\n').filter(Boolean);
const get = (t, k) => { const l = lines(t).find(x => x.startsWith(k + '=')); return l ? l.slice(k.length + 1) : undefined; };

test('OMA: etiquetas DCS, ojo derecho;izquierdo, CR LF y punto decimal', () => {
  const rec = C.buildRecord(R, u, p, { id: 'abcdef123456', date: '2026-11-18T10:20:30.000Z', frameName: 'Acetato; negro=52', material: 'acetate', pads: false });
  const t = C.recordToOMA(rec, { name: 'Ana', ref: 'H-12' }, { job: '000123' });
  assert.ok(t.endsWith('\r\n') && !/[^\r]\n/.test(t), 'líneas con CR LF');
  assert.equal(get(t, 'JOB'), '000123'); assert.equal(get(t, 'DO'), 'B');
  assert.equal(get(t, 'SPH'), '-2.25;-2.00'); assert.equal(get(t, 'CYL'), '-0.50;0.00'); assert.equal(get(t, 'AX'), '175;0');
  assert.equal(get(t, 'IPD'), '31.50;32.54'); assert.equal(get(t, 'NPD'), '29.60;30.50'); assert.equal(get(t, 'SEGHT'), '22.60;22.40');
  assert.equal(get(t, 'HBOX'), '52.80;52.90'); assert.equal(get(t, 'VBOX'), '39.20;39.10'); assert.equal(get(t, 'FED'), '58.60;58.80'); assert.equal(get(t, 'DBL'), '17.10');
  assert.equal(get(t, 'BVD'), undefined, 'el vértice supuesto no se envía'); assert.equal(get(t, 'PANTO'), undefined); assert.equal(get(t, 'ZTILT'), undefined);
  assert.equal(get(t, '_DIPFX_REF'), 'H-12'); assert.equal(get(t, '_DIPFX_NAME'), undefined, 'el nombre solo si se pide');
  assert.equal(get(t, '_DIPFX_FRAME'), 'Acetato  negro 52', 'sin ; ni = en los textos'); assert.equal(get(t, '_DIPFX_PADS'), '0');
});

test('OMA: posición de uso medida (BVD, PANTO, ZTILT) y sin graduación', () => {
  const rec = C.buildRecord(R, u, { ...p, rx: { od: { s: 0, c: 0, a: 0 }, os: { s: 0, c: 0, a: 0 } } }, { pers: { panto: 8.24, pantoSd: 1.6, bvd: 12.73, bvdSd: 0.6, wrapOd: 6.1, wrapOs: 5.86 } });
  const t = C.recordToOMA(rec, {}, { withName: true });
  assert.equal(get(t, 'BVD'), '12.73;12.73'); assert.equal(get(t, 'PANTO'), '8.2;8.2'); assert.equal(get(t, 'ZTILT'), '6.1;5.9');
  assert.equal(get(t, 'SPH'), undefined, 'sin graduación no se envía Rx');
});

test('JSON: estructura con unidades, ± y posición de uso', () => {
  const rec = C.buildRecord(R, u, p, { pers: { panto: 8.2, pantoSd: 1.6, wrapOd: 6, wrapOs: 6 }, frameName: 'X' });
  const j = C.recordToJSON(rec, { name: 'Ana', ref: 'H-12' });
  assert.equal(j.format, 'dipfx-measurement'); assert.deepEqual(j.units, { length: 'mm', angle: 'deg' });
  assert.deepEqual(j.centration.pdFar, { value: 64.04, sd: 0.7 }); assert.equal(j.centration.monoNearOS, 30.5);
  assert.equal(j.frame.boxing.os.A, 52.9); assert.equal(j.positionOfWear.pantoscopicTilt.measured, true);
  assert.equal(j.positionOfWear.vertex.measured, false); assert.equal(j.person.ref, 'H-12');
  assert.doesNotThrow(() => JSON.stringify(j));
});
