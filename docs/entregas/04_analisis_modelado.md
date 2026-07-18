# Entrega 4 — Diseño del análisis y estrategia de modelado

*Entrega incremental: [01](01_ideas_producto.md), [02](02_datos_necesarios.md) y [03](03_modelo_datos.md) se conservan sin modificar. Los cambios de alcance respecto a la Entrega 2 están documentados y justificados en el [anexo de transición](anexo_transicion_proyecto.md), que responde además al [feedback del tutor del 12-jul](feedback_tutor_2026-07-12.md); la validación del alcance ampliado queda sometida al tutor. Este diseño se estructura sobre **dos tareas de modelado**: la heredada directamente del proyecto avalado (T1, forecasting CCAA) como columna vertebral, y la del programa ampliado (T2, rendimiento ajustado del gasto público) como segunda pieza. Si el tutor prefiriese el alcance original, T1 y todo el §2-A se sostienen solos.*

---

## 1. Problema que se busca resolver

**Qué ocurre hoy.** (a) El precio de la vivienda en España crece por encima de los salarios con divergencias fuertes entre CCAA, y no existe un indicador integrado, actualizable y libre que lo mida ni proyecciones regionales con incertidumbre honesta. (b) A escala internacional, el gasto público se compara casi siempre en bruto (%PIB) o mediante rankings sin ajustar por renta y demografía — comparaciones que informan mal decisiones y debate público.

**Quién usará el resultado y para qué.** Analistas de política de vivienda y fiscal, periodismo de datos y ciudadanía informada. Decisiones que apoya: priorizar regiones en política de vivienda (T1), contextualizar cuánto rinde el gasto de un país frente a sus comparables (T2), explorar consecuencias de sendas de gasto alternativas (extensión D1). El proyecto **no prescribe políticas**: entrega medidas, proyecciones e intervalos.

**Resultado concreto para considerarse útil.** (1) Índice de asequibilidad por CCAA actualizado + su previsión trimestral a 1–2 años con intervalos, batiendo a un baseline ingenuo (criterio §7). (2) Atlas de evolución del gasto (siglos XX–XXI) con 15 figuras reproducibles. (3) Rendimiento ajustado por país con intervalo conformal — nunca una "liga".

## 2. Análisis de datos planteado y utilidad esperada

### 2-A. Vivienda / asequibilidad (núcleo avalado)
| Pregunta | Análisis | Utilidad / MVP |
|---|---|---|
| ¿Cuánto se ha deteriorado la asequibilidad y dónde? | Serie `ratio_asequibilidad` (IPV/salario indexado, aproximado por diseño — feedback del tutor) por CCAA 2008–2025; heatmap CCAA×año; ranking | Figura central del MVP + tabla gold |
| ¿El ratio aproximado cuenta la misma historia que el esfuerzo real? | Contraste con la **cuota hipotecaria teórica** ([PLAN_MAESTRO §7](../PLAN_MAESTRO.md)) y el esfuerzo BdE como validación externa | Responde directamente al feedback; robustez del indicador |
| ¿Qué CCAA divergen y desde cuándo? | Rupturas (test de Chow/CUSUM) alrededor de 2014 y 2021 | Segmentación para el forecasting (¿pooling o por CCAA?) |
| ¿Qué relación tienen Euríbor, IPC y salarios con el IPV? | Correlaciones cruzadas con retardos; causalidad de Granger exploratoria | Selección de exógenas de T1 |
| Estacionalidad y estacionariedad | ACF/PACF, test ADF por CCAA, descomposición STL | Especificación SARIMAX (órdenes d, D, s) |

### 2-B. Programa fiscal (alcance ampliado)
| Pregunta | Análisis | Utilidad / MVP |
|---|---|---|
| ¿Cómo evolucionó el gasto público en los siglos XX–XXI? | Tabla de eras ya calculada sobre `gold_century_fiscal` (mediana mundial 10,2 %PIB → 29,8 %PIB); trayectorias por país; deuda España 1900→hoy | Atlas (15 figuras, fase F2) |
| ¿Existen tipologías de gasto? | PCA + clustering sobre composición funcional (COFOG) | Contexto del modelo T2; figura MVP |
| ¿Más gasto sanitario → mejores resultados, ajustando por renta? | Dispersión GHED vs mortalidad tratable/e0, por grupo de renta | Motivación y sanity check de T2 |
| Hipótesis a comprobar | (H1) la asequibilidad empeora más donde más crece la demanda exógena; (H2) el gasto rinde con retornos decrecientes en renta; (H3) la composición (inversión vs corriente) importa tanto como el nivel | H1→T1 exógenas; H2/H3→T2 (SHAP sobre shares) |

