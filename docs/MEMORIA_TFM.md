# España en escenarios: simulación económica transparente y evaluación crítica de modelos de IA

**Estado documental:** 20 de septiembre de 2026, motor 1.1.0, corte de datos `2026-07-31`.
Pendiente de la portada y del formato exigidos por la normativa de la universidad,
y de la declaración de contribuciones y de uso de herramientas de IA. Los
resultados citados proceden de los artefactos indicados; las evaluaciones
pendientes se distinguen explícitamente de las realizadas.

## Resumen

Este trabajo desarrolla y examina una plataforma que integra simulación macroeconómica, análisis regional de vivienda, aprendizaje automático y consulta documental mediante generación aumentada por recuperación. Su finalidad es hacer explícitos los supuestos de escenarios económicos y evaluar qué respaldo empírico ofrece cada componente. Se implementan un motor semiestructural reproducible en Python y TypeScript, simulaciones Monte Carlo, estimadores de panel, un modelo neuronal de transferencia internacional, clasificación exploratoria de impago soberano y recuperación documental multilingüe con una capa de lenguaje sujeta a comprobación numérica.

Los resultados delimitan lo que el sistema puede sostener. La red neuronal no supera el criterio de comparación con una extrapolación de tendencia. La clasificación soberana presenta discriminación moderada y no está calibrada para España. La aparente precisión de la media regional de vivienda disminuye sustancialmente al preservar los movimientos nacionales comunes en el remuestreo: el 3 % de la calibración heredada deja de rechazarse. De ocho parámetros estructurales examinados, sólo tres resultan identificables con los datos disponibles, y los cinco restantes se declaran no identificados con su motivo econométrico.

La contribución es una infraestructura auditable y una evaluación que separa cuatro cosas que suelen confundirse: coherencia computacional, descripción histórica, capacidad predictiva e identificación causal. No se acredita una herramienta de previsión económica ni una mejora educativa medida experimentalmente.

**Palabras clave:** simulación macroeconómica, evaluación predictiva, mercado de la vivienda, cuantificación de la incertidumbre, datos de panel, generación aumentada por recuperación.

## Abstract

This work develops and examines a platform integrating macroeconomic simulation, regional housing analysis, machine learning and document retrieval through retrieval-augmented generation. Its purpose is to make the assumptions behind economic scenarios explicit and to assess what empirical support each component actually has. It implements a semi-structural engine reproduced in both Python and TypeScript, Monte Carlo simulation, panel estimators, a neural transfer model trained on foreign housing series, exploratory sovereign-default classification, and multilingual document retrieval with a language layer constrained by a numeric verification step.

The results bound what the system can claim. The neural network does not beat a trend extrapolation under a success rule fixed in advance. The sovereign classifier shows moderate discrimination and is not calibrated for Spain. The apparent precision of the regional housing mean falls substantially once common national movements are preserved in resampling: the inherited 3 % calibration is no longer rejected. Of eight structural parameters examined, only three are identifiable from the available data; the remaining five are declared unidentified, each with its econometric reason.

The contribution is an auditable infrastructure and an evaluation that separates four things commonly conflated: computational coherence, historical description, predictive capability and causal identification. No forecasting tool and no experimentally measured educational benefit are claimed.

**Keywords:** macroeconomic simulation, predictive evaluation, housing market, uncertainty quantification, panel data, retrieval-augmented generation.

## 1. Introducción

### 1.1 Problema

Una interfaz económica puede producir cifras precisas sin que sus supuestos estén identificados por los datos. Una explicación con citas puede parecer convincente aunque los pasajes no respalden todas sus afirmaciones. Y un sistema puede superar cientos de comprobaciones informáticas sin que ninguna de ellas hable de su validez económica. El problema abordado consiste en integrar cálculo y evidencia conservando estas distinciones, en lugar de dejar que la fluidez de la interfaz las borre.

El riesgo es concreto y asimétrico. Un modelo de escenarios mal comunicado no falla ruidosamente: produce un número plausible, con decimales, acompañado de un gráfico. Quien lo lee no dispone de ninguna señal que distinga una cifra estimada de una calibrada a mano, ni una proyección condicional de una previsión. El trabajo parte de la premisa de que esa señal debe construirse deliberadamente y de que construirla es una tarea de ingeniería tanto como de método.

### 1.2 Preguntas y objetivos

Se plantean tres preguntas de investigación:

- **P1.** ¿Qué propiedades del motor pueden contrastarse con los paneles disponibles y cuánto dependen de la muestra y del tratamiento de la incertidumbre?
- **P2.** ¿Aportan los modelos de aprendizaje automático mejoras observables frente a referencias explícitas, con qué particiones y para qué población?
- **P3.** ¿Puede la aplicación conservar la procedencia de datos y documentos, evitando presentar coherencia informática como validez científica?

