# PLAN INTEGRAL — "¿Qué país gasta mejor el dinero público?"

> **Decisión del autor (2026-07-18): el programa integral es el MARCO del trabajo, y la [Variante C (vivienda como consecuencias)](PLAN_vivienda_consecuencias.md) actúa como su ANÁLISIS COMPLEMENTARIO** — el caso donde la cadena gasto→rendimiento→consecuencias se demuestra de punta a punta. Para el TFM sigue rigiendo el gate del tutor (S1); ante el tribunal, la Variante C es el núcleo demostrable y el integral su marco y líneas futuras.
>
> **Estado de datos (2026-07-18):** extraídos y testeados — Eurostat completo (gasto×función×tipo, ingresos, deuda, SILC, migración UE, HPI, controles), WEO totales globales (151-229 países), **GHED sanidad global (195 países)**, UN DESA stock migrante (284 destinos, 1990-2024), ODA recibida, JST histórico 1870-2020, INE España (IPV/IPC/salarios, tablas nuevas), WWBI. Gold: panel UE anual + CCAA trimestral. Deferred con ruta: GRD, WB BOS, SIPRI, GMD, GFS-COFOG global (vía MCP), liquidaciones CCAA, DAC CRS microdatos, cohesiondata, Euríbor (ECB SDW).

*Programa de investigación completo. v1, 2026-07-17. Este documento define el objetivo MÁXIMO en los términos del autor, mapea TODAS las bases de datos disponibles (verificadas donde se indica) y descompone el trabajo en fases. **Advertencia de honestidad:** esto es un programa de 12–24 meses, no un TFM de 10 semanas — el tutor vetó el "fiscal integral" y tres rondas de consejo multi-modelo lo confirmaron. El TFM ([plan UE](PLAN_public_money_outcomes.md) / [plan GLOBAL](PLAN_public_money_outcomes_GLOBAL.md)) es la **Fase 1** de este programa; el resto es hoja de ruta post-TFM. Cada fase tiene entidad propia y produce resultados publicables.*

---

## 1. Objetivo (en los términos del autor)

1. **España-CCAA:** extraer gasto e ingresos de las 17 CCAA durante 30 años (1995–2025), con el gasto partido por función (vivienda, sanidad, educación, infraestructuras, pensiones, bienestar social) **y** por clasificación económica: remuneración de empleados (salarios + cotizaciones), consumo intermedio (bienes y servicios), intereses de la deuda, subvenciones a empresas, transferencias a otras administraciones/organismos, prestaciones sociales (monetarias y en especie), otro gasto corriente, y gasto de capital (formación bruta de capital fijo + transferencias de capital).
2. **Subir un nivel:** mismo esquema para los países de la UE y los europeos no-UE.
3. **Subir otro nivel:** gasto e ingresos del propio presupuesto de la UE como capa de gobierno.
4. **Resto del mundo:** América, África, Asia y Oceanía con el mismo esquema, hasta donde los datos lleguen.
5. **Pregunta central:** ¿qué país del mundo es el más eficiente gastando el dinero público?
6. **Focos especiales:** (a) España; (b) países de baja fiscalidad — Andorra, Suiza, Paraguay, República Dominicana… — ¿cómo entregan servicios públicos sin subir impuestos?; (c) **empresas públicas** (TV, distribución eléctrica, trenes, carreteras, puertos, aeropuertos…) y su rendimiento por país; (d) **flujos de dinero público entre países** (ayudas y préstamos); (e) **migración 1995–2025** y su impacto sobre vivienda, sanidad y demás servicios sometidos a estrés demográfico.
7. **Hipótesis de cierre:** cómo impacta en la vivienda la pérdida de eficiencia del gasto público.

## 2. Marco conceptual (una sola disciplina para todo el programa)

- La matriz de análisis es **función (COFOG) × clasificación económica (ESA/GFS)** — la lista del punto 1 es exactamente la clasificación económica ESA2010/GFS: D1 remuneración, P2 consumo intermedio, D41 intereses, D3 subvenciones, D7/D74 transferencias, D62+D632 prestaciones, P51G FBCF, D9 transferencias de capital. En Eurostat, `gov_10a_exp` (COFOG×na_item) y `gov_10a_main` (ingresos por tipo) YA proveen este cruce para Europa; el FMI GFS lo provee (parcial) para el mundo.
- "Eficiencia" siempre = **rendimiento ajustado** (GBM + residual conformal, funnel, no-causal, estratificado por renta) — la maquinaria vetada por el consejo, idéntica en todas las fases. Un método, muchas mesas.
- Toda cifra pasa smoke-test antes de entrar en gold (lección de la 3ª ronda: 5 códigos erróneos en la propia recomendación del consejo).

