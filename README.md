# España en escenarios

**Análisis macrofiscal condicional para España, con evaluación empírica y explicaciones trazables.**

TFM de Inteligencia Artificial y Data Science · motor **1.1.0** · referencia del escenario **2026-07-31**.

El proyecto permite explorar qué implica un conjunto de supuestos sobre tipos,
crecimiento, saldo primario y demografía para la deuda, la vivienda y doce
perfiles ciudadanos. Combina un motor semiestructural, simulación Monte Carlo,
contrastes empíricos, modelos de aprendizaje automático y recuperación de
información económica. Las proyecciones son condicionales; los experimentos
publican también resultados negativos y límites de identificación.

## Material académico

- [Borrador de memoria](docs/MEMORIA_TFM.md): preguntas, métodos, resultados,
  discusión y bibliografía. Requiere revisión del autor y tutor; no se presenta
  como una memoria ya aprobada.
- [Matriz de evidencia](docs/RESULTS.md): modelos, baselines, particiones,
  métricas y conclusiones permitidas.
- [Guía de defensa](docs/DEFENSA_TFM.md) y [presentación](docs/deck/deck.marp.md).
- [Reproducción](docs/REPRODUCIBILITY.md): entorno, datos, comandos y pasos
  todavía ausentes para reconstruir el pipeline legado completo.
- [Cambios metodológicos](docs/METHODOLOGY_CHANGES.md): correcciones del motor,
  significado de las métricas y revisión del contrato API.
- [Verificación local](docs/VERIFICATION.md): resultados de pruebas, build y
  revisión de los artefactos de presentación.
- [Comprobación funcional del modelo](docs/MODEL_CHECK.md): auditoría contable,
  límites numéricos, navegador, recuperación documental y versión desplegada.
- [Evaluación RAG](docs/eval/README_RAG.md): resultados de desarrollo y protocolo
  para un test independiente aún pendiente.

## Qué aporta y qué se ha medido

| Componente | Evidencia y límite |
|---|---|
| Motor Python y TypeScript | Identidades, invariantes y anclas numéricas compartidas. La paridad comprueba la implementación, no la verdad de los supuestos. |
| Vivienda regional | Media y persistencia estimadas en 17 CCAA + Ceuta y Melilla; se excluye el agregado nacional. La sensibilidad con bloques temporales muestra incertidumbre mucho mayor que la banda regional. |
| Transferencia de una red de vivienda | Entrenamiento extranjero anterior a los orígenes de evaluación; resultado conservado: 5/17 victorias y MASE 0,400 frente a drift 0,395. No supera el baseline principal. |
| Distress | AUC agrupada por país 0,674. Puntuación exploratoria sin calibración temporal o específica para España. |
| RAG bilingüe | 34/35 aciertos de documento en preguntas usadas durante el ajuste; 10/12 afirmaciones muestreadas respaldadas según un juez LLM. No es evaluación independiente ni exactitud de respuestas completas. |
| Monte Carlo | Bandas condicionales y sensibilidad a persistencia, escala de choques, número de trayectorias y semilla. Cobertura predictiva real no evaluada. |
| Análogos | Distancia de Mahalanobis sobre cinco variables comparables y completas. Sin veredicto de sostenibilidad ni pretensión causal/predictiva. |

## Arquitectura

```text
data/gold + data/external → research/ → docs/eval/
          │
          └→ engine/ → api/ → frontend/
                │               └→ motor TypeScript (anclas compartidas)
                └→ explain/ ← rag/ (corpus e índice privados)
```

`engine/` contiene el motor, las palancas, umbrales, Monte Carlo y analogías;
`research/` contiene estimación y experimentos; `explain/` separa hechos
calculados de narración; `rag/` implementa recuperación y generación;
`frontend/` presenta resultados, fuentes y limitaciones.

## Ejecutar

