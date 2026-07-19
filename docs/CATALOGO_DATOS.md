# Catálogo de datos — fuentes y contenido por capa

Inventario completo del `storage/` con las cifras reales del repositorio
(2026-07-19). Tres capas encadenadas: **raw** (descargas intactas, evidencia)
→ **processed** (una fuente, un fichero limpio) → **gold** (datasets finales de
consumo). Siglas: `docs/glosario.md`. Procedencia por URL y fecha:
`storage/raw/vintage_manifest.csv`.

| Capa | Ficheros | Tamaño | Qué es |
|---|---|---|---|
| `raw/` | 96 + manifest | 138 MB | Descargas sin tocar; cada una con fila de vintage (URL, fecha, bytes) |
| `processed/` | 67 CSV | 29 MB | Cada fuente limpiada a formato tidy por su conector |
| `gold/` | 22 CSV | 11 MB | Paneles, pronósticos, fronteras y sobres combinados por los análisis |

---

## 1. Fuentes (institución → contenido → capas)

| Fuente | Descargas raw | Contenido | Llega a gold vía |
|---|---|---|---|
| **INE** (España) | metadatos de series; datos por API JSON | IPV, IPC, salarios, compraventas, hipotecas, población trimestral CCAA | paneles trimestrales, asequibilidad, cuota teórica |
| **MITMA / Fomento** (España) | 25 XLS + 2 ZIP SIU | Licencias de obra, mercado de suelo (nº/valor/superficie/precio), valor tasado, stock urbanizable | suelo, driver de oferta, cuota teórica |
| **Eurostat** (UE) | 42 JSON | COFOG gasto, ingresos por tipo, deuda/intereses, población/proyecciones, AROPE/SILC, LUCAS, paro, reciclaje | atlas, triángulo fiscal, proyecciones, bienestar |
| **IMF / FMI** | 8 (WEO JSON, GMD `.dta`) + API | WEO totales fiscales, GMD historia larga, GFS-COFOG, WoRLD ingresos | totales fiscales, desglose mundial, historia, horizonte 50 |
| **World Bank** (WDI/ODA/WWBI/SPI/HLO) | API JSON (sin raw) | PIB pc, esperanza de vida, pobreza, mortalidad<5, nutrición, educación, servicios, empleo público | fronteras salud/educación/bienestar |
| **WHO / OMS** | `ghed.xlsx`, GHO | Gasto sanitario público/privado; obesidad/tabaquismo | frontera A1 salud |
| **OECD / OCDE** | 3 SDMX CSV | Precios de vivienda, suelo artificial, Global Revenue Statistics | vivienda global, reconciliación fiscal |
| **BIS** | 2 CSV | Precios residenciales nominal + real (ES desde 1971) | vivienda global |
| **ECB / BCE** | 2 CSV | Euríbor 12m, Bank Lending Survey (criterios de crédito vivienda) | cuota teórica, driver de crédito |
| **FHFA · Zillow · UK Land Registry** | 4 CSV | Índices de vivienda regionales EE. UU./UK | corpus de entrenamiento DL global |
| **JST Macrohistory** | `jst_r6.xlsx` | Niveles fiscales y de precios largos (18 países, 1870–) | empalme histórico, denominador PIB |
| **UN DESA** | `undesa_ims_2024.xlsx` | Stock internacional de migrantes | contexto demográfico |
| **Google Trends** | pytrends (vintage congelado) | Interés de búsqueda "comprar piso"/"hipoteca"/"alquiler" | driver de demanda (Tier 2) |

Procedencia registrada en el manifest: 141 descargas (75 MITMA, 42 Eurostat,
8 IMF, 4 INE-meta, 3 OECD, 2 BIS, 2 FHFA, 1 c/u ECB/Zillow/UK/MIVAU/Wayback).
Las fuentes por API JSON de gran volumen (World Bank, GHED, JST, UN DESA)
entran por `http_json`/xlsx sin fila de manifest — brecha declarada.

---

## 2. Capa RAW — descargas por fuente

