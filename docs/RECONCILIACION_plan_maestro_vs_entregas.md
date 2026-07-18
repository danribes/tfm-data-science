# Reconciliación — PLAN_MAESTRO vs entregas presentadas vs feedback del tutor

*2026-07-18. Cruza tres fuentes: (1) [PLAN_MAESTRO.md](PLAN_MAESTRO.md) v1, (2) las entregas presentadas en Classroom ([01](entregas/01_ideas_producto.md) · [02](entregas/02_datos_necesarios.md) · [03](entregas/03_modelo_datos.md)), (3) el [feedback del tutor del 12-jul](entregas/feedback_tutor_2026-07-12.md) y los enunciados oficiales (`exercises/Entrega_2_*.pdf`, `Entrega_3_*.pdf`).*

---

## 1. Requisitos de los enunciados (el "contrato" que cita el tutor)

| Requisito (enunciado) | Estado en el repo | Acción |
|---|---|---|
| Repositorio GitHub, **público** o compartido con `juliovalerog` con permisos de lectura completos | ❌ Solo local hasta hoy; remoto **privado** creado 2026-07-18 (pendiente decisión: público vs invitar a `juliovalerog`) | Decidir visibilidad ANTES de la próxima entrega |
| El repo contiene entregas + código + documentación + desarrollo completo; es el **entregable final** | ⚠️ Parcial: entregas ✅, ETL/tests ✅, pero el proyecto raíz es el plan fiscal (no avalado aún) y el proyecto vivienda original vive en `_old/` | Ver §3.1 |
| `docs/entregas/01..03*.md` presentes, entrega incremental, nunca borrar anteriores | ✅ Los tres ficheros + feedback archivado | — |
| Estructura de capas tipo `data/{raw,processed,gold}` (u otra justificada) | ⚠️ Existe pero se llama `storage/{raw,processed,gold}` y la Entrega 3 documenta `data/` | Renombrar o re-documentar (§3.3) |

## 2. Dónde PLAN_MAESTRO ya está alineado

- **Gate del tutor como fase F0.1**: el plan no asume el pivote fiscal — exige aval ESCRITO antes de reescribir entregas, con la vista C (vivienda) recomendada y el "fallback vivienda intacto". Coherente con que el feedback del tutor se refiere SOLO al proyecto vivienda.
- **"Alcance radicalmente reducido"** (feedback Entrega 1) reconocido como riesgo nº 1 en §6.1 del plan ("es un PROGRAMA, no un TFM… la condición es el recorte").
- **MVP por fases**: la Entrega 2 ya faseaba núcleo/extensión y el tutor lo elevó a exigencia; el plan lo respeta (calendario F0, RAG/DL como comparadores u opcionales).
- **Los 2 bugs declarados en la Entrega 3 §7.1–7.2 están corregidos** en el pipeline nuevo: IPC filtrado por serie exacta "Índice general. Índice." (no media de grupos) y el IPV trimestral ahora sí se persiste (`gold_ccaa_trimestral`, ratio Nacional 2024 = 1,26). Argumento de credibilidad ante el tutor: los problemas se anticiparon, se detectaron y se arreglaron.
- **Forecasting CCAA con comparador DL** (C1-Modo 1, N-BEATS/DeepAR) = exactamente el núcleo prometido en la Entrega 2.

## 3. Divergencias que hay que resolver (por gravedad)

### 3.1 Identidad del proyecto (LA gorda)
Las entregas comprometen UNA idea principal: **índice de asequibilidad de vivienda por CCAA** ("a partir de esta entrega deberéis trabajar sobre una única idea principal, que será la base de vuestro proyecto final"). El repo raíz hoy es el atlas fiscal (PLAN_MAESTRO), con el proyecto vivienda original relegado a `_old/`. Si el tutor abre el repo tal cual, ve un proyecto distinto del avalado → percepción de incumplimiento del contrato, justo su queja central.
**Acción:** antes de compartir el repo con el tutor, o (a) se obtiene el aval del pivote (F0.1) y se reescriben las entregas (F0.2), o (b) se restaura el proyecto vivienda como raíz visible y el atlas fiscal se presenta como rama/carpeta de exploración. Ninguna entrega nueva debe salir con esta ambigüedad abierta.