## 3. Mapa completo de bases de datos por pilar

### P1 — España CCAA (1995–2025)
| Dato | Fuente | Estado |
|---|---|---|
| Gasto funcional España total | INE `aappgastcofog95_23.xlsx` (COFOG 1995–2023) | ✅ verificado en vivo |
| Series por subsector (central/CCAA/local/SS) | IGAE series anuales (datos.gob.es índice) | ✅ verificado (User-Agent navegador) |
| Liquidaciones presupuestarias CCAA (funcional+económica) | Min. Hacienda — liquidaciones y avances (XLSX, ~2002→ online; anteriores en publicaciones IGAE/IEF) | página confirmada; profundidad 1995–2001 = riesgo |
| Finanzas regionales armonizadas | OECD REGOFI (2010–2022) | catalogado |
| Ingresos CCAA (financiación autonómica, tributos cedidos) | Hacienda (informes financiación) + AEAT recaudación por delegación | público, XLSX/PDF |
| Histórico pre-2000 | Carreras & Tafunell (Fund. BBVA) + series Comín; BADESPE (IEF, estado a verificar) | ✅ página BBVA verificada |
| Decisiones/eventos | BOE API (sumarios ≥1994, XML con tablas; pesetas pre-2002) | ✅ verificado en vivo |

### P2 — Europa (UE + no-UE)
| Dato | Fuente | Estado |
|---|---|---|
| Gasto COFOG×económica + ingresos | Eurostat `gov_10a_exp`, `gov_10a_main`, `gov_10dd` (1995–2023, 33 países) | ✅ verificado en vivo |
| No-UE europeos: Suiza | EFV/FFA (excelente) + OCDE | catalogado |
| No-UE: UK | HM Treasury PESA + OCDE; legislation.gov.uk | ✅ API verificada |
| No-UE: Noruega/Islandia | en Eurostat (AELC) | ✅ |
| Balcanes/Este no-UE | FMI GFS + Eurostat enlargement | parcial |
| **Andorra** | Departament d'Estadística + FMI Article IV | **muy limitado — sin COFOG; foco cualitativo** |

### P3 — Presupuesto de la UE como gobierno
| Dato | Fuente | Estado |
|---|---|---|
| Gasto UE por programa y país receptor | European Commission Financial Transparency System + DG BUDG open data (spending & revenue datasets) | público, CSV/API |
| Ingresos UE (recursos propios por país) | DG BUDG + informes anuales | público |
| Fondos cohesión/NGEU por país | cohesiondata.ec.europa.eu (portal abierto, API) | público |

### P4 — Mundo (América, África, Asia, Oceanía)
| Dato | Fuente | Estado |
|---|---|---|
| Gasto funcional + económico | FMI GFS (~60–90 reporters COFOG; económica más amplia) | catalogado (MCP operativo) |
| Ingresos tributarios | ICTD/UNU-WIDER GRD v2025 (196 países 1980–2023) + OECD Global Revenue Statistics (137) | catalogado |
| Sanidad (todo el mundo) | WHO GHED (~190, 2000→) | ✅ verificado |
| Educación | UNESCO UIS + WB HLO | catalogado |
| Totales largos | Global Macro Database (243 países) + JST | ✅ verificados en vivo |
| Regionales | CEPALSTAT, AfDB AIH, ADB KIDB, AMF, GCC-Stat | catalogados |
| Baja fiscalidad LatAm (Paraguay, R. Dominicana) | CEPALSTAT + Dipres-equivalentes nacionales + FMI Article IV | parcial; calidad heterogénea |

