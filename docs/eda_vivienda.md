# EDA §2-A — Hallazgos y decisiones de especificación (T1)

*2026-07-18. Ejecuta el análisis previo al modelado definido en la [Entrega 4 §2-A](entregas/04_analisis_modelado.md). Script reproducible: [`analysis/eda_vivienda.py`](../analysis/eda_vivienda.py); figuras y tablas en [`docs/figures/eda/`](figures/eda/). Las tres decisiones de especificación del §6.2 de la Entrega 4 quedan fijadas aquí, ANTES de comparar modelos.*

---

## 1. Hallazgos descriptivos

**El ciclo es nacional; el nivel de presión es regional.** El heatmap y los small multiples muestran la misma forma en las 17 CCAA (caída 2008–2013/14, mínimo, recuperación acelerada desde 2021), con diferencias sostenidas de nivel: en 2024 el ratio va de 0,99 (Rioja/Extremadura, recuperó los niveles de 2015) a 1,35 (Madrid), con Andalucía (1,31) y Cataluña (1,30) detrás y la media nacional en 1,26.

![Heatmap del ratio por CCAA y año](figures/eda/f1_heatmap_ratio_ccaa.png)

**La divergencia precio-salario es el fenómeno central.** Desde 2014 el IPV nacional sube de ~96 a ~193 (2015=100) mientras el salario indexado solo alcanza ~127; el ratio pasa de 1,0 a 1,26 en 2024 (y ~1,5 provisional en 2025–26, pendiente del salario EES). El tramo provisional del salario va marcado en la figura, como exige el diseño anti-fuga.

![IPV vs salario nacional](figures/eda/f2_nacional_ipv_salario.png)

![Ranking 2024](figures/eda/f3_ranking_2024.png)
![Small multiples](figures/eda/f4_small_multiples_ratio.png)

## 2. Diagnósticos de series (deciden la especificación)

| Diagnóstico | Resultado | Implicación |
|---|---|---|
| ADF sobre el nivel (log IPV), 20/20 series | p > 0,05 en todas | No estacionario en nivel: nadie modela el nivel directamente |
| ADF sobre Δlog, 20/20 series | p > 0,05 en todas (Nacional: 0,75) | **El crecimiento tampoco es estacionario según ADF**: persistencia alta |
| KPSS sobre Δlog (Nacional) | p = 0,01 (rechaza estacionariedad) | Concuerda con ADF: el crecimiento tiene componente persistente/tendencial |
| ADF sobre Δ²log (Nacional) | p ≈ 0,000 | La segunda diferencia sí es claramente estacionaria |
| AR(1) de Δlog (Nacional) | 0,61 | El crecimiento de este trimestre predice buena parte del siguiente |
| STL (periodo 4) | tendencia domina; estacionalidad débil | La componente S existe pero es secundaria frente a la T |

Matiz honesto: con n≈77 trimestres que contienen dos regímenes largos (caída 2008–14, expansión 2014–25) el ADF tiene poca potencia y "unit root en el crecimiento" y "crecimiento con cambios de régimen lentos" son observacionalmente parecidos. Por eso la decisión no se juega a un test: la arbitra el backtesting.

![STL nacional](figures/eda/f5_stl_nacional.png)
![ACF/PACF de Δlog](figures/eda/f6_acf_pacf_dlog.png)

## 3. Correlaciones cruzadas con las exógenas candidatas

Sobre Δlog IPV nacional (tabla completa en `figures/eda/xcorr_table.csv`):

| Exógena | Mejor retardo | r | Lectura |
|---|---|---|---|
| Euríbor (nivel) | t−3 | −0,19 | Signo esperado: tipos altos, crecimiento menor ~3 trimestres después. Magnitud modesta |
| Δ salario | t−5 | +0,33 | Los salarios llegan al precio con ~1 año largo de retardo |
| Δlog IPC | t0 | +0,25 | Componente nominal contemporánea |
| Δ Euríbor | t−8 | +0,28 | Signo contraintuitivo a 2 años; probable artefacto del ciclo de rebote, NO se persigue (regla anti-metric-chasing) |

Ninguna |r| supera 0,35: las exógenas aportan, pero poco — coherente con lo pre-registrado: los baselines serán difíciles de batir y el criterio de aceptación (MASE < 1) no está garantizado.

![Correlación cruzada con Euríbor](figures/eda/f7_xcorr_euribor.png)

## 4. Decisiones de especificación (quedan fijadas)

**D1 — Transformación:** la variable modelada es **Δlog del IPV** con estructura AR y deriva (SARIMAX (p,1,q) con constante sobre el log-nivel), que captura la persistencia observada (AR(1)=0,61). Dada la evidencia ADF/KPSS, se añade UNA variante d=2 al conjunto de candidatos como comprobación, aceptando su coste en ruido. Decide el backtesting rolling-origin, no el test de raíz unitaria.

**D2 — Pooling:** el ciclo común domina y la heterogeneidad es de nivel → el candidato global (LightGBM sobre el panel apilado con efectos CCAA) es razonable y los per-CCAA (SARIMAX) también; ambos se mantienen tal como estaban diseñados. La dispersión 0,99–1,35 en 2024 justifica conservar efectos regionales en cualquier candidato.

**D3 — Exógenas:** entran Euríbor (retardos 2–4), Δlog IPC (contemporáneo y t−1) y crecimiento salarial (retardos 4–6, con flag provisional). El Δ Euríbor a t−8 NO entra (artefacto probable). Los drivers V2 (suelo, ICSC, extranjeros, `oferta_nueva` de la Revisión 1) siguen siendo deseables, no núcleo.

## 5. Conexión con el MVP

F1 (heatmap), F2 (divergencia nacional) y F3 (ranking) son las tres figuras centrales del MVP descritas en la Entrega 2; F4 (small multiples) alimenta la discusión regional. Todas salen de la capa gold con un único script reproducible.
