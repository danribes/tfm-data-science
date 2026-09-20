# Comprobación funcional del modelo

Revisión local del 20 de septiembre de 2026. Las comprobaciones acreditan el
comportamiento observado del software y sus identidades contables. No miden
capacidad de predicción económica ni fidelidad semántica de respuestas nuevas.

## Estado del despliegue

La rama remota `main` y el HEAD local apuntaban a
`dde09c6e6e3fd4842535994e12884c8fdcdc139c`. Los cambios revisados seguían
sin commit ni push. Las últimas ejecuciones publicadas de GitHub Actions
correspondían a ese commit anterior.

El sitio público y `/health` respondieron HTTP 200. La
[API pública](https://danribes-evo-espana-api.hf.space/health) declaraba motor
**1.0.0**; el servidor local declaraba **1.1.0**. Por tanto, esta revisión no
acredita un despliegue público de las correcciones.

La comprobación posterior del mismo día confirmó HTTP 200 en Pages y en
`/health`, todavía con motor **1.0.0**, y HTTP 503 en `/rag/collections`.
La continuación descrita al final de este documento está preparada y probada
localmente; no se ha publicado ni subido el corpus privado.

## Auditoría matemática

| Comprobación | Resultado |
|---|---|
| Casos deterministas | 1.289: base, ocho presets, 1.024 combinaciones de extremos y 256 muestras con semilla 20260920 |
| Salidas examinadas | 40 series, 25 años por caso; todas finitas |
| Reconstrucción independiente de deuda nominal | Error máximo inferior a 6,3 × 10⁻¹³ puntos de PIB |
| Descomposición de la ratio con el saldo publicado | Error máximo inferior a 2,3 × 10⁻¹³ puntos |
| Monte Carlo | 44 ejecuciones; percentiles ordenados, trayectorias finitas y recuperación exacta del caso sin choques |
| Sensibilidades opcionales de Python | 99 configuraciones de persistencia y prima; todas finitas, algunas económicamente extremas |

Se corrigieron dos errores que las pruebas anteriores no detectaban: los
intereses usaban el PIB previo mientras la deuda usaba el corriente, y la
prima endógena opcional era cien veces menor que sus unidades declaradas.
También se corrigió la cuota de un préstamo a interés exactamente cero.
Las pruebas nuevas reconstruyen importes nominales y comprueban unidades,
además de mantener la concordancia entre Python y TypeScript.

En 24 combinaciones extremas, la recurrencia produce deuda bruta negativa
(mínimo −11,06% del PIB). La cola p5 Monte Carlo también puede ser negativa.
Estos casos se señalan como salidas del dominio del modelo. No se recortan
silenciosamente ni se interpretan como activos públicos modelizados.

El [informe completo](eval/model-audit.json) registra semilla, casos, extremos
y hashes de código y datos. Se reproduce desde la raíz con:

```bash
.venv/bin/python -m tools.check_model
```

## API, navegador y documentos

Se probaron 16 endpoints GET locales, escenarios y análogos en 2026/2036/2050,
repetibilidad de Monte Carlo, rechazo 422 de entradas inválidas, CORS y
explicaciones deterministas. Después de las correcciones, tres escenarios
completos coincidieron exactamente entre cálculo directo y API; la consulta
de análogos utilizó el saldo corregido del año seleccionado.

La comprobación del navegador ahora compara las 40 series y todos los años
con la API: la prueba anterior, limitada a deuda, no detectaba divergencias
en vivienda. Se corrigieron los diagramas presupuestarios para conservar
importes y separar saldo fiscal de variaciones del denominador PIB. Los
flujos dibujados se identifican como esquemas del escenario.

El navegador real se probó a 1440 px y 390 px. Se corrigió un panel móvil
inaccesible: ahora tiene apertura, cierre, Escape, control de foco y
desplazamiento vertical; los indicadores caben en la pantalla estrecha.
Pasaron cambios de palanca, horizonte, reset, tema y actualización de análogos,
sin errores de consola ni HTTP. En el caso vivienda de 2030 con Euríbor 4,8%,
la interfaz y Python mostraron precio 189.871,96 €, cuota 1.004,44 € y esfuerzo
49,867%. Las dos pruebas Playwright automatizadas también pasaron.

La recuperación documental se comprobó con E5 real almacenado localmente,
sin descargas ni llamadas a proveedores de generación. Tras guardar una
copia SQLite se actualizaron dos fuentes obsoletas y se incorporaron cuatro
documentos metodológicos. El índice quedó con **485 documentos y 18.143
fragmentos**, con igual número de registros FTS y vectores; `integrity_check`
devolvió `ok`. Los otros 479 documentos conservaron colección, ruta y hash.
Las consultas posteriores recuperaron la memoria, resultados y metodología
actuales dentro de la colección solicitada.

La ingestión ahora reemplaza una fuente de forma atómica y conserva su versión
anterior ante fallos, en lugar de acumular versiones obsoletas. Esto no vuelve
a medir los resultados históricos del RAG. La generación remota y una evaluación
humana independiente siguen pendientes.

Los resultados finales de suites, build y pruebas de navegador se registran
en [VERIFICATION.md](VERIFICATION.md).

## Ampliación posterior de la biblioteca

Después de esta revisión se incorporaron dos PDF completos ofrecidos por sus
autores: *Introduction to Information Retrieval* y *An Introduction to Statistical
Learning with Applications in Python*. El índice local pasa a **487 documentos y
19.325 fragmentos**; la colección académica contiene **51 fuentes**. Se corrigió
la atribución de página en fragmentos solapados y se verificaron los 1.182
fragmentos nuevos contra sus PDF. Los seis sondeos de recuperación ES/EN pasan,
y los resultados de las 39 preguntas de desarrollo no cambian. Véanse fuentes,
libros pendientes y límites en [RAG_BOOK_ADDITIONS.md](RAG_BOOK_ADDITIONS.md).

En una incorporación posterior se indexaron los cuatro PDF locales de
Wooldridge, Blanchard, Galí y el capítulo preliminar de Woodford. El estado
resultante es **494 documentos y 21.375 fragmentos**, con **58 fuentes académicas**.
Se corrigió la edición de Wooldridge y se identificó el alcance parcial de
Woodford. Se conservaron todos los documentos y vectores previos y pasaron los
controles de integridad y de la API. La recuperación documental del conjunto de
desarrollo se mantiene en 37/39, aunque las sondas nuevas detectan limitaciones
al localizar evidencia concreta. Los detalles y resultados están en
[RAG_STAGED_BOOKS.md](RAG_STAGED_BOOKS.md).

## Biblioteca pública preparada para Hugging Face

Se completó un modo público independiente del índice académico: SQLite FTS5
sobre **6 documentos propios y 27 fragmentos**, con colecciones `metodo` y
`defensa_tfm`. El manifiesto fija exactamente los archivos permitidos. La
atribución indica documentación propia; `/rag/eval` explica que las métricas
históricas de recuperación híbrida no evalúan este modo.

El paquete ensamblado se comprobó en un entorno Python 3.12 nuevo, instalado
únicamente con `requirements-deploy.txt`: **29 paquetes**, sin PyTorch,
sentence-transformers, sqlite-vec ni lector PDF. Pasaron **24 peticiones con
HTTP 200**, tres rechazos 422 para colecciones no publicadas y el control CORS.
Estas peticiones incluyen los informes públicos, escenarios, búsqueda en las
dos colecciones y consulta JSON/SSE. No se utilizaron claves de generación ni
se accedió al corpus privado. Sin proveedor, las respuestas conservan los
pasajes y explican la indisponibilidad de la redacción.

Biblioteca, Consulta y el cajón de fuentes seleccionan las colecciones que
anuncia el servidor. La conexión RAG y sus credenciales quedan separadas de
la API del motor; cambiar la biblioteca invalida sus consultas y su evaluación.
Se verificaron estos recorridos contra la API ensamblada en Chromium, incluido
Consulta a 390 px sin desbordamiento horizontal. Las comprobaciones de
Biblioteca y Consulta terminaron sin errores de consola ni respuestas HTTP
fallidas; el perfil recuperó fuentes propias mediante `/rag/search`.

El ensamblado rechaza destinos con contenido previo y copia solo cuatro
informes públicos de investigación. Las pruebas comprueban que un informe
privado antiguo no se incorpora por reutilizar el directorio. El workflow del
Space ejecuta la comprobación del paquete reducido antes de subirlo.

Esto prepara el funcionamiento público sin portátil de la documentación propia.
Los libros y el recuperador híbrido permanecen locales. La publicación conjunta
incluye también las correcciones previas del motor **1.1.0**, todavía sin commit;
el sitio existente sigue sirviendo la versión anterior hasta publicar esa
revisión. Procedimiento: [deploy/hf/README.md](../deploy/hf/README.md).