**Cómo alimenta al modelado:** 2-A fija las exógenas, la transformación (niveles vs Δlog) y el esquema de pooling de T1; 2-B fija controles, grupos de calibración y features de T2. Análisis post-modelado en §7 (errores por segmento).

## 3. Modelos planteados

**Regla maestra (PLAN_MAESTRO §3): el n efectivo decide la herramienta.** Panel T1 = 17 series × 72 trimestres; panel T2 ≈ 190 países × 20–25 años → GBM es el techo razonable de complejidad; el DL entra solo como comparador honesto en T1, y es extensión, no núcleo (feedback: MVP primero).

### T1 — Forecasting del IPV trimestral / asequibilidad por CCAA (regresión temporal)
| Alternativa | Tipo | Por qué se plantea | Limitación principal |
|---|---|---|---|
| **Baseline 1: naive estacional** (valor del mismo trimestre del año anterior) + **baseline 2: drift** (tendencia lineal reciente) | Regla simple | Referencia mínima; el IPV es persistente y tendencial → difícil de batir trivialmente, como pide el enunciado | Ignora Euríbor, IPC y salarios |
| **Candidato 1: SARIMAX por CCAA** con exógenas (Euríbor, IPC; salario interpolado) | Interpretable, clásico | Estándar en series macro cortas; coeficientes legibles; maneja estacionalidad y exógenas | Una especificación por CCAA; no comparte información entre regiones |
| **Candidato 2: LightGBM global** sobre el panel apilado (lags, estacionalidad codificada, dummies CCAA y COVID) | Flexible | Pooling: aprende patrones comunes a las 17 CCAA (n efectivo ×17); captura no linealidades (umbral de tipos) | Menos interpretable (mitigado con SHAP); riesgo de sobreajuste en panel corto |
| *(Extensión, no núcleo)* comparador DL: N-BEATS/DeepAR | DL | Comprobar si la complejidad extra aporta algo con n pequeño — resultado esperable: no; valor didáctico | Coste alto, n insuficiente; JAMÁS bloquea el núcleo |

### T2 — Rendimiento ajustado del gasto público (regresión de corte transversal/panel)
| Alternativa | Tipo | Por qué se plantea | Limitación principal |
|---|---|---|---|
| **Baseline: mediana del grupo de renta** + **OLS** (outcome ~ gasto + PIB pc + demografía) | Regla simple / lineal | Referencia mínima y primera aproximación explicable | No captura no linealidades ni interacciones |
| **Candidato 1: GAM** (splines sobre renta y gasto) | Semi-interpretable | Retornos decrecientes (H2) con forma funcional visible | Interacciones limitadas |
| **Candidato 2: LightGBM + SHAP + conformal por bloques** | Flexible | Interacciones y umbrales; el residual = rendimiento ajustado; intervalo conformal por país calibrado por grupo de renta | Interpretabilidad vía SHAP, no coeficientes; sensibilidad a especificación (mitigada con multiverso §6) |

## 4. Datos de entrada

| | T1 | T2 |
|---|---|---|
| Dataset gold | `storage/gold/gold_ccaa_trimestral.csv` | `storage/gold/gold_panel_wide.csv` (+ GHED en `processed/`) |
| Granularidad (1 fila =) | una CCAA en un trimestre (17 × 72, 2008T1–2025) | un país en un año |
| Clave / fecha | (`ccaa`, `periodo` YYYY-Qn) | (`iso3`, `anio`) |
| Entradas principales | lags 1–4 del IPV; Euríbor 12m (media trimestral); IPC CCAA; salario anual interpolado + `salario_flag`; dummies estacionales, CCAA y COVID (2020T1–2021T2) | gasto %PIB (medias 5a, retardos 3–5 años), composición COFOG, PIB pc PPS, estructura etaria, GHED; controles de confusores (Gini, gasto privado) |
| Transformaciones | Δlog del IPV si ADF lo exige (decisión en EDA §2-A); re-base 2015=100 ya hecha en gold | estandarización intra-fold; features de retardo calculadas SOLO con años ≤ t |
| Variables excluidas y motivo | drivers V2 (suelo, ICSC, % extranjeros): NaN parcial, deseables no imprescindibles (E2 §2); Ceuta/Melilla: sin salarios EES (E3 §7.5) | indicadores compuestos de gobernanza como *feature* (riesgo de circularidad); microdatos (privacidad, E2 §4) |
| Disponible en el momento de predecir | Euríbor e IPC del trimestre t: sí (publicación mensual); salario del año en curso: NO → entra interpolado/`provisional` y el último año se marca; IPV hasta t−1 (publicación ~2 meses) | outcomes con 1–2 años de retraso → el "presente" de T2 es t−2; se declara en toda figura |

**Guardas anti-fuga:** ninguna feature usa información posterior al origen de predicción; el salario `provisional` nunca entra en el conjunto de evaluación como observado; `storage/raw/vintage_manifest.csv` fija qué versión del dato existía en cada descarga.

