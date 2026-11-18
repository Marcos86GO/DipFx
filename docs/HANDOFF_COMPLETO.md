# DipFx — Traspaso completo del proyecto

Documento autocontenido para continuar el trabajo en otro proyecto o con otro equipo. Resume qué es la app, cómo está hecha, las decisiones tomadas y por qué, los formatos de datos, cómo se prueba, qué falta y las lecciones aprendidas.

Fecha: 18 nov 2026. Versión publicada: **0.8.1**.

---

## 1. Resumen en un minuto

**DipFx** es una app web de una sola página (`index.html`, unas 4500 líneas, sin build) que mide parámetros de centrado de lentes con la cámara del portátil, la tablet o el móvil:

- DIP de lejos y de cerca, monoculares y alturas pupilares, con corrección de la convergencia hacia la cámara y del efecto prismático de la lente.
- Dimensiones boxing de la montura: A, B, DBL, DNC, ED, descentramientos y diámetro mínimo.
- Tipo de montaje, bisel y plaquetas, por clasificación heurística.
- Opcionalmente, ángulo pantoscópico, distancia al vértice (foto de perfil) y galbe (plantilla en la pantalla).
- Cada resultado lleva su **incertidumbre (±)**.

La app guía la postura en vivo con iconos, texto y voz, y **solo dispara cuando todo cuadra**. Toma una ráfaga de 8 fotogramas y los promedia con precisión subpíxel. Guarda un **histórico por persona** en el navegador (IndexedDB). Las medidas se pueden **editar**, **exportar** (JSON y OMA/DCS) y **enviar al laboratorio** (carpeta vigilada o pasarela HTTP). Está en **español e inglés** y tiene un **registro de actividad** para diagnosticar problemas.

- Repositorio: `github.com/Marcos86GO/DipFx`. Rama `main` = producción; rama de desarrollo usada: `claude/ecstatic-allen-g14kxo`.
- Producción: GitHub Pages, `https://marcos86go.github.io/DipFx/` (desde `main`, raíz).
- Estado de validación: **todo probado con escenas sintéticas; nunca con una cámara y una cara reales.** Es lo más urgente.

## 2. Usuario y contexto

- Óptico‑optometrista formado en España, que trabaja en España y EE. UU. Dirige el equipo técnico de una empresa de **diseños de lentes freeform**.
- Tiene otra app basada en una pinza (clip) para medidas de centrado a partir de fotos. En ella echaba en falta detectar y compensar los giros de cabeza; DipFx nació para atacar ese problema.
- **Interfaz y comentarios del código en español** (inglés como opción de la interfaz). **El rigor óptico importa más que lo vistoso.** Hay que ser honesto en la interfaz con las limitaciones.
- Forma de trabajar: pide mejoras por lotes y que se publiquen en `main` cuando están listas («publícalo en main»). Espera que todo siga funcionando tras cada actualización y que **no se pierdan nunca las personas ni las medidas guardadas** (ver §13).

## 3. Historia del desarrollo (por versiones)

| Commit | Qué se añadió |
|---|---|
| `1bbf93f` | Código inicial: métodos tarjeta e iris, guiado de postura, voz, base de datos de FOV, Pages. |
| `33f2df6` | **Método montura**: calibración de la pantalla una vez y plantilla a escala real; **ráfaga apilada** (8 fotogramas, registro subpíxel, promedio ×2); bordes exteriores del aro. |
| `039bcb1` | **Histórico** de personas y medidas (IndexedDB), copia de seguridad JSON, CSV e interfaz guiada por pasos. |
| `8e5c8bb` | Logo SVG; plantilla a pantalla completa pegada al borde inferior (apoyar la montura en la base del teclado), silueta de la montura; tipo de montaje, material y plaquetas. |
| `0280d79` | **Selfie u óptico**: indicaciones junto a la cámara, fase final «Mira a la cámara», modo óptico con cámara trasera y nivel tipo horizonte; tablet vertical y sin girar. |
| `aee9dd0` | Posición de la cámara en Ajustes; solo se pregunta en la primera medida selfie. |
| `305bd33` | **Personalización**: foto de perfil (panto y vértice) y plantilla del galbe, activables en Ajustes. |
| `acdb590` | **Inglés** con selector de idioma. |
| `8769e86` (0.8.0) | **Editar** medidas guardadas; **exportar JSON y OMA (DCS)**; **envío al LMS** (carpeta vigilada o HTTP). |
| `9c393cd` (0.8.1) | Arreglo de la base de datos (incidente, §13); **registro de actividad**; barra de botones fija arriba en una medida. |

