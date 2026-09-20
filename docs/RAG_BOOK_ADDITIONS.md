# Ampliación bibliográfica del RAG — 20 de septiembre de 2026

Este documento registra la primera ampliación y sus recuentos de ese momento.
La incorporación posterior de cuatro PDF aportados por el usuario y el estado
actual de 58 fuentes académicas se documentan en [RAG_STAGED_BOOKS.md](RAG_STAGED_BOOKS.md).

Se buscaron versiones gratuitas de los seis libros recomendados. Se localizaron
dos PDF completos enlazados por sus autores y se descargaron en el directorio
privado `../evo_final_work_data/econ_pdfs/`. Los PDF no forman parte del repositorio.

## Libros incorporados

| Referencia | Fuente oficial | Páginas del PDF | Fragmentos | Tema |
|---|---|---:|---:|---|
| Manning, C. D., Raghavan, P. y Schütze, H. (2008). *Introduction to Information Retrieval*. Cambridge University Press. Edición en línea actualizada el 1 de abril de 2009. | [Web de los autores](https://nlp.stanford.edu/IR-book/), [PDF](https://nlp.stanford.edu/IR-book/pdf/irbookonlinereading.pdf) | 581 | 555 | Recuperación y evaluación de información |
| James, G., Witten, D., Hastie, T., Tibshirani, R. y Taylor, J. (2023). *An Introduction to Statistical Learning with Applications in Python*. Springer. | [Web de los autores](https://www.statlearning.com/), [enlace oficial de descarga](https://hastie.su.domains/ISLP/ISLP_website.pdf.download.html) | 613 | 627 | Aprendizaje estadístico y validación |

Ambos libros pertenecen a `libros`, con autoridad `academico`. La etiqueta visible
de esta colección pasa a **Economía y métodos**. Se mantienen los pesos de
recuperación, el modelo E5 y la separación respecto a metodología propia y opinión.

El manifiesto conserva autores, año, edición, URL de referencia y descarga,
fecha de consulta, disponibilidad y SHA-256 completo. Estos campos también se
guardan como metadatos del documento al incorporarlo al índice. Los PDF se
ofrecen gratuitamente por sus autores; no se les atribuye una licencia abierta
que la fuente no declare. Las citas de la aplicación usan páginas del archivo
PDF, que pueden diferir de la numeración impresa.

Se sincronizó [CORPUS_MANIFEST.csv](CORPUS_MANIFEST.csv) con el manifiesto privado
que utiliza la ingestión. Esto recoge también las siete incorporaciones previas
que faltaban en la copia del repositorio y conserva la exclusión del escaneo
ilegible de *Economics*, 16.ª edición.

## Corrección de extracción y citas

La revisión detectó que el solapamiento entre fragmentos perdía su página de
origen: 344 fragmentos de IIR y 443 de ISLP citaban una página posterior a su
inicio. El extractor ahora conserva página y sección por tramo de texto,
incluido el solapamiento, sin cargar todo el libro en memoria.

Se eliminan únicamente secuencias largas de líneas formadas por barras de
gráficos, conservando expresiones matemáticas y código. Tras esta limpieza,
ISLP pasa de 648 a 627 fragmentos; IIR permanece en 555. Los **1.182 fragmentos**
se cotejaron completos con el texto limpio de los PDF: ningún fragmento sin
correspondencia ni página inicial incorrecta. La mejora se aplicó a estos dos
libros; las fuentes anteriores conservan su indexación.

La extracción de la portada de ISLP tiene caracteres corruptos y las fórmulas
y tablas pueden perder disposición visual. La detección de secciones es
heurística y puede mantener un encabezado anterior en un índice no numerado;
la página física del PDF permite localizar el pasaje. Estos controles no
demuestran fidelidad semántica de respuestas generadas.

## Verificación del índice y la recuperación

El registro local `docs/eval/rag-book-additions-2026-09-20.json` documenta
los hashes, la configuración y los pasajes recuperados por identificador.
Los registros detallados de incorporación de libros no se publican en GitHub
ni en el Space; este documento conserva el resumen de resultados.

- **51 fuentes académicas y 15.352 fragmentos** en `libros`; **487 documentos y
  19.325 fragmentos** en el índice completo.
- Los 485 documentos anteriores y sus 18.143 fragmentos se conservan. SQLite,
  claves foráneas e integridad FTS pasan; hay un vector y una entrada léxica por
  fragmento. Volver a ingerir los mismos PDF omite ambas fuentes sin duplicarlas.
- Seis consultas de integración en inglés y español sobre precisión/recall,
  BM25, validación cruzada y lasso recuperan el libro esperado en primer lugar.
  Todas las citas pertenecen a la colección académica y tienen página del PDF.
- Las 39 preguntas contestables del conjunto de desarrollo mantienen sus
  posiciones: **37/39 aciertos documentales en top-8**, MRR **0,7774**. Esto compara
  títulos esperados; no es una evaluación independiente ni mide respuestas
  generadas. No se realizaron llamadas a proveedores de generación.
- Pasaron **113 pruebas Python del RAG**, **13 pruebas de la biblioteca web** y
  el build de producción del frontend.

El contador SQL de tamaño señala un pasaje de IIR con un carácter NUL de un
diagrama: SQLite cuenta 119 caracteres antes de ese carácter, mientras Python
lee los 2.932 caracteres completos. La comprobación con la longitud real no
encuentra fragmentos por debajo del mínimo. Los diagramas pueden conservar
caracteres de control procedentes de la extracción del PDF.

## Libros sin PDF gratuito oficial verificado

| Libro solicitado | Resultado de la búsqueda |
|---|---|
| Hyndman y Athanasopoulos, *Forecasting: Principles and Practice*, 3.ª ed. | [Texto completo gratuito en HTML](https://otexts.com/fpp3/); no se verificó un PDF completo gratuito del editor. No se incorporó una copia de terceros ni se convirtió la web en un supuesto PDF oficial. |
| Blanchard, *Macroeconomics*, 9.ª ed. | [Pearson](https://www.pearson.com/en-us/subject-catalog/p/macroeconomics/P200000010516/9780135343388): no se encontró un PDF completo gratuito autorizado. |
| Wooldridge, *Econometric Analysis of Cross Section and Panel Data*, 2.ª ed. | [MIT Press](https://mitpress.mit.edu/9780262232586/econometric-analysis-of-cross-section-and-panel-data/): edición comercial; hay diapositivas complementarias gratuitas, que no equivalen al libro. |
| Stiglitz y Rosengard, *Economics of the Public Sector*, 4.ª ed. | [Norton](https://wwnorton.com/books/9780393925227): no se encontró un PDF completo gratuito autorizado. |

No encontrar una copia autorizada en esta búsqueda no demuestra que no exista
ninguna modalidad de acceso institucional o préstamo.

## Reproducción

Con los dos PDF y el manifiesto en el directorio privado configurado:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m rag.ingest --collection libros
.venv/bin/python -m rag.ingest --stats
```

La ingestión omite fuentes cuyo contenido ya está indexado. Se guardó una copia
consistente de SQLite y del manifiesto antes de añadir los libros, en
`../evo_final_work_data/rag/backups/before-book-additions-20260920T063521Z.*`.