**MITMA / Fomento** (`apps.fomento.gob.es`, `cdn.mivau.gob.es`, `web.archive.org`):
`mitma_licencias_100201..1930.xls` (19, licencias por CCAA) ·
`mitma_suelo_361/362/363/364_00500.xls` (nº/valor/superficie/precio de suelo) ·
`mitma_valor_tasado_35102000.xls` · `siu_clases_suelo_2025.zip` (CDN) ·
`siu_clases_suelo_2021.zip` (Wayback).

**Eurostat** (`ec.europa.eu`): `gov_10a_exp_{TE,D1,D3,D62,D9,P2,P51G}.json` ·
`rev_{TR,D2REC,D4REC,D5REC,D61REC,D7REC,D91REC,D39REC,P11_P12_P131}.json` ·
`gov_debt.json` · `gov_revenue_deficit.json` · `interest_paid.json` ·
`population.json` · `population_broad_age.json` · `proj_23ndbi.json` ·
`arope_ninos.json` · `arop_post.json` · `arop_pre_nopensions.json` ·
`silc_overburden.json` · `silc_overcrowding.json` · `lucas_artificial.json` ·
`recycling_rate.json` · `unemployment_eu.json` · `gini.json` ·
`avoidable_mortality.json` · `gdp_pc_pps.json` · `gfcf_dwellings.json` ·
`house_price_index_q.json` · `building_permits_q.json` · `social_protection_exp.json` ·
`pensions_oldage.json` · `emigration.json` · `immigration.json`.

**IMF** (`www.imf.org`, `api.imf.org`): `weo_{exp,rev,GGX_NGDP,GGR_NGDP,GGXCNL_NGDP,GGXWDG_NGDP}.json` ·
`GMD_2026_06.dta` + `gmd_chainlinked_gov{debt,exp,rev,tax,def}_GDP.dta` ·
GFS-COFOG y WoRLD (API, a `processed`).

**INE** (`servicios.ine.es`): `ine_{ipv_q,ipc,salarios}_series_meta.json` (metadatos; datos por API).

**OECD** (`sdmx.oecd.org`): `oecd_house_prices.csv` · `oecd_land_cover.csv` · (RSGLOBAL a processed).

**BIS** (`stats.bis.org`): `bis_spp_N.csv` (nominal) · `bis_spp_R.csv` (real).

**ECB** (`data-api.ecb.europa.eu`): `ecb_euribor12m.csv` · `ecb_bls_es_vivienda.csv`. (`bde_ti_1_7.csv` = serie BdE histórica, superada.)

**Regional HPI** (corpus DL): `fhfa_metro.csv` · `fhfa_state.csv` · `zillow_metro.csv` (`files.zillowstatic.com`) · `uk_avg.csv` (`publicdata.landregistry.gov.uk`).

**Ficheros grandes sin manifest**: `ghed.xlsx` (OMS, 38 MB) · `jst_r6.xlsx` (Macrohistory) · `undesa_ims_2024.xlsx` (ONU) · World Bank (`wdi_*`, `oda`, `wwbi`, `gho_*` — API).

---

## 3. Capa PROCESSED (67 · una fuente, un fichero)

Filas reales y cobertura temporal. Conector = `connectors/<fuente>.py`.

