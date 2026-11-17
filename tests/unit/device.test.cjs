// Actitud del dispositivo (sensor de orientación) y colocación de las indicaciones junto a la cámara.
const test = require('node:test'), assert = require('node:assert/strict');
const C = require('../lib/extract-core.cjs');
const near = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg}: ${a} vs ${b}`);

test('actitud: vertical, tumbado, inclinado y girado en su plano', () => {
  let r = C.deviceAttitude(90, 0); near(r.tilt, 0, 1e-9, 'vertical'); near(r.roll, 0, 1e-9, 'vertical sin giro');
  r = C.deviceAttitude(0, 0); near(r.tilt, 90, 1e-9, 'tumbado boca arriba'); assert.equal(r.roll, null, 'tumbado: giro sin definir');
  r = C.deviceAttitude(80, 0); near(r.tilt, 10, 1e-9, 'parte de arriba hacia atrás 10°'); near(r.roll, 0, 1e-9, 'sin giro');
  r = C.deviceAttitude(100, 0); near(r.tilt, -10, 1e-9, 'parte de arriba hacia delante');
  // vertical y girado 10° en su plano: los navegadores dan gamma ≈ ±90 y beta = 90 ∓ 10
  r = C.deviceAttitude(80, -90); near(r.tilt, 0, 1e-9, 'girado: sigue vertical'); near(r.roll, 10, 1e-9, 'giro +10');
  r = C.deviceAttitude(80, 90); near(r.roll, -10, 1e-9, 'giro −10');
  // en horizontal (apaisado) y vertical: el giro se mide respecto al eje más próximo
  r = C.deviceAttitude(0, -90); near(r.tilt, 0, 1e-9, 'apaisado vertical'); near(r.roll, 0, 1e-9, 'apaisado sin giro');
  r = C.deviceAttitude(-5, -90); near(r.roll, 5, 1e-9, 'apaisado girado (misma convención de signo)');
});

test('indicaciones junto a la cámara: pegadas al borde y dentro de la pantalla', () => {
  let g = C.guidePlacement({ edge: 'top', pos: 0.5 }, 1440, 900, 360, 200);
  assert.deepEqual([g.left, g.top], [540, 8]); assert.deepEqual([g.cam.x, g.cam.y], [720, 0]);
  g = C.guidePlacement({ edge: 'top', pos: 0.02 }, 1440, 900, 360, 200); assert.equal(g.left, 8, 'no se sale por la izquierda');
  g = C.guidePlacement({ edge: 'left', pos: 0.5 }, 1180, 820, 300, 240); assert.deepEqual([g.left, g.top], [8, 290]); assert.equal(g.cam.x, 0);
  g = C.guidePlacement({ edge: 'right', pos: 1 }, 1180, 820, 300, 240); assert.deepEqual([g.left, g.top], [872, 572]);
  g = C.guidePlacement({ edge: 'bottom', pos: 0.5 }, 800, 1280, 300, 240); assert.equal(g.top, 1032); assert.equal(g.cam.y, 1280);
  g = C.guidePlacement(null, 1000, 800, 200, 100); assert.deepEqual([g.left, g.top], [400, 8], 'por defecto, arriba en el centro');
});
