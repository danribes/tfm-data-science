# Catálogo de preguntas: qué se le puede preguntar al modelo

Guía de lo que este sistema sabe responder, para hacerse una idea de qué es,
qué puede hacer y qué esperar. Cada bloque trae **preguntas de ejemplo**, una
**respuesta real** del sistema (los números salen de sus cálculos, no de este
texto) y **qué esperar** (incluidos los límites).

Se puede preguntar de tres formas: por el **panel interactivo**
(tfm-data-science-…streamlit.app), por el **asistente de texto**
(`python3 app/rag_assistant.py "..."`, que responde con citas), o mirando los
datos finales en `storage/gold/`.

Una idea que atraviesa todo: **el sistema no adivina el futuro incierto — lo
convierte en escenarios.** Donde una variable no se puede prever (salarios,
tipos de interés, política), la pone como palanca que fija el usuario y devuelve
la consecuencia. Donde sí se puede (la demografía), la proyecta.

---

## 1. Vivienda: precio, asequibilidad y esfuerzo

**Preguntas de ejemplo**
- ¿Cómo evolucionará la asequibilidad de la vivienda en mi comunidad hasta 2027?
- ¿Mejora si los salarios suben un 4 %?
- ¿Cuánto del sueldo se lleva hoy una hipoteca tipo?

**Respuesta real** — el esfuerzo de una hipoteca media nacional es hoy el
**41,6 % del salario bruto** (Baleares 60,6 %). El indicador de asequibilidad
pasa de 1,26 (2024) a **1,64 en 2027** con salarios al 2 % — y sigue
empeorando incluso con salarios al 4 % (1,53). La vivienda no se abarata sola.

**Qué esperar**: un pronóstico con banda de incertidumbre, no un número exacto;
y la advertencia de que el indicador es aproximado (así lo pidió el tutor).

## 2. Suelo edificable

**Preguntas de ejemplo**
- ¿Cuánto suelo urbanizable hay por comunidad y cómo evoluciona?
- ¿Se construye poco por falta de suelo?

**Respuesta real** — Murcia lidera (21,2 % de su superficie estudiada es
urbanizable); Madrid incluso lo reduce. El mercado de suelo se mueve hoy a
**un quinto** de su máximo de 2004 — el cuello de botella empieza antes de los
permisos de obra.

**Qué esperar**: comparación entre territorios y evolución; se compara en
porcentajes porque las dos "fotos" (2021 y 2025) no cubren los mismos
municipios (declarado).

## 3. Historia del gasto y los ingresos públicos (1703–2025)

**Preguntas de ejemplo**
- ¿Cuánto gastaba e ingresaba España hace un siglo?
- ¿Cuándo se construyó el Estado del bienestar español?

**Respuesta real** — gasto público: **11 % del PIB en 1900**, 29 % en 1977,
44 % en 1995, 49 % en el pico de 2012. La gran transformación fue 1977–1995
(+15 puntos en 18 años). El déficit crónico nace con el Estado del bienestar,
no antes.

**Qué esperar**: series largas empalmadas de fuentes distintas, con la "trampa"
de que las series antiguas a veces miden solo el Estado central (medida y
corregida).

## 4. En qué se gasta y de dónde sale el dinero (89–195 países)

**Preguntas de ejemplo**
- ¿Cuánto dedica España a sanidad, pensiones, defensa…?
- ¿De qué impuestos vienen los ingresos?
- ¿Usamos los valores correctos?

**Respuesta real** — España 2023: ingresos 41,2 % del PIB = impuestos 23,6
(el IRPF, 8,7, triplica al de sociedades, 2,9) + cotizaciones 13,2 + resto.
Gasto 2024: protección social 18,7, sanidad 6,3. Y una comprobación: tres
fuentes independientes coinciden función a función (15 de 15 controles).

**Qué esperar**: desglose por función y por tipo de impuesto, contrastado entre
fuentes — pensado precisamente para verificar que los valores son correctos.

## 5. ¿Qué compra el dinero público? (salud, educación, bienestar)

**Preguntas de ejemplo**
- ¿Qué países obtienen más salud por su gasto?
- ¿España rinde por encima o por debajo de lo esperado?

**Respuesta real** — España tiene **+2,7 años** de esperanza de vida por encima
de lo que predice su renta y su gasto (dentro de su banda; no es una "liga").
Entre países, lo que más explica la salud y la caída de la pobreza es la
**renta**, más que el gasto público en sí.

**Qué esperar**: un gráfico de "quién rinde mejor a renta comparable" con banda
de incertidumbre — nunca un ranking de ganadores y perdedores.

## 6. Deuda pública: escenarios (2024–2050 y hasta 2070)

**Preguntas de ejemplo**
- ¿Dónde acaba la deuda en 2050 según la política?
- ¿Y si los tipos suben al 5 %? ¿Y sin envejecimiento?

**Respuesta real** — deuda 2050: **224 %** del PIB por defecto; 156 con
consolidación de +2,5 puntos; 275 con tipos al 5 %; y solo **127 sin el
envejecimiento** de la población. A 2070, la banda central es 409 % (entre 272
y 618). La demografía manda por encima de cualquier palanca fiscal.

