// Personalización: foto de perfil (panto y vértice), plantilla del galbe y CSV en inglés.
const test = require('node:test'), assert = require('node:assert/strict');
const C = require('../lib/extract-core.cjs');
const near = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg}: ${a} vs ${b}`);
const D = Math.PI / 180;

// Escena de perfil: frente de 44 mm de alto inclinado 'panto' (borde inferior hacia la cara), escala 0,25 mm/px,
// córnea a 'bvd' mm por detrás de la cara posterior de la lente, a la altura del centro.
function scene(panto, bvd, face) {
  const s = 0.25, H = 44, T = { x: 800, y: 300 }, seg = H / s;
  const B = { x: T.x + face * seg * Math.sin(panto * D), y: T.y + seg * Math.cos(panto * D) };
  const P = { x: (T.x + B.x) / 2 + face * 3 / s, y: (T.y + B.y) / 2 }, Cc = { x: P.x + face * bvd / s, y: P.y };
  return { q: { T, B, C: Cc, P }, H, s };
}
for (const face of [1, -1]) for (const [panto, bvd] of [[0, 12], [8, 13.5], [-3, 10]]) {
  test(`perfil: panto ${panto}°, vértice ${bvd} mm, cara hacia ${face > 0 ? 'la derecha' : 'la izquierda'}`, () => {
    const { q, H } = scene(panto, bvd, face);
    const r = C.profileMeasure(q, H);
    near(r.panto, panto, 1e-9, 'panto'); near(r.bvd, bvd, 1e-9, 'vértice'); near(r.s, 0.25, 1e-12, 'escala');
    // altura tomada de la foto frontal (proyectada): H·cos(panto)
    const r2 = C.profileMeasure(q, H * Math.cos(panto * D), { projected: true });
    near(r2.bvd, bvd, 1e-9, 'vértice con altura proyectada');
    assert.ok(r.sdPanto >= 1.5 && r.sdPanto < 2, `± panto ${r.sdPanto}`); assert.ok(r.sdBvd > 0.1 && r.sdBvd < 1, `± vértice ${r.sdBvd}`);
  });
}
test('perfil: datos que no sirven', () => {
  assert.equal(C.profileMeasure({ T: { x: 1, y: 1 }, B: { x: 1, y: 1 }, C: { x: 5, y: 1 }, P: { x: 3, y: 1 } }, 44), null);
  assert.equal(C.profileMeasure(scene(5, 12, 1).q, 0), null);
});

test('galbe: montura plana, simétrica, asimétrica y girada en la pantalla', () => {
  // y hacia abajo = hacia las varillas (la cara)
  const pts = (wR, wL, rot = 0) => {
    const R = (p) => ({ x: 600 + p.x * Math.cos(rot * D) - p.y * Math.sin(rot * D), y: 400 + p.x * Math.sin(rot * D) + p.y * Math.cos(rot * D) });
    return { nL: R({ x: -40, y: 0 }), tL: R({ x: -40 - 200 * Math.cos(wL * D), y: 200 * Math.sin(wL * D) }), nR: R({ x: 40, y: 0 }), tR: R({ x: 40 + 200 * Math.cos(wR * D), y: 200 * Math.sin(wR * D) }) };
  };
  let w = C.wrapFromPoints(pts(0, 0)); near(w.od, 0, 1e-9, 'plana OD'); near(w.os, 0, 1e-9, 'plana OI');
  w = C.wrapFromPoints(pts(6, 6)); near(w.od, 6, 1e-9, 'OD'); near(w.os, 6, 1e-9, 'OI'); near(w.mean, 6, 1e-9, 'media');
  // asimétrica: el plano del frente (por los centros de las lentes) gira; la media no cambia, el reparto sí
  w = C.wrapFromPoints(pts(12, 4)); near(w.mean, 8, 1e-9, 'media asimétrica'); assert.ok(w.od > w.os, 'el lado más doblado tiene más galbe');
  w = C.wrapFromPoints(pts(6, 6, 7)); near(w.od, 6, 1e-9, 'montura girada 7° en la pantalla');
  w = C.wrapFromPoints(pts(-3, -3)); near(w.mean, -3, 1e-9, 'galbe inverso');
});

test('CSV en inglés: coma como separador, punto decimal, cabeceras y personalización', () => {
  const r = C.buildRecord({ mode: 'card', pdFar: 63.25, flags: [], flagsEn: [] }, {}, { rx: { od: { s: 0, c: 0, a: 0 }, os: { s: 0, c: 0, a: 0 } }, tpl: {} }, { personId: 'p', pers: { panto: 8.2, wrapOd: 5.1, wrapOs: 4.9 }, notes: 'a, b' });
  const [h, v] = C.recordsToCSV([{ id: 'p', name: 'Ann' }], [r], 'en').split('\r\n');
  const H = h.split(','); assert.equal(H[0], 'Person'); assert.ok(H.includes('Pantoscopic tilt'));
  assert.ok(v.includes(',63.25,'), v); assert.ok(v.includes(',8.2,5.1,4.9,'), v); assert.ok(v.endsWith(',"a, b"'), v);
  const es = C.recordsToCSV([{ id: 'p', name: 'Ann' }], [r]).split('\r\n')[1];
  assert.ok(es.includes(';63,25;') && es.includes(';8,2;5,1;4,9;'), es);
});
