# Panel internacional de vivienda y suelo (2026-07-19)

Respuesta a "¿se puede obtener en otros países la evolución del suelo edificable
y el precio medio de la vivienda?". Resumen: la evolución de PRECIOS sí y con
solidez (tres fuentes oficiales que se cruzan); los NIVELES (€/m² comparables)
no existen en abierto; el suelo urbanizable LEGAL no está armonizado en ningún
organismo — se usan proxies de suelo consumido y se declara la diferencia.

## 1. Fuentes conectadas (verificadas en vivo)

| Fuente | Qué da | Cobertura | Archivo |
|---|---|---|---|
| BIS `WS_SPP` (API v2) | Índice de precios residenciales nominal y REAL | 61 áreas, trimestral; núcleo desde años 70 (ES real 1971–, US 1927–) | `bis_precios_vivienda.csv` |
| OECD `DF_HOUSE_PRICES` (SDMX) | HPI, real, **precio/renta disponible** (HPI_YDH), precio/alquiler | 50 países, trimestral, 1960– | `oecd_precios_vivienda.csv` |
| OECD `DF_LAND_COVER` (ENV) | Superficie artificial LC_SUR_ART (km², satélite ESA) | ~200 territorios, épocas 2000–2022 | `oecd_suelo_artificial.csv` |
| Eurostat `lan_lcv_ovw` (LUCAS) | % suelo artificial (encuesta de campo) | UE, oleadas 2009/12/15/18/22 | `lucas_artificial.csv` |

Gold: `gold/gold_vivienda_global.csv` (país × precio/renta, crecimiento real
2000– y 2015–, suelo artificial 2022 y su crecimiento 2000–22, LUCAS %).
Figura: `docs/figures/atlas/b18_vivienda_global.png`.

## 2. Lo que NO existe (declarado)

- **€/m² medio comparable entre países**: ninguna serie oficial abierta.
  Eurostat tiene un ejercicio experimental reciente; el resto son consultoras
  (PDF) o crowdsourcing con licencia. La comparación honesta es por RATIOS
  (precio/renta), igual que en el panel español.
- **Suelo urbanizable legal**: concepto nacional no armonizado. El SIU español
  es una rareza; Alemania/Francia/Inglaterra publican los suyos en formatos
  heterogéneos (conector por país, extensión declarada). Los proxies de
  arriba miden suelo CONSUMIDO, no suelo PERMITIDO — la brecha española
  (mercado de suelo a 1/5 del pico con precios acelerando) es invisible para
  el satélite.

## 3. Lecturas (descriptivas, no causales)

| País | Precio/renta (2015=100) | Real desde 2015 | Suelo artificial 2000–22 |
|---|---|---|---|
| Portugal | **178,8** | +125,5 % | +103 % |
| Países Bajos | 135,5 | +61,4 % | +65 % |
| **España** | **132,5** | **+46,4 %** | **+119,8 %** |
| EE. UU. | 126,9 | +35,8 % | +51 % |
| Irlanda | 124,0 | +62,4 % | +79 % |
| Alemania | 107,0 | +18,4 % | +50 % |
| Francia | 93,6 | +4,4 % | +74 % |
| Italia | 89,1 | −3,7 % | +62 % |

- España es el país del panel núcleo que **más suelo artificial ha creado en
  proporción (+120 % desde 2000, el doble que Alemania o EE. UU.) y aun así
  su precio/renta está un 32 % por encima de 2015**: urbanizar mucho no ha
  comprado asequibilidad.
- Generalizando a 40 países: Spearman(precio/renta, crecimiento de suelo
  artificial 2000–22) = **+0,01** — sin relación transversal. Coherente con el
  hallazgo español: el cuello de botella no es el suelo físico consumido sino
  el suelo que llega al mercado y se convierte en vivienda (transacciones a
  1/5 del pico, visados a un tercio).
- El contraste Portugal (+125 % real) / Italia (−3,7 %) delimita el rango
  europeo completo; España va por la senda portuguesa, no la italiana.
- BIS real 1971–: España acumula TRES ciclos completos (1974–85, 1986–97,
  1998–2013) y el actual; la figura b18 los muestra contra DE/FR/IT/PT/IE.

## 4. Uso en el proyecto

Capa descriptiva y de contexto (atlas + RAG + defensa): sitúa el caso español
en distribución internacional. NO entra como feature de T1 (frecuencia y
retardos incompatibles con el panel trimestral CCAA; y la lección del cuarto
negativo aplica igual). El D1 global de deuda ya usaba WEO; este panel es su
espejo de vivienda.