Ideas evaluadas y **descartadas** (para no repetir el análisis):

- Cámara de infrarrojos del portátil: no es accesible desde el navegador y tiene poca resolución.
- Estéreo con dos cámaras: la separación entre cámaras es de 1–2 cm y no están calibradas.
- Rótulo de la varilla (calibre‑puente): poco fiable como escala.
- Foto de la montura desde abajo con una regla: paralaje de 35–40 mm.
- Barrido de giros de cabeza: interesante para el vértice, el centro de rotación y el galbe, pero se aplazó.

## 4. Métodos de medida

| Método | Fotos | Escala absoluta | Precisión típica |
|---|---|---|---|
| `frame` (por defecto) | Montura medida sobre la plantilla en la pantalla + 1 foto con gafas | ancho exterior del frente y, si se marcan, A + DBL (distancia entre centros) | ±0,5 mm por medida de la plantilla; necesita la pantalla calibrada |
| `card` | 1 foto con gafas y una tarjeta ID‑1 (85,60 mm) apoyada en la montura | tarjeta | DIP ±0,7 mm; el más preciso |
| `iris` | 1 sin gafas (N) + 1 con gafas (G), a la misma distancia | blanco‑blanco (HVID) 11,7 ± 0,45 mm o el del usuario | DIP ±2,5 mm (±0,8 con HVID medido); vértice útil solo con \|F\| ≥ 3 D |

**Flujo de una medida (asistente):** Persona → Montura (solo método montura) → Galbe* → Foto → Perfil* → Revisar y guardar. Los pasos marcados con * solo aparecen con la personalización activada y se pueden omitir.

**Guiado en vivo.** Comprobaciones: en tablet o móvil, dispositivo vertical (±3°) y sin girar (±1,5°); además, distancia, centrado, ojos a la altura de la cámara, giro, cabeceo, ladeo, ojos abiertos, quietud y tarjeta visible (método tarjeta). Después pide **mirar a la cámara**; dispara cuando han pasado al menos 0,9 s desde el aviso y la mirada lleva al menos 0,7 s correcta. A los 6 s dispara igualmente y lo avisa.

- **Selfie:** vista previa pequeña en espejo y la indicación pegada al borde de la pantalla donde está la cámara. En la fase final se oculta la vista previa y una flecha señala la cámara.
- **Óptico:** cámara trasera, imagen grande sin espejo, una sola indicación muy visible y un nivel tipo horizonte.

## 5. Modelo físico (resumen; detalle en `docs/MODELO.md`)

**Cámara.** Modelo estenopeico. `f_px = D_ref/2 / tan(FOV_diag/2)` y punto principal `((W−1)/2, (H−1)/2)`. Un punto a `u` px del centro, en un plano a la distancia Z, está en `X = u·Z/f`.

**Convergencia.** La persona mira al **objetivo** de la cámara, así que el punto visto en el plano de medida está sobre la línea de mirada.

- `rf` = distancia del plano de medida al centro de rotación:
  - con gafas: `vértice + espesor/2 + 13,5`;
  - sin gafas: `13,5 − 3,0 = 10,5`.
- Sin lente: `X_R = X_L·(ZL+rf)/ZL`.
- Con lente (Prentice): `δ = −c·F` y `X_R = X_L + rf·(X_L/ZL + δ)`, resuelto por punto fijo.
- Potencias por meridiano: `F_h = esf + cil·sen²(eje)` y `F_v = esf + cil·cos²(eje)`.
- DIP de cerca a la distancia N: `mono·N/(N+rf)`.

