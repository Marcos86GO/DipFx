# Traspaso: conversación de diseño (16–17 nov 2026)

Resumen de cómo se llegó al estado actual, para continuar en Claude Code.

## Origen y requisitos del usuario (en sus palabras, resumidos)

1. «¿Puedes, con una foto tipo retrato hecha con la webcam del portátil, saber a qué distancia está mi cara?»
2. La idea es una **app para medir la DIP y la altura pupilar con las gafas puestas**. El usuario no conoce su DIP ni tiene una foto a distancia medida. Pidió:
   - detectar el modelo del dispositivo para conocer las specs de su webcam;
   - **detectar si la cara no está recta y guiar** al usuario;
   - **no tomar la foto hasta que esté perfectamente alineada**, sin giros y con los ojos a la altura de la cámara;
   - dar la **DIP de lejos** teniendo en cuenta la **convergencia** al mirar el dispositivo.
3. Ampliación:
   - **modo iris con 2 capturas** (sin gafas y con gafas);
   - usar el **cambio de tamaño del iris** y la **graduación de cada lente** para afinar distancias, DIP y alturas;
   - calcular las **dimensiones de la montura** e **identificar el montaje, el bisel y si tiene plaquetas**.
4. Preparar este traspaso para un proyecto en Claude Code.

Contexto del usuario: optometrista formado en España, sin licencia en EE. UU. Dirige el equipo técnico de una empresa de diseños de lentes freeform. Tiene otra app basada en una pinza (clip) para medidas de centrado a partir de fotos, en la que echaba en falta detectar y compensar los giros de cabeza. Esta app ataca ese problema con guiado y bloqueo de postura.

## Decisiones clave y por qué

- **Sin referencia de tamaño conocido no hay escala absoluta.** Se eligió la **tarjeta ID‑1 apoyada en la montura** como método principal, porque deja el FOV como efecto de segundo orden (solo influye en la convergencia). El iris (HVID 11,7 ± 0,45) queda como alternativa sin tarjeta, con un error mayor declarado.
- **El navegador no expone el modelo del portátil.** Se identifica la cámara por su etiqueta y su ID USB, y en Mac se estima el modelo por la resolución de pantalla. La base de datos de FOV es pequeña y honesta sobre qué es ficha técnica y qué es estimación. Ejemplos: Dell publica 74,9–78,6° en sus portátiles; Logitech C920 78°, C270 55°; Apple no publica el FOV.
- **El usuario mira al objetivo de la cámara, no a la pantalla.** Así el punto de fijación es exactamente el centro de proyección y la corrección de convergencia es geométrica y exacta.
- La imagen del ojo, vista a través de la lente, cae sobre la línea de mirada. Por eso el **punto del plano de la lente se mide sin sesgo** sea cual sea la potencia, y solo hay que corregir el **prisma** entre la lente y el centro de rotación (Prentice, con el centro óptico en la posición de lejos).
- **Tolerancias**: el giro se aprieta (±2° normal) porque desplaza las monoculares unos 0,45 mm/°, y el cabeceo afecta igual a las alturas. Hay modos estricto, normal y flexible.
- **Voz** (speechSynthesis): el usuario mira a la cámara y no puede leer la pantalla.
- **Signos de la matriz de MediaPipe** no documentados: se verifican en tiempo de ejecución contra indicadores 2D (nariz frente a contorno facial) y por correlación.
- **Archivo único y sin build**, para alojarlo fácilmente (GitHub Pages). Las páginas de artefacto de claude.ai no permiten la cámara.
- **Modo iris de dos fotos**:
  - k (cambio de distancia) se mide con rasgos que no quedan detrás de las lentes;
  - el vértice se despeja con un modelo de lente gruesa y se fusiona con un valor previo;
  - la DIP sale de la foto sin gafas;
  - las monoculares, las alturas y la montura salen de la foto con gafas.
- **Clasificación de montura heurística, con corrección manual.** Es imposible garantizarla sin datos reales.

## Errores encontrados y corregidos durante el desarrollo

- Convenio de píxel (centro de píxel en *i* frente a *i*+0,5): sesgo de 0,5 px en los centros del iris. Se unificó a «píxel *i* = coordenada *i*».
- Emparejamiento de los bordes de la tarjeta con un distractor (pelo):
  - se añadió homogeneidad del interior y uniformidad a lo ancho de la tarjeta;
  - se corrigió un **NaN** que bloqueaba el emparejamiento cuando un borde caía en el límite de la ventana de búsqueda.
