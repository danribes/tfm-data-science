# Resultados: fiscal y bienestar

El atlas del gasto público, las series históricas 1703–2025, el desglose mundial de gasto e ingresos, las fronteras de rendimiento (salud, bienestar), la pobreza, los escenarios de deuda, el horizonte a 50 años y la paridad de poder adquisitivo.

## Contenido

- [Atlas de evolución del gasto público — lectura guiada (F2.1)](#atlas-de-evolución-del-gasto-público-lectura-guiada-f21)
- [Series históricas de gasto e ingresos: denominador verificado y empalme 1703–2025](#series-históricas-de-gasto-e-ingresos-denominador-verificado-y-empalme-17032025)
- [Desglose fiscal mundial + reconciliación de fuentes (2026-07-19)](#desglose-fiscal-mundial-reconciliación-de-fuentes-2026-07-19)
- [A1 — Rendimiento ajustado del gasto sanitario público (F3.1, módulo salud)](#a1-rendimiento-ajustado-del-gasto-sanitario-público-f31-módulo-salud)
- [Indicadores de bienestar y pobreza infantil (marco MPI/MODA) — 2026-07-19](#indicadores-de-bienestar-y-pobreza-infantil-marco-mpimoda-2026-07-19)
- [¿Se puede predecir la pobreza y la pobreza infantil?](#se-puede-predecir-la-pobreza-y-la-pobreza-infantil)
- [D1 — Simulador de escenarios fiscales: la deuda española 2024–2050](#d1-simulador-de-escenarios-fiscales-la-deuda-española-20242050)
- [Horizonte 50 años: economía y bienestar 2025–2070/2075](#horizonte-50-años-economía-y-bienestar-202520702075)
- [¿Es predecible la renta en paridad de poder adquisitivo (PPA)?](#es-predecible-la-renta-en-paridad-de-poder-adquisitivo-ppa)
- [Stress test — ocho preguntas de usuario real contra el sistema](#stress-test-ocho-preguntas-de-usuario-real-contra-el-sistema)

---

## Atlas de evolución del gasto público — lectura guiada (F2.1)

*2026-07-18. Una figura por pregunta del bloque B del [PLAN_MAESTRO](PLAN_MAESTRO.md), generadas desde la capa gold por [`analysis/atlas.py`](../analysis/atlas.py) (figuras en [`docs/figures/atlas/`](figures/atlas/)). España siempre resaltada frente a la mediana del panel europeo (banda p25–p75) o la mediana mundial del histórico GMD/JST (202 países). Todo descriptivo: el atlas muestra, no prescribe.*

---

| # | Figura | Lectura (con el dato) |
|---|---|---|
| B1 | ![](figures/atlas/b01_gasto_total_siglo.png) | **El siglo de la expansión:** la mediana mundial pasa de ~10 %PIB (1900) a ~30 % (hoy). España sigue la ola con retraso y la remonta en los 80: 11 % en 1900, 45,4 % en 2023. Los picos del Reino Unido son las guerras mundiales. |
| B2 | ![](figures/atlas/b02_composicion_economica.png) | **Qué compra el gasto español:** prestaciones sociales (D62) y salarios (D1) son el grueso; los intereses (D41) caen de ~5 %PIB (1995) a 2,4 % (2023) — el dividendo del euro — y financian en la práctica la expansión de lo demás. |
| B3 | ![](figures/atlas/b03_vivienda_publica_vs_total.png) | **La figura de la Revisión 1:** la inversión residencial TOTAL española va de 6 %PIB (1995) a 11,7 % (pico 2006), se hunde a 3,9 % (2015) y vuelve a 5,8 % (2025); el gasto público GF06 se mueve entre 1,3 y 0,5 %PIB. La palanca pública es un orden de magnitud menor que la promoción privada — contexto obligatorio de cualquier conclusión sobre vivienda. |
| B4 | ![](figures/atlas/b04_sanidad_ghed.png) | **Sanidad pública:** España sube de 4,9 %PIB (2000) a 6,7 % (2023), por encima de la mediana mundial y por debajo de Alemania; el escalón COVID es visible en casi todas las series. |
| B5 | ![](figures/atlas/b05_inversion_publica.png) | **El ajuste silencioso:** la FBCF pública española cae del ~5 % al 3,0 %PIB tras 2010 y no se recupera — la inversión fue la variable de ajuste de la consolidación. |
| B6 | ![](figures/atlas/b06_empleo_publico.png) | **Empleo público:** ~24,8 % del empleo total (2020, WWBI), en la zona alta de la banda del panel. |
| B7 | ![](figures/atlas/b07_salarios_publicos.png) | **Masa salarial pública:** España ~10–12,5 %PIB, estable y algo por encima de la mediana; el pico coincide con la caída del denominador en 2009–2013 y en 2020. |
| B8 | ![](figures/atlas/b08_deuda_siglo.png) | **La deuda en U:** ≈124 %PIB tras el desastre del 98, mínimo ≈30 % en 1960, 105 % hoy. España termina el siglo XX donde lo empezó, con dos guerras mundiales de distancia y muy por encima de la mediana mundial actual. |
| B9 | ![](figures/atlas/b09_proteccion_social.png) | **Protección social (GF10):** de 14,3 %PIB (1995) a 18,5 % (2023), con máximos de 21,9 % en la doble crisis; la partida más grande del Estado y la que más crece. |
| B10 | ![](figures/atlas/b10_desempleo.png) | **La anomalía persistente:** el paro español (máximo 26,1 % en 2013; 12,2 % en 2023) vive estructuralmente por encima de la banda p25–p75 europea durante toda la muestra. |
| B11 | ![](figures/atlas/b11_intereses.png) | **Intereses:** de ~5 %PIB (1995) a 2,4 % (2023) pese a duplicarse la deuda — el precio del dinero importó más que el volumen. La subida de tipos de 2022+ asoma al final de la serie. |
| B12 | ![](figures/atlas/b12_pensiones_envejecimiento.png) | **La tenaza demográfica:** pensiones de vejez 10,2 %PIB (2023) con la población 65+ pasando del 15,0 % (1995) al 20,1 % (2023). Los dos paneles se mueven juntos — el numerador es demografía. |
| B13 | ![](figures/atlas/b13_migracion.png) | **El amortiguador migratorio:** el stock de migrantes en España se multiplica (UN DESA, 1990–2024) y la inmigración anual alcanza ~1,25 millones (2023) — la única fuerza que frena el envejecimiento del panel B12/B16. |
| B14 | ![](figures/atlas/b14_oda.png) | **La otra cara fiscal:** para la mediana de países receptores la AOD ronda el 1–3 % de la RNB, con el percentil 90 muy por encima — hay Estados cuyo "presupuesto" depende del exterior; contexto para no leer el atlas solo en clave OCDE. |
| B15 | ![](figures/atlas/b15_deficit_siglo.png) | **El déficit como sismógrafo:** −11,2 %PIB (2009), −9,9 % (2020), −3,3 % (2023). Las crisis se leen mejor en el déficit que en ninguna otra serie. |
| B16 | ![](figures/atlas/b16_proyeccion_65.png) | **El futuro que empuja todo lo anterior:** la población 65+ española pasa del 20 % actual al **33,1 % en 2070** (línea base Eurostat); las seis variantes demográficas se abren en abanico — este es el insumo del motor de proyección de pensiones y sanidad 2023–2070. |

### Notas de método

- Histórico (B1, B8, B15): GMD 2026-06 + JST; la mediana mundial se calcula solo en años con ≥30 países informando. El desglose funcional continuo no existe antes de ~1970 (PLAN_MAESTRO, advertencia B2–B5): por eso las figuras funcionales empiezan en 1995 (Eurostat COFOG).
- Panel europeo: ~40 geos Eurostat (más agregados), banda p25–p75 y mediana; España en azul siempre.
- B3 usa la serie `nama_10_an6` (FBCF en viviendas, %PIB) extraída el 2026-07-18 vía el mismo cliente Eurostat del pipeline (`storage/processed/gfcf_dwellings.csv`), cumpliendo el compromiso de la [Revisión 1](entregas/04_analisis_modelado.md).
- B6 (WWBI) llega solo hasta 2020 y B7 (masa salarial WWBI/Eurostat) hasta 2022: cobertura declarada, no se interpola.

---

## Series históricas de gasto e ingresos: denominador verificado y empalme 1703–2025

Tres preguntas, tres respuestas medidas (`analysis/fiscal_historia.py`).

### 1. ¿Tenemos el PIB para calcular los porcentajes? Sí, y se comprueba

JST Macrohistory (18 países, 1870–2020) publica NIVELES: PIB nominal, ingresos
y gasto en moneda corriente. Se recalculó cada ratio desde los niveles y se
comparó con el publicado: **diferencia máxima 0,000000 pp en 2.516 país-años**.
El denominador existe, es explícito y los porcentajes son reproducibles desde
cifras primarias — no dependemos de ratios opacos.

### 2. ¿Cuadran las series históricas con las modernas (1995–2025)? Depende de la fuente — y la diferencia es el hallazgo

Brechas medias en la ventana de solape 1995–2020 (11 países UE, 286 país-años),
contra Eurostat como canónico:

| Fuente | Gasto | Ingresos | Diagnóstico |
|---|---|---|---|
| GMD (Global Macro Database) | **0,04 pp** | 1,63 pp | continuo en perímetro AAPP |
| WEO histórico | 0,50 pp | 0,49 pp | pero con SALTO de perímetro en 1995 (ES: 12,8→44,5) |
| JST Macrohistory | 21,4 pp | 21,6 pp | es SOLO administración central — no comparable sin decirlo |

La brecha de 21 pp de JST no es un error: es la diferencia entre Estado central
y AAPP totales (CCAA+local+Seguridad Social). Es la trampa clásica de las
series fiscales largas, y queda medida y declarada. Regla fijada: el empalme
canónico usa **Eurostat (1995+) + GMD (antes)** — GMD demuestra continuidad de
perímetro a través de 1995 (ES: 46,4 en 1994 → 44,1 en 1995). WEO se queda
para lo que ya hacía (totales largos comparativos y proyecciones D1); JST,
como capa declarada de "Estado central" y como fuente de niveles.

Caveat honesto: antes de ~1960 el "perímetro AAPP" es en la práctica el Estado
más lo poco que existía de administración territorial; el perímetro crece con
el propio Estado del bienestar y eso forma parte de la historia contada, no de
un error de medición.

### 3. ¿Qué se puede decir? España 1703–2025 (gold_fiscal_historico.csv, figura b19)

| Año | Gasto | Ingresos | Momento |
|---|---|---|---|
| 1850 | 9,1 | 9,2 | Estado liberal mínimo |
| 1900 | 11,0 | 11,5 | el "Estado del 10 %" (referencia del stress test) |
| 1935 | 17,3 | 15,1 | II República |
| 1960 | 17,8 | 15,1 | autarquía tardía |
| 1977 | 29,1 | 27,3 | arranque de la transición fiscal |
| 1995 | 44,1 | 37,3 | Estado del bienestar construido en ~18 años |
| 2007 | 39,2 | 41,1 | superávit del boom |
| 2012 | 49,2 | 37,7 | la tijera de la crisis: 11,5 pp de déficit |
| 2023 | 45,4 | 42,1 | meseta actual |

Lecturas para la defensa: (a) la transformación 1977–1995 (+15 pp en 18 años)
es EL evento fiscal español del siglo, y coincide con el arco del atlas B;
(b) el déficit no es un estado permanente histórico: 1850–1935 ingresos y
gasto van pegados (patrón oro, sin deuda social), la brecha crónica nace con
el Estado del bienestar y se abre en crisis (1993, 2009-13, 2020); (c) el
"Estado del 10 %" del stress test tiene fecha real en España: 1900. Panel
completo de 18 países en el mismo gold (Irlanda desde 1926: no existía antes).

---

## Desglose fiscal mundial + reconciliación de fuentes (2026-07-19)

Pregunta: ¿podemos desglosar gasto E ingresos públicos de España y del resto de
países, y comprobar que usamos los valores correctos por tipo? Respuesta: sí a
ambos lados, y la comprobación está ejecutada con fuentes independientes.

### 1. Fuentes nuevas (API nueva del FMI api.imf.org, sin clave; verificadas)

| Fuente | Qué da | Cobertura | Archivo |
|---|---|---|---|
| IMF **GFS_COFOG** | Gasto por las 10 funciones COFOG, % PIB | **89 países**, 1972–2025 | `gfs_cofog_global.csv` |
| IMF **WoRLD** | Ingresos por tipo: total, impuestos (renta personas/sociedades, propiedad, bienes y servicios, ventas, especiales, comercio), cotizaciones, donaciones, otros | **195 países**, 1980–2024 | `world_revenue_global.csv` |
| OCDE **Global Revenue Statistics** | 6 cabeceras de impuestos (clasificación OCDE, compilación independiente) | 146 países, 1990–2024 | `oecd_tax_global.csv` |
| Eurostat `gov_10a_main` | Componentes de ingresos UE que faltaban (D91, D4, D7, ventas, D39) | UE, 1995– | `gov_revenue_detail.csv` |

Cierra el hueco "GFS-COFOG global vía IMF pendiente" declarado en
`DATOS.md` §3. Gold unificado: `gold_fiscal_breakdown.csv`
(108.099 filas, 203 países, lado × categoría × fuente).

### 2. La reconciliación (gold_fiscal_reconciliation.csv): 15/15 checks OK

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

### 3. España 2023-24, el desglose que queda validado (% PIB)

- **Gasto** (GFS/Eurostat, 2024): protección social 18,7 · salud 6,3 ·
  servicios generales ~5,5 · educación ~4,4 · asuntos económicos ~4,9 ·
  vivienda 0,5 (el contraste del atlas B3 sigue vivo).
- **Ingresos** (WoRLD, 2023): total 41,2 = impuestos 23,6 (renta personas
  8,7 > sociedades 2,9; bienes y servicios ~9,4) + cotizaciones 13,2 +
  otros ~4,4. Con la OCDE dando 36,8 de presión fiscal 2022 vs 37,1 del FMI.

### 4. Uso en el proyecto

- El A1 (salud) y el atlas ya usaban valores que ahora quedan cross-checked.
- El desglose de INGRESOS mundial abre la pregunta simétrica del stress test
  ("¿qué gastos recortar para bajar al 10 %?") también por el lado de qué
  impuestos suben o bajan — material para el RAG y la defensa.
- 89 países con funciones + 195 con ingresos = base para replicar el A1 en
  otras funciones (educación ya hecho; justicia/defensa posibles).

---

## A1 — Rendimiento ajustado del gasto sanitario público (F3.1, módulo salud)

*2026-07-18. Primera instanciación global de la pregunta A1 del [PLAN_MAESTRO](PLAN_MAESTRO.md) ("¿qué país es más eficiente gastando?"), respondida como RENDIMIENTO AJUSTADO CON INCERTIDUMBRE, nunca como liga. Script: [`analysis/rendimiento_a1.py`](../analysis/rendimiento_a1.py); salida: `storage/gold/gold_rendimiento_pais.csv` (164 países); tests: [`tests/test_rendimiento.py`](../tests/test_rendimiento.py).*

---

### 1. Diseño (declarado antes de mirar resultados)

Outcome: esperanza de vida al nacer, media 2015–2019 (pre-COVID a propósito). Exposición: gasto sanitario público %PIB (GHED), media 2010–2014 — retardo de 5 años. Controles: log PIB pc PPP, obesidad, tabaquismo, % urbano. Muestra: 164 países con casos completos. Grupos de renta: cuartiles de PIB pc (proxy declarado). Validación: leave-one-country-out; los residuales publicados son SIEMPRE out-of-fold. Aceptación del GBM: MAE ≤ 0,90·OLS **y** Spearman ≥ 0,8 del residual entre 3 definiciones de gasto.

### 2. Resultados de la selección

| Modelo | MAE LOOCV (años) |
|---|---|
| mediana del cuartil de renta | 2,79 |
| **OLS (ganador)** | 2,82 |
| spline (GAM-lite) | 3,24 |
| LightGBM | 2,95 |

- **El GBM no cumple el criterio** (necesitaba ≤ 2,54): tercera vez consecutiva en el proyecto que la regla pre-registrada tumba al modelo flexible. El multiverso sí era estable (Spearman 0,83 con `che_gdp`, 0,88 con `public_share`), pero la precisión no acompaña con n=164.
- **Lectura incómoda y honesta:** hasta el OLS empata con la mediana del grupo de renta (2,82 vs 2,79). La renta explica la mayor parte de la esperanza de vida entre países; el margen del gasto y los controles, a esta granularidad, es pequeño. Cualquier "eficiencia" que se lea en este módulo es un efecto de segundo orden — y así se dice.

### 3. El funnel (la respuesta a A1)

![Funnel A1](figures/a1/a1_funnel.png)

- **España: +2,7 ± 3,5 años → por encima de lo esperado, pero DENTRO de la banda de su grupo.** Exactamente el caso que justifica el "nunca una liga": un titular diría "España, campeona de la eficiencia sanitaria"; el intervalo dice "buena posición, indistinguible de sus pares de renta alta con esta evidencia".
- Solo **16 de 164 países** quedan fuera de su banda del 90 %. Negativos: Nigeria (−15,8), Nauru, Esuatini, Lesoto — VIH/sida y fragilidad, no "ineficiencia del gasto". Positivos: Albania (+6,3), Costa Rica (+5,6) — casos clásicos de outperformance sanitaria con gasto modesto.
- La forma de embudo aparece: las bandas se estrechan del cuartil pobre (±~7 años) al rico (±~3,5) — la heterogeneidad no explicada se concentra donde la renta es baja.
- EE. UU.: residual ligeramente negativo con el gasto público más alto del cuartil — la anomalía conocida, aquí con su intervalo.

![Contribuciones](figures/a1/a1_contribuciones.png)

*Procedencia de las explicaciones: las contribuciones por variable y el campo `explicacion` del gold provienen del MODELO PUBLICADO (OLS, contribuciones estandarizadas), no del GBM rechazado; el GBM solo se reajusta con fines comparativos y sus contribuciones no se publican.*

### 4. Límites (en primera plana, PLAN_MAESTRO §6)

1. **Asociación, no causalidad**: el retardo de 5 años mitiga, no resuelve, la endogeneidad.
2. **n=164 países es la restricción dominante**: por eso ganan los modelos simples y por eso las bandas son anchas. El paso natural es el panel por bloques quinquenales (más n efectivo), declarado como siguiente iteración.
3. La falacia ecológica aplica: nada de esto habla de sistemas sanitarios concretos.
4. El outcome pre-COVID evita confundir gestión pandémica con rendimiento estructural; la versión con 2020–2023 es un análisis distinto, no una actualización.

---

## Indicadores de bienestar y pobreza infantil (marco MPI/MODA) — 2026-07-19

Incorpora el marco bienestar ↔ pobreza ↔ pobreza infantil (UN/WB/UNICEF) y lo
conecta con la pregunta central: cuánto bienestar OBJETIVO compra el ingreso
público. Conectores: `connectors/bienestar.py`; frontera:
`analysis/bienestar_a1.py`; gold: `gold_bienestar_pais.csv`.

### 1. Mapeo de los 7 bloques del marco a series implementadas

| Bloque del marco | Serie(s) implementadas | Fuente | Cobertura |
|---|---|---|---|
| 1. Renta/consumo del hogar | Pobreza $3,00/día 2021 PPP (`SI.POV.DDAY`), umbral nacional (`SI.POV.NAHC`), MPI UNDP&OPHI (`SI.POV.MPUN` — `SI.POV.MDIM` está archivada) | WB/UNDP | ~166/107 países |
| 2. Mortalidad <5 | `SH.DYN.MORT` (‰ nacidos vivos) | WB/UN-IGME | 189 países, 2000– |
| 3. Privación material infantil | AROPE <18 (`ilc_peps01n`, edad Y_LT18) | Eurostat | UE, 2015– |
| 4. Malnutrición | Stunting (`SH.STA.STNT.ZS`), wasting (`SH.STA.WAST.ZS`) | WB/JME | 157 países (ricos sin encuesta: ESP NaN, esperado) |
| 5. Educación en dos capas | Adultos 25+ con ≥secundaria baja (`SE.SEC.CUAT.LO.ZS`) + niños de primaria fuera de la escuela (`SE.PRM.UNER.ZS`) | WB/UIS | 186 países |
| 6. Piso de protección social | Cobertura de cualquier programa (`per_allsp.cov_pop_tot`, ASPIRE) | WB | 128 países |
| 7. Piso de servicios | Agua gestionada segura, saneamiento seguro, electricidad, combustibles limpios | WB/JMP | 137–193 países |

Declarado NO implementado (micro o gated): microdatos MPI (OPHI, descarga por
país), MODA de UNICEF (microdatos DHS/MICS), privación infantil específica
UE-SILC (ítem por ítem; el AROPE <18 es el agregado disponible), detalle de
transferencias child-sensitive de ASPIRE.

### 2. La frontera ingreso público → bienestar (protocolo A1 intacto)

Diseño: resultado ~ ingresos públicos % PIB (WoRLD, media 2010–18) + log PIB
pc + urbanización; LOOCV; regla flexible ≤0,90×OLS; conformal 90 % por cuartil
de renta. MLP omitido y declarado (mismo régimen n≈100–185 donde perdió dos
veces bajo reglas idénticas).

| Frontera | n | mediana | OLS | GBM | Publicado |
|---|---|---|---|---|---|
| log mortalidad <5 | 185 | 0,471 | **0,438** | 0,494 (no cumple) | OLS |
| stunting (pp) | 124 | 7,08 | **6,41** | 6,94 (no cumple) | OLS |

- **España**: mortalidad <5 mejor que lo que su renta+ingresos predicen
  (residual −0,51 ± 0,93, dentro de banda — funnel, no ranking).
- Extremos que validan el método: **Guinea Ecuatorial** +2,14 en log (≈8,5×
  la mortalidad esperada para su renta — PIB petrolero sin conversión en
  bienestar) y **Guatemala** +29 pp de stunting sobre lo esperado (la anomalía
  crónica documentada); mejor que lo esperado: Macedonia del Norte y Tonga.
- Cuarta y quinta victoria consecutiva del OLS sobre el flexible en fronteras
  transversales: con n≈100–200 países, la estructura lineal captura la señal.

### 3. El marco completo contra el dinero (Spearman, descriptivo)

| Indicador | rho vs ingresos públicos % PIB |
|---|---|
| Mortalidad <5 | **−0,60** |
| Agua segura | +0,56 |
| Pobreza $3/día | −0,52 |
| Electricidad | +0,51 |
| Stunting / MPI | −0,48 |
| Cobertura protección social | +0,40 |
| Niños sin escolarizar | −0,30 |

Todas las direcciones correctas y fuertes: más capacidad fiscal, menos
privación en todas las dimensiones del marco. La frontera responde la pregunta
fina — QUIÉN convierte mejor su capacidad fiscal en bienestar a renta
comparable — sin caer en la trampa del ranking (bandas conformal siempre).

### 4. Conexión con el resto del proyecto

- Cierra el triángulo: gasto por función (COFOG 89 países) + ingresos por tipo
  (WoRLD 195) + resultados de bienestar (13 series) — "dinero público →
  resultados" medido de punta a punta.
- El RAG y el stress test ganan la dimensión social: la pregunta "¿qué pasa
  con un Estado del 10 %?" ahora tiene contrapartida empírica en el marco
  (los países hoy en ~10 % de ingresos concentran los peores valores de las
  7 dimensiones).
- Réplica del patrón A1 en un tercer dominio con el MISMO protocolo y
  veredicto honesto — evidencia de método, no cherry-picking.

---

## ¿Se puede predecir la pobreza y la pobreza infantil?

Respuesta corta: **depende del tipo de pobreza, y solo como escenario
condicional — nunca como pronóstico automático.** El experimento
(`analysis/pobreza_infantil.py` → `gold/gold_pobreza_infantil.csv`) lo separa
con datos.

### Dos pobrezas distintas, dos respuestas

| Tipo | Qué es | ¿Predecible? | Vía |
|---|---|---|---|
| **Absoluta** (mundo en desarrollo, 3 $/día) | vivir por debajo de un umbral fijo | **Sí**, vía crecimiento de la renta | La frontera ya mostró que la renta domina; los sobres a 50 años la proyectan condicionada al crecimiento |
| **Relativa** (UE, AROPE, incl. infantil) | por debajo del 60 % de la mediana | **No desde el ciclo**; **sí desde la redistribución** | Palanca de transferencias (medida abajo) |

### Lo que NO predice la pobreza relativa: el ciclo económico

Panel de la UE (35 países, 2006–2025, 509 observaciones), efectos fijos de país
y año, errores agrupados: **el paro NO anticipa la pobreza relativa** dentro de
cada país (β ≈ +0,02 por punto de paro, no significativo, ni contemporáneo ni
con un año de retardo). No es un fallo del modelo: es la naturaleza de una
medida RELATIVA — en una recesión bajan a la vez los ingresos de los pobres y la
mediana, así que el umbral se mueve con ellos y la tasa apenas cambia. Un dato
que un LLM a pelo no daría: intuitivamente "más paro → más pobreza", y los datos
dicen que para la pobreza *relativa* no, dentro de cada país.

### Lo que SÍ la predice: la redistribución (palanca medida)

Comparando el AROPE antes y después de transferencias (sin pensiones):
- **España**: las transferencias quitan **5,9 pp** de pobreza total hoy.
- **Media UE**: **8,0 pp**.
- La pobreza infantil se mueve con la total (correlación 0,74 en niveles) y es
  de media **×1,47** — así que las transferencias quitan **~9 pp de pobreza
  infantil** en España.

Esa es la variable con poder predictivo: no el ciclo, sino cuánto redistribuye
el Estado.

### Sobre condicional de pobreza infantil (España, base 33,8 %)

| Palanca (intensidad de transferencias) | Pobreza infantil proyectada |
|---|---|
| +25 % | 31,6 % (−2,2 pp) |
| Sin cambios | 33,8 % |
| −50 % | 38,1 % (+4,3 pp) |
| Sin transferencias | 42,5 % (+8,7 pp) |

Se lee como el resto del sistema: **el usuario fija la palanca (aquí, la
política de transferencias) y el modelo devuelve la consecuencia con su
magnitud medida.** No es un pronóstico de lo que pasará, sino de lo que pasaría
bajo cada decisión.

### Encaje con el resto del proyecto

- Misma arquitectura que la deuda y el bienestar a 50 años: predicción =
  escenario condicional encadenado por una palanca (`docs/METODOLOGIA.md`).
- Refuerza el mensaje central para el tribunal: el sistema no "adivina" la
  pobreza; identifica QUÉ la mueve (la redistribución, no el ciclo — un
  resultado medido, contraintuitivo) y cuantifica cada opción.

### Límites declarados

- In-sample UE; un uso predictivo real pasaría por validación con datos futuros.
- AROPE infantil solo desde 2015 (serie corta); el efecto ×1,47 se estima sobre
  el solape con la total.
- La pobreza absoluta mundial es predecible vía renta, pero con el mismo caveat
  de las fronteras: la renta domina y la capacidad fiscal es de segundo orden a
  estos horizontes (`docs/RESULTADOS_FISCAL_BIENESTAR.md`, `docs/RESULTADOS_FISCAL_BIENESTAR.md`).

---

## D1 — Simulador de escenarios fiscales: la deuda española 2024–2050

*2026-07-18. Responde la pregunta D1 del [PLAN_MAESTRO](PLAN_MAESTRO.md) tal como quedó REFORMULADA (§ Bloque D): un MENÚ de sendas con consecuencias modeladas, nunca una prescripción — elegir qué partida priorizar es política, no estadística, y el propio gráfico lo dice. Script: [`analysis/escenarios_d1.py`](../analysis/escenarios_d1.py); salida: `storage/gold/gold_escenarios_deuda.csv`; tests: [`tests/test_escenarios.py`](../tests/test_escenarios.py).*

---

### 1. Mecánica (transparente y auditable)

`d(t+1) = d(t)·(1+r)/(1+g) − pb(t)` con:
- **r**: tipo efectivo (intereses/deuda = 2,28 % en 2023) que converge al tipo de mercado del escenario a velocidad 1/8 (vencimiento medio ~8 años) — la subida de tipos tarda una década en trasladarse del todo.
- **g**: crecimiento nominal = real (palanca) + deflactor 2 %.
- **pb**: saldo primario 2023 (−0,9 %PIB) **menos la presión demográfica del motor de proyección del propio repo**: pensiones y sanidad escalan con la senda 65+ de Eurostat según las elasticidades entrenadas en el panel UE (0,91 y 0,33) → **+3,1 pp de PIB en 2035, +6,6 pp en 2050** (variante base).

### 2. El menú (deuda %PIB en 2050)

| Escenario | 2050 | Lectura |
|---|---|---|
| Contrafactual sin envejecimiento | 127 % | La inercia pura apenas desestabiliza: el problema no es el punto de partida |
| **Central: demografía sin respuesta** | **224 %** (banda 198–267) | La presión de pensiones+sanidad, compuesta 26 años, domina todo lo demás |
| Crecimiento real 2 % | 200 % | Crecer ayuda mucho, no basta solo |
| Consolidación gradual (+0,25 pp/año hasta +2,5) | 172 % | Un esfuerzo fiscal considerable… que solo AMORTIGUA la senda |
| +1 pp inversión (vivienda+FBCF) 2025–35 a deuda | 236 % | El coste en deuda de la pregunta original del proyecto, en cifra: +12 pp sobre el central en 2050 |
| Tipos de mercado al 4,5 % | 256 % | La aritmética r−g castiga rápido con deuda alta |

Banda del central: 18 sendas (6 variantes demográficas × tipos de mercado 3,0/3,5/4,0).

![Escenarios de deuda](figures/d1/d1_deuda_escenarios.png)

### 3. Lo que el menú enseña (sin prescribir)

1. **La variable dominante no es ninguna palanca fiscal: es la demografía.** La distancia central↔contrafactual (97 pp) es mayor que el efecto de cualquier palanca individual del menú.
2. **Ninguna palanca aislada estabiliza la deuda**; las sendas que la doblegarían combinan varias (consolidación + crecimiento + gestión del envejecimiento — p. ej. la migración de B13/B16, que es exactamente la variante HMIGR de la banda).
3. **El coste de la propuesta original del proyecto** (más vivienda e infraestructura a déficit) queda cuantificado con su consecuencia (+12 pp de deuda en 2050) en vez de descartado — eso pedía la reformulación del Bloque D.
4. **Advertencia de método:** aritmética determinista con elasticidades constantes y sin retroalimentaciones (r no reacciona al nivel de deuda, g no reacciona a la inversión). Es un mapa de sensibilidades, no un pronóstico. Horizonte cortado en 2050: componer más allá es especulación.

### 4. Encaje en el TFM

Cierra el bloque analítico del plan: **T1** (forecasting con protocolo completo) + **atlas B1–B16** + **A1** (rendimiento ajustado) + **D1** (escenarios). Las piezas comparten capa gold, estilo de figuras, tests y la misma regla: incertidumbre y límites en primera plana.

---

## Horizonte 50 años: economía y bienestar 2025–2070/2075

Respuesta ejecutada a "¿puede el modelo predecir la evolución de la economía y
el bienestar social a 50 años?". Veredicto previo (auditoría): el sistema
estaba bien estructurado para EXTENDERSE a 50 años como máquina de sobres
condicionales — nunca como pronosticador. Las cinco piezas del plan están
implementadas; esta nota explica qué hace cada una y cómo leerlas.

### Por qué "predicción a 50 años" no existe (medido, no opinado)

La regla de arquitectura del proyecto (docs/METODOLOGIA.md):
encadenar solo a través de drivers más predecibles que el objetivo. A 50 años
solo la demografía cualifica. Y el pseudo-backtest (#5) puso número al resto:
proyectar gasto/ingresos con reglas de continuidad sobre las dos ventanas
reales de 50 años del panel histórico (1925→1975, 1975→2025, 18 países) da
errores MEDIANOS de 12,7–21,5 pp de PIB congelando el nivel — y extrapolar la
tendencia previa es PEOR (mediana 23,8, p90 102 pp: quien extrapoló en 1975
la expansión 1960–75 proyectó Estados del 80 % del PIB). España es el caso de
libro: gasto 26,4 % en 1975 → 45,4 % en 2025 (+19 pp que ninguna continuidad
podía ver). **Calibración fijada: cualquier sobre a 50 años más estrecho de
~13 pp de PIB finge certeza.**

### Las cinco piezas (código → salida)

#### 1. La frontera re-estimada como panel (`analysis/bienestar_panel.py`)
El transversal ("países con más ingresos tienen menos mortalidad infantil",
β=−0,011) NO es el parámetro de simulación: re-estimado DENTRO de país (efectos
fijos de país y año, errores CR1; 184 países × 2000–2023):
- a retardo 2–5 años el efecto del ingreso es **nulo** (+0,0006±0,0013);
- a retardo 8 aparece: **−0,0036±0,0015** por pp de PIB (estructural);
- la renta sí: γ = **−0,509±0,059** por unidad de log-PIBpc, neto de la mejora
  secular mundial (absorbida por los efectos de año).
Hallazgo honesto: simular con el transversal sobrestimaría ~3× lo que compra
el dinero a estos horizontes. Parámetros en `api/models/bienestar_panel_params.json`.

#### 2. Monte Carlo del simulador de deuda (`analysis/mc_d1.py`)
La incertidumbre de PARÁMETROS entra en las bandas: 4.000 trayectorias por
escenario muestreando elasticidades demográficas (β65 pensiones N(0,912,
0,194), sanidad N(0,325, 0,240) — misma forma funcional potencial del motor),
tipo de mercado y crecimiento, con variante demográfica aleatoria entre las 6
de Eurostat. Coherencia verificada con el D1 discreto: mediana central 2050 =
231 vs 224 del menú; banda 90 % [178–303] (más ancha que la discreta 198–267,
como debe). Salida: `gold_escenarios_deuda_mc.csv`.

#### 3. Horizonte 2070
EUROPOP llega a 2070 → el sobre se extiende: central 2070 mediana 409 % PIB
[272–619]; consolidación 2,5 pp → 298 [174–482]; tipos +1 pp → 518 [345–783].
DECLARADO: aritmética compuesta a 46 años = sobre condicional a continuidad
institucional; el propio ancho (347 pp entre p5 y p95) es el mensaje.

#### 4. Sobres de bienestar 2050/2070 (`analysis/bienestar_50.py`)
Cadena con los únicos parámetros legítimos (panel within): crecimiento de la
renta (γ) + capacidad fiscal (β retardo 8). Menú, no pronóstico — y en
VARIACIÓN RELATIVA a la senda base (la mejora secular NO se extrapola):
- crecimiento 1 % pc/año → mortalidad <5 −12 % (2050), −21 % (2070) vs base;
- 1,5 % → −18 % / −29 %; estancamiento 0,5 % → −6 % / −11 %;
- palanca fiscal ±2,5 pp de ingresos: ±0,8 % adicional — real pero de segundo
  orden frente al crecimiento (el hallazgo del panel, mostrado sin maquillar).
Salida: `gold_bienestar_50.csv`.

#### 5. El pseudo-backtest de continuidad (`analysis/backtest_50y.py`)
Descrito arriba; salida `gold_backtest_50y.csv`. No valida (solo hay 2
ventanas independientes en la historia): CALIBRA. Es todo el poder estadístico
que existe a ese horizonte, y más del que declara la mayoría de ejercicios
oficiales a 2070.

### Cómo leer el sistema a 50 años (síntesis para la defensa)

1. **Un solo driver pronosticado** (demografía, con sus 6 variantes y las SE
   de sus elasticidades propagadas). Todo lo demás — crecimiento, tipos,
   capacidad fiscal — es palanca del usuario, expuesta como tal.
2. **Sobres, nunca puntos**: deuda con percentiles por año y escenario;
   bienestar en variación relativa con IC95 de parámetros.
3. **Anchura mínima calibrada con 300 años de datos propios** (~13 pp de PIB);
   los sobres publicados la respetan de sobra.
4. **Los límites impresos en la salida**: continuidad institucional supuesta,
   mejora secular no extrapolada, efecto fiscal identificado solo a retardo 8.
   El sistema dice lo que no sabe con la misma precisión que lo que sabe.

---

## ¿Es predecible la renta en paridad de poder adquisitivo (PPA)?

Misma disección que el resto del proyecto (nivel vs evolución; predicción solo
condicional o con vara honesta), aplicada al PIB per cápita en PPA
(`analysis/ppp_predictibilidad.py`, WDI, 242 países 1995–2023). El hallazgo de
convergencia se sometió a **verificación adversarial** (workflow de 4 ataques
independientes que recomputaron sobre los datos reales).

### Respuesta en tres niveles

| Dimensión | ¿Predecible? | Detalle |
|---|---|---|
| **Nivel de PPA** (renta de un país el año que viene) | Sí, trivialmente | Persistencia extrema (correlación 0,92 entre 1995 y 2023) — pero a través de la COVID el naive (último valor) bate al drift (MAE 0,068 vs 0,080): extrapolar tendencia hace daño en un shock, la misma lección que la vivienda |
| **Crecimiento año a año** | Apenas | Autocorrelación AR(1) within-country = +0,11; el crecimiento es casi ruido alrededor de la media del país |
| **Convergencia (¿alcanzan los pobres?)** | Real pero CONDICIONAL | Pendiente −0,0044 (corr −0,31); verificado abajo |

### La convergencia, verificada adversarialmente (3 de 4 ataques superados)

Cuatro verificaciones independientes recomputaron el hallazgo sobre los datos:

1. **Falacia de Galton / reversión a la media** — ✅ SOBREVIVE. La pendiente no
   es un artefacto de error de medida: se mantiene con una ventana de medición
   independiente (2009→2023: −0,0032), hay sigma-convergencia genuina (la
   dispersión baja de 1,159 a 1,107) y la persistencia del nivel es alta (poca
   reversión). No es ruido disfrazado de convergencia.
2. **Selección muestral / outliers** — ✅ SOBREVIVE. Negativa y significativa en
   toda variante (rango jackknife [−0,0046, −0,0042]); NO la impulsan China
   (quitarla la debilita) ni los petroestados. Señal amplia, no de unos pocos.
3. **Ventana / endpoints** — ✅ SOBREVIVE. Estable 1995→2019 (−0,0051) y
   2000→2023 (−0,0044); no es un artefacto COVID (quitar 2023 la refuerza).
4. **Convergencia de club vs global** — ❌ NO SOBREVIVE. Y este es el matiz
   clave: la mitad POBRE de los países NO muestra convergencia significativa
   (p=0,37; los 50 más pobres p=0,69), mientras que se concentra en el club
   RICO (mitad rica −0,0082, p<0,0001). Condicionada por región, la pendiente
   se DUPLICA (−0,0088) — firma clásica de convergencia condicional.

### Veredicto honesto (para el tribunal)

**La convergencia de la PPA es un hallazgo estadísticamente real y robusto —
NO un artefacto — pero la lectura popular "los países pobres alcanzan a los
ricos" está sobredimensionada.** Es convergencia de **club/condicional**: los
países ricos y los de renta media convergen entre sí; los más pobres no dan
señal de alcanzar. Y es económicamente **glacial**: velocidad ~0,47 %/año,
media-vida ~147 años, R² 0,10. En términos de predicción: se puede proyectar
que un país de renta media-alta como España seguirá una senda de convergencia
lenta hacia la frontera, pero no que la desigualdad global entre países se
cierre.

España: log-renta 1995 = 10,42 → 2023 = 10,76; crecimiento medio 1,2 %/año —
una senda de convergencia de club coherente con el resto de la UE.

### Encaje con el proyecto

- Confirma la tesis central: **nivel trivialmente predecible (drift/persistencia),
  giros difíciles, y el uso honesto es el escenario condicional.** La PPA no es
  distinta de la vivienda o la deuda en esto.
- La convergencia de club, verificada, es un input legítimo para las cadenas
  condicionales de bienestar (la renta domina la mortalidad y la pobreza
  absoluta — `docs/RESULTADOS_FISCAL_BIENESTAR.md`): si la renta converge despacio,
  las mejoras de bienestar por la vía de la renta también.

### Límites declarados

- In-sample; verificación adversarial recomputada pero no validación
  out-of-sample formal (media-vida de 147 años excede cualquier ventana).
- 43 de los 230 "países" del cómputo bruto eran agregados WDI; quitarlos no
  cambia la pendiente (−0,0044 con 187 países reales), pero el recuento honesto
  es ~187 países.

---

## Stress test — ocho preguntas de usuario real contra el sistema

*2026-07-19. Ejercicio de validación final: preguntas "de ciudadano/analista" disparadas contra los artefactos construidos. Cada respuesta muestra una de las tres conductas de diseño: (a) responder con números y su incertidumbre, (b) REFRAMEAR si la pregunta es normativa (Bloque D: menú, no prescripción), (c) declarar el hueco si los datos no existen. Script reproducible: [`analysis/stress_test.py`](../analysis/stress_test.py).*

---

### Q1 · "¿Cómo evolucionará la deuda el año que viene en los países del mundo?"

**Conducta: responde (con la fuente en la etiqueta).** Proyección 2026→2027 para 207 países (FMI-WEO servido por el pipeline — el "ancla C1-Modo 3" del plan, no un modelo propio): la deuda sube en el 53 % de los países. Grandes economías: China +5,6 pp de PIB, EE. UU. +2,8, Francia +2,1, Alemania +1,9; bajan Japón (−4,3) y **España (−2,0, el denominador nominal trabajando)**. Extremos: Ucrania +14,5; San Marino −18,9. La aritmética r−g propia (con tipo efectivo calibrado) existe solo para España; extenderla a todos exigiría tipos efectivos por país — hueco declarado.

### Q2 · "¿Qué gastos hay que recortar para bajar al 10 % de impuestos en diez años?"

**Conducta: reframe — el sistema cuantifica, no elige.** El tamaño del cambio: España ingresa 42,1 %PIB y gasta 45,4; un Estado del 10 % exige recortar **35,4 pp de PIB — el 78 % de todo el gasto**. El menú COFOG completo: protección social 18,5 + sanidad 6,6 + educación 4,2 = 29,3 pp — **eliminar íntegramente el Estado del bienestar aún no basta**; habría que llevarse además servicios generales (5,6) o asuntos económicos (5,0). Contexto del atlas (B1): un Estado del 10 % es la mediana mundial de 1900–1910 (10,4 %PIB); hoy solo 5 de 195 países gastan ≤12 %. La elección de qué eliminar es política; el sistema entrega la factura y la foto histórica.

### Q3 · "¿Cuánta superficie hace falta para eliminar el déficit de vivienda en diez años?"

**Conducta: aritmética de orden de magnitud con supuestos declarados (y hueco declarado).** Con la proyección demográfica propia (BSL: +1,15 M habitantes 2025–35 → ~459 mil hogares a 2,5 personas/hogar), un déficit inicial de ~600 mil (supuesto EXTERNO, orden BdE) y 40 mil/año de reposición: **~1,46 M de viviendas en la década, ~146 mil/año**. En superficie: ~16 M m² edificados/año ≈ **1.400–1.500 ha de suelo/año (~14 mil ha en la década)**. Factibilidad histórica (licencias MITMA): es 1,8× el ritmo actual (79 mil/año) y solo el 20 % del pico de 2006 (737 mil) — el país supo construir mucho más. El pipeline NO tiene serie de déficit ni de suelo finalista: déficit, tamaño de hogar, m²/vivienda y edificabilidad son supuestos a la vista, no un modelo.

### Q4 · "¿Cuánta esperanza de vida compra +1 pp de PIB en sanidad?"

**Conducta: responde y se niega a sobre-prometer.** Asociación condicional a la renta (164 países): +1 pp de gasto ↔ **+0,44 años de e0** (IC90 bootstrap +0,17 a +0,74). Pero A1 mostró que la renta domina y que hasta el OLS empata con la mediana del grupo de renta: la asociación es de segundo orden y NO causal. El sistema entrega el coeficiente con su intervalo y el descargo en la misma frase.

### Q5 · "¿Y el rendimiento del gasto educativo?"

**Conducta: hueco declarado.** Lo que hay: España gasta 4,2 %PIB en educación (mediana del panel 4,9; en 1995 era 4,3 — estancado). Lo que falta: outcomes educativos (PISA está en la lista deferred con ruta identificada). Un A1-educación es la misma maquinaria con otro outcome — trabajo futuro concreto, no improvisación.

### Q6 · "Volver a la inversión pública del 5 % del PIB, ¿qué cuesta?"

**Conducta: responde con el simulador y expone la apuesta.** +2 pp de FBCF 2025–2035 financiados a deuda: **+24 pp de deuda en 2050** (248 % vs 224 % central). Si la inversión comprara +0,3 pp de crecimiento permanente (supuesto ilustrativo): 236 % — la apuesta política es exactamente esa elasticidad, que el simulador deliberadamente NO fija (sin retroalimentaciones, declarado).

### Q7 · "¿Y si se reduce un 10 % el empleo público?"

**Conducta: responde y dimensiona contra la fuerza dominante.** Masa salarial 10,9 %PIB → −10 % de plantilla ≈ **1,1 pp de PIB/año** de ahorro (a salario medio constante) → la deuda 2050 baja de 224 % a 196 % (−27 pp). Pero la presión demográfica añade +6,6 pp/año en 2050: **el ahorro cubre menos de una quinta parte de lo que el envejecimiento suma**. No modelado y dicho: efectos sobre servicios, paro y demanda — ~350 mil empleos son economía real.

### Q8 · "¿Qué ajuste neutraliza el envejecimiento en pensiones?"

**Conducta: responde con el motor propio.** Presión pensiones+sanidad: +3,1 pp de PIB en 2035, +6,6 en 2050 (elasticidad al 65+: 0,91 ± 0,19, SE agrupado). Neutralizarla sin recortar exige denominador: crecimiento, empleo o migración — la variante HMIGR de la banda D1 es exactamente ese experimento ya calculado.

---

### Veredicto del stress test

| Conducta esperada | Preguntas | ¿Funcionó? |
|---|---|---|
| Responder con números + incertidumbre | Q1, Q4, Q6, Q7, Q8 | ✅ con fuente, IC o banda en cada caso |
| Reframear lo normativo (menú, no prescripción) | Q2, Q6, Q7 | ✅ cuantifica la factura, no elige la víctima |
| Declarar huecos sin improvisar | Q3 (déficit/suelo), Q5 (outcomes educativos), Q1 (r−g global) | ✅ con la ruta de extensión identificada |

El sistema hace lo que la memoria promete: entrega números con su incertidumbre, convierte las preguntas normativas en menús cuantificados y dice "no lo sé, y esto es lo que faltaría" cuando procede.