## 5. Salida del modelo y uso en el MVP

Formato: CSV en `storage/gold/` (contrato de datos) + endpoint FastAPI (`api/`) + figuras del informe. Salida principal de T1 (`gold_forecast_ccaa.csv`):

| Campo de salida | Descripción | Tipo | Uso posterior |
|---|---|---|---|
| `ccaa` | Unidad predicha (17 CCAA + Nacional) | str | Trazabilidad, unión con el resto del proyecto |
| `periodo_origen` / `periodo_pred` | Último dato usado / trimestre predicho (h = 1–8) | str | Control de horizonte |
| `ipv_pred` | Predicción puntual del IPV (base 2015=100) | float | Serie proyectada en dashboard |
| `pi_80_low/high`, `pi_95_low/high` | Intervalos de predicción | float | Comunicación honesta de incertidumbre |
| `ratio_aseq_pred` | Ratio de asequibilidad implícito (con salario escenario) | float | Indicador aproximado + escenarios |
| `cuota_teorica_pct` | Cuota hipotecaria teórica / salario (complemento, feedback tutor) | float | Medida de esfuerzo real de compra |
| `escenario` | `central` / `euribor+150pb` / `salarios+2%` … | str | Motor de escenarios del MVP |
| `modelo`, `fecha_ejecucion` | Modelo ganador y momento de generación | str, datetime | Reproducibilidad |
| `explicacion` | Exógenas dominantes del tramo (coefs SARIMAX o top-3 SHAP) | texto | Interpretación por el usuario |

T2 produce `gold_rendimiento_pais.csv` análogo: `iso3`, outcome esperado vs observado, **residual ajustado + intervalo conformal 90 %**, grupo de renta, top-3 SHAP — se muestra SIEMPRE con el intervalo (funnel plot), nunca como ranking ordinal seco. El usuario del MVP ve: mapa/heatmap, serie con abanico de predicción, escenarios y, en T2, el funnel con su incertidumbre.

## 6. Estrategia para diseñar y seleccionar el modelo

1. Congelar el dataset de modelado desde gold (commit + vintage).
2. EDA §2-A → decisiones de especificación (transformación, pooling, exógenas), **antes** de ver métricas de test.
3. Construir baselines y registrar su MASE/MAE — son la vara de medir.
4. Entrenar candidatos (pocos, justificados §3) con hiperparámetros por validación, sin tocar test.
5. **Pre-registro (contra el "metric chasing"):** métrica principal, esquema de validación y criterio de aceptación quedan fijados en ESTA entrega (§7), antes de ejecutar la comparación. El test se evalúa UNA vez, al final.
6. Regla de selección: gana el modelo con mejor MASE medio en validación; ante empate ≤5 % relativo, gana el MÁS SIMPLE (parsimonia e interpretabilidad).
7. T2 además: multiverso de especificaciones (3 definiciones de gasto × conjuntos de controles × retardos) y estabilidad de los residuales entre especificaciones (Spearman) — un "hallazgo" que no sobrevive al multiverso no se publica.
8. Análisis de errores del ganador (§7) antes de integrarlo en el MVP.

## 7. Validación, métricas y criterios de aceptación

| Elemento | Decisión prevista | Justificación |
|---|---|---|
| Separación de datos (T1) | **Backtesting rolling-origin**: orígenes 2019T4→2023T4, horizontes h=1–8; test final = últimos 8 trimestres, evaluado una sola vez | Imita el uso real; evita contaminación temporal; varios orígenes ≫ un único split en series cortas |
| Separación de datos (T2) | **Leave-One-Country-Out** + bloques temporales (entrena ≤t, evalúa >t); nunca el mismo país en train y test del mismo fold | La unidad que no debe fugarse es el país; los bloques evitan mirar el futuro |
| Métrica principal | **MASE** vs naive estacional (T1); **MAE** vs baselines OLS/mediana (T2) | Comparable entre CCAA con escalas distintas; refleja "¿aporto algo sobre lo trivial?" |
| Métricas secundarias | RMSE, sesgo medio, **cobertura empírica de los intervalos** (80/95 % T1; 90 % conformal T2) | Un intervalo que no cubre lo prometido es peor que no darlo |
| Baseline | Naive estacional + drift (T1); mediana de grupo + OLS (T2) | §3 |
| Criterio de aceptación (T1) | **MASE < 1 en h≤4 en ≥12 de 17 CCAA** y cobertura del PI 80 % dentro de [72, 88] % | Mejora real sobre lo trivial en la mayoría de regiones, incertidumbre honesta |
| Criterio de aceptación (T2) | MAE(GBM) ≤ MAE(OLS) − 10 % **y** Spearman ≥ 0,8 de los residuales a través del multiverso | Si la flexibilidad no mejora, se publica el OLS; si el rendimiento ajustado no es estable, no se publica como hallazgo |
| Análisis de errores | Error por CCAA, por horizonte y por periodo (pre/post-COVID; pre/post-2022 tipos); en T2, por grupo de renta y chequeos residual⊥renta, residual⊥capacidad estadística | Detecta dónde falla el modelo y si el "rendimiento" es artefacto |
| Si nada alcanza el mínimo | Se publica el resultado negativo con su análisis (por qué el IPV regional no se predice mejor que naive), el MVP degrada a atlas + índice + escenarios sobre baseline — sigue siendo un entregable completo y honesto | La utilidad del proyecto no depende de inflar una métrica |

