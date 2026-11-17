# Modelo geométrico y óptico

Referencia de las fórmulas que implementa la sección CORE de `index.html`. Unidades: mm, dioptrías (D), píxeles (px).

## 1. Cámara

Modelo estenopeico con el punto principal en el centro de la imagen, `c = ((W−1)/2, (H−1)/2)`.

La focal sale del FOV diagonal publicado:

```
f_px = D_ref / 2 / tan(FOV_diag / 2)
```

`D_ref` es la diagonal del encuadre al que se refiere el FOV (16:9 o 4:3), escalada al stream actual. Si el stream tiene otra proporción, se asume que es un recorte que conserva la dimensión que encaja (`refDiag`).

Un punto de la imagen a `u` px del punto principal, situado en un plano a la distancia Z de la cámara, está en `X = u · Z / f_px`.

## 2. Convergencia hacia la cámara

El sujeto mira al objetivo. La línea de mirada de cada ojo va del centro de rotación del ojo a la cámara. Lo que vemos en la imagen es el punto donde esa línea cruza el plano de medida (plano de la lente o del limbo), porque está alineado con la cámara.

- `ZL`: cámara → plano de medida.
- `rf`: plano de medida → centro de rotación.
  - Con gafas: `rf = vértice + espesor/2 + 13,5`.
  - Sin gafas (plano del limbo): `rf = 13,5 − 3,0 = 10,5`.

Sin lente, la posición lateral del centro de rotación (que es la pupila en visión de lejos) es:

```
X_R = X_L · (ZL + rf) / ZL
```

Con lente de potencia F en ese meridiano, la línea de mirada se desvía al cruzar la lente (Prentice). Se asume el centro óptico en la posición de lejos:

```
δ = −c · F    (rad),   c = (X_L − X_R) / 1000   (m)
X_R = X_L + rf · (X_L/ZL + δ)      → iteración de punto fijo (rcFromLens)
```

Con esto:

- **DIP de lejos** = `X_R(OI) − X_R(OD)`.
- **Monoculares** = distancia desde el centro de la montura (punto medio de los lados nasales del recuadro) o, sin gafas, desde la nariz.
- **Cerca a la distancia N** del plano de la lente: `mono · N / (N + rf)`.
- **Alturas**: igual en vertical, con la potencia del meridiano vertical.

Potencias por meridiano (cilindro con su signo, eje en grados):

- Horizontal: `F_h = esf + cil · sin²(eje)`.
- Vertical: `F_v = esf + cil · cos²(eje)`.

## 3. Método tarjeta

```
Z_tarjeta = f_px · 85,60 / ancho_tarjeta_px
ZL = Z_tarjeta + offset(1,5)
```

El ancho de la tarjeta se mide en perpendicular a sus bordes (`cardWidthPx`), así que admite una tarjeta algo girada en su plano.

## 4. Método iris (dos fotos)

**Foto N (sin gafas).** La distancia al limbo se obtiene con el blanco‑blanco de cada ojo:

```
Z_N = f_px · mean(HVID_ojo / (2·r_ojo))
```

La DIP de lejos sale de N, sin prisma.

**Foto G (con gafas)**:

1. **Cambio de distancia entre fotos.** `k = mediana(d_G / d_N)` sobre pares de puntos faciales fuera de las lentes: comisuras, aletas nasales, mandíbula y contorno (`FEAT_PAIRS`). Entonces `Z_G = Z_N / k`.
2. **Aumento observado del iris.** Para cada ojo, `A_obs = (r_G / r_N) / k`.
3. **Modelo de lente gruesa** (`apparentMag`). La luz va del limbo a la cámara: cara posterior `F2 = F − F1/(1 − t/n·F1)`, espesor `t`, cara anterior `F1` (curva base). Vergencias reducidas:
   ```
   L1 = −1/h;  L1' = L1 + F2;  L2 = L1'/(1 − (t/n)·L1');  L2' = L2 + F1
   m = (L1/L1')·(L2/L2')
   A = m · (Zf + t + h) / (Zf − 1/L2')
   ```
   `h` es la distancia de la cara posterior al limbo (vértice + 3,0) y `Zf` la de la cámara a la cara anterior. Si no se introducen, se usan la curva base de la regla de Vogel (`F ≥ 0: F+6`; `F < 0: F/2+6`) y un espesor estimado.
