# PLAN — "Public Money → Outcomes": rendimiento ajustado y composición del gasto público en la UE

*Plan de trabajo TFM. v2, 2026-07-17 (v1 auditada por agente revisor independiente; 12 defectos corregidos). Deadline: fin de septiembre 2026 (~10 semanas, dedicación parcial — el autor trabaja a jornada completa). Diseño refinado en dos rondas de consejo multi-modelo (Claude+GLM+MiMo+Gemini, verificación adversarial + web-check) y datos verificados en vivo — ver [data_landscape.md](data_landscape.md) y [analisis_opciones_tfm.md](analisis_opciones_tfm.md).*

---

## 1. Especificación: qué queremos conseguir

**Pregunta central:** ¿qué gobiernos europeos convierten mejor el dinero de sus contribuyentes en resultados para la población — medido como *rendimiento ajustado* al contexto, nunca como "eficiencia" a secas — y qué papel juega la *composición* del gasto (inversión vs gasto corriente)?

### Preguntas de investigación
| RQ | Pregunta | Tipo |
|---|---|---|
| **RQ1** | ¿Cómo se gasta el dinero público en la UE por función (sanidad, educación, vivienda, pensiones, defensa…) y por tipo económico (inversión P51G+D9 vs corriente)? ¿Quién gasta más en vivienda, quién invierte más, quién es más "corriente"? | Descriptiva |
| **RQ2** | ¿Qué perfiles/tipologías de composición del gasto existen entre países y cómo evolucionan? | No supervisada |
| **RQ3** | ¿Qué países obtienen resultados mejores o peores de lo que su gasto y su contexto predicen — con qué certeza estadística? | ML supervisado |
| **RQ4** | ¿Importa la composición? ¿Predice una mezcla más inversora mejores resultados, con umbrales no lineales? | ML supervisado (contribución novedosa) |

### Lo que NO pretendemos (guardarraíles del consejo)
- NO afirmaciones causales ni normativas ("el país X debería reasignar €Y").
- NO ranking-liga: solo países cuyo intervalo de confianza excluye cero, en funnel plot.
- NO DEA/SFA/fronteras; NO RAG; NO deep learning (una sola línea técnica: GBM + SHAP + conformal; la exclusión de DL se justifica por escrito, §T4).
- NO "fiscal integral": 3 módulos de resultado como máximo (sanidad, educación, vivienda).

### Criterios de éxito
1. Aval ESCRITO del tutor antes de fin de S1 (gate GO/NO-GO; si NO → fallback vivienda, Entregas 1-3 intactas) + checkpoint intermedio S5.
2. Panel gold reproducible con tests automáticos (contrato de datos estilo Entrega 3 actual).
3. Los 4 RQ respondidos con la maquinaria vetada por el consejo (conformal, LOCO CV, multiverso).
4. Memoria (con declaración de uso de IA) + app demo + defensa antes del 30-sep.

---

## 2. Alcance

**Geografía:** UE+AELC (~33 países, Eurostat, 1995–2023). *(El tier global GHED ~190 países queda FUERA de alcance de esta tesis — anotado como línea futura en conclusiones; sin tarea asociada.)*
**Funciones (inputs):** las 10 COFOG nivel 1 (1995–2023); nivel 2 para vivienda (GF0601+GF1006) y sanidad **solo desde 2001** (límite real de COFOG-II). Se excluyen intereses de deuda (GF01 parcial).
**Tipo económico:** capital = P51G + D9; corriente = TE − capital; shares por función.
**Módulos de resultado:** sanidad (esperanza de vida `demo_mlexpec`; mortalidad tratable `hlth_cd_apr`, consistente 2011+), educación (PISA solo años-ola 2000–2022 + **HLO** como robustez), vivienda (EU-SILC sobrecarga `ilc_lvho07a` + hacinamiento `ilc_lvho05a`).
**Fuera de alcance:** impuestos como módulo propio, orden público, pensiones-como-producción, extractor BOE masivo (post-TFM), tier global, CCAA deep-dive (stretch S8 solo si todo verde).

---

## 3. Árbol de tareas

