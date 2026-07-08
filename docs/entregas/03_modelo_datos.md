# Entrega 3 — Diseño del modelo de datos y capa gold

*Entrega incremental: se conservan [01_ideas_producto.md](01_ideas_producto.md) y [02_datos_necesarios.md](02_datos_necesarios.md). Las fuentes citadas fueron verificadas en vivo el 2026-07-07 (ver [análisis de opciones](../analisis_opciones_tfm.md)).*

---

## 1. Resumen de la idea y datos del proyecto

**Problema:** el precio de la vivienda en España crece muy por encima de los salarios, con divergencias marcadas entre comunidades autónomas, y no existe un indicador integrado, actualizable y de acceso libre que combine precio, salarios e inflación regional en una única medida de asequibilidad.

**Solución:** el proyecto construye un **índice de asequibilidad de vivienda por comunidad autónoma** y, sobre él, modelos de **forecasting del IPV trimestral con escenarios** y una capa **RAG+LLM** que fundamenta las conclusiones en documentos oficiales. Cada fuente aporta un tipo de información distinto:

| Fuente | Qué aporta |
|---|---|
| INE — IPV (tablas 49300 anual, 76201 trimestral) | Variable objetivo: evolución del precio de la vivienda por CCAA y tipo (general/nueva/segunda mano) |
| INE — EES salarios (28191) | Denominador del índice de asequibilidad (capacidad de compra) |
| INE — IPC por CCAA (76136) | Deflactor regional para pasar de índices nominales a reales |
| Banco de España — Euríbor 12m | Driver de demanda (coste hipotecario), exógena del forecasting y palanca de escenarios |
| MITMA — precio suelo urbano, índice de costes de construcción | Drivers de oferta y costes (V2 del modelo) |
| Registradores — % compraventas extranjeros | Driver de demanda externa por CCAA (V2) |
| Corpus documental (BdE, INE) | Drivers estructurales **sin serie temporal**: suelo, regulación, fiscalidad — entran por la vía RAG, no por la tabular |

## 2. Tecnología y formato de almacenamiento

**Elección: ficheros CSV organizados en capas de carpetas, más un almacén vectorial local (ChromaDB) para el corpus documental.**

Justificación:
- **Volumen:** ~3.300 filas procesadas + panel de ~1.300 filas. Cualquier base de datos relacional sería complejidad sin retorno; pandas lee CSV de este tamaño en milisegundos.
- **Reproducibilidad y trazabilidad:** CSV versionable en Git, diffs legibles, sin servidor que mantener. El repo es el entregable final del curso — todo su contenido debe poder inspeccionarse sin infraestructura.
- **Excepciones conscientes:** (a) los datos **raw** conservan su formato de origen (JSON del INE, CSV del BdE, XLS del MITMA, PDF de Registradores) porque la capa raw es evidencia inmutable de lo descargado; (b) el **corpus RAG** requiere un índice vectorial — se usa ChromaDB persistido en disco (carpeta local, sin servidor), la opción mínima que cubre la necesidad.
- **Descartado:** SQLite/PostgreSQL (sin ventaja a este volumen), Parquet (beneficio marginal frente a CSV con ~5.000 filas; se reconsideraría solo si el panel creciera a granularidad provincial).

## 3. Estructura de capas de datos

```
data/
├── raw/          # descargas intactas, formato de origen, evidencia inmutable
│   ├── ine/          ipv_ccaa_anual.json, ipv_ccaa_trimestral.json, ipc_ccaa.json, salario_ccaa.json
│   ├── bde/          ti_1_7.csv                      (Euríbor, CSV BdE)
│   ├── mitma/        suelo_36400500.xls, icsc_08010000.xls
│   ├── registradores/ eri_Xt_YYYY.pdf | .xlsx        (vía datos.gob.es si es viable)
│   └── corpus/       PDFs fuente del RAG (BdE, notas de prensa INE) — evidencia raw como cualquier otra
├── processed/    # una tabla tidy por fuente: limpieza, tipado y filtrado, sin cruces
│   ├── ipv_ccaa.csv, ipv_ccaa_trimestral.csv, ipc_ccaa.csv, salario_ccaa.csv
│   ├── euribor_mensual.csv, suelo_ccaa.csv, icsc_mensual.csv, extranjeros_ccaa.csv
└── gold/         # contrato de datos: datasets finales que consumen las fases posteriores
    ├── gold_asequibilidad_ccaa.csv
    ├── gold_panel_trimestral.csv
    └── gold_corpus_manifest.csv

rag/
└── chroma/       # índice vectorial del corpus — artefacto DERIVADO, regenerable desde data/raw/corpus/
```

