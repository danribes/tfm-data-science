# Resumen ejecutivo — proyecto "Dinero público → Resultados"

*v1, 2026-07-18. Síntesis de objetivos, fuentes y procedimientos. Documentos de detalle: [pitch al tutor](pitch_tutor_fiscal.md) · [plan UE](PLAN_public_money_outcomes.md) · [plan GLOBAL](PLAN_public_money_outcomes_GLOBAL.md) · [variante C vivienda](PLAN_vivienda_consecuencias.md) · [programa integral](PLAN_integral.md) · [panorama de datos](data_landscape.md) · [diccionario maestro](data_dictionary_master.md) · [diccionario vivienda](data_dictionary_vivienda.md).*

---

## 1. Objetivos

**Pregunta central:** ¿qué gobiernos convierten mejor el dinero de los contribuyentes en resultados para la población — *rendimiento ajustado* al contexto, nunca "eficiencia" causal — y qué papel juegan la **composición del gasto** (inversión vs corriente) y la presión demográfica?

Cuatro preguntas operativas:
1. **RQ1** — ¿Cuánto y en qué se gasta? Por función (sanidad, educación, vivienda, pensiones…) y por tipo económico (salarios, bienes y servicios, intereses, subvenciones, transferencias, prestaciones, capital).
2. **RQ2** — ¿Qué perfiles/tipologías de gasto existen entre países y CCAA?
3. **RQ3** — ¿Quién obtiene mejores resultados de los que su gasto y su contexto predicen, con qué certeza estadística?
4. **RQ4** — ¿Importa la mezcla? ¿Un euro de inversión rinde más que uno corriente? ¿Cómo pesa la dotación de personal (plantilla × salario)?

**Tres variantes de TFM** (deadline 30-sep; gate del tutor en S1; fallback vivienda intacto en `main`):
- **A — UE:** 33 países, las 10 funciones, composición completa.
- **B — Global:** ~180 países, sanidad como núcleo (la mejor aritmética muestral).
- **C — Vivienda como consecuencias** *(recomendada en el pitch)*: el proyecto avalado profundizado — cadena gasto → rendimiento → asequibilidad → amplificador migratorio → respuesta política.

**Programa integral** (post-TFM, 9 fases, ~9–12 meses): CCAA 30 años → Europa completa → la UE como gobierno → mundo por continentes → focos de baja fiscalidad → empresas públicas → flujos entre países → migración → síntesis. El TFM es la Fase 0; el resto, hoja de ruta y capítulo de líneas futuras.

## 2. Fuentes de datos (~125 catalogadas; ~38 series seleccionadas para extraer)

| Capa | Fuentes clave | Estado |
|---|---|---|
| **Gasto fiscal** | Eurostat `gov_10a_exp` (COFOG × tipo económico, 33 países, 1995–2023) · INE COFOG España (un xlsx, 1995–2023) · IGAE subsectores · liquidaciones CCAA (~2002→) · FMI GFS (mundo) · BOE-PGE | ✅ verificadas en vivo |
| **Resultados** | EU-SILC (sobrecarga `ilc_lvho07a`, hacinamiento `ilc_lvho05a`, pobreza `ilc_li10`) · mortalidad tratable `hlth_cd_apr` (2011+) · PISA/HLO · esperanza de vida · **panel de asequibilidad propio** (17 CCAA × trimestre) | ✅ dims verificadas |
| **Trabajadores públicos** | WWBI (302 indicadores; 6 elegidos: empleo público, masa salarial, prima público-privada, sanitarios, docentes) · D1 por función (en gov_10a_exp) | ✅ verificada |
| **Decisiones/política** | BOE API (sumarios ≥1994, XML con tablas parseables; PGE y leyes CCAA extraídas en vivo; pesetas pre-2002) · TED v3 · BDNS · MIVAU/SERPAVI | ✅ parser probado |
| **Demografía** | INE migraciones/padrón (pipeline propio) · Eurostat `migr_*` · UN DESA migrant stock | ✅/[D] |
| **Comparables internacionales** | OECD price-to-income/price-to-rent · BIS precios de vivienda · OECD Affordable Housing DB · WHO GHED (sanidad, ~190 países) | catalogadas |
| **Histórico 1900→** | Global Macro Database (243 países) · JST Macrohistory · Carreras-Tafunell (España) | ✅ verificadas |

