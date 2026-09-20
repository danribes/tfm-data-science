# España en escenarios: simulación económica transparente y evaluación crítica de modelos de IA

**Borrador académico para revisión del autor y del tutor.** Estado documental: 20 de septiembre de 2026, motor 1.1.0. No sustituye la memoria aprobada por la universidad. El autor debe completar portada, atribución de contribuciones y uso de herramientas de IA, normativa de presentación y revisión bibliográfica. Los resultados citados proceden de los artefactos indicados; las evaluaciones pendientes se distinguen de las realizadas.

## Resumen

Este trabajo desarrolla y examina una plataforma que integra simulación macroeconómica, análisis regional de vivienda, aprendizaje automático y consulta documental mediante generación aumentada por recuperación. Su finalidad es hacer explícitos los supuestos de escenarios económicos y evaluar qué respaldo empírico ofrecen sus componentes. Se implementan un motor semiestructural reproducible en Python y TypeScript, simulaciones Monte Carlo, estimadores de panel, un modelo neuronal de transferencia internacional, clasificación exploratoria de impago y recuperación documental multilingüe. Los resultados muestran límites sustantivos: la red neuronal no supera el criterio de comparación con una extrapolación de tendencia; la clasificación soberana presenta discriminación moderada, sin calibración validada para España; y la aparente precisión de la media regional de vivienda disminuye al preservar los movimientos comunes en el remuestreo. La contribución consiste en una infraestructura auditable y una evaluación que separa coherencia computacional, descripción histórica, predicción e identificación causal. No se acredita todavía una herramienta de previsión económica ni una mejora educativa medida experimentalmente.

**Palabras clave:** simulación, evaluación predictiva, vivienda, incertidumbre, datos de panel, recuperación documental.

## 1. Problema y preguntas de investigación

Una interfaz económica puede producir cifras precisas sin que sus supuestos estén identificados por los datos. Además, una explicación con citas puede parecer convincente aunque los pasajes no respalden todas sus afirmaciones. El problema abordado consiste en integrar cálculo y evidencia conservando estas distinciones.

Se plantean tres preguntas. **P1:** ¿qué propiedades del motor pueden contrastarse con los paneles disponibles y cuánto dependen de la muestra y del tratamiento de la incertidumbre? **P2:** ¿aportan los modelos de aprendizaje automático mejoras observables frente a referencias explícitas, con qué particiones y para qué población? **P3:** ¿puede la aplicación conservar la procedencia de datos y documentos, evitando presentar coherencia informática como validez científica?

