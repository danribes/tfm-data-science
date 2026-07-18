# Diccionario de datos — Variante C (vivienda como consecuencias)

*v1, 2026-07-18. Responde a la decisión "¿extraer todo o seleccionar?" y fija el diccionario (dimensiones/campos) de cada dataset con la marca de qué columnas son NECESARIAS (✔) para los bloques B1–B6 del [plan](PLAN_vivienda_consecuencias.md). Provenance: **[V]** = esquema verificado en vivo (consulta real); **[D]** = documentado, pendiente de smoke-test en build (regla de la 3ª ronda: ningún código entra en gold sin test).*

---

## 0. Decisión: extracción SELECTIVA, nunca volcado completo

**Veredicto: seleccionar.** Razones:
1. El volcado completo de ~125 fuentes es ETL-suicidio (semanas de trabajo sin valor analítico; la mayoría de columnas jamás se usarían).
2. El contrato gold del plan ya impone la disciplina: cada conector extrae **series nombradas** con filtros explícitos, cae en `raw/` como evidencia y se transforma a formato largo `(geo, periodo, variable, valor, flag)`.
3. Criterios de inclusión de una columna: (a) alimenta un bloque B1–B6 concreto; (b) pasa smoke-test; (c) cabe en el grano del gold (país/CCAA × año/trimestre).
4. Presupuesto objetivo: **~15 grupos de series, gold < 100 MB.** Todo lo demás queda catalogado en el landscape, no extraído.

---

## 1. Capa fiscal (B1–B2)

### 1.1 Eurostat `gov_10a_exp` — gasto por función × tipo económico **[V]** (consultas reales 2026-07-16/17)
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

### 1.2 INE COFOG España (`aappgastcofog95_23.xlsx`) **[V]** (descargado y abierto)
7 hojas ("Tabla 1..7"); estructura tabla-informe (función × año, 1995–2023). ✔ Necesario: tabla función×año total AAPP + subsectores. Uso: B1 España profundo; validación cruzada del dato Eurostat.

### 1.3 IGAE series por subsector **[V]** (acceso verificado; UA navegador)
XLSX por subsector (central/CCAA/local/SS) catalogados en datos.gob.es. ✔ Función vivienda + sanidad + educación por subsector. [D] estructura exacta de columnas — smoke-test en build.

### 1.4 Liquidaciones presupuestarias CCAA (Hacienda) [D]
Clasificación funcional (política 26x vivienda) × económica (cap. 1–8) × CCAA × año, ~2002→ online. ✔ gasto vivienda por CCAA (B3). ⚠️ La estructura de los XLSX CAMBIA entre años — presupuestar parser por vintage.

### 1.5 BOE (API sumarios + XML) **[V]** (parser probado: PGE 2023 y 2021, leyes CCAA)
Campos JSON sumario: `identificador, titulo, url_pdf/xml, seccion, departamento`. XML: `<titulo>, <texto>` con `<table>` parseables. ✔ Para B5: fecha, id, título, tabla "Acceso vivienda" del PGE. Pesetas pre-2002 (÷166,386).

## 2. Outcomes de vivienda (B2–B3)

### 2.1 EU-SILC `ilc_lvho07a` (sobrecarga >40% renta) [D]
Dims esperadas: `freq, incgrp, geo, time` (+unit=PC). ✔ TOTAL población; opcional por grupo de renta (distributivo). 2003→. Smoke-test pendiente (endpoint estructura devolvió 400 — usar consulta de datos como test).

### 2.2 EU-SILC `ilc_lvho05a` (hacinamiento) [D]
Dims: `freq, age, sex, hhtyp?, geo, time`. ✔ TOTAL; edad joven (18–34) como sensibilidad. 2003→.

### 2.3 Panel de asequibilidad propio (gold del TFM) **[V]** (construido)
`asequibilidad_ccaa.csv`: `ccaa, anyo, ipv_general, salario_medio_anual, salario_idx, ratio_asequibilidad` ✔ TODAS — es la variable de consecuencias de B3–B4. (Nota: ficheros hoy en `_old/` — restaurar al reactivar pipeline.)

## 3. Núcleo España precios/drivers (B3, heredado del TFM) **[V]** (pipeline operativo)

| Dataset | Campos | Necesarios |
|---|---|---|
| INE IPV — ⚠️ **RENUMERADA 2026-07-18: 76201/49300 devuelven 404; trimestral = 80270, anual = 80271** (descubierto en barrido de esquemas; actualizar `config.py`) | serie → `ccaa, tipo_vivienda (general/nueva/2ªmano), trimestre, índice`; metadatos vía `GRUPOS_TABLA/{t}` (VARIABLES_TABLA no existe) | ✔ todos; ⚠️ bug conocido: no se persiste — arreglar |
| INE IPC 76136 | `ccaa, anyo/mes, índice general` | ✔ SOLO series "Índice general" (bug del promedio: valores 15–26 = corruptos) |
| INE EES 28191 | `ccaa, anyo, salario_medio` | ✔ "Ambos sexos"+"Media"; desfase ~1,5 años (flag) |
| BdE Euríbor `ti_1_7.csv` | `fecha, euribor_12m` (diario 1999→) | ✔ media trimestral |
| MITMA suelo 36400500 | `provincia, trimestre, €/m²` | ✔ agregado a CCAA (ruido provincial) |
| MITMA ICSC | `mes, índice costes construcción` (nacional, base 2021) | ✔ media trimestral |

## 4. Comparables internacionales (B2)

### 4.1 OECD Analytical House Prices [D]
Indicadores: precio nominal/real, **price-to-income ✔, price-to-rent ✔**, rentas; trimestral, décadas, ~40 países. ID del dataflow a fijar en build (la búsqueda MCP no lo resolvió — usar OECD Data Explorer, familia `DSD_AN_HOUSE...`).

### 4.2 BIS Residential Property Prices [D]
CSV bulk: `ref_area, period(Q), value, unit(index/yoy), nominal/real`. ✔ índice real, ~60 países (series largas, algunas 1970→). Contexto/robustez de B2.

### 4.3 OECD Affordable Housing Database [D]
Tablas XLSX por indicador (PH = policy, HC = conditions): stock vivienda social ✔, instrumentos ✔. No es panel limpio — usar como covariable estática/contexto.

### 4.4 Eurostat `prc_hpi_q` [D]
Dims: `purchase (TOTAL/NEW/EXST), unit (I15_Q, RCH_Q...), geo, time(Q)`. ✔ TOTAL×índice. Backup del IPV + comparador UE.

## 5. Trabajadores públicos (feature de composición, B2)

### 5.1 WWBI (WB source=64) **[V]** (diccionario completo extraído: 302 indicadores)
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

### 5.2 Eurostat D1 por función — ya cubierto en 1.1 (na_item=D1 ✔).

## 6. Demografía/amplificador (B4)

| Dataset | Campos | Necesarios |
|---|---|---|
| INE Estadística de Migraciones **[V]** (pipeline) | `ccaa, anyo, inmigración/emigración/saldo` | ✔ saldo por CCAA |
| INE padrón/población | `ccaa, anyo, población` | ✔ Δpoblación |
| Eurostat `migr_imm1ctz`/`migr_emi2` [D] | `citizen/agedef, geo, time` | ✔ flujo total país (tier UE) |
| UN DESA Migrant Stock [D] | matriz `origen × destino × año(quinq.)` | ✔ stock destino (si tier global) |
| INE Censo 2021 / ECH [D] | hogares, tenencia | contexto |

## 7. Resumen: el gold objetivo de la Variante C

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