4. **Despeje del vértice.** Se busca h por bisección en [3, 40] mm (`solveVertexH`). La desviación típica sale de la del radio del iris (±0,2 px por foto) y de la de k, a través de `dA/dh`.
5. **Fusión.** Los dos ojos se combinan con el valor previo (12 ± 2,5 mm) por media ponderada por la inversa de la varianza (`fuseVertex`).
6. **Plano de medida en G.** `ZL = Z_G − 3,0 − v − t̄/2` y `rf = v + t/2 + 13,5`. De aquí salen monoculares, alturas y montura.
7. Se informa también de las monoculares «ajustadas»: las de G reescaladas para que sumen la DIP de N.

**Sensibilidad.** Con un 0,8 % de error en A, el error del vértice es de unos ±8 mm a −1 D, ±2 mm a −4 D y ±1 mm a −8 D.

## 4 bis. Método montura (plantilla en la pantalla)

**Calibración de la pantalla** (una vez por equipo): el usuario ajusta una barra hasta que mide L mm con una regla. `k = px_CSS / L` (px CSS por mm). Se guarda con `screen.width/height` y `devicePixelRatio`; si cambian, se pide recalibrar.

**Plantilla**: la montura se apoya con el frente contra la pantalla y las varillas hacia el usuario (OD a la derecha). Seis líneas en mm desde el centro (`tplFromLines`):

```
W = oR − oL            (ancho exterior, a la altura de los centros de las lentes)
A_OI = nL − tL,  DBL = nR − nL,  A_OD = tR − nR      (borde interior del aro, opcional)
DNC = DBL + (A_OD + A_OI)/2
```

Son proyecciones frontales, igual que la foto, así que no hace falta corregir el galbe para la escala.

**Foto**: además de las cajas, se busca el borde exterior del aro (`detectOuterEdge`) desde el lado temporal de cada caja hacia fuera, a la altura de su centro:

- perfil de intensidad promediado en una banda de ±1,2 mm, derivada con semiancho 0,25 mm;
- se toma el pico de polaridad contraria al borde interior (aro → piel o fondo) entre 0,4 y 14 mm, con preferencia por los cercanos y, si hay plantilla con cajas, por la distancia esperada `(W − A_OD − A_OI − DBL)/2` (σ = 1,5 mm);
- posición subpíxel por el centroide del pico (la derivada de un escalón es una meseta).

**Escala** (`frameScaleZ`). Dos estimaciones de la distancia cámara → plano de la lente:

```
Z_ext  = f · W / W_px − off,      off = (W − DNC)/2 · sen(galbe)     (o pOuterOff)
Z_caja = f · DNC / DNC_px         (DNC_px entre centros de las cajas: no depende de la ranura)
```

Se combinan por la inversa de la varianza relativa:

- `σ_ext² = (0,5/W)² + (1,0·ss/W_px)² + (1,5/Z)²`
- `σ_caja² = (0,5/DNC)² + (0,7·ss/DNC_px)²`

Si `|Z_ext − Z_caja|/Z > 2,5·√(σ_ext² + σ_caja²)`, se avisa. A partir de Z, todo sigue como en el método tarjeta (§2 y §5).

## 4 ter. Ráfaga apilada

1. Se capturan 8 fotogramas. Referencia: entre los de nitidez ≥ 80 % de la máxima y sin parpadeo, el de menor `|giro| + |ladeo| + 0,5·|cabeceo|`.
2. Registro (`registerShift`) en dos zonas, una por ojo (±0,3·DIP_px × ±0,2·DIP_px, con el aro): búsqueda entera por NCC (±3 px alrededor de lo que indican los puntos faciales) y Lucas–Kanade de traslación con compensación del brillo medio. Precisión < 0,05 px en las pruebas.
3. Con los dos desplazamientos se obtiene una semejanza `z' = a·z + b` (`similarity2`). Se descartan los fotogramas con NCC < 0,9, nitidez < 60 %, parpadeo, |escala − 1| > 2 % o giro > 1°.
4. Con 3 o más fotogramas válidos se promedian (`stackRGBA`) en la zona de las gafas con remuestreo ×2 (píxel *j* ↔ `(j + 0,5)/2 − 0,5`); el resto de la imagen es la referencia ampliada. El ruido baja ≈ 1/√N.
5. En la incertidumbre, los errores de localización se expresan en píxeles de la cámara (`× ss`).

