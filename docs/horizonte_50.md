# Horizonte 50 años: economía y bienestar 2025–2070/2075

Respuesta ejecutada a "¿puede el modelo predecir la evolución de la economía y
el bienestar social a 50 años?". Veredicto previo (auditoría): el sistema
estaba bien estructurado para EXTENDERSE a 50 años como máquina de sobres
condicionales — nunca como pronosticador. Las cinco piezas del plan están
implementadas; esta nota explica qué hace cada una y cómo leerlas.

## Por qué "predicción a 50 años" no existe (medido, no opinado)

La regla de arquitectura del proyecto (docs/arquitecturas_prediccion.md):
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

## Las cinco piezas (código → salida)

### 1. La frontera re-estimada como panel (`analysis/bienestar_panel.py`)
El transversal ("países con más ingresos tienen menos mortalidad infantil",
β=−0,011) NO es el parámetro de simulación: re-estimado DENTRO de país (efectos
fijos de país y año, errores CR1; 184 países × 2000–2023):
- a retardo 2–5 años el efecto del ingreso es **nulo** (+0,0006±0,0013);
- a retardo 8 aparece: **−0,0036±0,0015** por pp de PIB (estructural);
- la renta sí: γ = **−0,509±0,059** por unidad de log-PIBpc, neto de la mejora
  secular mundial (absorbida por los efectos de año).
Hallazgo honesto: simular con el transversal sobrestimaría ~3× lo que compra
el dinero a estos horizontes. Parámetros en `api/models/bienestar_panel_params.json`.

### 2. Monte Carlo del simulador de deuda (`analysis/mc_d1.py`)
La incertidumbre de PARÁMETROS entra en las bandas: 4.000 trayectorias por
escenario muestreando elasticidades demográficas (β65 pensiones N(0,912,
0,194), sanidad N(0,325, 0,240) — misma forma funcional potencial del motor),
tipo de mercado y crecimiento, con variante demográfica aleatoria entre las 6
de Eurostat. Coherencia verificada con el D1 discreto: mediana central 2050 =
231 vs 224 del menú; banda 90 % [178–303] (más ancha que la discreta 198–267,
como debe). Salida: `gold_escenarios_deuda_mc.csv`.

### 3. Horizonte 2070
EUROPOP llega a 2070 → el sobre se extiende: central 2070 mediana 409 % PIB
[272–619]; consolidación 2,5 pp → 298 [174–482]; tipos +1 pp → 518 [345–783].
DECLARADO: aritmética compuesta a 46 años = sobre condicional a continuidad
institucional; el propio ancho (347 pp entre p5 y p95) es el mensaje.

### 4. Sobres de bienestar 2050/2070 (`analysis/bienestar_50.py`)
Cadena con los únicos parámetros legítimos (panel within): crecimiento de la
renta (γ) + capacidad fiscal (β retardo 8). Menú, no pronóstico — y en
VARIACIÓN RELATIVA a la senda base (la mejora secular NO se extrapola):
- crecimiento 1 % pc/año → mortalidad <5 −12 % (2050), −21 % (2070) vs base;
- 1,5 % → −18 % / −29 %; estancamiento 0,5 % → −6 % / −11 %;
- palanca fiscal ±2,5 pp de ingresos: ±0,8 % adicional — real pero de segundo
  orden frente al crecimiento (el hallazgo del panel, mostrado sin maquillar).
Salida: `gold_bienestar_50.csv`.

### 5. El pseudo-backtest de continuidad (`analysis/backtest_50y.py`)
Descrito arriba; salida `gold_backtest_50y.csv`. No valida (solo hay 2
ventanas independientes en la historia): CALIBRA. Es todo el poder estadístico
que existe a ese horizonte, y más del que declara la mayoría de ejercicios
oficiales a 2070.

## Cómo leer el sistema a 50 años (síntesis para la defensa)

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
