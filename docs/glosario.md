# Glosario de siglas y acrónimos

Todas las siglas que aparecen en el repositorio (fuentes de datos, bases,
métodos y códigos de contabilidad nacional). Referencia rápida para lectores
de la memoria, el código y el dashboard.

## Instituciones y fuentes de datos

| Sigla | Nombre completo | Qué aporta al proyecto |
|---|---|---|
| **MITMA** | Ministerio de Transportes, Movilidad y Agenda Urbana (España) | Licencias de vivienda, mercado de suelo, SIU |
| **SIU** | Sistema de Información Urbana (MITMA) | Suelo clasificado como urbanizable, por municipio |
| **INE** | Instituto Nacional de Estadística (España) | IPV, IPC, salarios, compraventas, hipotecas, población |
| **IMF / FMI** | International Monetary Fund / Fondo Monetario Internacional | WEO, GMD, GFS-COFOG, WoRLD |
| **OECD / OCDE** | Organisation for Economic Co-operation and Development | Precios de vivienda, land cover, estadísticas de ingresos |
| **BIS** | Bank for International Settlements | Índices de precios residenciales (ES desde 1971) |
| **ECB / BCE** | European Central Bank / Banco Central Europeo | Euríbor, Bank Lending Survey |
| **BdE** | Banco de España | Serie histórica de criterios de crédito (superada por el BCE) |
| **FHFA** | Federal Housing Finance Agency (EE. UU.) | Índices de precios de vivienda por estado/metro |
| **WHO / OMS** | World Health Organization / Org. Mundial de la Salud | GHED, GHO |
| **UN DESA** | United Nations Dept. of Economic and Social Affairs | Stock internacional de migrantes |
| **JST** | Jordà-Schularick-Taylor (los tres autores) | Macrohistory Database: series fiscales y de precios largas |
| **JMP / JME** | Joint Monitoring Programme / Joint Malnutrition Estimates (OMS-UNICEF) | Agua-saneamiento; stunting-wasting |
| **UIS** | UNESCO Institute for Statistics | Gasto educativo, resultados de aprendizaje |
| **SIPRI** | Stockholm International Peace Research Institute | Gasto militar (vía Banco Mundial) |
| **UNICEF** | United Nations Children's Fund | Marco MODA de pobreza infantil |
| **UNDP / PNUD** | United Nations Development Programme | Coproductor del MPI |
| **OPHI** | Oxford Poverty & Human Development Initiative | Coproductor del MPI |

## Bases de datos y datasets

| Sigla | Nombre completo | Contenido |
|---|---|---|
| **WEO** | World Economic Outlook (FMI) | Totales fiscales + proyecciones, 1800–2031 |
| **GMD** | Global Macro Database (vinculada al FMI) | Deuda/gasto/ingreso/impuestos encadenados % PIB, historia larga |
| **GFS** | Government Finance Statistics (FMI) | Estadísticas de finanzas públicas |
| **COFOG** | Classification of the Functions of Government | Las 10 funciones de gasto (sanidad, educación, defensa…) |
| **WoRLD** | World Revenue Longitudinal Database (FMI) | Ingresos por tipo de impuesto, 195 países, 1980– |
| **WDI** | World Development Indicators (Banco Mundial) | PIB pc, resultados, series de política |
| **GHED** | Global Health Expenditure Database (OMS) | Gasto sanitario público/privado |
| **GHO** | Global Health Observatory (OMS) | Obesidad, tabaquismo (confusores de A1) |
| **WWBI** | Worldwide Bureaucracy Indicators (Banco Mundial) | Empleo y salarios públicos |
| **ODA / AOD** | Official Development Assistance / Ayuda Oficial al Desarrollo | Ayuda donante % RNB |
| **SPI** | Statistical Performance Indicators (Banco Mundial) | Auditoría de capacidad estadística |
| **HLO** | Harmonized Learning Outcomes (Banco Mundial) | Resultados de aprendizaje comparables |
| **HCI** | Human Capital Index (Banco Mundial) | Índice matriz del HLO |
| **BLS** | Bank Lending Survey (BCE) | Endurecimiento de criterios de crédito (NO el Bureau of Labor Statistics de EE. UU.) |
| **SILC / EU-SILC** | Statistics on Income and Living Conditions | Sobrecarga y hacinamiento en vivienda |
| **AROPE** | At Risk Of Poverty or Social Exclusion (Eurostat) | Pobreza infantil (`arope_ninos`) |
| **MPI** | Multidimensional Poverty Index (PNUD-OPHI) | Recuento de pobreza |
| **MODA** | Multiple Overlapping Deprivation Analysis (UNICEF) | Marco de privación infantil |
| **LUCAS** | Land Use/Cover Area frame Survey (Eurostat) | Porcentaje de suelo artificial |
| **IPV** | Índice de Precios de Vivienda (INE) | House Price Index — el objetivo de T1 |
| **IPC** | Índice de Precios de Consumo (INE) | Deflactor a términos reales |
| **ZHVI** | Zillow Home Value Index | Valor de vivienda por metro EE. UU. |
| **RNB / GNI** | Renta Nacional Bruta / Gross National Income | Denominador de la AOD |

