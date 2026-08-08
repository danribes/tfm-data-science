# Fase 3 — Capa empírica ML/DL y biblioteca RAG

**Estado:** propuesta · **Fecha:** 2026-08-08 · **Entrega:** septiembre 2026

La fase 2 dejó un motor estructural honesto cuyo talón de Aquiles está declarado
en su propia Metodología: *las constantes son calibraciones, no estimaciones*.
La fase 3 construye la capa empírica que falta — estimar sobre las series
históricas lo que hoy se importa de la literatura — y añade la biblioteca RAG.
Regla de diseño que hereda todo lo de abajo: **cada número lleva su procedencia
visible** (`estructural` / `estimado` / `IA-redactado` / `libro citado`), y un
método que no bata al baseline se publica igualmente como hallazgo.

---

## 1. Inventario completo de activos (auditoría 2026-08-08)

Nada de esto es hipotético; todo existe hoy en disco.

### Datos (data/gold, congelados en el vintage 2026-07-31)

| Activo | Dimensión | Uso actual | Uso propuesto |
|---|---|---|---|
| `gold_fiscal_historico` | 18 países × 1700–2025 (3.212 obs) | gráfico histórico | panel de estimación + etiquetas de distress |
| `gold_ccaa_trimestral` | 20 CCAA × 77 trimestres (1.540 obs) | vivienda | **el único dataset con masa para DL** |
| `gold_asequibilidad_ccaa` | 18 CCAA × 2008–2024 | esfuerzo | validación de la cadena de vivienda |
| `gold_projections` | 9.504 filas, variantes BSL/HMIGR/… | solo variante base | selector de variantes demográficas en la UI |
| `gold_escenarios_deuda(_mc)` | central + alternativas | motor + abanico | envolvente de validación (ya se usa) |
| `gold_pobreza_infantil` | 4 filas de elasticidades | línea roja | persona 08 (🧒 Infancia) |
| `gold_bienestar_pais` | 309 países-obs con residuales | sin uso en UI | ruta Evidencia (residuales = quién sobre/infra-rinde) |
| `data/live/` | clientes Eurostat + World Bank + OECD, catálogo 19 indicadores | motor genérico | refresco de vintage + panel multi-país del modelo de distress |

### Corpus documental (evo_final_work_data/, FUERA de git)

| Activo | Contenido | Nota crítica |
|---|---|---|
| `econ_pdfs/` (1,4 GB, 44 PDF) | Mankiw (×7 ediciones), Case-Fair, CORE, Banerjee-Duflo, Mises… | **con copyright → jamás al repo público**; también hay libros fuera de tema (DeFi, day-trading) que NO deben entrar al corpus por defecto |
| `econ_pdfs/core_econ/` | **5 libros CORE ya convertidos a Markdown limpio** (`*_FULL.md`) | el mejor punto de partida del RAG: cero extracción de PDF, licencia CC |
| `crack23/` | transcripciones + resúmenes del canal citado por las líneas rojas | colección RAG separada, etiquetada como **opinión**, nunca mezclada con libros de texto |
| `design/` v05–v16 | el linaje de diseño completo | colección RAG "método" junto a Metodología/Cómo funciona |

### Trabajo previo reutilizable (repo antiguo + archive/)

| Activo | Qué demostró | Qué se rescata |
|---|---|---|
| `analysis/dl_global_t1.py` | transfer learning: DL entrenado en **1.760 series regionales extranjeras** (FHFA/Zillow/UK), España jamás en el entrenamiento, corte temporal ≤2019Q3 | el protocolo entero — es la única forma defendible de DL con 77 trimestres españoles |
| `analysis/foundation_t1.py` | Chronos-Bolt (modelo fundacional de series) zero-shot contra drift | benchmark de foundation model, caveat de corpus no auditable ya redactado |
| `analysis/expansion_dl.py` | MLP vs LightGBM vs OLS bajo LOOCV, diseño pre-declarado | la parrilla de candidatos y la disciplina "declarar antes de mirar" |
| `analysis/backtest_50y.py` | error real de proyecciones de continuidad a 50 años (1925→1975→2025) | la vara de medir de la humildad — va a la ruta Evidencia |
| `connectors/train_projection.py` | elasticidades panel within (pensiones, sanidad) UE 1995–2023 | re-estimar y exponer como procedencia de constantes |
| `archive/mvp-app-v1/models/fiscal_stress_model.joblib` + METRICS.md | clasificador de distress soberano (GradientBoosting, etiquetas Reinhart-Rogoff-Trebesch, LOCO-CV) | **la idea sí, el artefacto no**: el entrenamiento 2003–2015 dejó ~1 etiqueta positiva y AUC = None. Re-entrenar 1975–2015 con el panel completo |
| `app/rag_assistant.py` (viejo) | RAG léxico TF-IDF + cliente multi-proveedor OpenAI-compatible (Gemini/GLM/Kimi/MiMo) con fallback | el cliente multi-proveedor se porta tal cual; la recuperación se sube a híbrida |

