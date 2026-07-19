# Dinero público → Resultados

**Trabajo de Fin de Máster — Máster en Data Science (Evolve), enero 2026.**
Autor: Daniel Ribes ([danribes@gmail.com](mailto:danribes@gmail.com))

¿Qué obtiene cada país (y cada comunidad autónoma) a cambio de su gasto público? Este proyecto construye un **atlas de la evolución del gasto público en los siglos XX–XXI** (deuda, sanidad, pensiones, vivienda, salarios públicos, protección social…), un **modelo de rendimiento ajustado con incertidumbre** (GBM + intervalos conformales, nunca una "liga" de países) y un **simulador de escenarios fiscales** que proyecta consecuencias sin prescribir políticas.

El proyecto nació como un índice de asequibilidad de vivienda por CCAA y evolucionó hacia este programa más ambicioso. La transición completa, y cómo responde al feedback del tutor, está documentada en **[docs/entregas/anexo_transicion_proyecto.md](docs/entregas/anexo_transicion_proyecto.md)** — el análisis de vivienda sigue vivo dentro del programa como vista propia, con su pipeline ya construido.

## Documentos principales

| Documento | Qué contiene |
|---|---|
| [docs/PLAN_MAESTRO.md](docs/PLAN_MAESTRO.md) | Documento canónico: 20 preguntas de investigación, método, capa ML/DL, fases F0–F9, crítica y riesgos |
| [docs/PLAN_MAESTRO_deck.pptx](docs/PLAN_MAESTRO_deck.pptx) | El plan en formato presentación |
| [docs/entregas/](docs/entregas/) | Entregas incrementales del curso (01 ideas · 02 datos · 03 modelo de datos · 04 análisis y modelado · anexo transición) + feedback del tutor |
| [docs/data_landscape.md](docs/data_landscape.md) | Inventario completo de fuentes de datos |
| [docs/data_dictionary_master.md](docs/data_dictionary_master.md) · [data_dictionary_vivienda.md](docs/data_dictionary_vivienda.md) | Diccionarios de datos (programa fiscal y vista vivienda) |
| [docs/RECONCILIACION_plan_maestro_vs_entregas.md](docs/RECONCILIACION_plan_maestro_vs_entregas.md) | Auditoría interna: coherencia plan ↔ entregas ↔ enunciados |
| [docs/arquitecturas_prediccion.md](docs/arquitecturas_prediccion.md) | Cómo se predicen los resultados: directa vs encadenada (two-stage) vs condicional, y la regla que gobierna la elección |

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
- **API** (sirve la capa gold + simulador interactivo): `cd api && pip install -r requirements.txt && GOLD_DIR=../storage/gold uvicorn main:app --reload`, o `docker compose up --build` desde la raíz. Endpoints: `/atlas`, `/century`, `/ccaa/affordability`, `/forecast/ccaa/{territorio}`, `/performance/health`, `/scenarios/debt`, `POST /scenario` (palancas r/g/pb), `/project/{pensions|health}`.
- **Dashboard MVP** (cuatro pestañas: asequibilidad con abanico, atlas, funnel A1, simulador de deuda con sliders): `streamlit run app/dashboard.py`.

## Estado actual (2026-07-18)

**Bloque analítico del TFM completo**, todo con protocolo pre-registrado, tests (35+) y capa gold:

1. **T1 — Forecasting CCAA** con disciplina completa: [EDA](docs/eda_vivienda.md) → [baselines + backtesting rolling-origin](docs/backtest_t1_baselines.md) → [candidatos](docs/candidatos_t1.md) (SARIMAX/LightGBM: resultado negativo pre-registrado a corto) → [test final de un solo uso](docs/test_final_t1.md) (hipótesis GBM refutada; el protocolo evitó publicar una predicción de desplome) → [pronóstico de producción con abanico empírico y escenarios](docs/forecast_t1_mvp.md) (`gold_forecast_ccaa.csv`).
2. **Atlas B1–B16** — [16 figuras con lectura guiada](docs/atlas.md): siglos XX–XXI, España vs mediana mundial/UE, incluida la inversión pública en vivienda SIEMPRE junto a la residencial total.
3. **A1 — Rendimiento ajustado** del gasto sanitario ([funnel de 164 países](docs/rendimiento_a1.md), `gold_rendimiento_pais.csv`): residual con intervalo conformal por grupo de renta, nunca una liga; España +2,7 ± 3,5 años.
4. **D1 — Simulador de escenarios de deuda** ([menú 2024–2050](docs/escenarios_d1.md), `gold_escenarios_deuda.csv`): aritmética r−g + presión demográfica del motor de proyección; la demografía domina cualquier palanca.

Trabajo declarado en curso: driver de oferta [`oferta_nueva`](docs/oferta_nueva.md) (permisos residenciales: señal adelantada r=0,57 a 11 trimestres; adopción solo con datos 2026+), pata provincial MITMA, reescritura F0.2 de entregas pendiente del visto bueno del tutor. Calendario en el [PLAN_MAESTRO](docs/PLAN_MAESTRO.md) §4.
