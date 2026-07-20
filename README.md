# Dinero público → Resultados

**Trabajo de Fin de Máster — Máster en Data Science (Evolve), enero 2026.**
Autor: Daniel Ribes ([danribes@gmail.com](mailto:danribes@gmail.com))

**Demo en vivo:** [tfm-data-science-ufgfhpcvydyrswwzm7t6sz.streamlit.app](https://tfm-data-science-ufgfhpcvydyrswwzm7t6sz.streamlit.app/) — el dashboard completo (5 pestañas) desplegado desde este repo; cada push lo actualiza.

¿Qué obtiene cada país (y cada comunidad autónoma) a cambio de su gasto público? Este proyecto construye un **atlas de la evolución del gasto público en los siglos XX–XXI** (deuda, sanidad, pensiones, vivienda, salarios públicos, protección social…), un **modelo de rendimiento ajustado con incertidumbre** (GBM + intervalos conformales, nunca una "liga" de países) y un **simulador de escenarios fiscales** que proyecta consecuencias sin prescribir políticas.

El proyecto nació como un índice de asequibilidad de vivienda por CCAA y evolucionó hacia este programa más ambicioso. La transición completa, y cómo responde al feedback del tutor, está documentada en **[docs/entregas/anexo_transicion_proyecto.md](docs/entregas/anexo_transicion_proyecto.md)** — el análisis de vivienda sigue vivo dentro del programa como vista propia, con su pipeline ya construido.

## Documentos principales

La documentación está organizada en **documentos canónicos** y **cinco compendios temáticos**. El mapa completo está en **[docs/INDICE.md](docs/INDICE.md)**.

| Documento | Qué contiene |
|---|---|
| [docs/MEMORIA.md](docs/MEMORIA.md) | La memoria completa del TFM (resumen, datos, método, resultados, conclusiones) |
| [docs/PLAN_MAESTRO.md](docs/PLAN_MAESTRO.md) | Documento canónico de diseño: preguntas de investigación, método, fases, riesgos |
| [docs/entregas/](docs/entregas/) | Entregas del curso (01–04 + anexo transición) y feedback del tutor |
| [docs/GUIA_USUARIO.md](docs/GUIA_USUARIO.md) | **Cómo usar el sistema**: panel, catálogo de preguntas, guía ML/DL, despliegue, glosario |
| [docs/METODOLOGIA.md](docs/METODOLOGIA.md) | Cómo predice el sistema y la prueba de que la capa de datos/cálculo aporta los números |
| [docs/RESULTADOS_VIVIENDA.md](docs/RESULTADOS_VIVIENDA.md) | Bloque de vivienda: EDA, competición de modelos, pronóstico, demanda/suelo, señales, DL |
| [docs/RESULTADOS_FISCAL_BIENESTAR.md](docs/RESULTADOS_FISCAL_BIENESTAR.md) | Atlas, historia 1703–2025, gasto/ingresos, fronteras, pobreza, deuda, horizonte 50 años |
| [docs/DATOS.md](docs/DATOS.md) | Fuentes, catálogo del almacén (raw/processed/gold) y diccionarios de datos |
| [docs/RECONCILIACION_plan_maestro_vs_entregas.md](docs/RECONCILIACION_plan_maestro_vs_entregas.md) | Auditoría interna: coherencia plan ↔ entregas |

## Estructura del repositorio

```
connectors/    # extractores por fuente (INE, Eurostat, FMI-WEO, GMD/JST, GHED, UN DESA…)
               # contrato común en base.py: fetch() → tidy DataFrame; el crudo cae
               # SIEMPRE en storage/raw con fila de vintage (evidencia inmutable)
storage/
├── raw/       # descargas intactas + vintage_manifest.csv
├── processed/ # 67 datasets limpios (una fuente, un fichero)
└── gold/      # 23 datasets finales de consumo (paneles, pronósticos, fronteras, sobres 2070)
api/           # esqueleto FastAPI que sirve la capa gold (uvicorn main:app / docker compose up)
scripts/       # utilidades (generador del deck del plan)
docs/          # planes, diccionarios, entregas
_old/          # proyecto vivienda original completo (solo local; excluido del repo vía .gitignore)
```

## Reproducibilidad

- Cada conector es ejecutable de forma autónoma: `python -m connectors.ine`, `python -m connectors.eurostat_gov`, etc. (Python ≥ 3.10; `pandas` + `requests`).
- Nada entra en `storage/gold` sin pasar por `storage/raw` (evidencia) y `storage/processed` (limpieza trazable); `storage/raw/vintage_manifest.csv` registra fecha y URL de cada descarga.
- **Arranque garantizado con Docker** (la vía recomendada para replicar): `docker compose up --build` desde la raíz levanta los DOS servicios con la capa gold ya dentro de las imágenes — no requiere Python local ni descargar datos:
  - **Dashboard** en http://localhost:8501 (cinco pestañas: asequibilidad con abanico, atlas, funnel A1, simulador de deuda con sliders, horizonte 50 años con Monte Carlo), con healthcheck incluido.
  - **API** en http://localhost:8010 — endpoints: `/atlas`, `/century`, `/ccaa/affordability`, `/forecast/ccaa/{territorio}`, `/performance/health`, `/scenarios/debt`, `POST /scenario` (palancas r/g/pb), `/project/{pensions|health}`.
- Sin Docker: `cd api && pip install -r requirements.txt && GOLD_DIR=../storage/gold uvicorn main:app --reload` para la API; `pip install -r app/requirements.txt && streamlit run app/dashboard.py` para el dashboard.
- Publicación gratuita del dashboard: el repo es desplegable tal cual en Streamlit Community Cloud (share.streamlit.io → `app/dashboard.py`).

## Estado actual (2026-07-19)

**Sistema completo**, todo con protocolo pre-registrado, 91 tests y capa gold; dashboard publicado (enlace arriba).

1. **T1 — Forecasting CCAA**: [EDA](docs/RESULTADOS_VIVIENDA.md) → [baselines rolling-origin](docs/RESULTADOS_VIVIENDA.md) → cinco contests de candidatos ([clásicos](docs/RESULTADOS_VIVIENDA.md) · [demanda](docs/RESULTADOS_VIVIENDA.md) · [rutas DL](docs/RESULTADOS_VIVIENDA.md): el mejor llegó al empate 0,401 vs 0,395 y no se adoptó) → [test final de un solo uso](docs/RESULTADOS_VIVIENDA.md) → [producción drift + abanico empírico](docs/RESULTADOS_VIVIENDA.md).
2. **Atlas B1–B19** — [lectura guiada](docs/RESULTADOS_FISCAL_BIENESTAR.md) + [series históricas empalmadas 1703–2025](docs/RESULTADOS_FISCAL_BIENESTAR.md) con su trampa de perímetro medida.
3. **El triángulo fiscal** — [gasto por función (89 países) e ingresos por tipo (195), reconciliados 15/15](docs/RESULTADOS_FISCAL_BIENESTAR.md) + [marco de bienestar y pobreza infantil](docs/RESULTADOS_FISCAL_BIENESTAR.md).
4. **Fronteras de rendimiento** en tres dominios (salud, educación, bienestar/mortalidad infantil) con incertidumbre conformal — nunca rankings.
5. **D1 y el horizonte largo** — [menú de deuda 2024–2050](docs/RESULTADOS_FISCAL_BIENESTAR.md) → [sistema a 50 años](docs/RESULTADOS_FISCAL_BIENESTAR.md): Monte Carlo a 2070, panel within para bienestar y calibración de continuidad con la propia historia (~13 pp).
6. **Producto**: dashboard de 5 pestañas publicado + API + [asistente RAG citado](docs/GUIA_USUARIO.md); [despliegue y operación](docs/GUIA_USUARIO.md).

Trabajo declarado en curso: driver de oferta (visados, adopción solo con datos 2026+), revalidación del DL global con orígenes 2026+, respuesta del tutor pendiente.