### Herramientas IA disponibles

Claves en el entorno: Gemini, GLM, Kimi, MiMo, Qwen, OpenAI, Perplexity,
Anthropic (pendiente de crédito). GPU local RTX 3060 → embeddings y reranking
**locales y gratis** (sentence-transformers), sin coste por consulta ni
dependencia de red para la recuperación.

---

## 2. Dónde entra ML/DL — y dónde deliberadamente no

El principio: la potencia estadística viene de la dimensión de panel (18 países,
20 CCAA, 1.760 series extranjeras), nunca de las ~65 observaciones anuales
españolas modernas. Cada candidato compite contra un baseline tonto (drift /
mediana) bajo un protocolo pre-declarado, y perder contra el baseline es un
resultado publicable, no un fracaso.

### 2a. Validación empírica de las constantes del motor (econometría + ML)

- **Proyecciones locales de panel (Jordà)** sobre el panel fiscal 18 países
  (ventana moderna ≥1960, rupturas: euro 1999, 2008, COVID): IRFs con bandas de
  confianza para las cuatro transmisiones que el motor afirma (tipo→deuda,
  saldo→PIB, tipo→vivienda, paro→pobreza).
- **Salida UI:** ruta **Evidencia** — por constante: valor calibrado vs
  estimado, IC 90 %, muestra, gráfico IRF. La frase "un revisor puede
  discutirlas" se convierte en "aquí está el contraste".
- **Identificación** (la pregunta del tribunal): ordenación recursiva como
  base + robustez con instrumentos externos; sección propia en la memoria.

### 2b. Cadena de vivienda (el único sitio con masa para DL de verdad)

Portar el protocolo T1 completo del repo viejo, que ya está diseñado para esto:

- Candidatos: drift (baseline) · LightGBM con features de panel ·
  **DL por transferencia** (entrenado solo en las 1.760 series extranjeras,
  España fuera del entrenamiento) · **Chronos-Bolt zero-shot**.
- Protocolo: orígenes 2019Q4–2023Q4, horizontes h=1–8, test 2024+ intocable,
  criterio pre-declarado: batir al drift en ≥12/17 CCAA a h≤4.
- **Salida UI:** ruta **Predicción** — tabla de backtest honesta (quién bate a
  quién, por CCAA y horizonte) + proyección del ganador con abanico empírico.

### 2c. Alerta temprana de distress soberano (re-entrenamiento)

- Etiquetas Reinhart-Rogoff-Trebesch ampliadas a 1975–2015 (el intento
  archivado se quedó con una sola etiqueta positiva — inservible y así se
  documenta), features macro del panel + World Bank, LightGBM con LOCO-CV.
- **Salida UI:** indicador de probabilidad de distress junto al semáforo de
  líneas rojas — el complemento probabilístico del umbral del 7 %: el bono
  dice lo que exige el mercado hoy; el clasificador, a qué se parecieron
  históricamente los países que acabaron mal.

### 2d. Transmisiones dependientes del estado (el hallazgo diferencial)

- Proyecciones locales potenciadas con gradient boosting + SHAP: ¿el efecto de
  +100 pb es el mismo con deuda al 60 % que al 120 %? El motor asume que sí
  (E_R fijo); el contraste empírico probablemente diga que no.
- **Salida UI:** el ContributionChart gana un gemelo empírico — atribución
  estructural (motor re-corrido) al lado de atribución SHAP (histórica), con
  las discrepancias señaladas, no escondidas.

### 2e. Regímenes y anomalías (barato y vistoso)

- HMM / cambio de régimen sobre las series históricas (crisis vs normal) →
  colorear el fondo del espagueti y del histórico por régimen detectado.

### Donde NO va DL, dicho explícitamente

- Nada de LSTM/transformer entrenado sobre las ~65 obs anuales españolas: se
  memorizaría la muestra. La memoria lo dice con esta franqueza — es un punto
  a favor, no una carencia.

