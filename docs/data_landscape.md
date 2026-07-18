# Panorama de bases de datos fiscales y económicas (mundo)

*Compilado 2026-07-17. Fuentes: análisis propio (Claude) + cross-check con Perplexity (web-grounded) y Gemini (vía agy). Los ítems marcados **[verificado en vivo]** fueron comprobados con peticiones HTTP reales el 2026-07-16/17 en esta sesión. ✓✓ = nombrado independientemente por ≥2 motores (cross-validado). MCP = conector ya operativo en el entorno de trabajo.*

**Ámbito:** gasto público y recaudación tributaria por país; capa de *números* (series estadísticas) y capa de *decisiones* (boletines legales, contratos, subvenciones).

---

## 1. Multilaterales — núcleo armonizado

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

## 2. Multilaterales regionales

| Base | Contenido | Cobertura | Fuente |
|---|---|---|---|
| CEPALSTAT (ECLAC) | fiscal LatAm | América Latina | propio |
| CIAT / Revenue Statistics in Latin America | impuestos detallados | 27+ países LatAm | Gemini |
| AfDB Africa Information Highway | gasto + ingresos | 54 países África, 1980→, API | Gemini |
| ATAF African Tax Outlook | estructura y administración tributaria | 38+ países África | Gemini |
| ADB Key Indicators (KIDB) | finanzas públicas Asia-Pacífico | 49 economías, API | Gemini |
| Arab Monetary Fund | presupuestos, ingresos oil/non-oil | 22 estados árabes | Gemini |
| GCC-Stat | ingresos/gastos Golfo | 6 países CCG, 2000→ | Gemini |

## 3. Académicas / especializadas / históricas

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

## 3-bis. Serie histórica larga — siglo XX (1900–1995)

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

## 3-ter. Fuentes para módulos bolt-on gasto→resultado (3ª ronda del consejo, códigos verificados)

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

## 3-quater. Pilares del programa integral: SOEs, flujos entre países, migración, satélite

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

## 3-quinquies. Fuentes para el análisis de vivienda (Variante C)

*Añadido 2026-07-18 para [PLAN_vivienda_consecuencias](PLAN_vivienda_consecuencias.md). Las marcadas ✅ ya están verificadas (pipeline del TFM, comprobaciones 2026-07-07, o esta sesión).*

### Núcleo España (ya en el pipeline del TFM)
| Fuente | Serie | Estado |
|---|---|---|
| INE wstempus | IPV anual 49300 + trimestral 76201; IPC 76136 (solo "Índice general" — bug conocido); salarios EES 28191 | ✅ pipeline operativo |
| Banco de España | Euríbor 12m (`ti_1_7.csv`, diario 1999→) | ✅ verificado |
| MITMA | precio suelo urbano (36400500, provincial 2004→); ICSC costes de construcción | ✅ verificado (XLS legado, parser xlrd) |
| Registradores ERI | % compraventas por extranjeros | ⚠️ WAF + PDF; driver V2 descartable |

### Oferta privada de construcción (añadido 2026-07-18, revisión 1 de la Entrega 4)
| Fuente | Serie | Estado |
|---|---|---|
| MITMA Boletín Estadístico — visados | Visados de dirección de obra nueva (Colegios de Aparejadores; mensual, provincial → CCAA) | ⏳ ruta identificada (mismo boletín que suelo/ICSC, parser xlrd reutilizable); verificar en extracción |
| MITMA — viviendas iniciadas y terminadas | Obra nueva libre y protegida (calificaciones); trimestral/anual, provincial | ⏳ misma ruta; retardo visado→terminación ~18–24 meses = feature adelantada para T1 |
| Eurostat `nama_10_an6` | FBCF por activo AN_111 "viviendas" %PIB (inversión residencial TOTAL; privada ≈ total − GF06 capital) | ⏳ mismo cliente Eurostat del pipeline; contexto obligatorio de la figura B3 del atlas |
| INE — hipotecas constituidas | Número e importe por CCAA (mensual) | Opcional: demanda financiada, contraste del canal Euríbor |

### Gasto público en vivienda (la capa fiscal de la Variante C)
| Fuente | Serie | Estado |
|---|---|---|
| Eurostat `gov_10a_exp` | GF06 (L1, 1995→) y **GF0601+GF1006** (L2, 2001→) × na_item (capital vs corriente) | ✅ verificado en vivo (ES 0,5 vs UE 1,2 %PIB 2023; IT 4,4 superbonus) |
| INE COFOG + IGAE subsectores | gasto vivienda España/CCAA | ✅ verificados |
| Liquidaciones CCAA (Hacienda) | función vivienda por comunidad, ~2002→ online | página confirmada |
| BOE | Ley 12/2023, zonas tensionadas, planes estatales, PGE "Acceso vivienda" (3.476 M€ 2023 extraído) | ✅ verificado en vivo |
| MIVAU (Min. Vivienda) | Observatorio de Vivienda y Suelo; **SERPAVI** (índice de precios de alquiler); registro de zonas tensionadas | público |