| Fichero | Filas | Años | Fuente / conector |
|---|---|---|---|
| `ine_ipv_q` | 4.312 | 2007–2026 | INE · IPV trimestral (objetivo T1) |
| `ine_ipc` | 5.880 | 2002–2026 | INE · IPC (deflactor) |
| `ine_salarios` | 5.508 | 2008–2024 | INE · salarios |
| `ine_compraventas_ccaa` | 4.660 | 2007–2026 | INE · compraventas (`demanda.py`) |
| `ine_hipotecas_ccaa` | 5.600 | 2003–2026 | INE · hipotecas (`demanda.py`) |
| `ine_poblacion_q_ccaa` | 2.440 | 1971–2026 | INE · población trimestral (`demanda.py`) |
| `mitma_licencias_ccaa` | 412 | 2000–2022 | MITMA · licencias (`mitma.py`) |
| `mitma_suelo_ccaa` | 6.929 | 2004–2026 | MITMA · mercado de suelo (`mitma.py`) |
| `mitma_valor_tasado_ccaa` | 377 | 2010–2014 | MITMA · valor tasado €/m² (`mitma.py`) |
| `siu_clases_suelo_ccaa` | 38 | 2021+2025 | MITMA-SIU · stock urbanizable (`mitma.py`) |
| `building_permits_q` | 3.979 | — | Eurostat · visados residenciales |
| `house_price_index_q` | 2.923 | — | Eurostat · HPI trimestral |
| `gov_10a_exp` | 159.524 | 1995–2023 | Eurostat · COFOG gasto (`eurostat_gov.py`) |
| `gov_debt` | 950 | 1995–2025 | Eurostat · deuda |
| `gov_revenue_deficit` | 5.250 | 1995–2025 | Eurostat · ingresos/déficit |
| `gov_revenue_detail` | 9.253 | 1995–2025 | Eurostat · componentes de ingreso (`gfs_global.py`) |
| `rev_TR … rev_P11_P12_P131` (9) | ~1.050 c/u | 1995–2025 | Eurostat · ingresos por partida |
| `interest_paid` | 1.050 | 1995–2025 | Eurostat · intereses |
| `population`, `population_broad_age` | 1.578 / 4.391 | 1995–2025 | Eurostat · población |
| `pensions_oldage`, `social_protection_exp` | 879 / 996 | 1995–2025 | Eurostat · gasto social |
| `arope_ninos` | 430 | 2015–2025 | Eurostat · pobreza infantil AROPE |
| `arop_post`, `arop_pre_nopensions` | 899 / 891 | 1995–2025 | Eurostat · AROPE pre/post transferencias |
| `silc_overburden`, `silc_overcrowding` | 828 / 840 | 2003–2025 | Eurostat-SILC · vivienda |
| `lucas_artificial` | 1.878 | 2009–2022 | Eurostat-LUCAS · suelo artificial |
| `unemployment_eu`, `gini`, `recycling_rate`, `avoidable_mortality` | 635/435/808/920 | var. | Eurostat · atlas |
| `gdp_pc_pps`, `gfcf_dwellings` | 1.227 / 1.309 | 1995–2025 | Eurostat · PIB pc, inversión residencial |
| `emigration`, `immigration` | 900 / 853 | 1995–2024 | Eurostat · migraciones |
| `weo_fiscal_totals` | 34.861 | 1800–2031 | IMF-WEO (`weo.py`) |
| `gmd_fiscal` | 66.058 | 1670–2030 | IMF-GMD (`gmd.py`) |
| `gfs_cofog_global` | 17.304 | 1972–2025 | IMF-GFS · gasto por función (`gfs_global.py`) |
| `world_revenue_global` | 61.634 | 1980–2024 | IMF-WoRLD · ingresos por tipo (`gfs_global.py`) |
| `jst_fiscal` | 2.565 | 1870–2020 | JST Macrohistory |
| `wdi_outcomes` | 14.454 | 1995–2023 | World Bank-WDI · e0, PIB pc |
| `wdi_policy` | 13.274 | 1995–2024 | World Bank · SPI, militar, educación, HLO, ODA |
| `wdi_extras` | 11.799 | 1995–2023 | World Bank · urbanización, paro |
| `wdi_bienestar` | 37.456 | 2000–2024 | World Bank · 13 series del marco MPI (`bienestar.py`) |
| `oda`, `wwbi` | 10.483 / 11.308 | var. | World Bank · ayuda, empleo público |
| `ghed` | 32.207 | 2000–2024 | OMS-GHED · gasto sanitario |
| `gho_confounders` | 10.792 | 1980–2030 | OMS-GHO · obesidad, tabaquismo |
| `oecd_precios_vivienda` | 28.137 | 1960–2026 | OCDE · precios y precio/renta (`vivienda_global.py`) |
| `oecd_suelo_artificial` | 2.856 | 2000–2022 | OCDE · land cover (`vivienda_global.py`) |
| `oecd_tax_global` | 23.339 | 1990–2024 | OCDE-RS · impuestos (`gfs_global.py`) |
| `bis_precios_vivienda` | 18.092 | 1927–2026 | BIS · precios residenciales (`vivienda_global.py`) |
| `hpi_regional_global` | 208.640 | 1968–2026 | FHFA+Zillow+UK · 1.760 series (`hpi_regional_global.py`) |
| `euribor_12m` | 390 | — | ECB · Euríbor |
| `bls_criterios_vivienda` | 94 | 2003–2026 | ECB-BLS · crédito (`credito.py`) |
| `gtrends_vivienda` | 3.525 | — | Google Trends (`tendencias.py`) |
| `un_migrant_stock` | 2.280 | 1990–2024 | UN DESA · migrantes |