### P5 — Empresas públicas (SOEs)
| Dato | Fuente | Estado |
|---|---|---|
| Censo mundial de empresas estatales | **World Bank BOS (Businesses of the State)** — footprint por país/sector | catalogado (nuevo, 2023→) |
| Gobernanza y tamaño SOE OCDE | OECD Ownership & Governance of SOEs dataset | catalogado |
| España | SEPI + Informes IGAE sector público empresarial | público |
| Rendimiento por sector (TV, eléctricas, trenes, puertos, aeropuertos) | cuentas anuales individuales (registros mercantiles/portales corporativos) + reguladores sectoriales (CNMC, ERA, etc.) | **coste de extracción MUY alto — muestreo por sector, no censo** |
| Subvenciones a SOEs | Eurostat D3 por función + TAM (state aid) | parcial |

### P6 — Flujos de dinero público entre países
| Dato | Fuente | Estado |
|---|---|---|
| Ayuda oficial al desarrollo (donante→receptor, proyecto a proyecto) | **OECD DAC CRS** microdatos | público, el estándar |
| Préstamos chinos y financiación no-DAC | AidData | catalogado |
| Deuda bilateral/multilateral | World Bank IDS (International Debt Statistics) | público |
| Flujos intra-UE | P3 (cohesión + recursos propios) → posición neta por país | público |
| Remesas (contexto) | World Bank remittances matrix | público |

### P7 — Migración y estrés de servicios
| Dato | Fuente | Estado |
|---|---|---|
| Stock migrante por país 1990–2024 | UN DESA International Migrant Stock (quinquenal) | público |
| Flujos anuales Europa | Eurostat `migr_imm/emi` + OECD International Migration Database | público |
| Refugiados | UNHCR | público |
| España por CCAA | INE Estadística de Migraciones + padrón | ✅ (pipeline vivienda) |
| Estrés de servicios | outcomes ya mapeados (SILC vivienda, listas de espera nacionales — heterogéneo) | parcial |

## 4. Árbol de tareas por fases (con puertas)

**F0 — TFM (S1–S10, YA planificado).** = [plan UE](PLAN_public_money_outcomes.md) o [plan GLOBAL](PLAN_public_money_outcomes_GLOBAL.md) + bolt-ons opcionales. Produce: la maquinaria completa (conectores, gold, GBM+conformal, funnel, app) y la respuesta europea/global a "¿quién gasta mejor?" en 2–3 funciones. **Todo lo posterior REUTILIZA esta maquinaria.**

**F1 — España-CCAA 30 años (~4–6 semanas post-TFM).**
- F1.1 Conector liquidaciones Hacienda (funcional×económica por CCAA; resolver 1995–2001 vía IGAE/IEF/BBVA o declarar inicio 2002).
- F1.2 Ingresos CCAA (financiación + tributos cedidos) → panel ingresos-gastos 17×30.
- F1.3 Benchmarking conformal de CCAA en sanidad/educación/vivienda (N=17 declarado; funnel).
- F1.4 Eventos BOE (prórrogas, reformas de financiación) como capa cualitativa.

**F2 — Europa completa (~3–4 semanas).** Extensión no-UE (CH/UK/Balcanes vía GFS); matriz función×económica completa; actualizar módulos TFM con la dimensión económica (D1/P2/D41/D3/D62/P51G+D9 como features — parte ya está: D1, P51G+D9, WWBI).

**F3 — La UE como gobierno (~2–3 semanas).** FTS + cohesiondata: gasto UE por país receptor + recursos propios → posición neta; ¿el gasto UE mejora el rendimiento ajustado de los receptores? (cuidado: absorción ≠ resultado — veto de 3ª ronda; usar la cuota de inversión financiada por UE como feature de composición).

**F4 — Mundo por continentes (~6–8 semanas).** GFS económica global + GRD ingresos; sanidad/educación globales (ya en plan GLOBAL); rankings por grupo de renta; coverage map continental. América/África/Asia/Oceanía = el MISMO pipeline con menos funciones, nunca esquemas nuevos por continente.

**F5 — Focos de baja fiscalidad (~2–3 semanas, mayormente cualitativo).** Andorra, Suiza, Paraguay, R. Dominicana + set de comparación (Irlanda, Singapur, Golfo): presión fiscal (GRD) vs cobertura de servicios (outcomes) vs mecanismos (bases imponibles externas, turismo fiscal, escala pequeña, cotizaciones, petróleo). **Advertencia de constructo:** "entregan servicios sin subir impuestos" debe contrastarse con outcomes, no asumirse; Andorra casi sin datos comparables → estudio de caso, no fila del modelo.

