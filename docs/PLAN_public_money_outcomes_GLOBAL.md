# PLAN GLOBAL — "Public Money → Outcomes": rendimiento ajustado del gasto público a escala mundial

*Variante global del [PLAN_public_money_outcomes.md](PLAN_public_money_outcomes.md) (UE). v2, 2026-07-17 (v1 auditada por agente revisor independiente; 10 defectos corregidos). **Todos los países del mundo con datos utilizables**, por niveles de disponibilidad. Deadline: fin de septiembre 2026 (~10 semanas, dedicación parcial).*

---

## 1. Especificación

**Pregunta central:** a escala mundial, ¿qué gobiernos convierten mejor el dinero público en resultados para la población — *rendimiento ajustado* al contexto y al nivel de renta — y qué papel juega la composición del gasto donde es observable?

### Preguntas de investigación
| RQ | Pregunta | Cobertura real (honesta) |
|---|---|---|
| **RQ1** | ¿Cómo se gasta el dinero público en el mundo: cuánto, en qué funciones, con qué mezcla? ¿Quién gasta más en vivienda, sanidad, educación? | Total: ~190. Por función (COFOG): **solo reporters FMI GFS (~60–90)**. Capital sanitario: **solo subconjunto GHED-HK** (ver AC T1.2.1) |
| **RQ2** | ¿Qué tipologías de gasto existen y siguen líneas de renta o región? | ~150+ (clustering pasa a *stretch* — ver T2.2) |
| **RQ3** | ¿Qué países obtienen mejores resultados de lo que su gasto, renta y contexto predicen — con qué certeza? | Sanidad ~180+ panel; educación **corte transversal** ~140 |
| **RQ4** | ¿Predice la composición (capital vs corriente) mejores resultados? | **Submuestra HK-reporters**, declarada — espejo de la honestidad "reporters" del GFS |

### Guardarraíles (heredados + globales)
- Heredados: no causal, no normativo, no liga, no DEA/RAG/DL, "rendimiento ajustado" nunca "eficiencia".
- **Estratificación por renta (grupos BM, por año) en TODO**: funnels, calibración conformal, **SHAP y chequeos de residuales dentro de grupo** (pooled solo como sensibilidad). Nunca Noruega-vs-Chad.
- **Procedencia del dato como primera clase**: (a) covariable de capacidad estadística **a nivel país** (SPI empalmado con SCI, regla de vintage declarada; PEFA/OBS relegados a anexo — no tienen panel anual); (b) **flag de procedencia del outcome** (registro vital vs imputado por modelo WHO/IGME) en el coverage map + spec de robustez que excluye país-años fuertemente imputados. *(Riesgo circularidad: HALE/U5MR/HLO se imputan con covariables que incluyen PIB — "superar la predicción" podría redescubrir el modelo imputador de la OMS.)*
- PPP constante (int$ 2021); exclusiones por regla (población <300k; proxy de conflicto WDI), no ad-hoc.

### Criterios de éxito
1. Aval escrito del tutor S1 (gate) + checkpoint S5. Fallback vivienda intacto en `main`.
2. Gold global reproducible + **coverage map** (país×año×variable×procedencia) — el mapa de agujeros es un resultado, no una vergüenza.
3. RQ1–RQ4 respondidos con la maquinaria vetada, cada uno sobre su cobertura declarada.
4. Memoria (con declaración de uso de IA) + app + defensa antes del 30-sep.

---

## 2. Alcance por niveles de datos

| Tier | Países | Fuentes gasto | Resultados | Papel |
|---|---|---|---|---|
| **A — Sanidad global** ★ | ~180+ | WHO GHED 2000–2023 (público/privado/OOP per cápita PPP; **HK capital = submuestra con AC propia**) | esperanza de vida (preferencia registro vital), U5MR, HALE (con flag de procedencia) | Núcleo RQ3–RQ4. ~3.500+ filas, ~180 clústeres |
| **B — Educación global** | ~140 | UNESCO UIS | HLO (BM) | **Corte transversal** (HLO no es panel utilizable): réplica LOCO sin bloque temporal ni lags — modelo propio, no "config del A" |
| **C — Funciones COFOG mundo** | ~60–90 | FMI GFS COFOG + clasificación económica | — | RQ1-funciones ("¿quién gasta más en vivienda?") SOLO reporters, N declarado |
| **D — UE contraste (mínimo)** | ~33 | Eurostat (conector del plan UE) + **outcome emparejado: esperanza de vida** | esperanza de vida | **Refit mínimo explícito** (T3.3): mismo outcome que el global para que la comparación de residuales sea interpretable |

