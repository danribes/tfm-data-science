# VARIANTE C — Vivienda como laboratorio de consecuencias del gasto público

*v1, 2026-07-17. Combina el [programa integral](PLAN_integral.md) con el proyecto de vivienda comprometido: la vivienda deja de ser "un módulo más" y pasa a ser el CASO DE CONSECUENCIAS donde se demuestra toda la maquinaria fiscal. Es la variante de MENOR riesgo con el tutor: el proyecto avalado se conserva y se amplía — no hay pivote, hay profundización. Reutiliza: panel de asequibilidad ya construido, maquinaria GBM+conformal (planes UE/GLOBAL), bolt-ons verificados, capa de eventos BOE.*

---

## 1. La idea en una frase

**Seguir el euro de vivienda de punta a punta:** cuánto se gasta y en qué (nivel + composición) → qué rendimiento ajustado obtiene cada país/CCAA de ese gasto → qué consecuencias medibles tiene gastarlo mal o poco (asequibilidad, sobrecarga, hacinamiento) → cómo lo amplifica la presión migratoria/demográfica → y cómo responde la política (leyes BOE), cerrando el círculo.

**La cadena de consecuencias (marco del proyecto):**
```
decisiones fiscales (PGE/CCAA/BOE)
   → gasto en vivienda: nivel + composición (GF06/GF0601+GF1006; capital vs corriente)
      → rendimiento ajustado del gasto (residual conformal, funnel)
         → consecuencias: asequibilidad (ratio IPV/salario), sobrecarga SILC, hacinamiento
            → amplificador: presión demográfica/migratoria (stock+flujos)
               → respuesta política (Ley 12/2023, zonas tensionadas, planes estatales)
                  → (vuelta al inicio)
```
Cada flecha es ASOCIATIVA y se declara como tal — la cadena es el hilo narrativo, no una afirmación causal encadenada.

## 2. Bloques de análisis (todo con datos ya verificados en vivo)

### B1 — ¿Dónde va el euro de vivienda? (descriptivo, 1995–2023)
- España vs UE-33: GF06 total (L1 desde 1995) y GF0601+GF1006 (L2 desde 2001); **España 0,5 %PIB vs UE 1,2 (2023, verificado)**; Italia 4,4 = artefacto superbonus (outlier documentado).
- Composición: ¿capital (P51G+D9 — construir/rehabilitar) o corriente/transferencias (ayudas al alquiler)? Colapso de la inversión post-2008 vs recuperación (o no).
- CCAA: liquidaciones de vivienda por comunidad (Hacienda/IGAE) — el mapa interno español.
- *Datos: Eurostat gov_10a_exp ✅, INE COFOG ✅, IGAE ✅ (UA navegador).*

### B2 — Rendimiento ajustado del gasto en vivienda, UE-33
- El módulo T3.3 del plan UE tal cual: GF0601+GF1006 → sobrecarga (`ilc_lvho07a`) + hacinamiento (`ilc_lvho05a`), GBM + residual conformal + funnel; controles renta/urbanización/demografía.
- Resultado: qué países obtienen mejores condiciones de vivienda de las que su gasto y contexto predicen — y dónde cae España, con intervalo.

### B3 — La capa CCAA (el terreno del TFM original)
- Panel propio: gasto vivienda CCAA × asequibilidad CCAA (el gold `ratio_asequibilidad` YA construido) + sobrecarga regional si SILC da desglose.
- Benchmarking conformal de 17 CCAA (N=17 declarado, funnel estilo SMR — método del plan, escala del proyecto avalado).
- *Aquí el TFM comprometido y el programa integral se tocan físicamente: mismas filas, columnas nuevas.*

### B4 — El amplificador migratorio (hipótesis final del autor, operacionalizada)
- Features de presión: Δpoblación, Δstock migrante, flujos INE por CCAA (pipeline existente) / Eurostat-UN DESA por país.
- **La pregunta de consecuencias:** ¿los países/CCAA con PEOR rendimiento ajustado en vivienda muestran mayor deterioro de asequibilidad/sobrecarga ante el MISMO shock demográfico? → interacción presión×rendimiento en el modelo de asequibilidad. Asociativo, declarado.
- Gemelo sanitario opcional: misma interacción sobre listas de espera/outcomes — conecta con el módulo sanidad si hay tiempo.