**Escala por método:**
- Tarjeta: `Z = f·85,60/ancho_px + 1,5`.
- Iris: `Z_N = f·HVID/(2r)`.
- Montura: fusión por la inversa de la varianza de dos estimaciones:
  - `Z_ext = f·W/W_px − (W−DNC)/2·sen(galbe)`;
  - `Z_caja = f·DNC/DNC_px`;
  - si discrepan más de 2,5 σ, se avisa.

**Vértice con el método iris.** El cambio de distancia entre fotos, `k`, sale de pares de puntos faciales fuera de las lentes. El aumento aparente del iris se ajusta con un modelo de lente gruesa (curva base de Vogel si no se introduce). El vértice se despeja por bisección y se fusiona con el valor previo de 12 ± 2,5 mm.

**Boxing.** Contorno de cada lente por programación dinámica polar (polaridad constante, radio mínimo elíptico, refinado subpíxel). El recuadro va girado según la inclinación de la montura (`tau`).

- `A = |t−n|·s/cos(galbe)`.
- `B = (bot−top)·s/cos(panto)`.
- `ED = 2·radio máximo`.
- Diámetro mínimo = `ED + 2·|descentramiento H| + 2`.
- La ranura o bisel (0,5 mm) se suma según el montaje.

**Personalización:**
- **Perfil:** `panto = atan2(ΔxTB·lado, ΔyTB)`.
  - Escala: altura exterior del frente H (con regla, o de la foto frontal dividida por cos panto).
  - `vértice = |C−P|·escala`.
- **Galbe:** ángulo de cada lente respecto al plano por los puntos medios de las lentes (ISO 13666).

**Incertidumbre** (`solveWithUnc`). Suma cuadrática de perturbaciones:
- FOV: ±4 % con ficha técnica, ±15 % estimado.
- Localización: iris ±0,4 px, lados de la caja ±0,7 px, multiplicados por `ss`.
- Plantilla ±0,5 mm, vértice ±2,5 mm, HVID ±0,45 mm.
- Postura: `rf·sen(|giro|+0,5°)` en las monoculares y `rf·sen(|cabeceo|+1°)` en las alturas.

## 6. Convenios invariantes (si se cambian, los resultados se rompen en silencio)

- **Píxeles.** El píxel *i* está en la coordenada *i*; MediaPipe se convierte con `x·W − 0,5`.
- **Remuestreo ×up.** El píxel de salida *j* corresponde a la coordenada `(j+0,5)/up − 0,5`, el mismo convenio que `drawImage`. Los errores en píxeles se multiplican por `cap.ss`.
- **OD = ojo derecho del sujeto = izquierda de la imagen sin espejo.** La vista en vivo va en espejo (CSS); las fotos de medida, no.
- **Plantilla.** El frente va contra la pantalla y las varillas hacia el usuario: **OD a la derecha** de la pantalla.
- **Recuadro.** Coordenadas (u, v) relativas al punto principal y giradas −`tau`. Lados `n`, `t`, `top`, `bot`; en OD el lado nasal tiene la u mayor.
- **Postura.** `yaw > 0` = cabeza girada hacia **su** izquierda; `pitch > 0` = barbilla arriba. El orden de la matriz de MediaPipe no está documentado: se verifica en tiempo de ejecución (`updateConvention`).
- **Actitud del dispositivo.** Vertical del mundo `u = (−cos β sen γ, sen β, cos β cos γ)`. `tilt > 0`: la pantalla mira hacia arriba. `roll > 0`: girado en sentido antihorario.
- **Constantes:** córnea → centro de rotación 13,5 mm; córnea → plano del limbo 3,0 mm; HVID 11,7 mm; tarjeta 85,60 mm (1,5 mm por delante del plano de la lente); vértice = córnea → cara posterior de la lente.
- **Ranura o bisel:** en aro completo se suma a los 4 lados; en nylon, solo arriba; al aire, nada.

