# Desglose fiscal mundial + reconciliación de fuentes (2026-07-19)

Pregunta: ¿podemos desglosar gasto E ingresos públicos de España y del resto de
países, y comprobar que usamos los valores correctos por tipo? Respuesta: sí a
ambos lados, y la comprobación está ejecutada con fuentes independientes.

## 1. Fuentes nuevas (API nueva del FMI api.imf.org, sin clave; verificadas)

| Fuente | Qué da | Cobertura | Archivo |
|---|---|---|---|
| IMF **GFS_COFOG** | Gasto por las 10 funciones COFOG, % PIB | **89 países**, 1972–2025 | `gfs_cofog_global.csv` |
| IMF **WoRLD** | Ingresos por tipo: total, impuestos (renta personas/sociedades, propiedad, bienes y servicios, ventas, especiales, comercio), cotizaciones, donaciones, otros | **195 países**, 1980–2024 | `world_revenue_global.csv` |
| OCDE **Global Revenue Statistics** | 6 cabeceras de impuestos (clasificación OCDE, compilación independiente) | 146 países, 1990–2024 | `oecd_tax_global.csv` |
| Eurostat `gov_10a_main` | Componentes de ingresos UE que faltaban (D91, D4, D7, ventas, D39) | UE, 1995– | `gov_revenue_detail.csv` |

Cierra el hueco "GFS-COFOG global vía IMF pendiente" declarado en
`expansion_corpus.md` §3. Gold unificado: `gold_fiscal_breakdown.csv`
(108.099 filas, 203 países, lado × categoría × fuente).

## 2. La reconciliación (gold_fiscal_reconciliation.csv): 15/15 checks OK

| # | Check | Resultado |
|---|---|---|
| 1 | **COFOG por función, Eurostat vs IMF** (UE 2015–23, 153 país-año × 10 funciones) | brecha media 0,03–0,06 pp por función — compiladores independientes, mismos valores: **los tipos de gasto que usamos son correctos** |
| 2 | Gasto total Eurostat vs WEO | 0,31 pp de media; único atípico sistemático **Rumanía (3–4,5 pp)**: WEO usa la presentación nacional (caja), Eurostat ESA-devengo — diferencia metodológica conocida, no un error de datos |
| 3 | Ingresos totales Eurostat vs WoRLD vs WEO | 0,29–0,65 pp de media |
| 4 | Presión fiscal like-for-like: WoRLD (impuestos+cotizaciones) vs OCDE (Σ cabeceras) | mediana 0,70 pp en 96 países; ESP 2022: 37,1 vs 36,8 — ojo declarado: la OCDE cuenta las cotizaciones como impuesto (cabecera 2000), GFS las separa; comparar sin ese ajuste infla brechas ~12 pp |
| 5 | Aditividad interna WoRLD (total = Σ componentes) | 99 % de país-años cuadran a <1 pp |

Regla operativa que queda fijada: **para la UE, Eurostat es la fuente
canónica; fuera de la UE, IMF GFS/WoRLD; WEO solo para totales largos y
proyecciones (D1)** — y la brecha rumana enseña por qué no se mezclan
presentaciones dentro de un mismo análisis.

## 3. España 2023-24, el desglose que queda validado (% PIB)

- **Gasto** (GFS/Eurostat, 2024): protección social 18,7 · salud 6,3 ·
  servicios generales ~5,5 · educación ~4,4 · asuntos económicos ~4,9 ·
  vivienda 0,5 (el contraste del atlas B3 sigue vivo).
- **Ingresos** (WoRLD, 2023): total 41,2 = impuestos 23,6 (renta personas
  8,7 > sociedades 2,9; bienes y servicios ~9,4) + cotizaciones 13,2 +
  otros ~4,4. Con la OCDE dando 36,8 de presión fiscal 2022 vs 37,1 del FMI.

## 4. Uso en el proyecto

- El A1 (salud) y el atlas ya usaban valores que ahora quedan cross-checked.
- El desglose de INGRESOS mundial abre la pregunta simétrica del stress test
  ("¿qué gastos recortar para bajar al 10 %?") también por el lado de qué
  impuestos suben o bajan — material para el RAG y la defensa.
- 89 países con funciones + 195 con ingresos = base para replicar el A1 en
  otras funciones (educación ya hecho; justicia/defensa posibles).