Regla de paso entre capas: **raw** nunca se edita; **processed** limpia cada fuente por separado (una fuente = una tabla tidy); **gold** es el único sitio donde se cruzan fuentes. Análisis, modelos, escenarios y dashboard leen exclusivamente de `gold/` — si algo no está en gold, no existe para las fases posteriores.

## 4. Definición de la capa gold (contrato de datos)

### 4.1 `gold_asequibilidad_ccaa.csv`

- **Descripción funcional:** índice anual de asequibilidad — el dataset del análisis descriptivo y del dashboard.
- **Granularidad:** una fila = una CCAA en un año.
- **Volumen esperado:** 17 CCAA × 17 años (2008–2024) ≈ **289 filas**.
- **Clave primaria:** (`ccaa`, `anio`).

| Campo | Tipo | Descripción |
|---|---|---|
| `ccaa` | str (canónico) | Comunidad autónoma, nombre normalizado |
| `anio` | int | Año |
| `ipv_indice` | float | IPV general, base 2015=100 |
| `ipv_nueva`, `ipv_segunda` | float | IPV por tipo de vivienda (NaN en series no publicadas) |
| `salario_medio` | float | Salario bruto anual medio (€) |
| `salario_idx` | float | Salario indexado, base 2015=100 |
| `ipc_medio` | float | IPC medio anual, base común |
| `ratio_asequibilidad` | float | **Variable objetivo:** `ipv_indice / salario_idx` |
| `ratio_real` | float | Ratio deflactado por IPC |

- **Consumidor posterior:** EDA, heatmap CCAA×año, ranking regional, informe final.

### 4.2 `gold_panel_trimestral.csv`

- **Descripción funcional:** panel de modelado — el dataset de entrenamiento del forecasting y del motor de escenarios. **Es el dataset central del proyecto.**
- **Granularidad:** una fila = una CCAA en un trimestre.
- **Volumen esperado:** 17 CCAA × 72 trimestres (2008T1–2025T4) ≈ **1.224 filas**. El año 2007 del IPV se descarta del panel: los salarios EES empiezan en 2008 y el contrato exige el campo salarial en todas las filas — perder 4 trimestres es preferible a un contrato con excepciones.
- **Clave primaria:** (`ccaa`, `periodo`).

| Campo | Tipo | Descripción |
|---|---|---|
| `ccaa` | str (canónico) | Comunidad autónoma |
| `periodo` | str `YYYY-Qn` | Trimestre |
| `ipv_trimestral` | float | **Variable objetivo del forecasting** (base 2015=100) |
| `ipv_var_interanual` | float | Derivada: variación % interanual |
| `euribor_12m` | float | Media trimestral del Euríbor 12m (driver nacional, repetido por CCAA) |
| `ipc_trimestral` | float | IPC medio del trimestre por CCAA |
| `salario_anual_interp` | float | Salario anual asignado al trimestre (interpolación lineal; flag en `salario_flag`) |
| `salario_flag` | str | `observado` / `interpolado` / `provisional` (último año) |
| `precio_suelo` | float | €/m² suelo urbano, agregado provincial→CCAA (V2; NaN hasta integrarse) |
| `icsc` | float | Índice de costes de construcción, nacional (V2) |
| `pct_extranjeros` | float | % compraventas por extranjeros (V2) |

- **Consumidor posterior:** modelos SARIMAX / gradient boosting / DL comparativo; motor de escenarios (el usuario fija trayectorias de `euribor_12m`, `ipc_trimestral`, `salario_anual_interp` y el modelo proyecta `ipv_trimestral`).

### 4.3 `gold_corpus_manifest.csv`

