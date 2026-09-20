# RAG: alcance de la evidencia y protocolo de evaluación

## Resultados existentes

`rag-eval-2026-08-09.json` y `rag-chat-eval.json` son **resultados históricos de
desarrollo**. El conjunto de `rag/golden.py` se utilizó para ajustar pesos,
glosario y diversidad. No constituye un test independiente. Las anotaciones de
alcance añadidas al JSON no son nuevas mediciones; no se han repetido llamadas
de inferencia ni completado retrospectivamente configuraciones desconocidas.

El 34/35 de recuperación mide si aparece un documento cuyo título coincide con
el esperado entre ocho fragmentos. No mide si el fragmento responde la pregunta.
Las 10/12 verificaciones de fidelidad se refieren a la primera frase citada de
cada respuesta seleccionada y al primer pasaje citado, recortado a 2.000
caracteres, con otro modelo como juez. No son una revisión humana ni una medida
de exactitud de las respuestas completas. La presencia de corchetes sólo mide
integridad formal de referencias. Cuatro abstenciones no estiman de forma
precisa el comportamiento fuera del corpus.

El campo de compatibilidad `grounded` significa **hay contexto recuperado**.
Puede ser verdadero aunque el modelo se abstenga, falle o produzca una
afirmación incorrecta. La versión actual rechaza referencias ausentes o fuera
de rango y respuestas interrumpidas; publica el texto transmitido sólo después
de esa comprobación. Esto no demuestra respaldo semántico de cada afirmación.
El narrador de escenarios comprueba también que las magnitudes numéricas
aparezcan en sus hechos o en el contexto de calibración, admitiendo redondeo.
No valida automáticamente signos, unidades, asociación cifra-concepto ni
números escritos en palabras. En caso de fallo usa la narración determinista.

Los documentos y el índice se almacenan localmente. La generación remota envía
los fragmentos seleccionados y, si se solicita, los hechos del escenario al
proveedor configurado. Los tests unitarios no necesitan proveedores ni modelos
descargados; las evaluaciones del corpus y de chat se ejecutan explícitamente.

Las ampliaciones locales del 20 de septiembre de 2026 tienen registros separados:
`rag-book-additions-2026-09-20.json` para IIR e ISLP y
`rag-staged-books-2026-09-20.json` para los cuatro PDF aportados después.
Comparan el conjunto de desarrollo vigente de 39 preguntas antes y después de
cada operación, sin sobrescribir las métricas históricas de agosto. Las ocho
sondas de `rag-staged-book-probes-2026-09-20.json` se redactaron desde las fuentes
y se congelaron antes de consultar el recuperador; son sondas de desarrollo,
no un test independiente. Sus aciertos documentales, anclas de pasaje y revisión
de respaldo semántico deben interpretarse por separado.
Los tres registros detallados se conservan localmente: contienen anclas del
texto de las fuentes y no se distribuyen en GitHub ni en Hugging Face. Los
documentos `RAG_BOOK_ADDITIONS.md` y `RAG_STAGED_BOOKS.md` publican sus resúmenes.

## Congelar un test antes de utilizarlo

1. Una persona distinta de quien ajusta la recuperación redacta las preguntas,
   sin inspeccionar resultados del sistema. Conviene cubrir preguntas ES/EN,
   paráfrasis, comparaciones, datos numéricos, preguntas que exigen varias
   fuentes, desacuerdos entre fuentes, preguntas parcialmente respondibles y
   casos fuera del corpus. Definir por escrito tamaño, composición, métricas
   principales y reglas de exclusión antes de ejecutar el test. No se afirma
   que exista ya un conjunto de este tipo.
2. Archivar una copia consistente de SQLite con su API `backup` (sin otro
   proceso modificándola), los ficheros originales, la versión del extractor,
   el snapshot local del modelo y tokenizer y la revisión Git. Calcular SHA-256
   de la copia: `sha256sum /ruta/privada/corpus-frozen.db`. Usar esa misma copia
   mediante `EVO_RAG_DB` en todas las variantes. Guardar sus hashes y versiones
   en el registro del experimento; no publicar textos sin permiso.
3. Copiar `rag-heldout-template.jsonl` a una ubicación privada y completar una
   línea por pregunta. `expect_docs` contiene títulos o subcadenas;
   `expect_chunk_ids` identifica pasajes que realmente contienen la respuesta
   en el índice congelado, no sólo libros relacionados. El anotador puede
   consultar el corpus sin ver rankings del sistema. Registrar respuesta de
   referencia, justificación y todos los pasajes aceptables encontrados.
   Documentar que las etiquetas pueden ser incompletas.
4. Para cada pregunta, poner `annotation_status: "frozen"`, `split: "held_out"`,
   identidad del anotador, fecha ISO 8601 y SHA-256 de la copia en
   `corpus_sha256`. Las preguntas no respondibles llevan listas de fuentes
   esperadas vacías y `unanswerable: true`. El cargador rechaza la plantilla
   incompleta, preguntas duplicadas y hashes de corpus distintos. Validar
   manualmente la independencia: el programa no puede certificar quién vio
   las preguntas ni cuándo. Sellar el hash del JSONL antes de cualquier prueba.
