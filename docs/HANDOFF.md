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
- Pendiente: informe PDF, sincronización entre dispositivos (la edición de medidas guardadas se hizo después).

## Sesión del 18 nov 2026: logo y plantilla rediseñada

- Logo SVG propio (dos lentes con las pupilas y una cota de DIP debajo), en la cabecera y como favicon.
- Paso Montura en ordenador: ocupa toda la pantalla y, si el navegador lo permite, entra en pantalla completa. La plantilla queda **en el borde inferior de la pantalla** para apoyar la montura en la base del teclado. La línea de centros se arrastra en vertical (por defecto, 30 mm sobre el borde).
- Silueta de la montura detrás de las líneas, según el tipo (aro completo, ranurado, al aire), el material (grosor del aro) y las plaquetas. Cotas A, DBL y ancho en chips.
- En ese paso se eligen tipo de montaje, material (pasta, TR90, metal, titanio, mixta) y plaquetas. Pasan a la revisión como elección manual y se guardan con la medida (CSV con columnas Material y Plaquetas).

## Sesión del 18 nov 2026: selfie y óptico, indicaciones junto a la cámara, nivel del dispositivo

- Nuevo control «¿Quién hace la foto?»: la propia persona (selfie) u otra persona (óptico, con la cámara trasera de una tablet o móvil). Se elige en el primer paso o en Ajustes y se recuerda.
- Selfie: las indicaciones (icono grande y una frase) y una vista previa pequeña se ponen pegadas al borde de la pantalla donde está la cámara, para que los ojos no se desvíen. Cuando la cabeza está bien, se oculta la vista previa, se pide «Mira a la cámara» con una flecha hacia ella, se espera a que la mirada llegue y se asiente, y se dispara la ráfaga (sin cuenta atrás en pantalla).
- Posición de la cámara: en Ajustes → Cámara (12 puntos en el borde de un esquema de pantalla). Si falta, se pregunta solo en la primera medida selfie del dispositivo (y la primera vez en cada orientación de una tablet) y se guarda en Ajustes. No se pide al calibrar la pantalla.
- Óptico: imagen grande sin espejo, una sola indicación muy visible (mover la tablet, pedir a la persona que gire la cabeza…), nivel tipo horizonte artificial y comprobaciones resumidas en puntos.
- Tablet o móvil (selfie u óptico): se exige el dispositivo vertical (±3°) y sin girar respecto al suelo (±1,5°), a partir del sensor de orientación. Después, cara y cámara enfrentadas y alineadas con las comprobaciones de siempre.
- Sin probar en una tablet real: los signos del sensor y la cámara trasera están por validar.

## Sesión del 18 nov 2026: personalización e inglés

- Panto y vértice con una **foto de perfil**: en tablet o móvil, la hace otra persona con la cámara trasera y la app la guía con el nivel del dispositivo (en selfie no es posible); en ordenador, se pide poner la cámara recta y una voz guía a la persona, de lado, y dispara. Se marcan cuatro puntos y la escala sale de la altura exterior del frente (de la foto frontal o medida con regla).
- **Galbe** con una plantilla nueva: la montura apoyada por el borde inferior del frente y cuatro puntos en los extremos de las lentes.
- Las dos medidas se activan en Ajustes («Medidas de personalización») y añaden dos pasos omitibles al asistente.
- **Inglés**: selector de idioma en Ajustes (por defecto, el del navegador). Textos fijos por diccionario y textos generados con `Lg()`. CSV en inglés con coma y punto decimal.
- Corregido de paso: al volver a elegir la misma foto en «Analizar fotos ya hechas» no se analizaba (el selector no avisaba del cambio); al subir fotos se arrastraban parámetros de la medida anterior.

## Sesión del 18 nov 2026: editar, exportar y enviar al laboratorio

