# PLAN MAESTRO — "El precio de lo público": el documento único

*v1, 2026-07-18. **Documento canónico** que consolida: PLAN_integral (marco, 9 fases), PLAN_vivienda_consecuencias (Variante C, análisis complementario), PLAN_public_money_outcomes A/UE y B/GLOBAL (absorbidos como vistas), RESUMEN_ejecutivo, pitch_tutor_fiscal y el estado real de extracción. Los ficheros originales se conservan como anexos históricos; los esquemas técnicos viven en [data_dictionary_master.md](DATOS.md) y [data_dictionary_vivienda.md](DATOS.md); el inventario completo de fuentes en [data_landscape.md](DATOS.md).*

---

## 1. Preguntas de investigación (consolidadas y de-duplicadas)

### Bloque A — Núcleo de rendimiento (las 4 originales)
| RQ | Pregunta | Método |
|---|---|---|
| A1 | **¿Qué país es el más eficiente gastando el dinero público?** *(nueva #1 ≡ original RQ3 — misma pregunta; se responde como RENDIMIENTO AJUSTADO con incertidumbre, nunca como liga)* | GBM + residual conformal + funnel por grupo de renta |
| A2 | ¿Qué tipologías de gasto existen entre países? | PCA + clustering (N global) |
| A3 | ¿Importa la composición (inversión vs corriente)? ¿Hay umbrales no lineales? | SHAP sobre shares |
| A4 | ¿Cómo pesa la dotación de personal (plantilla × salario)? | features D1 + WWBI |

### Bloque B — Batería de evolución (siglos XX–XXI) — las nuevas preguntas del autor
*Todas descriptivas ("¿cómo ha evolucionado…?"); cada una con su fuente y estado de datos. Periodo: 1900–2023 donde el dato histórico existe (GMD/JST), 1995/2000–2023 en detalle fino.*

| RQ | Pregunta (evolución de…) | Fuente | Estado |
|---|---|---|---|
| B1 | **Gasto público total %PIB, siglos XX y XXI** | GMD (202 países, 158 pre-1995) + JST + Eurostat/WEO | ✅ EXTRAÍDO — tabla de eras ya calculada (mediana mundial 10,2%→29,8%) |
| B2 | **Tipo de gasto** (económica: salarios/bienes/intereses/transferencias/capital) | Eurostat na_item 1995→ (UE); FMI GFS económico (mundo, parcial); histórico solo benchmarks (Tanzi-Schuknecht, Flora) | ✅ UE / ⏳ mundo / histórico = años-referencia |
| B3 | **Inversión en vivienda** | GF06/GF0601 %PIB (UE 1995→; L2 2001→) + GFS reporters | ✅ UE (ES 0,5 vs UE 1,2 documentado) |
| B4 | **Inversión en sanidad** | GHED 195 países 2000→ + GF07 UE 1995→ | ✅ EXTRAÍDO |
| B5 | **Inversión en infraestructuras** | P51G (FBCF) total y por función; GF04 con su caveat de constructo | ✅ UE; proxy global P51G/WEO |
| B6 | **Empleados públicos / población** | WWBI empleo público (%) + demo_pjan | ✅ EXTRAÍDO (ES 24,8% del empleo, 2020) |
| B7 | **Gasto en salarios públicos** | D1 %PIB por función (UE) + WWBI masa salarial (global) | ✅ EXTRAÍDO (ES 10,9 %PIB 2023) |
| B8 | **Deuda pública** | gov_10dd (UE) + WEO (226 países) + GMD/JST (histórico) | ✅ EXTRAÍDO (ES: 124% en 1900, 30% en 1960, 105% hoy) |
| B9 | **Bienestar social (protección social)** | GF10 + ESSPROS `spr_exp_type` | ✅ EXTRAÍDO |
| B10 | **Desempleo** | Eurostat `une_rt_a` + WDI SL.UEM.TOTL.ZS | ⏳ RE-PULL menor (tarea F2.0.1) |
| B11 | **Pago de intereses** | D41PAY (gov_10dd/gov_10a_main) + WEO | ⏳ RE-PULL menor (F2.0.2) |
| B12 | **Pensiones + nº de jubilados** | ESSPROS `spr_exp_func` (vejez) + demo_pjan edad ≥65 + OECD | ⏳ RE-PULL menor (F2.0.3: spr por función + población por edad) |
| B13 | **Migración + nº de inmigrantes** | UN DESA stock (284 destinos 1990–2024) + Eurostat flujos + INE CCAA | ✅ EXTRAÍDO |
| B14 | **Ayuda internacional %PIB** | `oda.csv` (recibida %RNB) + DAC donantes (deferred CRS) | ✅ recibida / ⏳ donante |
| B15 | **Déficit fiscal + deuda total** | B9 + GD (UE), WEO balance (229), GMD déficit histórico | ✅ EXTRAÍDO |

*De-duplicación: la nueva "país más eficiente" = A1; "evolución del gasto %PIB" y "tipo de gasto" amplían el antiguo RQ1; B13 ≡ el amplificador migratorio de la Variante C; B15 solapa con B8 (se tratan juntas). Advertencia B2–B5 histórica: el desglose funcional continuo NO existe antes de ~1970 — solo totales + benchmarks; se declara, no se interpola.*

### Bloque C — Predicción
| RQ | Pregunta | Método |
|---|---|---|
| C1 | ¿Cómo evolucionarán estos parámetros? | **Modo 1** forecasting real (panel trimestral CCAA, SARIMAX/GBM + comparador DL); **Modo 2** proyección condicionada a escenarios (modelo A1 + sendas de gasto, intervalos conformales); **Modo 3** ancla FMI-WEO 2030 (ya en disco) |

### Bloque D — Escenarios de política (REFORMULADO — ver crítica §6)
La petición original ("un plan para reducir la deuda, aumentar vivienda e infraestructuras y despriorizar otras partidas") es una PRESCRIPCIÓN NORMATIVA — indefendible como ciencia de datos (§6.2). Se reformula como:
| RQ | Pregunta defendible | Método |
|---|---|---|
| D1 | **Simulador de escenarios fiscales:** dadas sendas alternativas de composición del gasto (p.ej. +0,5pp vivienda, +0,5pp inversión, −Xpp partida Y, superávit primario Z), ¿qué trayectorias de deuda (aritmética r−g) y qué resultados proyecta el modelo, con qué incertidumbre? | simulador contable de deuda + proyección condicionada (C1-Modo 2) |
| D2 | ¿Qué menús de reasignación son COHERENTES con los patrones observados (países que lograron bajar deuda subiendo inversión: ¿existen? ¿en qué condiciones)? | análisis de episodios históricos (GMD 1900→: consolidaciones fiscales) |
*El producto es un MENÚ de escenarios con consecuencias modeladas — la elección de qué despriorizar es política, no estadística, y así se dice en la memoria.*

---

## 2. Pool de datos (estado 2026-07-18)

**Extraído y testeado (28 processed + 4 gold, todo con smoke tests y raw inmutable):**
- **Fiscal UE:** gov_10a_exp (159k filas: 7 tipos × 13 funciones × 1995–2023), ingresos/impuestos/déficit, deuda — anclas verificadas
- **Fiscal global:** WEO (gasto/ingresos 151, saldo 229, deuda 226 países, 1980→proyecciones 2030)
- **Fiscal histórico:** GMD 2026_06 (66k filas, 202 países, exp/rev/tax/debt/déficit; 158 países pre-1995) + JST (18 países 1870–2020) → `gold_century_fiscal.csv` con eras
- **Sanidad global:** GHED (32k filas, 195 países: total/público/privado/OOP/% del gasto)
- **Outcomes:** SILC sobrecarga+hacinamiento, AROP pre/post (focalización), mortalidad tratable, e0
- **España:** IPV trimestral (tabla nueva 80270), IPC (20 series exactas), salarios, WWBI, gold CCAA (ratio asequibilidad Nacional 2024 = 1,26)
- **Migración:** UN DESA (2.280 filas, 284 destinos) + Eurostat flujos
- **Otros:** ODA, HPI trimestral, Gini, PIB pc PPS, población, ESSPROS, reciclaje

**Re-pulls menores pendientes (F2.0):** desempleo, D41 intereses, ESSPROS por función + población ≥65, D62/D41 en el histórico donde GMD lo tenga.
**Deferred con ruta:** GFS-COFOG global (MCP FMI), UIS+HLO, SPI, PISA, CEPEJ, GNI\*, liquidaciones CCAA, DAC CRS, cohesiondata, WB BOS, GRD, SIPRI, Euríbor (ECB), nightlights (NOAA/EOG).
**Esquemas:** diccionario maestro (9 familias, 120 verificados en vivo) + contrato de extracción selectiva (~38 series núcleo; regla: nada entra en gold sin smoke-test).

---

## 3. Método (una línea técnica) + capa ML/DL

**Núcleo:** GBM prediciendo resultado desde gasto (medias 5a, retardos 3–5a, features intra-fold) + controles (renta, demografía, gobernanza, capacidad estadística SPI) → **residual = rendimiento ajustado con intervalo conformal (block-conformal por país, calibración por grupo de renta)** → funnel plots. Validación LOCO + bloques temporales (COVID dummy); métrica pre-registrada MAE vs baselines OLS/GAM; multiverso de especificaciones (3 definiciones de gasto incl. %GNI\* IE/LU × controles × retardos) con estabilidad Spearman; auditoría de confusores (obesidad/tabaco/Gini/gasto privado); chequeos residual⊥renta y ⊥SPI dentro de grupo.

**Capa ML/DL completa** (regla maestra: el n efectivo decide la herramienta):
| Técnica | Uso | Datos |
|---|---|---|
| GBM + SHAP + conformal | A1–A4 rendimiento y composición | gold_panel_wide + GHED ✅ |
| PCA/clustering/arquetipos/DTW | A2 tipologías + trayectorias del siglo | gold_century ✅ |
| Isolation Forest | QA de anomalías (superbonus, ventas de activos) | pipeline ✅ |
| Change-point (PELT/bayesiano) | ratchets de guerra/crisis en el siglo XX | gold_century ✅ |
| SARIMAX/GBM + backtesting rolling | C1-Modo 1 (panel trimestral CCAA) | gold_ccaa ✅ |
| Proyección condicionada + conformal | C1-Modo 2 / D1 escenarios | modelo A1 + WEO ✅ |
| Control sintético + placebos | eventos (tope alquileres Cataluña 2024) | gold_ccaa ✅ |
| Métricas de red (NO GNN) | ayuda donante→receptor (F7) | DAC deferred |
| **DL-1: transformer español (MarIA)** | extractor BOE — cascada C0 parser→C1 triaje→C2 fine-tune→C3 LLM solo etiquetador | corpus BOE (post-TFM) |
| **DL-2: nightlights VIIRS/DMSP + CNN** | outcome/control independiente de imputaciones OMS en países con estadística débil (Henderson et al.) | conector pendiente |
| **DL-3: N-BEATS/DeepAR comparador** | forecasting CCAA (avalado por la Entrega 2 original) | gold_ccaa ✅ |
| **DL-4: TabPFN v2 comparador** | tabular pequeño (con permiso del tutor) | gold ✅ |
**Negativos asentados:** sin LSTM/TFT primario en paneles anuales; sin GNN a ~150 nodos; sin LLM como extractor masivo; sin liga mundial única.

**Sobre "el ML/DL aumentará la precisión de las predicciones" (petición del autor, con honestidad):** en agregados macro lentos, la ganancia de GBM/DL sobre baselines (naive/ETS/ARIMA) suele ser MODESTA y debe demostrarse con backtesting, no asumirse; donde el ML sí aporta de verdad es en (a) patrones e interacciones no lineales (umbrales de gasto, composición×renta), (b) cuantificación de incertidumbre (conformal), y (c) el panel trimestral denso. El capítulo de predicción se escribe con esa expectativa calibrada — "batir al naive es noticia; no batirlo también se publica".

---

## 4. Fases y tareas (árbol único, 3 niveles)

### F0 — TFM (S1–S10; gate del tutor) ★
- F0.1 Pitch + aval ESCRITO (S1) — tres vistas: A/UE, B/Global, **C/Vivienda (recomendada, complementaria del marco integral)**; fallback vivienda intacto en `main`.
  - F0.1.1 Enviar pitch (hecho: docs/pitch_tutor_fiscal.md) · F0.1.2 reunión · F0.1.3 email "adelante" = GO.
- F0.2 Reescritura de entregas (S2–S3) según la vista elegida; E3 = gold con tests (**YA CONSTRUIDO** ✅).
- F0.3 Checkpoint tutor S5 con primer funnel; F0.4 borrador S9; F0.5 defensa; F0.6 buffer S10.

### F1 — España-CCAA 30 años (post-gate o post-TFM)
- F1.1 Liquidaciones Hacienda (funcional×económica por CCAA; 1995–2001 vía IGAE/IEF o declarar inicio 2002).
- F1.2 Ingresos CCAA (financiación + tributos cedidos). F1.3 Benchmarking conformal 17 CCAA (funnel N=17). F1.4 Eventos BOE curados (15–20 hitos, a mano).

### F2 — Atlas de evolución (Bloque B) ★ — LA FASE NUEVA de este plan maestro
- **F2.0 Re-pulls menores** (una tarde): F2.0.1 desempleo (`une_rt_a`+WDI) · F2.0.2 D41 intereses · F2.0.3 ESSPROS por función + `demo_pjan` por edad (≥65) · F2.0.4 D62/GMD extras.
- **F2.1 Figuras de evolución B1–B15** (una por RQ, plantilla común: mundo-mediana + selección de países + España destacada; eras anotadas):
  - F2.1.1 gasto total siglo XX–XXI (tabla ya calculada → figura) · F2.1.2 composición económica · F2.1.3 vivienda · F2.1.4 sanidad · F2.1.5 infraestructuras/P51G · F2.1.6 empleados públicos/población · F2.1.7 masa salarial · F2.1.8 deuda · F2.1.9 protección social · F2.1.10 desempleo · F2.1.11 intereses · F2.1.12 pensiones+jubilados · F2.1.13 migración · F2.1.14 ayuda %RNB · F2.1.15 déficit+deuda (con B8).
  - F2.1.16 Change-point detection sobre B1/B8 (ratchets encontrados algorítmicamente).
- **F2.2 Capítulo "El siglo del Estado"**: síntesis narrativa de las 15 evoluciones + caveats (central-vs-general, pesetas, benchmarks funcionales).

### F3 — Rendimiento ajustado (Bloque A) ★
- F3.1 Módulo sanidad global (GHED, ~180 clústeres): baselines → GBM → conformal → funnel por renta → SHAP (nivel+composición+personal) → multiverso. **AC: residual⊥renta y ⊥SPI.**
- F3.2 Módulo vivienda UE (GF0601+GF1006 → sobrecarga/hacinamiento; superbonus con/sin).
- F3.3 Módulo educación (transversal HLO; sin interpolar). F3.4 Contraste Tier-D (outcome emparejado, Spearman+IC). F3.5 Síntesis entre módulos + tipologías. F3.6 Bolt-ons opcionales (justicia CEPEJ, focalización — datos ya extraídos, contratación, reciclaje).

### F4 — Predicción (Bloque C)
- F4.1 Forecasting CCAA (Modo 1): baselines naive/ETS → SARIMAX/GBM → **comparador DL (N-BEATS/DeepAR)** → backtesting rolling-origin, MAE por horizonte (4–8 trimestres). AC: tabla modelo×horizonte con el ganador honesto.
- F4.2 Proyección condicionada país (Modo 2): sendas WEO 2030 + escenarios de composición → outcomes proyectados con intervalos. F4.3 Validación contra proyecciones FMI (Modo 3).

### F5 — Simulador de escenarios fiscales (Bloque D, reformulado)
- F5.1 Aritmética de deuda (r−g, saldo primario) por país: trayectorias 2024–2035 bajo escenarios.
- F5.2 Menús de reasignación: escenarios "+vivienda/+inversión/−partida X" → consecuencias proyectadas (F4.2) + coste en deuda (F5.1). **Producto: matriz escenario×consecuencia con incertidumbre — nunca una recomendación única.**
- F5.3 Episodios históricos (GMD): consolidaciones que subieron inversión — casuística y condiciones.

### F6–F9 — Resto del programa integral (post-TFM): F6 empresas públicas (WB BOS, muestreo sectorial) · F7 flujos DAC CRS/IDS + red · F8 migración×servicios (interacción presión×rendimiento — hipótesis vivienda del autor) · F9 síntesis/papers/app.

**Calendario TFM (10 semanas):** S1 gate ★ · S2–S3 entregas+F2.0+F2.1 núcleo · S4–S5 F3.1 ★ + checkpoint · S6 F3.2 + F2 cierre · S7 F4.1 + síntesis · S8 app+memoria · S9 borrador ★ · S10 buffer. *(F5 completo y F6–F9 = líneas futuras salvo que la vista elegida los requiera.)*

---

## 5. Productos finales
1. **Memoria TFM** (metodología anti-tribunal, declaración IA, anexo reproducibilidad + "considerado y rechazado").
2. **Atlas de evolución** (15 figuras B + tabla de eras) — responde TODAS las preguntas nuevas del autor.
3. **Funnel de rendimiento ajustado** por módulo y grupo de renta (A1).
4. **Simulador de escenarios** (D1: deuda + composición → consecuencias, con incertidumbre).
5. **App Streamlit** + gold reproducible (ya: 4 gold, 28 processed, smoke tests).

---

## 6. Crítica del proyecto (a petición del autor): relevancia y riesgos

### 6.1 ¿Es un TFM relevante? SÍ, con una condición
El tema es relevante (pregunta social de primer orden, datos abiertos, método moderno, hueco real: nadie publica rendimiento-ajustado-con-incertidumbre + composición + siglo XX en un solo marco). **Pero tal como está formulado es un PROGRAMA, no un TFM**: 20 RQs, 10 fases, 4 siglos-persona de datos. La condición de relevancia-como-TFM es el recorte: la vista C (o sanidad global) como núcleo demostrable + el atlas B como capítulo descriptivo + F4.1 como predicción — y el resto declarado líneas futuras. El tutor exigió exactamente esto ("alcance radicalmente reducido"); ignorarlo es el riesgo nº1 del proyecto, por delante de cualquier riesgo estadístico.

### 6.2 Riesgos metodológicos (por gravedad)
1. **Normatividad (FATAL si no se corrige):** "un plan para reducir la deuda y despriorizar partidas" no es ciencia de datos — es política fiscal. Qué despriorizar es un juicio de VALOR; ningún GBM lo responde. Reformulado como simulador de escenarios (§1-D) es defendible; como "plan" recomendado, el tribunal (y cualquier economista) lo desmonta. La frase de la memoria: *"este trabajo proyecta consecuencias de escenarios; no prescribe políticas"*.
2. **Endogeneidad / causalidad inversa (el clásico):** el gasto responde a los resultados tanto como al revés — se gasta más en sanidad donde la población envejece y enferma; más en desempleo cuando hay paro; más en intereses cuando la deuda subió por crisis pasadas. El residual "eficiencia" absorbe TODO lo omitido (instituciones, historia, geografía, informalidad). Mitigado (retardos, medias 5a, controles, encuadre no causal, multiverso) pero NUNCA eliminado — se declara como límite, no se esconde.
3. **Sesgo de composición del panel (survivorship/measurement):** los países con datos largos son los ricos y estables — la "mediana mundial 1900" es la mediana de 37 países medibles, no del mundo; los outcomes de países pobres están parcialmente IMPUTADOS por modelos OMS/IGME que usan el PIB → riesgo de circularidad (el residual "descubre" el imputador). Mitigación: flag de procedencia + spec sin imputados + SPI como control — y aún así, cautela en las conclusiones globales.
4. **Rupturas de comparabilidad temporal:** central-vs-general (pre/post ~1960), pesetas→euro, revisiones COFOG, empalmes GMD, PISA irregular. El atlas B es robusto a esto (tendencias grandes); el modelo A NO se estima sobre el panel histórico (1995→ solo) — mezclarlos sería un error grave.
5. **Predicción macro = humildad obligatoria:** los modelos entrenados en un régimen fallan en el cambio de régimen (nadie predijo 2008 ni COVID con GBMs); n efectivo pequeño + autocorrelación inflan la confianza aparente. Por eso: baselines obligatorios, conformal, escenarios en vez de puntos, y la expectativa calibrada de §3.
6. **Falacia ecológica:** todo es agregado-país; "España gasta X" no dice nada de la distribución interna (CCAA lo palía en parte; hogares, nada).
7. **Goodhart / mal uso:** un funnel de "eficiencia" invita a titulares-liga ("España, peor que…"); el diseño (intervalos, no-liga, por grupo) lo mitiga, la memoria debe anticiparlo explícitamente.
8. **Jardín de senderos (p-hacking involuntario):** 15 evoluciones + multiverso + módulos = miles de comparaciones posibles. Mitigación: RQs y métricas pre-registradas en ESTE documento, multiverso reportado completo, hallazgos exploratorios etiquetados como tales.
9. **Riesgo de ejecución:** 10 semanas a tiempo parcial; cada re-pull "menor" cuesta medio día; el atlas B son 15 figuras con datos ya en disco (barato) pero el texto no se escribe solo. El calendario F0 con buffer real existe por esto.

### 6.3 Veredicto
**Relevante y original: sí. Defendible: solo con (a) el recorte del alcance TFM, (b) la reformulación no normativa del Bloque D, (c) los límites de causalidad en primera plana.** Con esas tres correcciones — ya incorporadas en este documento — es un TFM fuerte con continuación natural de programa de investigación.

---

## 7. Incorporación del feedback del tutor (12-jul-2026)

*Fuente: [comentarios privados en Classroom](entregas/feedback_tutor_2026-07-12.md); transición documentada en [entregas/anexo_transicion_proyecto.md](entregas/anexo_transicion_proyecto.md).*

1. **Repositorio como entregable ("formato de entrega = contrato").** Este repositorio público es la entrega; toda modificación de alcance se documenta en `docs/entregas/` de forma incremental, sin borrar entregas anteriores.
2. **Asequibilidad de vivienda — indicador complementario (vista C / F4.1).** El ratio IPV/salario indexado se presenta SIEMPRE como indicador aproximado de evolución relativa. Se añade una **cuota hipotecaria teórica** por CCAA: precio medio de transacción (€/m² MITMA/Registradores × superficie tipo) × LTV 80 % financiado a 25 años al Euríbor 12m + diferencial, expresada como % del salario medio CCAA (esfuerzo de compra). Insumos: Euríbor ✅ extraído, IPV ✅, salarios ✅, €/m² con ruta identificada (E2 §3). El dato de esfuerzo del BdE (ratio cuota/renta) sirve de validación externa del indicador propio.
3. **MVP primero.** El núcleo TFM (atlas B + rendimiento A1 + forecasting CCAA) va antes que cualquier extensión; RAG/LLM, DL adicional (más allá del comparador avalado) y fases F5–F9 son explícitamente extensiones que no bloquean el núcleo. El calendario F0 con buffer (§4) implementa esta prioridad.

4. **Oferta privada de vivienda (revisión 2026-07-18, posterior a la Entrega 4).** El diseño de vivienda modelaba la demanda (Euríbor, IPC, salarios) y la inversión PÚBLICA (GF06), pero no la construcción PRIVADA — que en España produce la inmensa mayoría de la vivienda nueva (GF06 ≈ 0,5 %PIB frente a una inversión residencial total del orden de 5–6 %PIB). Sin una señal de oferta, el forecasting arrastra una variable omitida (la respuesta de la promoción privada amortigua o amplifica los precios) y el atlas puede sugerir que la palanca pública es mayor de lo que es. Mitigación en tres frentes:
   - **T1 (forecasting CCAA):** nuevo driver de oferta V2 `oferta_nueva` — visados de obra nueva y viviendas iniciadas/terminadas del MITMA (mensual, provincial → CCAA, mismo Boletín Estadístico ya usado para suelo e ICSC), con su retardo natural visado→terminación (~18–24 meses) como feature adelantada. Entra como driver deseable (contrato V2 de la Entrega 2: su ausencia no bloquea el núcleo).
   - **Atlas (B3):** la figura de inversión pública en vivienda se presenta SIEMPRE junto a la inversión residencial total (Eurostat, FBCF por activo "viviendas", `nama_10_an6`/AN_111), de modo que el peso público quede en su contexto real y la privada = total − pública quede visible.
   - **T2 (rendimiento):** en los outcomes de vivienda (sobrecarga, hacinamiento, asequibilidad), la inversión residencial privada entra como CONFUSOR en la auditoría — un buen outcome con GF06 bajo puede deberse a oferta privada abundante, y atribuirlo al gasto público sería un artefacto.
   - Limitación declarada en memoria y MVP: la asequibilidad es un equilibrio oferta-demanda; el proyecto mide y proyecta, y la acción pública es UNA de las palancas, no la única.