De ellas se derivan cinco objetivos operativos:

1. **O1.** Portar un prototipo heredado a una implementación doble (servidor y navegador) cuya concordancia numérica sea verificable mediante anclas compartidas.
2. **O2.** Determinar cuáles de los parámetros estructurales del motor son identificables con los datos congelados y estimar únicamente esos, declarando el resto como no identificados con su motivo.
3. **O3.** Evaluar los componentes de aprendizaje automático contra referencias explícitas y reglas de éxito fijadas antes de conocer el resultado, publicando los resultados negativos.
4. **O4.** Cuantificar la sensibilidad de las conclusiones al esquema de inferencia, en particular al tratamiento de la dependencia temporal común entre regiones.
5. **O5.** Construir una capa de consulta documental y de lenguaje natural cuyas afirmaciones numéricas sean verificables contra los hechos calculados por el motor.

### 1.3 Estructura de la memoria

La sección 2 sitúa el trabajo en la literatura de sostenibilidad de la deuda, dinámica de precios de vivienda, predicción con modelos globales y evaluación de sistemas de recuperación. La sección 3 describe los datos y el régimen de trazabilidad. La sección 4 presenta la arquitectura. La sección 5 detalla el diseño metodológico de cada componente. La sección 6 reúne los resultados. Las secciones 7 y 8 discuten e inventarían los límites, y la 9 concluye. Los anexos recogen la matriz de evidencia, los parámetros estimados, los comandos de reproducción y el manifiesto del corpus.

## 2. Estado del arte

<!-- PENDIENTE: sección de estado del arte con literatura verificada. -->

## 3. Datos y trazabilidad

### 3.1 Régimen de corte y procedencia

La capa española reúne series fiscales, vivienda por comunidad autónoma, demografía y otros indicadores procedentes de fuentes públicas. La fecha `2026-07-31` identifica la referencia del escenario; no demuestra que todos los artefactos añadidos posteriormente se descargaran ese día. Se distinguen fecha de adquisición, periodo observado y fecha de construcción. Los metadatos y las sumas de comprobación permiten identificar los archivos empleados, pero no prueban su autenticidad originaria ni reconstruyen transformaciones históricas ausentes. Véanse [metadatos](../data/ARTIFACT_METADATA.json) y [reproducibilidad](REPRODUCIBILITY.md).

Congelar el corte tiene un coste explícito: faltan datos que existen. El INE publica paro regional que el corte no incorpora, y añadirlo rompería la repetibilidad de todo cálculo anterior. Es una elección de reproducibilidad sobre completitud, y se declara como tal porque condiciona qué parámetros pueden estimarse (sección 5.2).

### 3.2 Inventario de fuentes

| Capa | Contenido | Cobertura | Tamaño |
|---|---|---|---|
| Panel regional de vivienda | Índice de precio de vivienda por CCAA | 2008T1–2026T1, 19 unidades | 1.387 variaciones interanuales |
| Reversión autorregresiva | Pares de crecimiento separados cuatro trimestres | mismo panel | 1.311 pares |
| Corpus inmobiliario extranjero | Series de EE. UU. y Reino Unido | objetivos ≤ 2019T3 | 1.760 series, 113.649 ventanas |
| Panel de impago soberano | Indicadores WDI + etiquetas BoC–BoE | — | 3.874 país-año, 154 países, 377 eventos |
| Panel de estado macroeconómico | Crecimiento compuesto a tres años | 1981–2021 | 2.816 país-año, 140 países |
| Análogos históricos | Cinco variables normalizadas | 1991–2020 | 4.091 observaciones, 173 países |
| Corpus documental | Manuales, metodología propia y opinión | — | 474 documentos, 17.848 fragmentos |

El panel regional contiene 17 CCAA, Ceuta y Melilla. Se excluye Nacional porque agrega información de las mismas regiones. La media conjunta otorga igual peso a cada observación regional; no equivale a ponderar por población o transacciones. Los periodos de ajuste y recuperación se presentan por separado. [Construcción del panel](../research/panel.py).

