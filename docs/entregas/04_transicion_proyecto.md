# Entrega 4 (adenda voluntaria) — Transición del proyecto: de la vivienda al programa "Dinero público → Resultados"

*2026-07-18. Documento incremental: las entregas [01](01_ideas_producto.md), [02](02_datos_necesarios.md) y [03](03_modelo_datos.md) se conservan íntegras, sin modificar, como exige el enunciado. Este documento explica la evolución del proyecto desde la idea avalada (índice de asequibilidad de vivienda por CCAA) hacia el programa descrito en [PLAN_MAESTRO.md](../PLAN_MAESTRO.md), y responde punto por punto al [feedback del tutor del 12 de julio](feedback_tutor_2026-07-12.md).*

---

## 1. Respuesta directa al feedback del 12 de julio

| Petición del tutor | Respuesta |
|---|---|
| **"Espero ver el repositorio completo, con la estructura real alineada con lo que documentas"** | Hecho: este repositorio público ES la entrega. Contiene el pipeline completo (conectores + capas raw/processed/gold con manifiesto de vintage), la API, toda la documentación y el proyecto vivienda original íntegro (`_old/`). La estructura real se describe en el [README](../../README.md); las diferencias respecto a lo documentado en la Entrega 3 se explican en §4. |
| **"El índice de asequibilidad es un indicador aproximado; complementarlo con una medida adicional de esfuerzo de compra"** | Aceptado e incorporado al plan ([PLAN_MAESTRO §7](../PLAN_MAESTRO.md)): el ratio IPV/salario se presentará siempre como indicador aproximado de evolución relativa, y se complementa con una **cuota hipotecaria teórica** (precio medio × LTV 80 % a 25 años con Euríbor + diferencial, sobre salario medio CCAA) construible con datos ya extraídos (Euríbor BdE ✅, IPV ✅, salarios ✅) más el precio por m² (MITMA/Registradores, ruta identificada en la Entrega 2). |
| **"Un MVP claramente priorizado antes de extender el proyecto con modelos adicionales o RAG"** | Aceptado: el alcance TFM es un recorte estricto del programa (§5). El núcleo se entrega primero; todo lo demás queda etiquetado como extensión que no bloquea ni compromete el núcleo. La capa RAG/LLM pasa explícitamente a extensión post-núcleo. |

## 2. Por qué se amplía el proyecto

Al construir el pipeline de vivienda apareció una pregunta más general que la contiene: **¿qué obtiene un país a cambio de su gasto público?** La vivienda es una partida más del gasto (COFOG GF06) junto a sanidad, pensiones, educación o intereses de la deuda. Los mismos ingredientes del proyecto avalado —ETL reproducible sobre APIs públicas, índices comparables, forecasting con escenarios e incertidumbre honesta— escalan de 4 tablas del INE a un pool Eurostat + FMI + histórico 1870–2023 sin cambiar de línea tecnológica (Python + pandas, sin infraestructura nueva).

La ampliación no es un cambio de tema sino de zoom: el análisis de vivienda **se conserva como vista propia dentro del programa** (vista C del PLAN_MAESTRO), con su pipeline ya construido y mejorado.

## 3. Qué se conserva del proyecto vivienda (todo)

| Compromiso de las entregas 2–3 | Estado en este repositorio |
|---|---|
| Pipeline INE (IPV, IPC, salarios) + Euríbor BdE | ✅ Reescrito en `connectors/ine.py` con el contrato raw→processed→gold |
| **Bug declarado E3 §7.1** (IPC promediaba 1.120 series ECOICOP en vez de filtrar "Índice general") | ✅ **Corregido**: filtrado por serie exacta; validación de rango en carga |
| **Bug declarado E3 §7.2** (IPV trimestral descargado pero nunca persistido) | ✅ **Corregido**: `storage/gold/gold_ccaa_trimestral.csv` (ratio de asequibilidad Nacional 2024 = 1,26) |
| Índice de asequibilidad CCAA | ✅ Construido sobre la serie trimestral; la vista anual (289 filas, E3 §4.1) se genera en la fase de reescritura |
| Forecasting IPV trimestral con escenarios + comparador DL | ✅ Mantenido como fase F4.1 del plan (SARIMAX/GBM vs N-BEATS/DeepAR, rolling-origin) |
| Corpus RAG (BdE, INE) | Extensión post-núcleo, como pedía el MVP de la E2 y refuerza el feedback |
| Código y documentos originales | ✅ Íntegros en `_old/` (trazabilidad completa; nada se ha borrado) |

**Corrección técnica sobrevenida:** el INE renumeró las tablas del IPV citadas en las entregas 2–3 — la 49300 (anual) y la 76201 (trimestral) ya no existen; las vivas son **80271** y **80270**. Es exactamente el riesgo "cambio de IDs de tabla en la API del INE" declarado en la Entrega 2 §3; la mitigación prevista (cliente parametrizado + snapshots en processed) funcionó y el pipeline actual usa los IDs nuevos.

## 4. Estructura real vs estructura documentada en la Entrega 3

El enunciado permite una estructura propia justificada. La construida mejora la documentada:

| Entrega 3 | Repositorio real | Motivo |
|---|---|---|
| `data/{raw,processed,gold}` | `storage/{raw,processed,gold}` | Mismo patrón de capas; nombre único para evitar colisión con paquetes Python |
| `fetch_data.py` monolítico | paquete `connectors/` (un módulo por fuente, contrato común en `base.py`) | El pool pasó de 4 tablas a ~30 fuentes; cada conector es ejecutable y testeable por separado |
| — | `storage/raw/vintage_manifest.csv` | Evidencia inmutable: fecha y URL de cada descarga (mejora sobre lo prometido) |
| `rag/chroma` | no existe aún | Extensión post-núcleo (coherente con el MVP y con el feedback) |

## 5. Alcance TFM (el recorte, no el programa)

El programa completo (20 RQs, fases F0–F9) NO es el TFM. El TFM entrega tres piezas, todas con datos ya en disco:

1. **Atlas de evolución** (15 figuras: deuda, sanidad, pensiones, vivienda, salarios públicos… siglos XX–XXI) — [PLAN_MAESTRO §4, F2].
2. **Rendimiento ajustado con incertidumbre** (GBM + SHAP + intervalos conformales; nunca una liga) — F3.
3. **Forecasting CCAA con escenarios** (la pieza heredada directamente del proyecto vivienda) — F4.1.

Con calendario de 10 semanas y buffer explícito (PLAN_MAESTRO §4-F0). Las fases F5–F9 (simulador completo, empresas públicas, flujos de ayuda, migración×servicios) quedan como líneas futuras declaradas.

## 6. Validación

Esta transición se somete a la validación del tutor. Si se prefiriera mantener el alcance original (solo vivienda), el proyecto avalado sigue intacto y entregable: su pipeline está construido y mejorado (§3) y el resto del programa se declararía como trabajo exploratorio adicional. La decisión no bloquea el desarrollo: las tres piezas del §5 comparten el mismo núcleo técnico.
