# Primer mensaje sugerido para Claude Code

Pega esto al abrir el proyecto:

---

Lee CLAUDE.md, docs/HANDOFF.md y docs/MODELO.md. Luego:

1. Instala lo necesario y ejecuta `npm run fixtures`, `npm test` y `npm run test:e2e` para confirmar que todo pasa en esta máquina.
2. Crea un modo de depuración activable con `?debug` que muestre en pantalla los valores en vivo (giro, cabeceo, ladeo, versión de la mirada, blendshapes, k, contraste del aro) y permita descargar un JSON con las medidas y los marcadores, para validar con mi cámara real.
3. Prepara `tests/real/`: una estructura para fotos reales (sin gafas, con gafas, con tarjeta) con un `labels.json` de medidas de referencia (DIP, monoculares, alturas, A, B, DBL, montaje, plaquetas), y un script que las procese por la vía de «subir fotos» y dé una tabla de errores.

No cambies los convenios de CLAUDE.md sin preguntarme. Mantén index.html autocontenido.
