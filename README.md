# Dinero público → Resultados

**Trabajo de Fin de Máster — Máster en Data Science (Evolve), enero 2026.**
Autor: Daniel Ribes ([danribes@gmail.com](mailto:danribes@gmail.com))

¿Qué obtiene cada país (y cada comunidad autónoma) a cambio de su gasto público? Este proyecto construye un **atlas de la evolución del gasto público en los siglos XX–XXI** (deuda, sanidad, pensiones, vivienda, salarios públicos, protección social…), un **modelo de rendimiento ajustado con incertidumbre** (GBM + intervalos conformales, nunca una "liga" de países) y un **simulador de escenarios fiscales** que proyecta consecuencias sin prescribir políticas.

El proyecto nació como un índice de asequibilidad de vivienda por CCAA y evolucionó hacia este programa más ambicioso. La transición completa, y cómo responde al feedback del tutor, está documentada en **[docs/entregas/04_transicion_proyecto.md](docs/entregas/04_transicion_proyecto.md)** — el análisis de vivienda sigue vivo dentro del programa como vista propia, con su pipeline ya construido.

## Documentos principales

| Documento | Qué contiene |
|---|---|
| [docs/PLAN_MAESTRO.md](docs/PLAN_MAESTRO.md) | Documento canónico: 20 preguntas de investigación, método, capa ML/DL, fases F0–F9, crítica y riesgos |
| [docs/PLAN_MAESTRO_deck.pptx](docs/PLAN_MAESTRO_deck.pptx) | El plan en formato presentación |
| [docs/entregas/](docs/entregas/) | Entregas incrementales del curso (01 ideas · 02 datos · 03 modelo de datos · 04 transición) + feedback del tutor |
| [docs/data_landscape.md](docs/data_landscape.md) | Inventario completo de fuentes de datos |
| [docs/data_dictionary_master.md](docs/data_dictionary_master.md) · [data_dictionary_vivienda.md](docs/data_dictionary_vivienda.md) | Diccionarios de datos (programa fiscal y vista vivienda) |
| [docs/RECONCILIACION_plan_maestro_vs_entregas.md](docs/RECONCILIACION_plan_maestro_vs_entregas.md) | Auditoría interna: coherencia plan ↔ entregas ↔ enunciados |

## Estructura del repositorio

```
connectors/    # extractores por fuente (INE, Eurostat, FMI-WEO, GMD/JST, GHED, UN DESA…)
               # contrato común en base.py: fetch() → tidy DataFrame; el crudo cae
               # SIEMPRE en storage/raw con fila de vintage (evidencia inmutable)
storage/
├── raw/       # descargas intactas + vintage_manifest.csv
├── processed/ # 32 datasets limpios (una fuente, un fichero)
└── gold/      # 5 datasets finales de consumo (paneles anual/trimestral, siglo XX, proyecciones)
api/           # esqueleto FastAPI que sirve la capa gold (uvicorn main:app / docker compose up)
scripts/       # utilidades (generador del deck del plan)
docs/          # planes, diccionarios, entregas
_old/          # proyecto vivienda original completo (trazabilidad; ver entrega 04)
```

## Reproducibilidad

- Cada conector es ejecutable de forma autónoma: `python -m connectors.ine`, `python -m connectors.eurostat_gov`, etc. (Python ≥ 3.10; `pandas` + `requests`).
- Nada entra en `storage/gold` sin pasar por `storage/raw` (evidencia) y `storage/processed` (limpieza trazable); `storage/raw/vintage_manifest.csv` registra fecha y URL de cada descarga.
- La API local: `cd api && pip install -r requirements.txt && uvicorn main:app --reload`, o `docker compose up --build` desde la raíz.

## Estado actual (2026-07-18)

Extracción del pool de datos ≈ completa (32 processed, 5 gold, fuentes UE + globales + histórico 1870–2023), motor de proyección 2023–2070 (pensiones y sanidad × 6 variantes demográficas), esqueleto de API. Siguientes hitos: figuras del atlas de evolución (F2.1), modelo de rendimiento ajustado (F3.1) y forecasting CCAA (F4.1) — calendario en el [PLAN_MAESTRO](docs/PLAN_MAESTRO.md) §4.
