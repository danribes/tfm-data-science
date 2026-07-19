# Despliegue y operación del producto (2026-07-19)

Cómo se sirve el sistema, cómo se actualiza y cómo replicarlo. Tres modos
sobre el MISMO código y los MISMOS datos (la capa gold del repo).

## 1. Demo pública (Streamlit Community Cloud) — el modo por defecto

**https://tfm-data-science-ufgfhpcvydyrswwzm7t6sz.streamlit.app/**

- Sirve `app/dashboard.py` (5 pestañas) directamente desde el repo de GitHub.
- **Actualización automática**: cada `git push` a `main` redespliega (webhook
  de Streamlit instalado en el repo). No hay paso manual de publicación.
- Dependencias: `requirements.txt` de la RAÍZ (duplicado de
  `app/requirements.txt` — Streamlit Cloud solo lee la raíz).
- Comportamiento del plan gratuito: la app **duerme** tras ~12 h sin visitas;
  el primer visitante ve "waking up" ~30 s. Ante una demo importante,
  visitarla antes para calentarla.
- El dashboard NO depende de la API ni de claves: lee los CSV gold del propio
  repo. Por eso es desplegable tal cual.

## 2. Local con Docker — la vía de réplica garantizada

```bash
git clone https://github.com/danribes/tfm-data-science
cd tfm-data-science
docker compose up --build
```

- **Dashboard** → http://localhost:8501 · **API** → http://localhost:8010
- Las imágenes son autocontenidas: capa gold y figuras copiadas DENTRO en el
  build. No requiere Python local, ni paquetes, ni descargas de datos, ni red
  tras el build. Único requisito: Docker.
- Un clon antiguo se refresca con `git pull && docker compose up --build`
  (el contenedor queda congelado en el commit del build; la nube no).
- Healthcheck incluido (`/_stcore/health`); parar todo: `docker compose down`.
- Uso previsto además de la réplica: **modo sin-red para la defensa** (si la
  wifi falla, el sistema completo corre del portátil).

## 3. Local sin Docker (desarrollo)

```bash
pip install -r app/requirements.txt && streamlit run app/dashboard.py
cd api && pip install -r requirements.txt && GOLD_DIR=../storage/gold uvicorn main:app --reload
```

## Qué sirve cada superficie

| Superficie | Contenido | Fuente de datos |
|---|---|---|
| Dashboard (nube y contenedor) | 5 pestañas: asequibilidad con abanico empírico, atlas B1–B19, funnel A1, simulador de deuda con palancas, horizonte 50 años (Monte Carlo 2070 + sobres de bienestar + calibración) | CSV de `storage/gold/` leídos en local; sin API, sin claves |
| API FastAPI | `/atlas`, `/century`, `/ccaa/affordability`, `/forecast/ccaa/{t}`, `/performance/health`, `/scenarios/debt`, `POST /scenario`, `/project/{pensions\|health}` | capa gold + `api/models/*.json` (elasticidades, panel bienestar) |
| Asistente RAG (`app/rag_assistant.py`, solo local) | respuestas citadas sobre los 33 documentos del proyecto; `--llm` opcional con clave | `gold_corpus_manifest.csv` |

## Advertencias que viajan con el producto

Cada pestaña y cada endpoint llevan sus límites de método en la propia
respuesta (aproximación del ratio, drift como campeón por protocolo, funnel
no-ranking, aritmética determinista, sobres condicionales y calibración de
~13 pp). Publicar el dashboard no cambia el contrato: el sistema dice lo que
no sabe con la misma claridad que lo que sabe.

## Historial de despliegue (trazabilidad)

- Contenedorización dashboard+API: commit `22e7831`.
- `requirements.txt` raíz para Streamlit Cloud: `484e616`.
- Alta en Streamlit Community Cloud: manual (OAuth del autor), 2026-07-19;
  verificada con render headless (5 pestañas, datos vivos).
- URL en README: `7cff9a6`. Un túnel Cloudflare temporal usado el mismo día
  quedó retirado al entrar la nube.
