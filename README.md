# Dinero público → Resultados

**Trabajo de Fin de Máster — Máster en Data Science (Evolve), enero 2026.**
Autor: Daniel Ribes ([danribes@gmail.com](mailto:danribes@gmail.com))

**Demo en vivo:** [tfm-data-science-ufgfhpcvydyrswwzm7t6sz.streamlit.app](https://tfm-data-science-ufgfhpcvydyrswwzm7t6sz.streamlit.app/) — el dashboard completo (5 pestañas) desplegado desde este repo; cada push lo actualiza.

¿Qué obtiene cada país (y cada comunidad autónoma) a cambio de su gasto público? Este proyecto construye un **atlas de la evolución del gasto público en los siglos XX–XXI** (deuda, sanidad, pensiones, vivienda, salarios públicos, protección social…), un **modelo de rendimiento ajustado con incertidumbre** (GBM + intervalos conformales, nunca una "liga" de países) y un **simulador de escenarios fiscales** que proyecta consecuencias sin prescribir políticas.

El proyecto nació como un índice de asequibilidad de vivienda por CCAA y evolucionó hacia este programa más ambicioso. La transición completa, y cómo responde al feedback del tutor, está documentada en **[docs/entregas/anexo_transicion_proyecto.md](docs/entregas/anexo_transicion_proyecto.md)** — el análisis de vivienda sigue vivo dentro del programa como vista propia, con su pipeline ya construido.

## Documentos principales

| Documento | Qué contiene |
|---|---|
| [docs/PLAN_MAESTRO.md](docs/PLAN_MAESTRO.md) | Documento canónico: 20 preguntas de investigación, método, capa ML/DL, fases F0–F9, crítica y riesgos |
| [docs/PLAN_MAESTRO_deck.pptx](docs/PLAN_MAESTRO_deck.pptx) | El plan en formato presentación |
| [docs/entregas/](docs/entregas/) | Entregas incrementales del curso (01 ideas · 02 datos · 03 modelo de datos · 04 análisis y modelado · anexo transición) + feedback del tutor |
| [docs/data_landscape.md](docs/data_landscape.md) | Inventario completo de fuentes de datos |
| [docs/CATALOGO_DATOS.md](docs/CATALOGO_DATOS.md) | Catálogo del storage: fuentes y contenido clasificado por raw / processed / gold, con filas y años reales |
| [docs/Guia de Uso.md](docs/Guia%20de%20Uso.md) | Guía de uso: cómo funciona el dashboard y ejemplos de preguntas por escenario con la estimación real del modelo |
| [docs/Catalogo de Preguntas.md](docs/Catalogo%20de%20Preguntas.md) | Catálogo completo de preguntas que admite el modelo, por área, con respuesta real y qué esperar |
| [docs/data_dictionary_master.md](docs/data_dictionary_master.md) · [data_dictionary_vivienda.md](docs/data_dictionary_vivienda.md) | Diccionarios de datos (programa fiscal y vista vivienda) |
| [docs/RECONCILIACION_plan_maestro_vs_entregas.md](docs/RECONCILIACION_plan_maestro_vs_entregas.md) | Auditoría interna: coherencia plan ↔ entregas ↔ enunciados |
| [docs/arquitecturas_prediccion.md](docs/arquitecturas_prediccion.md) | Cómo se predicen los resultados: directa vs encadenada (two-stage) vs condicional, y la regla que gobierna la elección |
| [docs/bienestar_indicadores.md](docs/bienestar_indicadores.md) | Marco bienestar↔pobreza infantil (MPI/MODA): 7 bloques → 13 series + frontera ingreso público → bienestar objetivo |
| [docs/pobreza_infantil.md](docs/pobreza_infantil.md) | ¿Se predice la pobreza infantil? Absoluta sí (renta); relativa no del ciclo pero sí de la redistribución (palanca medida ~9 pp) |
| [docs/fiscal_breakdown.md](docs/fiscal_breakdown.md) | Desglose mundial de gasto (COFOG, 89 países) e ingresos por tipo (195) + reconciliación de fuentes 15/15 OK |
| [docs/fiscal_historia.md](docs/fiscal_historia.md) | Series históricas 1703–2025: denominador PIB verificado, trampa de perímetro medida y empalme canónico |
| [docs/demanda_suelo.md](docs/demanda_suelo.md) | Capas de demanda, crédito y suelo urbanizable (SIU + mercado de suelo) + cuarto contest negativo |
| [docs/proxy_adelantado.md](docs/proxy_adelantado.md) | Proxies adelantados: aceleración de población (→precio +10 trim.) e hipotecas (+1 trim.) — anticipan los giros |
| [docs/ppp_predictibilidad.md](docs/ppp_predictibilidad.md) | ¿Es predecible la PPA? Nivel sí (persistencia), crecimiento no; convergencia real verificada (3/4 ataques) pero de club, no global |
| [docs/vivienda_global.md](docs/vivienda_global.md) | Panel internacional de vivienda: precios reales (BIS 1971–), precio/renta (OCDE) y suelo artificial |
| [docs/dl_rutas.md](docs/dl_rutas.md) | Deep learning contra el protocolo: Chronos zero-shot y DL global entrenado en 1.760 series extranjeras (empate técnico) |
| [docs/Guia ML-DL.md](docs/Guia%20ML-DL.md) | Guía ML/DL: mapa de técnicas por módulo, el tooling con LLM (RAG, motores, consejo) y ejemplos de uso con Claude |
| [docs/ablacion_llm.md](docs/ablacion_llm.md) | Ablación LLM: prueba de que la capa ML/DL+RAG diferencia (LLM solo 3/12 vs LLM+sistema 11/12) + dónde vive el ML/DL |
| [docs/comparativa_llm_vs_modelo.md](docs/comparativa_llm_vs_modelo.md) | Comparativa detallada pregunta a pregunta: IA sola vs modelo completo (por qué difieren) |
| [docs/horizonte_50.md](docs/horizonte_50.md) | Sistema a 50 años: sobres condicionales de deuda (MC 2070) y bienestar, panel within y calibración con 300 años de historia |
| [docs/despliegue.md](docs/despliegue.md) | Despliegue y operación: demo pública, réplica Docker, modo sin-red y qué sirve cada superficie |
| [docs/glosario.md](docs/glosario.md) | Glosario de todas las siglas: instituciones, bases de datos, métodos y códigos de contabilidad nacional |

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
_old/          # proyecto vivienda original completo (trazabilidad; ver entrega 04)
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

1. **T1 — Forecasting CCAA**: [EDA](docs/eda_vivienda.md) → [baselines rolling-origin](docs/backtest_t1_baselines.md) → cinco contests de candidatos ([clásicos](docs/candidatos_t1.md) · [demanda](docs/demanda_suelo.md) · [rutas DL](docs/dl_rutas.md): el mejor llegó al empate 0,401 vs 0,395 y no se adoptó) → [test final de un solo uso](docs/test_final_t1.md) → [producción drift + abanico empírico](docs/forecast_t1_mvp.md).
2. **Atlas B1–B19** — [lectura guiada](docs/atlas.md) + [series históricas empalmadas 1703–2025](docs/fiscal_historia.md) con su trampa de perímetro medida.
3. **El triángulo fiscal** — [gasto por función (89 países) e ingresos por tipo (195), reconciliados 15/15](docs/fiscal_breakdown.md) + [marco de bienestar y pobreza infantil](docs/bienestar_indicadores.md).
4. **Fronteras de rendimiento** en tres dominios (salud, educación, bienestar/mortalidad infantil) con incertidumbre conformal — nunca rankings.
5. **D1 y el horizonte largo** — [menú de deuda 2024–2050](docs/escenarios_d1.md) → [sistema a 50 años](docs/horizonte_50.md): Monte Carlo a 2070, panel within para bienestar y calibración de continuidad con la propia historia (~13 pp).
6. **Producto**: dashboard de 5 pestañas publicado + API + [asistente RAG citado](docs/rag_asistente.md); [despliegue y operación](docs/despliegue.md).

Trabajo declarado en curso: driver de oferta (visados, adopción solo con datos 2026+), revalidación del DL global con orígenes 2026+, respuesta del tutor pendiente.
