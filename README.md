# DIPFx

Aplicación para la toma de medidas de ajuste de gafas.

## Medidas objetivo

| Medida | Descripción | Unidad |
|---|---|---|
| **DIP** (distancia interpupilar) | Distancia entre los centros pupilares, total y monocular (OD/OI) | mm |
| **Altura pupilar** | Distancia vertical desde el centro pupilar hasta el borde inferior del aro, por ojo | mm |
| **Ángulo pantoscópico (panto)** | Inclinación de la montura respecto al plano vertical | ° |
| **Ángulo de envolvente (wrap / facial)** | Curvatura horizontal de la montura respecto al plano frontal | ° |
| **Distancia de vértice posterior (DVP / BVD)** | Distancia entre la cara posterior de la lente y el vértice corneal | mm |

## Probar la webapp

La cámara solo funciona con **https** o en **localhost**:

- **En línea (GitHub Pages)**: el workflow `.github/workflows/pages.yml` pasa las pruebas y publica `index.html` en cada push a `main` (o a mano desde *Actions → Publicar en GitHub Pages → Run workflow*). Requiere activar una vez *Settings → Pages → Source: GitHub Actions*. La URL será `https://<usuario>.github.io/DipFx/`.
- **En local**: `npm run serve` y abrir http://localhost:8000.

---

## Medidor de DIP, alturas y montura

App web (un único `index.html`) que usa la webcam para medir:

- la **DIP de lejos** binocular y monocular, con corrección de la convergencia;
- las **alturas pupilares**;
- las **dimensiones boxing** de la montura (A, B, DBL, ED, descentramientos y diámetro mínimo de lente);
- el **tipo de montaje, el bisel y si hay plaquetas** (clasificación orientativa).

La captura es guiada: solo se dispara cuando la cabeza está recta y los ojos a la altura de la cámara.

### Uso rápido

```bash
npm run serve          # http://localhost:8000  (la cámara exige https o localhost)
```

1. Elige el método:
   - **Tarjeta**: una foto con gafas y una tarjeta estándar apoyada sobre la montura. Es el más preciso.
   - **Iris**: una foto sin gafas y otra con gafas. Después introduce la graduación y, si lo conoces, tu blanco‑blanco.
2. Desactiva el encuadre automático de la cámara (Center Stage, Windows Studio Effects).
3. Sigue las indicaciones de voz y de pantalla, y mira al objetivo de la cámara.
4. Revisa y ajusta los marcadores con la lupa.

### Desarrollo

```bash
pip install numpy pillow playwright && playwright install chromium   # para fixtures y e2e
npm run fixtures && npm test && npm run test:e2e
```

Lee [`CLAUDE.md`](CLAUDE.md) para la arquitectura y los convenios, [`docs/MODELO.md`](docs/MODELO.md) para las fórmulas y [`docs/HANDOFF.md`](docs/HANDOFF.md) para el historial de decisiones.

> Aviso: herramienta experimental, aún no validada con cámaras ni caras reales. No sustituye a una medición profesional.