Para aprendizaje internacional se conservan 1.760 series inmobiliarias estadounidenses y británicas. Su documentación identifica un procesamiento heredado, por lo que reproducir el entrenamiento desde el archivo congelado y reconstruir la extracción original son objetivos distintos. La clasificación soberana combina indicadores WDI con etiquetas derivadas de la base BoC–BoE, cuya definición incluye distintas modalidades de incumplimiento y reestructuración. Las etiquetas transformadas deben distinguirse de las observaciones originales. [Corpus extranjero](../data/external/README.md), [fuentes de impago](../data/external/README_distress.md), [Beers, Ndukwe y Berry, 2025](https://www.bankofcanada.ca/2025/10/staff-analytical-note-2025-24/).

### 3.3 Correcciones de procedencia detectadas

Dos errores de etiquetado se detectaron y corrigieron durante el trabajo, y se documentan porque afectan a la interpretación de resultados anteriores. El primero: la serie *bank lending rate* del Banco Mundial se había empleado como rendimiento soberano y dentro de un diferencial nominal-real; es un tipo bancario, no soberano, y se retiró de ambos usos y del emparejamiento de análogos. El segundo: los valores ausentes se mostraban imputados como medias o ceros en algunos gráficos; ahora política, régimen cambiario y vencimiento se presentan como no disponibles en lugar de inferirse de aproximaciones estáticas. [Cambios metodológicos](METHODOLOGY_CHANGES.md).

## 4. Arquitectura del sistema

### 4.1 Cuatro capas con una regla

El sistema se organiza en cuatro capas gobernadas por una regla: *cada capa sólo puede hacer aquello que la siguiente puede comprobar*.

1. **Motor determinista.** Identidad de deuda y reglas calibradas, implementado en Python (servidor) y TypeScript (navegador). Su salida es reproducible byte a byte desde artefactos congelados.
2. **Capa empírica.** Estimadores de panel, modelos predictivos y descriptivos. Publica parámetros, métricas y resultados negativos como artefactos JSON versionados.
3. **Capa de explicación.** Calcula primero los hechos desde el motor y redacta después, con una comprobación numérica entre ambos pasos.
4. **Capa de recuperación.** Índice documental híbrido con separación por colecciones y verificación de citas.

La paridad numérica entre el motor de servidor y el de navegador se verifica con un conjunto común de anclas y se comprueba sobre las 40 series en todos los años del horizonte, no sólo sobre la deuda: la comprobación anterior sólo comparaba deuda y por eso no detectaba discrepancias en vivienda y saldo. Esta paridad acredita consistencia de implementación; la evaluación empírica responde a otras preguntas. [Motor](../engine/spain.py), [anclas](../tests/fixtures/engine_anchors.json).

### 4.2 Entorno, despliegue y reproducción

El entorno de referencia es Linux x86_64 con Python 3.12 y Node 22, con cierre de dependencias fijado en `requirements-lock.txt` y registrado en [`docs/environment.json`](environment.json). La aplicación se publica como sitio estático (GitHub Pages) y API contenedorizada (Hugging Face Spaces). El índice documental público se construye desde una lista explícita de documentos propios del proyecto; las colecciones con derechos de autor no forman parte de él.

Durante la evaluación del trabajo existe una excepción acotada: un índice de revisión que sí incluye los manuales, accesible sólo mediante un token, alojado temporalmente en un servidor de terceros y retirado al concluir la evaluación. Se documenta aquí porque es una decisión sobre licencias de datos, no un detalle de despliegue. [Procedimiento](../README.md).

Las limitaciones de reproducción conocidas se declaran: la instalación limpia no está verificada en un entorno nuevo, la integración continua está definida pero no ejecutada en remoto, y algunas transformaciones del pipeline original no se han reconstruido. El anexo C recoge el mapa de comandos.

## 5. Diseño metodológico

Esta sección describe, para cada componente, qué se calcula, con qué supuestos y qué tipo de afirmación permite. El orden va de lo más determinista a lo más incierto.

### 5.1 Simulación y coherencia computacional

El motor combina una identidad de deuda con reglas calibradas para crecimiento, empleo, inflación, salarios y vivienda. La identidad fundamental es:

$$b_t = b_{t-1}\frac{1+i_t}{1+g_t} - sp_t,$$

donde los tipos se expresan en tanto por uno y el saldo primario en puntos de PIB. Mover una palanca produce una trayectoria condicional a estas relaciones; no constituye por sí mismo una intervención causal estimada. Buena parte de los coeficientes y la selección de rangos incorporan juicio del modelizador.

Los intereses sobre el PIB corriente son $b_{t-1}i_t/(1+g_t)$, y el saldo total resta estos intereses al saldo primario. Una versión anterior omitía el denominador al calcular intereses y saldo total, aunque lo aplicaba correctamente en la identidad de deuda; corregirlo sitúa los intereses base de 2026 en 2,73967 % del PIB y el saldo total en −4,08967 %, sin alterar la senda de deuda. Esta misma base contable se usa ahora en ambos motores.

En combinaciones extremas la recurrencia puede producir deuda negativa: se señala como salida del dominio de deuda bruta, pues no se modelan activos públicos ni una reacción de política al agotar la deuda.

La dinámica de precios de vivienda sigue una reversión hacia una media de largo plazo,

$$h_k = \mu + (h_0-\mu)(1-\kappa)^k + \text{canales de tipos y crecimiento},$$

donde $\kappa$ es la tasa anual de reversión y $h_0$ el crecimiento observado de partida.

La simulación Monte Carlo genera 4.000 trayectorias con perturbaciones AR(1) de tipos, crecimiento y saldo primario, con semilla 42. Los percentiles son bandas de simulación condicionadas a distribuciones y reglas calibradas. Una sensibilidad separada varía persistencia, escala, número de trayectorias y semilla, sin afirmar cobertura empírica del 90 %. [Método y resultados](eval/montecarlo-sensitivity.json).

Dos precisiones de unidades se corrigieron y conviene dejar escritas. `alpha_spread = 0,04` significa 4 puntos básicos por punto porcentual de deuda por encima del umbral: veinte puntos de exceso producen 80 pb, no 0,8. Y `omega = 0` elimina la persistencia de la desviación de inflación respecto a la referencia congelada; no impone un objetivo del 2 % del BCE.

### 5.2 Identificación de parámetros

Antes de estimar se escribió qué podía estimarse y qué no. La lista de imposibles es parte del resultado, y es la razón por la que el núcleo fiscal del motor sigue calibrado.

| Parámetro | Estado | Motivo |
|---|---|---|
| `IPV_LR` | estimado: 1,2151 % [0,9008; 1,5295] | media regional, 1.387 observaciones, 19 unidades |
| `IPV_REV` | estimado: 0,2039 [0,1811; 0,2268] | AR(1) sobre la desviación, 1.311 pares |
| `PB_PERSIST` | estimado: 0,8720 [0,8085; 0,9354] | panel de 18 países desde 1960 |
| `E_IPV_R` | no identificado | el Euríbor es nacional y el panel regional: sin variación transversal en el tipo |
| `OKUN` | no identificado | el corte no trae paro regional ni brecha del producto |
| `KAPPA` | no identificado | no hay serie de expectativas de inflación |
| `MULT` | no identificado | exigiría un choque fiscal identificado; gasto e ingreso son endógenos al ciclo |
| `E_R` | no identificado | sin serie de PIB por país, sólo gasto e ingreso |

Declarar un parámetro no identificado es una afirmación más fuerte que publicar un coeficiente obtenido de una regresión que no lo sostiene. Tres de ocho parámetros pasan el filtro; los cinco restantes conservan su valor calibrado y la interfaz no presenta esos valores como estimaciones. [Estimación](../research/panel.py), [parámetros conservados](../data/gold/estimated_params.json).

La tasa de reversión se define como $r = 1-\phi$, siendo $\phi$ la persistencia. La versión heredada utilizaba el número 0,60 como factor retenido; su tasa comparable es 0,40. Reproducir exactamente aquella senda requiere fijar ambos valores, `ipv_rev = 0,40` y `ipv_lr = 3,0`. Las anclas numéricas se regeneraron con los valores actuales y por tanto ya no fijan la trayectoria heredada. Esta precisión evita intercambiar magnitudes con efectos opuestos: con los valores heredados la mediana del precio en 2050 es 400.982 €, y con los actuales 353.640 €.

### 5.3 Estimación regional e incertidumbre

Se estima la media de crecimiento y una relación autorregresiva anual mediante efectos fijos regionales. Los intervalos primarios emplean errores agrupados por unidad. Agrupar permite dependencia interna, pero requiere atender también a la dependencia entre grupos y al número de grupos. [Cameron y Miller, 2015](https://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015.pdf).

Como contraste, un bootstrap circular de 500 réplicas con semilla 42 remuestrea bloques comunes de 4, 8 y 12 trimestres. Todas las regiones de cada trimestre se desplazan juntas, conservando la covariación nacional. Las regiones permanecen fijas. El ejercicio supone estabilidad aproximada dentro de cada ventana y crea una unión artificial entre final e inicio; se publica como sensibilidad complementaria, no como sustituto de la banda primaria. [Implementación](../research/housing_robustness.py).

La intuición del contraste importa más que su mecánica. Al remuestrear todas las regiones a la vez, diecinueve series dejan de aportar diecinueve piezas de información independiente y pasan a comportarse aproximadamente como un único ciclo inmobiliario nacional de dieciocho años. La banda se ensancha porque la información efectiva es menor, no porque el método sea más conservador por capricho.

Las regresiones horizonte a horizonte siguen la organización de las proyecciones locales, pero aquí relacionan crecimiento interanual previo y cambio futuro del logaritmo del precio, descontando las medias regionales. No identifican una innovación exógena. El crecimiento interanual solapado tampoco equivale a un choque trimestral. La comparación con el motor acumula cambios de nivel desde el precio observado en $t$, presenta sólo puntos anuales y normaliza el primer año: esa coincidencia es impuesta. [Jordà, 2005](https://www.aeaweb.org/articles?id=10.1257/0002828053828518), [implementación](../research/validate.py).

### 5.4 Modelos predictivos

**Transferencia neuronal inmobiliaria.** Un perceptrón multicapa de arquitectura 16→128→128→64→8 recibe dieciséis cambios logarítmicos trimestrales y produce ocho cambios acumulados. Se entrena con 113.649 ventanas extranjeras cuyos objetivos terminan como máximo en 2019T3. El backtest utiliza orígenes desde 2019T4, elimina objetivos posteriores a 2023T4 y compara con último valor, ingenuo estacional y tendencia reciente de ocho trimestres. MASE se escala exclusivamente con errores estacionales del entrenamiento. [Protocolo](../research/backtest.py), [Hyndman y Koehler, 2006](https://robjhyndman.com/papers/mase.pdf).

La regla de éxito exige superar la tendencia en al menos 12 de 17 CCAA para horizontes hasta cuatro trimestres. Esa regla se fijó en el repositorio antes de conocer el resultado, lo que la distingue de un umbral elegido después; no se depositó en un registro externo independiente, de modo que es más débil que una preinscripción formal y más fuerte que un criterio *post hoc*. La distinción es relevante porque el resultado obtenido es negativo y su valor depende precisamente de cuándo se escribió el criterio.

**Clasificación de impago soberano.** Un clasificador de *boosting* utiliza características de $t$ para el inicio de impago en $t+1$, excluyendo años ya en impago. Las cinco particiones `GroupKFold` separan países pero mezclan épocas: evalúan transferencia entre países, no anticipación prospectiva. Se conserva una correspondencia local de nombres y códigos; los fallos de mapeo detienen el proceso. Su salida se denomina puntuación exploratoria sin calibrar, en escala 0–1.

### 5.5 Modelos descriptivos

Tres componentes describen la historia sin pretender predecirla, y se agrupan aquí para que esa condición quede explícita.

**Dependencia del estado macroeconómico.** Un segundo *boosting* relaciona estado macroeconómico y crecimiento acumulado a tres años sobre 2.816 observaciones país-año de 140 países, 1981–2021, con `GroupKFold` de cinco particiones y 60 réplicas bootstrap por país. Las pendientes SHAP por régimen de deuda describen el modelo ajustado. SHAP atribuye predicciones a variables y no convierte asociaciones endógenas en efectos causales. [Lundberg y Lee, 2017](https://proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html), [análisis](../research/state_dependence.py).

**Regímenes históricos.** Un modelo oculto de Markov gaussiano de dos estados, ajustado retrospectivamente sobre saldo fiscal e índice de vivienda, con Viterbi y posteriores suavizados. Etiqueta como «crisis» el estado de mayor varianza y publica episodios, por ejemplo vivienda 2008T1–2014T1. Es una segmentación descriptiva dependiente de la especificación, no un detector anticipado validado ni una etiqueta oficial de crisis. [Resultados](eval/regimes.json), [método](../research/regimes.py).

**Vecinos históricos.** Un KNN con distancia de Mahalanobis sobre cinco variables normalizadas, con covarianza y diferencias en las mismas coordenadas, consultado en el año seleccionado, sobre 4.091 observaciones completas de 173 países entre 1991 y 2020, con España excluida del conjunto de referencia. No imputa huecos como valores observados y no aplica bonificación por palanca —un ajuste arbitrario que se retiró—. El tipo bancario de préstamo queda excluido del emparejamiento. No emite veredicto de sostenibilidad. La semejanza histórica no predice la trayectoria española. [Motor](../engine/analog.py), [informe](eval/analog-metric.json).

### 5.6 Recuperación documental y capa de lenguaje

**Recuperación.** La consulta combina embeddings multilingües E5, búsqueda léxica BM25 y fusión de rangos, con separación entre colecciones académicas, metodología propia y opinión, y con etiquetado de autoridad para que un manual y un canal divulgativo no se citen con el mismo peso. Se comprueban identificadores, citas y pertenencia de pasajes a la colección solicitada. La evaluación distingue tres cosas: encontrar un documento, recuperar un pasaje pertinente y producir una respuesta respaldada. [Lewis et al., 2020](https://proceedings.nips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html), [Wang et al., 2024](https://arxiv.org/abs/2402.05672), [protocolo](eval/README_RAG.md).

**Capa de lenguaje.** El modelo de lenguaje tiene dos usos y en ambos rige la misma restricción: *escribe, nunca calcula*.

En resolución de preguntas (`/ask`), el modelo traduce texto libre a una consulta ejecutable —serie, año y valores de palanca— eligiendo de un vocabulario cerrado de 25 series. Una serie desconocida produce un rechazo, una palanca desconocida se descarta y un valor fuera del rango publicado se recorta a él. El modelo elige; los límites del motor deciden qué es admisible.

En redacción (`/explain`), los hechos llegan ya calculados y el modelo sólo pone palabras. Una comprobación posterior rechaza cualquier magnitud numérica que no esté literalmente en los hechos, admitiendo redondeos pero no truncamientos. Esa comprobación descarta en torno a una de cada cinco redacciones, y las violaciones observadas son informativas: conversiones a puntos básicos, restas entre cifras dadas, un porcentaje derivado de una proporción y un año histórico citado de memoria. Todas son casos de un modelo calculando cuando se le pidió que narrara. Por ese motivo la redacción por defecto la producen plantillas deterministas y el modelo es opcional; cada respuesta declara cuál de las dos vías la ha escrito.

## 6. Resultados

### 6.1 Vivienda regional: la precisión depende del esquema de inferencia

| Magnitud | Estimación | Banda 90 % | Muestra |
|---|---|---|---|
| Media regional de crecimiento | 1,2151 % | [0,9008; 1,5295] | 1.387 obs., 19 unidades |
| Media del ajuste (2008T1–2013T4) | −6,4497 % | — | 456 obs. |
| Media de la recuperación (2014T1–2026T1) | 4,9694 % | — | 931 obs. |
| Tasa de reversión AR | 0,2039 | [0,1811; 0,2268] | 1.311 pares |

El contraste de dependencia común cambia la lectura:

| Bloques del bootstrap sincronizado | Banda 90 % | ¿Contiene el 3 %? |
|---|---|---|
| 4 trimestres | [−1,34; 3,85] | sí |
| 8 trimestres | [−2,14; 4,49] | sí |
| 12 trimestres | [−2,70; 4,77] | sí |

La banda primaria excluye el 3 % de la calibración heredada; las tres bandas sincronizadas lo incluyen. **El rechazo del 3 % no es robusto al tratamiento de la dependencia temporal común.** Estas cifras describen la muestra, no una ley de largo plazo. [Resultados](eval/housing-robustness.json).

![Incertidumbre de la media regional según el esquema de remuestreo](deck/figures/housing-uncertainty.svg)

### 6.2 Transferencia neuronal: resultado negativo conservado

| Horizonte | Red | Tendencia | Regiones ganadas | Regla |
|---|---|---|---|---|
| ≤ 4 trimestres | MASE 0,4000 | MASE 0,3953 | 5/17 | 12/17 |
| 5–8 trimestres | MASE 0,8421 | MASE 0,7960 | — | — |

La red no satisface la regla. Las medias MASE incluyen la serie Nacional; el conteo de victorias la excluye. No se presenta una diferencia estadísticamente significativa ni una derrota universal del aprendizaje profundo: se documenta el resultado de esta arquitectura bajo este protocolo. El tramo final 2024–2025 sigue pendiente de evaluación. [Artefacto](eval/t1-dl-global.json).

### 6.3 Impago soberano: discriminación moderada, sin calibración

AUC agrupada por países **0,6736**, desviación entre particiones 0,0308, *average precision* **0,1945** sobre una frecuencia base de 0,0973, en 3.874 observaciones, 154 países y 377 eventos. La desviación entre particiones no es un intervalo de confianza. No hay validación temporal, calibración española ni comparador logístico. [Artefacto](eval/distress.json).

La puntuación que el sistema produce para España es **0,017409** en escala 0–1, sobre la fila de 2024 y con cobertura de 8 de 12 características. No debe leerse como un 1,74 % de probabilidad de impago ni como «seis veces menos riesgo» que ningún otro país: la población etiquetada es selectiva, España queda fuera de ella y la transferencia no está validada. Mostrar esta cifra en la interfaz es una decisión discutible, y retirarla dejándola sólo en la matriz de evidencia sería defendible.

### 6.4 Dependencia del estado: sin capacidad predictiva demostrada

$R^2$ entre países de **−0,0074**, por debajo de la referencia de media implícita. El intervalo bootstrap de la diferencia de pendientes entre deuda alta y baja, **[−0,0309; 0,0537]**, incluye cero. Esto no demuestra igualdad causal ni valida la constante del motor; y la falta de capacidad predictiva limita directamente cuánto puede interpretarse de las pendientes SHAP obtenidas del mismo modelo. [Resultados](eval/state_dependence.json).

### 6.5 Incertidumbre Monte Carlo: los supuestos dominan

| Persistencia $\rho$ | Anchura p5–p95 de deuda en 2050 |
|---|---|
| 0,50 | 21,53 pp de PIB |
| 0,80 | 49,33 pp de PIB |
| 0,96 | 127,40 pp de PIB |

Manteniendo la escala de perturbación, la anchura se multiplica por seis al variar un solo supuesto. La sensibilidad a supuestos puede dominar la precisión numérica. [Informe](eval/montecarlo-sensitivity.json).

![Sensibilidad de la anchura de la banda a los supuestos](deck/figures/montecarlo-sensitivity.svg)

### 6.6 Recuperación y generación

| Métrica | Valor | Alcance real |
|---|---|---|
| Hit@8 por título | 34/35 = 97,14 % | recuperación de documento, no exactitud de respuesta |
| MRR | 0,7820 | mismo conjunto de desarrollo |
| Top-1 | 68,57 % | mismo conjunto de desarrollo |
| Primeras frases citadas con respaldo | 10/12 | una frase por respuesta, juez automático |
| Proporción media de frases citadas | 92,71 % | presencia de cita, no respaldo |
| Referencias fuera de rango | 0 | integridad formal |
| Rechazos de preguntas no respondibles | 4/4 | comportamiento esperado |

Las 35 preguntas participaron en el ajuste de pesos y glosario: son conjunto de desarrollo, no prueba independiente, y el hit@8 debe leerse como **cota superior, no como estimación**. Tampoco se han vuelto a medir tras los cambios del validador. [Recuperación](eval/rag-eval-2026-08-09.json), [generación](eval/rag-chat-eval.json).

En aislamiento e integridad, el artefacto histórico registra 156 búsquedas de aislamiento sobre un corpus de 474 documentos y 17.848 fragmentos, con 0 fugas observadas entre colecciones y los índices de embeddings y texto completo. Acredita la integridad del índice examinado, no seguridad universal. [Validador](../rag/validation.py).

### 6.7 Coherencia de implementación

La comparación entre el motor de servidor y el de navegador cubre las 40 series en todos los años del horizonte, además de los ocho escenarios ilustrativos. Las anclas fijan el resultado esperado y cualquier divergencia detiene la construcción. Es una prueba de consistencia de implementación: no dice nada sobre la exactitud económica de las trayectorias.

## 7. Discusión

**P1** encuentra respaldo para describir propiedades de la muestra y una fuerte dependencia de las conclusiones respecto al esquema de incertidumbre. El hallazgo más transferible del trabajo es negativo y metodológico: preservar los movimientos nacionales comunes en el remuestreo ensancha la banda regional hasta hacer irrelevante el rechazo del valor heredado. Un resultado que parecía una corrección empírica resulta ser una consecuencia del esquema de inferencia elegido.

**P2** no obtiene evidencia de superioridad neuronal bajo la regla fijada de antemano. La discriminación soberana es moderada, y el modelo de estado carece de capacidad predictiva demostrada entre países. Estos resultados no son sorprendentes a la luz de la literatura de competiciones de predicción, pero sí lo sería no haberlos publicado: el protocolo se conserva íntegro precisamente porque el resultado fue el que fue.

**P3** dispone de mecanismos verificables de procedencia y consistencia —sumas de comprobación, separación de colecciones, verificación de citas, comprobación numérica de la redacción—, aunque permanecen lagunas en la reconstrucción desde fuentes originales y en la validación independiente del RAG.

La distinción central que atraviesa las tres preguntas es que repetir resultados con una semilla fija acredita reproducibilidad computacional, mientras que interpretar bandas, probabilidades o multiplicadores requiere supuestos adicionales. Cientos de comprobaciones informáticas no sustituyen un diseño de validación estadística. Que la capa de lenguaje rechace una de cada cinco redacciones por introducir aritmética propia ilustra el mismo punto en otro registro: la fluidez del texto y la corrección de sus cifras son propiedades independientes, y sólo la segunda puede comprobarse automáticamente.

## 8. Limitaciones

1. **Núcleo fiscal calibrado.** Cinco de los ocho parámetros examinados no son identificables con los datos congelados. Los rangos de las palancas incorporan juicio del modelizador.
2. **Escenarios condicionales, no previsiones.** Las trayectorias son implicaciones de supuestos mantenidos. No incorporan cambios de régimen, reacción de política ni incertidumbre paramétrica completa.
3. **Bandas sin cobertura empírica demostrada.** Los percentiles Monte Carlo son distribucionales, no intervalos con cobertura verificada en datos reales.
4. **Evaluación RAG sobre conjunto de desarrollo.** Las métricas publicadas no constituyen prueba independiente y no se han reejecutado tras los cambios del validador.
5. **Sin anotación humana.** La fidelidad de las citas fue juzgada por un segundo modelo de lenguaje, no por personas.
6. **Impago soberano sin validación temporal ni calibración**, y sin comparador logístico.
7. **Reconstrucción del pipeline original incompleta**, instalación limpia no verificada, integración continua definida pero no ejecutada en remoto.
8. **Regla de éxito no registrada externamente.** Fijada antes del resultado en el repositorio, pero sin depósito en un registro independiente.
9. **Utilidad educativa no medida.** No se ha realizado ningún estudio con usuarios.
10. **Componentes descriptivos** —HMM, SHAP, análogos— sin validación prospectiva de ningún tipo.

No se afirma que el modelo mida la eficiencia del gasto público, que identifique los efectos causales de las palancas ni que pronostique la economía española hasta 2050.

## 9. Conclusiones y líneas futuras

La aportación es una plataforma reproducible desde artefactos conservados, acompañada de protocolos que permiten auditar resultados positivos, negativos y dependientes de supuestos. Tres conclusiones concretas:

1. **Preservar los movimientos nacionales comunes cambia sustancialmente la incertidumbre regional**, y con ella la conclusión sustantiva sobre el crecimiento inmobiliario de largo plazo. Es el hallazgo metodológico más claro del trabajo.
2. **Declarar qué no se puede estimar es un resultado.** Tres de ocho parámetros son identificables; publicar los cinco restantes como calibrados, con su motivo, es más informativo que publicar coeficientes que los datos no sostienen.
3. **Separar cálculo de redacción es verificable y merece la pena.** La comprobación numérica rechaza en torno a una de cada cinco redacciones generadas, todas ellas por introducir aritmética que no se le había pedido.

Las líneas futuras se ordenan por lo que desbloquean: evaluar una sola vez el tramo inmobiliario reservado tras congelar decisiones; realizar validación temporal y calibración soberana con población justificada y referencia logística; anotar externamente preguntas y pasajes RAG congelados, con baseline independiente; comprobar empíricamente la cobertura de las bandas de deuda mediante *hindcasts* por horizonte; completar la reconstrucción de las fuentes originales; y diseñar identificación causal si se pretende interpretar las palancas como efectos de políticas. La utilidad educativa requeriría además un estudio con usuarios. Ninguna de estas tareas se da por realizada.

La [matriz de evidencia](RESULTS.md) resume cada experimento, su alcance y sus pendientes.

## Referencias

- Beers, D., Ndukwe, O. y Berry, J. (2025). [BoC–BoE Sovereign Default Database: What's new in 2025?](https://www.bankofcanada.ca/2025/10/staff-analytical-note-2025-24/). Bank of Canada, Staff Analytical Note 2025-24.
- Cameron, A. C. y Miller, D. L. (2015). [A Practitioner's Guide to Cluster-Robust Inference](https://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015.pdf). *Journal of Human Resources*, 50(2), 317–372.
- FMI (2022). [Staff Guidance Note on the Sovereign Risk and Debt Sustainability Framework for Market Access Countries](https://www.imf.org/-/media/files/publications/pp/2022/english/ppea2022039.pdf). Policy Paper 2022/039.
- Hyndman, R. J. y Koehler, A. B. (2006). [Another look at measures of forecast accuracy](https://robjhyndman.com/papers/mase.pdf). *International Journal of Forecasting*, 22(4), 679–688. DOI: 10.1016/j.ijforecast.2006.03.001.
- Jordà, Ò. (2005). [Estimation and Inference of Impulse Responses by Local Projections](https://www.aeaweb.org/articles?id=10.1257/0002828053828518). *American Economic Review*, 95(1), 161–182. DOI: 10.1257/0002828053828518.
- Lewis, P. et al. (2020). [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://proceedings.nips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html). *Advances in Neural Information Processing Systems*, 33.
- Lundberg, S. M. y Lee, S.-I. (2017). [A Unified Approach to Interpreting Model Predictions](https://proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html). *Advances in Neural Information Processing Systems*, 30.
- Wang, L. et al. (2024). [Multilingual E5 Text Embeddings: A Technical Report](https://arxiv.org/abs/2402.05672). arXiv:2402.05672.

## Anexos

### Anexo A. Matriz de evidencia

La matriz completa —modelo, diseño, muestra, resultado, lectura permitida y artefacto, para cada uno de los catorce experimentos— se publica en [`docs/RESULTS.md`](RESULTS.md), junto con la tabla de siete tareas pendientes y el motivo por el que cada una no se da por completada.

### Anexo B. Parámetros y cambios metodológicos

Los parámetros estimados, con sus bandas y muestras, están en [`data/gold/estimated_params.json`](../data/gold/estimated_params.json). El registro de correcciones metodológicas —contabilidad de intereses, etiquetado del tipo bancario, unidades del diferencial, semántica de `omega`, retirada de la bonificación por palanca, política de no imputación y cambios del contrato de la API— está en [`docs/METHODOLOGY_CHANGES.md`](METHODOLOGY_CHANGES.md).

### Anexo C. Reproducción

El entorno, los comandos y el mapa de qué regenera cada análisis, con sus límites conocidos, están en [`docs/REPRODUCIBILITY.md`](REPRODUCIBILITY.md). La verificación de integridad se ejecuta con `scripts/check_data_integrity.py` y no requiere descargas ni el corpus privado.

### Anexo D. Corpus documental

El manifiesto del corpus —81 entradas con fichero, tamaño, suma de comprobación, tema, decisión de inclusión y motivo— está en [`docs/CORPUS_MANIFEST.csv`](CORPUS_MANIFEST.csv). Las colecciones con derechos de autor no se publican; el índice desplegado por defecto se construye desde una lista explícita de documentos propios del proyecto.
