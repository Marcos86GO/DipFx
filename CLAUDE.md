# CLAUDE.md — Medidor de DIP, alturas y montura

Contexto para Claude Code. Léelo entero antes de tocar el código. El historial de decisiones está en `docs/HANDOFF.md` y el modelo físico, con sus fórmulas, en `docs/MODELO.md`.

## Qué es

App web de una sola página (`index.html`, sin build) que, con la webcam del portátil o del móvil:

1. **Identifica el dispositivo y la cámara.** Usa el nombre de la cámara, su resolución y su ID USB, y busca el FOV en una pequeña base de datos. El navegador **no** puede leer el modelo del portátil en escritorio; en Mac se deduce de forma aproximada por la resolución de pantalla.
2. **Guía la postura en vivo** con iconos, texto y voz, y **solo dispara cuando todo cuadra**: (en tablet o móvil) dispositivo vertical y sin girar respecto al suelo, distancia, centrado, ojos a la altura de la cámara, giro, cabeceo, ladeo, ojos abiertos, quietud y (en el método tarjeta) tarjeta visible. Después pide **mirar a la cámara**, espera a que la mirada llegue y se asiente (≥ 0,9 s desde el aviso y ≥ 0,7 s con la mirada correcta; a los 6 s dispara igualmente y lo avisa) y entonces dispara, sin cuenta atrás en pantalla.
   - **¿Quién hace la foto?** (`S.who`): `selfie` (la propia persona) u `operator` (el óptico, con la cámara trasera). En selfie, las indicaciones y una vista previa pequeña en espejo se colocan **pegadas al borde de la pantalla donde está la cámara** (`camPos`, `guidePlacement`), y en la fase final se oculta la vista previa y una flecha señala la cámara. En modo óptico, vista previa grande sin espejo, una sola indicación muy visible para el óptico («Sube la tablet», «Pide que gire la cabeza…») y un nivel tipo horizonte artificial.
   - La **posición de la cámara** está en Ajustes → Cámara. Si no está indicada, se pregunta una sola vez, en la primera medida selfie del dispositivo, y se guarda allí, por orientación (`screen.orientation.type`; en una tablet, la primera vez que se use en vertical y la primera en horizontal), en `localStorage` `dipapp.campos`. Hace una **ráfaga de 8 fotogramas**, los registra con precisión subpíxel contra el más nítido y mejor alineado, y los **promedia remuestreados ×2** en la zona de las gafas. Si hay demasiado movimiento, usa el mejor fotograma. En la medición se puede elegir entre el promedio y el mejor fotograma.
3. **Mide**:
   - DIP de lejos binocular y monoculares, con corrección de la convergencia hacia la cámara.
   - DIP de cerca.
   - Alturas pupilares.
   - Dimensiones boxing de la montura: A, B, DBL, distancia entre centros, ED, descentramientos y diámetro mínimo de lente.
   - Tipo de montaje, bisel y si hay plaquetas, como clasificación heurística.
4. Todo marcador es **editable a mano**, con lupa y flechas del teclado. Los resultados llevan su **incertidumbre (±)**, calculada por perturbación.
5. **Guarda un histórico por persona**: fichas de personas (nombre, referencia, fecha de nacimiento, notas), cada una con todas sus medidas (valores, ±, montura, graduación, parámetros y, opcionalmente, la foto con las marcas). Muestra la media y la dispersión de varias medidas. Todo queda **solo en el navegador** (IndexedDB), con copia de seguridad JSON, importación y exportación CSV.

**Interfaz**: logo SVG propio (cabecera y favicon, en línea). Cabecera con «Personas», «Ajustes» y «+ Nueva medida». Una medida es un asistente por pasos: Persona → Montura (solo método montura) → Foto → Revisar y guardar. Los detalles técnicos y los parámetros avanzados van plegados. La calibración de la pantalla y la ficha de persona son ventanas modales. En ordenador, el paso Montura ocupa toda la pantalla (intenta ponerla en pantalla completa) con la plantilla **pegada al borde inferior**, para apoyar la montura en la base del teclado; dibuja detrás una silueta de la montura que sigue las líneas marcadas y el tipo elegido, y permite indicar **tipo de montaje, material y plaquetas**.

Usuario y destinatario: óptico‑optometrista (España/EE. UU.) que dirige un equipo técnico en una empresa de diseños de lentes freeform. **Interfaz y comentarios en español.** El rigor óptico importa más que lo vistoso.

