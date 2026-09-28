# `data/` — qué alimenta el modelo, y qué no

Tres carpetas con tres papeles distintos:

- **`gold/`** es el corte congelado, el *vintage* `2026-07-31`. Es lo único que
  lee el motor, y de ahí sale cada cifra que enseña la aplicación.
- **`external/`** son series extranjeras para entrenar y poner a prueba
  modelos. No entran nunca en el motor; se describen en
  [`external/README.md`](external/README.md).
- **`vintages/`** son descargas posteriores hechas con
  `scripts/refresh_vintage.py`. Están fuera del control de versiones y no
  cambian nada hasta que alguien promueve una (ver
  [`docs/ACTUALIZAR_DATOS.md`](../docs/ACTUALIZAR_DATOS.md)).

La página «Estado de las fuentes» de la aplicación sólo comprueba **las 16
fuentes descargables de `gold/manifest.csv`**. Este documento dice qué más hay
y por qué no está ahí.

---

## 1. Lo que lee el motor

| Fichero | Qué aporta | De dónde sale | ¿Lo comprueba «Estado de las fuentes»? |
|---|---|---|---|
| `kpis_perfiles.json` | Valores de partida e historia reciente: 42 indicadores y 21 series | Cada indicador declara su `fuente`. 25 de los 42 vienen de las 16 fuentes del manifiesto; los otros 17, de la tabla de abajo | 25 de 42 |
| `gold_escenarios_deuda.csv` | Senda central: deuda, saldo primario, tipo efectivo, crecimiento nominal y presión demográfica | Heredada del prototipo v16. No es la previsión del FMI: el WEO lleva la deuda al 91,7 % del PIB en 2030 y esta senda al 112,9 %. Su construcción no está en este repositorio | No |
| `gold_projections.csv` | Las seis variantes demográficas (Base, Migración alta…) | Proyecciones de población de Eurostat, EUROPOP2023 | No |
| `estimated_params.json` | `IPV_LR` e `IPV_REV`, los dos únicos parámetros estimados con datos | `tools/gen_estimated_params.py` sobre `gold_ccaa_trimestral.csv`, el IPV regional del INE en 19 territorios | No |
| `gold_analog_panel.csv` y `_stats.json` | El panel de análogos históricos | `scripts/build_analog_panel.py`: API del Banco Mundial, DataMapper del FMI y Penn World Table 10.01. El fichero de la PWT no se conservó en el repositorio | Como «derivado»: se reconstruye, no se descarga |
| `VINTAGE` | La fecha del corte | — | — |

Los 17 indicadores de `kpis_perfiles.json` que no salen de las 16 fuentes:

| Fuente declarada | Indicadores |
|---|---|
| `gov_10a_exp.csv` (Eurostat, gasto por funciones) | 5 |
| `interest_paid.csv` (Eurostat `gov_10a`, D41PAY) | 1 |
| `gold_cuota_teorica.csv` | 3 |
| `gold_escenarios_deuda_mc.csv` | 2 |
| `gold_projections.csv` | 2 |
| `ine_salarios.csv` (INE, EAES) | 1 |
| `life_expectancy_e0.csv` | 1 |
| `bls_criterios_vivienda.csv` (encuesta de préstamos bancarios del BCE) | 1 |
| `ine_hipotecas_ccaa.csv` (INE) | 1 |

Además del dato, el motor lleva unas 35 constantes calibradas en
`engine/constants.py`. No son datos: se documentan en la página «Datos y
método». Dos ficheros de `gold/` sirvieron para fijarlas y no se leen en
ejecución: `gold_cuota_teorica.csv` (la cuota mediana contra la que se calibra
el diferencial hipotecario) y `gold_escenarios_deuda_mc.csv` (el abanico que el
Monte Carlo reproduce dentro de ±2 pp).

## 2. Lo que usa la investigación, no el motor