## 7. Arquitectura del código

Un único `index.html` con un `<script type="module">` en dos partes:

- **CORE**, entre `// ==CORE START==` y `// ==CORE END==`. Funciones puras **sin DOM**, probadas con `node:test`. `tests/lib/extract-core.cjs` extrae esa sección y exporta todo `function` y `const` de nivel superior. **No hay que romper los marcadores.**
  - Geometría: `focalFromDfov`, `rcFromLens`, `cardWidthPx`, `measureCap`, `solveAll`, `solveWithUnc`.
  - Método montura: `tplFromLines`, `tplDNC`, `detectOuterEdge`, `frameScaleZ`.
  - Ráfaga: `nccAt`, `registerShift` (NCC entera + Lucas–Kanade), `similarity2`, `stackRGBA`.
  - Dispositivo: `deviceAttitude`, `guidePlacement`.
  - Personalización: `profileMeasure`, `wrapFromPoints`.
  - Óptica: `lensData`, `apparentMag`, `solveVertexH`, `fuseVertex`.
  - Visión: `detectCard`, `refineEdge`, `refineIris` (Kåsa), `detectLensContour`, `rimAnalysis`, `classifyFrame`, `padAnalysis`, `featureScale`.
  - Histórico y exportación: `buildRecord`, `summarizeHistory`, `recordsToCSV(people, measures, lang)`, `normalizeImport`, `mountingFrom`, `recordToOMA`, `recordToJSON`.
  - Registro: `logMsg`, `logPush`, `logToText`.
- **App** (DOM):
  - Idioma: `Lg(es, en)` para el texto generado. Los textos fijos se traducen con el diccionario `I18N_EN`, mediante `translateStatic`. **No se puede usar una variable local llamada `L`.**
  - Navegación: `go(vista)`. Asistente: `startMeasure`, `showStep`.
  - Bucle en vivo: `evaluate` → `guidance` → `captureBurst` → `stackBurst` → `analyzeCapture`.
  - Editor de marcadores con lupa y teclado: `drawScene`, `recompute`.
  - Datos: `DB`, `KV`. Edición: `captureState`, `editRecord`.
  - Laboratorio: `openJob`, `doJob`, `lmsWriteFolder`, `lmsPost`.
  - Registro: `logEvt`, `logWrap`.
