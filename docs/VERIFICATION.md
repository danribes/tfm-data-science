# Verificación de la revisión metodológica

Comprobaciones locales del 20 de septiembre de 2026, motor **1.1.0**.
El entorno instalado se describe en [environment.json](environment.json).

| Comprobación | Resultado |
|---|---|
| Suite Python ordinaria, sin descargas de modelos | **450 pruebas superadas**, 6 avisos de deprecación |
| Vitest | **299 pruebas superadas** en 40 archivos |
| TypeScript y build de producción Vite | Correctos; aviso de tamaño del bundle principal |
| Playwright con API simulada | **2 pruebas superadas**: flujo de escritorio y controles móviles a 390 px |
| Navegador con API real local | Escritorio 1440 px y móvil 390 px: cálculo, vivienda, análogos, horizonte, reset y tema; sin errores de consola ni HTTP |
| Presentación regenerada | HTML, PDF y PowerPoint; **19 páginas/diapositivas** |
| Inspección del PDF | Ningún bloque de texto fuera de página; revisión visual de fórmula de vivienda, ambas figuras y tabla de escenarios |
| Dependencias del entorno | `pip check`: sin incompatibilidades declaradas |
| Integridad de entradas e informes | **40 artefactos verificados** mediante SHA-256 y tamaño |
| Auditoría contable y extremos | 1.289 escenarios, 44 ejecuciones Monte Carlo y 99 sensibilidades opcionales; detalle en [MODEL_CHECK.md](MODEL_CHECK.md) |
| Recuperación documental real | E5 local; fuentes revisadas actualizadas con copia SQLite previa; índice de 485 documentos / 18.143 fragmentos íntegro |

Desde la raíz, la suite Python se ejecutó con:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
```

Desde `frontend/`: `npm test` y `npm run build`. Los tests de API requirieron
un entorno que permitiera los sockets Unix utilizados por `TestClient`.
La prueba Playwright (`npm run e2e`) construye respuestas simuladas; después se
restauró el build de producción con `npm run build`. La comprobación adicional
del navegador utilizó la API real local y verificó las cifras contra Python.

Se regeneraron parámetros regionales, constantes TypeScript, anclas numéricas,
sensibilidad de vivienda, sensibilidad Monte Carlo y el informe descriptivo
de analogías. Los informes históricos de distress, transferencia neuronal y
RAG **no se volvieron a estimar**. Actualizar sus advertencias no cambia sus
métricas ni demuestra una mejora de sus modelos.

No se realizó una instalación limpia, ejecución remota de CI, despliegue,
evaluación humana del RAG ni validación temporal calibrada de impago.
Estas comprobaciones verifican software y artefactos; los límites científicos
y los experimentos pendientes figuran en [RESULTS.md](RESULTS.md).

## Continuación: biblioteca pública y aislamiento de conexión

Comprobaciones posteriores del 20 de septiembre de 2026:

| Comprobación | Resultado |
|---|---|
| Suite Python ordinaria completa | **492 pruebas superadas**, 6 avisos de deprecación |
| Vitest completo | **326 pruebas superadas** en 44 archivos |
| TypeScript y build de producción | Correctos; persiste el aviso de tamaño del bundle |
| Playwright con API simulada | **2 pruebas superadas**, escritorio y móvil |
| API pública ensamblada en entorno reducido nuevo | **24 peticiones HTTP 200**, 3 rechazos 422 esperados y CORS correcto; 29 dependencias compatibles |
| Biblioteca pública | 6 documentos propios, 27 fragmentos; búsqueda léxica sin modelo ni índice privado |
| Navegador con API pública ensamblada | Biblioteca, Consulta y fuentes de perfil; Consulta a 390 px sin desbordamiento; sin fallos HTTP en los recorridos comprobados |
| Integridad de artefactos | **43 artefactos verificados** |
| Publicación remota | No realizada; `/health` público sigue anunciando 1.0.0 y `/rag/collections` devuelve 503 |

La comprobación reducida se reproduce con `deploy/hf/smoke.py` siguiendo
[estas instrucciones](../deploy/hf/README.md). A diferencia del entorno completo
de investigación, este entorno sí se instaló desde cero. No se probaron llamadas
reales a proveedores de generación ni el arranque de un contenedor remoto;
el navegador utilizó la API ensamblada servida localmente con Uvicorn.

Las comprobaciones funcionales de búsqueda no son una evaluación de calidad
del corpus público. La documentación propia y sus fragmentos no heredan las
métricas del recuperador híbrido académico.

## Preparación de la publicación conjunta

El contenido exacto preparado para Git se extrajo a un directorio limpio, sin
índice privado, documentos fuente locales ni archivos `.env`. En esa copia
pasaron **493 pruebas Python** y las comprobaciones del paquete público con
dependencias reducidas. La prueba adicional comprueba que disponer de informes
privados de libros no altera el manifiesto de integridad público.

Los tres registros detallados de libros, las transcripciones locales y las
capturas archivadas se excluyen de Git. El manifiesto público verifica
**40 artefactos**; la comprobación anterior de 43 incluía los tres registros
locales. Los resultados científicos no se modifican por esta separación.