## 5. Montura (boxing)

**Contorno de cada lente** (`detectLensContour`):

- Gradiente radial muestreado alrededor de la pupila: 144 ángulos y un paso de radio de 0,2 mm, entre 4 y 40 mm.
- El radio mínimo es una elipse que deja fuera el ojo: ±16 mm en horizontal, 7,5 mm arriba y 13 mm abajo.
- Programación dinámica de camino cerrado, con sesgo hacia el interior, penalización de suavidad y la intensidad de borde recortada a 1 (para que el sesgo interior decida los empates).
- Segunda pasada con **polaridad constante**.
- Búsqueda del **borde interior** del aro, de polaridad opuesta, hacia dentro.
- Refinado subpíxel del radio.
- Si el sector inferior es débil (nylon, al aire), se recalcula solo el arco superior y se marca `bottomWeak`.

**Recuadro.** Se toman los extremos del contorno en coordenadas giradas por `tau`, la inclinación de la montura: la recta entre centroides de las lentes, o la de las pupilas si falla. Comprobación de plausibilidad: A entre 34 y 70 mm, B entre 20 y 60 mm, y la pupila a más de 7 mm del borde superior y a más de 11 mm del inferior.

**Medidas**, con la ranura sumada según el montaje (§ CLAUDE.md):

- `A = |t−n|·s / cos(galbe)`.
- `B = (bot−top)·s / cos(panto)`.
- `DBL` = distancia entre lados nasales.
- `DNC = DBL + (A_OD + A_OI)/2`.
- Descentramiento horizontal = `DNC/2 − mono` (+ hacia nasal). Descentramiento vertical = `altura − B/2`.
- `ED = 2 · radio máximo del contorno` respecto al centro del recuadro (si no hay contorno, `0,95·√(A²+B²)`).
- Diámetro mínimo de lente = `ED + 2·|descentramiento H| + 2`.

**Clasificación** (`rimAnalysis`, `classifyFrame`, `padAnalysis`):

- Contraste entre el aro (0,3–1,2 mm por fuera del borde interior) y el interior de la lente, por sectores (superior, inferior, lados). Grosor visible del aro.
- Umbral `T = max(14, 0,15·dispersión)`.

| Aro arriba | Aro abajo | Montaje |
|---|---|---|
| Sí | Sí | Aro completo: pasta si el grosor ≥ 2 mm, metálico si no |
| Sí | No | Ranurado (nylon) |
| No | No | Al aire |

- **Bisel**: se asigna según el montaje (V / mini‑bisel / canto con ranura / canto plano taladrado).
- **Plaquetas**: se mira la fracción de material del aro en el flanco nasal (puente de acetato apoyado) frente a bordes y brillos pequeños, comparados con la mejilla.

## 6. Incertidumbre

Suma cuadrática de las perturbaciones (`solveWithUnc`):

- FOV: ±4 % (ficha técnica), ±15 % (estimado), ±3 % (calibrado).
- Método montura: W ±0,5 mm, DBL ±0,5 mm, bordes exteriores ±0,7 px y su profundidad ±1,5 mm.
- Centros del iris ±0,4 px; radios ±0,2 px; lados del recuadro ±0,7 px; borde de la tarjeta ±0,7 px.
- Vértice previo ±2,5 mm; HVID ±0,45 mm (±0,1 si lo introduce el usuario).
- k ± su desviación típica; curva base ±1,5 D y espesor ±0,5 mm.

Se añaden los términos de postura `rf · sin(|giro| + 0,5°)` para las monoculares y `rf · sin(|cabeceo| + 1°)` para las alturas.