---

## 3. Biblioteca RAG (la construye el autor; este es el plano)

### Corpus, por colecciones separadas y etiquetadas

1. **`libros`** — los 5 CORE ya en Markdown (`core_econ/*_FULL.md`) primero;
   después el subconjunto macro/micro curado de los 44 PDF (Mankiw 9ª ed. — no
   las 7 ediciones duplicadas —, Case-Fair, Banerjee-Duflo, Mises). Excluidos
   por defecto: day-trading, DeFi, blockchain (fuera de tema; diluyen la
   recuperación).
2. **`metodo`** — Metodología, Cómo funciona, specs v12–v16: el chat puede
   responder "¿por qué el 7 %?" con la procedencia de la propia app.
3. **`crack23`** — resúmenes del canal, siempre etiquetados como opinión.

### Pipeline

- Troceado consciente de encabezados (~800 tokens, solape 120), metadatos
  libro/capítulo/sección.
- **Embeddings locales** en la 3060 (`BAAI/bge-m3` o `multilingual-e5-large`
  — el corpus es bilingüe ES/EN) → ChromaDB persistente.
- Recuperación **híbrida**: BM25 + denso, fusión RRF, reranker local opcional
  (`bge-reranker-v2-m3`). El RAG viejo era TF-IDF puro; esta es la subida.
- Generación: portar el cliente multi-proveedor del `rag_assistant.py` viejo
  (OpenAI-compatible con fallback Gemini→GLM→Kimi; Anthropic cuando haya
  crédito). Clave siempre en el servidor.
- **Cita obligatoria**: cada afirmación con libro + sección; sin pasajes por
  encima del umbral → "el corpus no cubre esto", nunca inventar.

### La integración que lo diferencia de "un chat más"

El chat recibe **también el bloque de hechos del escenario actual** (el mismo
`facts` de `/explain`). Pregunta: "¿qué dice Mankiw del escenario que tengo
puesto?" → respuesta anclada en (a) pasajes citados y (b) los números del motor
en pantalla. Libro de texto + simulador en la misma frase — eso es lo que un
tribunal no ha visto antes.

### Evaluación y guardarraíles (no opcionales)

- 30–50 preguntas doradas con respuesta y fuente esperadas; métricas de
  recuperación (hit@k) y de fidelidad (¿la cita sostiene la frase?) en CI.
- El chat hereda `computed_not_advice`; rechaza consejo financiero.
- Los PDFs y el ChromaDB viven fuera del repo público (copyright); el repo
  lleva solo el código del pipeline y el manifiesto de corpus con hashes.

---

## 4. Rutas nuevas de la app

| Ruta | Contenido |
|---|---|
| **/evidencia** | calibrado vs estimado por constante, IRFs con IC, backtest de 50 años, residuales de bienestar |
| **/prediccion** | tabla de backtest T1 (drift vs LightGBM vs DL-transfer vs Chronos), abanico empírico vs estructural, gauge de distress |
| **/biblioteca** | chat RAG con citas, selector de colecciones, contexto del escenario activo |
| Inicio/Laboratorio | espagueti coloreado por régimen; SHAP junto al ContributionChart; selector de variante demográfica |

## 5. Fases (septiembre = ~6 semanas)

1. **S1** — panel de estimación + proyecciones locales + ruta Evidencia.
2. **S2** — puerto del protocolo T1 de vivienda (4 candidatos) + ruta Predicción.
3. **S3** — distress re-entrenado + gauge; LP potenciadas + SHAP gemelo.
4. **S4** — corpus RAG (CORE primero) + evaluación dorada + chat con citas.
5. **S5** — integración escenario↔RAG; regímenes; variantes demográficas;
   crédito Anthropic y narración LLM viva.
6. **S6** — endurecimiento: despliegue público, LICENSE, personas 04–12,
   material de memoria (cada capa ya genera sus tablas y figuras).

## 6. Riesgos con nombre

- **Identificación causal** — la pregunta más dura del tribunal; respuesta
  preparada en Evidencia y memoria.
- **Fugas temporales** — todo split respeta el tiempo; el protocolo T1 ya lo
  resuelve y se hereda tal cual.
- **Copyright** — libros y vectores jamás en el repo público.
- **Sobreventa de DL** — el criterio "batir al drift o contarlo" se mantiene
  aunque duela.
