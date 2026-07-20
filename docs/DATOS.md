# Datos: fuentes, catálogo y diccionarios

De dónde sale cada dato y cómo está organizado: catálogo por capas (raw/processed/gold), inventario de fuentes, expansión del corpus y diccionarios de datos.

## Contenido

- [Catálogo de datos — fuentes y contenido por capa](#catálogo-de-datos-fuentes-y-contenido-por-capa)
- [Panorama de bases de datos fiscales y económicas (mundo)](#panorama-de-bases-de-datos-fiscales-y-económicas-mundo)
- [Expansión del corpus de evidencia (2026-07-19)](#expansión-del-corpus-de-evidencia-2026-07-19)
- [Diccionario maestro de datos — todas las familias de fuentes](#diccionario-maestro-de-datos-todas-las-familias-de-fuentes)
- [Diccionario de datos — Variante C (vivienda como consecuencias)](#diccionario-de-datos-variante-c-vivienda-como-consecuencias)

---

## Catálogo de datos — fuentes y contenido por capa

Inventario completo del `storage/` con las cifras reales del repositorio
(2026-07-19). Tres capas encadenadas: **raw** (descargas intactas, evidencia)
→ **processed** (una fuente, un fichero limpio) → **gold** (datasets finales de
consumo). Siglas: `docs/GUIA_USUARIO.md`. Procedencia por URL y fecha:
`storage/raw/vintage_manifest.csv`.

| Capa | Ficheros | Tamaño | Qué es |
|---|---|---|---|
| `raw/` | 96 + manifest | 138 MB | Descargas sin tocar; cada una con fila de vintage (URL, fecha, bytes) |
| `processed/` | 67 CSV | 29 MB | Cada fuente limpiada a formato tidy por su conector |
| `gold/` | 22 CSV | 11 MB | Paneles, pronósticos, fronteras y sobres combinados por los análisis |

---

### 1. Fuentes (institución → contenido → capas)

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

### 2. Capa RAW — descargas por fuente

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

### 3. Capa PROCESSED (67 · una fuente, un fichero)

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

### 4. Capa GOLD (22 · datasets finales)

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

### Notas de trazabilidad

- **Contrato de evidencia**: nada entra en `gold` sin pasar por `raw`
  (descarga intacta) y `processed` (limpieza trazable). El manifest registra
  URL y fecha de cada descarga estática.
- **Brecha declarada**: las fuentes por API de gran volumen (World Bank, GHED,
  JST, UN DESA) llegan por `http_json`/xlsx sin fila de manifest. Extensión
  pendiente si se quiere evidencia 100 %.
- **Docker**: la réplica contenedorizada solo necesita `gold` (copiada en la
  imagen); `raw`/`processed` quedan fuera (dockerignore) — el pipeline
  completo solo hace falta para regenerar desde cero.

---

## Panorama de bases de datos fiscales y económicas (mundo)

*Compilado 2026-07-17. Fuentes: análisis propio (Claude) + cross-check con Perplexity (web-grounded) y Gemini (vía agy). Los ítems marcados **[verificado en vivo]** fueron comprobados con peticiones HTTP reales el 2026-07-16/17 en esta sesión. ✓✓ = nombrado independientemente por ≥2 motores (cross-validado). MCP = conector ya operativo en el entorno de trabajo.*

**Ámbito:** gasto público y recaudación tributaria por país; capa de *números* (series estadísticas) y capa de *decisiones* (boletines legales, contratos, subvenciones).

---

### 1. Multilaterales — núcleo armonizado

| Base | Contenido | Cobertura | Acceso |
|---|---|---|---|
| IMF GFS (Government Finance Statistics) | gasto por función COFOG + ingresos por tipo | ~190 países | API (data.imf.org) · MCP |
| IMF WEO / Fiscal Monitor | agregados fiscales + proyecciones a 2031 | 190 | API · MCP |
| IMF WoRLD | ingresos longitudinal | ~193 | API |
| World Bank WDI | gasto/ingresos %PIB, salud, educación | ~190, 1960→ | API · MCP |
| World Bank BOOST | microdatos presupuestarios línea a línea | ~50 países (España NO) | descarga |
| WB Fiscal Space Database | espacio fiscal, deuda | 204 países, 1990→ | descarga |
| WB Quarterly Public Sector Debt | deuda pública trimestral | emergentes | API |
| OECD National Accounts COFOG (`DSD_NASEC10@DF_TABLE11`) | gasto por función | 34/38 OCDE (CAN/MEX/NZ/TUR no reportan) | API SDMX · MCP |
| **OECD Global Revenue Statistics** | impuestos por tipo y nivel de gobierno | **137 economías**, 1990→ | API/descarga |
| OECD Tax Database / SOCX / Gov at a Glance | tipos impositivos, protección social, indicadores | OCDE | API |
| **Eurostat `gov_10a_exp`** **[verificado en vivo]** | COFOG nivel 1 **y nivel 2** (GF0601 vivienda, obligatorio desde 2001) | UE+AELC, 1995–2023 | API JSON sin clave · MCP |
| Eurostat `gov_10dd` (EDP), ESSPROS, Taxation Trends | déficit/deuda, pensiones, impuestos | UE | API · MCP |
| ECB Data Portal | series fiscales zona euro | euro área | API |
| **WHO GHED** | gasto sanitario (público/privado/OOP) | ~190, 2000→ | xlsx directo |
| UNESCO UIS | gasto educativo | global | API |
| ILOSTAT | protección social | global | API |
| BIS | deuda, crédito | ~60 | API |
| UN SNA / UNdata | cuentas nacionales | global | API |
| **WB WWBI (Worldwide Bureaucracy Indicators)** **[verificado en vivo 2026-07-17: source=64, actualizado 2025-02]** | empleo público (% empleo), masa salarial %PIB, prima salarial público-privado, composición | ~200 países, 2000→ | misma API BM, `source=64`; derivado de encuestas (lagunas: p. ej. Alemania) |

### 2. Multilaterales regionales

| Base | Contenido | Cobertura | Fuente |
|---|---|---|---|
| CEPALSTAT (ECLAC) | fiscal LatAm | América Latina | propio |
| CIAT / Revenue Statistics in Latin America | impuestos detallados | 27+ países LatAm | Gemini |
| AfDB Africa Information Highway | gasto + ingresos | 54 países África, 1980→, API | Gemini |
| ATAF African Tax Outlook | estructura y administración tributaria | 38+ países África | Gemini |
| ADB Key Indicators (KIDB) | finanzas públicas Asia-Pacífico | 49 economías, API | Gemini |
| Arab Monetary Fund | presupuestos, ingresos oil/non-oil | 22 estados árabes | Gemini |
| GCC-Stat | ingresos/gastos Golfo | 6 países CCG, 2000→ | Gemini |

### 3. Académicas / especializadas / históricas

| Base | Contenido | Fuente |
|---|---|---|
| ICTD/UNU-WIDER Government Revenue Dataset (v2025, congelada; 1980–2023) | LA referencia global de ingresos tributarios, 196 países | propio ✓✓ |
| IMF Public Finances in Modern History | ingresos+gastos desde ~1800 | propio |
| Jordà-Schularick-Taylor Macrohistory | 18 países, 1870→ | propio |
| NBER Macrohistory | fiscal pre-1945 | Perplexity |
| SIPRI | gasto militar global, 1949→ | propio |
| CPDS (Comparative Political Data Set) | fiscal + político OCDE | propio |
| QoG (Quality of Government) | mega-merge ~100 fuentes | propio |
| GTED (Global Tax Expenditures Database) | recaudación perdida por beneficios fiscales, 100+ países | Gemini |
| WID.world | redistribución fiscal, transferencias, 1900→ | Gemini |
| Oxford CBT (Devereux-Griffith) | tipos efectivos de sociedades EATR/EMTR, 1983→ | Gemini |
| Tax Justice Network / Tax Foundation | paraísos, competitividad fiscal | Gemini |
| AidData | financiación al desarrollo (incl. préstamos chinos), nivel proyecto | Gemini |
| Our World in Data | agregador curado con citas | propio |

### 3-bis. Serie histórica larga — siglo XX (1900–1995)

*Añadido 2026-07-17 tras verificación en vivo. Regla de oro: los TOTALES (gasto, ingresos, déficit, deuda, militar) existen en continuo; el desglose FUNCIONAL (sanidad/educación/vivienda) muere antes de ~1970 — solo estimaciones en años-referencia. Series históricas = gobierno CENTRAL (ruptura de comparabilidad con el gobierno general moderno, ~1950–70).*

| Base | Contenido | Cobertura | Acceso |
|---|---|---|---|
| **Global Macro Database (GMD)** — Müller et al. **[verificado en vivo: release 2026_03]** | govexp, govrev, déficit, deuda + 42 vars macro | **243 países**, siglos→2024 | GitHub KMueller-Lab + `pip install global-macro-data` |
| **JST Macrohistory R6** **[verificado en vivo: España 1900/1930/1960/1990 extraída]** | revenue, expenditure, debtgdp + macro completo | 18 países avanzados (incl. ES), 1870–2020 | xlsx directo (macrohistory.net) |
| IMF Public Finances in Modern History | ingresos/gastos/déficit/deuda %PIB, gob. central | ~150 países, 1800→ | descarga IMF |
| Tanzi & Schuknecht (2000) | los cuadros canónicos "10%→45% PIB" con desglose funcional aproximado | avanzados, años-referencia 1870/1913/1937/1960/1980/1996 | tablas del libro (copiado manual, pequeño) |
| Flora, *State, Economy and Society* (GESIS histat) | desglose parcial por función (educación, social) | Europa occidental 1815–1975 | digitalizado en GESIS |
| **Carreras & Tafunell, Estadísticas históricas de España** **[verificado: página Fund. BBVA activa]** | capítulo de hacienda pública (series Comín ~1850–2000) | España s. XIX–XX | PDF/xlsx gratuito |
| US OMB Historical Tables / BoE "A Millennium of Macroeconomic Data" | gasto oficial de largo plazo | EEUU 1789→ / UK s. XVIII→ | gratuito |
| COW NMC / SIPRI | gasto militar | 1816→ / 1949→ | gratuito |
| Mitchell, International Historical Statistics | el clásico multi-país | global, s. XVIII→ | comercial (Palgrave; vía biblioteca) |

**Uso recomendado en el TFM:** prólogo descriptivo (tarea T2.0 de ambos planes) — una figura del arco del siglo; NUNCA modelado ML sobre el panel histórico (rupturas de comparabilidad).

### 3-ter. Fuentes para módulos bolt-on gasto→resultado (3ª ronda del consejo, códigos verificados)

*Añadido 2026-07-17. La verificación adversarial corrigió 5 códigos erróneos de la propia recomendación del consejo — lección: todo código pasa smoke-test antes de entrar en gold.*

| Fuente | Módulo | Detalle verificado | Trampas corregidas |
|---|---|---|---|
| **CEPEJ-STAT** + estudio CEPEJ del **EU Justice Scoreboard** | Justicia (STRONG unánime) | CEPEJ máquina-legible **2010–2022** (7 olas bienales, no 10); el estudio del Scoreboard es anual DESDE 2012 pero se nutre del cuestionario bienal + ad-hoc → **panel solo parcialmente anual** (doble-check Perplexity) | gasto judicial Eurostat = **GF0303** (=COFOG 03.3; GF0301 = policía). Nota: GF10xx = códigos COFOG (10.4 familia, 10.5 desempleo); ESSPROS usa códigos propios (FAM, UNEMPLOY) |
| **EU-SILC `ilc_li10`** + `ilc_li02` | Focalización de transferencias (STRONG) | AROP pre-transferencias con pensiones EXCLUIDAS vs post | `ilc_li09` incluye pensiones → contaminaría el constructo; familia = **GF1004** (GF1005 = desempleo) |
| **ESSPROS `spr_exp_type`/`spr_exp_func`** | gasto social no-pensiones | 1990–2024 | `spr_exp_sum` MUERTO (404, reestructurado) |
| **opentender.eu / DigiWhist** | calidad de contratación (feature transversal) | single-bidding + CRI Fazekas (validado peer-review, 2.8M contratos) | ⚠️ estado post-eForms (oct-2023) DISPUTADO entre verificaciones (GTI abr-2024 dice actualizado; Perplexity no lo confirma) → **verificar en build; fallback = calcular single-bidding directo de la TED API v3** (verificada en vivo en esta sesión); solo sobre-umbral; missingness=flag, nunca imputar |
| **Eurostat `cei_wm011`** (tasa) + `env_wasmun` (tonelajes por tratamiento) | reciclaje municipal (GF0501) | UE ~2000→ | la TASA de reciclaje es `cei_wm011` (indicador economía circular); `env_wasmun` son los tonelajes subyacentes — no confundir. GF05→emisiones = KILL (las emisiones las mueve el mix energético, no GF05) |
| **LMP (DG EMPL redisstat)** | ALMP (aparcado, split 2-2) | 1998→ (UE-15), categorías 2–7 activas estables desde 2006 | NO está en la API principal de Eurostat; normalizar por parado, nunca %PIB |
| Rechazados con motivo | — | cultura, defensa, DESI-como-módulo, green tagging, GTED, SOEs, absorción NGEU, I+D→patentes (WEAK: las patentes siguen al I+D empresarial — cuota pública minoritaria confirmada) | anexo "considerado y rechazado" del plan |

### 3-quater. Pilares del programa integral: SOEs, flujos entre países, migración, satélite

*Añadido 2026-07-17 al mapear la capa ML/DL del [PLAN_integral](PLAN_integral.md).*

| Base | Contenido | Cobertura | Acceso / nota |
|---|---|---|---|
| **World Bank BOS (Businesses of the State)** | censo mundial de empresas estatales: huella por país/sector | ~90 países, 2023→ | descarga abierta; NO incluye rendimiento — eso es construcción manual |
| OECD Ownership & Governance of SOEs | tamaño/gobernanza del sector SOE | OCDE+ | descarga |
| España: SEPI + IGAE sector público empresarial | cuentas del sector empresarial público | España | público |
| **OECD DAC CRS** | TODOS los flujos de ayuda oficial donante→receptor, nivel proyecto | mundial, 1973→ | descarga/API abierta — el estándar para F7 |
| AidData (ya en §3) | financiación china y no-DAC | 165+ receptores | abierto |
| **World Bank IDS** (International Debt Statistics) | deuda bilateral/multilateral entre países | mundial | API abierta |
| WB Bilateral Remittance Matrix | remesas país→país (contexto de flujos) | mundial | descarga |
| **EC Financial Transparency System + DG BUDG open data** | gasto del presupuesto UE por beneficiario/país + recursos propios | UE, 2007→ (FTS) | CSV/API abiertos — la "UE como gobierno" (F3) |
| cohesiondata.ec.europa.eu | fondos de cohesión + NGEU por país/programa | UE | portal + API abiertos |
| **UN DESA International Migrant Stock** | stock migrante por país origen×destino | mundial, 1990–2024 (quinquenal) | descarga abierta — núcleo de F8 |
| Eurostat `migr_imm/emi` + OECD International Migration Database | flujos anuales | Europa/OCDE | API |
| UNHCR Refugee Data | refugiados/desplazados | mundial | API abierta |
| **VIIRS / DMSP night-time lights** | luminosidad nocturna por satélite — proxy de actividad/infraestructura (Henderson et al.); procesable con CNN | mundial, DMSP 1992–2013 + VIIRS 2012→ | descarga abierta (NOAA/EOG) — el hueco DL honesto del tier global |
| *Tooling NLP (no es base de datos):* MarIA / RoBERTa-BNE | transformers en español preentrenados (BNE) para el extractor BOE (clasificación + NER) | — | HuggingFace, abiertos |

### 3-quinquies. Fuentes para el análisis de vivienda (Variante C)

*Añadido 2026-07-18 para [PLAN_vivienda_consecuencias](PLAN_vivienda_consecuencias.md). Las marcadas ✅ ya están verificadas (pipeline del TFM, comprobaciones 2026-07-07, o esta sesión).*

#### Núcleo España (ya en el pipeline del TFM)
| Fuente | Serie | Estado |
|---|---|---|
| INE wstempus | IPV anual 49300 + trimestral 76201; IPC 76136 (solo "Índice general" — bug conocido); salarios EES 28191 | ✅ pipeline operativo |
| Banco de España | Euríbor 12m (`ti_1_7.csv`, diario 1999→) | ✅ verificado |
| MITMA | precio suelo urbano (36400500, provincial 2004→); ICSC costes de construcción | ✅ verificado (XLS legado, parser xlrd) |
| Registradores ERI | % compraventas por extranjeros | ⚠️ WAF + PDF; driver V2 descartable |

#### Oferta privada de construcción (añadido 2026-07-18, revisión 1 de la Entrega 4)
| Fuente | Serie | Estado |
|---|---|---|
| Eurostat `sts_cobp_q` — permisos | Permisos de vivienda (nº, residencial excl. colectivas, I21, NSA), 39 geos, ES 1995Q1→ | ✅ EXTRAÍDO 2026-07-18 (`building_permits_q.csv`); señal adelantada r=0,57 a 11 trimestres — ver [oferta_nueva.md](RESULTADOS_VIVIENDA.md) |
| MITMA Boletín Estadístico — visados | Visados de dirección de obra nueva (Colegios de Aparejadores; mensual, provincial → CCAA) | ⏳ ruta identificada (mismo boletín que suelo/ICSC, parser xlrd reutilizable); daría la variación regional |
| MITMA — viviendas iniciadas y terminadas | Obra nueva libre y protegida (calificaciones); trimestral/anual, provincial | ⏳ misma ruta; retardo visado→terminación ~18–24 meses = feature adelantada para T1 |
| Eurostat `nama_10_an6` | FBCF por activo AN_111 "viviendas" %PIB (inversión residencial TOTAL; privada ≈ total − GF06 capital) | ⏳ mismo cliente Eurostat del pipeline; contexto obligatorio de la figura B3 del atlas |
| INE — hipotecas constituidas | Número e importe por CCAA (mensual) | Opcional: demanda financiada, contraste del canal Euríbor |

#### Gasto público en vivienda (la capa fiscal de la Variante C)
| Fuente | Serie | Estado |
|---|---|---|
| Eurostat `gov_10a_exp` | GF06 (L1, 1995→) y **GF0601+GF1006** (L2, 2001→) × na_item (capital vs corriente) | ✅ verificado en vivo (ES 0,5 vs UE 1,2 %PIB 2023; IT 4,4 superbonus) |
| INE COFOG + IGAE subsectores | gasto vivienda España/CCAA | ✅ verificados |
| Liquidaciones CCAA (Hacienda) | función vivienda por comunidad, ~2002→ online | página confirmada |
| BOE | Ley 12/2023, zonas tensionadas, planes estatales, PGE "Acceso vivienda" (3.476 M€ 2023 extraído) | ✅ verificado en vivo |
| MIVAU (Min. Vivienda) | Observatorio de Vivienda y Suelo; **SERPAVI** (índice de precios de alquiler); registro de zonas tensionadas | público |

#### Comparables internacionales (outcomes + precios)
| Fuente | Serie | Nota |
|---|---|---|
| **EU-SILC** `ilc_lvho07a` / `ilc_lvho05a` | sobrecarga de coste (>40% renta) / hacinamiento — los OUTCOMES de B2 | API sin clave, 2003→ |
| **OECD Affordable Housing Database** | stock de vivienda social, instrumentos de política, indicadores de asequibilidad por país | descarga abierta — el comparador de POLÍTICA de vivienda |
| **OECD Analytical House Prices** | **price-to-income y price-to-rent** por país, trimestral, décadas | API — el gemelo internacional del ratio de asequibilidad del TFM |
| **BIS Residential Property Prices** | precios de vivienda, ~60 países, series largas (algunas desde 1970) | descarga abierta |
| Eurostat `prc_hpi_q` | índice de precios de vivienda UE (respaldo del IPV con menos detalle) | API; ya identificado como backup en Entrega 3 |
| EMF Hypostat | mercados hipotecarios europeos, anuario | PDF/tablas gratuitas |
| Portales privados (Idealista/Fotocasa) | precios de oferta, alquiler | NO oficiales; API restringida — solo contexto, nunca núcleo |

#### Demografía/demanda (amplificador B4)
| Fuente | Serie | Nota |
|---|---|---|
| INE Estadística de Migraciones + padrón | flujos y stock por CCAA | ✅ (pipeline) |
| INE Censo 2021 + Encuesta Continua de Hogares | hogares, tenencia, tamaño | API/descarga |
| Eurostat `migr_imm/emi` + UN DESA | flujos/stock por país (tier UE) | §3-quater |

### 4. Subnacional (la mayor laguna del listado inicial)

| Base | Contenido | Cobertura | Fuente |
|---|---|---|---|
| **SNG-WOFI** (OECD+UCLG) | gasto/ingresos/deuda subnacional | 120–135 países | ✓✓ ambos |
| **OECD REGOFI** | finanzas de gobiernos regionales — **incluye CCAA en panel armonizado** | ~37 países, 550 regiones, 2010–2022 | Perplexity |
| OECD MUNIFI | finanzas municipales | ~120.000 municipios | Perplexity |
| IMF Fiscal Decentralization Dataset | cuotas subnacionales desde GFS | 86 economías, 1970s→ | Perplexity |
| US Census of Governments | todos los estados+locales EEUU, décadas | EEUU | Perplexity |
| Lincoln Institute FiSC | 150 mayores ciudades EEUU, 1977→ | EEUU | Gemini |
| Brasil SICONFI | todos los entes subnacionales | Brasil | propio |
| Indonesia DJPK | finanzas regionales | Indonesia | Gemini |

### 5. Portales nacionales

| País | Gasto | Impuestos | Nota |
|---|---|---|---|
| **España** | INE (`aappgastcofog95_23.xlsx` **[verificado: COFOG 1995–2023 en un fichero]**), IGAE series por subsector **[verificado; requiere User-Agent de navegador]**, PGE en BOE **[verificado: XML con 197 tablas parseables]** | AEAT informes anuales de recaudación | grado A− |
| **EEUU** | **USAspending.gov** (cada transacción federal), Treasury FiscalData API, BEA NIPA, FRED | IRS SOI | **A+ — el mejor del mundo** |
| **Reino Unido** | HM Treasury PESA (COFOG), ONS, OBR; legislation.gov.uk **[verificado: Supply & Appropriation Acts por API]** | HMRC | A |
| **Alemania** | Destatis Genesis API; **bundeshaushalt.de [verificado: presupuesto federal completo en un CSV]** | BMF | A |
| **Francia** | INSEE, budget.gouv.fr, data.gouv.fr (PLF) | DGFiP | A− (API Légifrance con clave OAuth gratuita) |
| **Italia** | ISTAT, OpenBDAP (RGS) | MEF | B+ (Gazzetta sin API) |
| **Países Bajos** | CBS StatLine API, rijksfinancien.nl | CBS | A |
| **Suecia** ✓✓ | ESV, SCB | Skatteverket | abierto, API |
| **Noruega** ✓✓ | DFØ Statsregnskapet, SSB | — | API/JSON |
| **Dinamarca** ✓✓ | StatBank Denmark | — | REST API |
| **Finlandia** ✓✓ | tutkibudjettia.fi (Valtiokonttori) | — | export abierto |
| **Corea del Sur** ✓✓ | **openfiscaldata.go.kr** (ejecución diaria, OpenAPI), KOSIS | NTS | A |
| **Japón** | e-Stat API, MOF | NTA | B+ |
| **China** | NBS (data.stats.gov.cn), MOF | limitado | **C — opaco, desfasado; investigadores usan CEIC ($)** |
| **India** | RBI DBIE, indiabudget.gov.in, data.gov.in, MOSPI | CBDT/GST | B− fragmentado |
| **México** ✓✓ | Transparencia Presupuestaria (SHCP) | SAT | abierto, CSV/API |
| **Brasil** | Tesouro Transparente, SICONFI | RFB | A− |
| **Sudáfrica** ✓✓ | vulekamali.gov.za (JSON API) | SARS Tax Statistics | abierto |
| **Indonesia** ✓✓ | Kemenkeu portal APBN | DJP | B |
| **Golfo** ✓✓ | Saudi MoF open data, UAE MoF/FCSC, Qatar PSA | — | 2016→ (post-IVA) |
| **Rusia** ✓✓ | budget.gov.ru, roskazna.gov.ru | FTS | ⚠️ series restringidas post-2022 |
| **Chile** | Dipres | SII | Perplexity |
| **Argentina** | ONP / Presupuesto Abierto | AFIP | Perplexity |
| **Ucrania** | portal MoF (muy granular, 2003→) | — | Perplexity |
| **Canadá / Australia** | StatCan / ABS | CRA / ATO | A |
| Otros (Perplexity) | Kazajistán, Filipinas DBM, Kenia, Taiwán DGBAS | — | variable |

### 6. Capa de decisiones (boletines legales, contratos, subvenciones)

*No existe en ninguna base estadística — es la laguna que haría novedoso un extractor. **Regla de decisión (verificada 2026-07-18): nunca extraer del BOE lo que Hacienda/IGAE publican como hoja de cálculo** — los IMPORTES aprobados y ejecutados están estructurados; del BOE solo es insustituible la capa de decisiones/eventos (instrumento legal + fecha + texto + rastro de prórrogas).*

**Importes presupuestarios estructurados (sustituyen la extracción BOE de cifras):**
| Fuente | Contenido | Estado |
|---|---|---|
| **SEPG/Hacienda — "PGE Consolidados" + "Series históricas"** | PGE APROBADOS en Excel (ejercicio en curso + 9 anteriores); años previos vía los "Libros" anuales del portal | ✅ verificado en vivo (datos.gob.es + sepg.pap 200) |
| **IGAE — ejecución presupuestaria mensual + liquidaciones** | presupuesto EJECUTADO (mejor que aprobado para análisis) | ✅ página verificada |
| **Hacienda — ejecución presupuestaria mensual de las CCAA** | ejecución regional mensual, dataset catalogado | ✅ catalogado datos.gob.es |

| Fuente | Contenido | Estado |
|---|---|---|
| **BOE (España)** | PGE + créditos + prórrogas + leyes CCAA (Cataluña/Madrid/Andalucía **[verificado]**); API de sumarios desde ≥1994 **[verificado]**; XML con tablas parseables (pesetas pre-2002) | A |
| BDNS / infosubvenciones.es | TODAS las subvenciones España desde 2016, estructurado + API | A |
| PLACSP | contratos públicos España, datos abiertos ~2012→ | A− |
| **TED API v3** **[verificado en vivo]** | contratos UE armonizados, 27 países, ~2006→ | A |
| opentender.eu | TED + nacional pre-limpiado, 28 jurisdicciones, CSV bulk | A (extracción ya hecha) |
| EU State Aid Transparency (TAM) | ayudas de estado | B+ |
| EUR-Lex / CELLAR | corpus legal UE, SPARQL | A |
| legislation.gov.uk **[verificado]** | leyes UK texto completo, XML/Atom | A+ |
| Bundesgesetzblatt (recht.bund.de) | boletín alemán, gratuito desde 2023 | B− |
| Légifrance/JORF (PISTE) | boletín francés, API con clave gratuita | B+ |
| Gazzetta Ufficiale (IT) | HTML sin API | C+ |
| officielebekendmakingen.nl / dre.pt | boletines NL/PT con API | B+ |

### 7. Agregadores

| Agregador | Nota |
|---|---|
| **DBnomics** (db.nomics.world) | **gratuito, una API sobre 80+ proveedores** (IMF, Eurostat, OECD, ECB, INSEE, Destatis, AMECO…) — el atajo "una sola base" |
| FRED | 800k+ series incl. internacionales, API limpia |
| OpenSpending (OKFN) | presupuestos multi-país centralizados, CSV/JSON/API |
| CEIC / Haver / Trading Economics | comerciales; solo justificados para China/emergentes |

### 8. Meta: transparencia y calidad fiscal (útiles como controles)

| Base | Contenido | Cobertura |
|---|---|---|
| Open Budget Survey (IBP) | puntuación de transparencia presupuestaria | 125+ países, bienal 2006→ |
| PEFA | indicadores de gestión financiera pública | 155+ países, 700+ evaluaciones |
| GIFT Data Portal / OFDP | datasets fiscales estandarizados | ~20 países |

---

### 9. Notas prácticas (gotchas comprobados en sesión)

1. **IGAE bloquea clientes no-navegador** — enviar User-Agent de Chrome; sin él la conexión se corta (HTTP 000). Datos públicos; throttling cortés.
2. **BOE**: API de sumarios `datosabiertos/api/boe/sumario/YYYYMMDD` (JSON) desde ≥1994; texto completo `diario_boe/xml.php?id=`. Cifras **en pesetas hasta PGE 2001** (conversión 166,386 pta/€). Años de prórroga sin ley nueva: 1996, 2012, 2019–20, 2024–26.
3. **OECD↔Eurostat COFOG**: la OCDE copia Eurostat para miembros UE → al fusionar, Eurostat = canónico para UE, OCDE solo para no-UE (evita duplicar país-años).
4. **INE**: `https://www.ine.es/daco/daco42/cne24/aappgastcofog95_23.xlsx` = COFOG España 1995–2023 completo, descarga directa, sin trucos.
5. **datos.gob.es apidata** = índice limpio de los datasets IGAE/INE (sin User-Agent especial).
6. Relevancia TFM: capa de números = servida (Eurostat/INE/IGAE/GHED, extracción trivial); capa de decisiones = inexistente como base de datos → un extractor BOE sería contribución original (línea "extractor de datos" avalada por el tutor en Entrega 1).

---

## Expansión del corpus de evidencia (2026-07-19)

Cierre de los conectores pendientes declarados tras la Entrega 4. Criterio: se
implementa todo lo alcanzable por rutas ya probadas (API pública, XLS estático);
lo que exige registro, scraping o dependencias geoespaciales se documenta como
bloqueado con su motivo, no se simula.

### 1. Conectores implementados en esta expansión

| Fuente | Serie | Cobertura | Archivo | Uso |
|---|---|---|---|---|
| MITMA BoletinOnline2 (35102000) | Valor tasado vivienda libre, €/m² por CCAA | 2010–2014, trimestral | `processed/mitma_valor_tasado_ccaa.csv` | Ancla de niveles para la cuota teórica (puente: × IPV propio de cada CCAA) |
| World Bank SPI (IQ.SPI.OVRL) | Statistical Performance Indicators | 2016– , ~170 países | `processed/wdi_policy.csv` | Auditoría residual⊥capacidad estadística del A1 (declarada en el PLAN, antes sin datos) |
| World Bank / SIPRI (MS.MIL.XPND.GD.ZS) | Gasto militar % PIB | 1960– | `processed/wdi_policy.csv` | Contexto de composición del gasto (atlas / RAG) |
| World Bank / UIS (SE.XPD.TOTL.GD.ZS) | Gasto educativo público % PIB | 1970– | `processed/wdi_policy.csv` | Input del módulo A1-educación |
| World Bank HCI (HD.HCI.HLOS) | Harmonized Learning Outcomes | ~170 países | `processed/wdi_policy.csv` | Outcome del módulo A1-educación (sustituye a PISA: cobertura mundial armonizada) |
| World Bank / OCDE-CAD (DC.ODA.TOTL.GN.ZS) | AOD neta donante % RNB | 1960– | `processed/wdi_policy.csv` | Contexto donante (RAG / atlas) |

Derivados analíticos nuevos:

- `analysis/cuota_teorica.py` → `gold/gold_cuota_teorica.csv`. Cuota hipotecaria
  teórica por CCAA (90 m², LTV 80 %, 25 años, Euríbor12m medio 2024 + 1 pp).
  Cierra el compromiso del PLAN_MAESTRO §7.2 con el tutor.
- `analysis/expansion_dl.py` → `gold/gold_rendimiento_edu.csv`. Módulo
  A1-educación (HLO ~ gasto + renta + urbanización) con contraste DL bajo LOOCV,
  y auditoría SPI del A1-salud. Resultados en `docs/MEMORIA.md` y en la salida
  del script.

### 2. Sobre "deep learning" en este corpus — decisión declarada

Se contrasta un MLP (perceptrón multicapa, 32×16, regularizado) como candidato
"deep" bajo el MISMO protocolo que el resto del proyecto: LOOCV y regla de
aceptación (batir al OLS por ≥10 % de MAE). No se usan arquitecturas mayores
porque el cuello de botella es n (~100–160 países por módulo), no la capacidad
del modelo: con esas muestras, más capas añaden varianza, no señal. La única vía
donde DL aporta de verdad valor diferencial (CNN sobre luces nocturnas para PIB
sin datos) queda bloqueada por dependencias (ver §3) y se declara como extensión.

### 3. Conectores bloqueados (motivo declarado)

| Fuente | Qué aportaría | Bloqueo |
|---|---|---|
| VIIRS/DMSP nightlights (Earth Engine / NOAA) | PIB estimado sin estadística oficial (CNN) | Registro Earth Engine + stack geoespacial (GDAL/rasterio) no presente; descarga masiva raster |
| UNU-WIDER GRD | Ingresos fiscales armonizados largos | Descarga manual con formulario (sin API) |
| CEPEJ (justicia) | Eficiencia judicial europea | Solo tablas HTML/PDF; requiere scraping frágil |
| Liquidaciones presupuestarias CCAA (MinHac) | Gasto autonómico funcional fino | Ficheros heterogéneos por año/CCAA sin esquema estable |
| Cohesion Open Data (UE) | Fondos de cohesión por región | API SPARQL compleja; prioridad baja para las preguntas del TFM |
| World Bank BOS (Bureaucracy) | Empleo/salarios públicos micro | Microdatos con licencia por país |
| BdE informes / INE PDFs | Corpus textual regulatorio | Pipeline PDF→md aparte; pospuesto (post-TFM, vía ai_library) |
| BOE | Series normativas | Post-TFM |
| GFS-COFOG global (IMF) | Gasto funcional mundial | Vía MCP IMF disponible pero pendiente de priorizar; COFOG-Eurostat ya cubre la UE |
| ECB Euríbor | Ya cubierto | Redundante: `processed/euribor_12m.csv` existe |
| GNI* (Irlanda) | PIB corregido | Ajuste puntual de un país; no cambia conclusiones |

### 4. Qué mejora con el corpus ampliado (medido, no prometido)

1. **Cuota teórica** (antes imposible: faltaba el nivel €/m²): esfuerzo nacional
   2024 = 41,6 % del salario bruto; Baleares 60,6 %, Madrid 56,0 %. El ratio
   índice y el esfuerzo real ordenan las CCAA con Spearman 0,79 — el ratio
   aproximado del panel era un buen proxy ordinal, y ahora hay medida en euros.
2. **A1-educación**: módulo nuevo completo (frontera gasto→aprendizaje) con
   residuales conformal por cuartil de renta, replicando el diseño del A1-salud.
3. **Auditoría SPI**: la comprobación residual⊥capacidad estadística declarada
   en el PLAN ya está ejecutada con datos reales (resultado en el script).
4. **Contraste DL honesto**: el MLP compite bajo las mismas reglas
   pre-registradas que GBM; el veredicto (gane o pierda) se publica sin retocar
   el criterio.

---

## Diccionario maestro de datos — todas las familias de fuentes

*v1, 2026-07-18. Generado por barrido paralelo de 9 agentes (94 sondas vivas, 0 errores). Provenance: **[V]** = esquema confirmado por sonda en vivo AHORA; **[D]** = documentado, pendiente de smoke-test en build; **[V-404]** = probado y NO existe (hallazgo). Complementa el [diccionario de vivienda](DATOS.md) (subconjunto Variante C con marcas ✔ de necesidad) y el [panorama](DATOS.md).*

**Regla de uso:** este documento es el CATALOGO de esquemas; la decisión de qué extraer vive en el diccionario de vivienda (§7: ~38 series). Ningún código [D] entra en gold sin pasar a [V] vía smoke-test.

---


### 1. Eurostat

#### EUROSTAT — Gobierno / finanzas públicas
| Dataset | Dimensiones (códigos clave) | Cobertura | Prov. | Trampa |
|---|---|---|---|---|
| gov_10a_exp (gasto AAPP por función COFOG) | freq=A; unit: MIO_EUR, MIO_NAC, PC_GDP, PC_TOT; sector: S13, S1311–S1314; cofog99 (80): TOTAL, GF01…GF10 + grupos GF0101…GF1009; na_item (32): TE, P2, P31, P32, P51G, D1, D3, D4, D62, D632…; geo; time | EU27+EFTA, aggr. EU27_2020/EA20 × 1995→ (probe devolvió time=2025) | [V] | lastTimePeriod puede devolver año con celdas vacías (COFOG suele parar en T-2); PC_TOT = % del gasto total, no del PIB |
| gov_10a_main (agregados principales AAPP) | freq=A; unit: MIO_EUR, MIO_NAC, PC_GDP; sector (7): S1, S13, S1311–S1314, S212; na_item (119): TE, TR, B9, B1G, P1, D2REC, D5REC, D61REC, D62PAY, D3PAY…; geo; time | EU27+EFTA × 1995→2025 | [V] | B9 = cap./nec. financiación (déficit); códigos REC/PAY duplican conceptos — filtrar dirección |
| gov_10dd_edpt1 (deuda PDE Maastricht) | freq=A; unit: MIO_EUR, MIO_NAC, PC_GDP; sector (6): S1, S13, S1311–S1314; na_item (18): GD, GD_F2, GD_F3, GD_F31, GD_F32, GD_F4, B9, B1GQ, D41PAY, IGL_F4_EA21/EA20/EA19/EU27_2020…; geo; time | EU27+EFTA × 1995→2025 | [V] | GD = deuda bruta consolidada; los IGL_F4_* cambian con la composición del euro — no mezclar vintages |
| gov_10a_sub | **404: "GOV_10A_SUB is not available for dissemination"** — no existe como dataflow; subsidios (D3/D3PAY) están en gov_10a_main y gov_10a_exp | — | [V-404] | Sustituir por na_item=D3 en gov_10a_main; smoke-test alternativa en build |

#### EUROSTAT — EU-SILC ingresos y vivienda
| Dataset | Dimensiones (códigos clave) | Cobertura | Prov. | Trampa |
|---|---|---|---|---|
| ilc_lvho07a (sobrecarga coste vivienda) | freq=A; unit=PC; rskpovth: TOTAL, A_60, B_60; age (17): TOTAL, Y_LT18, Y18-64, Y_GE65…; sex: T/M/F; geo; time | EU27+EFTA × ~2003→2025 | [V] | A_60/B_60 = por encima/debajo del 60% mediana (estatus pobreza), no umbral alternativo |
| ilc_lvho05a (tasa de hacinamiento) | freq=A; unit=PC; rskpovth: TOTAL, A_60, B_60; age (16): TOTAL, Y_LT18, Y18-64, Y_GE65…; sex: T/M/F; geo; time | EU27+EFTA × ~2003→2025 | [V] | Mismo esquema que lvho07a; series con ruptura metodológica SILC 2020/21 |
| ilc_li10 (pobreza anclada en el tiempo / dispersión) | freq=A; statinfo: MEAN_EI, MED_EI; rskpovth: B_40, B_50, B_60, B_70; sex; age (12): TOTAL, Y_LT16, Y16-64, Y_GE65…; unit=PC; geo; time | EU27+EFTA × 2003→2025 | [V] | Solo códigos B_ (bajo umbral); statinfo media vs mediana cambia el nivel |
| ilc_li02 (tasa riesgo de pobreza por umbral) | freq=A; statinfo: MEAN_EI, MED_EI; unit: PC, THS_PER; rskpovth (8): A_40…A_70, B_40…B_70; sex; age (33): TOTAL, Y_LT16, Y16-64, Y_GE65…; geo; time | EU27+EFTA × 1995/2003→2025 | [V] | Umbral estándar AROPE = B_60 + MED_EI; 33 grupos de edad se solapan (Y6-10 vs Y6-11) |
| ilc_di12 (Gini renta disponible) | freq=A; age: TOTAL, Y_LT18; statinfo=GINI_HND; geo; time | EU27+EFTA × 1995/2003→2025 | [V] | Ahora lleva dimensión age (TOTAL/Y_LT18) — pipelines antiguos sin age rompen; escala 0–100 |

#### EUROSTAT — Precios vivienda y migración
| Dataset | Dimensiones (códigos clave) | Cobertura | Prov. | Trampa |
|---|---|---|---|---|
| prc_hpi_q (índice precios vivienda, trimestral) | freq=Q; purchase: TOTAL, DW_NEW, DW_EXST; unit: I15_Q, I25_Q, RCH_Q, RCH_A; geo; time | EU+EFTA × 2005Q1→2026-Q1 (ES desde 2007) | [V] | Conviven dos bases índice (2015=100 y 2025=100); RCH_Q = var. intertrimestral, RCH_A = interanual |
| migr_imm1ctz (inmigración por ciudadanía) | freq=A; citizen (289): TOTAL, NAT, FOR, EU27_2020_FOR, país ISO-2…; agedef: REACH, COMPLET; age (27): TOTAL, Y_LT5…Y_GE85, grupos 5a; unit=NR; sex; geo; time | EU27+EFTA × 2008→2024 | [V] | Fijar SIEMPRE agedef (REACH vs COMPLET duplica filas); citizen tiene agregados solapados (EU15/EU25/EU27) |
| migr_emi2 (emigración por edad y sexo) | freq=A; age (103): TOTAL, Y_LT1, Y1…Y99 año a año; agedef: REACH, COMPLET; unit=NR; sex; geo; time | EU27+EFTA × 2008→2024 | [V] | Edad en años simples — usar age=TOTAL salvo pirámides; misma trampa agedef |

#### EUROSTAT — Protección social y residuos
| Dataset | Dimensiones (códigos clave) | Cobertura | Prov. | Trampa |
|---|---|---|---|---|
| spr_exp_type (gasto protección social ESSPROS) | freq=A; spdeps: TOTAL, SPR, ADM, OTH; unit (13): MIO_EUR, PC_GDP, PC_EXP, EUR_HAB, PPS_HAB, MEUR_KP15/KP10…; geo; time | EU27+EFTA × 1990→2024 | [V] | 13 unidades: elegir explícitamente (KP15 = precios constantes 2015); ESSPROS ≠ COFOG GF10 |
| cei_wm011 (tasa reciclaje residuos municipales) | freq=A; wst_oper=RCY; unit=PC; geo; time | EU27+EFTA × 2000→2024 | [V] | Indicador derivado de env_wasmun — una sola serie, sin más palancas |
| env_wasmun (residuos municipales por operación) | freq=A; wst_oper (10): GEN, TRT, RCY, RCY_M, RCY_C_D, RCV_E, DSP_L_OTH, DSP_I, DSP_I_RCV_E, PRP_REU; unit: KG_HAB, THS_T; geo; time | EU27+EFTA × 1995→2024 | [V] | GEN ≠ TRT (generado vs tratado); no sumar sub-operaciones con agregados |

#### EUROSTAT — Cuentas nacionales, demografía y salud
| Dataset | Dimensiones (códigos clave) | Cobertura | Prov. | Trampa |
|---|---|---|---|---|
| nama_10_pc (agregados per cápita) | freq=A; unit (12): CP_EUR_HAB, CP_PPS_EU27_2020_HAB, CLV_I20_HAB, CLV_PCH_PRE_HAB, PC_EU27_2020_HAB_MEUR_CP…; na_item (9): B1GQ, P3, P31_S14, P3_S13…; geo; time | EU27+EFTA+cand. × 1975→2025 | [V] | 12 unidades — CP (corrientes) vs CLV (volumen encadenado) vs %EU27; no mezclar bases I20/I15/I10 |
| demo_pjan (población 1 enero) | freq=A; unit=NR; age (103): TOTAL, Y_LT1, Y1…Y99, Y_OPEN, UNK; sex: T/M/F; geo; time | EU27+EFTA+cand. × 1960→2025 | [V] | Y_OPEN = 100+; UNK existe — TOTAL ≠ suma de edades si hay UNK |
| demo_mlexpec (esperanza de vida por edad) | freq=A; unit=YR; sex: T/M/F; age (97): Y_LT1, Y1…Y95…; geo; time | EU27+EFTA × 1960→2024 | [V] | Es e(x) a cada edad exacta — e(0) = age=Y_LT1, no TOTAL (no existe TOTAL) |
| hlth_cd_apr (mortalidad evitable/tratable) | freq=A; mortalit: TOTAL, PRVT, TRT; sex; icd10 (98): TOTAL, A00-A09, SEPSIS, C18-C21, I20-I25…; unit: NR, RT; geo; time | EU27+EFTA × 2011→2023 | [V] | RT = tasa estandarizada/100k (población <75); PRVT y TRT se solapan en algunas causas — no sumar a TOTAL |
| nama_10_a64_e (empleo por rama A*64) | freq=A; unit (6): THS_PER, THS_HW, THS_JOB, PCH_PRE_PER/HW/JOB; nace_r2 (96): TOTAL, A…U + detalle C10-C12…; na_item: EMP_DC, SAL_DC, SELF_DC; geo; time | EU27+EFTA × 1975→2025 | [V] | EMP_DC = SAL_DC + SELF_DC (concepto interior CN, ≠ LFS); THS_HW = miles de horas trabajadas |

### 2. FMI

#### IMF — WEO (World Economic Outlook)

| Dataset | Key dimensions (kwargs) | Example codes | Coverage | Prov. | Trap/note |
|---|---|---|---|---|---|
| `WEO` | `country`, `indicator`, `frequency` | country: ISO3 `ESP`; indicator: `NGDP`, `NGDP_R`, `NGDP_RPCH`, `NGDPD`, `NGDPDPC`, `NGDP_D`, `PPPGDP`, `PPPPC`, `PPPSH`, `GGXWDG`, `GGXWDG_NGDP`, `GGXWDN_NGDP`, `DS_NGDPD`; freq: `A` | ~196 economies + aggregates; annual ~1980→forecast horizon (+5y) [D] | [V] | Units baked into indicator code (no unit dim): `_NGDP`=%GDP, `D` suffix=USD, `PC`=per-capita, `PCH`=%change. Vintage DBs exist as separate ids (`*_VINTAGE` pattern). |

#### IMF — GFS family (data.imf.org, new API)

All annual GFS presentations share the SAME 6 dimensions: `country`, `sector`, `gfs_grp`, `indicator`, `type_of_transformation`, `frequency`.

| Dataset | Dimension example codes | Coverage | Prov. | Trap/note |
|---|---|---|---|---|
| `GFS_COFOG` (Expenditures by Function) | sector: `S13` gen gov, `S131`, `S13O/R/T/P` (except-X variants); gfs_grp: `G2MF` Expenditure-by-function; indicator: `GF07_T` Health, `GF0740_T` Public health svcs, `GF075_T` R&D Health (COFOG divisions `GF01..GF10` + `_T` suffix); transf: `XDC`, `POGDP_PT`, `POTO_PT`; freq: `A` | Global; annual ~1972→latest [D] | [V] | COFOG codes carry `_T` (Transactions) suffix; unit lives in `type_of_transformation`, NOT the indicator. Sector list is huge (13.7KB) — filter with `search`. |
| `GFS_SOO` (Statement of Operations) | indicator: `G1_T` Revenue, `G2_T` Expense, `G2G_T`, `G28_T`; cash-basis twins `G2_TCB_CAB`, `G28_TCB_CAB` | idem | [V] | Accrual vs cash are SEPARATE indicator codes (`_TCB_CAB` = cash basis). |
| `GFS_BS` (Balance Sheet) | gfs_grp: `BS`, `BSA`, `BSL`, `BSN` | idem | [V] | Same 6-dim schema confirmed live. |
| `GFS_SSUC` (Sources/Uses of Cash) | gfs_grp: `G1`/`G2` cash items | idem | [V] id listed; dims [D] | Assume same 6-dim schema; smoke-test. |
| `GFS_SOEF` (Other Economic Flows) | gfs_grp: `OEF`, `HGL`, `OCVA` | idem | [V] id listed; dims [D] | idem. |
| `GFS_SFCP` (Stocks/Flows by Counterparty) | counterparty splits | idem | [V] id listed; dims [D] | idem. |
| `QGFS` (Quarterly GFS) | dims: `country`, `accounts`, `sector`, `indicator`, `frequency`; accounts: `SOO`, `SOEF`, `BS`/`BSGFS`, `COFOG`, `SSUC`, `SFCP`; freq: `Q` | Global subset; quarterly [D] | [V] | Different schema from annual GFS: statement selected via `accounts` dim, no `gfs_grp`/`type_of_transformation`. Monthly vintage ids exist: `QGFS_2026_JAN/FEB/APR/MAY_VINTAGE`. |

#### IMF — related fiscal DBs found in same probe

| Dataset | Notes | Prov. |
|---|---|---|
| `FM` (Fiscal Monitor) | Vintage twin `FM_2025_OCT_VINTAGE`; WEO-style fiscal aggregates | [V] id only |
| `FD` (Fiscal Decentralization) | Sub-national fiscal shares | [V] id only |
| `GENENVPROEXP` | Gov environmental protection expenditures (COFOG 05 slice) | [V] id only |

#### Cross-cutting traps

| Item | Note |
|---|---|
| `frequency` codelist | 226 codes returned (A, Q, M, D, W, A2…_Z) but only `A` (annual GFS/WEO) and `Q` (QGFS) are populated in practice — don't enumerate. |
| MCP access | Tools: `imf_list_databases` / `imf_search_databases` / `imf_get_parameter_defs` / `imf_get_parameter_codes` / `imf_fetch_data`; ~155 DBs on new data.imf.org API (old SDMX 2.1 dataflow ids like `GFSCOFOG`, `WEO:xxx` do NOT apply). |
| Country codes | New API uses ISO3 (`ESP`) — old IMF SDMX used ISO2/numeric; remap at build. |

### 3. Banco Mundial

#### WDI — World Development Indicators (source=2)

| Indicator | Name (as returned) | Coverage | Prov | Note |
|---|---|---|---|---|
| NY.GDP.PCAP.PP.KD | GDP per capita, PPP (constant 2021 international $) | ~217 econ + aggregates; annual 1990–2025 | [V] | Rebased to 2021 PPP — old "2017 intl $" series name is gone |
| SP.POP.TOTL | Population, total | ~217 econ; 1960–2025 | [V] | — |
| SI.POV.GINI | Gini index | ~170 econ; sparse/irregular years | [V] | Survey-year gaps; use `mrnev` not `mrv` for latest non-null |
| SP.DYN.LE00.IN | Life expectancy at birth, total (years) | ~217 econ; 1960–2023 | [V] | — |
| SH.DYN.MORT | Mortality rate, under-5 (per 1,000 live births) | ~195 econ; 1960–2023 | [V] | — |

Data-record fields confirmed live: `indicator{id,value}, country{id,value}, countryiso3code, date, value, unit, obs_status, decimal` [V]. Response = JSON array `[metadata, data]`; page 1 is metadata — always index `[1]`.

#### WWBI — Worldwide Bureaucracy Indicators (source=64, 302 indicators [V])

| Indicator | Name | Coverage | Prov | Note |
|---|---|---|---|---|
| BI.EMP.TOTL.PB.ZS | Public sector employment, share of total employment | ~200 econ; ~2000–2022 | [V] | — |
| BI.WAG.TOTL.GD.ZS | Wage bill as % of GDP | idem | [V] | — |
| BI.WAG.TOTL.PB.ZS | Wage bill as % of Public Expenditure | idem | [V] | — |
| BI.WAG.PREM.PB | Public sector wage premium (vs formal wage employees) | idem | [V] | Premium family also has .GP (by gender) variants [D] |
| BI.EMP.FRML.HE.PB.ZS | Health workers, share of public formal employees | idem | [V] | — |
| BI.EMP.FRML.TS.PB.ZS | Teachers, share of public formal employees | idem | [V] | — |

#### Sources registry (api.worldbank.org/v2/sources) [V]

| Source id | Name | Note |
|---|---|---|
| 2 | World Development Indicators | core |
| 3 | Worldwide Governance Indicators | new GOV_WGI_* codes (see below) |
| 6 | International Debt Statistics | 577 indicators [V]; DT.* debt family; debtor LMICs only (~120), 1970–2032 incl. projections [D] |
| 81 | International Debt Statistics: DSSI | separate DSSI slice |
| 83 | Statistical Performance Indicators (SPI) | 72 indicators [V]; SPI.D1..D5 pillar codes + SPI.INDEX [D]; ~2016+ |
| 63 | Human Capital Index | hosts HLO (below) |
| 64 | Worldwide Bureaucracy Indicators | 302 indicators [V] |
| 57 | WDI Database Archives | where legacy WGI codes now live — trap |

#### WGI — six governance dimensions

| Legacy code (resolves, src=57) | Source-3 code [V] | Dimension | Coverage | Prov |
|---|---|---|---|---|
| CC.EST | GOV_WGI_CC.EST | Control of Corruption | ~214 econ; 1996–2023 | [V] |
| GE.EST | GOV_WGI_GE.EST | Government Effectiveness | idem | [V] |
| PV.EST | GOV_WGI_PV.EST | Political Stability / Absence of Violence | idem | [V] |
| RQ.EST | GOV_WGI_RQ.EST | Regulatory Quality | idem | [V] |
| RL.EST | GOV_WGI_RL.EST | Rule of Law | idem | [V] |
| VA.EST | GOV_WGI_VA.EST | Voice and Accountability | idem | [V] |

Trap: source=3 was recoded — 36 indicators = 6 dims × suffixes {.EST estimate −2.5..+2.5, .SC score 0–100, .SC_LB/.SC_UB 90% CI, .SE, .SR n-sources} [V]. Bare `CC.EST` etc. still resolve but are tagged source 57 (Archives); for source-scoped queries use the `GOV_WGI_` prefix.

#### HLO — Harmonized Learning Outcomes (under HCI, source=63)

| Indicator | Name | Coverage | Prov | Note |
|---|---|---|---|---|
| HD.HCI.HLOS | Harmonized Test Scores | ~174 econ; HCI rounds (2010/2017/2018/2020) | [V] | Exists; sex splits HD.HCI.HLOS.FE / .MA [D] |
| HD.HCI.OVRL | Human Capital Index (scale 0-1) | idem | [V] | — |
| HD.HCI.HLO, LO.HLO.OVRL | — | — | [V-neg] | Do NOT resolve (404/empty) — don't use |

### 4. OCDE

#### OECD — Gasto público COFOG (National Accounts Table 11)
| Dataset | Key dimensions (codes) | Coverage | Prov. | Trap/note |
|---|---|---|---|---|
| `OECD.SDD.NAD:DSD_NASEC10@DF_TABLE11` v1.1 — Annual government expenditure by function (COFOG) | FREQ(A) · REF_AREA(469: AUS,AUT,BEL…) · SECTOR(S13,S1311–S1314,_Z) · COUNTERPART_SECTOR · ACCOUNTING_ENTRY(D) · TRANSACTION(20: P3,P31,P32,P5,P51G,D1,D3,D4,D62,D632,D6M,D7…) · INSTR_ASSET(_Z) · EXPENDITURE=CL_COFOG(81: _T,GF01…GF10 + 2-digit GF0101…) · UNIT_MEASURE(XDC) · VALUATION(S) · PRICE_BASE(V) · TRANSFORMATION(N) · TABLE_IDENTIFIER(T1100) · TIME_PERIOD | OECD+accession, annual (~1995→) | [V] | 14 dims, most single-valued — pin all fillers (`A.{cc}.S13.….T1100`) or queries over-match; national currency only (XDC), compute %GDP yourself. MCP tool rejects "@" in IDs — use raw SDMX curl. |

#### OECD — Revenue Statistics (Global)
| Dataset | Key dimensions (codes) | Coverage | Prov. | Trap/note |
|---|---|---|---|---|
| `OECD.CTP.TPS:DSD_REV_COMP_GLOBAL@DF_RSGLOBAL` v2.1 — Global Revenue Statistics, comparative tax revenues | REF_AREA(560) · MEASURE(TAX_REV,NONTAX_REV,TAX_NONTAX_REV,B1GQ_V,CC) · SECTOR(216: S13 + subsectors) · STANDARD_REVENUE=CL_STANDARD_REVENUE(118: _T,T_1000,T_1100,T_1110,T_1120,T_1200,T_2000,T_3000,T_4000,T_5000,T_6000…) · CTRY_SPECIFIC_REVENUE(_T) · UNIT_MEASURE(USD,XDC,PT_B1GQ,PT_OTR_REV_CAT,PT_OTR_SECTOR) · FREQ(A) · TIME_PERIOD | ~130 economies (OECD+LAC+Africa+Asia-Pacific), annual 1990→ | [V] | OECD tax classification uses `T_` prefix (T_1000 income, T_2000 SSC, T_5000 goods&services); shares vs GDP = UNIT_MEASURE=PT_B1GQ, no separate transformation dim. |

#### OECD — SOCX gasto social
| Dataset | Key dimensions (codes) | Coverage | Prov. | Trap/note |
|---|---|---|---|---|
| `SOCX_AGG` (MCP alias; canonical `OECD.ELS.SPD:DSD_SOCX_AGG@DF_SOCX_AGG`) — Social Expenditure aggregates | REF_AREA(OECD38 + ROU,PER,HRV,BGR,OECD,WXOECD) · FREQ(A) · MEASURE(SOCX) · UNIT_MEASURE(PT_B1GQ, PT_OTE_S13, XDC, USD_PPP_PS) · EXPEND_SOURCE(ES10 public, ES20 mandatory-private, ES30 voluntary-private, ES40 net-public, ES50 net-total, ES10_20, ES20_30) · SPENDING_TYPE(_T,C cash,K in-kind) · PROGRAMME_TYPE(50 codes: TP11 old-age, TP21 survivors, TP31 incapacity, TP41 health, TP51 family, TP60 ALMP, TP71 unemployment, TP82 housing, TP91 other + 3-digit leaves) · PRICE_BASE(V,Q,_Z) · TIME_PERIOD | OECD + few non-OECD, annual 1980→~2024 (detail lags ~2yr) | [V] | Programme hierarchy mixes 2- and 3-digit codes — sum only one level or double-count; TP60 ALMP here is expenditure-only (participants live in LMP dataset below). |

#### OECD — Analytical house prices
| Dataset | Key dimensions (codes) | Coverage | Prov. | Trap/note |
|---|---|---|---|---|
| `OECD.ECO.MPD:DSD_AN_HOUSE_PRICES@DF_HOUSE_PRICES` v1.0 — Analytical house price indicators | REF_AREA(447: countries + OECD/EA aggs) · FREQ(A,Q) · MEASURE(RHP real, HPI nominal, RPI rent, HPI_RPI price-to-rent, HPI_RPI_AVG, HPI_YDH price-to-income, HPI_YDH_AVG) · UNIT_MEASURE(shared 841-code list; effectively IX index 2015=100) · TIME_PERIOD | OECD+, quarterly & annual, ~1970→ | [V] | Ratio measures (`*_AVG`) are deviations from LR average, not levels; MCP `RPPI` alias returns stub dims ("varies") — use raw SDMX. |

#### OECD — ALMP / Labour market programmes
| Dataset | Key dimensions (codes) | Coverage | Prov. | Trap/note |
|---|---|---|---|---|
| `OECD.ELS.JAI:DSD_LMP@DF_LMP` v1.0 — Labour market programmes: expenditure & participants | REF_AREA(505) · MEASURE(EXP expenditure, STO participant stocks) · PROGRAMME=CL_PROGRAMME_LMP(36: LMP_10 PES/admin, LMP_20 training, LMP_40 employment incentives, LMP_50 sheltered/supported, LMP_60 direct job creation, LMP_70 start-up, LMP_80 out-of-work income maintenance, LMP_90 early retirement, _T, aggs LMP_10T70 active / LMP_80_90 passive) · UNIT_MEASURE(PS persons, XDC, PT_LF %labour-force, PT_B1GQ %GDP) · TIME_PERIOD | OECD+EU, annual ~1985/2004→ | [V] | Active-vs-passive split = LMP_10T70 vs LMP_80_90, don't sum categories across it; STO participants only valid with UNIT_MEASURE=PS or PT_LF. |

#### OECD — International Migration Database
| Dataset | Key dimensions (codes) | Coverage | Prov. | Trap/note |
|---|---|---|---|---|
| `OECD.ELS.IMD:DSD_MIG@DF_MIG` v1.0 — International Migration Database | REF_AREA(505) · CITIZENSHIP(same CL_AREA, 505 — country of origin/nationality) · FREQ(A) · MEASURE(B11 inflows foreign pop, B12 outflows, B13 asylum inflows, B15 stocks foreign pop, B16 nationality acquisitions by former nationality) · SEX(F,_T — no M code exposed) · BIRTH_PLACE(_Z) · EDUCATION_LEV(_Z) · UNIT_MEASURE(PS) · TIME_PERIOD | OECD destinations × world origins, annual ~2000→ | [V] | Agency is `OECD.ELS.IMD` (probes under ELS.JAI/ELS.MIG 404 — resolve via `dataflow/all/`); SEX list has F and _T only; MCP `MIG` alias returns stub dims — use raw SDMX; flows are national-definition, not harmonised across countries. |

### 5. OMS / UNESCO / OIT

#### WHO GHED — Global Health Expenditure Database (via GHO OData, SHA-2011)

| Item | Detail | Prov |
|---|---|---|
| Endpoint | `https://ghoapi.azureedge.net/api/{IndicatorCode}` — OData; row schema returned live: `IndicatorCode, SpatialDimType, SpatialDim` (ISO3), `ParentLocationCode, TimeDim` (year), `Dim1Type/Dim1–Dim3, Value, NumericValue, Low, High, Date` | [V] |
| % aggregates | `GHED_CHEGDP_SHA2011` (CHE %GDP), `GHED_GGHE-DCHE_SHA2011`, `GHED_GGHE-DGDP_SHA2011`, `GHED_GGHE-DGGE_SHA2011` (govt %GGE), `GHED_PVT-DCHE_SHA2011`, `GHED_OOPSCHE_SHA2011`, `GHED_EXTCHE_SHA2011` | [V] |
| Per-capita | `GHED_CHE_pc_US_SHA2011`, `GHED_CHE_pc_PPP_SHA2011`, `GHED_GGHE-D_pc_US/_PPP_SHA2011`, `GHED_OOP_pc_US/_PPP_SHA2011`, `GHED_PVT-D_pc_US/_PPP_SHA2011`, `GHED_EXT_pc_US/_PPP_SHA2011`, `GHED_PHC_pc_US_SHA2011`, `GHED_PHC_GGHE-D_PHC_SHA2011` (~184 GHED_* codes total on API) | [V] |
| Full-DB extra vars (download only) | `hk` (gross capital formation), fs/fa financing-scheme & agent splits, `che` LCU/USD levels — not exposed as GHO indicators | [D] |
| Coverage | ~192 countries × 2000–2023 (data stamp 2025-12-05); no Dim1 disaggregation (country-year only) | [V] |
| Trap | OData `$filter` values with spaces return EMPTY body unless `%20`-encoded; `apps.who.int/nha` bulk download unstable — use GHO API per indicator | [V] |

#### WHO GHO — Obesity & Tobacco indicators

| Family | Codes | Coverage | Prov | Note |
|---|---|---|---|---|
| Obesity adults | `NCD_BMI_30A` (age-std %), `NCD_BMI_30C` (crude), `EQ_OVERWEIGHTADULT`, `obesewm` (women 15-49) | ~195 countries, 1990–2022 | [V] | Dim1=SEX (`MLE/FMLE/BTSX`); Low/High = 95% UI |
| Obesity child/adol | `NCD_BMI_PLUS2A`, `NCD_BMI_PLUS2C` (BMI >+2SD) | 5-19y, 1990–2022 | [V] | age in Dim2 (AGEGROUP) |
| Overweight (adjunct) | `NCD_BMI_25A/25C` | same | [D] | smoke-test at build |
| Tobacco use (WHO estimates) | `M_Est_tob_curr`, `M_Est_tob_curr_std`, `M_Est_tob_daily(_std)`, `M_Est_smk_curr(_std)`, `M_Est_smk_daily(_std)`, `M_Est_cig_curr`, `M_Est_cig_daily_std`, `SDGTOBACCO` (SDG 3.a.1 age-std 15+) | ~165 countries, 2000–2030 (est/proj) | [V] | `_std`=age-standardized; crude vs std easy to mix |
| Tobacco surveys/policy | `Adult_curr_tob_smoking`, `Yth_curr_tob_smoking`, `Yth_daily_tob_smoking`, MPOWER `TOBACCO_MPOWER_M3_*`, `E11_*`–`E25_*` bans, `NTCP_*` | survey-year sparse | [V] | survey series ≠ modeled estimates; don't pool |

#### UNESCO UIS — Education finance (new public API)

| Item | Detail | Prov |
|---|---|---|
| Endpoints | base `https://api.uis.unesco.org/api/public`; `/versions/default` (live: version 20260507, Feb-2026 release), `/definitions/indicators` (5,063 indicators w/ code, name, theme, timeLine, geoUnits) | [V] |
| Data call | `/data/indicators?indicatorCode=X&geoUnit=ESP` returns dims: `indicatorCode, geoUnit, year, value` | [D] |
| %GDP family | `XGDP.FSGOV` (govt exp on education %GDP, 1970–2025), level splits `XGDP.02/1/2/2T3/3/4/5T8.FSGOV`, totals `XGDP.FFNTR`, private `XGDP.FSHH.FFNTR`, combined `XGDP.FSGOV.FSHH.FSODA.FFNTR` | [V] |
| %Govt-budget family | `XGOVEXP.IMF` (educ. % total govt expenditure, 1980–2025), `XGOVEXP.IMFCALC` | [V] |
| Composition family | `XSPENDP.{level}.FDPUB.{FNCAP,FNCUR,FNS,FNTS,FNNTS,FNNONS,FNBOOKS}` (capital/current/staff-compensation % of public inst. expenditure), 1998–2024 | [V] |
| Coverage | ~200 geoUnits, NATIONAL type; per-indicator timeLine returned in metadata | [V] |
| Trap | `?indicatorCodes=` filter on `/definitions/indicators` is IGNORED — always returns all 5,063; filter client-side. Old `data.uis.unesco.org` SDMX/BDDS is retired | [V] |

#### ILOSTAT — Employment / public-sector employment

| Item | Detail | Prov |
|---|---|---|
| Endpoint | `https://rplumber.ilo.org/data/indicator/?id={ID}&ref_area=ISO3&time=YYYY&format=.json` (also `.csv`); live row schema: `ref_area, source, indicator, sex, classif1, classif2, time, obs_value, obs_status, note_*` | [V] |
| ID grammar | `{topic}_{concept}_{disaggs}_{measure}_{freq}`: measure `NB`=count(thousands), `RT`=rate, `DT`=distribution; freq `_A/_Q/_M`. Live-confirmed: `EAP_DWAP_SEX_AGE_RT_A` (LFPR, ESP 2023 = 58.06) | [V] |
| Key families | `EMP_TEMP_SEX_AGE_NB_A` (employment), `UNE_DEAP_SEX_AGE_RT_A` (unemployment rate), `EAP_DWAP_SEX_AGE_RT_A`, `EAR_4MTH_SEX_ECO_CUR_NB_A` (earnings), SDG series `SDG_0111_SEX_AGE_RT_A`, `SDG_0852_SEX_AGE_RT_A` | [D] |
| Public employment | `EMP_TEMP_SEX_INS_NB_A` — employment by institutional sector; classif1 codes `INS_SECTOR_PUB` / `INS_SECTOR_PRI` / `INS_SECTOR_TOTAL`; % variant `EMP_TEMP_SEX_INS_DT_A` | [D] |
| Classif codes | `SEX_T/M/F`; age bands `AGE_YTHADULT_YGE15 / Y15-64 / Y15-24 / YGE25` (live), also `AGE_5YRBANDS_*`, `AGE_AGGREGATE_*` | [V] |
| Coverage | 180+ ref_areas; annual mostly 1990/2000–2024 (source-dependent, `source` col e.g. `BA:2244` = LFS) | [V] |
| Trap | Returns **403 Forbidden without a browser User-Agent header** (both rplumber and sdmx.ilo.org); always send `-A "Mozilla/5.0"`. Metadata endpoints: `rplumber.ilo.org/metadata/...` same rule | [V] |

### 6. España nacional

#### INE wstempus (base `https://servicios.ine.es/wstempus/js/ES/{FUNC}/{id}`) — [V] probed 2026-07-18
**API traps [V]:** `VARIABLES_TABLA` does NOT exist (404 HTML) — use `GRUPOS_TABLA/{t}` + `VALORES_GRUPOSTABLA/{t}/{grupoId}`. Table ids **49300 and 76201 are DEAD** (jaxiT3 404): IPV was renumbered on rebase → quarterly=**80270**, annual=**80271** (discover via `TABLAS_OPERACION/IPV`). Data via `DATOS_TABLA/{t}?nult=N` / `DATOS_SERIE/{COD}`; obs fields: `Fecha`(epoch ms), `FK_Periodo`, `Anyo`, `Valor`, `Secreto`.

| id | name | key dimensions (GRUPOS_TABLA, actual values) | coverage | mark | trap |
|---|---|---|---|---|---|
| 80270 (ex-76201) | IPV trimestral | CCAA+Nacional × {General, Vivienda nueva, Segunda mano} × Índices y tasas {Índice=0, Var.trimestral=8, Var.anual, Var. en lo que va de año=A}; series `IPV1209`="Nacional. General. Índice." | ES+19 CCAA × quarterly, 2007Q1→ | [V] | Clasificación 124 = new base; old ids in saved code must be remapped |
| 80271 (ex-49300) | IPV medias anuales | same 3 groups (order differs: CCAA × tasas × general/nueva/2ªmano); series `IPV1276`="Nacional. Media anual. General." | ES+CCAA × annual, 2007→ | [V] | annual = media anual, not Q4 |
| 76136 | IPC (grupos ECOICOP × CCAA) | CCAA × Grupos ECOICOP ver.2 {00=Índice general, 01 Alimentos … 12, hierarchical `FK_JerarquiaPadres`} × Tipo de dato {Índice=0, Var.mensual=1, Var.anual=2, Var. en lo que va de año=5}; series `IPC290751` | ES+CCAA × monthly; latest pub Jun-2026 | [V] | **rebased to Base 2025 (Clasificación 120)** in Jan-2026 — index levels reset; "ECOICOP ver.2" is the new nomenclature |
| 28191 | EAES salarios (Encuesta Anual de Estructura Salarial) | Sexo {Ambos, Hombres, Mujeres} × CCAA × Medidas {Media, P10, Cuartil inferior, Mediana, Cuartil superior, P90}; series `EAES741`="Ambos sexos. Total Nacional. Dato base. Media." | ES+CCAA × annual; latest = Definitivos 2024 | [V] | percentile values have empty `Codigo` — match by `Nombre`; secreto flag possible in small cells |

#### INE COFOG file
| id | columns | coverage | mark | trap |
|---|---|---|---|---|
| `aappgastcofog95_23.xlsx` | 7 sheets Tabla1–Tabla7; rows = COFOG function (01–10, incl. 06 vivienda y servicios comunitarios), cols = year | AAPP total + subsectors × 1995–2023, annual | [V] (prior session) | function labels in Spanish, merged header rows; sheet# = subsector/measure |

#### IGAE subsector series
| id | dimensions | coverage | mark | trap |
|---|---|---|---|---|
| IGAE ejecución presupuestaria / contabilidad nacional AAPP | subsector {AAPP, Estado/AC, CCAA, CCLL, Fondos Seg. Social} × ESA-2010 economic operation (recursos/empleos) × period | ES × monthly (AC/SS) + quarterly/annual (all), ~1995→ | [D] | site blocks non-browser UA — set `User-Agent: Mozilla/5.0`; files are xlsx with multi-row headers |

#### BOE open-data API — [V] probed (sumario 20260717, HTTP 200)
| id | fields (confirmed live) | coverage | mark | trap |
|---|---|---|---|---|
| `GET /datosabiertos/api/boe/sumario/{AAAAMMDD}` | `status.{code,text}`; `data.sumario.metadatos.{publicacion,fecha_publicacion}`; `diario[].{numero,sumario_diario,seccion[]}`; `seccion.{codigo,nombre,departamento[]}`; `departamento.{codigo,nombre,epigrafe[]}` → item `{identificador (BOE-A-2026-15573), control, titulo, url_pdf{szBytes,szKBytes,pagina_inicial,pagina_final}, url_html, url_xml}` | daily, 1960→ | [V] | must send `Accept: application/json` else XML; `departamento` is dict when single, list when multiple — normalize; doc body (texto with tables) via `url_xml` per-item |

#### AEAT informes de recaudación
| id | structure | coverage | mark | trap |
|---|---|---|---|---|
| Informe Anual/Mensual de Recaudación Tributaria (xlsx annexes) | tax figure {IRPF, IS, IVA, IIEE, resto} × concept {ingresos brutos, devoluciones, recaudación líquida, homogénea} × month/year; separate delegación/CCAA sheets | ES (+delegaciones) × monthly/annual, 1995→ | [D] | sheet layout shifts across vintages; totals rows interleaved — needs positional parsing per year |

#### Liquidaciones presupuestos CCAA (Min. Hacienda)
| id | dimensions | coverage | mark | trap |
|---|---|---|---|---|
| Liquidación presupuestaria CCAA | functional/policy code (26x = Vivienda; also 261 acceso vivienda) × economic chapters 1–8 (gastos) × CCAA × year | 17 CCAA (+ceuta/melilla) × annual, ~2002→ | [D] | classification vintages differ (pre/post-2015 policy codes); consolidated vs no-consolidated files differ — pin vintage per year at build |

#### MITMA vivienda/suelo
| id | dimensions | coverage | mark | trap |
|---|---|---|---|---|
| 36400500 precio suelo urbano | province × quarter, €/m² (+ nº transacciones) | 50 prov × quarterly, 2004Q1→ | [D] | municipal size-band breakdowns exist; small-province cells suppressed |
| ICSC índice costes construcción | monthly index (total + materiales/mano de obra components) | ES × monthly, 1980s→ | [D] | base changes across series; check base year on join |

### 7. Capa legal / decisiones

#### 1. TED API v3 (EU public procurement notices)
| Field | Note |
|---|---|
| Endpoint | `POST https://api.ted.europa.eu/v3/notices/search` — JSON body `{query, fields[], limit}` [V] |
| Confirmed fields [V] | `publication-number`, `notice-type` (e.g. `cn-standard`, `can-standard`, `corr`), `buyer-name` (multilingual map by 3-letter lang), `publication-date`, `total-value`, `total-value-cur`, `buyer-country`, `contract-nature` (works/supplies/services), `notice-title`, `deadline-receipt-tender-date-lot`, `classification-cpv` (query dim), auto `links{xml,pdf,html}` per language |
| Other documented fields [D] | `place-of-performance`, `winner-name`, `winner-country`, `procedure-type`, `contract-duration`, `buyer-city`, `description-lot`, `estimated-value` (eForms field list at /v3/fields) |
| Coverage | EU/EEA + some 3rd-country notices; API back to ~2014, eForms-rich from 2023-11 |
| Trap | Value fields silently omitted when empty (frequent on pre-award notices); buyer-name replicated across all 24 langs — pick one; query language is expert-search syntax, not JSON filters |

#### 2. BDNS / infosubvenciones (Spanish subsidies, SNPSAP)
| Field | Note |
|---|---|
| Endpoint | `GET https://www.infosubvenciones.es/bdnstrans/api/convocatorias/busqueda?page=0&pageSize=N` [V] — plain `/api/convocatorias` returns the Angular SPA, must use `/busqueda` |
| List fields [V] | `id`, `numeroConvocatoria` (código BDNS), `descripcion`, `descripcionLeng`, `fechaRecepcion`, `nivel1` (ESTADO/AUTONOMICO/LOCAL), `nivel2` (territory), `nivel3` (órgano), `mrr` (NextGenEU flag), `codigoInvente`; Spring pageable envelope (`totalElements`=643,262 on probe) |
| Detail fields [D] | `?numConv=` → `presupuestoTotal`, `fechaPublicacion`, `instrumentos[]`, `tiposBeneficiarios[]`, `sectores[]` (CNAE), `regiones[]`, `finalidad`, `abierto`, `fechaInicioSolicitud`/`fechaFinSolicitud`, bases reguladoras URL; sibling `/concesiones/busqueda`, `/minimis/busqueda`, `/ayudasestado/busqueda` |
| Coverage | Spain, all admin levels; convocatorias 2014→today, concesiones coverage thinner pre-2016 |
| Trap | Legal notice warns of throttling on abuse; data mutable after extraction (corrections/deletions) — re-pull, don't cache forever |

#### 3. legislation.gov.uk (UK statute book)
| Field | Note |
|---|---|
| Feed | `GET https://www.legislation.gov.uk/{type}/data.feed` Atom [V]; per-year facet feeds (e.g. `/ukpga/2026/data.feed`); CSV alternate `data.csv` [V] |
| Entry fields [V] | `id` (URI `/id/ukpga/{year}/{num}`), `title`, `link` (self + alternates: `data.xml` CLML, `data.rdf`, `data.akn` AkomaNtoso, `data.html` HTML5, `data.pdf`, `data.csv`), `updated`, `published`, `ukm:DocumentMainType`, `ukm:Year`, `ukm:Number`, `ukm:ISBN`, `ukm:CreationDate`, `leg:facetYears`/`leg:facetTypes` counts |
| Full text | `/{type}/{year}/{num}/{version}/data.xml` (CLML) and `data.akn` confirmed linked per entry [V] |
| Coverage | UK (ukpga, uksi, asp, wsi, nisr…); ukpga 1801→2026; 20 items/page (`leg:morePages` for pagination) |
| Trap | `enacted` vs `made` vs current revised version in URL — omit version segment and you may get revised text, not as-enacted |

#### 4. opentender.eu (bulk tender data, DIGIWHIST/TheyBuyForYou)
| Field | Note |
|---|---|
| Column families [D] | tender: `tender_id`, `title`, `procedure_type`, `supply_type`, `final_price`, `estimated_price`, cpv main/secondary; buyer: `buyer_name`, `buyer_id`, `buyer_country`, `buyer_type`, NUTS; lot/bid: `lot_title`, `bids_count`, `single-bidding flag` (bidsCount==1), `bidder_name`, `bidder_id`; dates: publication, award, decision |
| Integrity/CRI [D] | composite CRI + components: single bidding, call-for-tender absent, advertisement period, decision period, procedure type risk, new company, tax-haven bidder |
| Coverage | 33 jurisdictions (EU-27 + GE, IS, NO, CH, UK, EU-institutions); ~2006–2023 depending on country; JSON/CSV bulk per country-year |
| Trap | Bulk dumps versioned and refresh irregularly since project wind-down — check file dates; buyer/bidder IDs are DIGIWHIST-generated, not official registry IDs |

#### 5. EUR-Lex CELLAR / SPARQL
| Field | Note |
|---|---|
| Endpoint [D] | `http://publications.europa.eu/webapi/rdf/sparql` (CELLAR); CDM ontology |
| Main entities [D] | `cdm:work` (CELEX id, `cdm:work_date_document`, `cdm:work_created_by_agent` (institution), `cdm:resource_legal_in-force`, `cdm:work_is_about_concept_eurovoc` (EuroVoc), directory code, legal basis via `cdm:resource_legal_based_on_resource_legal`); `cdm:expression` (language, title `cdm:expression_title`); `cdm:manifestation` (format: fmx4/xhtml/pdf) |
| Identifiers [D] | CELEX (e.g. `32016R0679`), ELI URIs, OJ reference; sector 3=legislation, 6=case-law |
| Coverage | EU acquis 1951→today, 24 languages; case-law (CJEU) sector 6 |
| Trap | Work/expression/manifestation triple-hop needed for titles-in-language — naive queries explode; endpoint times out on unbounded property paths, always LIMIT + FILTER by date |

#### 6. EC Financial Transparency System (FTS)
| Field | Note |
|---|---|
| Access | Old `budget/financial-transparency-system/download.html` now redirects to commission.europa.eu budget page [V-dead]; `.../financial-transparency-system/analysis.html` reachable, offers "download all financial transparency system datasets" (CSV/XLSX per year) [V] |
| Columns [D] | `Year`, `Beneficiary name` (+ coordinator flag), `Beneficiary VAT/registration`, `Address`, `City`, `Postal code`, `Beneficiary country`, `NUTS2`, `Type of beneficiary`, `Amount (EUR)` (committed), `Source of funding` / `Fund`, `Budget line name and number`, `Programme name`, `Funding type` / `Action type`, `Expense type`, `Subject of grant/contract`, `Responsible DG`, `Project period` |
| Coverage | EU budget direct-management commitments, one file per financial year 2007→(n-1); published annually ~June |
| Trap | Direct management only (no shared-management CAP/ESIF — those live in national portals); beneficiary names not deduplicated/ID-keyed across years — entity resolution needed |

### 8. Académicas / históricas

#### JST Macrohistory Database (jst.xlsx, R6-style)
| Aspecto | Detalle |
|---|---|
| Keys | `year`, `country`, `iso`, `ifs` — panel 18 países × 1870–2020 (2.718 filas, 59 cols) [V] |
| Macro reales | `pop`, `rgdpmad`, `rgdpbarro`, `rconsbarro`, `gdp`, `iy`, `cpi`, `ca`, `imports`, `exports`, `unemp`, `wage`, `xrusd` [V] |
| Dinero/tipos | `narrowm`, `money`, `stir`, `ltrate`, `bill_rate`, `bond_rate` [V] |
| Fiscal | `debtgdp`, `revenue`, `expenditure` [V] |
| Crédito bancario | `tloans`, `tmort`, `thh`, `tbus`, `bdebt`, `lev`, `ltd`, `noncore` [V] |
| Crisis/regímenes | `crisisJST`, `crisisJST_old`, `peg`, `peg_strict`, `peg_type`, `peg_base`, `JSTtrilemmaIV` [V] |
| Retornos (RORE) | `eq_tr`, `housing_tr`, `bond_tr`, `hpnom`, `rent_ipolated`, `housing_capgain(_ipolated)`, `housing_rent_rtn`, `housing_rent_yd`, `eq_capgain(_interp)`, `eq_dp(_interp)`, `eq_tr_interp`, `eq_div_rtn`, `capital_tr`, `risky_tr`, `safe_tr` [V] |
| Trap | Una sola hoja `Sheet1`; países = ISO3 (AUS…USA); niveles en moneda local de escala variable — usar ratios (`debtgdp`, `iy`) o deflactar con `cpi`; series de retornos con huecos interpolados (`_interp`/`_ipolated`). |

#### Global Macro Database (KMueller-Lab GMD)
| Aspecto | Detalle |
|---|---|
| Id/acceso | 239 países, 1086–2025 (+proyecciones 2030); paquetes `gmd` Stata / `global_macro_data` (Py) / `globalmacrodata` (R); versiones trimestrales (`2026_06`) [V] |
| Keys | country (ISO3) × year [V] |
| Cuentas nacionales | `nGDP`, `rGDP`, `rGDP_pc`, `rGDP_USD`, `nGDP_USD`, `deflator`, `cons`, `hcons`, `gcons`, `inv`, `finv` (+`_GDP`, `_USD`), `sav` [V varlist.csv] |
| Comercio/BOP | `exports`, `imports`, `CA` (+`_GDP`, `_USD`), `USDfx`, `REER` [V] |
| Precios/trabajo | `CPI`, `infl`, `HPI`, `rHPI`, `unemp`, `emp`, `pop` [V] |
| Dinero/tipos | `M0`–`M4`, `M3_GDP`, `cbrate`, `strate`, `ltrate` [V] |
| Fiscal | consolidado: `govrev`, `govexp`, `govtax`, `govdef_GDP`, `govdebt_GDP`; central: `cgovrev/cgovexp/cgovtax/cgovdef/cgovdebt` (+`_GDP`); general: `gen_govrev/…/gen_govdebt` (+`_GDP`) [V] |
| Crisis | `BankingCrisis`, `SovDebtCrisis`, `CurrencyCrisis` (dummies) [V] |
| Trap | 46 conceptos = 77 series (niveles LC + `_GDP` + `_USD`); ratios fiscales ahora spliced directamente (release 2026_06) — no recomputar ratio desde niveles spliced; niveles en millones de moneda local. |

#### ICTD/UNU-WIDER Government Revenue Dataset (GRD)
| Aspecto | Detalle |
|---|---|
| Keys | `iso`/`country` × `year`; ~196 países, 1980–2023 (release anual) [D] |
| Vars núcleo (%GDP) | `rev_inc_sc` / `rev_ex_sc` (ingreso total incl/excl contribuciones sociales), `tax_inc_sc` / `tax_ex_sc`, `resource_tax` / `nrtax` (no-recurso), `tot_res_rev` / `tot_nrrev` [D] |
| Desglose impositivo | `direct` (con/sin recursos), `pit`, `cit`, `property`, `payroll`, `tax_g_s` (bienes y servicios), `vat`, `excises`, `tax_int_trade`, `other_tax`, `nontax`, `sc` (social contributions), `grants` [D] |
| Meta/flags | nivel de gobierno (general vs central, dummy `general`), `cautionnote`, income group, región [D] |
| Trap | Mezcla GG/CG por país-año — filtrar por nivel de gobierno antes de comparar; splits recurso/no-recurso faltan en muchos países. |

#### SIPRI Military Expenditure Database
| Aspecto | Detalle |
|---|---|
| Keys | país × año; ~173 países, 1949–2024 (algunos desde 1948) [D] |
| Medidas (hojas xlsx) | milex en moneda local corriente; constant (2023) USD m; current USD m; % del PIB; per cápita; % del gasto público [D] |
| Trap | Formato ancho (años en columnas), una hoja por medida; códigos `..` = no disponible y `xxx` = país inexistente rompen parsers numéricos. |

#### WID.world (World Inequality Database)
| Aspecto | Detalle |
|---|---|
| Código de variable | 1 letra tipo + concepto 5-char + edad + unidad: tipo `a`=media, `s`=share, `t`=umbral, `g`=Gini, `b`=Pareto invertido; conceptos `ptinc` (pre-tax income), `diinc` (post-tax), `fiinc` (fiscal), `hweal` (riqueza neta), `nninc` (macro); ej. `sptinc992j`, `shweal992j`, `aptinc992j` [D] |
| Población/unidad | edad `992`=adultos, `999`=todos; unidad `j`=equal-split adults, `i`=individuos, `t`=tax unit [D] |
| Percentiles | strings `p0p50`, `p90p100`, `p99p100`, `p99.9p100`… como dimensión aparte [D] |
| Coverage | ~200 territorios; income desde ~1900 (algunos s.XIX), wealth más corto; bulk CSV + API [D] |
| Trap | Valores monetarios en moneda local constante — convertir con los índices `xlcusx`/PPP de la propia WID; percentil es texto, no numérico. |

#### CEPEJ-STAT (European judicial systems)
| Aspecto | Detalle |
|---|---|
| Keys | Estado (46 CoE + observadores) × ciclo bienal (datos 2010–2022; ciclo 2024 = datos 2022) [D] |
| Presupuesto | presupuesto sistema judicial / tribunales / fiscalía / legal aid — total, € por habitante, % PIB [D] |
| Profesionales | jueces profesionales, fiscales, staff no-juez, abogados — por 100.000 hab.; balance de género [D] |
| Eficiencia | clearance rate (%), disposition time (días), casos entrantes/resueltos/pendientes — por instancia (1ª/2ª/suprema) × tipo de caso (civil-mercantil litigioso, administrativo, penal) [D] |
| Trap | Códigos NA/NAP en export; cambios metodológicos entre ciclos limitan series largas — comparar dentro del mismo ciclo. |

#### CPDS + QoG (one-liners)
| Dataset | Detalle |
|---|---|
| CPDS (Comparative Political Data Set, Armingeon et al.) | 36 democracias OECD/EU × 1960–2022 anual; ~300 vars: composición de gobierno (`gov_left`, `gov_right`, Schmidt index), elecciones por familia partidaria, instituciones (federalismo, bicameralismo), controles socioeconómicos [D] |
| QoG (Quality of Government, U. Gothenburg) | Standard dataset cross-section + time-series (1946–, ~194 países, ~2.000 vars compiladas de ~100 fuentes); prefijo de variable = fuente (`wbgi_`, `icrg_`, `vdem_`, `fh_`); variantes Basic / OECD / EU-Regional [D] — trap: es agregador, verificar licencia/versión de la fuente subyacente antes de citar. |

### 9. Flujos y migración

#### 1. OECD DAC CRS (creditor reporting system)

| dataset | key dimensions / columns | coverage | prov | trap |
|---|---|---|---|---|
| `OECD.DCD.FSD,DSD_CRS@DF_CRS` (SDMX) + CRS bulk microdata | SDMX dims: DONOR, RECIPIENT, SECTOR, MEASURE, CHANNEL, MODALITY, FLOW_TYPE, PRICE_BASE, TIME_PERIOD [D]. Microdata file cols: `donor_code/donor_name, recipient_code, year, flow_code (11=ODA grants,13=ODA loans,19=OOF), bi_multi, purpose_code (5-digit CRS), sector_code, channel_code, usd_commitment, usd_disbursement, usd_received, finance_t` [D] | All DAC + non-DAC + multilateral donors × ~150 recipients; activity-level 1995–2024 (aggregates from 1960s) | [V] endpoint alive: dataflow returns SDMX structure (HTTP 200) | `stats.oecd.org` is RETIRED — 301→ data-explorer.oecd.org; use `sdmx.oecd.org/public/rest/`; DSD dimension fetch needs XML parse (JSON accept header returned non-JSON in probe) |

#### 2. World Bank IDS (International Debt Statistics)

| dataset | key dimensions / columns | coverage | prov | trap |
|---|---|---|---|---|
| WB API **source id = 6** "International Debt Statistics" (DSSI variant = id 81) | Dims returned live: `Country × Series × Counterpart-Area × Time`. Bilateral indicator `DT.DOD.BLAT.CD` (PPG bilateral DOD, current US$) confirmed; URL pattern `/v2/sources/6/country/{iso3}/series/DT.DOD.BLAT.CD/counterpart-area/all/time/YR{yyyy}` | ~120 low/middle-income debtors × creditor counterparts, 1970–2023 (lastupdated 2025-12-03) | [V] probed now — source list + KEN×2023 counterpart query both resolved | Counterpart-Area codes are IDS-numeric NOT ISO (e.g. 265=Zimbabwe, includes defunct entities like Yugoslavia); matrix is sparse — many `value: null` rows to drop |

#### 3. UN DESA International Migrant Stock 2024

| dataset | key dimensions / columns | coverage | prov | trap |
|---|---|---|---|---|
| UN DESA IMS 2024 (Excel workbooks, un.org/development/desa/pd) | origin country × destination country × year × sex (both/male/female); country identifiers = UN M49 location codes | ~230 origins × ~230 destinations; quinquennial 1990–2020 + 2024 | [D] — smoke-test download at build | Wide Excel with multi-row headers; regional aggregates interleaved with countries (filter on M49 code list); origin×dest matrix and totals live in separate sheets |

#### 4. UNHCR Refugee Population Statistics API

| dataset | key dimensions / columns | coverage | prov | trap |
|---|---|---|---|---|
| `api.unhcr.org/population/v1/population/` | Fields returned live: `year, coo_id/coo_name/coo/coo_iso, coa_id/coa_name/coa/coa_iso, refugees, asylum_seekers, returned_refugees, idps, returned_idps, stateless, ooc, oip, hst` | Global, annual 1951–2024; coo (origin) × coa (asylum) bilateral | [V] probed now — JSON returned | Without `coo_all=true&coa_all=true` you get aggregated rows with `"-"` in country slots; numeric fields mixed int/string (`"0"`); paginated (`maxPages` in envelope) |

#### 5. AidData Global Chinese Development Finance (GCDF 3.0)

| dataset | key dimensions / columns | coverage | prov | trap |
|---|---|---|---|---|
| AidData GCDF 3.0 (project-level Excel/CSV) | `AidData Record ID, Funding Agency/Funder, Recipient, Commitment Year, Amount (Constant 2021 USD), Flow Type (loan/grant/export credit), Flow Class (ODA-like / OOF-like / Vague), Sector (CRS-aligned), Status, Interest Rate, Maturity` | China → ~165 LMICs, 2000–2021 | [D] — static file download, verify at build | One row per project; must filter `Recommended For Aggregates = Yes` before summing or totals double-count; amounts in constant 2021 USD (not nominal) |

#### 6. World Bank / KNOMAD bilateral remittance matrix

| dataset | key dimensions / columns | coverage | prov | trap |
|---|---|---|---|---|
| KNOMAD/WB Bilateral Remittance Matrix (Excel) | sending (origin) country × receiving (destination) country × year; values USD mn | ~200×200 countries; annual estimate vintages ~2010–2021 | [D] — Excel on knomad.org / worldbank.org migration portal | MODELED estimates (Ratha method), not observed flows; matrix orientation (rows=receiving, cols=sending) easy to transpose wrongly; updates irregular post-2021 (WB API sources 76/77 are Remittance PRICES, not this matrix) |

#### 7. EU Cohesion Open Data (cohesiondata)

| dataset | key dimensions / columns | coverage | prov | trap |
|---|---|---|---|---|
| `cohesiondata.ec.europa.eu` (DG REGIO, Socrata/SODA API) | fund (ERDF/CF/ESF+/JTF/EAFRD/EMFF), member state (+ sometimes NUTS2), programming period (2007-13 / 2014-20 / 2021-27), year, planned EU amount, decided/eligible cost, spent (declared expenditure), theme/category | EU-27/28 × 2007–2027 | [D] — Socrata endpoints per dataset id, smoke-test at build | NOT on the Eurostat API despite the name — it's a Socrata platform (SODA `$limit` default 1000); spend series are CUMULATIVE not annual; planned vs implemented live in separate datasets per period |

---

## Diccionario de datos — Variante C (vivienda como consecuencias)

*v1, 2026-07-18. Responde a la decisión "¿extraer todo o seleccionar?" y fija el diccionario (dimensiones/campos) de cada dataset con la marca de qué columnas son NECESARIAS (✔) para los bloques B1–B6 del [plan](PLAN_vivienda_consecuencias.md). Provenance: **[V]** = esquema verificado en vivo (consulta real); **[D]** = documentado, pendiente de smoke-test en build (regla de la 3ª ronda: ningún código entra en gold sin test).*

---

### 0. Decisión: extracción SELECTIVA, nunca volcado completo

**Veredicto: seleccionar.** Razones:
1. El volcado completo de ~125 fuentes es ETL-suicidio (semanas de trabajo sin valor analítico; la mayoría de columnas jamás se usarían).
2. El contrato gold del plan ya impone la disciplina: cada conector extrae **series nombradas** con filtros explícitos, cae en `raw/` como evidencia y se transforma a formato largo `(geo, periodo, variable, valor, flag)`.
3. Criterios de inclusión de una columna: (a) alimenta un bloque B1–B6 concreto; (b) pasa smoke-test; (c) cabe en el grano del gold (país/CCAA × año/trimestre).
4. Presupuesto objetivo: **~15 grupos de series, gold < 100 MB.** Todo lo demás queda catalogado en el landscape, no extraído.

---

### 1. Capa fiscal (B1–B2)

#### 1.1 Eurostat `gov_10a_exp` — gasto por función × tipo económico **[V]** (consultas reales 2026-07-16/17)
| Dimensión | Valores necesarios | Bloque |
|---|---|---|
| `freq` | A (anual) ✔ | — |
| `unit` | **PC_GDP** ✔ (+ MIO_EUR para per-cápita propio) | B1–B2 |
| `sector` | **S13** ✔ (AAPP consolidado) | — |
| `cofog99` | **GF06** ✔ (L1, 1995→); **GF0601 + GF1006** ✔ (L2, 2001→); GF01–GF10 (contexto composición) | B1–B2 |
| `na_item` | **TE** ✔ [V], **P51G** ✔ [V] (inversión), **D9** ✔ (transf. capital), **D1** ✔ (salarios), P2, D3, D62+D632 [D] | B1 composición |
| `geo` | UE-27 + EFTA + UK ✔ (~33) | — |
| `TIME_PERIOD` | 1995–2023 ✔ | — |

*Receta:* una consulta por bloque `na_item×cofog99`, formato largo. Trampa conocida: dedup OCDE↔Eurostat; IT-superbonus flag 2021–23.

#### 1.2 INE COFOG España (`aappgastcofog95_23.xlsx`) **[V]** (descargado y abierto)
7 hojas ("Tabla 1..7"); estructura tabla-informe (función × año, 1995–2023). ✔ Necesario: tabla función×año total AAPP + subsectores. Uso: B1 España profundo; validación cruzada del dato Eurostat.

#### 1.3 IGAE series por subsector **[V]** (acceso verificado; UA navegador)
XLSX por subsector (central/CCAA/local/SS) catalogados en datos.gob.es. ✔ Función vivienda + sanidad + educación por subsector. [D] estructura exacta de columnas — smoke-test en build.

#### 1.4 Liquidaciones presupuestarias CCAA (Hacienda) [D]
Clasificación funcional (política 26x vivienda) × económica (cap. 1–8) × CCAA × año, ~2002→ online. ✔ gasto vivienda por CCAA (B3). ⚠️ La estructura de los XLSX CAMBIA entre años — presupuestar parser por vintage.

#### 1.5 BOE (API sumarios + XML) **[V]** (parser probado: PGE 2023 y 2021, leyes CCAA)
Campos JSON sumario: `identificador, titulo, url_pdf/xml, seccion, departamento`. XML: `<titulo>, <texto>` con `<table>` parseables. ✔ Para B5: fecha, id, título, tabla "Acceso vivienda" del PGE. Pesetas pre-2002 (÷166,386).

### 2. Outcomes de vivienda (B2–B3)

#### 2.1 EU-SILC `ilc_lvho07a` (sobrecarga >40% renta) [D]
Dims esperadas: `freq, incgrp, geo, time` (+unit=PC). ✔ TOTAL población; opcional por grupo de renta (distributivo). 2003→. Smoke-test pendiente (endpoint estructura devolvió 400 — usar consulta de datos como test).

#### 2.2 EU-SILC `ilc_lvho05a` (hacinamiento) [D]
Dims: `freq, age, sex, hhtyp?, geo, time`. ✔ TOTAL; edad joven (18–34) como sensibilidad. 2003→.

#### 2.3 Panel de asequibilidad propio (gold del TFM) **[V]** (construido)
`asequibilidad_ccaa.csv`: `ccaa, anyo, ipv_general, salario_medio_anual, salario_idx, ratio_asequibilidad` ✔ TODAS — es la variable de consecuencias de B3–B4. (Nota: ficheros hoy en `_old/` — restaurar al reactivar pipeline.)

### 3. Núcleo España precios/drivers (B3, heredado del TFM) **[V]** (pipeline operativo)

| Dataset | Campos | Necesarios |
|---|---|---|
| INE IPV — ⚠️ **RENUMERADA 2026-07-18: 76201/49300 devuelven 404; trimestral = 80270, anual = 80271** (descubierto en barrido de esquemas; actualizar `config.py`) | serie → `ccaa, tipo_vivienda (general/nueva/2ªmano), trimestre, índice`; metadatos vía `GRUPOS_TABLA/{t}` (VARIABLES_TABLA no existe) | ✔ todos; ⚠️ bug conocido: no se persiste — arreglar |
| INE IPC 76136 | `ccaa, anyo/mes, índice general` | ✔ SOLO series "Índice general" (bug del promedio: valores 15–26 = corruptos) |
| INE EES 28191 | `ccaa, anyo, salario_medio` | ✔ "Ambos sexos"+"Media"; desfase ~1,5 años (flag) |
| BdE Euríbor `ti_1_7.csv` | `fecha, euribor_12m` (diario 1999→) | ✔ media trimestral |
| MITMA suelo 36400500 | `provincia, trimestre, €/m²` | ✔ agregado a CCAA (ruido provincial) |
| MITMA ICSC | `mes, índice costes construcción` (nacional, base 2021) | ✔ media trimestral |

### 4. Comparables internacionales (B2)

#### 4.1 OECD Analytical House Prices [D]
Indicadores: precio nominal/real, **price-to-income ✔, price-to-rent ✔**, rentas; trimestral, décadas, ~40 países. ID del dataflow a fijar en build (la búsqueda MCP no lo resolvió — usar OECD Data Explorer, familia `DSD_AN_HOUSE...`).

#### 4.2 BIS Residential Property Prices [D]
CSV bulk: `ref_area, period(Q), value, unit(index/yoy), nominal/real`. ✔ índice real, ~60 países (series largas, algunas 1970→). Contexto/robustez de B2.

#### 4.3 OECD Affordable Housing Database [D]
Tablas XLSX por indicador (PH = policy, HC = conditions): stock vivienda social ✔, instrumentos ✔. No es panel limpio — usar como covariable estática/contexto.

#### 4.4 Eurostat `prc_hpi_q` [D]
Dims: `purchase (TOTAL/NEW/EXST), unit (I15_Q, RCH_Q...), geo, time(Q)`. ✔ TOTAL×índice. Backup del IPV + comparador UE.

### 5. Trabajadores públicos (feature de composición, B2)

#### 5.1 WWBI (WB source=64) **[V]** (diccionario completo extraído: 302 indicadores)
Necesarios (✔, 6 de 302):
| Código | Indicador |
|---|---|
| `BI.EMP.TOTL.PB.ZS` ✔ [V] | empleo público / empleo remunerado (ES 24,8% 2020 verificado) |
| `BI.WAG.TOTL.GD.ZS` ✔ [V] | masa salarial %PIB (ES 12,5% 2020 verificado) |
| `BI.WAG.TOTL.PB.ZS` ✔ [D] | masa salarial % gasto público |
| `BI.WAG.PREM.PB.*` ✔ [D] | prima salarial público-privado (fijar sufijo exacto en build) |
| `BI.EMP.FRML.HE.PB.ZS` [D] | sanitarios / empleados públicos (módulo sanidad) |
| `BI.EMP.FRML.TS.PB.ZS` [D] | docentes / empleados públicos (módulo educación) |
⚠️ Encuesta-derivado: lagunas (DE vacía), lag ~2 años. Features, no titular.

#### 5.2 Eurostat D1 por función — ya cubierto en 1.1 (na_item=D1 ✔).

### 6. Demografía/amplificador (B4)

| Dataset | Campos | Necesarios |
|---|---|---|
| INE Estadística de Migraciones **[V]** (pipeline) | `ccaa, anyo, inmigración/emigración/saldo` | ✔ saldo por CCAA |
| INE padrón/población | `ccaa, anyo, población` | ✔ Δpoblación |
| Eurostat `migr_imm1ctz`/`migr_emi2` [D] | `citizen/agedef, geo, time` | ✔ flujo total país (tier UE) |
| UN DESA Migrant Stock [D] | matriz `origen × destino × año(quinq.)` | ✔ stock destino (si tier global) |
| INE Censo 2021 / ECH [D] | hogares, tenencia | contexto |

### 7. Resumen: el gold objetivo de la Variante C

**Grano:** `(geo[país|ccaa], periodo[anual|trimestral], variable, valor, flag_calidad, vintage)`

| Grupo | Series ✔ | Bloque |
|---|---|---|
| gasto vivienda (nivel+composición, UE33+CCAA) | ~10 | B1–B2 |
| outcomes SILC + asequibilidad propia | ~5 | B2–B3 |
| precios/drivers España (IPV, IPC, salarios, Euríbor, suelo, ICSC) | ~8 | B3 |
| comparables internacionales (P2I, P2R, BIS) | ~3 | B2 |
| trabajadores públicos (WWBI 6 + D1) | ~7 | B2 |
| demografía (saldo migratorio, población) | ~4 | B4 |
| eventos BOE (tabla curada) | 1 tabla | B5 |
| **TOTAL** | **~38 series + 1 tabla** — frente a los miles disponibles | |

*Regla final: si una columna no aparece en esta tabla, NO se extrae — se cataloga. Cualquier alta nueva exige: bloque de destino + smoke-test + fila aquí.*