**F6 — Empresas públicas (~6–10 semanas, el pilar más caro).** WB BOS + OCDE SOE como censo; selección de 3 sectores comparables (TV pública, gestor ferroviario, aeropuertos) × ~10 países; indicadores: subvención pública por usuario/output, ROA, empleo; integración como feature ("intensidad SOE del país") en el modelo de rendimiento. **No existe base armonizada de rendimiento SOE — este pilar es construcción manual; muestrear, no censar.**

**F7 — Flujos entre países (~3–4 semanas).** DAC CRS + AidData + IDS → matriz donante→receptor 1995–2023; para receptores: ayuda como ingreso adicional en el modelo (¿el rendimiento ajustado sube con ayuda? — literatura de aid-effectiveness, encuadre no-causal); para donantes: GF01 cooperación como función.

**F8 — Migración y estrés de servicios (~4–6 semanas).** Stock/flujos por país-año → features de presión demográfica (Δpoblación, Δstock migrante) en los módulos vivienda/sanidad; España-CCAA con el pipeline del TFM de vivienda; **la hipótesis final del autor** ("la pérdida de eficiencia impacta la vivienda") se operacionaliza aquí: ¿los países/CCAA con peor rendimiento ajustado en vivienda muestran mayor deterioro de asequibilidad/sobrecarga ante el mismo shock migratorio? — interacción presión×rendimiento, siempre asociativa.

**F9 — Síntesis programa (~2–3 semanas).** Ranking mundial por grupo de renta con incertidumbre; atlas web; papers: (1) metodología+Europa [del TFM], (2) CCAA, (3) baja fiscalidad, (4) migración×vivienda.

**Total programa: ~9–12 meses a dedicación parcial tras el TFM.** Puertas: cada fase se cierra con su gold+tests+nota antes de abrir la siguiente; cualquier fase es publicable por sí sola.

## 5. Advertencias de constructo heredadas (no reabrir)
- "Eficiencia" = rendimiento ajustado no-causal; nunca liga mundial única (estratificar por renta).
- Absorción de fondos ≠ resultado (F3). SOE-rendimiento sin base armonizada (F6 = muestreo). Ayuda↔outcomes = literatura minada (F7, encuadre asociativo). Migración↔servicios = doble causalidad evidente (F8, asociativo).
- Andorra/micro-estados: caso de estudio, no fila del panel.
- Pesetas pre-2002 (166,386 pta/€), rupturas de series, central-vs-general en históricos.

## 6. Capa ML/DL por pilar

**Regla maestra: el tamaño muestral EFECTIVO decide la herramienta.** Clústeres-país ≈ 33–190 → GBM+conformal. Documentos ≈ 10⁴–10⁵ → transformers. Nodos de red ≈ 150 → métricas de grafo, no GNN. Píxeles ≈ millones → CNN. Decirlo explícitamente en la memoria desactiva la pregunta "¿y el deep learning?".

### 6.1 Formas del dato → técnica → fase

| Objetivo | Técnica | Fase | Defensa |
|---|---|---|---|
| Benchmarking de eficiencia | GBM + SHAP + residual conformal (núcleo ya diseñado) | F0–F4 | ✅ vetada por consejo |
| Descubrir patrones | PCA + clustering de composición; **análisis arquetípico** (países como mezclas de perfiles extremos, más interpretable que k-means); **clustering de trayectorias** (DTW sobre sendas de 30 años: convergencia/divergencia) | F2, F4, prólogo | ✅ con N≥150; exploratorio a N=33 |
| Clasificación | (a) clasificador de régimen fiscal (¿la estructura del gasto "delata" el grupo de renta?); (b) clasificador de documentos BOE (¿presupuestario? ¿qué función?) multi-etiqueta | F4; F1 | (b) = DL honesto, ver 6.2 |
| Detección de anomalías | Isolation Forest / z-robusto sobre CAMBIOS de composición → auto-detecta artefactos tipo superbonus + errores de datos; red-flags de contratación (single-bidding, CRI) | QA de gold (todas); F6 | ✅ doble uso como higiene de pipeline |
| Series temporales | Forecasting (SARIMAX/GBM — maquinaria del TFM vivienda); **detección de puntos de cambio** (PELT/bayesiano) sobre series seculares → los "ratchets" de guerra/crisis encontrados algorítmicamente | vivienda; prólogo T2.0 | ✅ |
| Análisis de eventos | **Control sintético** para eventos únicos (p. ej. tope de alquileres Cataluña 2024: Cataluña sintética desde pool de CCAA donantes) | F1, F8, capa BOE | ✅ método establecido, amable con tribunal |
| ML de grafos | Red de ayuda donante→receptor: centralidad, comunidades, persistencia; las métricas (dependencia de ayuda) entran como features del modelo de rendimiento. GNN = rechazado explícitamente (~150 nodos) | F7 | ✅ como métricas |
| Compleción de matrices | Imputación tipo-recomendador de celdas GFS ausentes | F4 | ⚠️ desaconsejado — publicar coverage map, no imputar |

