// Histórico: registro de una medida, resumen de varias, CSV y validación de copias de seguridad.
const test = require('node:test'), assert = require('node:assert/strict');
const C = require('../lib/extract-core.cjs');

const R = { mode: 'frame', pdFar: 64.0123, monoOD: 31.504, monoOS: 32.5, hOD: 22.46, hOS: 22.6, pdNear: 60.3, DBL: 17.1, DNC: 70.2, Z: 421.7, vertex: 12, mounting: 'full-acetate', flags: [],
  frame: { od: { A: 53.05, B: 39.3, ED: 58.8, decH: 3.5, decV: 3, MBS: 68 }, os: { A: 53.1, B: 39.3, ED: 58.9, decH: 2.5, decV: 3, MBS: 66 } } };
const u = { pdFar: 0.712, monoOD: 0.4, A_od: 0.35 };
const p = { rx: { od: { s: -2, c: -0.5, a: 180 }, os: { s: -1.75, c: 0, a: 0 } }, index: 1.6, vertex: 12, wrap: 5, panto: 8, groove: 0.5, nearDist: 400, tpl: { W: 131, Aod: 52, Aos: NaN, DBL: 18 }, hvidUser: false, hvid: { od: 11.7, os: 11.7 } };

test('registro: valores redondeados, montura, parámetros y plantilla limpia', () => {
  const r = C.buildRecord(R, u, p, { id: 'm1', personId: 'p1', frameName: 'Acetato 52□18', date: '2026-11-18T10:00:00.000Z' });
  assert.equal(r.values.pdFar, 64.01); assert.equal(r.values.monoOD, 31.5); assert.equal(r.unc.pdFar, 0.71); assert.equal(r.unc.A_od, 0.35);
  assert.equal(r.frame.od.A, 53.05); assert.equal(r.method, 'frame'); assert.equal(r.personId, 'p1');
  assert.deepEqual(r.params.tpl, { W: 131, Aod: 52, DBL: 18 }, 'los valores no válidos de la plantilla se descartan');
  assert.equal(r.params.rx.od.c, -0.5); assert.equal(r.params.hvid, null);
  const r2 = C.buildRecord({ mode: 'card', pdFar: 63 }, {}, { ...p, tpl: {} });
  assert.equal(r2.frame, null); assert.equal(r2.params.tpl, null); assert.equal(r2.values.monoOD, null);
});

test('resumen de varias medidas: media y desviación típica muestral', () => {
  const recs = [64.0, 64.4, 63.8].map((d, i) => ({ values: { pdFar: d, monoOD: 31.5 + i * 0.1, monoOS: null } }));
  const s = C.summarizeHistory(recs);
  assert.equal(s.pdFar.n, 3); assert.ok(Math.abs(s.pdFar.mean - 64.0667) < 1e-3);
  assert.ok(Math.abs(s.pdFar.sd - 0.30551) < 1e-4); assert.equal(s.pdFar.min, 63.8); assert.equal(s.pdFar.max, 64.4);
  assert.equal(s.monoOS, undefined, 'sin datos no hay resumen');
  assert.equal(C.summarizeHistory([recs[0]]).pdFar.sd, null, 'con una sola medida no hay dispersión');
});

test('CSV: separador «;», coma decimal, comillas y orden por persona y fecha', () => {
  const people = [{ id: 'b', name: 'Zoe; "Z"', ref: '' }, { id: 'a', name: 'Ana', ref: 'H-12' }];
  const ms = [C.buildRecord(R, u, p, { id: '1', personId: 'b', date: '2026-01-02T09:00:00Z' }), C.buildRecord(R, u, p, { id: '2', personId: 'a', date: '2026-03-01T09:00:00Z' }), C.buildRecord({ ...R, pdFar: 63.5 }, u, p, { id: '3', personId: 'a', date: '2026-02-01T09:00:00Z' })];
  const lines = C.recordsToCSV(people, ms).split('\r\n');
  assert.equal(lines.length, 4);
  assert.ok(lines[0].startsWith('Persona;Referencia;Fecha;Método;Montura;DIP lejos'));
  assert.ok(lines[1].startsWith('Ana;H-12;2026-02-01 09:00;montura;;63,5;0,71;31,5;'), lines[1]);
  assert.ok(lines[2].includes(';64,01;'));
  assert.ok(lines[3].startsWith('"Zoe; ""Z"""'), lines[3]);
});

test('importación: valida la estructura y descarta entradas incompletas', () => {
  assert.equal(C.normalizeImport({ people: [] }).ok, false);
  const r = C.normalizeImport({ app: 'dipfx', people: [{ id: 'a', name: 'Ana' }, { id: 'x', name: ' ' }, { name: 'sin id' }], measures: [{ id: 'm', personId: 'a', values: {} }, { id: 'n', values: {} }] });
  assert.ok(r.ok); assert.equal(r.people.length, 1); assert.equal(r.measures.length, 1); assert.equal(r.skipped, 3);
});
