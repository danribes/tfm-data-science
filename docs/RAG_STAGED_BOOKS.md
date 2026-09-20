# Incorporación de los cuatro PDF locales — 20 de septiembre de 2026

Se completó la ingestión pendiente descrita en la conversación adjunta. Los
cuatro PDF ya estaban en el directorio privado y seleccionados en su manifiesto;
ninguno tenía todavía un documento en el índice. Se revisaron los archivos,
se corrigieron sus referencias y se incorporaron a la colección `libros`.

## Fuentes incorporadas

| Fuente verificada | Páginas físicas del PDF | Fragmentos | Alcance de la copia |
|---|---:|---:|---|
| Jeffrey M. Wooldridge, *Econometric Analysis of Cross Section and Panel Data*, primera edición, 2002, MIT Press | 741 | 737 | Capítulos 1–20 y referencias; faltan la página de copyright y el índice alfabético final. La identificación de edición se contrastó con contenido y catálogo; el nombre anterior decía erróneamente segunda edición. |
| Olivier Blanchard, *Macroeconomics*, novena edición, copyright 2025, Pearson | 591 | 873 | Libro con texto extraíble; ISBN 9780138119010. |
| Jordi Galí, *Monetary Policy, Inflation, and the Business Cycle: An Introduction to the New Keynesian Framework*, primera edición, 2008, Princeton University Press | 216 | 210 | Primera edición; ISBN 9780691133164. |
| Michael Woodford, *Interest and Prices — Chapter 1: The Return of Monetary Rules*, borrador preliminar del 30 de enero de 2002 | 72 | 73 | Portada, contenido y páginas impresas 1–70 del capítulo 1. No es el libro publicado completo. |

Se corrigieron los nombres de las cuatro copias locales antes de indexarlas,
conservando exactamente sus bytes. Los manifiestos privado y del repositorio
registran autores, año, edición, idioma, SHA-256 y procedencia **PDF local
aportado por el usuario**. No se atribuye a estos archivos una descarga oficial
gratuita. Los PDF y el índice permanecen en `../evo_final_work_data/`.

La sincronización de [CORPUS_MANIFEST.csv](CORPUS_MANIFEST.csv) también conserva
las tres fuentes Markdown añadidas previamente desde otra sesión: FPP3, *The
Effect* y el capítulo de paneles de *Causal Inference: The Mixtape*. Esas fuentes
ya estaban indexadas y no se reprocesaron. El manifiesto contiene **81 entradas,
58 seleccionadas**, todas presentes en la colección académica.

## Integridad y citas

- Se añadieron **1.893 fragmentos**. El índice completo contiene **494 documentos
  y 21.375 fragmentos**; la colección académica, **58 fuentes y 17.402 fragmentos**.
- Los **490 documentos, 19.482 fragmentos y 19.482 vectores anteriores** se
  compararon con una copia SQLite previa: se conservaron sin cambios.
- Pasaron `integrity_check`, claves foráneas e integridad FTS. Hay una entrada
  vectorial y léxica por fragmento. Repetir la ingestión de las cuatro fuentes
  devuelve `ya-indexado` y no añade duplicados.
- Los 1.893 fragmentos nuevos se cotejaron completos con el texto extraído:
  ninguno sin correspondencia ni con una página inicial errónea. Las páginas
  citadas son las del archivo PDF, no necesariamente las impresas en el libro.
- La API local respondió 200 en `/rag/collections` y `/rag/search`, y publicó
  los recuentos del índice actualizado.

El PDF de Wooldridge presenta errores de codificación de algunas ligaduras y
símbolos; las ecuaciones y los gráficos pueden perder disposición. Los títulos
de sección se detectan mediante reglas y pueden confundir etiquetas de gráficos
con encabezados. La página física verificada es la referencia más fiable para
localizar el pasaje. Dos candidatos cortos del diagnóstico SQL contienen NUL:
al comprobar la longitud completa con Python, ninguno está por debajo del mínimo.