La unidad de contribución es un sistema de investigación aplicada: arquitectura, protocolos de evaluación y resultados interpretados conjuntamente. El trabajo no propone un algoritmo general nuevo. El análisis de deuda se sitúa en una tradición de escenarios y evaluación de riesgos, aunque esta implementación no reproduce ni acredita el marco operativo del FMI. [FMI, 2022](https://www.imf.org/-/media/files/publications/pp/2022/english/ppea2022039.pdf).

## 2. Datos y trazabilidad

La capa española reúne series fiscales, vivienda por comunidad autónoma, demografía y otros indicadores procedentes de fuentes públicas. La fecha `2026-07-31` identifica la referencia del escenario; no demuestra que todos los artefactos añadidos posteriormente se descargaran ese día. Se distinguen fecha de adquisición, periodo observado y fecha de construcción. Los metadatos y las sumas de comprobación permiten identificar los archivos empleados, pero no prueban su autenticidad originaria ni reconstruyen transformaciones históricas ausentes. Véanse [metadatos](../data/ARTIFACT_METADATA.json) y [reproducibilidad](REPRODUCIBILITY.md).

El panel regional de estimación contiene 17 CCAA, Ceuta y Melilla. Se excluye Nacional porque agrega información de las mismas regiones. Las variaciones interanuales utilizables abarcan 2008T1–2026T1: 73 trimestres por 19 unidades, 1.387 observaciones. La media conjunta otorga igual peso a cada observación regional; no equivale a ponderar por población o transacciones. Los periodos de ajuste y recuperación se presentan por separado. [Construcción del panel](../research/panel.py).

Para aprendizaje internacional se conservan 1.760 series inmobiliarias estadounidenses y británicas. Su documentación identifica un procesamiento heredado, por lo que reproducir el entrenamiento desde el archivo congelado y reconstruir la extracción original son objetivos distintos. La clasificación soberana combina indicadores WDI con etiquetas derivadas de la base BoC–BoE, cuya definición incluye distintas modalidades de incumplimiento y reestructuración. Las etiquetas transformadas deben distinguirse de las observaciones originales. [Corpus extranjero](../data/external/README.md), [fuentes de impago](../data/external/README_distress.md), [Beers, Ndukwe y Berry, 2025](https://www.bankofcanada.ca/2025/10/staff-analytical-note-2025-24/).

## 3. Diseño metodológico

### 3.1 Simulación y coherencia computacional

El motor combina una identidad de deuda con reglas calibradas para crecimiento, empleo, inflación, salarios y vivienda. La identidad fundamental es:

\[
b_t=b_{t-1}\frac{1+i_t}{1+g_t}-sp_t,
\]

donde los tipos se expresan aquí en tanto por uno y el saldo primario en puntos de PIB. Mover una palanca produce una trayectoria condicional a estas relaciones; no constituye por sí mismo una intervención causal estimada. Buena parte de los coeficientes y la selección de rangos incorporan juicio del modelizador.

Los intereses sobre el PIB corriente son \(b_{t-1}i_t/(1+g_t)\), y el saldo total resta estos intereses al saldo primario. Esta misma base contable se usa en ambos motores. En combinaciones extremas, la recurrencia puede producir deuda negativa: se señala como salida del dominio de deuda bruta, pues no se modelan activos públicos ni una reacción de política al agotar la deuda.

El port TypeScript permite interacción local. Un conjunto común de anclas verifica la concordancia entre implementaciones; pruebas adicionales contrastan identidades y comportamientos límite. Estas comprobaciones acreditan consistencia del cálculo en los casos examinados, no exactitud económica futura. [Motor](../engine/spain.py), [anclas](../tests/fixtures/engine_anchors.json).

La simulación Monte Carlo genera 4.000 trayectorias con perturbaciones AR(1) de tipos, crecimiento y saldo primario. Su configuración central utiliza persistencia 0,96 y semilla 42. Los percentiles son bandas de simulación condicionadas a distribuciones y reglas calibradas. Una sensibilidad separada varía persistencia, escala, número de trayectorias y semilla, sin afirmar cobertura empírica del 90 %. [Método y resultados](eval/montecarlo-sensitivity.json).

### 3.2 Estimación regional e incertidumbre

Se estima la media de crecimiento y una relación autorregresiva anual mediante efectos fijos regionales. Los intervalos primarios emplean errores agrupados por unidad. Agrupar permite dependencia interna, pero requiere atender también a la dependencia entre grupos y al número de grupos. [Cameron y Miller, 2015](https://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015.pdf).

La tasa de reversión se define como \(r=1-\phi\), siendo \(\phi\) la persistencia. La versión anterior utilizaba el número 0,60 como factor retenido; su tasa comparable es 0,40. La implementación actual conserva \((1-r)^k\) de la desviación inicial. Esta precisión evita intercambiar magnitudes con efectos opuestos.

Como contraste de incertidumbre, un bootstrap circular de 500 réplicas remuestrea bloques comunes de 4, 8 y 12 trimestres. Todas las regiones de cada trimestre se desplazan juntas, conservando la covariación nacional. Las regiones permanecen fijas. El ejercicio supone estabilidad aproximada dentro de cada ventana y crea una unión artificial entre final e inicio; se publica como sensibilidad complementaria. [Implementación](../research/housing_robustness.py).

Las regresiones horizonte a horizonte siguen la organización de las proyecciones locales, pero aquí relacionan crecimiento interanual previo y cambio futuro del logaritmo del precio, descontando las medias regionales. No identifican una innovación exógena. El crecimiento interanual solapado tampoco equivale a un choque trimestral. La comparación con el motor acumula cambios de nivel desde el precio observado en \(t\), presenta sólo puntos anuales y normaliza el primer año: esa coincidencia es impuesta. [Jordà, 2005](https://www.aeaweb.org/articles?id=10.1257/0002828053828518), [implementación concreta](../research/validate.py).

### 3.3 Modelos predictivos y descriptivos

La red inmobiliaria es un perceptrón multicapa: recibe 16 cambios logarítmicos trimestrales y produce ocho cambios acumulados. Se entrena con 113.649 ventanas extranjeras cuyos objetivos terminan como máximo en 2019T3. El backtest utiliza orígenes desde 2019T4, elimina objetivos posteriores a 2023T4 y compara con último valor, ingenuo estacional y tendencia reciente de ocho trimestres. MASE se escala exclusivamente con errores estacionales del entrenamiento. La regla del repositorio exige superar la tendencia en al menos 12 de 17 CCAA para horizontes hasta cuatro trimestres; no se aporta un registro externo independiente de esa regla. [Protocolo](../research/backtest.py), [MASE: Hyndman y Koehler, 2006](https://robjhyndman.com/papers/mase.pdf).

El clasificador soberano utiliza boosting y características de \(t\) para el inicio de impago en \(t+1\), excluyendo años ya en impago. Las cinco particiones separan países, pero mezclan épocas: evalúan transferencia entre países, no anticipación prospectiva. Se conserva una correspondencia local de nombres y códigos; fallos de mapeo detienen el proceso. Su salida se denomina puntuación exploratoria sin calibrar.

Un segundo boosting relaciona estado macroeconómico y crecimiento acumulado a tres años. Las pendientes SHAP por régimen de deuda describen el modelo ajustado; un bootstrap por país vuelve a estimarlo. SHAP atribuye predicciones a variables y no convierte asociaciones endógenas en efectos causales. Los HMM de dos estados y los vecinos históricos son igualmente herramientas descriptivas retrospectivas. [SHAP: Lundberg y Lee, 2017](https://proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html), [análisis aplicado](../research/state_dependence.py).

### 3.4 Recuperación documental

La consulta combina embeddings multilingües E5, búsqueda léxica y fusión de rankings, con separación entre colecciones académicas, metodología y opinión. Esta arquitectura aplica recuperación aumentada, sin reproducir el entrenamiento de los modelos originales. Se comprueban identificadores, citas y pertenencia de pasajes a la colección solicitada. La evaluación distingue encontrar un documento, recuperar un pasaje pertinente y producir una respuesta respaldada. [Lewis et al., 2020](https://proceedings.nips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html), [Wang et al., 2024](https://arxiv.org/abs/2402.05672), [protocolo local](eval/README_RAG.md).

## 4. Resultados

La media regional es **1,215 % anual**. Su banda primaria al 90 % es **[0,901; 1,530]**. Sin embargo, el remuestreo sincronizado produce **[−1,34; 3,85]**, **[−2,14; 4,49]** y **[−2,70; 4,77]** para bloques de 4, 8 y 12 trimestres. Las tres incluyen el 3 % de la calibración previa: **su rechazo no es robusto al tratamiento de la dependencia temporal común**. Las medias de ajuste y recuperación son −6,450 % y 4,969 %. La tasa autorregresiva de reversión estimada es 0,2039, con banda primaria [0,1811; 0,2268]. Estas cifras describen la muestra, no una ley de largo plazo. [Resultados regionales](eval/housing-robustness.json), [parámetros conservados](../data/gold/estimated_params.json).

La red neuronal obtiene MASE **0,4000**, frente a **0,3953** de la tendencia, y gana en **5/17 CCAA**: no satisface la regla. A horizontes de cinco a ocho trimestres registra 0,8421 frente a 0,7960. Las medias MASE del informe incluyen la serie Nacional; el conteo de victorias la excluye. No se presenta una diferencia estadísticamente significativa ni una derrota universal del aprendizaje profundo; se documenta el resultado de esta arquitectura y protocolo. El tramo final 2024–2025 sigue pendiente de evaluación. [Artefacto](eval/t1-dl-global.json).

El clasificador soberano conserva un resultado histórico de AUC **0,674**, desviación entre particiones 0,031 y average precision **0,195**, sobre 3.874 observaciones y 377 eventos. La frecuencia del panel es 9,73 %. No es una referencia poblacional válida para convertir la salida española en una probabilidad relativa: España está fuera del conjunto etiquetado y presenta cobertura incompleta. Las métricas no se recalcularon al corregir su presentación. [Artefacto y advertencias](eval/distress.json).

El modelo de estado presenta \(R^2\) entre países de **−0,0074**. El intervalo bootstrap de la diferencia de pendientes entre deuda alta y baja, **[−0,0309; 0,0537]**, incluye cero. Esto no demuestra igualdad causal ni valida la constante del motor. [Resultados](eval/state_dependence.json).

En Monte Carlo, manteniendo la escala de perturbación, la anchura p5–p95 de deuda en 2050 cambia de **21,53** a **127,40 puntos de PIB** al pasar de persistencia 0,50 a 0,96. La sensibilidad a supuestos puede dominar la precisión numérica. [Informe](eval/montecarlo-sensitivity.json).

El RAG histórico alcanza hit@8 por título **34/35 = 97,14 %**, con MRR 0,782. Las preguntas participaron en el desarrollo: no son una prueba independiente. En generación, un segundo modelo consideró respaldadas **10/12 primeras frases citadas**; no evaluó todas las afirmaciones ni hubo verificación humana. Esos resultados tampoco se han repetido después de los cambios del validador. [Recuperación](eval/rag-eval-2026-08-09.json), [generación](eval/rag-chat-eval.json).

## 5. Discusión y límites

P1 encuentra respaldo para describir propiedades de la muestra y una fuerte dependencia de las conclusiones respecto al esquema de incertidumbre. P2 no obtiene evidencia de superioridad neuronal bajo la regla elegida; la discriminación soberana es moderada y el modelo de estado carece de capacidad predictiva demostrada entre países. P3 dispone de mecanismos verificables de procedencia y consistencia, aunque permanecen lagunas en la reconstrucción desde fuentes originales y en la validación independiente del RAG.

La revisión identifica una distinción central: repetir resultados con una semilla fija acredita reproducibilidad computacional, mientras que interpretar bandas, probabilidades o multiplicadores requiere supuestos adicionales. Tampoco cientos de comprobaciones informáticas sustituyen un diseño de validación estadística. Las calibraciones conservan componentes subjetivos y los escenarios largos omiten posibles cambios de régimen, adaptación de políticas e incertidumbre paramétrica.

Antes de una defensa definitiva deben completarse cuatro tareas: evaluar una sola vez el tramo inmobiliario reservado tras congelar decisiones; realizar validación temporal y calibración soberana con una población justificada y una referencia logística; anotar externamente preguntas y pasajes RAG congelados; y diseñar identificación causal si se pretende interpretar palancas como efectos de políticas. La utilidad educativa también requiere un estudio con usuarios. Ninguna de estas tareas se da por realizada en este borrador.

## 6. Contribución y conclusión

La aportación es una plataforma reproducible desde artefactos conservados, acompañada de protocolos que permiten auditar resultados positivos, negativos y dependientes de supuestos. El hallazgo metodológico más claro es que preservar movimientos nacionales comunes cambia sustancialmente la incertidumbre regional. La plataforma constituye una base útil para explorar escenarios y estudiar modelos; los resultados disponibles delimitan explícitamente las afirmaciones predictivas y causales que todavía no puede sostener. La [matriz de evidencia](RESULTS.md) resume cada experimento y sus pendientes.

## Referencias

- Beers, D., Ndukwe, O. y Berry, J. (2025). [BoC–BoE Sovereign Default Database: What's new in 2025?](https://www.bankofcanada.ca/2025/10/staff-analytical-note-2025-24/). Bank of Canada, Staff Analytical Note 2025-24.
- Cameron, A. C. y Miller, D. L. (2015). [A Practitioner's Guide to Cluster-Robust Inference](https://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015.pdf). *Journal of Human Resources*, 50(2), 317–372.
- FMI (2022). [Staff Guidance Note on the Sovereign Risk and Debt Sustainability Framework for Market Access Countries](https://www.imf.org/-/media/files/publications/pp/2022/english/ppea2022039.pdf). Policy Paper 2022/039.
- Hyndman, R. J. y Koehler, A. B. (2006). [Another look at measures of forecast accuracy](https://robjhyndman.com/papers/mase.pdf). *International Journal of Forecasting*, 22(4), 679–688. DOI: 10.1016/j.ijforecast.2006.03.001.
- Jordà, Ò. (2005). [Estimation and Inference of Impulse Responses by Local Projections](https://www.aeaweb.org/articles?id=10.1257/0002828053828518). *American Economic Review*, 95(1), 161–182. DOI: 10.1257/0002828053828518.
- Lewis, P. et al. (2020). [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://proceedings.nips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html). *Advances in Neural Information Processing Systems*, 33.
- Lundberg, S. M. y Lee, S.-I. (2017). [A Unified Approach to Interpreting Model Predictions](https://proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html). *Advances in Neural Information Processing Systems*, 30.
- Wang, L. et al. (2024). [Multilingual E5 Text Embeddings: A Technical Report](https://arxiv.org/abs/2402.05672). arXiv:2402.05672.