## Tres métodos

| Método | Fotos | Escala absoluta | Notas |
|---|---|---|---|
| `frame` (por defecto) | Montura medida sobre una plantilla a escala real en la pantalla + 1 foto con gafas, sin tarjeta | ancho exterior del frente y, si se marcan, A + DBL (distancia entre centros de las cajas) | Necesita la pantalla calibrada una vez (o medidas escritas a mano, con regla o trazador). |
| `card` | 1 con gafas + tarjeta ID‑1 (85,60 mm) apoyada sobre la montura | tarjeta | El más preciso: DIP ±0,7 mm típico. |
| `iris` | 1 **sin** gafas (N) + 1 **con** gafas (G), a la misma distancia | blanco‑blanco (HVID): 11,7 ± 0,45 mm o el valor del usuario | La DIP sale de N. El vértice se deduce del cambio de tamaño del iris a través de cada lente, con la Rx del usuario. Monoculares, alturas y montura salen de G. |

## Cómo ejecutar

- La cámara exige **https o localhost**: `npm run serve` y abrir http://localhost:8000. Para producción, GitHub Pages.
- **No sirve como artefacto de claude.ai**: el iframe aislado bloquea la cámara.
- Dependencias externas en tiempo de ejecución (CDN, versión fijada):
  - `@mediapipe/tasks-vision@1.2.3` (jsdelivr): FaceLandmarker con 478 puntos, blendshapes y matriz de transformación facial.
  - Modelo: `storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task`.
- Modo sin cámara: subir fotos ya hechas («Foto SIN gafas» / «Foto CON gafas»). Es útil para depurar con fotos reales.

## Pruebas

```bash
npm run fixtures     # genera imágenes sintéticas en tests/fixtures/out/ (python3, numpy, Pillow; ffmpeg opcional)
npm test             # 38 pruebas unitarias con node:test sobre la sección CORE
npm run test:e2e     # Chrome sin cabeza: cámara simulada + detector facial simulado (playwright; CHROME_PATH opcional)
```

- `tests/lib/extract-core.cjs` extrae la sección entre `// ==CORE START==` y `// ==CORE END==` de `index.html` y exporta todo `function` y `const` de nivel superior. **No rompas esos marcadores** y mantén el CORE **sin DOM**.
- Las pruebas e2e cubren el método montura en vivo (calibración de pantalla, plantilla a pantalla completa pegada al borde inferior, arrastre de líneas y de la línea de centros, tipo, material y plaquetas, ráfaga apilada, bordes exteriores, cambio a mejor fotograma), el histórico (crear persona, dos medidas, resumen, detalle con foto, persistencia tras recargar, CSV), indicaciones junto a la cámara en selfie y fase final «Mira a la cámara», pregunta de la posición de la cámara si no se conoce, modo óptico sin espejo, el método tarjeta en vivo y el método iris con fotos subidas guardado en una persona nueva.
- Las pruebas e2e sustituyen MediaPipe por `tests/fixtures/out/fake_vision.mjs`, que devuelve puntos coherentes con cada imagen sintética. El detector distingue la imagen por el píxel marcador (1,1): 10 = sin gafas, 240 = con gafas, 128 = tarjeta.
- Las escenas sintéticas se proyectan con el mismo modelo físico. Por eso validan la coherencia interna y los algoritmos de visión, **no** la exactitud con caras reales. **Nunca se ha probado con una cámara y una cara reales.**

## Arquitectura de `index.html`

- **CORE** (funciones puras, probadas):
  - Geometría: `focalFromDfov`, `rcFromLens` (centro de rotación + Prentice), `cardWidthPx`, `measureCap`, `solveAll`, `solveWithUnc`.
  - Método montura: `tplFromLines`, `tplDNC`, `detectOuterEdge`, `frameScaleZ`.
  - Ráfaga: `nccAt`, `registerShift` (búsqueda entera por NCC + Lucas–Kanade), `similarity2`, `stackRGBA`.
  - Dispositivo: `deviceAttitude` (inclinación y giro respecto al suelo a partir de beta/gamma), `guidePlacement` (indicaciones junto a la cámara).
  - Histórico: `buildRecord` (registro que se guarda, con `material` y `pads`), `summarizeHistory`, `recordsToCSV` (`;` y coma decimal), `normalizeImport`, `mountingFrom` (tipo + material → montaje del cálculo), `MATERIAL_LABEL`.
  - Óptica: `lensData`, `apparentMag` (lente gruesa), `solveVertexH`, `fuseVertex`.
  - Visión: `detectCard`, `refineEdge`, `refineIris` (ajuste de circunferencia de Kåsa sobre bordes laterales), `detectLensContour` (programación dinámica polar), `rimAnalysis`, `classifyFrame`, `padAnalysis`, `featureScale`.