**Qué esperar**: el usuario mueve las palancas (tipos, crecimiento, ajuste
fiscal) y el sistema devuelve la senda. Es un mapa de consecuencias, no un
pronóstico; a 50 años, un abanico ancho — y esa anchura es el mensaje.

## 7. Bienestar y pobreza a largo plazo

**Preguntas de ejemplo**
- Si la renta crece un 1 % al año, ¿cuánto baja la mortalidad infantil a 2050?
- ¿Se puede predecir la pobreza infantil?

**Respuesta real** — con crecimiento del 1 %, la mortalidad infantil baja
**~12 % a 2050** frente a la senda base. La pobreza RELATIVA no depende del
ciclo económico (dato medido y contraintuitivo), sino de las transferencias:
en España quitan ~9 puntos de pobreza infantil; sin ellas subiría del 34 % al
**42,5 %**.

**Qué esperar**: escenarios condicionales a una palanca (crecimiento,
transferencias), con su magnitud medida — no una profecía.

## 8. Preguntas globales de economía

**Preguntas de ejemplo**
- ¿Es predecible la renta de un país (en paridad de poder adquisitivo)?
- ¿Los países pobres alcanzan a los ricos?

**Respuesta real** — la renta es muy predecible como nivel, poco como
crecimiento año a año. Sí hay convergencia (verificada con cuatro pruebas
independientes), pero es de **club**: los países ricos y medios convergen entre
sí; los más pobres no. Y es lentísima (media-vida ~147 años). "Los pobres
alcanzan a los ricos" está sobredimensionado.

**Qué esperar**: respuestas con matiz y verificadas de forma adversarial; el
sistema distingue lo que es real de lo que suena bien.

## 9. Señales que se adelantan (indicadores tempranos)

**Preguntas de ejemplo**
- ¿Qué anticipa las subidas del precio de la vivienda?

**Respuesta real** — la **aceleración de la población** anticipa el precio unos
2,5 años; las hipotecas, un trimestre. La aceleración de población es la señal
del "shock de demanda" que los modelos habituales no ven venir.

**Qué esperar**: correlaciones adelantadas honestas, con el aviso de que un
uso predictivo real exige validarlas con datos futuros.

## 10. Comparación internacional de vivienda

**Preguntas de ejemplo**
- ¿España está cara comparada con otros países?
- ¿Urbanizar más abarata la vivienda?

**Respuesta real** — España va por la senda portuguesa (precios muy al alza),
no la italiana (plana). Y el dato incómodo: España es de las que más suelo ha
urbanizado (+120 % desde 2000) y aun así el precio/renta sigue alto —
**urbanizar más no compra asequibilidad** (correlación casi nula en 40 países).

## 11. Preguntas normativas ("¿qué habría que recortar…?")

**Preguntas de ejemplo**
- ¿Qué hay que recortar para bajar los impuestos al 10 % del PIB?

**Respuesta real** — el sistema **no prescribe**: reformula. Un Estado del 10 %
implica recortar ~el 78 % del gasto actual; ni eliminando todo el Estado del
bienestar se llega. Contexto: España tuvo ese "Estado del 10 %" en 1900. La
elección es política; el sistema pone el precio.

**Qué esperar**: ante una pregunta política, no una recomendación, sino la
magnitud real de lo que implica — y la elección devuelta a quien pregunta.

## 12. Preguntas sobre el propio método (para el tribunal)

**Preguntas de ejemplo**
- ¿Por qué el modelo sencillo gana a los sofisticados?
- ¿Qué aporta esto que no daría una inteligencia artificial de texto?

**Respuesta real** — cinco modelos sofisticados compitieron contra el más
simple y ninguno lo superó de forma fiable; una vez ese rigor evitó anunciar un
desplome falso. Y en una prueba directa, una IA de texto sin el sistema acierta
**3 de 12** preguntas; con los cálculos del sistema, **11 de 12**.

**Qué esperar**: el sistema puede explicar y defender sus propias decisiones,
con la evidencia en el repositorio.

---

## Qué NO hace el sistema (y por qué es una virtud)

- **No da un número exacto del futuro incierto**: da escenarios con su banda.
- **No prescribe políticas**: pone precio a cada opción y devuelve la elección.
- **No inventa cifras**: si el asistente de texto no encuentra el dato en los
  cálculos del sistema, no se lo inventa (a diferencia de una IA a secas).
- **No esconde sus límites**: cada respuesta trae su incertidumbre y su
  advertencia de método.

## Cómo preguntar en la práctica

| Vía | Para qué | Cómo |
|---|---|---|
| Panel interactivo | Explorar escenarios visualmente | La demo en internet, 5 pestañas |
| Asistente de texto | Preguntar en lenguaje natural con citas | `python3 app/rag_assistant.py "tu pregunta"` |
| Datos finales | Ver los números en bruto | Ficheros de `storage/gold/` |

Referencias por tema: `docs/Guia de Uso.md` (escenarios), `docs/horizonte_50.md`
(largo plazo), `docs/bienestar_indicadores.md` (bienestar/pobreza),
`docs/fiscal_breakdown.md` (gasto e ingresos), `docs/glosario.md` (siglas).