5. Tras mirar resultados, no ajustar el sistema y volver a llamar “test” a
   esas preguntas. Un ajuste posterior exige un nuevo conjunto independiente.

## Comparaciones de recuperación reproducibles

Ejecutar desde la raíz del repositorio, con dependencias y modelo disponibles
localmente. `HF_HUB_OFFLINE=1` evita descargas implícitas. Reemplazar las rutas
de ejemplo. Las preguntas no respondibles se excluyen de hit/MRR y se revisan
en la evaluación de chat. Los chequeos auxiliares de aislamiento y filtro
siguen usando las sondas de desarrollo y están identificados como tales.

```bash
export EVO_RAG_DB=/ruta/privada/corpus-frozen.db
export HF_HUB_OFFLINE=1
# BM25, sin expansión bilingüe:
EVO_RAG_W_DENSE=0 EVO_RAG_W_DENSE_EN=0 EVO_RAG_W_LEXICAL=1 EVO_RAG_GLOSSARY=0 .venv/bin/python -m rag.evaluate --questions /ruta/privada/test.jsonl --json /tmp/rag-bm25.json
# Dense, consulta original:
EVO_RAG_W_DENSE=1 EVO_RAG_W_DENSE_EN=0 EVO_RAG_W_LEXICAL=0 EVO_RAG_GLOSSARY=0 .venv/bin/python -m rag.evaluate --questions /ruta/privada/test.jsonl --json /tmp/rag-dense.json
# Híbrido, sin expansión:
EVO_RAG_W_DENSE=6 EVO_RAG_W_DENSE_EN=0 EVO_RAG_W_LEXICAL=1 EVO_RAG_GLOSSARY=0 .venv/bin/python -m rag.evaluate --questions /ruta/privada/test.jsonl --json /tmp/rag-hybrid.json
# Híbrido + glosario + consulta inglesa, configuración congelada:
EVO_RAG_W_DENSE=6 EVO_RAG_W_DENSE_EN=4 EVO_RAG_W_LEXICAL=1 EVO_RAG_GLOSSARY=1 .venv/bin/python -m rag.evaluate --questions /ruta/privada/test.jsonl --json /tmp/rag-bilingual.json
```

Mantener top-k, límite por documento, corpus y candidatos constantes. Los pesos
anteriores son los de desarrollo, no el resultado de optimizar el test. Reportar
por separado hit/MRR documental y `passage_hit_rate`/`passage_mrr` sobre etiquetas
de pasajes, además de resultados por tema. Añadir intervalos de confianza y
comparaciones pareadas por pregunta; no contar ocho pasajes de una pregunta
como ocho observaciones independientes. Publicar también errores y latencia.

## Evaluación humana de respuestas y narración

La ejecución `python -m rag.eval_chat` sigue siendo una evaluación **de
desarrollo con API remota**, no el protocolo independiente anterior. Sus nuevas
salidas incluyen respuestas completas, modelo, errores, identificadores y
hashes de pasajes para auditarlos contra la copia local. Los resultados antiguos
no contienen todo esto y no pueden reconstruirse sólo desde sus JSON.

Para la evaluación independiente, registrar cada intento del test congelado en
una tabla con: `run_id`, `question_id`, `system_variant`, `provider`, `model`,
`prompt_hash`, `corpus_hash`, `timestamp`, `answer`, `retrieved_chunk_ids`,
`error`, `latency_ms`, `cost`, `reviewer_id`, `answerability`, `correctness`,
`completeness`, `claim_text`, `cited_chunk_ids`, `claim_supported`,
`numeric_consistency`, `rationale`. Conservar respuestas y errores de todas las
ejecuciones, sin descartar fallos de proveedor del denominador. Los costes y
latencias requieren medición, no están disponibles en los artefactos históricos.

Dos revisores, sin conocer la variante, evalúan todas las afirmaciones de cada
respuesta y contrastan las cifras, fechas y unidades con los pasajes completos.
Usar una rúbrica acordada: respuesta correcta/completa/parcial/incorrecta;
afirmación respaldada/contradicha/no consta; abstención apropiada/inapropiada.
Registrar desacuerdos, acuerdo entre revisores y adjudicación. Un juez LLM puede
servir de análisis secundario, calibrado contra esas etiquetas humanas.

Medir también el narrador y el intérprete de intención: fidelidad de cifras y
signos, unidad y horizonte correctos, palancas/serie/año interpretados, y
comportamiento ante escenarios fuera de rango. Un error de proveedor se cuenta
como fallo operativo; una abstención excesiva no es una respuesta correcta.
Predefinir repeticiones y parámetros de generación para estimar variabilidad.
Hasta ejecutar este protocolo, dejar sus resultados como **pendientes**.