## Métodos y términos de modelado

| Sigla | Significado |
|---|---|
| **MASE** | Mean Absolute Scaled Error — la vara del pronóstico (drift = 0,40) |
| **LOOCV** | Leave-One-Out Cross-Validation — evaluación de las fronteras |
| **OLS / MCO** | Ordinary Least Squares / Mínimos Cuadrados Ordinarios — la regresión simple ganadora |
| **GBM** | Gradient Boosting Machine (LightGBM) — el candidato flexible |
| **MLP** | Multi-Layer Perceptron — el candidato "deep learning" |
| **DL** | Deep Learning / aprendizaje profundo |
| **SARIMAX** | Seasonal ARIMA with eXogenous variables — un candidato de T1 |
| **FE** | Fixed Effects (país + año) — el panel within |
| **CR1 / cluster SE** | Cluster-Robust standard errors — errores agrupados por país |
| **MC** | Monte Carlo — la simulación de deuda a 2070 |
| **r−g** | tipo de interés menos crecimiento — la aritmética de la deuda |
| **β65 / γ** | elasticidades: cuota 65+ → gasto (β), renta → resultado (γ) |
| **RAG** | Retrieval-Augmented Generation — el asistente de pasajes citados |
| **MVP** | Minimum Viable Product — el dashboard/API |
| **CCAA** | Comunidades Autónomas — las regiones de España (unidad del panel T1) |
| **PSA / CEAC** | (no usados aquí; términos de otros proyectos HEOR) |

## Etiquetas T1/A1/A2/D1 (nomenclatura interna del proyecto)

| Etiqueta | Módulo |
|---|---|
| **T1** | Pronóstico de asequibilidad de vivienda por CCAA (núcleo avalado) |
| **A1** | Frontera de rendimiento ajustado (gasto → resultado): salud, educación, bienestar |
| **A2** | Tipologías de composición del gasto (PCA + KMeans) |
| **D1** | Simulador de escenarios de deuda 2024–2050 (+ horizonte 50 años) |

## Códigos de contabilidad nacional (en `rev_*` y `gov_10a_exp_*`)

Sistema Europeo de Cuentas (SEC/ESA); aparecen como sufijos de fichero.

| Código | Concepto |
|---|---|
| `TE` | Gasto total (Total Expenditure) |
| `TR` | Ingreso total (Total Revenue) |
| `D1` | Remuneración de asalariados |
| `D3` | Subvenciones |
| `D62` | Prestaciones sociales |
| `D9` | Transferencias de capital |
| `P2` | Consumos intermedios |
| `P51G` | Formación bruta de capital fijo (inversión) |
| `D2REC` | Impuestos sobre la producción (recibidos) |
| `D5REC` | Impuestos sobre la renta (recibidos) |
| `D61REC` | Cotizaciones sociales (recibidas) |
| `D91REC` | Impuestos sobre el capital (recibidos) |
| `GF01`–`GF10` | Las diez funciones COFOG (01 servicios generales … 10 protección social) |