- **App**:
  - Navegación: `go(vista)` entre `viewPeople`, `viewPerson`, `viewRecord`, `viewWizard` y `viewSettings`. Asistente: `startMeasure(personId)`, `showStep('person'|'frame'|'photo'|'review')`, estado en `wiz = {person, step, savedId}`.
  - Datos: `DB` (IndexedDB `dipfx` v1; almacenes `people` {id, name, ref, birth, notes, created, updated} y `measures` (registro de `buildRecord`, índice `personId`, `image` como Blob JPEG)). `renderPeople`, `renderPerson`, `renderRecord`, `saveMeasure`, `snapshotBlob`, `exportJson`, `exportCsv`, `importJson`. Preferencias (método, exigencia, voz) en `localStorage` `dipapp.prefs`.
  - Calibración de la pantalla (`scrCal`, `openScr`; clave `dipapp.screen`) y plantilla de la montura (`openTpl`, `tplDraw`, `tplSilhouette`, `tplLeave`; clave `dipapp.tpl` con líneas, altura de la línea de centros `yMm` desde el borde inferior, tipo, material y plaquetas). Al confirmar, el tipo y el material pasan a `mountSel` (vía `mountingFrom`), `matSel` y `padSel` como elección manual.
  - Detección del dispositivo y base de datos de FOV (`CAM_DB`).
  - Carga de MediaPipe y `analyzeFace`.
  - Bucle en vivo: `evaluate` (comprobaciones con mensaje e icono según selfie u óptico) → `guidance` (fases `pos` → `look`) → `captureBurst` → `stackBurst`. Indicaciones: `showGuide`, `icon`, `placeGuide`, `enterLook`, `updateLevel`. Capa de la foto a pantalla completa (`#livePanel.selfie` / `.operator`); `fsEnter`/`fsExit`.
  - `analyzeCapture` → `frameDetect` → (método montura) `outerDetect`.
  - Interfaz de medición: `handles`, `moveHandle`, `drawScene`, `recompute` (cifras clave en `#results`; geometría y afinado en `#techDetails`). El editor muestra por defecto la zona de las gafas (`viewRect`, `cap.vr`); `cap.full` muestra la foto completa.
- Modelo de medición: `M = { mode, caps: [N?, G] }`. Cada `cap` contiene:
  - `cv` (lienzo), `W`, `H`, `f` (focal en px), `ss` (remuestreo de la imagen: 2 si es el promedio ×2 de la ráfaga, 1 si no), `burst` (`{stack, best, info}`, o null si es una foto subida).
  - `iris.{od,os}.{x,y,r}`, `lmk` (478 puntos en px), `pose`.
  - Solo en N: `bridge`.
  - Solo en tarjeta: `card.{L,R}`.
  - Solo en G: `box.{od,os}.{n,t,top,bot}`, `tau`, `contour`, `box0`, `contourOK`, `frameAuto`.
  - Solo en el método montura: `outer.{od,os}` (coordenada u del borde exterior, a la altura del centro de cada caja), `outer0`, `outerAuto`.
- Parámetros (`params()`): además de los ópticos, `tpl = {W, Aod, Aos, DBL}` (mm, de la plantilla) y `outerOff` (mm que los bordes exteriores quedan detrás del plano de la lente; vacío = se deduce del galbe).

## Convenios (invariantes: si los cambias, rompes resultados en silencio)