### B5 — Respuesta política y eventos (capa BOE)
- Tabla curada de hitos (15–20): Ley 12/2023 por el derecho a la vivienda ✅ (extraída en vivo), zonas tensionadas, planes estatales, superbonus IT como contraste europeo.
- **Control sintético para Cataluña** (tope de alquileres 2024): Cataluña sintética desde pool de CCAA donantes → ¿divergencia post-tratamiento en asequibilidad/oferta? Método establecido, amable con tribunal.

### B6 — Síntesis de consecuencias (la pieza delicada — encuadre estricto)
- **Escenario ilustrativo, NO contrafactual causal:** "si España presentara el residual mediano de la UE en vivienda, la sobrecarga asociada a su nivel de gasto y contexto sería X pp menor" — presentado como ILUSTRACIÓN DESCRIPTIVA del tamaño de la brecha de rendimiento, con intervalo, nunca como efecto de política.
- Cuantifica "la pérdida de eficiencia impacta la vivienda" sin cruzar la línea causal que el consejo vetó tres veces.

## 3. Encaje con las entregas y el tutor

| Pieza | Estado |
|---|---|
| Entregas 1–2 (idea vivienda) | **casi intactas** — la idea sigue siendo vivienda; se amplía el porqué (dimensión fiscal) |
| Entrega 3 (gold asequibilidad) | se conserva; el gold CRECE con columnas fiscales (GF06/CCAA, composición) y de presión demográfica |
| Pipeline INE existente | se reutiliza entero |
| Línea técnica | UNA: GBM+SHAP+conformal (B2–B4) + descriptivos; control sintético como análisis de evento único acotado |
| Riesgo con tutor | **el menor de las tres variantes** — es su proyecto avalado, profundizado |

**Pitch (añadir Variante C al [pitch](pitch_tutor_fiscal.md)):** "C — Vivienda como caso de consecuencias: mantengo el proyecto avalado y le añado la capa fiscal (cuánto/cómo se gasta en vivienda y qué rendimiento obtiene cada país/CCAA) y el amplificador migratorio. Pivote mínimo, pregunta más honda."

## 4. Calendario (mismas 10 semanas, menos riesgo)

```
S1  gate tutor (C como opción preferente) ─ conectores fiscales (gov_10a_exp GF06 ya validado)
S2  gold ampliado: asequibilidad + gasto vivienda + presión demográfica (= Entrega 3 ampliada)
S3  B1 descriptivo ES vs UE vs CCAA
S4–S5  B2 rendimiento ajustado UE-33 ★ ─ checkpoint tutor S5
S6  B3 CCAA benchmarking ★
S7  B4 interacción migración×rendimiento ★ ─ B5 eventos + control sintético Cataluña
S8  app (atlas vivienda: funnel UE + mapa CCAA + ficha España) ─ memoria arranque
S9  borrador completo → tutor ─ defensa
S10 buffer real
```
Recortables sin romper la tesis: B5-sintético, gemelo sanitario de B4, B6.

## 5. Riesgos específicos
| Riesgo | Mitigación |
|---|---|
| B6 leído como afirmación causal | encuadre "ilustración descriptiva" + intervalo + frase literal en métodos; ensayar en banco de preguntas |
| GF06 heterogéneo entre países (agua/alumbrado en L1) | usar L2 (GF0601+GF1006) desde 2001; L1 solo descriptivo largo |
| SILC sin desglose CCAA suficiente | outcome regional = ratio de asequibilidad propio (ya construido) |
| Liquidaciones CCAA pre-2002 | declarar inicio 2002 para la capa fiscal CCAA; el panel de asequibilidad conserva su rango completo |
| Cataluña-sintético con N donante pequeño | placebo tests + presentarlo como análisis exploratorio de evento |