## 8. Riesgos y alternativas

| Riesgo | Concreción en este proyecto | Alternativa/mitigación |
|---|---|---|
| Variable objetivo con retraso | IPV publica ~2 meses; salario EES ~1,5 años (E2 §5) | Horizontes desde t−1; salario por escenarios + flag; el último año siempre `provisional` |
| Fuga por interpolación salarial | El salario trimestral interpolado usa el dato anual "futuro" dentro del año | En backtesting, el salario del año del origen entra como provisional (extrapolado), no interpolado con el dato final |
| Panel corto para ML/DL | 72 trimestres; DL con n insuficiente | GBM global con pooling; DL solo comparador; regularización + pocas features |
| Rupturas estructurales | COVID 2020–21; ciclo de tipos 2022 | Dummy COVID; evaluación por sub-periodos; no extrapolar reglas pre-2022 sin test |
| Cambios en la fuente | INE renumeró 49300/76201 → 80271/80270 (riesgo declarado en E2 que SE MATERIALIZÓ; mitigación funcionó) | Cliente parametrizado + snapshots + vintage manifest |
| Endogeneidad/causalidad (T2) | Gasto y outcome se causan mutuamente | Lenguaje asociativo SIEMPRE; retardos 3–5a; límites en primera plana (PLAN_MAESTRO §6) |
| Goodhart / mal uso del ranking | Un funnel leído como liga | Intervalos obligatorios en toda visualización; sin ordinales secos; disclaimer en el MVP |
| Sobre-alcance (riesgo nº 1, §6.1 del plan) | Programa ≫ TFM | Núcleo = atlas + T1 + T2 base; todo lo demás extensión etiquetada; calendario F0 con buffer |

**¿Y si el enfoque entero fallara?** El fallback declarado en el [anexo](anexo_transicion_proyecto.md) §6 sigue vigente: el proyecto vivienda original (avalado) es entregable por sí solo con T1 + análisis 2-A.

---

## Revisión 1 (2026-07-18, posterior a la presentación de la entrega)

*El enunciado pide explicar los cambios manteniendo la trazabilidad: la versión presentada queda congelada en el tag `entrega-4` del repositorio; esta revisión añade, no sustituye.*

**Cambio: incorporación de la oferta privada de vivienda.** El diseño presentado modela la demanda (Euríbor, IPC, salarios) pero no la construcción privada, que produce la inmensa mayoría de la vivienda nueva en España — una variable omitida relevante para T1 y un posible confusor para T2. Se corrige así (detalle en [PLAN_MAESTRO §7.4](../PLAN_MAESTRO.md)):

| Sección afectada | Qué cambia |
|---|---|
| §2-A (análisis) | Nueva hipótesis **H4**: la respuesta de la oferta privada (visados → viviendas terminadas, con ~18–24 meses de retardo) amortigua el crecimiento del precio; se analiza su correlación cruzada con el IPV por CCAA |
| §3 / §4 (T1) | Nuevo driver de oferta V2 `oferta_nueva`: visados de obra nueva y viviendas iniciadas/terminadas (MITMA, Boletín Estadístico ya usado para suelo e ICSC; mensual, provincial → CCAA). El retardo natural visado→terminación lo hace utilizable como feature adelantada sin riesgo de fuga. Driver deseable: su ausencia no bloquea el núcleo (mismo contrato V2 de la Entrega 2) |
| §2-B (atlas) | La figura de inversión pública en vivienda (GF06) se muestra siempre junto a la inversión residencial TOTAL (Eurostat `nama_10_an6`, FBCF en viviendas), para no sobredimensionar la palanca pública |
| §7 (T2, errores) | La inversión residencial privada se añade a la auditoría de confusores en los outcomes de vivienda |
| §8 (riesgos) | Nuevo riesgo: *variable omitida de oferta* — mitigado con H4 + driver V2; si los datos de visados no llegan a tiempo, se declara la limitación en la memoria y las conclusiones de T1 se formulan condicionadas a la demanda |