**Regla de extracción: selectiva, nunca volcado.** Una columna se extrae solo si alimenta un bloque de análisis concreto, pasa smoke-test y cabe en el grano del gold (`geo × periodo × variable × valor × flag × vintage`). Objetivo: ~38 series + 1 tabla de eventos, gold < 100 MB.

**Hallazgos críticos ya corregidos:** INE renumeró el IPV (76201/49300 → **80270/80271**; config del pipeline pendiente de actualizar) · `gov_10a_sub` no existe [V-404] · HLO no es API sino descarga · 5 códigos erróneos de la propia recomendación del consejo cazados por verificación adversarial (GF0303 tribunales, GF1004 familia, `ilc_li10`, `spr_exp_type`, GF0451 inexistente).

## 3. Procedimientos

**Método — UNA línea técnica, vetada por 3 rondas de consejo multi-modelo (Claude+GLM+MiMo+Gemini) con verificación adversarial y web-check:**

1. **ETL con contrato:** `raw/` (evidencia inmutable) → `processed/` (una fuente = una tabla tidy) → `gold/` **con tests automáticos** (PK única, rangos, grid completo, flags de outlier: superbonus IT 2021-23, GNI\* Irlanda, COVID 2020-22). Ningún código entra en gold sin smoke-test.
2. **Descriptivo (RQ1–RQ2):** rankings por función y tipo, composición inversión/corriente, clustering de tipologías solo donde N lo permite (N≥150 global; exploratorio a N=33).
3. **Núcleo ML (RQ3–RQ4):** GBM prediciendo el resultado desde gasto (promedios 5a, retardo 3–5a) + controles (renta, demografía, gobernanza) → **residual = rendimiento ajustado con intervalo conformal** → **funnel plot, nunca liga**; validación **leave-country-out + bloques temporales** (tuning anidado); **SHAP** para umbrales no lineales y la extensión de personal; **multiverso de especificaciones** (controles × definiciones de gasto × retardos) con estabilidad de rangos; chequeo residual⊥renta (y ⊥capacidad estadística en lo global).
4. **DL solo donde es honesto:** extractor BOE en cascada (C0 parser determinista → C1 triaje → **C2 fine-tune MarIA/RoBERTa-BNE** → C3 LLM solo como etiquetador y residuo de casos difíciles); comparador DL de forecasting en el panel trimestral (avalado por la Entrega 2 original); TabPFN con permiso del tutor. **Nunca** LSTM/TFT sobre paneles macro anuales — y explicar por qué.
5. **Eventos de política:** tabla curada BOE (Ley 12/2023, zonas tensionadas, planes estatales) + **control sintético** para el tope de alquileres de Cataluña (con placebos).
6. **Producto:** app Streamlit (funnels por grupo, atlas, ficha España) + memoria con capítulo de métodos anti-tribunal, anexo de reproducibilidad, licencias de datos y **declaración de uso de IA**.

**Calendario TFM (10 semanas):** S1 aval ESCRITO del tutor ★ + conectores → S2–S3 gold con tests (= Entrega 3) → S4–S5 módulo insignia + checkpoint tutor ★ → S6–S7 réplicas + síntesis → S8 app → S9 borrador completo → S10 buffer real.

**Salvaguardas innegociables:** no causal, no normativo, no ranking-liga; estratificación por renta en lo global; incertidumbre en cada cifra publicada; anexo "considerado y rechazado" documentando cada idea descartada y su porqué.