- **Coordenadas de píxel**: el píxel *i* está en la coordenada *i*. Los puntos de MediaPipe se convierten con `x*W − 0.5`. El punto principal es `((W−1)/2, (H−1)/2)`.
- **Remuestreo ×up** (ráfaga apilada): el píxel de salida *j* está en la coordenada original `(j + 0,5)/up − 0,5`. Es el mismo convenio que usa `drawImage` al ampliar, así que el punto principal y la focal (`focalFromDfov` con el nuevo W) siguen siendo coherentes. Los errores de localización del ± (`solveWithUnc`) se multiplican por `cap.ss` para expresarlos en píxeles de la cámara. Entre dos capturas con distinto `ss`, `k` se calcula en unidades angulares (`N.f / G.f`).
- **Plantilla**: la montura se apoya con el frente contra la pantalla y las varillas hacia el usuario, así que la **lente derecha (OD) queda a la derecha** de la pantalla. Las medidas de la plantilla son proyecciones frontales, igual que la foto. Calibración de la pantalla en px CSS por mm; se invalida si cambian `screen.width/height` o `devicePixelRatio` (zoom del navegador).
- **OD = ojo derecho del sujeto = izquierda de la imagen sin espejo.** La vista en vivo se muestra en espejo (CSS); las fotos de medición, sin espejo.
- **Recuadro de la lente** en coordenadas (u, v) relativas al punto principal y giradas `−tau`, donde `tau` es la inclinación de la montura (recta entre centroides de las lentes). Lados: `n` nasal, `t` temporal, `top` superior, `bot` inferior. En OD el lado nasal tiene la u mayor; en OI, la menor.
- **Actitud del dispositivo** (`deviceAttitude`): vertical del mundo en ejes del dispositivo `u = (−cos β sen γ, sen β, cos β cos γ)`. `tilt > 0`: la pantalla mira hacia arriba (se corrige inclinando la parte de arriba hacia quien la mira). `roll > 0`: el dispositivo está girado en sentido antihorario visto de frente (se corrige en sentido horario); se mide respecto al eje más próximo, así que vale en vertical y en horizontal. Tolerancias: 3° de inclinación y 1,5° de giro.
- **Direcciones en las indicaciones**: en selfie, la imagen se ve en espejo y «tu derecha» está a la derecha de la pantalla. En modo óptico, la imagen va sin espejo, así que la derecha de la persona queda a la izquierda de la pantalla. Los iconos de giro y desplazamiento siguen esa vista.
- **Signos de postura**: `yaw > 0` significa cabeza girada hacia **su** izquierda y `pitch > 0`, barbilla arriba. Se verifican en tiempo de ejecución contra indicadores 2D (`updateConvention`), porque el orden de la matriz de MediaPipe no está documentado. Se detecta por la posición de la traslación.
- Constantes ópticas:
  - Córnea → centro de rotación `CR = 13,5 mm`.
  - Córnea → plano del limbo/pupila `E_L = 3,0 mm`.
  - HVID medio `11,7 mm`.
  - Tarjeta `85,60 mm`.
- **Vértice** (`pVertex`) = córnea → cara posterior de la lente. El plano de medida es la mitad del espesor de la lente.
- **Tarjeta**: se asume 1,5 mm por delante de ese plano (`pCardOff`).
- **Bordes exteriores de la montura** (método montura): se miden a la altura del centro de cada caja y se asumen `(W − DNC)/2 · sen(galbe)` mm por detrás del plano de la lente (`pOuterOff` lo sustituye).
- **Ranura o bisel** (0,5 mm por defecto): se suma según el montaje. En aro completo, a los 4 lados; en nylon, solo arriba; al aire, nada.

## Limitaciones conocidas (sé honesto con ellas en la interfaz)

- **FOV**:
  - Apple no publica el FOV de las cámaras de sus portátiles; la mayoría de fabricantes tampoco.
  - Un error del 15 % en el FOV afecta sobre todo a la corrección de convergencia: unos ±0,6 mm en la DIP.
  - Calibración opcional (método tarjeta): medir con cinta la distancia de la cámara a la tarjeta en una foto.
- **Método iris**:
  - La escala depende del HVID: ±2,5 mm en la DIP con el valor medio, ±0,8 mm con el valor medido del usuario.
  - El vértice solo se puede deducir de forma útil con |F| ≥ ~3 D. Con −1 D el margen es de ±8 mm, y por debajo de 0,5 D no se calcula. Si la medida es floja, se fusiona con el valor previo de 12 ± 2,5 mm.
- **Postura**: el giro residual mueve las monoculares unos 0,45 mm por grado y el cabeceo, las alturas en la misma proporción. Se incluye en el ±.
- **Monturas**:
  - En **nylon**, el borde inferior no se ve: la app lo estima como `top + 0,72·A` y pide ajustarlo.
  - En monturas **al aire**, puede no encontrar el contorno y usar un recuadro típico (52□18, B 38).
