# Guía de usuario

Todo lo necesario para usar el sistema: cómo funciona el panel, qué preguntas admite, la capa de aprendizaje automático explicada, cómo desplegarlo y el glosario de siglas.

## Contenido

- [Guía de uso — dashboard, escenarios y capacidad de predicción](#guía-de-uso-dashboard-escenarios-y-capacidad-de-predicción)
- [Catálogo de preguntas: qué se le puede preguntar al modelo](#catálogo-de-preguntas-qué-se-le-puede-preguntar-al-modelo)
- [Guía de aplicaciones ML/DL y del tooling con Claude](#guía-de-aplicaciones-mldl-y-del-tooling-con-claude)
- [Despliegue y operación del producto (2026-07-19)](#despliegue-y-operación-del-producto-2026-07-19)
- [Asistente RAG — "el LLM narra; el sistema calcula"](#asistente-rag-el-llm-narra-el-sistema-calcula)
- [Glosario de siglas y acrónimos](#glosario-de-siglas-y-acrónimos)

---

## Guía de uso — dashboard, escenarios y capacidad de predicción

Cómo se usa la interfaz del proyecto y qué devuelve el modelo cuando el usuario
plantea escenarios. Todos los números de esta guía son salidas REALES del
sistema (capa gold + motor D1), no ilustrativos.

**Demo pública:** https://tfm-data-science-ufgfhpcvydyrswwzm7t6sz.streamlit.app/
**Local:** `docker compose up --build` → dashboard en `localhost:8501`, API en `localhost:8010`.

### Principio que gobierna la interfaz

El sistema **no adivina el futuro incierto: lo pone como palanca del usuario**.
Donde una variable es imprevisible (salarios, tipos, crecimiento), no se
pronostica — se pregunta "¿y SI vale X?" y se devuelve la consecuencia
calculada. Donde una variable es predecible (demografía), sí se proyecta. Cada
respuesta lleva su banda de incertidumbre y su límite de método. Detalle
conceptual en `docs/METODOLOGIA.md`.

---

### Las cinco pestañas

#### 🏠 1. Asequibilidad CCAA — pronóstico con escenarios salariales
- **Controles**: territorio (17 CCAA + Nacional) · escenario salarial (0 %, 2 %, 4 %).
- **Devuelve**: el IPV histórico + el abanico empírico 2026–2027 (bandas 80/95 %)
  y el ratio de asequibilidad proyectado bajo el crecimiento salarial elegido.
- **Cómo leerlo**: el salario mueve el RATIO (esfuerzo), no el precio. La banda,
  no el punto, es la parte informativa.

#### 🗺️ 2. Atlas fiscal
- **Control**: selector de figura (B1–B19).
- **Devuelve**: España frente a la mediana mundial/UE en gasto, deuda, sanidad,
  pensiones, vivienda pública vs residencial total, suelo, historia 1703–2025.

#### ⚕️ 3. Rendimiento A1
- **Devuelve**: funnel de 164 países (residual de esperanza de vida ~ gasto
  sanitario) con banda conformal por cuartil de renta. **No es un ranking**:
  solo importan los países fuera de su banda.

#### 📉 4. Deuda: escenarios D1 — el simulador interactivo
- **Palancas (sliders)**: tipo de mercado (2–6 %) · crecimiento real (0–3 %) ·
  ajuste del saldo primario (−2 a +4 pp) · presión demográfica on/off.
- **Devuelve**: "TU SENDA" de deuda 2024–2050 sobre el menú de escenarios base.

#### 🔭 5. Horizonte 50 años
- **Controles**: escenario de deuda (Monte Carlo) · horizonte de bienestar (2050/2070).
- **Devuelve**: el abanico probabilístico de deuda a 2070 (bandas 50/90 %) y los
  sobres de mortalidad infantil según crecimiento, con la calibración histórica
  (~13 pp) al pie.

---

### Ejemplos de preguntas y la respuesta del modelo

Cada bloque = una pregunta en lenguaje natural, el escenario que fija el usuario,
y la estimación REAL que devuelve el sistema.

#### A. Asequibilidad de la vivienda (pestaña 1)

> **"¿Cómo evoluciona la asequibilidad nacional hasta 2027 según lo que suban los salarios?"**

| Escenario del usuario | Ratio de asequibilidad 2027Q4 (2024 = 1,26) |
|---|---|
| Salarios +0 %/año | **1,77** |
| Salarios +2 %/año (central) | **1,64** |
| Salarios +4 %/año | **1,53** |

Lectura del modelo: aun con salarios subiendo un 4 %, el ratio empeora respecto
a 2024 — la asequibilidad no se corrige sola por la vía salarial. (Indicador
aproximado de evolución relativa; el modelo de producción es el drift, ganador
del protocolo completo.)

#### B. Sostenibilidad de la deuda a 2050 (pestaña 4 / `POST /scenario`)

> **"¿Dónde acaba la deuda pública en 2050 según la política que se elija?"**

| Palancas del usuario | Deuda 2050 (% PIB) |
|---|---|
| Por defecto (tipo 3,5 · crec. 1,3 · sin ajuste) | **224** |
| Consolidación +2,5 pp de saldo primario | **156** |
| Crecimiento real 2,5 % | **184** |
| Tipos al 5 % | **275** |
| Sin presión demográfica (contrafactual) | **127** |

Lectura del modelo: **la demografía domina cualquier palanca individual**
(224 con envejecimiento vs 127 sin él = 97 pp); ninguna palanca aislada
estabiliza la senda. Determinista, sin retroalimentaciones: mapa de
sensibilidades, no pronóstico.

#### C. Deuda a largo plazo con incertidumbre (pestaña 5, Monte Carlo)

> **"¿Y si miramos a 2070, con la incertidumbre de los parámetros?"**

| Escenario | 2050 mediana [banda 90 %] | 2070 mediana [banda 90 %] |
|---|---|---|
| Central | 231 [178–302] | **409 [272–618]** |
| Consolidación +2,5 pp | 172 [121–235] | 298 [174–482] |
| Crecimiento alto | 196 [150–256] | 321 [214–481] |
| Tipos altos | 264 [203–344] | 518 [345–784] |

Lectura del modelo: el ancho de la banda ES el mensaje. Condicional a
continuidad institucional; la calibración histórica dice que ningún sobre a
50 años puede ser más estrecho de ~13 pp de PIB.

#### D. Bienestar social a 50 años (pestaña 5, sobres)

> **"¿Cuánto bajaría la mortalidad infantil según el crecimiento de la renta?"**

| Crecimiento (renta pc/año) | Δ mortalidad <5 en 2050 | en 2070 |
|---|---|---|
| Estancamiento 0,5 % | −6,4 % [−7,8, −5,0] | −11,0 % |
| Central 1,0 % | −12,3 % [−14,9, −9,7] | −20,8 % |
| Dinámico 1,5 % | −17,9 % [−21,5, −14,2] | −29,4 % |

Lectura del modelo: **el crecimiento de la renta domina**; subir la capacidad
fiscal ±2,5 pp añade solo ±0,8 % (efecto estructural real, a 8 años de retardo,
pero de segundo orden). Variación relativa a la senda base — la mejora secular
mundial no se extrapola.

#### E. Preguntas normativas — el sistema reformula, no prescribe

> **"¿Qué habría que recortar para bajar la presión fiscal al 10 %?"**

El sistema no responde "recorta X". Devuelve la magnitud: un Estado del 10 %
de ingresos implica recortar ~el 78 % del gasto actual (35 pp de PIB); ni
eliminando TODO el Estado del bienestar (29 pp) se llega. Contexto histórico:
España tuvo ese "Estado del 10 %" en 1900. La elección es política; el sistema
pone el precio (ver stress test, `docs/RESULTADOS_FISCAL_BIENESTAR.md`).

---

### Usar el motor por API (para reproducir los números)

El simulador de deuda es un endpoint. Palancas en el cuerpo JSON:

```bash
curl -X POST localhost:8010/scenario -H "Content-Type: application/json" -d '{
  "r_mercado": 3.5,      # tipo de mercado %
  "g_real": 1.3,         # crecimiento real %
  "pb_palanca_pp": 2.5,  # ajuste permanente del saldo primario, pp
  "con_demografia": true,
  "hasta": 2050
}'
```

Devuelve la senda año a año (`deuda`, `pb`, `r_efectivo`) con la nota "mapa de
sensibilidades, no pronóstico". Otros endpoints:
`/forecast/ccaa/{territorio}` (abanico), `/performance/health` (funnel A1),
`/scenarios/debt` (menú), `/project/{pensions|health}` (elasticidades).

### Preguntar en lenguaje natural — el asistente RAG

```bash
python3 app/rag_assistant.py "¿Qué pasa con la deuda si los tipos suben al 5%?"
```

Responde con pasajes citados de la documentación del proyecto.
Con `--llm` redacta la respuesta a partir SOLO de esos pasajes (motor `gemini`
por defecto, con reserva automática a `glm` y `mimo`), con cita por afirmación;
sin clave, devuelve los pasajes tal cual.

---

### Qué NO hace el sistema (y por qué es una virtud)

- **No da un número puntual del futuro incierto**: da sobres condicionales al
  escenario que fija el usuario.
- **No prescribe políticas**: pone precio a cada opción y devuelve la elección.
- **No oculta su incertidumbre ni sus límites**: cada respuesta lleva su banda
  y su advertencia de método. El sistema dice lo que no sabe con la misma
  claridad que lo que sabe. *El LLM narra; el sistema calcula.*

---

## Catálogo de preguntas: qué se le puede preguntar al modelo

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

### 1. Vivienda: precio, asequibilidad y esfuerzo

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

### 2. Suelo edificable

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

### 3. Historia del gasto y los ingresos públicos (1703–2025)

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

### 4. En qué se gasta y de dónde sale el dinero (89–195 países)

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

### 5. ¿Qué compra el dinero público? (salud, educación, bienestar)

**Preguntas de ejemplo**
- ¿Qué países obtienen más salud por su gasto?
- ¿España rinde por encima o por debajo de lo esperado?

**Respuesta real** — España tiene **+2,7 años** de esperanza de vida por encima
de lo que predice su renta y su gasto (dentro de su banda; no es una "liga").
Entre países, lo que más explica la salud y la caída de la pobreza es la
**renta**, más que el gasto público en sí.

**Qué esperar**: un gráfico de "quién rinde mejor a renta comparable" con banda
de incertidumbre — nunca un ranking de ganadores y perdedores.

### 6. Deuda pública: escenarios (2024–2050 y hasta 2070)

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

### 7. Bienestar y pobreza a largo plazo

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

### 8. Preguntas globales de economía

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

### 9. Señales que se adelantan (indicadores tempranos)

**Preguntas de ejemplo**
- ¿Qué anticipa las subidas del precio de la vivienda?

**Respuesta real** — la **aceleración de la población** anticipa el precio unos
2,5 años; las hipotecas, un trimestre. La aceleración de población es la señal
del "shock de demanda" que los modelos habituales no ven venir.

**Qué esperar**: correlaciones adelantadas honestas, con el aviso de que un
uso predictivo real exige validarlas con datos futuros.

### 10. Comparación internacional de vivienda

**Preguntas de ejemplo**
- ¿España está cara comparada con otros países?
- ¿Urbanizar más abarata la vivienda?

**Respuesta real** — España va por la senda portuguesa (precios muy al alza),
no la italiana (plana). Y el dato incómodo: España es de las que más suelo ha
urbanizado (+120 % desde 2000) y aun así el precio/renta sigue alto —
**urbanizar más no compra asequibilidad** (correlación casi nula en 40 países).

### 11. Preguntas normativas ("¿qué habría que recortar…?")

**Preguntas de ejemplo**
- ¿Qué hay que recortar para bajar los impuestos al 10 % del PIB?

**Respuesta real** — el sistema **no prescribe**: reformula. Un Estado del 10 %
implica recortar ~el 78 % del gasto actual; ni eliminando todo el Estado del
bienestar se llega. Contexto: España tuvo ese "Estado del 10 %" en 1900. La
elección es política; el sistema pone el precio.

**Qué esperar**: ante una pregunta política, no una recomendación, sino la
magnitud real de lo que implica — y la elección devuelta a quien pregunta.

### 12. Preguntas sobre el propio método (para el tribunal)

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

### Qué NO hace el sistema (y por qué es una virtud)

- **No da un número exacto del futuro incierto**: da escenarios con su banda.
- **No prescribe políticas**: pone precio a cada opción y devuelve la elección.
- **No inventa cifras**: si el asistente de texto no encuentra el dato en los
  cálculos del sistema, no se lo inventa (a diferencia de una IA a secas).
- **No esconde sus límites**: cada respuesta trae su incertidumbre y su
  advertencia de método.

### Cómo preguntar en la práctica

| Vía | Para qué | Cómo |
|---|---|---|
| Panel interactivo | Explorar escenarios visualmente | La demo en internet, 5 pestañas |
| Asistente de texto | Preguntar en lenguaje natural con citas | `python3 app/rag_assistant.py "tu pregunta"` |
| Datos finales | Ver los números en bruto | Ficheros de `storage/gold/` |

Referencias por tema: `docs/GUIA_USUARIO.md` (escenarios), `docs/RESULTADOS_FISCAL_BIENESTAR.md`
(largo plazo), `docs/RESULTADOS_FISCAL_BIENESTAR.md` (bienestar/pobreza),
`docs/RESULTADOS_FISCAL_BIENESTAR.md` (gasto e ingresos), `docs/GUIA_USUARIO.md` (siglas).

---

## Guía de aplicaciones ML/DL y del tooling con Claude

Dos capas distintas y complementarias:
1. **El ML/DL DENTRO del modelo** — qué técnica se usa en cada módulo, con qué
   resultado, y bajo qué regla se acepta o rechaza.
2. **El tooling con LLM (Claude + motores)** — cómo se usan los grandes modelos
   de lenguaje para HACER y OPERAR el sistema de forma más eficiente, sin que
   nunca sean la fuente de los números.

Principio que separa las dos capas: **el LLM narra; el sistema calcula.** Los
números salen siempre de código y datos con trazabilidad, nunca del texto de un
LLM. Detalle en `MEMORIA.md` §4.6 y `docs/METODOLOGIA.md`.

---

### Parte 1 — El ML/DL dentro del modelo

#### Mapa de técnicas por módulo

| Módulo | Técnica ML/DL | Librería | Papel | Veredicto bajo protocolo |
|---|---|---|---|---|
| T1 baseline | Drift (persistencia con deriva) | numpy | **Campeón de producción** | MASE h≤4 = **0,40** |
| T1 candidato | SARIMAX (± exógena Euríbor) | statsmodels | Retador clásico | 1/17 · 0/17 — no adoptado |
| T1 candidato | LightGBM (Gradient Boosting) | lightgbm | Retador flexible | 0/17 (0,666) — no adoptado |
| T1 candidato | LightGBM + capas de demanda | lightgbm | Retador con features | 0/17 (0,653) — no adoptado |
| T1 candidato | **Chronos-Bolt (modelo fundacional)** | chronos (PyTorch) | DL preentrenado zero-shot | 0/17 (0,460) — no adoptado |
| T1 candidato | **DL global (MLP sobre 1.760 series)** | PyTorch | Red entrenada en booms extranjeros | **empate técnico 0,401**, 7/17 — no adoptado |
| A1 salud/edu/bienestar | OLS vs LightGBM vs MLP | sklearn/lightgbm | Frontera gasto→resultado | **OLS gana 5/5** |
| A2 tipologías | PCA + KMeans | sklearn | Composición del gasto | clusters débiles (silueta 0,20) |
| Motor de proyección | Regresión con FE + errores CR1 (cluster) | numpy | Elasticidades demográficas | β65 pensiones 0,91±0,19 |
| Frontera 50 años | Panel within (FE país+año, CR1) | numpy | Efecto ingreso→bienestar | β retardo 8 = −0,0036±0,0015 |
| D1 horizonte | Monte Carlo (4.000 trayectorias) | numpy | Propagar incertidumbre de parámetros | banda 2070 [272–618] |
| Incertidumbre | Intervalos conformal por cuartil | numpy | Bandas con cobertura comprobable | funnel A1, abanico T1 |
| Validación | LOOCV, rolling-origin, test de un solo uso | sklearn/propio | Selección honesta | 5 contests, todos negativos |
| Asistente | TF-IDF + similitud coseno | sklearn | Recuperación del corpus | RAG offline |

#### La lección central: el ML/DL potente perdió, y eso es el resultado

Cinco veces un modelo flexible o profundo compitió contra una alternativa
simple bajo reglas fijadas ANTES de mirar. Ninguno se adoptó. El mejor (el DL
global entrenado con ciclos inmobiliarios extranjeros) llegó al empate técnico
(0,401 vs 0,395) y ganó a un solo horizonte — insuficiente para la regla de
12/17 CCAA, que no se relajó. En las fronteras transversales, el OLS ganó las
cinco veces al GBM y al MLP.

**Por qué**: con ~150–200 países o una ventana de validación sin giros de
ciclo, la señal la captura la estructura simple; más capas añaden varianza, no
información. El DL solo mostró valor donde tenía un corpus de DOMINIO grande
(1.760 series extranjeras con crisis reales) — la pista de que el cuello de
botella era el dato, no la arquitectura. Detalle: `docs/RESULTADOS_VIVIENDA.md`.

#### Dónde el DL SÍ aporta (declarado, no fingido)

- **Modelos fundacionales** (Chronos): útiles como retador de coste cero;
  se integran en la misma parrilla y se juzgan igual.
- **Corpus de dominio grande** (ruta 1 DL): la única vía con evidencia
  direccional de que puede anticipar un giro; revalidable solo con datos 2026+.
- **La frontera del DL real** (CNN sobre luces nocturnas para PIB sin datos)
  queda declarada como extensión bloqueada por infraestructura, no simulada.

---

### Parte 2 — El tooling con LLM (Claude y motores)

Los LLM NO producen números del modelo. Se usan en tres papeles de eficiencia:

#### 2.1 El asistente RAG del proyecto (`app/rag_assistant.py`)

Recuperación aumentada sobre los 37 documentos del propio proyecto.

- **Sin clave** (modo por defecto): devuelve los pasajes citados más relevantes
  (TF-IDF), sin red. Determinista, auditable.
- **`--llm`**: un LLM redacta la respuesta a partir SOLO de esos pasajes, con
  cita por afirmación y reformulación de lo normativo. Motores configurables:

| Motor | Modelo | Endpoint | Nota |
|---|---|---|---|
| `gemini` (defecto) | gemini-2.5-pro | generativelanguage.googleapis.com | El más fiel+rápido+consistente en el benchmark de grounding |
| `glm` (reserva) | glm-5.2 | api.z.ai (Coding Plan) | Reserva automática 1 |
| `mimo` (reserva) | mimo-v2.5-pro | xiaomimimo | Reserva automática 2 |
| `kimi` | kimi-k2.6 | api.moonshot.ai | Sin "tasa de razonamiento" |
| `kimi-k3` | kimi-k3 | api.moonshot.ai | Razonador (más presupuesto) |

Si el motor primario (gemini) falla o devuelve vacío, el asistente cae
automáticamente a `glm` y luego a `mimo` (los dos más parecidos: fieles,
rápidos, sin impuesto de razonamiento), anotando qué motor respondió.

Uso:
```bash
python3 app/rag_assistant.py "¿Por qué el drift gana a los modelos de ML?"
python3 app/rag_assistant.py --llm --engine kimi "Resume el sistema a 50 años"
```
Regla estricta del prompt: solo números que aparezcan textualmente en los
pasajes; nunca inventa cifras; si la pregunta es normativa, reformula.

#### 2.2 Claude como herramienta de proceso (construcción)

Declarado en la memoria (uso de IA): el LLM se usó para escribir código,
redactar documentación y explorar diseño — nunca como fuente de datos ni de
resultados. Cada número del repositorio es reproducible desde `analysis/` sin
ningún LLM en el camino.

#### 2.3 Consejo de LLMs para decisiones de diseño (segunda opinión)

Para decisiones de arquitectura (qué módulos, qué códigos de datos, qué
riesgos) se consultó un consejo de varios LLM y se TRIANGULÓ, verificando cada
afirmación contra las fuentes primarias — porque los LLM se equivocan en
códigos y detalles. Ejemplo real: un consejo recomendó códigos COFOG y ESSPROS,
la verificación pilló 5 códigos erróneos antes de usarlos.

---

### Parte 3 — Ejemplos para sacar el máximo al ML/DL con Claude

Cómo un usuario (o el tribunal) exprime la combinación modelo + LLM. Cada
ejemplo respeta la separación: **el sistema calcula, Claude explica/orquesta.**

#### Ejemplo 1 — Interrogar un resultado del modelo
> Usuario: *"¿Por qué el modelo profundo perdió contra el drift?"*
- El asistente RAG recupera `RESULTADOS_VIVIENDA.md` y explica los cinco contests con sus
  MASE reales, citados. Claude narra; los 0,401/0,395 vienen del gold.

#### Ejemplo 2 — Explorar un escenario y su consecuencia
> Usuario: *"Si los tipos suben al 5 % y no hay consolidación, ¿dónde acaba la deuda?"*
- El motor D1 (`POST /scenario`, `r_mercado=5`) calcula la senda → **275 % en
  2050**. Claude puede envolver la cifra en lenguaje natural, pero el 275 es
  aritmética r−g, no lenguaje.

#### Ejemplo 3 — Pedir un contraste ML honesto sobre datos nuevos
> Usuario: *"He añadido una variable nueva. ¿Bate al drift?"*
- Se enchufa como `forecaster(train,h)` en `backtest_t1.py` y corre la misma
  parrilla pre-registrada. El veredicto es 0–17/17, no una opinión del LLM.
- **Sacar el máximo**: usar Claude para escribir el nuevo `forecaster` y los
  tests; usar el HARNESS para juzgarlo. División de trabajo correcta.

#### Ejemplo 4 — Ampliar el corpus DL (la vía prometedora)
> Usuario: *"¿Mejoraría el DL con más series regionales?"*
- El hallazgo dice que el cuello de botella es el dato. Claude ayuda a escribir
  el conector (p. ej. más países con historia de crisis) → `hpi_regional_global`
  crece → se reentrena el MLP global → se revalida en 2026+. El sistema decide
  si se adopta, no el LLM.

#### Ejemplo 5 — Encadenar predicción condicional (clima→cosecha)
> Usuario: *"Proyecta el bienestar según el crecimiento de la renta."*
- Cadena legítima: crecimiento (palanca) → panel within (γ) → sobre de
  mortalidad con IC95. 2050: crecimiento 1 % → **−12,3 %**. Claude explica la
  cadena; los parámetros y las bandas son del panel.

#### Ejemplo 6 — Auditar la honestidad del sistema
> Usuario: *"Enséñame los tres backtests que el modelo suspendió."*
- El sistema los publica (`RESULTADOS_VIVIENDA.md`, contests). Claude los resume; la
  prueba de que son reales es que están en el repo con sus números, no en la
  memoria de un modelo.

---

### Regla de oro para el usuario

Para exprimir ML/DL + Claude sin engañarse:
1. **Deja calcular al sistema** (motor, harness, gold) — ahí están los números.
2. **Deja narrar y orquestar a Claude** (RAG, código, diseño) — ahí está la
   eficiencia.
3. **Nunca aceptes una cifra de un LLM sin su fuente en el gold.** Si el
   asistente no puede citar el pasaje, la cifra no entra.
4. **Todo candidato nuevo pasa por el protocolo**, gánelo un GBM, un MLP o un
   modelo fundacional. La regla no se relaja para lo que está de moda.

---

## Despliegue y operación del producto (2026-07-19)

Cómo se sirve el sistema, cómo se actualiza y cómo replicarlo. Tres modos
sobre el MISMO código y los MISMOS datos (la capa gold del repo).

### 1. Demo pública (Streamlit Community Cloud) — el modo por defecto

**https://tfm-data-science-ufgfhpcvydyrswwzm7t6sz.streamlit.app/**

- Sirve `app/dashboard.py` (5 pestañas) directamente desde el repo de GitHub.
- **Actualización automática**: cada `git push` a `main` redespliega (webhook
  de Streamlit instalado en el repo). No hay paso manual de publicación.
- Dependencias: `requirements.txt` de la RAÍZ (duplicado de
  `app/requirements.txt` — Streamlit Cloud solo lee la raíz).
- Comportamiento del plan gratuito: la app **duerme** tras ~12 h sin visitas;
  el primer visitante ve "waking up" ~30 s. Ante una demo importante,
  visitarla antes para calentarla.
- El dashboard NO depende de la API ni de claves: lee los CSV gold del propio
  repo. Por eso es desplegable tal cual.

### 2. Local con Docker — la vía de réplica garantizada

```bash
git clone https://github.com/danribes/tfm-data-science
cd tfm-data-science
docker compose up --build
```

- **Dashboard** → http://localhost:8501 · **API** → http://localhost:8010
- Las imágenes son autocontenidas: capa gold y figuras copiadas DENTRO en el
  build. No requiere Python local, ni paquetes, ni descargas de datos, ni red
  tras el build. Único requisito: Docker.
- Un clon antiguo se refresca con `git pull && docker compose up --build`
  (el contenedor queda congelado en el commit del build; la nube no).
- Healthcheck incluido (`/_stcore/health`); parar todo: `docker compose down`.
- Uso previsto además de la réplica: **modo sin-red para la defensa** (si la
  wifi falla, el sistema completo corre del portátil).

### 3. Local sin Docker (desarrollo)

```bash
pip install -r app/requirements.txt && streamlit run app/dashboard.py
cd api && pip install -r requirements.txt && GOLD_DIR=../storage/gold uvicorn main:app --reload
```

### Qué sirve cada superficie

| Superficie | Contenido | Fuente de datos |
|---|---|---|
| Dashboard (nube y contenedor) | 5 pestañas: asequibilidad con abanico empírico, atlas B1–B19, funnel A1, simulador de deuda con palancas, horizonte 50 años (Monte Carlo 2070 + sobres de bienestar + calibración) | CSV de `storage/gold/` leídos en local; sin API, sin claves |
| API FastAPI | `/atlas`, `/century`, `/ccaa/affordability`, `/forecast/ccaa/{t}`, `/performance/health`, `/scenarios/debt`, `POST /scenario`, `/project/{pensions\|health}` | capa gold + `api/models/*.json` (elasticidades, panel bienestar) |
| Asistente RAG (`app/rag_assistant.py`, solo local) | respuestas citadas sobre los 33 documentos del proyecto; `--llm` opcional con clave | `gold_corpus_manifest.csv` |

### Advertencias que viajan con el producto

Cada pestaña y cada endpoint llevan sus límites de método en la propia
respuesta (aproximación del ratio, drift como campeón por protocolo, funnel
no-ranking, aritmética determinista, sobres condicionales y calibración de
~13 pp). Publicar el dashboard no cambia el contrato: el sistema dice lo que
no sabe con la misma claridad que lo que sabe.

### Historial de despliegue (trazabilidad)

- Contenedorización dashboard+API: commit `22e7831`.
- `requirements.txt` raíz para Streamlit Cloud: `484e616`.
- Alta en Streamlit Community Cloud: manual (OAuth del autor), 2026-07-19;
  verificada con render headless (5 pestañas, datos vivos).
- URL en README: `7cff9a6`. Un túnel Cloudflare temporal usado el mismo día
  quedó retirado al entrar la nube.

---

## Asistente RAG — "el LLM narra; el sistema calcula"

*2026-07-19. La extensión de la Entrega 2 ("asistente con IA"), construida DESPUÉS de cerrar el núcleo — exactamente como exigía la regla MVP-primero del tutor. Script: [`app/rag_assistant.py`](../app/rag_assistant.py); tests: [`tests/test_rag.py`](../tests/test_rag.py); manifiesto: `storage/gold/gold_corpus_manifest.csv` (cierra el contrato de la Entrega 3 §4.1 con alcance declarado).*

---

### Diseño

El papel correcto de un LLM en este proyecto quedó fijado en la [memoria §4.6](MEMORIA.md): **interfaz de lenguaje natural SOBRE los artefactos calculados** — nunca fuente de números. El asistente lo implementa con tres decisiones:

1. **Corpus = la documentación del propio proyecto** (memoria, cadena de backtesting, atlas, entregas, análisis; el recuento vivo de pasajes/documentos está en `gold_corpus_manifest.csv`), troceada por encabezados e indexada por TF-IDF (sklearn: determinista, sin red, sin dependencias nuevas). Excluidos `_old/` (planes sustituidos) y `defensa/` (duplica la memoria). El corpus EXTERNO (informes BdE/INE en PDF) sigue siendo la pata futura declarada.
2. **Dos modos**:
   - **Por defecto (sin red, sin clave)**: devuelve los pasajes citados tal cual — la respuesta con su fuente, sin redactar.
   - **`--llm`**: un LLM redacta SOLO a partir de los pasajes recuperados; motor configurable con `--engine`: **kimi** (defecto — Moonshot k2.6, OpenAI-compatible, sin impuesto de razonamiento oculto), **glm** (Z.ai, endpoint del Coding Plan — el general devuelve 429) o **mimo** (Xiaomi). Los tres superaron la misma prueba de grounding con trampa (2026-07-19), con cita [n] por afirmación y la regla dura: *"solo puedes escribir una cifra si aparece textualmente en un pasaje"*. Las preguntas normativas se reencuadran (Bloque D). Sin credenciales/saldo/red degrada limpiamente al modo pasajes.
3. **Testeado offline** (6 tests): corpus sin trivialidades ni duplicados, manifiesto con contrato, y dos consultas doradas ("por qué ganó el drift" → docs del protocolo; "elasticidad pensiones" → pasaje con el 0,91).

### Uso

```
python3 app/rag_assistant.py "¿por qué el modelo de producción es el drift?"
python3 app/rag_assistant.py --llm "¿qué dice el test final?"              # gemini (defecto) con reserva glm/mimo
python3 app/rag_assistant.py --llm --engine glm "¿qué dice el test final?"  # o glm / mimo
python3 app/rag_assistant.py --build                                # regenerar manifiesto
```

### Límites declarados

- TF-IDF léxico: preguntas parafraseadas lejos del vocabulario del corpus pueden no recuperar (mitigable con embeddings locales como siguiente iteración).
- El modo `--llm` requiere la clave del motor elegido en el entorno o `~/.secrets` (`KIMI_API_KEY` / `GLM_API_KEY` / `MIMO_API_KEY`); glm y mimo son razonadores (max_tokens generoso o content vacío), kimi k2.6 no. El modo por defecto no depende de nada externo. Kimi y GLM verificados en vivo: respuestas fieles a los pasajes con citas por afirmación.
- El asistente NO accede a la capa gold numérica directamente: si un número no está en la documentación, la respuesta correcta es "el corpus no lo cubre" — por diseño.

---

## Glosario de siglas y acrónimos

Todas las siglas que aparecen en el repositorio (fuentes de datos, bases,
métodos y códigos de contabilidad nacional). Referencia rápida para lectores
de la memoria, el código y el dashboard.

### Instituciones y fuentes de datos

| Sigla | Nombre completo | Qué aporta al proyecto |
|---|---|---|
| **MITMA** | Ministerio de Transportes, Movilidad y Agenda Urbana (España) | Licencias de vivienda, mercado de suelo, SIU |
| **SIU** | Sistema de Información Urbana (MITMA) | Suelo clasificado como urbanizable, por municipio |
| **INE** | Instituto Nacional de Estadística (España) | IPV, IPC, salarios, compraventas, hipotecas, población |
| **IMF / FMI** | International Monetary Fund / Fondo Monetario Internacional | WEO, GMD, GFS-COFOG, WoRLD |
| **OECD / OCDE** | Organisation for Economic Co-operation and Development | Precios de vivienda, land cover, estadísticas de ingresos |
| **BIS** | Bank for International Settlements | Índices de precios residenciales (ES desde 1971) |
| **ECB / BCE** | European Central Bank / Banco Central Europeo | Euríbor, Bank Lending Survey |
| **BdE** | Banco de España | Serie histórica de criterios de crédito (superada por el BCE) |
| **FHFA** | Federal Housing Finance Agency (EE. UU.) | Índices de precios de vivienda por estado/metro |
| **WHO / OMS** | World Health Organization / Org. Mundial de la Salud | GHED, GHO |
| **UN DESA** | United Nations Dept. of Economic and Social Affairs | Stock internacional de migrantes |
| **JST** | Jordà-Schularick-Taylor (los tres autores) | Macrohistory Database: series fiscales y de precios largas |
| **JMP / JME** | Joint Monitoring Programme / Joint Malnutrition Estimates (OMS-UNICEF) | Agua-saneamiento; stunting-wasting |
| **UIS** | UNESCO Institute for Statistics | Gasto educativo, resultados de aprendizaje |
| **SIPRI** | Stockholm International Peace Research Institute | Gasto militar (vía Banco Mundial) |
| **UNICEF** | United Nations Children's Fund | Marco MODA de pobreza infantil |
| **UNDP / PNUD** | United Nations Development Programme | Coproductor del MPI |
| **OPHI** | Oxford Poverty & Human Development Initiative | Coproductor del MPI |

### Bases de datos y datasets

| Sigla | Nombre completo | Contenido |
|---|---|---|
| **WEO** | World Economic Outlook (FMI) | Totales fiscales + proyecciones, 1800–2031 |
| **GMD** | Global Macro Database (vinculada al FMI) | Deuda/gasto/ingreso/impuestos encadenados % PIB, historia larga |
| **GFS** | Government Finance Statistics (FMI) | Estadísticas de finanzas públicas |
| **COFOG** | Classification of the Functions of Government | Las 10 funciones de gasto (sanidad, educación, defensa…) |
| **WoRLD** | World Revenue Longitudinal Database (FMI) | Ingresos por tipo de impuesto, 195 países, 1980– |
| **WDI** | World Development Indicators (Banco Mundial) | PIB pc, resultados, series de política |
| **GHED** | Global Health Expenditure Database (OMS) | Gasto sanitario público/privado |
| **GHO** | Global Health Observatory (OMS) | Obesidad, tabaquismo (confusores de A1) |
| **WWBI** | Worldwide Bureaucracy Indicators (Banco Mundial) | Empleo y salarios públicos |
| **ODA / AOD** | Official Development Assistance / Ayuda Oficial al Desarrollo | Ayuda donante % RNB |
| **SPI** | Statistical Performance Indicators (Banco Mundial) | Auditoría de capacidad estadística |
| **HLO** | Harmonized Learning Outcomes (Banco Mundial) | Resultados de aprendizaje comparables |
| **HCI** | Human Capital Index (Banco Mundial) | Índice matriz del HLO |
| **BLS** | Bank Lending Survey (BCE) | Endurecimiento de criterios de crédito (NO el Bureau of Labor Statistics de EE. UU.) |
| **SILC / EU-SILC** | Statistics on Income and Living Conditions | Sobrecarga y hacinamiento en vivienda |
| **AROPE** | At Risk Of Poverty or Social Exclusion (Eurostat) | Pobreza infantil (`arope_ninos`) |
| **MPI** | Multidimensional Poverty Index (PNUD-OPHI) | Recuento de pobreza |
| **MODA** | Multiple Overlapping Deprivation Analysis (UNICEF) | Marco de privación infantil |
| **LUCAS** | Land Use/Cover Area frame Survey (Eurostat) | Porcentaje de suelo artificial |
| **IPV** | Índice de Precios de Vivienda (INE) | House Price Index — el objetivo de T1 |
| **IPC** | Índice de Precios de Consumo (INE) | Deflactor a términos reales |
| **ZHVI** | Zillow Home Value Index | Valor de vivienda por metro EE. UU. |
| **RNB / GNI** | Renta Nacional Bruta / Gross National Income | Denominador de la AOD |

### Métodos y términos de modelado

| Sigla | Significado |
|---|---|
| **MASE** | Mean Absolute Scaled Error — la vara del pronóstico (drift = 0,40) |
| **LOOCV** | Leave-One-Out Cross-Validation — evaluación de las fronteras |
| **OLS / MCO** | Ordinary Least Squares / Mínimos Cuadrados Ordinarios — la regresión simple ganadora |
| **GBM** | Gradient Boosting Machine (LightGBM) — el candidato flexible |
| **MLP** | Multi-Layer Perceptron — el candidato "deep learning" |
| **DL** | Deep Learning / aprendizaje profundo |
| **SARIMAX** | Seasonal ARIMA with eXogenous variables — un candidato de T1 |
| **FE** | Fixed Effects (país + año) — el panel within |
| **CR1 / cluster SE** | Cluster-Robust standard errors — errores agrupados por país |
| **MC** | Monte Carlo — la simulación de deuda a 2070 |
| **r−g** | tipo de interés menos crecimiento — la aritmética de la deuda |
| **β65 / γ** | elasticidades: cuota 65+ → gasto (β), renta → resultado (γ) |
| **RAG** | Retrieval-Augmented Generation — el asistente de pasajes citados |
| **MVP** | Minimum Viable Product — el dashboard/API |
| **CCAA** | Comunidades Autónomas — las regiones de España (unidad del panel T1) |
| **PSA / CEAC** | (no usados aquí; términos de otros proyectos HEOR) |

### Etiquetas T1/A1/A2/D1 (nomenclatura interna del proyecto)

| Etiqueta | Módulo |
|---|---|
| **T1** | Pronóstico de asequibilidad de vivienda por CCAA (núcleo avalado) |
| **A1** | Frontera de rendimiento ajustado (gasto → resultado): salud, educación, bienestar |
| **A2** | Tipologías de composición del gasto (PCA + KMeans) |
| **D1** | Simulador de escenarios de deuda 2024–2050 (+ horizonte 50 años) |

### Códigos de contabilidad nacional (en `rev_*` y `gov_10a_exp_*`)

Sistema Europeo de Cuentas (SEC/ESA); aparecen como sufijos de fichero.

| Código | Concepto |
|---|---|
| `TE` | Gasto total (Total Expenditure) |
| `TR` | Ingreso total (Total Revenue) |
| `D1` | Remuneración de asalariados |
| `D3` | Subvenciones |
| `D62` | Prestaciones sociales |
| `D9` | Transferencias de capital |
| `P2` | Consumos intermedios |
| `P51G` | Formación bruta de capital fijo (inversión) |
| `D2REC` | Impuestos sobre la producción (recibidos) |
| `D5REC` | Impuestos sobre la renta (recibidos) |
| `D61REC` | Cotizaciones sociales (recibidas) |
| `D91REC` | Impuestos sobre el capital (recibidos) |
| `GF01`–`GF10` | Las diez funciones COFOG (01 servicios generales … 10 protección social) |