## 6. Capa ML/DL por bloque

**Regla maestra (idéntica a todos los planes): el tamaño muestral EFECTIVO decide la herramienta.** 1.224 obs trimestrales justifican un comparador DL (no un DL primario); 10⁴⁺ documentos BOE justifican un transformer; 17 CCAA justifican funnels, no GNNs. Decirlo en la memoria desactiva la pregunta del tribunal.

| Bloque | Capa | Técnica |
|---|---|---|
| **B1** descriptivo | Detección de anomalías como QA: Isolation Forest / z-robusto sobre cambios interanuales de composición → auto-detecta artefactos tipo superbonus y errores de datos ANTES de modelar. Opcional: clustering de perfiles de gasto en vivienda (construcción vs ayudas al alquiler) — exploratorio a N=33 | no supervisada |
| **B2** rendimiento UE-33 | Núcleo: GBM + SHAP + residual conformal (funnel). Pregunta SHAP: ¿el gasto intensivo en CAPITAL (construir/rehabilitar) predice mejores resultados que el intensivo en transferencias (ayudas)? Umbrales no lineales | supervisada |
| **B3** CCAA | (a) benchmarking conformal a N=17; (b) **el stack de forecasting del TFM original**: SARIMAX/GBM sobre el panel trimestral de asequibilidad (17×~72 ≈ 1.224 obs), con backtesting | supervisada + series |
| **B4** amplificador migratorio | GBM con features de interacción (presión×rendimiento) + **SHAP interaction values** — el test de la hipótesis vive en el término de interacción; GAM como contraste interpretable de la superficie | supervisada |
| **B5** eventos | Control sintético (regresión con pesos aprendidos — adyacente a ML y amable con tribunal) para Cataluña; placebo tests | evento único |
| **B6** escenario | Los intervalos conformales se propagan a la ilustración — la incertidumbre ES el producto | — |

### 6.1 Los tres huecos honestos de deep learning en la variante C
1. **Comparador DL de forecasting sobre el panel trimestral** — N-BEATS/DeepAR como modelo GLOBAL sobre las 17 series CCAA vs SARIMAX/GBM, backtesting riguroso. **Es literalmente el "modelo DL comparativo" que la Entrega 2 avalada ya prometía** — no requiere permiso nuevo. Si el GBM gana, es un hallazgo sobre DL en paneles pequeños; publicable en ambos sentidos.
2. **Extractor BOE de legislación de vivienda** — si B5 crece más allá de los 15–20 hitos curados a mano: fine-tuning de transformer español (MarIA/RoBERTa-BNE) para clasificar + NER todas las disposiciones de vivienda desde 1995 → **índice de intensidad de política** por CCAA-año como feature. Decenas de miles de docs = territorio DL genuino; reutiliza la experiencia Trustpilot del autor.
3. **TabPFN v2** como comparador tabular en B2 — solo con aval explícito del tutor (regla de una línea).

**Además:** la capa **RAG sobre informes BdE/INE** sigue disponible como V2 — el consejo la vetó para las variantes de pivote (regla de una línea), pero en C formaba parte de la arquitectura que el tutor aprobó explícitamente en la Entrega 2, así que sobrevive como capa cualitativa avalada si el calendario lo permite.

**Negativo asentado:** nada de LSTM/TFT como modelo PRIMARIO sobre el panel anual país-año; el comparador DL vive solo en el panel trimestral (donde hay datos) y como comparador, no como titular.

## 7. Qué demuestra esta variante (argumento de cierre para la defensa)
Une las tres preguntas del programa integral en un caso tangible: **cuánto se gasta (B1) → cómo de bien se convierte en resultados (B2–B3) → qué consecuencias tiene no hacerlo bien cuando la demanda aprieta (B4) → y qué hace la política al respecto (B5)** — todo con datos abiertos verificados, un solo método central, y el proyecto que el tutor ya avaló como columna vertebral.