- **Descripción funcional:** inventario del corpus documental indexado en el RAG — hace auditable qué sabe la capa LLM y de dónde.
- **Granularidad:** una fila = un documento.
- **Volumen esperado:** **20–40 filas** (creciente: BdE publica semestralmente, INE trimestralmente).
- **Clave primaria:** `doc_id`.

| Campo | Tipo | Descripción |
|---|---|---|
| `doc_id` | str | Identificador (p. ej. `bde_do2433`) |
| `titulo` | str | Título del documento |
| `fuente` | str | `BdE` / `INE` |
| `fecha_pub` | date | Fecha de publicación |
| `url` | str | URL de descarga verificada |
| `tipo` | str | informe / nota de prensa / documento ocasional |
| `n_chunks` | int | Fragmentos indexados en ChromaDB |
| `sha256` | str | Hash del PDF (integridad y deduplicación) |

- **Consumidor posterior:** capa RAG (recuperación con cita `doc_id` + página); QA del corpus.

### Resumen de la capa gold

| Dataset gold | Granularidad | Campos clave | Uso posterior |
|---|---|---|---|
| `gold_asequibilidad_ccaa.csv` | 1 fila por CCAA × año | ccaa, anio, ipv_indice, salario_idx, **ratio_asequibilidad** | EDA, dashboard, informe |
| `gold_panel_trimestral.csv` | 1 fila por CCAA × trimestre | ccaa, periodo, **ipv_trimestral**, euribor_12m, ipc, salario | Forecasting + escenarios |
| `gold_corpus_manifest.csv` | 1 fila por documento | doc_id, fuente, fecha_pub, url | RAG (conclusiones LLM con citas) |

## 5. Relaciones entre datos

```
gold_asequibilidad_ccaa (ccaa, anio)  1 ─── N  gold_panel_trimestral (ccaa, periodo)
      [un año contiene 4 trimestres de la misma CCAA; válida en la intersección de
       rangos (2008–2024) — los trimestres de 2025 aún no tienen fila anual madre]

euribor trimestral (nacional, trimestre)       1 ─── N  gold_panel_trimestral
      [agregado previo mes→trimestre; el valor nacional se repite en las 17 CCAA]

processed/salario_ccaa (ccaa, anio)            1 ─── N  gold_panel_trimestral
      [un salario anual se reparte en 4 trimestres, interpolado y marcado]

gold_corpus_manifest (doc_id)                  1 ─── N  rag/chroma (chunks)
```

- **Clave de unión maestra:** `ccaa` normalizada mediante una tabla de mapeo canónico (los nombres difieren entre fuentes: "Comunitat Valenciana" en INE vs "C. Valenciana" en Registradores vs "Valencia" en MITMA; tildes y artículos inconsistentes).
- **Cardinalidades:** todas las uniones tabulares son 1:N por diseño (agregados hacia el panel); no hay relaciones N:M.
- **Cruces necesarios:** agregación temporal en dos pasos para el Euríbor (diario→mensual en processed; mensual→media trimestral al construir gold), mes→trimestre para IPC e ICSC, desagregación temporal año→trimestre para salarios (con flag), y agregación geográfica provincia→CCAA para suelo urbano (ponderando por población o media simple — decisión documentada en §8). Las uniones del panel se hacen siempre contra los agregados trimestrales, nunca contra las tablas de frecuencia fina — así todas las relaciones efectivas son 1:N.
- **Problemas esperables al combinar:** ver §7 (desfases de calendario entre fuentes, cobertura Ceuta/Melilla, bases de índice distintas).
- **Relación tabular↔documental:** deliberadamente **no hay join** entre el panel y el corpus — son contratos separados que solo se encuentran en la capa LLM (el modelo aporta números, el RAG aporta contexto citado). Esta separación es una decisión de diseño, no una carencia.

## 6. Diccionario de datos inicial

Campos principales de las tablas gold, con su fuente y obligatoriedad:

