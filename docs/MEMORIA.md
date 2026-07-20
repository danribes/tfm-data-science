# El precio de lo público
## Memoria del Trabajo de Fin de Máster — v0.1 (borrador)

*Máster en Data Science (Evolve, enero 2026) · Daniel Ribes · Repositorio: [github.com/danribes/tfm-data-science](https://github.com/danribes/tfm-data-science)*

---

## Resumen

Este trabajo responde, solo con datos públicos, a una pregunta de interés general: **¿qué obtiene un país —y cada comunidad autónoma— a cambio del dinero público que gasta y recauda?** El resultado es un sistema que cualquiera puede usar: un panel interactivo, publicado en internet, donde se pueden plantear preguntas del tipo «¿y si los salarios suben un 2 %?» o «¿y si se recortan a la mitad las ayudas sociales?» y obtener una estimación con su margen de error. Por debajo reúne más de 40 fuentes oficiales (entre otras el INE, Eurostat, el Fondo Monetario Internacional, la OMS y el Banco Mundial), reconstruye la evolución del gasto y los ingresos públicos de España desde 1703 hasta hoy, y mide qué resultados sociales —esperanza de vida, pobreza, pobreza infantil, aprendizaje— compra realmente ese dinero en cerca de 200 países.

Los hallazgos son concretos y a menudo contraintuitivos: la vivienda no se vuelve asequible sola, ni siquiera con los salarios creciendo al 4 %; el dinero público que España dedica a construir vivienda es una fracción mínima de lo que invierte el sector privado; entre países, lo que más explica la salud y la caída de la pobreza es la renta, más que el gasto público; y la trayectoria de la deuda depende sobre todo del envejecimiento de la población, por encima de cualquier decisión fiscal concreta. El sistema también localiza señales que se adelantan a los cambios —por ejemplo, la aceleración del crecimiento de la población anticipa las subidas del precio de la vivienda unos dos años y medio.

La aportación central no es un único modelo «ganador», sino un método fiable para saber **cuándo una predicción es de fiar y cuándo sería un espejismo**. Las reglas del juego se fijaron antes de mirar los resultados y luego se dejó que descartaran los modelos más vistosos: cinco modelos sofisticados —incluida una red neuronal entrenada con 1.760 series de precios de otros países— compitieron contra el método más simple posible (suponer que las cosas siguen su tendencia reciente) y ninguno lo superó de forma fiable; en una ocasión ese rigor evitó publicar una predicción de desplome de precios justo cuando el mercado estaba en pleno auge. Por eso el modelo que se entrega es sencillo: no por falta de alternativas, sino porque ganó una competición justa. Esa honestidad —decir con la misma claridad lo que se sabe y lo que no— es lo que separa a este sistema de una respuesta improvisada de una inteligencia artificial, y se demuestra con un experimento propio: sin los datos y los cálculos del sistema, un modelo de lenguaje solo acierta 3 de 12 preguntas; con ellos, 11 de 12.

## 1. Introducción y evolución del proyecto

### 1.1 El problema
El precio de la vivienda en España crece sistemáticamente por encima de los salarios, con divergencias fuertes entre comunidades autónomas, y no existe una herramienta pública, libre y actualizable que integre precio, salarios e inflación en un indicador regional con proyecciones e incertidumbre honesta. A escala internacional, el gasto público se compara casi siempre en bruto (%PIB) o mediante rankings que ignoran renta y demografía.

### 1.2 De la vivienda al programa
El proyecto avalado en las entregas 1–3 fue un **índice de asequibilidad de vivienda por CCAA**. Durante su construcción emergió la pregunta más general que lo contiene: la vivienda es una partida más (COFOG GF06) junto a sanidad, pensiones o intereses de la deuda, y los mismos ingredientes — ETL reproducible sobre APIs públicas, índices comparables, forecasting con escenarios — escalan del INE a Eurostat + FMI + histórico 1870–2023 sin cambiar de línea tecnológica. La transición **conserva el proyecto de vivienda completo como núcleo** (es el módulo con protocolo de modelado más exigente de la memoria) y está documentada con su trazabilidad en `docs/entregas/anexo_transicion_proyecto.md`.

### 1.3 El feedback del tutor como especificación
Tres indicaciones del tutor (12-jul) actuaron como requisitos de diseño verificables: (i) el ratio IPV/salario se presenta SIEMPRE como indicador aproximado y se complementa con una medida de esfuerzo real de compra; (ii) MVP primero — núcleo antes que extensiones; (iii) el repositorio es la entrega ("el formato de entrega funciona como un contrato"). Las tres atraviesan la memoria: la advertencia viaja hasta el propio payload de la API, las extensiones (RAG, DL) nunca bloquearon el núcleo, y el repositorio contiene el desarrollo completo con tests del contrato de datos.

## 2. Datos y arquitectura

### 2.1 Capas y contrato
```
connectors/  →  storage/raw  →  storage/processed  →  storage/gold  →  analysis/ · api/ · app/
```
- **raw**: descargas intactas con `vintage_manifest.csv` (fecha y URL de cada descarga — qué versión del dato existía en cada momento).
- **processed**: un fichero por fuente, limpieza trazable (67 datasets).
- **gold**: 23 datasets finales de consumo, con clave primaria verificada y tests automáticos (`tests/`, 95 tests): paneles fiscal europeo y mundial-histórico, panel CCAA trimestral, asequibilidad anual, proyecciones demográficas, y los tres artefactos de resultados (pronóstico, rendimiento, escenarios).

### 2.2 Fuentes principales
INE (IPV, IPC, salarios EES), Banco de España (Euríbor), Eurostat (COFOG, ESSPROS, demografía, EUROPOP2023, FBCF por activo, permisos de construcción), FMI-WEO, OMS-GHED, GHO, Banco Mundial (WDI, WWBI), Global Macro Database y Jordà-Schularick-Taylor (histórico 1870–2023, 202 países), UN DESA (migración), MITMA (suelo, costes).

### 2.3 La calidad de datos como resultado, no como trámite
Tres defectos de pipeline se detectaron y corrigieron durante el trabajo, dos de ellos declarados de antemano como riesgo: (1) el filtrado del IPC promediaba 1.120 series ECOICOP en lugar de la serie general; (2) la serie trimestral del IPV se descargaba pero no se persistía; (3) un patrón multi-carácter en `str.split` de pandas actúa como expresión regular, rompiendo silenciosamente las CCAA de nombre compuesto — el ratio de asequibilidad solo existía en 8 de 18 territorios y una comprobación laxa (`n >= 18`) lo enmascaraba. Los tres tienen hoy test de regresión. Además, el riesgo declarado en la Entrega 2 ("cambio de IDs de tabla del INE") **se materializó** durante el curso (49300/76201 → 80271/80270) y la mitigación prevista (cliente parametrizado + snapshots) funcionó.

## 3. Metodología: el protocolo pre-registrado

La regla que organiza todo el modelado: **los criterios se fijan antes de mirar; endurecerlos a posteriori está permitido, relajarlos no.**

1. **EDA con decisiones vinculantes** (D1 transformación, D2 pooling, D3 exógenas) fijadas antes de comparar modelos.
2. **Baselines difíciles** primero: la vara no fue el naive estacional (MASE 0,89 — la escala, inflada por la crisis 2008–14, lo hacía cómodo) sino el drift (0,40), y el criterio de aceptación se ENDURECIÓ en consecuencia antes de entrenar candidato alguno.
3. **Validación rolling-origin** (17 orígenes 2019Q4–2023Q4, h=1–8) con guardas anti-fuga verificadas por tests (un forecaster-espía comprueba que ningún modelo ve datos posteriores a su origen).
4. **Test final de un solo uso** (2024Q1–2025Q4), intocable durante toda la selección y gastado una única vez con la regla de decisión escrita en el código antes de ejecutar.
5. **Multiverso** en el análisis transversal (3 definiciones de gasto; estabilidad Spearman como requisito para publicar).
6. **Incertidumbre siempre**: abanico empírico por horizonte (asimétrico si los errores lo son), intervalos conformal por grupo de renta, bandas de variantes demográficas.

### 3.1 Cómo se predicen los resultados: directa, encadenada y condicional
Tres arquitecturas conviven y la elección está gobernada por una regla única (detalle en `docs/METODOLOGIA.md`): la predicción **directa** (el objetivo desde su propio pasado, con drivers solo retardados — T1 y todos sus candidatos); la **encadenada** o two-stage (predecir primero los drivers y convertirlos en objetivo con una regresión — D1: proyecciones demográficas × elasticidades entrenadas → presión de gasto → senda de deuda); y la **condicional** (la misma regresión con el driver fijado por el usuario — abanico salarial, palancas de deuda, `POST /scenario`). Encadenar solo compensa cuando el driver es mucho más fácil de predecir que el objetivo: la demografía lo cumple (los mayores de 2050 ya han nacido), los drivers de vivienda no — y el caso límite está medido: ni con los valores verdaderos de los drivers (retardados) ningún candidato batió al drift, luego una cadena con drivers previstos sería estrictamente peor. Cuando la regresión vale pero el driver es imprevisible, se degrada honestamente a máquina condicional en lugar de fingir un pronóstico.

## 4. Resultados

### 4.1 T1 — Pronóstico de asequibilidad por CCAA (el núcleo avalado)
- **EDA**: el ciclo es nacional, la presión es regional (ratio 2024: 0,99 Rioja/Extremadura – 1,35 Madrid; nacional 1,26). El crecimiento del IPV es no estacionario según ADF y KPSS concordantes (persistencia AR(1)=0,61).
- **Selección**: ningún candidato (SARIMAX, SARIMAX+Euríbor, LightGBM global) batió al drift en h≤4 (1/17, 0/17, 0/17 CCAA) — los tres habrían aprobado el criterio original blando. Resultado negativo publicado.
- **Test final**: la hipótesis post-hoc "GBM gana en h≥6" quedó **refutada** (0/17): el GBM pronosticó una caída (≈145→127) en el arranque del mayor boom de la muestra (152→187), por reversión a la media aprendida de la crisis. El protocolo evitó publicar esa predicción.
- **Producción**: drift + abanico empírico 80/95 % (mediana de error +0,5 %→+4,9 % con el horizonte: el drift se queda corto en booms y la banda lo hereda) + escenarios salariales. **Lectura central: el ratio nacional pasaría de 1,26 (2024) a ~1,5–1,6 en 2027 incluso con salarios creciendo al 2 %** — el denominador no compensa el numerador sin cambio de régimen.

![El test final: el GBM pronosticó caída en pleno boom](figures/backtest/b3_test_final.png)

![Pronóstico de producción con abanico empírico](figures/backtest/b4_fan_nacional.png)
- **Señal para la siguiente iteración**: los permisos residenciales (driver `oferta_nueva`, compromiso de la Revisión 1) son la señal adelantada más fuerte encontrada (r=0,57 con 11 trimestres; 3 trimestres de aviso en el único giro de la muestra). Se adoptará solo si lo confirman los datos de 2026+.

### 4.2 Atlas B1–B19 — el siglo del gasto público
Mediana mundial del gasto: ~10 %PIB (1900) → ~30 % (hoy); España 11 → 45,4 %. Deuda española en U (124 % tras 1898, 30 % en 1960, 105 % hoy). Los intereses cayeron de 5 a 2,4 %PIB pese a duplicarse la deuda (el dividendo del euro). La protección social es la partida mayor y la que más crece (14,3 → 18,5 %PIB). La inversión pública fue la variable de ajuste tras 2010 (5 → 3 %PIB). Y la figura exigida por la revisión de oferta privada: **la inversión residencial total española (6 → 11,7 → 3,9 → 5,8 %PIB) es un orden de magnitud mayor que el gasto público en vivienda (1,3 → 0,5 %PIB)** — contexto obligatorio de cualquier conclusión sobre política de vivienda.

![Vivienda: palanca pública vs promoción privada](figures/atlas/b03_vivienda_publica_vs_total.png)

### 4.3 A1 — Rendimiento ajustado del gasto sanitario (164 países)
Bajo las reglas pre-registradas ganó el OLS (el GBM no alcanzó la mejora exigida; tercera victoria consecutiva de lo simple). El hallazgo honesto: hasta el OLS empata con la mediana del grupo de renta — **la renta domina; la "eficiencia" es un efecto de segundo orden**. España: +2,7 ± 3,5 años de esperanza de vida sobre lo esperado — por encima, pero DENTRO de la banda de su grupo: el ejemplo canónico de por qué este análisis se publica como funnel con intervalos y nunca como liga. Solo 16/164 países salen de su banda, y los extremos se explican por epidemiología (VIH) o outperformance conocida (Albania, Costa Rica), no por "gestión".

![Funnel A1: años de vida sobre lo esperado, con intervalo](figures/a1/a1_funnel.png)

### 4.3-bis A2 — Tipologías de composición del gasto
PCA + KMeans sobre las 10 funciones COFOG (% del gasto total, medias 2019–23, 30 países). El hallazgo honesto: **las tipologías son débiles** (mejor silueta 0,20, k=2) — la composición europea es un continuo con dos polos suaves: "inversión y Estado clásico" (miembros de 2004+, asuntos económicos sobre-representados) y "Estado del bienestar maduro" (protección social +3,2 pp; España aquí, con el 40,9 % del gasto en protección social). El eje principal se lee casi como renta + antigüedad en la UE — coherente con A1.

### 4.3-ter Expansión del corpus: educación, SPI y cuota teórica
Tras la Entrega 4 se implementaron los conectores pendientes alcanzables (valor tasado MITMA €/m², SPI, gasto militar, gasto educativo, HLO, AOD donante — ver `docs/DATOS.md`) y con ellos tres piezas nuevas. (1) **Cuota hipotecaria teórica por CCAA** (compromiso con el tutor): con hipoteca tipo de 90 m², LTV 80 %, 25 años y Euríbor 2024 +1 pp, el esfuerzo nacional es el **41,6 % del salario bruto** (Baleares 60,6 %, Madrid 56,0 %); ordena las CCAA casi igual que el ratio índice del panel (Spearman 0,79), validando el proxy y añadiendo la medida en euros. (2) **A1-educación** (157 países): HLO ~ gasto educativo retardado + renta + urbanización bajo LOOCV; el OLS vuelve a ganar (MAE 32,7 puntos; GBM 31,2 y MLP 33,4 no cumplen la regla del −10 %), España queda dentro de banda (+37 ± 78) y los extremos son Vietnam (+111) y Kuwait (−100). (3) **Auditoría SPI declarada en el PLAN**: Spearman(residual A1-salud, SPI) = **+0,08** sobre 163 países — el "rendimiento" estimado no es un artefacto de capacidad estadística; añadir SPI como control tampoco mueve el MAE (2,76→2,75). El contraste "deep learning" (MLP) se ejecutó bajo las mismas reglas pre-registradas y perdió en ambos módulos: con n≈150 países la señal la captura la estructura lineal, y así se defiende.

### 4.3-quater Capas de demanda, crédito y suelo
Segunda expansión (`docs/RESULTADOS_VIVIENDA.md`): compraventas e hipotecas mensuales por CCAA (INE), población trimestral por CCAA desde 1971 (ECP), mercado de suelo trimestral 2004– (MITMA: número, valor, superficie y precio de transacciones), stock de suelo urbanizable planificado por CCAA (SIU 2021 y 2025) y criterios de crédito vivienda (ECB BLS 2003–). Hallazgos descriptivos: la superficie de suelo transmitida sigue a ~1/5 del pico de 2004 (117→25 millones m²) mientras los precios aceleran, y Madrid reduce su suelo urbanizable (9,4 %→8,9 % con cobertura completa) — la restricción de oferta empieza aguas arriba de los visados. El contest de validación con estas capas como features rezagadas produjo el **cuarto resultado negativo pre-registrado** (GBM+demanda 0/17 CCAA vs drift; MASE 0,653 vs 0,395): el modelo de producción sigue siendo el drift, y las capas quedan como valor descriptivo y opción de giro validable solo con datos 2026+.

### 4.3-quinquies Panel internacional de vivienda y suelo
Con BIS (precios reales, 61 áreas, ES desde 1971), OCDE (precio/renta disponible, 50 países) y suelo artificial satelital (OCDE/ESA 2000–2022) se construyó `gold_vivienda_global.csv` (`docs/RESULTADOS_VIVIENDA.md`, figura b18). España: +46 % real desde 2015 y precio/renta 132,5 (2015=100), en la senda portuguesa (+125 %, 178,8) y lejos de la italiana (−3,7 %, 89,1). El dato incómodo: España es también el país núcleo que más suelo artificial ha creado (+120 % desde 2000, el doble que Alemania) — y transversalmente, en 40 países, Spearman(precio/renta, crecimiento de suelo artificial) = +0,01: **urbanizar más suelo no compra asequibilidad**; el cuello de botella es el suelo que llega al mercado (transacciones a 1/5 del pico), no el consumido. Declarado: no existe €/m² comparable abierto ni suelo urbanizable legal armonizado entre países — el SIU español es una rareza estadística.

### 4.3-sexies Deep learning de verdad: dos rutas contra el protocolo
Con las bases que sí permiten entrenar DL (`docs/RESULTADOS_VIVIENDA.md`): (a) **Chronos-Bolt zero-shot** (fundacional, preentrenado en millones de series): MASE h≤4 0,460 — mejor que todo candidato clásico, por debajo del drift (0,395) en todos los horizontes y roto a h≥6; 0/17 CCAA. (b) **DL global entrenado en 1.760 series regionales extranjeras** (FHFA+Zillow+UK, 208.640 observaciones, 113.649 ventanas con objetivo ≤2019Q3, España nunca en el entrenamiento): **empate técnico con el campeón** — MASE h≤4 0,401 vs 0,395, gana en 7/17 CCAA y bate al drift en h=2. No alcanza el criterio (12/17) y no se adopta; es el primer candidato en cinco contests que llega al empate, y la lectura es direccional: el corpus de dominio (ciclos inmobiliarios extranjeros completos) aporta lo que ni las features ricas ni el preentrenamiento genérico aportaron. Revalidación declarada solo con orígenes 2026+; si el ciclo español gira, esta es la apuesta auditable en tiempo real.

### 4.3-septies Desglose fiscal mundial y reconciliación de fuentes
Con la API nueva del FMI se incorporaron el gasto por función COFOG de 89 países (GFS_COFOG, 1972–2025) y los ingresos por tipo de 195 países (WoRLD, 1980–2024), más las Global Revenue Statistics de la OCDE (146 países) como compilación independiente (`docs/RESULTADOS_FISCAL_BIENESTAR.md`). La reconciliación cruzada — 15/15 checks OK en `gold_fiscal_reconciliation.csv` — valida los valores que el proyecto venía usando: Eurostat e IMF coinciden función a función con brechas de 0,03–0,06 pp de PIB; ingresos totales cuadran a 0,3–0,7 pp entre tres fuentes; la única brecha sistemática (Rumanía, 3–4,5 pp vs WEO) es metodológica (caja vs devengo) y queda declarada como regla operativa: Eurostat canónico en la UE, GFS/WoRLD fuera, WEO solo para totales largos y proyecciones. España validada: gasto 2024 con protección social 18,7 y salud 6,3 % PIB; ingresos 2023 = 41,2 % (impuestos 23,6 + cotizaciones 13,2 + resto), con IRPF (8,7) triplicando sociedades (2,9).

### 4.3-octies Series históricas: denominador verificado y empalme 1703–2025
Con los niveles de JST (PIB, ingresos y gasto en moneda corriente) se verificó que los porcentajes son reproducibles desde cifras primarias (recalculado vs publicado: 0,000000 pp en 2.516 país-años) — tenemos el PIB, no ratios opacos. La reconciliación del solape 1995–2020 descubrió la trampa clásica de las series largas y la midió: JST es solo administración central (brecha 21 pp vs Eurostat), WEO salta de perímetro justo en 1995 (ES 12,8→44,5), y GMD es el único continuo en perímetro AAPP (0,04 pp de brecha) → empalme canónico = Eurostat 1995+ + GMD antes (`gold_fiscal_historico.csv`, figura b19, `docs/RESULTADOS_FISCAL_BIENESTAR.md`). España 1703–2025 queda contada en una sola serie: Estado del 10 % en 1900, transición fiscal 1977–1995 (+15 pp en 18 años, el evento del siglo), déficit crónico solo desde el Estado del bienestar, tijera de 11,5 pp en 2012.

### 4.3-nonies Bienestar y pobreza infantil: el marco MPI contra el dinero público
Los 7 bloques del marco bienestar↔pobreza infantil (UN/WB/UNICEF) quedan mapeados a 13 series abiertas + AROPE infantil UE (`docs/RESULTADOS_FISCAL_BIENESTAR.md`), y la frontera A1 se replica en un tercer dominio con el ingreso público (WoRLD) como dinero de entrada: log-mortalidad <5 (185 países) y stunting (124) ~ ingresos + renta + urbanización, LOOCV, conformal por cuartil. El OLS vuelve a ganar en ambos (GBM no cumple; MLP omitido y declarado). España mejor que lo esperado y dentro de banda (−0,51±0,93); los extremos validan el método (Guinea Ecuatorial ≈8,5× la mortalidad esperada para su renta; Guatemala +29 pp de stunting). Descriptivo del marco completo: Spearman(ingresos públicos, dimensión) entre −0,60 (mortalidad) y +0,56 (agua segura), todas las direcciones correctas — más capacidad fiscal, menos privación en las 7 dimensiones, y la frontera identifica quién convierte mejor a renta comparable. Cierra el triángulo del proyecto: gasto por función + ingresos por tipo + resultados de bienestar objetivos.

### 4.4 D1 — Escenarios de deuda 2024–2050
Aritmética r−g con presión demográfica del motor de proyección propio (elasticidades panel UE: pensiones 0,91, sanidad 0,33 sobre la senda 65+ de Eurostat → +6,6 pp de PIB en 2050). El menú: sin envejecimiento 127 % / central 224 % (banda 198–267) / crecimiento 2 % 200 % / consolidación +2,5 pp 172 % / +1 pp inversión a deuda 236 % / tipos 4,5 % 256 %. **La demografía domina cualquier palanca individual** (97 pp de distancia central–contrafactual) y ninguna palanca aislada estabiliza la senda. La pregunta original del proyecto (más vivienda e infraestructura a déficit) queda cuantificada (+12 pp en 2050) en lugar de prescrita o descartada.

![Menú de escenarios de deuda 2024–2050](figures/d1/d1_deuda_escenarios.png)

### 4.4-bis Horizonte 50 años: sobres condicionales de economía y bienestar
El sistema se extiende a 2070 como máquina de sobres condicionales — nunca como pronosticador — con cinco piezas (`docs/RESULTADOS_FISCAL_BIENESTAR.md`): (1) la frontera ingreso→bienestar re-estimada como PANEL within (184 países, FE país+año, CR1): el efecto del ingreso es nulo a 2–5 años y aparece a retardo 8 (−0,0036±0,0015 por pp), ~3× menor que el transversal — simular con el transversal sobrestimaría lo que compra el dinero; la renta domina (γ=−0,51±0,06). (2) Monte Carlo del simulador de deuda con la incertidumbre de parámetros propagada (4.000 trayectorias × escenario; coherente con el menú discreto: central 2050 mediana 231 vs 224, banda 90 % más ancha como debe). (3) Horizonte 2070 (EUROPOP): central mediana 409 % PIB [272–619] — el ancho ES el mensaje. (4) Sobres de bienestar 2050/2070 encadenando solo parámetros within: crecimiento 1 % pc/año → mortalidad <5 −12 %/−21 % vs senda base; la palanca fiscal ±2,5 pp añade ±0,8 % — real pero de segundo orden. (5) Pseudo-backtest de continuidad sobre las DOS ventanas reales de 50 años del panel histórico (1925→1975, 1975→2025): errores medianos 12,7–21,5 pp de PIB congelando, peores extrapolando tendencia (p90 102 pp); España +19 pp (la transición fiscal, invisible para la continuidad). **Calibración fijada: todo sobre a 50 años más estrecho de ~13 pp de PIB finge certeza.** Un solo driver pronosticado (demografía); todo lo demás, palanca expuesta.

### 4.5 El producto (MVP): dashboard publicado, API y arranque garantizado
Tres superficies sobre la misma capa gold. (1) **Dashboard Streamlit de cinco pestañas** (asequibilidad con abanico, atlas, funnel A1, simulador de deuda con palancas, horizonte 50 años con Monte Carlo), **publicado en abierto** en https://tfm-data-science-ufgfhpcvydyrswwzm7t6sz.streamlit.app/ — se redespliega automáticamente con cada push al repositorio. (2) **API FastAPI** con todos los artefactos y el simulador interactivo (`POST /scenario`). (3) **Arranque garantizado con Docker**: `docker compose up --build` levanta dashboard (8501) y API (8010) con los datos dentro de las imágenes — replicar no requiere Python, dependencias ni descargas; también sirve como modo sin-red para la defensa. Las advertencias de método viajan dentro de las respuestas de la API y de cada pestaña: la honestidad es parte del producto, no de la letra pequeña.

### 4.6 ¿Por qué no basta un LLM?

La pregunta obligada hoy: ¿no respondería todo esto un modelo de lenguaje? No, y la diferencia es examinable. Un LLM produce números *recordados o patroneados del texto* con el que se entrenó; este sistema los *calcula* con estimadores específicos sobre datos con cadena de custodia. Cinco diferencias defendibles, cada una con evidencia propia del proyecto:

1. **Procedencia auditable**: cada cifra traza hasta `vintage_manifest.csv` (URL y fecha de cada descarga). La proyección de deuda de Q1 del stress test sale de una edición del WEO que está EN el repositorio; la de un LLM, de una memoria no verificable anterior a su corte de entrenamiento.
2. **Falsabilidad**: las afirmaciones de rendimiento se puntúan out-of-sample (rolling-origin + test final de un solo uso). La mejor prueba de que la evaluación es real es que los modelos propios la **suspendieron tres veces en público** — la respuesta de un LLM no puede suspender un backtest porque nunca se presenta a uno.
3. **Incertidumbre calibrada**: las bandas del abanico son cuantiles de errores medidos, con cobertura comprobable; los intervalos de A1 son conformal por grupo de renta. Un LLM emite *tono* de confianza, no intervalos calibrados.
4. **Reproducibilidad**: mismo código + mismos datos → mismos números, con 95 tests que lo blindan (el tercer bug del parser lo cazó un test; el número erróneo de un LLM es silencioso para siempre).
5. **Rechazo por diseño**: el reframe del Bloque D y los huecos declarados (déficit de vivienda, outcomes educativos) son arquitectura. Un LLM prescribe con soltura qué ministerios suprimir; este sistema pone precio a la pregunta (el 78 % del gasto) y devuelve la elección a la política.

Los objetos entrenados que un tribunal puede examinar: la elasticidad de las pensiones al envejecimiento (0,91 ± 0,19, SE agrupado), los cuantiles de error por horizonte que forman el abanico (aprendidos de 486 errores de backtesting), los residuales LOOCV con su semiancho conformal, la estructura adelantada de los permisos (r=0,57 a 11 trimestres) y los parámetros de los modelos evaluados y RECHAZADOS — el resultado negativo también es conocimiento entrenado.

**Evidencia empírica (ablación, `docs/METODOLOGIA.md`)**: la afirmación anterior se comprobó como experimento. El mismo LLM (gemini-2.5-pro) respondió 12 preguntas cuya respuesta es una salida del sistema, en dos brazos idénticos salvo la capa de conocimiento: sin el sistema acertó **3/12** (error relativo mediano 27 %, con fallos de hasta 2382 %); con los resultados de la capa ML/DL recuperados por RAG, **11/12** (error mediano 0 %). Los fallos del LLM solo son del tipo "plausible pero falso" — proyecta la deuda 2050 en 135 % (ignora la presión demográfica que el motor cuantifica en +97 pp) e inventa una correlación suelo-precio de 0,35 donde el panel mide 0,01. La diferencia no es de matiz: es la capa ML/DL lo que produce los números, y sin ella el LLM se equivoca. Un test permanente (`tests/test_ablacion.py`) falla si esa diferencia desaparece.

**Declaración de uso de IA**: en este proyecto se emplearon asistentes LLM como herramienta de programación y redacción (proceso), nunca como fuente de los números (producto). El asistente RAG (motores configurables: kimi, glm, mimo, gemini) es el papel correcto de un LLM aquí: interfaz de lenguaje natural SOBRE los artefactos calculados — el LLM narra, el sistema calcula.

## 5. Limitaciones

1. **Causalidad**: todo el trabajo es asociativo y descriptivo; los retardos mitigan pero no resuelven la endogeneidad, y así se declara en cada pieza.
2. **El ratio de asequibilidad es un indicador aproximado** de evolución relativa (no incorpora €/m², renta disponible, entrada ni financiación); el complemento de cuota hipotecaria teórica está especificado y pendiente del precio por m².
3. **Regímenes**: el test final demostró que 2024–25 fue una aceleración fuera del régimen de entrenamiento — a 2 años vista, en cambios de régimen, la banda es la parte informativa del pronóstico, no el punto.
4. **n pequeño en el análisis transversal** (164 países): gana lo simple y las bandas son anchas; el paso natural es el panel por bloques quinquenales.
5. **El simulador es determinista y sin retroalimentaciones**: mapa de sensibilidades, no pronóstico. Las bandas del motor de proyección usan el σ residual histórico y NO incluyen la incertidumbre de las elasticidades — los errores estándar agrupados por país son ≈2× los clásicos y así se reportan (la API lo declara en su respuesta).
5-bis. **Hiperparámetros sin optimizar**: los GBM usan configuraciones conservadoras por defecto; con tres rechazos consecutivos del modelo flexible bajo reglas pre-registradas, optimizarlos habría sido buscar la métrica, no la verdad — la decisión es deliberada y se declara.
6. **Falacia ecológica**: nada de lo dicho a nivel país habla de centros, sistemas o personas concretas.

## 6. Conclusiones

1. **El sistema funciona de principio a fin y está publicado.** Cualquiera puede consultarlo, probar sus propios escenarios y ver de dónde sale cada número. Se ha construido solo con fuentes públicas y herramientas abiertas, con una trazabilidad de nivel profesional: cada cifra puede seguirse hasta su descarga original, y todo el proceso se reproduce con un solo comando.
2. **Da respuestas claras a la pregunta de fondo.** La asequibilidad de la vivienda en España no se corrige sola (ni con salarios al 4 %); lo que el Estado gasta en construir vivienda es muy inferior a lo que invierte el sector privado; entre países, la renta explica la salud y la caída de la pobreza más que el propio gasto público; y el envejecimiento de la población pesa sobre la deuda más que cualquier decisión fiscal individual.
3. **La aportación que mejor defiende este trabajo es de método: saber dónde se puede predecir y dónde no.** Se fijaron las reglas antes de mirar y se dejó que descartaran lo vistoso; ganó lo sencillo, y una vez ese rigor evitó anunciar un desplome de precios en pleno auge. En un trabajo de fin de máster, donde la tentación es lucir el modelo más complejo, aquí se demuestra —con evidencia propia— que un modelo sencillo, bien medido y honesto vale más que uno complejo que solo aparenta acertar. Reconocer los límites de lo predecible no es una carencia del trabajo: es uno de sus resultados.

## 7. Trabajo futuro
Pata provincial de visados (MITMA) y evaluación del driver de oferta con datos 2026+; cuota hipotecaria teórica con €/m²; panel quinquenal para A1 y módulos vivienda/educación; episodios históricos de consolidación (D2); actualización trimestral automática del pipeline; registro formal de modelos y versiones (hoy el versionado es git + artefactos gold, suficiente a esta escala pero explícitamente mínimo).

## Referencias

**Fuentes de datos** (versión exacta de cada descarga en `storage/raw/vintage_manifest.csv`):

- Banco de España. *Tipos de interés: Euríbor a 12 meses*. https://www.bde.es
- Eurostat. *Government expenditure by function (COFOG)* (`gov_10a_exp`); *ESSPROS social protection expenditure* (`spr_exp_type`, `spr_exp_func`); *Population projections EUROPOP2023* (`proj_23n`); *GFCF by asset type* (`nama_10_an6`); *Building permits* (`sts_cobp_q`); series demográficas, SILC y de mortalidad evitable. https://ec.europa.eu/eurostat
- Fondo Monetario Internacional. *World Economic Outlook Database*. https://www.imf.org/en/Publications/WEO
- Instituto Nacional de Estadística. *Índice de Precios de Vivienda* (tablas 80270/80271); *IPC* (76136); *Encuesta Anual de Estructura Salarial* (28191). https://www.ine.es
- Jordà, Ò., Schularick, M. y Taylor, A. M. (2017). "Macrofinancial History and the New Business Cycle Facts". *NBER Macroeconomics Annual*, 31(1). Datos: https://www.macrohistory.net
- Ministerio de Transportes y Movilidad Sostenible (MITMA). *Boletín Estadístico: precio del suelo urbano; índice de costes de la construcción*. https://apps.fomento.gob.es
- Müller, K., Xu, C., Lehbib, M. y Chen, Z. (2025). *The Global Macro Database*. https://www.globalmacrodata.com
- Naciones Unidas, DESA. *International Migrant Stock 2024*. https://www.un.org/development/desa/pd
- Organización Mundial de la Salud. *Global Health Expenditure Database (GHED)*; *Global Health Observatory (GHO)*. https://apps.who.int/nha ; https://www.who.int/data/gho
- World Bank. *World Development Indicators*; *Worldwide Bureaucracy Indicators (WWBI)*. https://data.worldbank.org

**Métodos:**

- Angelopoulos, A. N. y Bates, S. (2023). "Conformal Prediction: A Gentle Introduction". *Foundations and Trends in Machine Learning*, 16(4).
- Blanchard, O. (2019). "Public Debt and Low Interest Rates". *American Economic Review*, 109(4).
- Hyndman, R. J. y Athanasopoulos, G. (2021). *Forecasting: Principles and Practice* (3ª ed.). OTexts. https://otexts.com/fpp3
- Hyndman, R. J. y Koehler, A. B. (2006). "Another look at measures of forecast accuracy". *International Journal of Forecasting*, 22(4).
- Ke, G. et al. (2017). "LightGBM: A Highly Efficient Gradient Boosting Decision Tree". *NeurIPS 30*.
- Lundberg, S. M. y Lee, S.-I. (2017). "A Unified Approach to Interpreting Model Predictions". *NeurIPS 30*.
- Tanzi, V. y Schuknecht, L. (2000). *Public Spending in the 20th Century: A Global Perspective*. Cambridge University Press.

## Anexo — Guía de reproducción

**Vía rápida (sin instalar nada más que Docker):**
```
docker compose up --build           # dashboard en :8501 y API en :8010, datos incluidos
```
Demo pública equivalente: https://tfm-data-science-ufgfhpcvydyrswwzm7t6sz.streamlit.app/

**Vía completa (re-ejecutar el pipeline; Python ≥3.10):**
```
python3 -m connectors.<fuente>      # extracción por fuente (raw → processed)
python3 connectors/gold.py          # capa gold + smoke tests
python3 analysis/eda_vivienda.py    # EDA y decisiones D1–D3
python3 analysis/backtest_t1.py     # baselines + harness rolling-origin
python3 analysis/candidates_t1.py   # candidatos (validación)
python3 analysis/final_test_t1.py   # test final (YA GASTADO: no re-ejecutar para seleccionar)
python3 analysis/forecast_t1.py     # pronóstico de producción + abanico
python3 analysis/atlas.py           # figuras del atlas (B1–B19 con suelo e historia)
python3 analysis/rendimiento_a1.py  # A1 salud: funnel 164 países
python3 analysis/expansion_dl.py    # A1 educación + auditoría SPI
python3 analysis/bienestar_a1.py    # frontera ingreso→bienestar (marco MPI)
python3 analysis/bienestar_panel.py # panel within (parámetros de simulación a 50 años)
python3 analysis/escenarios_d1.py   # D1: menú de deuda 2024–2050
python3 analysis/mc_d1.py           # Monte Carlo de deuda hasta 2070
python3 analysis/bienestar_50.py    # sobres de bienestar 2050/2070
python3 analysis/backtest_50y.py    # calibración histórica de continuidad
python3 analysis/fiscal_breakdown.py    # desglose y reconciliación fiscal mundial
python3 analysis/fiscal_historia.py     # empalme histórico 1703–2025
python3 -m pytest tests/ -q         # 95 tests del contrato de datos y modelos
streamlit run app/dashboard.py      # dashboard (5 pestañas)
python3 app/rag_assistant.py "..."  # asistente RAG sobre la documentación del proyecto
```
Los contests DL (`foundation_t1.py`, `dl_global_t1.py`, `demanda_features.py`) son re-ejecutables pero sus veredictos ya están registrados; el test final de T1 está gastado y no debe usarse para seleccionar. Documentos de detalle: los enlazados en la tabla del README, más `docs/METODOLOGIA.md` (cómo se predice), `docs/RESULTADOS_FISCAL_BIENESTAR.md` (sistema a 50 años) y `docs/GUIA_USUARIO.md` (operación del producto).