- **Dependencias externas** (CDN, versión fijada): `@mediapipe/tasks-vision@1.2.3` (FaceLandmarker: 478 puntos, blendshapes, matriz facial) y el modelo `face_landmarker.task` de `storage.googleapis.com`. Nada más.
- **Requisitos de ejecución:** la cámara exige https o localhost (`npm run serve` → http://localhost:8000). **No funciona como artefacto de claude.ai**, porque el iframe bloquea la cámara.

**Modelo de medición en memoria:** `M = {mode, caps: [N?, G]}`. Cada `cap` contiene:
- `cv`, `W`, `H`, `f`, `ss`, `burst`;
- `iris.{od,os}.{x,y,r}`, `lmk`, `pose`;
- en G: `box`, `tau`, `contour`, `frameAuto`, `outer`, `outerV`;
- en N: `bridge`; en tarjeta: `card.{L,R}`;
- en la foto de perfil (`id: 'P'`): `prof`;
- `alerts` y `notes`.

## 8. Datos guardados y formatos

### Almacenamiento (todo en el navegador del dispositivo; no se sincroniza)

| Dónde | Contenido |
|---|---|
| IndexedDB `dipfx` | Almacenes `people` {id, name, ref, birth, notes, created, updated} y `measures` (índice `personId`). **Se abre sin número de versión y no se sube nunca** (§13). |
| IndexedDB `dipfx-kv` | Permiso de la carpeta del LMS (`FileSystemDirectoryHandle`). |
| localStorage | `dipapp.prefs`: método, exigencia, voz, quién hace la foto, personalización, idioma. |
| | `dipapp.screen`: calibración en px/mm, ligada a pantalla y zoom. |
| | `dipapp.tpl`: líneas de la plantilla, tipo, material y plaquetas. |
| | `dipapp.campos`: posición de la cámara por orientación. |
| | `dipapp.lms`: configuración del envío, incluida la clave de la pasarela. |
| | `dipapp.fov.*`: FOV calibrado por cámara. |
| | `dipapp.log`: registro de actividad (últimas 800 entradas). |

### Registro de una medida (`buildRecord`, almacén `measures`)

```js
{ id, personId, date, method: 'frame'|'card'|'iris', frameName, notes,
  values: { pdFar, monoOD, monoOS, hOD, hOS, pdNear, monoNearOD, monoNearOS, DBL, DNC, Z, vertex },
  unc:    { …las mismas claves (±1σ, mm)…, A_od, A_os },
  frame:  { od: {A, B, ED, decH, decV, MBS}, os: {…} },
  mounting, material, pads, vertexMeasured, flags: [es], flagsEn: [en],
  pers:   { panto, pantoSd, bvd, bvdSd, wrapOd, wrapOs } | null,
  params: { rx: {od:{s,c,a}, os:{…}}, index, vertex, wrap, panto, groove, nearDist, tpl:{W,Aod,Aos,DBL}, hvid },
  camera: { label, dfov, src }, image: Blob JPEG | null, text,
  // desde 0.8.0 (opcionales):
  state:  { v:1, mode, caps:[…marcadores + recorte JPEG…], inputs:{…}, wrap, tpl, fov },   // para «Editar»
  editedAt, original: { date, values, frame, pers }, manualValues, job, sentAt }
```

**Regla:** todo campo nuevo es **opcional** y el código debe funcionar con registros antiguos que no lo tienen. Por ejemplo, una medida sin `state` se edita a mano.

### Exportaciones

- **Copia de seguridad JSON** (Ajustes → Datos): personas y medidas, opcionalmente con fotos en base64. Se valida al importar con `normalizeImport`.
- **CSV**: en español con `;` y coma decimal; en inglés con `,` y punto.
- **JSON por medida** (`recordToJSON`): `format: 'dipfx-measurement', version: 1`, unidades explícitas, cada valor como `{value, sd}`, montura, posición de uso (con indicación de si se midió) y graduación.
- **OMA/DCS por medida** (`recordToOMA`): fin de línea CRLF y orden `derecho;izquierdo`:
  ```
  JOB=T123
  DO=B
  SPH=-2.00;-1.75   CYL=…   AX=…        (solo si hay graduación)
  IPD=31.50;32.50                      (monoculares de lejos)
  NPD=…                                (monoculares de cerca)
  SEGHT=22.50;22.50                    (alturas)
  HBOX=…  VBOX=…  FED=…  DBL=17.00
  BVD=…  PANTO=…  ZTILT=…              (solo si se midieron con la personalización)
  _DIPFX_PD, _DIPFX_NEARPD, _DIPFX_UNC_*, _DIPFX_METHOD, _DIPFX_DATE, _DIPFX_REF,
  _DIPFX_NAME (solo si se permite), _DIPFX_FRAME, _DIPFX_MOUNT, _DIPFX_MATERIAL, _DIPFX_PADS
  ```
  ⚠️ La correspondencia se hizo con DCS 3.x **sin la norma completa a mano**. Hay que verificarla con el LMS real del laboratorio. La versión vigente de DCS es la 3.14 (julio de 2025).

### Envío al laboratorio (LMS)

- **Carpeta vigilada:** File System Access API; solo Chrome y Edge de escritorio. El LMS o su importador recoge el archivo.
- **Pasarela HTTP:** POST del archivo con una cabecera de clave opcional. Necesita https y CORS.
- **No es posible desde un navegador** abrir la conexión TCP del protocolo DCS con Innovations, DVI o RxUniverse. Hace falta un **puente local**, por ejemplo un pequeño servicio en el PC de la óptica que reciba por HTTP o vigile una carpeta y hable DCS por TCP, además de las especificaciones de integración de cada LMS. Está pendiente.

## 9. Pruebas

```bash
npm run fixtures     # escenas sintéticas en tests/fixtures/out/ (python3, numpy, Pillow; ffmpeg opcional)
npm test             # 53 pruebas unitarias (node:test) sobre CORE
npm run test:e2e     # Chrome sin cabeza con cámara simulada (.y4m) y MediaPipe simulado (playwright; CHROME_PATH opcional)
```

- **Unitarias** (`tests/unit/`):
  - geometry, optics, image, frame, template, burst, device, personal;
  - history, export, log.
- **e2e** (`tests/e2e/run_e2e.py`):
  - método montura completo: calibración, plantilla, ráfaga, bordes exteriores e histórico;
  - edición de una medida guardada, exportación OMA y JSON, envío a una pasarela simulada;
  - barra de botones, registro de actividad;
  - selfie y óptico; método tarjeta;
  - personalización (galbe y perfil por voz); método iris con fotos subidas; interfaz en inglés;
  - **compatibilidad con datos antiguos**: base de datos v1 y v2, con y sin otra ventana abierta.
- Trucos de las pruebas:
  - `?e2e` acorta las esperas de la voz y expone `window.__dipfx`.
  - Las pruebas fijan `locale='es-ES'`.
  - El detector simulado distingue la imagen por el píxel (1,1): 10 = sin gafas, 240 = con gafas, 128 = tarjeta.
- En el entorno de Claude Code en la nube, Chrome está en `/opt/pw-browsers/…/chrome` (variable `CHROME_PATH`).
- CI: `.github/workflows/tests.yml` ejecuta las unitarias en cada push a `main`.
- Las escenas sintéticas se proyectan con el **mismo** modelo físico: validan la coherencia interna y los algoritmos de visión, **no** la exactitud con caras reales.

## 10. Limitaciones conocidas (hay que mostrarlas con honestidad en la interfaz)

- **FOV:** Apple y la mayoría de fabricantes no lo publican. Un 15 % de error supone unos ±0,6 mm en la DIP (vía la convergencia). No hay que inventar FOV en `CAM_DB`: se cita la fuente y se usa `kind: 'spec'` solo si viene de una ficha técnica.
- **Iris:** depende del HVID. El vértice solo se deduce con |F| ≥ 3 D.
- **Postura:** cada grado de giro residual mueve las monoculares unos 0,45 mm, y el cabeceo, las alturas en la misma proporción. Está incluido en el ±.
- **Monturas:**
  - Nylon: el borde inferior se estima con `top + 0,72·A`.
  - Al aire: puede usar un recuadro típico.
  - La clasificación usa umbrales sin calibrar.
- **Método montura:** depende de la calibración de la pantalla y del paralaje al marcar. El borde exterior se pierde con monturas transparentes o finas, o contra el pelo.
- **Ráfaga:** solo mejora si hay desplazamientos subpíxel entre fotogramas; no crea detalle que la óptica no resuelve.
- **Tablet:**
  - Los signos de `deviceAttitude`, la elección de la cámara trasera y el FOV trasero están sin validar.
  - La mirada (`gazeOk`) está sin validar con caras reales.
- **Perfil y galbe:** los puntos se marcan a mano. La escala del perfil es frágil. El galbe es el de la montura sola, como recta entre extremos.
- **Pupila:** se usa el centro del iris, no el centro pupilar ni el reflejo corneal.
- **Histórico:** vive en un navegador y en un dispositivo. Solo la copia JSON lo protege. Las fotos de caras son datos personales.

## 11. Prioridades siguientes

1. **Validar con una cámara y caras reales.** Signos y umbrales de postura y mirada; tarjeta con dedos y pelo; contorno de la lente con reflejos y pestañas; umbrales de clasificación. En tablet: sensor, cámara trasera y colocación de las indicaciones.
2. **Banco de fotos reales etiquetadas** (pupilómetro, centrador, trazador) y un script que las pase por «subir fotos» y mida el error.
3. **Verificar el OMA con un LMS real** y, si se necesita envío directo, construir el **puente DCS** con las especificaciones de cada LMS.
4. **Modularizar** sin perder la entrega en un archivo: `src/core`, `src/app` y esbuild → `dist/index.html`, adaptando `extract-core.cjs`.
5. Óptica:
   - centro pupilar o reflejo corneal;
   - detección automática de los puntos del perfil;
   - vértice en el método tarjeta.
6. Producto:
   - informe PDF;
   - sincronización entre dispositivos (necesita servidor; cuidado con la protección de datos);
   - edición del contorno completo para el ED.

## 12. Normas de trabajo que se han seguido

- `index.html` autocontenido y sin build hasta que se acuerde modularizar.
- Toda función de cálculo va en CORE, sin DOM, con su prueba unitaria.
- Antes de dar algo por terminado: `npm test` y, si se toca el flujo o la interfaz, `npm run test:e2e`.
- Todo texto nuevo de la interfaz lleva su traducción: `Lg()` para el texto generado o una entrada en `I18N_EN` para los textos fijos.
- Se sube `APP_VERSION` y `package.json` en cada publicación. Los pasos nuevos y sus errores se registran con `logEvt`.
- Los convenios de §6 no se cambian sin consultarlo.

## 13. Lección importante: el incidente de la 0.8.0 (datos «desaparecidos»)

- **Qué pasó.** La 0.8.0 subió la base de datos `dipfx` de la versión 1 a la 2 para añadir un almacén. El usuario tenía varias ventanas de la app abiertas, una de ellas la app instalada en Edge con la versión anterior. En IndexedDB, una subida de versión **espera a que se cierren todas las demás conexiones**. La app nueva se quedó esperando sin avisar: no mostraba las personas ni las medidas, y crear una persona o tomar una medida no hacía nada. Los datos no se perdieron.
- **Arreglo (0.8.1):**
  - La base de datos se abre **sin número de versión** y no se sube nunca.
  - Lo nuevo va en campos opcionales o en **otra base de datos** (`dipfx-kv`).
  - Si algo bloquea la apertura, se avisa al usuario y queda en el registro.
  - Las conexiones abiertas se cierran solas si otra ventana pide una actualización (`onversionchange`).
- **Prueba permanente.** El e2e siembra datos como los guardaban las versiones anteriores (BD v1 y v2), con y sin otra ventana abierta. Comprueba que se ven las personas y las medidas y que se pueden crear nuevas.
- **Norma:** los datos guardados son sagrados. Ningún cambio de formato puede impedir leer los registros antiguos.
- **Diagnóstico a distancia.** El usuario puede descargar el **registro de actividad** (Ajustes → Registro de actividad) y compartirlo. Incluye la versión, el navegador, la pantalla, si la app está instalada, el estado de IndexedDB, el número de registros y los eventos y errores. No incluye nombres, fotos ni claves.

## 14. Preguntas abiertas para el usuario

- ¿Qué LMS usa el laboratorio de destino y qué versión de DCS? ¿Hay especificaciones de integración (dirección, puerto, etiquetas aceptadas, carpeta de importación)?
- ¿Hay acceso a equipos de referencia (pupilómetro, centrador digital, trazador) para el banco de fotos reales?
- ¿Cuál es el destino final: herramienta interna, demo para clientes o integración con la app de la pinza? Esto decide si se modulariza, si hace falta un servidor y cómo se sincroniza.

## 15. Primer mensaje sugerido para continuar en un proyecto nuevo

> Lee `docs/HANDOFF_COMPLETO.md`, `CLAUDE.md` y `docs/MODELO.md` del repositorio Marcos86GO/DipFx. Ejecuta `npm run fixtures`, `npm test` y `npm run test:e2e` para confirmar que todo pasa. No cambies los convenios de §6 ni la versión de la base de datos `dipfx`, y mantén la compatibilidad con los datos guardados. Después, [tarea concreta].