Entorno comprobado: Python 3.12 y Node 22. Las versiones Python están
restringidas por `requirements-lock.txt`; npm utiliza `package-lock.json`.
Para detalles sobre instalación limpia, PyTorch y dependencias opcionales,
consultar [REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn api.main:app --port 8000
```

En otro terminal:

```bash
cd frontend
npm ci
npm run dev
```

La API publica su contrato en `http://localhost:8000/docs`. El panel usa
`http://localhost:8000` salvo que se configure `VITE_API_BASE`. Para una demo con
respuestas simuladas: `npm run build:mock` y `npm run preview` desde `frontend/`.
Esas respuestas son fixtures de interfaz, no resultados de investigación.

El corpus privado y su índice se localizan mediante `EVO_RAG_DATA` y
`EVO_RAG_DB`. El modo local predeterminado es híbrido: E5 y búsqueda léxica.
Los documentos se almacenan localmente; la generación remota envía los pasajes
seleccionados al proveedor configurado.

## Aplicación pública y biblioteca

El despliegue utiliza [GitHub Pages](https://danribes.github.io/tfm-data-science/)
para el panel y [Hugging Face Spaces](https://huggingface.co/spaces/danribes/evo-espana-api)
para la API y la biblioteca pública. Los workflows `deploy-pages` y
`deploy-hf-space` publican ambos servicios desde este repositorio; el paquete
de la API se prepara con las herramientas de `deploy/hf/`.

La configuración del Space incorpora un modo `public_lexical`: busca con
SQLite FTS5 en seis documentos propios del proyecto, enumerados en
[`rag/public_sources.json`](rag/public_sources.json). Expone las colecciones
`metodo` y `defensa_tfm`, con atribución `propio`. El ensamblado genera su índice
desde esos archivos, sin acceder al corpus privado ni cargar embeddings.
Los resultados históricos del RAG híbrido no evalúan este corpus público.

La búsqueda y consulta de fragmentos públicos funcionan sin claves de IA.
La redacción de respuestas requiere una clave de proveedor en los secretos
del Space; si no está disponible, se muestran los pasajes y el motivo.
Los libros privados siguen requiriendo su servicio local. La conexión RAG se
configura por separado de la API del motor, desde Biblioteca o Consulta; un
servicio RAG caído no impide utilizar los escenarios.

Preparar estos cambios no actualiza el sitio publicado. El procedimiento y
las comprobaciones previas a publicar están en
[`deploy/hf/README.md`](deploy/hf/README.md); el estado observado se registra en
[MODEL_CHECK.md](docs/MODEL_CHECK.md).

## Verificar y regenerar

```bash
.venv/bin/python scripts/check_data_integrity.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m pytest
```

Desde `frontend/`: `npm test` y `npm run build`. Los tests ordinarios no requieren
el corpus privado ni inferencia remota. Las pruebas opcionales de integración
se seleccionan con `pytest -m integration`. Playwright requiere su navegador.

Para regenerar resultados y figuras, instalar primero las dependencias opcionales
con `.venv/bin/python -m pip install -r requirements-regenerate.txt`.
Después de revisar cambios intencionados del motor o sus parámetros, desde la raíz:

```bash
.venv/bin/python -m tools.gen_estimated_params
node frontend/scripts/gen-constants.mjs
.venv/bin/python scripts/generate_anchor_fixture.py
.venv/bin/python -m research.housing_robustness
.venv/bin/python -m research.uncertainty
.venv/bin/python -m tools.evaluate_analogs
.venv/bin/python docs/deck/build_deck.py
.venv/bin/python scripts/check_data_integrity.py --update
```

El generador TypeScript importa el motor Python local: no necesita levantar la
API. `EVO_PYTHON` permite seleccionar otro intérprete. La actualización de
checksums debe acompañarse de la revisión del diff de resultados.

## Datos y limitaciones

La fecha de referencia del escenario no equivale a la fecha de adquisición de
todas las fuentes. El manifiesto distingue adquisición, corte de observaciones
y construcción. Las tablas congeladas permiten repetir cálculos; todavía falta
incorporar parte del pipeline legado de transformación desde datos originales.

Los parámetros de comportamiento siguen siendo en gran parte calibraciones.
Los resúmenes regionales estimados no prueban causalidad ni identifican por sí
solos parámetros estructurales de largo plazo. Los umbrales son referencias de
presentación, no probabilidades de crisis. Las bandas Monte Carlo omiten partes
de la incertidumbre y el score de distress no es una probabilidad validada.
Las combinaciones extremas que producen deuda negativa se señalan como salidas
del dominio de deuda bruta; el modelo no incorpora activos ni la respuesta de
política al agotar la deuda.

Quedan pendientes la evaluación RAG independiente con revisión humana, el
holdout final de vivienda, la validación temporal y calibración de distress,
y la reconstrucción completa desde las fuentes originales. Sus protocolos y
límites se publican; no se presentan como experimentos ya realizados.

Trabajo académico. Los datos y documentos conservan las condiciones de uso de
sus fuentes respectivas.