- El contorno de la lente saltaba entre el borde interior y el exterior del aro, a las plaquetas o al ojo. Se corrigió con:
  - una pasada de polaridad constante;
  - el radio mínimo elíptico;
  - la intensidad de borde recortada a 1;
  - el refinado subpíxel.

## Estado de verificación

- 19 pruebas unitarias en verde (óptica, geometría de los dos métodos, visión, contornos y clasificación de 4 tipos de montura). Desde el 17 nov son 31: se añaden el método montura, el borde exterior del aro y la ráfaga.
- e2e en Chrome sin cabeza, en verde, con resultados frente a la verdad sintética:
  - **Método tarjeta**: DIP 64,1/64,0; monoculares 31,5/32,5 exactas; alturas 22,5 exactas; A 53,0 y DBL 17,0 exactos (con 0,5 mm de ranura); «aro completo metálico» con plaquetas.
  - **Método iris** (−5/−4 D, vértice real 13): DIP 64,0; monoculares exactas; alturas 22,7 frente a 22,5; vértice deducido 13,1 y 12,7; «pasta» sin plaquetas.
- **Pendiente: nada se ha probado con una cámara y una cara reales.**

## Sesión del 17 nov 2026: método montura y ráfaga apilada

- El usuario no quiere depender de una tarjeta. Se descartaron, por este orden:
  - cámara de IR: no accesible desde el navegador y de baja resolución;
  - estéreo con dos cámaras: línea base de 1–2 cm, sin calibrar;
  - barrido de giros de cabeza: interesante para vértice, centro de rotación y galbe, aplazado;
  - rótulo de la varilla: poco fiable;
  - foto de la montura desde abajo con regla: paralaje de 35–40 mm.
- Se eligió: **calibrar la pantalla una vez** (regla sobre la pantalla) y **medir la montura sobre una plantilla a escala real**: ancho exterior y, opcionalmente, A y DBL. Después, una foto con las gafas puestas, en la que se detectan los bordes exteriores y las cajas, ajustables a mano.
- Flujo pedido por el usuario:
  1. medir la montura en la plantilla;
  2. ráfaga frontal;
  3. mejor imagen o promedio procesado en 2–4 s como máximo (en Chrome sin cabeza, unos 0,4–0,6 s de procesado);
  4. detección de bordes y pupilas;
  5. confirmación o ajuste;
  6. medidas.
- La ráfaga apilada se aplica a todos los métodos.

## Sesión del 17–18 nov 2026: histórico de personas e interfaz guiada

- El usuario pidió guardar las medidas de cada persona, con un histórico de todas sus medidas, y una interfaz limpia, sencilla y que guíe el proceso.
- Decisión: sin servidor, **todo en el navegador** con IndexedDB (personas y medidas; la foto con las marcas, opcional, como JPEG). Copia de seguridad JSON (con o sin fotos), importación y CSV para hojas de cálculo. Motivo: la app es estática (GitHub Pages) y las fotos de caras son datos personales sensibles.
- Interfaz rehecha: cabecera con Personas / Ajustes / + Nueva medida; asistente por pasos con indicador de progreso; resultados en tarjetas con las cifras clave y los detalles técnicos plegados; editor que amplía la zona de las gafas; ajustes agrupados; diseño adaptado al móvil.
- Pendiente: reabrir una medida guardada para reeditar marcadores, informe PDF, sincronización entre dispositivos.

## Sesión del 18 nov 2026: logo y plantilla rediseñada

- Logo SVG propio (dos lentes con las pupilas y una cota de DIP debajo), en la cabecera y como favicon.
- Paso Montura en ordenador: ocupa toda la pantalla y, si el navegador lo permite, entra en pantalla completa. La plantilla queda **en el borde inferior de la pantalla** para apoyar la montura en la base del teclado. La línea de centros se arrastra en vertical (por defecto, 30 mm sobre el borde).
- Silueta de la montura detrás de las líneas, según el tipo (aro completo, ranurado, al aire), el material (grosor del aro) y las plaquetas. Cotas A, DBL y ancho en chips.
- En ese paso se eligen tipo de montaje, material (pasta, TR90, metal, titanio, mixta) y plaquetas. Pasan a la revisión como elección manual y se guardan con la medida (CSV con columnas Material y Plaquetas).

## Preguntas abiertas para el usuario

- ¿Hay acceso a equipos de referencia (pupilómetro, centrador digital, trazador de monturas) para crear un banco de fotos reales etiquetadas?
- ¿Destino final? Herramienta interna, demo para clientes o integración con la app de la pinza. Esto decide si modularizar y si hacen falta exportaciones (JSON/PDF, formato OMA/VCA para el trazado).
- ¿Interfaz bilingüe (es/en)?
