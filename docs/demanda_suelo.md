# Capas de demanda, crédito y suelo (expansión Tier 1-3, 2026-07-19)

Segunda ronda de conectores tras `expansion_corpus.md`: las capas con potencial
predictivo para T1 y la medida de suelo urbanizable pedida.

## 1. Conectores nuevos (todos verificados en vivo)

| Capa | Fuente / id | Cobertura | Archivo |
|---|---|---|---|
| Compraventas de vivienda | INE ETDP tabla **6149** (mensual, CCAA) | 2007M01– | `ine_compraventas_ccaa.csv` |
| Hipotecas constituidas (viviendas) | INE HPT tabla **76316** (mensual, CCAA) | 2003M01– | `ine_hipotecas_ccaa.csv` |
| Población residente trimestral | INE ECP tabla **56940** (FK 19–22 = Q1–Q4) | **1971Q1–** | `ine_poblacion_q_ccaa.csv` |
| Mercado de suelo: nº, valor, superficie, precio | MITMA Boletín v2, sección 36 (**36100500/36200500/36300500/36400500**) | 2004Q1– | `mitma_suelo_ccaa.csv` |
| Stock de suelo por clases urbanísticas | MITMA **SIU**, añadas 2021 y 2025 (la de 2021 rescatada del Wayback: el CDN la retiró) | 2 añadas | `siu_clases_suelo_ccaa.csv` |
| Criterios de crédito vivienda | **ECB BLS** `BLS.Q.ES.ALL.Z.H.H.B3.ST.S.FNET` (la serie del BdE muere en 2021) | 2003Q1– | `bls_criterios_vivienda.csv` |
| Interés de búsqueda (Trends) | Google Trends ES, 3 términos, ventanas de 5 años encadenadas por solape | 2004M01–, añada congelada | `gtrends_vivienda.csv` |

Bloqueados esta ronda (motivo declarado): **Idealista/Fotocasa** (API con clave y
licencia; sin clave en el entorno), **Catastro suelo vacante** (el portal
estadístico antiguo es ahora una SPA sin ficheros descargables localizables;
serie ideal si reaparece), **Registradores** (microdatos de pago).

## 2. La medida de suelo urbanizable y su evolución

Dos piezas complementarias (no existe una serie anual larga de stock):

**STOCK planificado (SIU)** — `gold/gold_suelo_ccaa.csv`: % de la superficie
estudiada clasificada como urbanizable (delimitado + no delimitado) por CCAA,
2021 vs 2025. La cobertura municipal cambia entre añadas (p. ej. Andalucía
49 %→71 % de municipios), así que se comparan porcentajes y la cobertura viaja
en la tabla. Lecturas: Murcia es la CCAA con más suelo urbanizable relativo
(20,3 %→21,2 %; 2.378 km²); Madrid, con cobertura 100 % en ambas añadas,
REDUCE su urbanizable (9,4 %→8,9 %: se consume más de lo que se reclasifica);
La Rioja sube (7,3 %→9,0 %) aunque con cobertura baja (11 %→17 %, leer con
cautela); Comunitat Valenciana baja (5,4 %→4,3 %).

**FLUJO transmitido (MITMA)** — superficie de transacciones de suelo: pico
117 millones m²/año (2004), colapso a 20 (2012), 2024 en 25 — **el mercado de
suelo sigue a ~1/5 del pico** mientras los precios de vivienda aceleran: la
restricción de oferta empieza en el suelo, no solo en los visados. Figura
`docs/figures/atlas/b17_suelo_transacciones.png`.

## 3. Contest de validación (protocolo intacto) — CUARTO resultado negativo

Candidato: el MISMO LightGBM global de C2 (hiperparámetros congelados) +
6 features nuevas conocidas en el origen (compraventas YoY t−1, hipotecas YoY
t−1, Δpoblación YoY t−1, superficie de suelo YoY t−2, BLS t−1, Trends t−1).
Orígenes 2019Q4–2023Q4, h=1–8, test 2024+ intocable.

| | MASE h≤4 | CCAA que baten al drift |
|---|---|---|
| drift (producción) | **0.395** | — |
| GBM sin capas nuevas | 0.666 | 0/17 |
| GBM + demanda/crédito/suelo | 0.653 | **0/17** |

Las capas nuevas mejoran al GBM un 2 % — y siguen a +65 % del drift. A h5–8:
0.88 vs 0.80, tampoco. **El modelo de producción no cambia.** Lectura honesta:
en una ventana de validación sin giros de ciclo, ningún regresor rezagado
supera a la persistencia con deriva; el valor de estas capas es (a) descriptivo
(suelo, crédito, demografía en el atlas y el RAG) y (b) opción de giro para
2026+ (los volúmenes colapsan antes que los precios en 2007-08 — eso solo se
podrá validar con datos futuros, nunca readjudicando el test gastado).