### 3.2 IDs de tablas INE muertos en las entregas
Entregas 2 y 3 citan IPV tablas **49300 (anual) y 76201 (trimestral)** — el INE las renumeró y hoy dan 404; las vivas son **80271 (anual) y 80270 (trimestral)** (verificado en el barrido de esquemas; el pipeline nuevo ya usa 80270). Las verificaciones "en vivo 2026-07-07" de la Entrega 2 quedaron obsoletas en días — exactamente el riesgo "cambio de IDs de tabla" que la propia entrega declaró.
**Acción:** en la reescritura (F0.2), actualizar IDs y añadir nota: "el riesgo declarado se materializó; la mitigación (snapshots + cliente parametrizado) funcionó". Convierte un fallo en evidencia de madurez.

### 3.3 Estructura documentada ≠ estructura real
| Entrega 3 documenta | Repo real |
|---|---|
| `data/{raw,processed,gold}` | `storage/{raw,processed,gold}` |
| `fetch_data.py` + `src/ccaa_map.py` | paquete `connectors/` + `tests/` |
| `rag/chroma` (ChromaDB) | no existe aún (extensión, correcto por MVP) |
| gold: `gold_asequibilidad_ccaa.csv`, `gold_panel_trimestral.csv`, `gold_corpus_manifest.csv` | gold: `gold_panel_anual`, `gold_panel_wide`, `gold_ccaa_trimestral`, `gold_century_fiscal` |
"Formato de entrega = contrato": o el repo converge a lo documentado o la documentación se actualiza a lo construido (el enunciado permite estructura propia justificada). Lo indefendible es el desajuste silencioso.
**Acción (mínimo coste):** en F0.2 re-documentar `storage/` y `connectors/` (mejores que lo prometido: tests + raw inmutable) y construir el `gold_asequibilidad_ccaa` anual que falta (289 filas, construible hoy según la propia Entrega 3 §9).

### 3.4 Métrica de asequibilidad — petición del tutor sin recoger aún en el plan
El tutor (dos veces): IPV÷salario = indicador aproximado; complementar con medida de **esfuerzo real de compra** (€/m², renta disponible, entrada, cuota hipotecaria). La Entrega 2 ya tenía los ganchos (BdE "esfuerzo hipotecario (ratio cuota/renta)" como alternativa; MITMA €/m² de suelo como driver; Euríbor ya extraído). PLAN_MAESTRO no lo incorpora explícitamente.
**Acción:** añadir al plan (F1.3 / vista C) un indicador complementario: cuota hipotecaria teórica (precio medio × LTV 80% × Euríbor+diferencial, a 25 años) / salario medio CCAA — calculable con datos ya extraídos o de ruta conocida (BdE, MITMA, Registradores precio/m²). Presentar SIEMPRE el ratio como aproximado, como pide el tutor.

### 3.5 Ficheros que no deben viajar al remoto
`exercises/` contiene enunciados y trabajos de OTROS módulos (estadística, Fabric, DL) — no es desarrollo de este proyecto y no debe publicarse en el repo entregable → añadido a `.gitignore` (se conserva en local).

## 4. Secuencia recomendada (sin cambiar el calendario F0)

1. **Hoy:** remoto privado creado y materiales subidos (este doc, feedback, deck, scripts). `exercises/` fuera del control de versiones.
2. **Antes de la reunión F0.1.2:** decidir identidad (§3.1). Llevar al tutor: bugs corregidos + gold vivienda ya construido + medida complementaria de esfuerzo (§3.4) como respuesta directa a su feedback.
3. **F0.2 (reescritura):** actualizar IDs INE (§3.2), re-documentar estructura real (§3.3), construir `gold_asequibilidad_ccaa` anual.
4. **Al compartir con el tutor:** hacer público el repo o invitar a `juliovalerog` (requisito del enunciado) — decisión del autor, no automatizable.