- **Clasificación** de montaje, material y plaquetas: umbrales heurísticos sin calibrar con imágenes reales.
- **Método montura**:
  - La escala depende de la calibración de la pantalla (regla sobre la pantalla) y de cómo se marquen los bordes en la plantilla (paralaje: mirar cada línea de frente). Estimado ±0,5 mm por medida de la plantilla.
  - El borde exterior en la foto se pierde con monturas transparentes, finas o contra el pelo: el usuario lo ajusta a mano. En monturas al aire no hay borde exterior propio.
  - Con galbe, los bordes exteriores quedan por detrás del plano de la lente: si no se introduce el galbe, ±1,5 mm de profundidad en el ±.
  - Si se marcan las dos referencias (ancho exterior y cajas), se avisa cuando discrepan más de 2,5 σ.
- **Ráfaga**: el registro es una semejanza (dos zonas, una por ojo). Si la cabeza gira o la cara cambia de expresión entre fotogramas, se descartan (NCC < 0,9, escala > 2 %, giro > 1°). El remuestreo ×2 mejora el ruido y la nitidez de los bordes solo si hay desplazamientos subpíxel entre fotogramas; no crea detalle que la óptica no resuelva.
- **Sensores de orientación y modo óptico**: sin probar en una tablet real. Hay que validar el signo del giro y de la inclinación (`deviceAttitude`) en iPad y Android, y que la cámara trasera se elige bien. El FOV de las cámaras traseras de tablets no está en `CAM_DB` (se usa el genérico estimado).
- **Mirada**: la espera de la fase final depende del umbral de mirada (`gazeOk`), que no está validado con caras reales; si no se confirma en 6 s, se dispara igualmente y se avisa en la revisión.
- **Pupila**: se usa el centro del iris (circunferencia ajustada), no el centro pupilar ni el reflejo corneal.
- **Histórico**: vive en el navegador de un dispositivo. No se sincroniza; si se borran los datos del sitio, se pierde. Solo la copia de seguridad JSON lo protege. Las fotos de caras son datos personales: se guardan solo si se marca la casilla y nunca salen del dispositivo salvo en la copia con fotos.

## Prioridades siguientes

1. **Validación con cámara real** (lo más urgente):
   - En tablet: signos de `deviceAttitude`, cámara trasera en modo óptico, colocación de las indicaciones junto a la cámara en vertical y en horizontal.
   - Signos y umbrales de postura, umbral de mirada (`version < 0.07`, `lookUp/lookDown < 0.45`).
   - Detección de la tarjeta con dedos y pelo.
   - Contorno de lente con reflejos, cejas y pestañas.
   - Umbrales de `classifyFrame` (`T = max(14, 0.15·spread)`) y de `padAnalysis`.
2. **Banco de pruebas con fotos reales** etiquetadas con medidas de referencia (pupilómetro, trazador). Hacer un script que lo ejecute por la vía de «subir fotos» y mida el error.
3. **Modularizar** sin perder la entrega en un solo archivo. Por ejemplo, `src/core/*.js` y `src/app/*.js` con un empaquetado mínimo (esbuild) que genere `dist/index.html`. Actualizar `extract-core.cjs` en consecuencia.
4. **Mejoras ópticas**:
   - Centro pupilar o reflejo corneal en lugar del centro del iris.
   - Ángulo pantoscópico y galbe estimados (hoy son entradas manuales).
   - Vértice también en el método tarjeta (segunda foto sin gafas y con tarjeta en la frente).
5. **Mejoras de producto**:
   - Exportar una medida a PDF (informe para el cliente o el laboratorio).
   - Reabrir una medida guardada para reajustar sus marcadores (hoy se guarda la foto con las marcas, no el estado editable).
   - Sincronización entre dispositivos (necesitaría un servidor; cuidado con la protección de datos).
   - Edición del contorno completo para el ED.

## Normas de trabajo en este repo

- Mantén `index.html` autocontenido y funcionando sin build hasta que se acuerde modularizar.
- Toda función nueva de cálculo va en CORE, sin DOM y con su prueba en `tests/unit/`.
- Antes de dar algo por terminado: `npm test`, y si tocas el flujo o la interfaz, `npm run test:e2e`.
- No inventes especificaciones de FOV: si añades una cámara a `CAM_DB`, cita la fuente en `src` y usa `kind: 'spec'` solo si viene de una ficha técnica.
