// Registro de actividad: recorte, formato y resumen de errores
const test = require('node:test'), assert = require('node:assert/strict');
const C = require('../lib/extract-core.cjs');
test('logPush conserva solo las últimas entradas', () => {
  const a = []; for (let i = 0; i < 12; i++) C.logPush(a, { ev: 'e' + i }, 5);
  assert.equal(a.length, 5); assert.equal(a[0].ev, 'e7'); assert.equal(a[4].ev, 'e11');
});
test('logMsg resume errores, objetos y textos largos', () => {
  const e = new Error('fallo de prueba'); const m = C.logMsg(e);
  assert.match(m, /^Error: fallo de prueba/);
  assert.equal(C.logMsg({ a: 1.23456, b: [2] }), '{"a":1.235,"b":[2]}');
  assert.equal(C.logMsg(null), '');
  const long = C.logMsg('x'.repeat(1000), 50); assert.equal(long.length, 51); assert.ok(long.endsWith('…'));
  const circ = {}; circ.self = circ; assert.equal(typeof C.logMsg(circ), 'string');
});
test('logToText pone la cabecera y una línea por entrada', () => {
  const t = C.logToText([{ t: '2026-11-18T10:00:00.000Z', lvl: 'error', ev: 'db.open', msg: 'blocked' }, { t: '2026-11-18T10:00:01.000Z', lvl: 'info', ev: 'view' }], { version: '0.8.1', data: { people: 3 } });
  const L = t.split('\n');
  assert.equal(L[1], 'version: 0.8.1'); assert.equal(L[2], 'data: {"people":3}');
  assert.ok(t.includes('2026-11-18T10:00:00.000Z ERROR db.open — blocked'));
  assert.ok(t.includes('2026-11-18T10:00:01.000Z INFO  view\n'));
});