| Campo | Descripción | Tipo | Fuente | Obligatorio | Observaciones |
|---|---|---|---|---|---|
| `ccaa` | CCAA, nombre canónico | str | mapeo propio | Sí | 17 valores; Ceuta/Melilla excluidas (§7) |
| `anio` | Año natural | int | — | Sí | 2007–2025 según tabla |
| `periodo` | Trimestre `YYYY-Qn` | str | — | Sí | Ordenable lexicográficamente |
| `ipv_indice` / `ipv_trimestral` | Índice de precios de vivienda | float | INE 49300/76201 | Sí | Base 2015=100; "Secreto" → NaN |
| `salario_medio` | Salario bruto anual medio | float | INE 28191 | Sí | Solo "Ambos sexos"+"Media"; llega a 2024 |
| `ipc_medio` / `ipc_trimestral` | IPC índice general | float | INE 76136 | Sí | **Solo series "Índice general"** — filtrado por código de serie, no por media de grupos (§7) |
| `euribor_12m` | Euríbor a 12 meses | float | BdE ti_1_7 | Sí (panel) | Serie desde 1999; columnas pre-1999 del CSV se descartan |
| `precio_suelo` | Precio suelo urbano €/m² | float | MITMA 36400500 | No (V2) | Trimestral 2004+; ruido en provincias pequeñas |
| `icsc` | Índice costes construcción | float | MITMA sección 08 | No (V2) | Nacional, mensual, base 2021=100 |
| `pct_extranjeros` | % compraventas extranjeros | float | Registradores ERI | No (V2) | Extracción PDF o XLSX datos.gob.es |
| `ratio_asequibilidad` | IPV / salario indexado | float | derivado | Sí | Métrica central del proyecto |
| `ratio_real` | Ratio deflactado por IPC | float | derivado | Sí | Aísla el efecto inflación |
| `salario_idx` | Salario indexado base 2015=100 | float | derivado | Sí | Denominador del ratio |
| `ipv_var_interanual` | Variación % interanual del IPV | float | derivado | Sí (panel) | Feature de modelado; NaN en el primer año |
| `salario_flag` | Origen del valor salarial | str | derivado | Sí (panel) | observado / interpolado / provisional |

## 7. Problemas de calidad esperados (caso concreto)

Problemas **ya observados** en el pipeline actual o verificados en las fuentes — no lista genérica:

1. **Bug real detectado en el IPC procesado:** el parser actual promedia todas las series de la tabla 76136 (1.120 series: 56 rúbricas ECOICOP × 20 territorios) en lugar de filtrar las 20 de "Índice general", produciendo valores de 15–26 donde el índice real es ~70–120. Corrección diseñada en §8. Lección incorporada: validar rangos de valores por columna en la carga.
2. **Serie trimestral descargada pero nunca guardada:** `fetch_data.py` parsea la tabla 76201 y no la persiste; además deja `nombre_serie` sin separar en columnas ccaa/tipo. El panel gold depende de arreglarlo.
3. **Desfase de calendario entre fuentes:** salarios hasta 2024 (retraso EES ~1,5 años), IPV hasta 2025, IPC con meses de 2026 parciales. El gold anual solo incorpora años con salario observado (de ahí su tope en 2024); en el panel trimestral el último año entra con `salario_flag = provisional`.
4. **Año 2026 parcial en IPC:** promediar un año incompleto sesga la media anual — los años incompletos se excluyen del agregado anual.
5. **Cobertura territorial desigual:** Ceuta y Melilla sin salarios EES y sin desagregación nueva/segunda mano del IPV → el proyecto se restringe a las 17 CCAA (decisión, no accidente).
6. **Valores "Secreto" y nulos del INE** en celdas de baja muestra → NaN explícito, nunca cero.
7. **Nombres de CCAA inconsistentes entre las 4 fuentes** (tildes, artículos, abreviaturas) → tabla de mapeo canónico obligatoria; cualquier fila que no cruce se reporta, no se descarta en silencio.
8. **Bases de índice distintas:** IPV e IPC base 2015, ICSC base 2021, salarios en euros → renormalización a base común 2015=100 documentada.
9. **XLS legados del MITMA:** formato ancho (un bloque de columnas por año), parser `xlrd`, riesgo de cambio de maquetación entre ediciones → test de estructura en la carga.
10. **Registradores tras WAF y en PDF:** la descarga necesita User-Agent de navegador y la serie histórica exige extracción de tablas de PDF → alternativa machine-readable (datos.gob.es XLSX) por confirmar; si falla, driver V2 descartable sin impacto en el núcleo.
11. **Ruido en suelo urbano provincial** (pocas transacciones notariales en provincias pequeñas) → agregación a CCAA y suavizado; se usa como driver, no como objetivo.
12. **Descarga IPC sobredimensionada** (55,9 MB para usar 20 series) → filtrado en origen con parámetros de la API donde sea posible.

