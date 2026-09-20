# API pública y documentación del proyecto en Hugging Face

El Space sirve el motor, datos congelados e informes de investigación junto
con una biblioteca de seis documentos propios. La biblioteca usa SQLite FTS5
y se construye desde la documentación del repositorio. GitHub Pages publica
el panel, que conecta con esta API.

## Preparación y comprobación local

Desde la raíz del repositorio, con Python 3.12:

```bash
stage=$(mktemp -d /tmp/evo-hf-stage.XXXXXX)
./deploy/hf/assemble.sh "$stage"
python3.12 -m venv "$stage-venv"
"$stage-venv/bin/python" -m pip install -r "$stage/requirements-deploy.txt"
"$stage-venv/bin/python" deploy/hf/smoke.py "$stage"
```

El destino debe ser nuevo o estar vacío. Se rechazan los directorios con
contenido para evitar que archivos de un ensamblado anterior entren en una
publicación. Para repetir, crear otro destino.

`smoke.py` carga la API desde el paquete ensamblado. Comprueba informes,
escenarios, búsqueda, consultas JSON y SSE, colecciones y CORS, con las
dependencias reducidas y sin claves de proveedor. No mide calidad semántica
ni prueba inferencia remota. El Dockerfile fija `EVO_RAG_MODE=public_lexical`
y `EVO_RAG_DB=/app/data/rag/public.db`.

## Contenido publicado

[`rag/public_sources.json`](../../rag/public_sources.json) enumera exactamente
README, memoria, resultados, cambios metodológicos, reproducibilidad y defensa.
El constructor verifica rutas, rechaza enlaces simbólicos, conserva hashes y
genera un índice reproducible. Solo ofrece `metodo` y `defensa_tfm`; pedir
`libros` o `crack23` devuelve 422.

El ensamblado copia cuatro informes de investigación explícitos. No copia
PDF, el índice privado ni los informes de adquisición y sondeos de libros.
`/rag/eval` explica que la evaluación híbrida privada no se aplica a esta
biblioteca pública. La interfaz identifica los documentos como fuentes
propias del proyecto.

## Publicación

Los workflows `deploy-hf-space` y `deploy-pages` publican los cambios al hacer
push a `main`; también admiten ejecución manual. La rama publicada debe incluir
los seis documentos del manifiesto, el código y el archivo de restricciones
`requirements-lock.txt`. El workflow del Space ensambla y ejecuta `smoke.py`
antes de subir; un fallo impide ese paso. `verify` repite la comprobación del
paquete público en un trabajo separado.

El repositorio GitHub necesita el secreto `HF_TOKEN` con permiso de escritura
en el Space. Pages usa `API_BASE`, con el Space existente como valor por defecto.
`RAG_API_BASE` permite seleccionar otro servicio para la biblioteca; su valor
por defecto también es el Space. No introducir claves de proveedor ni tokens
de acceso en variables `VITE_*`.

Para generar respuestas, configurar en los **Secrets** del Space una clave
admitida: `GEMINI_API_KEY`, `GLM_API_KEY`, `KIMI_API_KEY` u `OPENAI_API_KEY`.
La búsqueda no requiere ninguna. Sin proveedor disponible, Consulta conserva
los fragmentos recuperados y explica que no ha podido redactar una respuesta.

Después de publicar, comprobar `/health`, `/rag/collections`, una búsqueda
en `/rag/search` y Consulta en el panel. Si el navegador conserva una dirección
de biblioteca antigua, restablecer la conexión RAG desde sus ajustes o abrir
el panel con `?rag=reset`. Este ajuste no cambia la conexión del motor.