### Comparables internacionales (outcomes + precios)
| Fuente | Serie | Nota |
|---|---|---|
| **EU-SILC** `ilc_lvho07a` / `ilc_lvho05a` | sobrecarga de coste (>40% renta) / hacinamiento — los OUTCOMES de B2 | API sin clave, 2003→ |
| **OECD Affordable Housing Database** | stock de vivienda social, instrumentos de política, indicadores de asequibilidad por país | descarga abierta — el comparador de POLÍTICA de vivienda |
| **OECD Analytical House Prices** | **price-to-income y price-to-rent** por país, trimestral, décadas | API — el gemelo internacional del ratio de asequibilidad del TFM |
| **BIS Residential Property Prices** | precios de vivienda, ~60 países, series largas (algunas desde 1970) | descarga abierta |
| Eurostat `prc_hpi_q` | índice de precios de vivienda UE (respaldo del IPV con menos detalle) | API; ya identificado como backup en Entrega 3 |
| EMF Hypostat | mercados hipotecarios europeos, anuario | PDF/tablas gratuitas |
| Portales privados (Idealista/Fotocasa) | precios de oferta, alquiler | NO oficiales; API restringida — solo contexto, nunca núcleo |

### Demografía/demanda (amplificador B4)
| Fuente | Serie | Nota |
|---|---|---|
| INE Estadística de Migraciones + padrón | flujos y stock por CCAA | ✅ (pipeline) |
| INE Censo 2021 + Encuesta Continua de Hogares | hogares, tenencia, tamaño | API/descarga |
| Eurostat `migr_imm/emi` + UN DESA | flujos/stock por país (tier UE) | §3-quater |

## 4. Subnacional (la mayor laguna del listado inicial)

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

## 5. Portales nacionales

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

## 6. Capa de decisiones (boletines legales, contratos, subvenciones)

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

## 7. Agregadores

| Agregador | Nota |
|---|---|
| **DBnomics** (db.nomics.world) | **gratuito, una API sobre 80+ proveedores** (IMF, Eurostat, OECD, ECB, INSEE, Destatis, AMECO…) — el atajo "una sola base" |
| FRED | 800k+ series incl. internacionales, API limpia |
| OpenSpending (OKFN) | presupuestos multi-país centralizados, CSV/JSON/API |
| CEIC / Haver / Trading Economics | comerciales; solo justificados para China/emergentes |

## 8. Meta: transparencia y calidad fiscal (útiles como controles)

| Base | Contenido | Cobertura |
|---|---|---|
| Open Budget Survey (IBP) | puntuación de transparencia presupuestaria | 125+ países, bienal 2006→ |
| PEFA | indicadores de gestión financiera pública | 155+ países, 700+ evaluaciones |
| GIFT Data Portal / OFDP | datasets fiscales estandarizados | ~20 países |

---

## 9. Notas prácticas (gotchas comprobados en sesión)

1. **IGAE bloquea clientes no-navegador** — enviar User-Agent de Chrome; sin él la conexión se corta (HTTP 000). Datos públicos; throttling cortés.
2. **BOE**: API de sumarios `datosabiertos/api/boe/sumario/YYYYMMDD` (JSON) desde ≥1994; texto completo `diario_boe/xml.php?id=`. Cifras **en pesetas hasta PGE 2001** (conversión 166,386 pta/€). Años de prórroga sin ley nueva: 1996, 2012, 2019–20, 2024–26.
3. **OECD↔Eurostat COFOG**: la OCDE copia Eurostat para miembros UE → al fusionar, Eurostat = canónico para UE, OCDE solo para no-UE (evita duplicar país-años).
4. **INE**: `https://www.ine.es/daco/daco42/cne24/aappgastcofog95_23.xlsx` = COFOG España 1995–2023 completo, descarga directa, sin trucos.
5. **datos.gob.es apidata** = índice limpio de los datasets IGAE/INE (sin User-Agent especial).
6. Relevancia TFM: capa de números = servida (Eurostat/INE/IGAE/GHED, extracción trivial); capa de decisiones = inexistente como base de datos → un extractor BOE sería contribución original (línea "extractor de datos" avalada por el tutor en Entrega 1).