---

## 4. Capa GOLD (22 · datasets finales)

Filas reales y análisis productor (`analysis/<script>.py`).

| Fichero | Filas | Años | Producido por | Contenido |
|---|---|---|---|---|
| `gold_ccaa_trimestral` | 1.540 | 2007–2026 | `gold.py` | Panel trimestral CCAA (IPV, IPC, salario, ratio) |
| `gold_asequibilidad_ccaa` | 306 | 2008–2024 | `gold.py` | Ratio de asequibilidad deflactado |
| `gold_forecast_ccaa` | 432 | — | `forecast_t1.py` | Pronóstico drift + abanico 80/95 × 3 escenarios salariales |
| `gold_cuota_teorica` | 17 | — | `cuota_teorica.py` | Esfuerzo hipotecario por CCAA (€/m² × IPV) |
| `gold_panel_anual` | 43.246 | 1980–2030 | `gold.py` | Panel anual multi-país (fiscal + outcomes) |
| `gold_panel_wide` | 2.126 | 1980–2030 | `gold.py` | Panel anual en formato ancho |
| `gold_century_fiscal` | 54.068 | 1900–2023 | `gold.py` | Series del siglo (atlas B1–B16) |
| `gold_projections` | 9.504 | 2023–2070 | `train_projection.py` | Proyecciones demográficas (6 variantes EUROPOP) |
| `gold_rendimiento_pais` | 164 | — | `rendimiento_a1.py` | Frontera A1 salud (funnel, conformal) |
| `gold_rendimiento_edu` | 157 | — | `expansion_dl.py` | Frontera A1 educación (HLO) |
| `gold_bienestar_pais` | 309 | — | `bienestar_a1.py` | Frontera ingreso→mortalidad<5 / stunting |
| `gold_tipologias_gasto` | 30 | — | `tipologias_a2.py` | A2: clusters de composición del gasto |
| `gold_suelo_ccaa` | 19 | — | `suelo_urbanizable.py` | Stock urbanizable + flujo de suelo |
| `gold_vivienda_global` | 279 | — | `vivienda_global.py` | Panel internacional precios/renta/suelo |
| `gold_fiscal_breakdown` | 108.099 | 1972–2025 | `fiscal_breakdown.py` | Gasto por función + ingresos por tipo, mundial |
| `gold_fiscal_reconciliation` | 15 | — | `fiscal_breakdown.py` | Los 15 checks de reconciliación entre fuentes |
| `gold_fiscal_historico` | 3.212 | 1700–2025 | `fiscal_historia.py` | Empalme gasto/ingreso 1703–2025 (18 países) |
| `gold_escenarios_deuda` | 162 | 2024–2050 | `escenarios_d1.py` | Menú de escenarios de deuda (aritmética r−g) |
| `gold_escenarios_deuda_mc` | 188 | 2024–2070 | `mc_d1.py` | Monte Carlo de deuda a 2070 (percentiles) |
| `gold_bienestar_50` | 18 | 2050–2070 | `bienestar_50.py` | Sobres condicionales de mortalidad<5 |
| `gold_backtest_50y` | 56 | — | `backtest_50y.py` | Calibración histórica de continuidad a 50 años |
| `gold_corpus_manifest` | 313 | — | `rag_assistant.py` | Índice del corpus RAG (35 documentos) |

---

## Notas de trazabilidad

- **Contrato de evidencia**: nada entra en `gold` sin pasar por `raw`
  (descarga intacta) y `processed` (limpieza trazable). El manifest registra
  URL y fecha de cada descarga estática.
- **Brecha declarada**: las fuentes por API de gran volumen (World Bank, GHED,
  JST, UN DESA) llegan por `http_json`/xlsx sin fila de manifest. Extensión
  pendiente si se quiere evidencia 100 %.
- **Docker**: la réplica contenedorizada solo necesita `gold` (copiada en la
  imagen); `raw`/`processed` quedan fuera (dockerignore) — el pipeline
  completo solo hace falta para regenerar desde cero.