## Recuperación antes y después

Se conservaron las mismas 39 preguntas contestables de desarrollo, el mismo
modelo E5 y los mismos parámetros de recuperación. Se midieron ambos estados
durante esta operación, sin reutilizar los resultados de una sesión anterior.

| Medida documental | Antes | Después |
|---|---:|---:|
| Fuente esperada presente entre ocho pasajes | 37/39 | 37/39 |
| Fuente esperada en primera posición | 25/39 | 25/39 |
| MRR | 0,75177 | 0,75049 |

Solo cambió la posición de una fuente esperada: `exp-anclaje`, de cuarta a quinta.
La ampliación no produjo una caída general de los aciertos de este conjunto.
Estas medidas se basan en títulos de documentos; no establecen que los pasajes
contengan la respuesta ni constituyen una evaluación independiente.

Además se redactaron y congelaron **ocho sondas de desarrollo** antes de ejecutar
sus búsquedas: dos por fuente, cuatro en español y cuatro en inglés. Sus 21
anclas textuales se verificaron en páginas concretas y todas se localizaron en
los fragmentos indexados. Se separó encontrar un libro de encontrar su evidencia:

- El libro previsto apareció en **7/8 consultas**, en primera posición en **3/8**.
- Se recuperaron completos **3 de 12 grupos de anclas**; **1/8 consultas** encontró
  todos los grupos previstos. Este criterio exige las frases y fuentes concretas
  congeladas; otros pasajes o fuentes también pueden respaldar una respuesta.
- La consulta en español sobre la trayectoria esperada de tipos no recuperó
  el capítulo de Woodford entre los ocho resultados. No se modificaron las
  preguntas ni los pesos para ocultar el fallo.

Una revisión posterior de los 64 pasajes recuperados, realizada por el asistente
contra los criterios congelados, encontró contexto suficiente para **5/8
consultas**, parcial para **2/8** e insuficiente para **1/8**. A nivel de los 16
puntos de respuesta previstos, 12 estaban respaldados, dos parcialmente y dos
no. Se aceptó evidencia pertinente de otros libros; por eso esta revisión no
coincide con el criterio de anclas exactas de una fuente concreta.

Los huecos afectan al supuesto explícito de tamaños de clúster fijos, la pérdida
de rango al eliminar la media temporal de un regresor constante y el mecanismo
de transmisión de la trayectoria esperada de tipos. La revisión aporta pasajes
y razones por punto; sigue siendo una revisión de desarrollo por un asistente,
no validación humana independiente ni medición de respuestas generadas.

La ingestión está completa. La recuperación de pasajes concretos sigue siendo
un aspecto a mejorar y medir; añadir libros no garantiza respuestas mejores.
No se hicieron llamadas a proveedores de generación durante esta comprobación.

## Registro y reproducción

- Sondas congeladas locales, `docs/eval/rag-staged-book-probes-2026-09-20.json`: preguntas,
  hashes de fuente, páginas, anclas y criterios de respuesta; conjunto de desarrollo.
- Informe local de ingestión y recuperación, `docs/eval/rag-staged-books-2026-09-20.json`:
  fuentes, controles de conservación, resultados completos por pregunta y API.
- Los pasajes íntegros usados para la revisión se guardaron en el directorio
  privado `../evo_final_work_data/rag/checks/staged-books-2026-09-20-passages.json`.

Estos registros detallados, que incluyen anclas del texto de los libros, se
conservan localmente y se excluyen tanto de GitHub como del Space. El resumen
de resultados de este documento sí forma parte del repositorio público.

Desde la raíz, con el modelo ya disponible localmente:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m rag.ingest --collection libros
.venv/bin/python -m rag.ingest --stats
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m rag.evaluate --json /tmp/rag-current-development.json
```

El último comando vuelve a medir el conjunto habitual y sus comprobaciones
auxiliares. Las ocho sondas adicionales deben ejecutarse con el texto exacto y
el protocolo del archivo congelado, manteniendo separados sus resultados.