**Controles globales:** PIB/cápita PPP, estructura etaria (WDI/UN WPP), WGI, **Gini WDI** (SWIID descartado — sin conector presupuestado), urbanización; confusores: obesidad/tabaco (WHO GHO).
**Fuera de alcance:** impuestos como módulo, vivienda como módulo de resultado global, BOE/extractor, CCAA, tipologías si el calendario aprieta (T2.2 = stretch).

---

## 3. Árbol de tareas

*◆ = cambia respecto al plan UE. Sin marca = idéntico (misma AC).*

### T0 — Gobernanza ★ [S1, S2–S3, S5]
- T0.1 Pitch al tutor ★ ◆ argumento: "mismo método, ~180 clústeres en vez de 33; DOS módulos de resultado (sanidad panel + educación transversal) + un contraste UE mínimo". Evidencia: GHED verificado, rankings UE como teaser.
- T0.2 Fallback (idéntico: rama `fiscal-global`, gate S1 escrito).
- T0.3 Reescritura entregas [S2–S3] ◆ E3 = gold global + coverage map, **entregable fin S3** (fecha realista, no "fin S2").
- T0.4 Checkpoint tutor S5: primer funnel por grupo de renta.

### T1 — Plataforma de datos global ★ [S1–S3]
- **T1.1 Andamiaje** (plan UE + registro de exclusiones por regla).
- **T1.2 Conectores** ★
  - T1.2.1 ◆ WHO GHED: gasto sanitario completo. **AC doble: ≥170 países ≥15 años en gasto público corriente; AC-HK separada: ≥60 países ≥8 años en capital (HK) — si no se alcanza, RQ4 se declara sobre la submuestra real y punto.**
  - T1.2.2 ◆ UNESCO UIS + HLO. **AC: ≥130 países con par gasto→HLO; AC-tendencia: ≥2 puntos temporales solo para las afirmaciones de evolución.**
  - T1.2.3 ◆ FMI GFS (MCP operativo): COFOG + clasificación económica; manifiesto de cobertura publicado.
  - T1.2.4 ◆ Controles WDI/UN (MCP operativo) + **SPI/SCI empalmado (covariable a NIVEL PAÍS, regla de vintage declarada)** + **WWBI (source=64, misma API BM; verificado en vivo)**: empleo público, masa salarial, prima salarial público-privado (~200 países, 2000→) — features del módulo sanidad (intensidad laboral/dotación), con sus lagunas de encuesta declaradas.
  - T1.2.5 WHO GHO (obesidad/tabaco).
  - T1.2.6 Eurostat gasto sanitario UE (reuso conector plan UE) **+ esperanza de vida `demo_mlexpec`** (outcome emparejado del Tier-D).
  - T1.2.7 ◆ **Auxiliares estáticos con vintage fijo**: grupos de renta BM por año, proxy de conflicto WDI, población. *(UCDP/SWIID/PEFA descartados — sin conector presupuestado.)*
  - T1.2.8 AC global: test de humo + vintage por conector; `coverage_map.parquet` **con flag de procedencia del outcome**.
- **T1.3 Gold global** ★ [S2–S3]
  - T1.3.1 País canónico ISO3; grupos de renta POR AÑO; región.
  - T1.3.2 Derivadas: PPP constante, shares HK. **Las medias móviles y lags se computan DENTRO de cada fold de CV, no aquí** (evita fuga temporal — trampa detectada en revisión).
  - T1.3.3 Exclusiones por regla (población, conflicto-proxy, <8 años de datos) → anexo.
  - T1.3.4 Tests: PK, rangos, sin imputación silenciosa; outliers globales documentados (petro-estados = análogos de Irlanda).
  - T1.3.5 AC: `gold_global.parquet` + diccionario + coverage map = **Entrega 3, fin S3**.