### 6.2 Los TRES huecos honestos para deep learning
1. **Extractor BOE = DL de verdad, plenamente justificado.** Fine-tuning de transformer español (MarIA / RoBERTa-BNE) para clasificación de disposiciones + NER (importes, organismos, funciones) sobre decenas de miles de documentos. n≈10⁴–10⁵ de TEXTO = territorio DL genuino; alimenta la capa de decisiones de F1 y reutiliza la experiencia Trustpilot del autor. LA respuesta a "¿dónde está el deep learning?".
2. **Luces nocturnas por satélite (VIIRS/DMSP) como outcome/control en países con estadística débil** (F4): proxy establecido en economía (Henderson et al.) procesado con CNN; canal de resultado independiente de la circularidad de imputación OMS/IGME señalada en revisión. DL real, precedente real, datos abiertos.
3. **TabPFN v2 como comparador tabular** — solo con aval explícito del tutor (regla de una línea técnica); si el GBM gana, es un hallazgo publicable sobre DL en tabular pequeño.

**Negativo asentado (repetirlo):** nada de LSTM/TFT sobre paneles macro anuales — 25 puntos autocorrelacionados por país es indefendible; explicar POR QUÉ vale más nota que forzarlo.

### 6.3 Arquitectura del extractor BOE: cascada de 4 capas (LLM ≠ ML/DL — cada uno en su sitio)

**Regla: nunca usar ML para lo que un parser hace mejor, ni un LLM para lo que un modelo pequeño hace más barato.**

```
API sumarios → C0 parser determinista (metadatos, tablas, importes)
    → C1 triaje por título (clasificador rápido TF-IDF+logística, 2,9M títulos en minutos)
        → C2 fine-tuning MarIA/RoBERTa-BNE (clasificación doc/artículo + NER importes↔organismos↔funciones)
            → C3 LLM: SOLO (a) generar etiquetas de entrenamiento para C2 (weak supervision,
               3–5k docs anotados por LLM + muestra verificada a mano → destilación) y
               (b) residuo de casos difíciles con baja confianza (~1–5%)
→ salida: fecha | id | instrumento | organismo | función | importe | enlace | confianza
```

- **C0 ya está probado en vivo** (esta sesión): las tablas del PGE y de las leyes CCAA se extraen con regex/XML sin ML — determinista, gratis, reproducible. ~70% del valor.
- **C2 es el "hueco DL honesto" nº1** (§6.2): pesos fijos → inferencia determinista, evaluación P/R/F1 sobre held-out etiquetado a mano, coste de céntimos sobre todo el corpus. Componente de nivel tesis.
- **C3 nunca como extractor masivo:** ~850k docs ≈ 1,7B tokens → miles de € y semanas de API, salida estocástica, versiones de modelo que cambian debajo — indefendible en el anexo de reproducibilidad. "Transformer ajustado, F1=0,94 en held-out" se defiende solo; "prompteamos una API" invita a la pregunta que no se puede responder.
- Cada capa medida, cada traspaso registrado, flags de confianza nunca imputados en silencio.

## 7. Qué hacer AHORA
Nada de esto cambia el TFM: **F0 = plan UE o GLOBAL, gate del tutor en S1.** Este documento es el mapa del programa completo — útil para (a) el capítulo de "líneas futuras" de la memoria, (b) decidir el siguiente proyecto post-defensa, (c) demostrar al tribunal que el recorte de alcance fue una decisión informada, no una carencia.