| Fichero | Para qué |
|---|---|
| `gold/gold_ccaa_trimestral.csv` | Estimación de los parámetros de vivienda, su robustez, el backtest y los regímenes |
| `gold/gold_fiscal_historico.csv` | Saldo público español 1850–2023: regímenes de crisis (`research/regimes.py`) y persistencia fiscal |
| `external/` | Clasificador de impago (etiquetas BoC–BoE y panel del Banco Mundial), dependencia de estado (deuda del FMI) y el experimento de aprendizaje profundo (1.760 series de vivienda de FHFA, Zillow y Reino Unido) |

Sus resultados se congelan en `docs/eval/` y la API los sirve tal cual.

## 3. Ficheros sin lector en el código

Se conservan congelados por trazabilidad, pero ningún código los lee:

- `gold_asequibilidad_ccaa.csv`. El propio `kpis_perfiles.json` lo desaconseja
  («ratio precario — usar gold_cuota_teorica para esfuerzo»).
- `imf_GGXCNL_NGDP.json`, `imf_GGXONLB_NGDP.json` e `imf_GGXWDG_NGDP.json`.
- `gold_bienestar_pais.csv` y `gold_pobreza_infantil.csv` se citan en la
  aplicación como procedencia, pero sus valores llegan al motor a través de
  `kpis_perfiles.json`.

## 4. Los dos inventarios de procedencia

- **`gold/manifest.csv`**, 18 filas: las 16 fuentes que `refresh_vintage.py`
  sabe volver a descargar y los 2 artefactos derivados. 16 de las 18 filas no
  tienen `sha256`, así que contra este vintage sólo se puede comparar el
  tamaño.
- **`gold/provenance_vintage_manifest.csv`**, 141 filas: el registro de las
  descargas originales del 18 y 19 de julio de 2026. Es la cifra de «141
  descargas» de la portada. Son descargas, no fuentes: hay **85 fuentes
  distintas**, porque algunos ficheros se descargaron hasta siete veces. Una
  fuente es una URL y un nombre, no sólo una URL: 11 series de Eurostat
  comparten la URL de `gov_10a_main` porque el registro no anotó sus
  parámetros, y cada una tiene su nombre y su tamaño. Los ficheros crudos no se
  conservaron; lo congelado son las tablas construidas con ellos.

  | Organismo | Descargas | Fuentes distintas |
  |---|---:|---:|
  | Ministerio de Transportes (licencias de obra) | 75 | 24 |
  | Eurostat | 42 | 41 |
  | FMI (WEO) | 8 | 6 |
  | INE | 4 | 3 |
  | OCDE | 3 | 2 |
  | Ministerio de Vivienda (clasificación del suelo, SIU) | 2 | 2 |
  | BIS | 2 | 2 |
  | FHFA (EE. UU.) | 2 | 2 |
  | BCE (encuesta de préstamos bancarios) | 1 | 1 |
  | Zillow (EE. UU.) | 1 | 1 |
  | HM Land Registry (Reino Unido) | 1 | 1 |
  | **Total** | **141** | **85** |

  **Ninguna de sus URL coincide con las del manifiesto**, y ninguna se vuelve
  a descargar. Sumadas las 16 del manifiesto, son **101 fuentes de datos
  distintas de 12 organismos**; la página «Estado de las fuentes» las lista
  todas. Las cuenta `tools/gen_sources_status.py`, no esta tabla: si cambian,
  la página cambia con ellas.

Que haya dos inventarios que no se solapan es herencia del proyecto anterior,
no un diseño. Unificarlos exige reconstruir las tablas `gold` desde las
fuentes, que es el pendiente anotado en
[`docs/REPRODUCIBILITY.md`](../docs/REPRODUCIBILITY.md).

## 5. Huecos declarados

Lo que falta se declara, no se rellena. Son los mismos huecos que enseña la
página «Datos y método»:

- **Mora bancaria (NPL, Banco de España).** La serie sigue sin conectar; el
  riesgo de crédito del perfil de banca se aproxima con paro y colateral.
- **Bases de cotización del RETA.** Sin API pública; la senda de la cuota de
  autónomo no está modelada.
- **Control de la corrupción (WGI, Banco Mundial).** La API está archivada;
  sólo hay descarga manual.
- **Contratos menores.** La señal vive a nivel de contrato, sin serie pública.
- **Paro regional.** El corte no lo trae, y por eso la ley de Okun no se
  estima: se calibra.