- **Editar** una medida guardada: desde ahora cada medida guarda su estado (marcadores, parámetros, plantilla, FOV y un recorte JPEG de la zona de las gafas), así que «Editar» la reabre en la revisión con todo ajustable. Al guardar se sustituye (no se duplica) y se conservan la fecha original, la fecha de edición y los valores originales. Las medidas guardadas antes no tienen estado: se editan sus valores a mano.
- **Exportar** cada medida en JSON (formato `dipfx-measurement` v1, con ± y origen de cada dato) y en OMA según DCS (`.oma`, CRLF, derecho;izquierdo). BVD, PANTO y ZTILT solo se escriben si se midieron. Pide número de trabajo (JOB).
- **Enviar al LMS**: Ajustes → Envío al laboratorio. Carpeta vigilada (Chrome/Edge de escritorio; el LMS o su software de importación recoge el archivo) o pasarela HTTP (POST con cabecera de clave opcional). La medida queda marcada como enviada con su número de trabajo.
- Límite: el navegador no puede hablar DCS por TCP. Para una conexión directa con Innovations, DVI o RxUniverse hace falta un puente local y sus especificaciones. La correspondencia de etiquetas DCS está por verificar con un LMS real.
- IndexedDB pasa a la versión 2 (almacén `kv`).

## Sesión del 18 nov 2026: incidente de datos «desaparecidos», registro de actividad

- Incidente: con la 0.8.0, el usuario tenía varias ventanas de la app abiertas (una con la versión anterior). La 0.8.0 subía la base de datos a la versión 2; esa subida espera a que se cierren las demás conexiones, así que la app no listaba personas ni guardaba nada, sin avisar. Los datos no se perdieron.
- Arreglo (0.8.1): la base de datos se abre sin número de versión y no se sube nunca; el almacén `kv` pasa a una base de datos aparte (`dipfx-kv`). Si algo bloquea la apertura, se avisa y queda en el registro. Prueba e2e de compatibilidad con datos de la versión 1 y 2, con y sin otra ventana abierta.
- **Registro de actividad** en Ajustes, para que el usuario lo comparta cuando haya un problema.
- Los botones de una medida guardada (Editar, Exportar, Enviar…) van en una barra fija arriba.

## Sesión del 17 nov 2026: identidad corporativa de IOT (0.9.0)

- El usuario pidió adaptar el aspecto de la app al diseño corporativo de la plantilla `IOT_PPT_Template_2026.pptx`. De su diapositiva de guía de marca salen la paleta (IOT Blue #0062FF, IOT Black #130500, tonos del azul al 70/40/20/10 %, Cool Gray 9/7/3/2 y los secundarios magenta, violeta y cian) y la tipografía (Source Sans Pro: titulares Semibold, texto Light).
- Cambios solo de estilo: variables de color en `:root`, Source Sans Pro (jsdelivr, con `local()` primero), formas planas y rectas, cabecera en IOT Blue con el logotipo de IOT en blanco (vectorizado del PNG de la plantilla con OpenCV), favicon plano, pasos del asistente con el actual subrayado en azul, cabeceras de tabla con filete negro, resultado principal y primera estadística de la ficha en un bloque IOT Blue. Los lienzos de la plantilla usan el azul y los grises corporativos y la misma fuente.
- Decisiones: el texto va en Regular (400) y no en Light, que en pantalla y a 14–16 px se lee peor; el Light queda para entradillas y la segunda mitad de «DipFx». Se mantienen el verde, el rojo y el ámbar de estado y los colores de las marcas sobre la foto, porque son funcionales y los textos de ayuda los nombran.
- La sección CORE no cambia.
- Corregido de paso: al abrir la ficha de una persona, el nombre recibía el foco a los 30 ms aunque ya se estuviera escribiendo en otro campo, y lo escrito acababa en el nombre (la e2e lo destapó: «Ana PérezH-0012»). Ahora solo se enfoca si el foco no está ya en la ficha.

## Preguntas abiertas para el usuario

- ¿Hay acceso a equipos de referencia (pupilómetro, centrador digital, trazador de monturas) para crear un banco de fotos reales etiquetadas?
- ¿Destino final? Herramienta interna, demo para clientes o integración con la app de la pinza. Esto decide si modularizar y si hacen falta exportaciones (JSON/PDF, formato OMA/VCA para el trazado).
- ¿Interfaz bilingüe (es/en)?