### T2 — Atlas descriptivo (RQ1) [S3–S4] ◆ recortado
- T2.0 (OPCIONAL) **Prólogo siglo XX** — figura única de apertura (gasto total %PIB 1900–2023, GMD/JST + Eurostat, España destacada; solo descriptivo, caveats central-vs-general y sin desglose funcional pre-1970; recortable). Con GMD (243 países) el prólogo global es incluso más natural que en el plan UE.
- T2.1 Rankings globales: sanidad/educación per cápita PPP y %PIB por grupo de renta; funciones (vivienda) solo reporters GFS con N declarado; capital vs corriente solo HK-reporters. AC: notebook reproducible.
- T2.2 ◆ **Tipologías (RQ2) = STRETCH [S7]**, solo si T3.1 va en verde. Clustering ~150 países, silhouette+bootstrap, contraste con grupos de renta. *(Sacrificado del núcleo para pagar la semana extra de ETL — en v1 el calendario fingía que la semana salía gratis.)*
- T2.3 Perfil España vs mundo.

### T3 — ML de rendimiento ajustado ★ [S4–S7]
- **T3.1 Sanidad global (buque insignia)** ★ [S4–S5]
  - T3.1.1 Baselines OLS/GAM; **métrica pre-registrada: MAE sobre folds LOCO**; GBM se adopta solo si mejora.
  - T3.1.2 GBM: nivel + share HK (submuestra) + controles + grupo de renta; **LOCO + bloque temporal; rolling/lags computados intra-fold; tuning anidado o defaults declarados**.
  - T3.1.3 ◆ Conformal robusto: **block-conformal a nivel país (intercambiabilidad de países, no de filas), calibración estratificada por grupo de renta**; n efectivo por país ~3–5 declarado; flags anti-conservadores mitigados con nivel 90% + corrección por autocorrelación. Funnels POR GRUPO. AC: figura + tabla flagged por grupo.
  - T3.1.4 ◆ SHAP **dentro de cada grupo de renta** (umbral "$500 PPP" estimable de verdad en el grupo bajo); pooled solo como sensibilidad; estabilidad bootstrap.
  - T3.1.5 Multiverso: 3 sets de controles × 2 definiciones de gasto × 2 lags × 2 tratamientos de renta (interacción vs estratificado); Spearman de estabilidad. **Una spec de robustez excluye país-años con outcome fuertemente imputado.**
  - T3.1.6 ◆ AC: residuales held-out no correlacionan (|r|<0.3, **calculado dentro de grupo**) ni con PIB/cápita ni con SPI — **sobre la spec que EXCLUYE SPI de las features** (evita circularidad).
- **T3.2 Educación global (transversal)** [S6] ◆
  - T3.2.1 Modelo transversal propio: pooled reciente, LOCO simple, SIN bloque temporal ni lags multi-año (no hay panel); conformal por país no aplicable → intervalos por bootstrap.
  - T3.2.2 AC: n y diseño declarados como distintos del módulo A (no se finge "misma config").
- **T3.3 Contraste UE mínimo** [S6–S7] ◆ explícito, ya no escondido:
  - T3.3.1 Refit del pipeline A sobre panel Eurostat UE-33 con **outcome emparejado (esperanza de vida)**.
  - T3.3.2 **Concordancia de rangos (Spearman + IC bootstrap)** entre residuales global-UE33 y refit fino. **Sin gate pass/fail** (r a n=33 lleva ±0.25 de IC — se reporta, se interpreta, no se aprueba/suspende).
- **T3.4 Síntesis** ★ [S7]: correlación residuales sanidad×educación (con la cautela transversal), persistencia de flagged entre specs.

### T3.5 — (OPCIONAL) Bolt-ons — solo aplicables al contraste UE/CoE, no al tier global
- Justicia CEPEJ (~45 estados CoE, panel anual UE 2012–2022 vía Justice Scoreboard; gasto **GF0303** tribunales), focalización de transferencias (SILC `ilc_li10`, UE), contratación pública (opentender, UE) — ver detalle en el plan UE (T3.5). En el plan global entran, como mucho, como análisis del Tier-D; el anexo "considerado y rechazado" (T3.5.4 del plan UE) aplica igual.

### T4 — Posición sobre DL [S7, ligera] — idéntico plan UE (la respuesta sigue siendo GBM: clústeres≈180, cadencia anual).