## 8. Decisiones de limpieza y transformación previstas

Hipótesis iniciales (revisables, pero definidas):

- **Nulos:** "Secreto"/None del INE → NaN; nunca imputación silenciosa. NaN en drivers V2 aceptable (los modelos núcleo no los usan).
- **Duplicados:** verificación de unicidad de PK en cada dataset gold como test automático de la carga; duplicado = error de pipeline, no dato.
- **Filtrado IPC (corrección del bug):** seleccionar series por su código/nombre exacto "Índice general" por territorio — nunca `groupby().mean()` sobre grupos ECOICOP.
- **Normalización:** nombres CCAA vía tabla canónica única (`src/ccaa_map.py`); fechas a `anio`/`periodo` ordenables; todos los índices re-basados a 2015=100; salarios además en euros corrientes.
- **Agregación temporal:** Euríbor diario → media trimestral; IPC/ICSC mensual → media trimestral; años incompletos excluidos de medias anuales.
- **Desagregación salarial:** anual → trimestral por interpolación lineal, con `salario_flag` que preserva qué es observado y qué derivado; el último año se marca `provisional`.
- **Variables derivadas:** `ratio_asequibilidad`, `ratio_real`, `ipv_var_interanual`, `salario_idx`.
- **Descartes justificados:** 1.100 series ECOICOP no generales del IPC; columnas pre-1999 del CSV del Euríbor (tipos interbancarios legados); provincias (se agregan a CCAA); Ceuta y Melilla.
- **Criterios de validez** (tests de carga): rangos plausibles (IPC 60–130, IPV 40–250 — el nacional 2025 ya marca 179,9 y las CCAA tensionadas superarán 200, Euríbor −1–6), malla completa 17 CCAA × periodos en gold, índices ≈100 en 2015, PK únicas. Un dataset que no pasa los tests no se promociona a gold.
- **Corpus RAG:** solo PDFs con URL verificada y hash registrado en el manifest; troceado por secciones con metadatos (doc_id, página) para que cada respuesta del LLM pueda citar documento y página.

## 9. Riesgos del modelo de datos

- **Parte más clara:** el flujo INE → processed → gold anual. Pipeline ya operativo, fuentes dobles-verificadas, volumen trivial. `gold_asequibilidad_ccaa` es construible hoy.
- **Parte con más incertidumbre:** la fusión del panel trimestral — cuatro frecuencias (día/mes/trimestre/año) y tres geografías (nacional/provincial/CCAA) convergiendo en una PK. Mitigación: los drivers entran de uno en uno, cada unión con sus tests; el panel mínimo (IPV + Euríbor + IPC) ya soporta el forecasting.
- **Fuente más problemática:** Registradores (WAF + extracción PDF, redistribución XLSX por confirmar). Plan: intentar datos.gob.es primero; si no, extracción PDF de los 8 últimos trimestres; si tampoco, descartar el driver — es V2 y su ausencia no toca el contrato gold núcleo.
- **¿Qué ocurriría si no pudiera construirse la capa gold tal como está definida?** El diseño degrada por columnas, no por datasets: las fases posteriores seguirían consumiendo los mismos tres ficheros con menos columnas pobladas (panel mínimo IPV + Euríbor + IPC, ya construible hoy con el pipeline existente), de modo que EDA, forecasting básico y dashboard sobreviven a cualquier recorte de drivers V2 o del corpus. El único fallo realmente estructural sería el INE: improbable (organismo estatutario, API estable >10 años), y aun así los snapshots en `data/processed/` congelan el último estado bueno y Eurostat (`prc_hpi_q`) sirve de respaldo para el IPV con menos detalle regional.
- **Vía de simplificación asumible:** si el calendario aprieta, el proyecto se repliega a `gold_asequibilidad_ccaa` + forecasting sobre el panel mínimo de 3 columnas, y el RAG se reduce a 5–10 documentos clave. Ninguna simplificación rompe el contrato de datos.