*Niveles: T (tarea) → T.x (subtarea) → T.x.y (sub-subtarea). [S#] = semana. ★ = camino crítico. AC = criterio de aceptación.*

### T0 — Gobernanza y aval del tutor ★ [S1, S2, S5]
- **T0.1 Pitch al tutor** ★ [S1]
  - T0.1.1 Redactar pitch 1 página (ES): pregunta, método (UNA línea técnica: GBM+SHAP+conformal), datos verificados, calendario.
  - T0.1.2 Adjuntar evidencia viva: rankings 2023 (vivienda IT 4.4/ES 0.5; inversión EE 6.5/ES 3.0), captura del panel Eurostat.
  - T0.1.3 Enviar + reunión; obtener **aval por escrito**. AC: email del tutor con "adelante".
- **T0.2 Protección del fallback** ★ [S1]
  - T0.2.1 Rama git `fiscal-pivot`; `main` conserva vivienda intacta.
  - T0.2.2 Gate GO/NO-GO fin de S1: sin aval → plan B (vivienda + métodos elevados: LOCO CV + benchmarking conformal de CCAA).
- **T0.3 Reescritura de entregas (solo si GO)** [S2 — tras existir el gold]
  - T0.3.1 E1: narrativa de convergencia (la línea "monitorización con datos accesibles" se mantiene; cambia el dominio).
  - T0.3.2 E2: idea + datos necesarios (reusar data_landscape.md, fuentes ya verificadas).
  - T0.3.3 E3: modelo de datos + capa gold. AC: los 3 documentos, con E3 apuntando al entregable T1.3.5 (mismo hito de S2).
- **T0.4 Checkpoint intermedio con el tutor** ★ [S5]
  - T0.4.1 Enviar primer funnel plot (sanidad) + atlas resumido; reunión corta. AC: feedback registrado antes de replicar módulos. *(Ocho semanas sin visibilidad del tutor era el riesgo nº1 del plan v1.)*

### T1 — Plataforma de datos ★ [S1–S2]
- **T1.1 Andamiaje del repo** [S1]
  - T1.1.1 Estructura `connectors/ storage/{raw,processed,gold} tests/ notebooks/ app/` (mismo contrato raw→gold del proyecto vivienda).
  - T1.1.2 Interfaz común de conector: `fetch() → DataFrame tidy` + caché en raw/ + log de vintage.
  - T1.1.3 CI mínimo: pytest en carga (PK únicas, rangos, grid completo).
- **T1.2 Conectores numéricos** ★ [S1–S2]
  - T1.2.1 Eurostat `gov_10a_exp` completo: cofog99 (L1 1995–2023; L2 vivienda/sanidad 2001–2023) × na_item (TE, P51G, D9, D1, P2, D62) × geo. Validar contra los rankings ya extraídos en sesión.
  - T1.2.2 Resultados: `hlth_cd_apr` (2011+), `demo_mlexpec`, PISA (solo años-ola), **HLO (World Bank, robustez educación)**, `ilc_lvho07a`/`ilc_lvho05a`.
  - T1.2.3 Controles: PIB/cápita PPS (`nama_10_pc`), estructura etaria (`demo_pjan`), WGI, Gini (`ilc_di12`); auditoría de confusores: obesidad/tabaco (WHO GHO), gasto sanitario privado (GHED, solo variable de control).
  - T1.2.4 España profundo: INE `aappgastcofog95_23.xlsx` + series IGAE por subsector (User-Agent navegador, throttle 1 req/s).
  - T1.2.5 **GNI\* Irlanda (CSO) + GNI Luxemburgo**: conector para denominador alternativo. *(Sin esto el tratamiento de outliers declarado no es operativo.)*
  - T1.2.6 **WWBI (Banco Mundial, source=64; verificado en vivo 2026-07-17)**: empleo público (% del empleo), masa salarial %PIB, prima salarial público-privado. La masa salarial POR FUNCIÓN ya viene gratis en T1.2.1 (`na_item=D1`). Caveats: derivado de encuestas, lagunas (Alemania vacía), definición sector público vs gobierno general — features, no serie titular.
  - T1.2.7 (OPCIONAL, para bolt-ons T3.5) conectores adicionales — códigos corregidos por verificación adversarial + doble-check Perplexity (3ª ronda): **CEPEJ-STAT** (presupuesto judicial; máquina-legible solo 2010–2022) + estudio CEPEJ del Justice Scoreboard (anual desde 2012 pero de base bienal+ad-hoc → panel parcialmente anual); **EU-SILC `ilc_li10`** (AROP pre-transferencias, pensiones EXCLUIDAS — no `ilc_li09`); **ESSPROS `spr_exp_type`/`spr_exp_func`** (`spr_exp_sum` muerto); **`cei_wm011`** (TASA reciclaje; `env_wasmun` = tonelajes); **contratación**: opentender bulk si sigue vivo post-eForms (estado disputado) o single-bidding calculado directo de la **TED API v3** (verificada en vivo). Códigos COFOG: tribunales **GF0303** (GF0301=policía); familia **GF1004** (GF1005=desempleo); en ESSPROS los códigos son propios (FAM, UNEMPLOY).
  - T1.2.8 AC: cada conector con test de humo + fichero en processed/ + fila en el manifiesto de vintage.
- **T1.3 Construcción del panel gold** ★ [S2]
  - T1.3.1 Dimensiones conformadas: geo (ISO + tabla canónica), función COFOG, na_item, año. Dedup OCDE↔Eurostat: Eurostat canónico para UE.
  - T1.3.2 Derivadas: `capital = P51G + D9`; `corriente = TE − capital`; shares por función; medias móviles 5a y lags 3–5a.
  - T1.3.3 Tests de calidad: PK única; rangos (gasto 0–60 %PIB); grid país×año completo o NaN explícito; **flags de outlier**: Italia superbonus (GF06 2021-23), Irlanda/Luxemburgo (usar T1.2.5), COVID 2020-22 (dummy).
  - T1.3.4 Política de datos faltantes documentada: cadencia PISA (sin interpolación en modelado — §T3.2), COFOG L2 solo 2001+, mortalidad tratable solo 2011+.
  - T1.3.5 AC: `gold_panel.parquet` + `gold_panel_dict.md` + tests verdes. **Este es el entregable de la Entrega 3 (fin S2).**

### T2 — Atlas descriptivo (RQ1–RQ2) [S3]
- **T2.0 (OPCIONAL) Prólogo siglo XX** — figura única de apertura de la memoria, sin ML
  - T2.0.1 Gasto público total %PIB 1900–2023, ~8–10 países con España destacada: empalme GMD/JST (verificados en vivo 2026-07-17) + Eurostat post-1995; Carreras-Tafunell para el detalle español.
  - T2.0.2 Anotaciones: guerras (ratchet), despegue del estado del bienestar, hitos España (Guerra Civil, 1978, UE).
  - T2.0.3 Caveats en pie de figura: gobierno central vs general (ruptura ~1950–70), sin desglose funcional pre-1970. **Solo descriptivo — el modelado sigue en 1995→.** Coste ~2–3 días; se recorta sin impacto si el calendario aprieta.
- **T2.1 Rankings y composición (RQ1)**
  - T2.1.1 Tablas/gráficos: top-bottom por función y tipo — 2023 y evolución. Vivienda: **GF06 L1 para 1995–2000, L2 desde 2001** (empalme documentado).
  - T2.1.2 Descomposición inversión vs corriente por país (stacked shares) + narrativa Este-cohesión vs Oeste-corriente.
  - T2.1.3 AC: notebook `02_atlas.ipynb` reproducible con las cifras verificadas (IT 4.4, EE 6.5, FR ~53 corriente).
- **T2.2 Tipologías (RQ2)**
  - T2.2.1 Vectores de composición (~20 dims, **ventana 2001–2023** por el límite L2) → PCA (scree, biplot).
  - T2.2.2 K-means + jerárquico sobre componentes; k por silhouette + estabilidad bootstrap (Jaccard ≥0.6 o se rebaja a "exploratorio").
  - T2.2.3 Contraste con tipologías Esping-Andersen.
  - T2.2.4 Trayectorias temporales de clúster.
- **T2.3 Perfil España**
  - T2.3.1 España vs UE27 por función y composición; brechas vivienda (0.5 vs 1.2) e inversión (3.0 vs 3.6).

### T3 — ML de rendimiento ajustado (RQ3–RQ4) ★ [S4–S7]
- **T3.1 Módulo sanidad (buque insignia)** ★ [S4–S5]
  - T3.1.1 Baseline OLS y GAM. **Métrica primaria pre-registrada: MAE medio sobre folds LOCO; el GBM se adopta solo si mejora el MAE del mejor baseline; en caso contrario el capítulo lo declara y analiza el baseline.**
  - T3.1.2 GBM (LightGBM): features = nivel + composición (share capital sanitario L2, 2001+) + controles; **CV leave-country-out Y time-blocked** (COVID excluido/dummy); tuning anidado o defaults fijos declarados.
  - T3.1.3 Residuales conformales: intervalo por país (split-conformal por bloques-país); **funnel plot**; solo se nombran países con intervalo ≠ 0. AC: figura funnel + tabla de flagged.
  - T3.1.4 SHAP: umbrales no lineales de nivel y share de inversión (RQ4); **extensión trabajadores**: intensidad laboral (share D1 de la función) + empleo público y prima salarial (WWBI) como features — ¿predice *cómo se dota de personal* más allá de *cuánto se gasta*? (masa salarial = plantilla × salario medio: dos países con el mismo 12% PIB pueden ser muchos-baratos o pocos-caros). Estabilidad bootstrap de cada umbral.
  - T3.1.5 Multiverso: 3 sets de controles × **3 definiciones de gasto (%PIB, per-cápita PPS, %GNI\* para IE/LU)** × 2 lags; estabilidad de rangos (Spearman). Auditoría de confusores: residuales held-out vs obesidad/tabaco/Gini/gasto privado.
  - T3.1.6 AC: residuales no correlacionan con PIB/cápita (|r|<0.3); **n efectivo ≈ 33 clústeres-país declarado en el capítulo**.
- **T3.2 Módulo educación (réplica)** [S6]
  - T3.2.1 Mismo pipeline **solo sobre años-ola PISA** (sin outcomes interpolados — conformal no se calibra sobre puntos sintéticos); HLO como robustez.
  - T3.2.2 AC: pipeline corre con cambio de config, no de código; **declaración propia de n efectivo** (≈33 países × ~7 olas).
- **T3.3 Módulo vivienda (UE-only)** [S6–S7]
  - T3.3.1 Gasto GF0601+GF1006 (2001+) → sobrecarga + hacinamiento SILC (2003+).
  - T3.3.2 Italia-superbonus con/sin; **declaración propia de n efectivo**.
- **T3.4 Síntesis entre módulos** ★ [S7]
  - T3.4.1 Matriz de correlación de residuales + biplot (exploratorio por mandato del consejo).
  - T3.4.2 Evolución temporal del rendimiento ajustado (ventanas móviles).

### T3.5 — (OPCIONAL) Módulos bolt-on y features transversales [S7–S8, solo si núcleo en verde]
*Veredictos de la 3ª ronda del consejo (4 motores + web-check Perplexity), códigos corregidos. Son bolt-ons, NUNCA pilares nuevos — el núcleo sigue siendo sanidad+educación+vivienda.*
- **T3.5.1 JUSTICIA (CEPEJ)** — el módulo nuevo más limpio (unánime): presupuesto judicial (CEPEJ; contraste Eurostat **GF0303** tribunales) → disposition time / clearance rate, con caseload entrante como control. Panel anual UE 2012–2022 vía Justice Scoreboard; restringir a civil/mercantil 1ª instancia.
- **T3.5.2 FOCALIZACIÓN DE TRANSFERENCIAS** — el bolt-on más barato (reusa pipeline SILC de vivienda): gasto social no-pensiones (ESSPROS `spr_exp_type` o GF10 sin vejez; variante familia **GF1004**) → reducción de AROP por transferencias (**`ilc_li10`** pre vs `ilc_li02` post). Encuadre: eficiencia de FOCALIZACIÓN (vínculo parcialmente mecánico, declarado).
- **T3.5.3 Features transversales**: (a) calidad de contratación pública (opentender: single-bidding, CRI Fazekas) como feature país-año en todos los módulos + UNA figura secundaria: residuales vs single-bidding; (b) reciclaje municipal (**GF0501**→`env_wasmun`) como mini-módulo o descriptivo.
- **T3.5.4 Anexo "considerado y rechazado"** (oro para la defensa): GF05→emisiones (error de constructo), I+D→patentes (las patentes siguen al I+D EMPRESARIAL), cultura/defensa/DESI/green-tagging/GTED/SOEs/absorción NGEU — cada uno con su porqué. ALMP aparcado (split 2-2 del consejo; solo viable como gasto POR PARADO, dataset en redisstat de DG EMPL, no en Eurostat).

### T4 — Posición sobre deep learning [S7, ligera]
- **T4.1 Justificación escrita** de por qué DL (LSTM/TFT/transformers tabulares) es indefendible con n≈33 clústeres y cadencia anual — se anticipa la pregunta del tribunal. *(La comparativa TabPFN del plan v1 se elimina: violaba la regla de UNA línea técnica. Si el tutor la pidiera explícitamente, se reabre como apéndice.)*

### T5 — Capa de producto [S7–S8]
- **T5.1 App Streamlit**
  - T5.1.1 Vistas: atlas (rankings/mapas), composición por país, funnel por módulo, ficha-país (España destacada).
  - T5.1.2 Descarga CSV por vista; página de metodología con caveats.
  - T5.1.3 AC: `streamlit run app.py` funciona desde clone limpio. *(La app es escaparate: si se retrasa, los notebooks bastan.)*
- **T5.2 Mini-tabla de eventos de política (V2, opcional)**
  - T5.2.1 15–20 hitos legales (PGE, prórrogas, superbonus, leyes vivienda) curados A MANO desde BOE/EUR-Lex, fechas + enlaces. SIN NLP masivo.
- **T5.3 Stretch: España CCAA** [S8, solo si S1–S7 verdes]
  - T5.3.1 REGOFI/IGAE CCAA + benchmarking conformal de 17 CCAA (sanidad/educación), N=17 declarado.

### T6 — Memoria y defensa ★ [S8–S10]
- **T6.1 Memoria** ★ [S8–S9]
  - T6.1.1 Estructura: intro/motivación, literatura (AST, WHO-2000 y críticas, value-added models, funnel plots SMR — anclaje HEOR), datos (contrato gold + landscape), métodos (caveats: no causal, OVB, stock-flujo, n efectivo), resultados por RQ, limitaciones, conclusiones, **anexo de reproducibilidad + licencias de datos + declaración de uso de IA** (consejo multi-modelo documentado).
  - T6.1.2 Capítulo de métodos contra checklist del consejo (renombrado, conformal, LOCO, multiverso, outliers, no-normativo).
  - T6.1.3 **Draft completo fin de S9 → tutor.** AC: draft enviado.
- **T6.2 Defensa** ★ [S9]
  - T6.2.1 Deck 15–20 slides + demo Streamlit (con grabación de respaldo).
  - T6.2.2 Banco de preguntas hostiles ("¿qué es un residual?", "¿por qué no DEA?", "¿causalidad?", "¿por qué no DL?") con respuestas de 30s.
- **T6.3 Buffer real [S10]** — solo re-runs, correcciones del tutor e imprevistos. Sin trabajo nuevo.

---

## 4. Calendario y camino crítico

```
S1  T0.1–T0.2 gate ★ ─ T1.1 + T1.2 arranque
S2  T1.2–T1.3 gold ★ ─ T0.3 entregas (= Entrega 3)
S3  T2 atlas
S4  T3.1 sanidad ★
S5  T3.1 conformal/multiverso ★ ─ T0.4 checkpoint tutor ★
S6  T3.2 educación ─ T3.3 vivienda arranque
S7  T3.3 cierre ─ T3.4 síntesis ★ ─ T4 ─ T5.1 arranque
S8  T5.1 app ─ T6.1 memoria arranque (+T5.3 solo si verde)
S9  T6.1 draft completo → tutor ★ ─ T6.2 defensa ★
S10 T6.3 buffer real
```
**Camino crítico:** T0.1 → T1.2.1 → T1.3 → T3.1 → T0.4 → T3.4 → T6.1 → T6.2. Holgura real solo en T2.2, T5.1, T5.2; T5.3 y el tier global son prescindibles por diseño.

## 5. Riesgos y disparadores de contingencia

| Riesgo | Prob. | Impacto | Mitigación / trigger |
|---|---|---|---|
| Tutor no avala el pivote | media | fatal para el plan | Gate S1 escrito → plan B vivienda+métodos (pérdida: 1 semana). Checkpoint S5 evita deriva. |
| ETL se come el calendario | media | alto | Gold mínimo = sanidad; educación/vivienda recortables sin romper la tesis |
| PISA/L2 más agujereados de lo previsto | media | medio | HLO robustez; vivienda degradable a descriptivo (RQ1) |
| Conformal costoso de calibrar | baja | medio | Bootstrap por bloques como sustituto; multiverso reducido a 6 specs |
| Tribunal ataca "residual = eficiencia" | segura | alto | Renombrado + literatura HEOR + intervalos + no-normativo; ensayado en T6.2.2 |
| Carga de trabajo (jornada completa) | media | alto | Módulos independientes y recortables; S10 sin trabajo nuevo; T5 degradable a notebooks |

## 6. Decisiones ya tomadas (no reabrir)
1. UNA línea técnica: GBM + SHAP + incertidumbre conformal. Sin DEA, sin RAG, sin DL (T4 = justificación escrita).
2. "Rendimiento ajustado", nunca "eficiencia" sin apellidos — también en título y app.
3. 3 módulos máximo; impuestos/orden/pensiones fuera; tier global fuera (línea futura).
4. Eurostat canónico UE; OCDE solo consulta; PISA sin interpolar en modelado.
5. Vivienda (proyecto actual) = fallback intocable en `main` hasta el aval escrito.
