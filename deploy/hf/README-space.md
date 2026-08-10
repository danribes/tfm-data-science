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

La biblioteca RAG **no** está en este despliegue a propósito: el corpus
contiene libros con derechos de autor y vive sólo en la máquina local. Las
rutas `/rag/*` responden 503 explicándolo.

Se sincroniza automáticamente desde GitHub en cada push a `main`.