### T5 — Producto [S7–S8]
- T5.1 Streamlit: coroplético por grupo, funnels, ficha-país (España), **página coverage-map navegable** (honestidad como feature). AC: corre desde clone limpio; degradable a notebooks.
- T5.2 (opcional) hitos de política sanitaria global curados a mano (Tailandia UHC 2002, Ruanda mutuelles…).

### T6 — Memoria y defensa ★ [S8–S10] — idéntico plan UE (declaración IA + anexo reproducibilidad) más:
- T6.1.x ◆ limitaciones globales: procedencia/imputación de outcomes, comparabilidad PPP, por qué no se compara entre grupos, sesgo de no-reporte (los que no reportan no son aleatorios), HK-submuestra.

---

## 4. Calendario

```
S1  T0.1–T0.2 gate ★ ─ T1.1 ─ T1.2.1/T1.2.4 (GHED+WDI primero)
S2  T1.2 resto ─ T1.3 arranque ★ ─ T0.3 arranque
S3  T1.3 cierre + coverage map ★ (= Entrega 3) ─ T0.3 cierre ─ T2.1 arranque
S4  T2.1/T2.3 cierre ─ T3.1 sanidad ★
S5  T3.1 conformal/multiverso ★ ─ T0.4 checkpoint tutor ★
S6  T3.2 educación ─ T3.3 contraste UE arranque
S7  T3.3 cierre ─ T3.4 síntesis ★ ─ T4 ─ (T2.2 tipologías SOLO si verde) ─ T5.1 arranque
S8  T5.1 app ─ T6.1 memoria arranque
S9  T6.1 draft → tutor ★ ─ T6.2 defensa ★
S10 T6.3 buffer real
```
Camino crítico: T0.1 → T1.2.1 → T1.3 → T3.1 → T0.4 → T3.4 → T6.1 → T6.2. El coste real de la semana extra de ETL lo paga T2.2 (degradado a stretch), no un descuento imaginario.

## 5. Riesgos diferenciales

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| ETL (≥7 fuentes reales) desborda S1–S3 | **alta** | alto | Orden estricto GHED+WDI primero; GFS/UIS recortables; la tesis sobrevive con sanidad sola |
| GHED-HK insuficiente para RQ4 | alta | medio | AC-HK separada + RQ4 declarado sobre submuestra (espejo del "reporters" GFS) |
| Outcomes imputados contaminan residuales | media-alta | alto | Flag de procedencia + spec de robustez sin país-años imputados + preferencia registro vital |
| Conformal anti-conservador (n≈3-5/país) | media | alto | Block-conformal por país, calibración por grupo, nivel 90%, declarado en métodos |
| Tribunal: "¿Noruega vs Chad?" | segura | alto | Estratificación en TODO (funnels, SHAP, chequeos); ensayado en T6.2.2 |
| Tutor percibe más alcance que el plan UE | media | fatal | Pitch: 2 módulos + contraste mínimo; T2.2 stretch; una fuente núcleo (GHED) |

## 6. UE vs GLOBAL — decisión

| Criterio | Plan UE | Plan GLOBAL |
|---|---|---|
| N para ML | ~33 clústeres (justo) | **~180 clústeres (holgado)** |
| RQ1 funciones/vivienda | **completa (COFOG L1+L2)** | solo reporters GFS (~60–90) |
| Composición inversión/corriente | **todas las funciones** | solo sanidad-HK (submuestra) + GFS |
| Calidad/comparabilidad | **alta y homogénea** | heterogénea (procedencia gestionada, no resuelta) |
| ETL real | 1 fuente núcleo | ≥7 fuentes (S1–S3 + T2.2 sacrificado) |
| Educación | panel PISA (olas) | transversal HLO (más débil) |
| Encaje HEOR del autor | medio | **máximo (GHED, salud global)** |
| Novedad | composición×función UE | **umbrales globales de gasto sanitario + coverage-map honesto** |
| Riesgo tribunal | N justo | imputación/comparabilidad (mitigadas y declaradas) |

**Recomendación:** prioridad = pregunta de funciones y composición inversión/corriente → **UE**. Prioridad = solidez muestral del ML + encaje HEOR → **GLOBAL (sanidad núcleo)**, la variante que el consejo (ronda 2, inversión de niveles) señaló como de mejor aritmética. Ambos comparten T0, la maquinaria T3 y T6 — la decisión puede tomarse EN el pitch del tutor presentando las dos portadas.
