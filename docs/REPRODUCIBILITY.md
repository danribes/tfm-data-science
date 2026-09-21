# Reproducción y alcance de los artefactos

El repositorio permite ejecutar el motor y repetir los análisis sobre las tablas
congeladas. No contiene todavía la reconstrucción completa desde cada descarga
original hasta esas tablas. Esta distinción se mantiene explícita: un checksum
verifica la identidad del archivo, no su autenticidad ni la validez del modelo.

## Entorno

El entorno comprobado es Linux x86_64, Python 3.12, Node 22 y npm 10.
`docs/environment.json` registra las versiones instaladas y `pip check`.
`requirements-lock.txt` fija las versiones de la clausura de dependencias usada
por los archivos `requirements*.txt`; estos archivos aplican esas restricciones.
El frontend usa `package-lock.json` y debe instalarse con `npm ci`.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
cd frontend
npm ci
```

No se ha realizado una instalación limpia durante esta revisión: los tests se
ejecutan sobre el entorno ya instalado. Las restricciones no son un archivo de
hashes de ruedas ni una garantía entre sistemas operativos. PyTorch fija la
versión 2.5.1; la máquina de desarrollo usa la rueda `2.5.1+cu121`. La CI instala
primero la rueda CPU de esa misma versión y después el resto de dependencias.
No se necesita una GPU para los tests. No se promete identidad numérica entre
dispositivos o versiones distintas a las registradas.

El despliegue API usa `requirements-deploy.txt` con las mismas restricciones;
no instala PyTorch, el modelo de embeddings ni el índice privado. La imagen de
Hugging Face incluye el archivo de restricciones antes de instalar.

## Verificación sin descargas ni corpus privado

Desde la raíz del repositorio:

```bash
.venv/bin/python scripts/check_data_integrity.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m pytest
```

Desde `frontend/`:

```bash
npm test
npm run build
```

La suite ordinaria usa datos congelados, modelos pequeños sintéticos o dobles
de prueba; no vuelve a entrenar la red global ni llama al proveedor del chat.
`pytest.ini` reserva `integration` para pruebas que requieran un servicio, una
descarga o un corpus externo, y las excluye por defecto. Para seleccionarlas de
forma explícita: `python -m pytest -m integration`. El marcador no sustituye
a los fixtures offline.

`TestClient` usa sockets Unix dentro del proceso. En un sandbox que prohíba
`socket.send` con `EPERM`, incluso una app FastAPI mínima puede bloquearse.
En ese caso ejecutar los tests en un entorno que permita esos sockets; no
modificar la implementación para saltarse las pruebas. Se verificó que el test
de salud responde correctamente fuera de ese sandbox.

Playwright es opcional y requiere tener su navegador instalado previamente.
`npm run e2e` construye el modo simulado y abre un servidor local. Los tests
unitarios y el build no prueban por sí solos el servicio externo desplegado.

## Datos, fechas y huellas

- `data/gold/VINTAGE` es la **fecha de referencia del escenario**, 2026-07-31.
  No implica que todos los artefactos de investigación añadidos después fueran
  descargados antes de esa fecha.
- `data/gold/manifest.csv` separa `acquired_at` (adquisición),
  `observation_cutoff` (corte de observaciones) y `built_at` (construcción).
  Los campos vacíos indican información no documentada. No se infieren fechas
  de la fecha de modificación del archivo.
- `data/gold/provenance_vintage_manifest.csv` conserva el inventario histórico
  y sus registros de descarga. No equivale a un archivo de todas las respuestas
  originales ni a un grafo completo de transformaciones.
- `data/ARTIFACT_METADATA.json` define estas convenciones.
- `data/artifact_checksums.json` sella los archivos de `data/gold/`,
  `data/external/` y `docs/eval/` con SHA-256 y tamaño.

Después de regenerar y revisar intencionadamente un artefacto:

```bash
.venv/bin/python scripts/check_data_integrity.py --update
.venv/bin/python scripts/check_data_integrity.py
```

Revisar el diff del artefacto y del manifiesto juntos. Actualizar hashes no
convierte un resultado incorrecto en correcto.

El cruce de países de distress está congelado en
`data/external/distress_country_codes.csv`. Su procedencia local y sus alias
explícitos figuran en el archivo `.metadata.json` contiguo. No hace consultas
al World Bank. Un cruce ausente o incompleto produce un error; los únicos
estados excluidos expresamente son Czechoslovakia y Yugoslavia. El cruce
reproduce las 3.874 observaciones, 377 eventos y 154 países del informe previo.

## Repetir los análisis desde los archivos congelados

Los siguientes comandos se ejecutan desde la raíz. Algunos regeneran informes
versionados y requieren revisar los cambios antes de actualizar checksums.

| Comando | Función y límite |
|---|---|
| `python -m research.validate` | Contrastes empíricos de los parámetros con las tablas congeladas. No identifica efectos causales por sí solo. |
| `python -m tools.gen_estimated_params` | Regenera `data/gold/estimated_params.json`; revisar después constantes, anclas y consumidores. |
| `python scripts/generate_anchor_fixture.py` | Regenera el contrato numérico compartido Python/TypeScript tras revisar motor y parámetros. |
| `python -m research.housing_robustness` | Estabilidad temporal y bootstrap de bloques de trimestres comunes a todas las regiones, comparado con la inferencia regional primaria. |
| `python -m research.uncertainty` | Sensibilidad de las bandas Monte Carlo a sus supuestos. |
| `python -m tools.evaluate_analogs` | Regenera normalización, covarianza y vecinos descriptivos de referencia; no mide predicción. |
| `python -m research.regimes` | Reestima el HMM y escribe `docs/eval/regimes.json`. Es una descripción retrospectiva. |
| `python -m research.distress` | Reentrena el clasificador, valida por grupos de países y reescribe `docs/eval/distress.json`. No es una validación temporal ni una calibración para España. |
| `python -m research.state_dependence` | Reentrena el contraste exploratorio con SHAP y bootstrap; puede tardar. |
| `python -m research.dl_global` | Entrena de nuevo la red con series extranjeras y repite el backtest; puede tardar. No forma parte de la suite ordinaria. |

En `frontend/`, `npm run gen:constants` regenera las constantes compartidas
directamente desde Python, sin consultar la API. Usa `.venv/bin/python` de la
raíz; `EVO_PYTHON` permite seleccionar otro intérprete. Tras cambiar parámetros,
regenerar primero `estimated_params.json`, después constantes y anclas, revisar
las diferencias y ejecutar ambas suites.
No confundir anclas de paridad con validación predictiva: dos implementaciones
pueden reproducir exactamente una misma hipótesis que los datos no apoyen.

Instalar `requirements-regenerate.txt` antes de generar las figuras: incluye
Matplotlib y su clausura de dependencias fijada en el archivo de restricciones.
`python docs/deck/build_deck.py` genera las diapositivas Markdown y dos figuras
SVG desde informes locales. `--render` añade HTML, PDF y PowerPoint mediante
Marp CLI y un navegador Chromium instalado; `CHROME_PATH` permite indicar su
ejecutable. Estas herramientas de presentación son opcionales y no forman
parte de las dependencias de la API.

El informe conservado de distress recibió una corrección de metadatos e
interpretación, **sin recalcular sus métricas** en esta revisión. `probability`
se conserva como nombre de campo API por compatibilidad, pero es la salida sin
calibrar del clasificador. La interfaz la presenta como puntuación 0–1 y no
como probabilidad de impago ni como múltiplo de riesgo frente a la tasa base.
No se han añadido Brier score, curvas de fiabilidad o validación temporal
porque aún no se han medido. Las importancias por permutación del informe
existente se calcularon sobre la muestra de entrenamiento.

## Actualización de fuentes y límites pendientes

Para instalar las dependencias opcionales de adquisición y figuras:

```bash
.venv/bin/python -m pip install -r requirements-regenerate.txt
```

El procedimiento completo —descargar, comparar, decidir, promover, recalcular
y comprobar— está en **[ACTUALIZAR_DATOS.md](ACTUALIZAR_DATOS.md)**. Lo que
sigue resume las herramientas sueltas.

`python scripts/refresh_vintage.py` descarga las URL HTTP(S) registradas a
`data/vintages/<fecha>/raw/`. Omite artefactos derivados y registros sin URL
descargable, registra fallos y no toca `data/gold/`. No reconstruye los gold,
no establece automáticamente un corte de observaciones y no recupera revisiones
históricas ya sustituidas por el proveedor.

`python scripts/diff_vintage.py <antes> <después>` compara dos vintages
descargados y dice qué se ha movido en el origen. Devuelve 1 si hay algo que
revisar. El vintage congelado no guarda el sha256 de sus descargas originales
—16 de sus 18 filas lo tienen vacío— así que contra él no hay comparación
posible; la herramienta lo declara «no comparable» en vez de fingir un «sin
cambios».

`python -m tools.fetch_wb_panel` puede adquirir un panel WDI nuevo.
`python scripts/build_analog_panel.py` requiere red para fuentes no almacenadas
y puede escribir artefactos gold. Sus datos nuevos no son el mismo vintage
histórico aunque cubran los mismos años. No ejecutar estos comandos como parte
de la comprobación offline.

Pendientes para una reconstrucción completa:

1. Incorporar o archivar con referencias estables el pipeline legado de
   adquisición y transformación de las tablas gold.
2. Documentar y conservar las descargas/transformaciones de las series FHFA,
   Zillow y Reino Unido, cuyo corpus comprimido procede del proyecto anterior.
3. Conservar el extractor original de las etiquetas BoC–BoE y su libro fuente
   con una identificación inequívoca de versión; aquí se incluyen las etiquetas
   ya derivadas y su atribución.
4. Recuperar los archivos fuente opcionales ausentes, como el Excel PWT para
   reproducir esa ampliación concreta del panel de analogías.
5. Reconstruir y comprobar un entorno limpio con las restricciones publicadas;
   la CI añadida lo verifica cuando se ejecute, no se afirma haberlo hecho aquí.

La evaluación RAG real depende de documentos e índice que no se distribuyen
con este repositorio. Sus métricas históricas, separación desarrollo/prueba y
límites de la evaluación se documentan en `docs/eval/README_RAG.md`. La suite
sintética comprueba el mecanismo; no reproduce las métricas del corpus privado.

La biblioteca pública se construye por separado con
`python -m rag.public_corpus --source-root . --out /tmp/evo-public.db`.
Solo lee los seis documentos propios enumerados en `rag/public_sources.json`;
no necesita corpus privado, embeddings ni paquetes externos. Para ejecutar
la API con ese índice, fijar `EVO_RAG_MODE=public_lexical` y
`EVO_RAG_DB=/tmp/evo-public.db` antes de arrancar el proceso. El modo local
predeterminado sigue siendo `hybrid`.

La instalación reducida y la prueba del paquete exacto para Hugging Face se
describen en [deploy/hf/README.md](../deploy/hf/README.md). Este modo ofrece
búsqueda por palabras en documentación propia, no reproduce la recuperación
bilingüe del corpus académico ni hereda sus métricas.

La comprobación de integridad pública excluye los registros locales
`rag-book-additions-*.json`, `rag-staged-book-probes-*.json` y
`rag-staged-books-*.json`, también ignorados por Git. Pueden contener anclas
textuales de los libros; sus resúmenes se conservan en los documentos RAG.
El manifiesto de publicación verifica los 40 artefactos distribuibles y no
requiere disponer de esos registros privados en una instalación limpia.

Tras revisar los documentos propios, repetir la ingestión de las colecciones
`metodo` y `defensa_tfm` actualiza sus fuentes. Guardar antes una copia del índice
con la API de backup de SQLite. Una fuente modificada sustituye atómicamente
sus versiones previas dentro de la misma colección, incluidos texto, FTS y
vectores; un fallo conserva la versión anterior completa. Las fuentes sin
cambios se omiten. Cambiar el corpus no actualiza las métricas históricas: una
evaluación nueva debe fijar y publicar su propia huella del corpus.
