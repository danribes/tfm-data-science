---
title: España en escenarios · API
emoji: 📊
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
---

# España en escenarios — API pública

Servicio FastAPI del TFM «España en escenarios»: motor fiscal dual,
artefactos de investigación (backtest T1, distress, dependencia del estado,
regímenes) e informes.

- Frontend: <https://danribes.github.io/tfm-data-science/>
- Código: <https://github.com/danribes/tfm-data-science>

La biblioteca pública busca en seis documentos propios del proyecto:
memoria, resultados, metodología, reproducibilidad, defensa y README.
Las colecciones `metodo` y `defensa_tfm` usan búsqueda léxica SQLite FTS5;
cada fragmento incluye su documento y sección. Esta versión no incluye
los libros privados ni usa el recuperador híbrido local. Su rendimiento
no está medido por los informes de evaluación del corpus privado.

`/rag/search` funciona sin claves de proveedor. Para generar respuestas en
`/rag/chat` y `/rag/chat/stream`, configura una clave admitida en **Settings →
Secrets** del Space (`GEMINI_API_KEY`, `GLM_API_KEY`, `KIMI_API_KEY` u
`OPENAI_API_KEY`). Sin clave, se devuelven los fragmentos y una explicación
de la indisponibilidad de la generación. Nunca pongas estas claves en el
frontend ni en variables públicas del Space.

Se sincroniza automáticamente desde GitHub en cada push a `main`.
