# Metodología: cómo predice el sistema y por qué es fiable

Cómo se producen las predicciones (directa, encadenada, condicional) y la prueba de que la capa de datos y cálculo —no el modelo de lenguaje— es la que aporta los números. El protocolo pre-registrado completo está en `MEMORIA.md` §3.

## Contenido

- [Cómo se predicen los resultados: directa, encadenada y condicional](#cómo-se-predicen-los-resultados-directa-encadenada-y-condicional)
- [Ablación LLM: ¿marca la diferencia la capa ML/DL + RAG?](#ablación-llm-marca-la-diferencia-la-capa-mldl-rag)
- [Comparativa detallada: asistente de IA solo vs modelo completo](#comparativa-detallada-asistente-de-ia-solo-vs-modelo-completo)

---

## Cómo se predicen los resultados: directa, encadenada y condicional

Mapa conceptual de las tres arquitecturas de predicción del proyecto, dónde se
usa cada una y por qué. (Origen: pregunta sobre si, sabiendo predecir las
variables independientes, se puede encadenar una regresión que calcule la
dependiente — el ejemplo clásico: predecir el clima y convertirlo en producción
agrícola con una regresión de rendimientos.)

### Las tres arquitecturas

**1. Predicción DIRECTA.** El objetivo se predice desde su propio pasado (y,
como mucho, desde valores YA OBSERVADOS de otras variables, retardados). No se
predice ningún driver.

**2. Predicción ENCADENADA (two-stage).** Primero se predicen los drivers
(etapa 1), después una regresión estructural los convierte en el objetivo
(etapa 2). El ejemplo clima→cosecha. Su error total es:

    error(driver previsto) × sensibilidad de la regresión + error de la regresión

Regla que gobierna la elección: **encadenar solo compensa cuando el driver es
mucho más fácil de predecir que el objetivo.** Si no, la cadena amplifica.

**3. Predicción CONDICIONAL (escenarios).** La misma regresión de la etapa 2,
pero sin predecir el driver: lo fija el usuario ("SI los salarios crecen un
2 %…"). El error de predecir X se le devuelve a quien pregunta, que
normalmente ya sabe qué escenario le importa. Es predicción honesta cuando el
driver es imprevisible.

### Dónde está cada una en el proyecto

| Pieza | Arquitectura | Detalle |
|---|---|---|
| T1 producción (drift + abanico) | Directa pura | Sin variables independientes; incertidumbre = cuantiles de errores reales |
| T1 candidatos (GBM, GBM+demanda, Chronos, DL global) | Directa con drivers RETARDADOS | Compraventas, hipotecas, Δpoblación, crédito, suelo — siempre valores ya observados en el origen; nunca previstos |
| C1b (SARIMAX + Euríbor) | Encadenada degenerada, declarada | Necesitaba Euríbor futuro → se congeló en el último valor ("tipos constantes"); perdió 0/17 |
| A1 salud / educación | La regresión de la etapa 2, usada SOLA | Explica diferencias entre países hoy (frontera gasto→resultado); no predice el futuro |
| **D1 deuda** | **Encadenada completa — el ejemplo clima→cosecha construido** | Etapa 1: proyecciones demográficas de Eurostat (el driver). Etapa 2: elasticidades entrenadas en panel UE (β65: pensiones 0,91±0,19, sanidad 0,33) → presión de gasto → aritmética r−g → senda de deuda |
| Abanico salarial T1, palancas D1, `POST /scenario` | Condicional | El usuario fija salarios/tipos/consolidación; el sistema calcula |

### Por qué D1 encadena y T1 no (la decisión, con evidencia)

**La demografía cumple la regla; los drivers de vivienda no.**

- Los mayores de 65 de 2050 ya han nacido: la estructura de población tiene
  una inercia enorme y se puede proyectar décadas — por eso D1 encadena, y por
  eso su resultado central (deuda 224 % vs 127 % sin envejecimiento) es
  creíble con bandas.
- Para encadenar en T1 harían falta pronósticos a 2 años de hipotecas,
  migración o tipos — tan difíciles o más que predecir el propio precio. Y el
  proyecto midió el caso LÍMITE favorable: dando a los modelos los valores
  verdaderos observados de los drivers (retardados), ninguno batió al drift
  (quinto contest: mejor resultado 0,401 vs 0,395, 7/17 CCAA, no adoptado).
  Una versión encadenada — con drivers previstos en lugar de verdaderos — es
  matemáticamente peor que ese techo. El ejemplo del clima ilustra la trampa:
  a horizonte de campaña, el clima es MÁS difícil de predecir que la cosecha;
  la agronomía real usa normales climáticas o lluvia ya observada — el mismo
  movimiento que hacen nuestros candidatos con los retardos.

### Síntesis para la defensa

1. El proyecto contiene la arquitectura encadenada que sugiere la pregunta —
   construida y publicada donde su precondición se cumple (D1: driver
   predecible), y probada y rechazada donde no (T1: cinco contests).
2. Cuando la regresión estructural vale pero el driver es imprevisible, no se
   tira la regresión: se degrada honestamente a máquina condicional
   ("si X entonces Y") — escenarios del abanico, palancas de deuda, API.
3. Extensión declarada (no construida): encadenar proyecciones de población
   por CCAA (driver predecible) con la regresión de demanda → perspectiva
   CONDICIONAL de demanda de vivienda por CCAA. Pasaría por el protocolo:
   validación primero, adopción solo si la gana.

---

## Ablación LLM: ¿marca la diferencia la capa ML/DL + RAG?

### Resumen en lenguaje llano (para leer antes que las tablas)

La pregunta: el valor del proyecto debe estar en las **matemáticas** (los
modelos que procesan los datos); el asistente de IA solo debe poner esos
resultados en palabras, nunca inventar los números. Para comprobarlo hicimos
un experimento sencillo: cogimos **un mismo asistente de IA** (Gemini de Google)
y le hicimos las mismas 12 preguntas dos veces. **Primera vuelta:** el asistente
solo, de memoria, sin acceso al proyecto. **Segunda vuelta:** el mismo
asistente, pero entregándole antes los resultados que ha calculado el proyecto,
y pidiéndole que responda únicamente a partir de ellos. Las 12 preguntas tienen
respuestas que *solo el proyecto puede saber* (por ejemplo, la deuda que
proyecta el simulador para 2050). Resultado: **el asistente solo acertó 3 de 12;
con los resultados del proyecto, 11 de 12.** Y sus fallos "a solas" son del tipo
peligroso — sonar convincente y equivocarse: estimó la deuda de 2050 en 135 %
del tamaño de la economía cuando el proyecto calcula 224 % (no "ve" el efecto
del envejecimiento que las matemáticas del proyecto sí miden), e inventó una
relación entre suelo y precios donde los datos muestran que apenas existe. En
resumen: **sin la capa de matemáticas y datos el asistente se equivoca; con ella
acierta — luego esa capa es la que produce el conocimiento, y el asistente solo
lo narra.** ("RAG", que aparece más abajo, significa simplemente: antes de
responder, buscar primero los documentos reales y contestar solo con ellos —
ese "buscar primero" es toda la diferencia entre las dos vueltas.)

Detalle completo pregunta a pregunta: `docs/METODOLOGIA.md`.

---

Requisito del tutor, convertido en experimento medible: **las matemáticas
(la capa ML/DL) producen los resultados; el LLM se limita a explicarlos.** Si
eso se cumple, un LLM a pelo — sin el sistema — NO debería reproducir los
números del modelo, y con el sistema SÍ. Aquí se comprueba, en vivo.

Reproducible: `python3 analysis/ablacion_llm.py` → `gold/gold_ablacion_llm.csv`.
Aserción permanente en `tests/test_ablacion.py` (falla si la capa deja de
diferenciar). Ejecutado con **gemini-2.5-pro** (2026-07-19); el diseño es
agnóstico al motor — el registro `ENGINES` admite kimi/glm/mimo/gemini.

### Diseño

Mismo LLM en los dos brazos; la ÚNICA variable es la capa de conocimiento.

- **Brazo A — LLM solo**: el modelo sin contexto, "da tu mejor estimación".
- **Brazo B — LLM + sistema (RAG)**: el mismo modelo con los pasajes
  recuperados del corpus del proyecto — es decir, con los resultados que
  calcula la capa ML/DL.
- **Verdad**: el valor que produce el sistema (gold / motores).

12 preguntas cuya respuesta es una SALIDA del sistema (backtests, Monte Carlo,
paneles, fronteras): imposibles de acertar sin las matemáticas, triviales de
citar con ellas.

### Resultado

| Pregunta | Verdad (sistema) | LLM solo | LLM + sistema |
|---|---|---|---|
| Ratio asequibilidad nacional 2024 | 1,26 | 1,32 ✅ | 1,26 ✅ |
| Ratio proyectado 2027Q4 (+2 % sal.) | 1,64 | **40,7** ❌ | 1,64 ✅ |
| MASE drift h≤4 (validación) | 0,395 | 0,87 ❌ | — ❌ (declina) |
| Deuda 2050 central (% PIB) | 224 | **135** ❌ | 224 ✅ |
| Deuda 2050 sin demografía | 127 | **6,5** ❌ | 127 ✅ |
| Deuda 2070 mediana MC | 409 | 181 ❌ | 409 ✅ |
| Esfuerzo hipotecario nacional 2024 | 41,6 % | 37,0 ❌ | 41,6 ✅ |
| Gasto público España 1900 | 11,0 | 8,7 ❌ | 11,0 ✅ |
| Residual sanitario España (A1) | 2,72 | 3,2 ✅ | 2,7 ✅ |
| Bienestar 2050, crec. 1 % | −12,3 % | −8,2 ❌ | −12,3 ✅ |
| Elasticidad β65 pensiones | 0,912 | 1,0 ✅ | 0,91 ✅ |
| Spearman precio/renta vs suelo | 0,01 | **0,35** ❌ | 0,01 ✅ |

**LLM solo: 3/12. LLM + sistema: 11/12. Error relativo del LLM solo: mediana 27 % (rango 5 %–2382 %) → con el sistema, 0 %.**

(El rango importa: la mediana del 27 % no significa "27 % de error de media" sino
"típicamente 27 %, pero hasta 2382 %" — el caso del ratio 2027, donde el LLM solo
dio 40,7 frente al 1,64 real. Un solo número esconde lo catastrófico de algunos
fallos.)

#### Lectura

- **Los dos resultados difieren de forma efectiva y masiva.** El requisito del
  tutor se cumple: sin la capa ML/DL el LLM no reproduce los números; con ella,
  sí. La diferencia no es de matiz — es 3/12 vs 11/12.
- **Los errores del LLM solo son los del "plausible pero falso"**: proyecta la
  deuda 2050 en 135 % (ignora la presión demográfica que el motor cuantifica en
  +97 pp); inventa una correlación suelo-precio de 0,35 cuando el panel mide
  0,01; da un ratio 2027 de 40,7 (confunde escalas). Exactamente el fallo que la
  capa de datos + validación evita.
- **Honestidad del propio experimento**: 11/12, no 12/12. En `mase_drift` el
  RAG recuperó el pasaje correcto pero el LLM declinó entre 0,40 (titular) y
  0,395 (h≤4) y no emitió número. Se reporta el fallo, no se esconde — es la
  misma disciplina del resto del proyecto.

### Segunda parte: ¿dónde vive el ML/DL en el modelo?

La percepción de "poco ML/DL" viene de que el modelo PUBLICADO es simple (drift,
OLS). Pero esa simplicidad es una CONCLUSIÓN de la capa matemática, no su
ausencia. El ML/DL está en toda la tubería:

| Dónde | Técnica | Rol |
|---|---|---|
| Selección T1 | 5 contests: SARIMAX, LightGBM, LightGBM+demanda, Chronos (fundacional), MLP global (PyTorch, 1.760 series) | La maquinaria que JUZGA; el drift gana porque la superó |
| Producción D1 | Regresión panel UE con efectos fijos + errores CR1 (cluster) | Elasticidades β65 0,91±0,19 — ENTRENADAS, alimentan la deuda a 2070 |
| Fronteras A1 (×3) | OLS vs GBM vs MLP bajo LOOCV + conformal | El OLS gana 5/5 — resultado medido, no supuesto |
| Horizonte 50 | Panel within (FE país+año, CR1) + Monte Carlo 4.000 trayectorias | Efecto ingreso→bienestar a retardo 8; propagación de incertidumbre |
| Tipologías A2 | PCA + KMeans | Composición del gasto (clusters débiles, silueta 0,20) |
| DL profundo | MLP entrenado sobre 208.640 observaciones (PyTorch) | Empate técnico 0,401 vs 0,395 — la única vía con evidencia de anticipar giros |
| Asistente | TF-IDF + coseno (RAG) | Recuperación; la capa de este experimento |

La matemática defendible del TFM no es "usé una red neuronal", sino: **construí
la capa de evaluación ML que dejó ganar al modelo simple en público cinco veces,
entrené las elasticidades que están en producción, y demostré que sin todo eso
el LLM se equivoca.** Esa capa ES el contenido; el LLM solo la narra.

---

## Comparativa detallada: asistente de IA solo vs modelo completo

Informe completo, pregunta a pregunta, del experimento de ablación
(`docs/METODOLOGIA.md`). Muestra qué responde un asistente de IA **por sí solo**
frente a qué responde **el mismo asistente apoyado en el modelo completo**
(sus datos y sus cálculos), y cuál es el valor verdadero que produce el sistema.

Todos los números salen de `storage/gold/gold_ablacion_llm.csv`, generado por
`analysis/ablacion_llm.py` con Gemini 2.5 Pro el 2026-07-19.

### Qué significan las tres columnas

- **Modelo completo (verdad)**: el número que calcula el sistema — la capa de
  datos + los modelos estadísticos + los motores de simulación. Es la respuesta
  correcta contra la que se compara todo.
- **IA sola**: el asistente de IA respondiendo de memoria, sin acceso al
  proyecto. Simula "preguntar a alguien muy leído, sin dejarle consultar nada".
- **IA + modelo**: el mismo asistente, pero al que primero se le entregan los
  resultados calculados del proyecto y solo puede responder a partir de ellos.

Un acierto = caer dentro de una tolerancia razonable del valor verdadero
(entre 5 % y 25 % según la pregunta; para la correlación, ±0,05 absoluto).

### Marcador global

| | Aciertos | Error relativo (mediana · rango) |
|---|---|---|
| **IA sola** | **3 / 12** | 27 % · de 5 % a 2382 % |
| **IA + modelo completo** | **11 / 12** | 0 % |

El rango de la IA sola es lo revelador: la mediana del 27 % no dice "27 % de
error de media", sino "típicamente 27 %, pero hasta 2382 %" — hay fallos
puntuales catastróficos (el ratio 2027, donde da 40,7 en vez de 1,64). Un solo
número esconde esa cola; por eso se reporta con su rango.

La diferencia es masiva y en la dirección que exige el tutor: la capa de
matemáticas y datos es la que produce los resultados; el asistente, sin ella,
no los reproduce.

---

### Detalle pregunta a pregunta

#### 1. Ratio de asequibilidad de la vivienda en España, 2024
- **Verdad (modelo):** 1,26 · **IA sola:** 1,32 ✅ · **IA + modelo:** 1,26 ✅
- Ambos aciertan. Es un dato razonablemente conocido (los precios han subido más
  que los salarios desde 2015), así que la IA lo estima bien de memoria. Cuando
  la respuesta es "de cultura general", la IA sola basta — pero son la minoría.

#### 2. Ratio de asequibilidad proyectado a finales de 2027
- **Verdad:** 1,64 · **IA sola:** 40,7 ❌ · **IA + modelo:** 1,64 ✅
- El fallo más aparatoso de la IA sola: da 40,7, un disparate de escala (confunde
  un índice con un porcentaje). El modelo, que arrastra la definición correcta y
  el pronóstico, da 1,64. Muestra que en cuanto la pregunta exige el resultado
  concreto de un cálculo, la IA sola descarrila.

#### 3. Precisión del modelo campeón en la validación (MASE, horizonte ≤4)
- **Verdad:** 0,395 · **IA sola:** 0,87 ❌ · **IA + modelo:** sin respuesta ❌
- El único punto donde el modelo completo NO acierta: la IA, aun con el documento
  delante, no supo elegir entre dos cifras muy próximas (0,40 titular y 0,395 a
  horizonte corto) y prefirió no responder. Lo reportamos abierto: 11 de 12, no
  12. La IA sola, por su parte, se inventa un 0,87.

#### 4. Deuda pública proyectada para 2050 (escenario central)
- **Verdad:** 224 % · **IA sola:** 135 % ❌ · **IA + modelo:** 224 % ✅
- Clave. La IA sola proyecta 135 % — no "ve" la presión del envejecimiento, que
  el motor del proyecto cuantifica en +97 puntos. Es justo el conocimiento que
  aportan los datos demográficos y las elasticidades entrenadas.

#### 5. Deuda 2050 SIN presión demográfica (contrafactual)
- **Verdad:** 127 % · **IA sola:** 6,5 % ❌ · **IA + modelo:** 127 % ✅
- La IA sola da 6,5 %, absurdo. No puede reproducir un contrafactual que solo
  existe dentro del simulador del proyecto.

#### 6. Deuda mediana en 2070 (simulación Monte Carlo)
- **Verdad:** 409 % · **IA sola:** 181 % ❌ · **IA + modelo:** 409 % ✅
- Una proyección a 46 años con incertidumbre propagada: imposible de memoria.
  La IA sola se queda a menos de la mitad.

#### 7. Esfuerzo hipotecario nacional en 2024 (% del salario bruto)
- **Verdad:** 41,6 % · **IA sola:** 37,0 % ❌ · **IA + modelo:** 41,6 % ✅
- La IA sola se acerca pero falla: no tiene el €/m² concreto ni los supuestos de
  la hipoteca tipo que usa el proyecto.

#### 8. Gasto público de España en 1900 (% del PIB)
- **Verdad:** 11,0 % · **IA sola:** 8,7 % ❌ · **IA + modelo:** 11,0 % ✅
- Dato histórico fino que exige la serie empalmada del proyecto; la IA sola lo
  subestima.

#### 9. Rendimiento sanitario de España sobre lo esperado (años de vida)
- **Verdad:** 2,72 · **IA sola:** 3,2 ✅ · **IA + modelo:** 2,7 ✅
- Ambos dentro de la tolerancia amplia de esta pregunta (±25 %), pero el modelo
  clava el valor de la frontera; la IA sola acierta por aproximación.

#### 10. Efecto en la mortalidad infantil a 2050 (crecimiento de renta 1 %)
- **Verdad:** −12,3 % · **IA sola:** −8,2 % ❌ · **IA + modelo:** −12,3 % ✅
- La IA sola intuye el signo (menos pobreza → menos mortalidad) pero falla la
  magnitud, que sale del panel estadístico del proyecto.

#### 11. Elasticidad del gasto en pensiones al envejecimiento
- **Verdad:** 0,912 · **IA sola:** 1,0 ✅ · **IA + modelo:** 0,91 ✅
- La IA sola da un "1,0" de libro; el modelo aporta el valor estimado real con su
  incertidumbre (0,91 ± 0,19). Ambos dentro de tolerancia, pero solo el modelo
  puede defender de dónde sale.

#### 12. Relación entre suelo urbanizado y precios de la vivienda (correlación)
- **Verdad:** 0,01 · **IA sola:** 0,35 ❌ · **IA + modelo:** 0,01 ✅
- El fallo más instructivo: la IA sola **inventa** una relación moderada (0,35)
  porque "suena lógico" que urbanizar más abarate. El dato real del proyecto,
  sobre 40 países, es 0,01 — no hay relación. La IA reproduce el prejuicio; el
  modelo, la evidencia.

---

### Conclusión

- **En 8 de 12 preguntas la IA sola falla y el modelo acierta.** En 3 aciertan
  ambos (preguntas de "cultura general"). En 1 falla el modelo por prudencia
  (no eligió entre dos cifras casi iguales).
- **Los errores de la IA sola no son ruido: son sesgo plausible.** Ignora el
  envejecimiento, inventa correlaciones que "suenan bien", confunde escalas.
  Son exactamente los errores que la capa de datos + validación existe para
  evitar.
- **Confirma el diseño del proyecto**: el sistema calcula, el asistente narra.
  La prueba está automatizada (`tests/test_ablacion.py`): si algún día la IA
  sola empezara a igualar al modelo, el test fallaría y avisaría de que la capa
  de matemáticas ha dejado de aportar.
