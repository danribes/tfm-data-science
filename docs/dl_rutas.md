# Dos rutas de deep learning contra el protocolo T1 (2026-07-19)

Pregunta: ¿qué bases de datos permiten entrenar DL de verdad? Respuesta
ejecutada: las dos rutas viables con datos abiertos, ambas bajo la parrilla
pre-registrada intacta (orígenes 2019Q4–2023Q4, h=1–8, test 2024+ gastado e
intocable, adopción solo con ≥12/17 CCAA batiendo al drift a h≤4).

## Ruta 2 — Modelo fundacional zero-shot (Chronos-Bolt, Amazon)

Preentrenado sobre millones de series, aplicado sin ajuste al IPV por CCAA
(`analysis/foundation_t1.py`). Caveat declarado: su corpus de preentrenamiento
no es auditable — si contiene series que solapan la ventana, juega con ventaja
y aun así pierde.

| h | chronos | drift |
|---|---|---|
| 1–4 (media) | 0.460 | **0.395** |
| 5–8 (media) | 1.032 | **0.796** |

**0/17 CCAA.** Mejor que todos los candidatos clásicos (GBM 0.653–0.666) pero
por debajo del campeón en TODOS los horizontes, y se descompone a h≥6 (1.36 a
h=8): la misma reversión a la media importada que hundió al GBM en el test.

## Ruta 1 — DL global entrenado en 1.760 series regionales extranjeras

`connectors/hpi_regional_global.py`: FHFA (410 metros + 51 estados, 1975–),
Zillow (894 metros, 2000–), UK Land Registry (405 áreas, 1968–) → 208.640
observaciones trimestrales. España JAMÁS en el entrenamiento; ventanas con
objetivo ≤2019Q3 (nada posterior a los orígenes desde ninguna geografía).
MLP 16→128→128→64→8 sobre Δlog, 113.649 ventanas (`analysis/dl_global_t1.py`).

| h | dl_global | drift |
|---|---|---|
| 1 | 0.242 | 0.241 |
| 2 | **0.344** | 0.358 |
| 3 | 0.481 | 0.465 |
| 4 | 0.574 | 0.553 |
| 1–4 (media) | 0.401 | **0.395** |
| 5–8 (media) | 0.862 | **0.796** |

**7/17 CCAA — no alcanza el criterio (12/17): no se adopta.** Pero es el
primer candidato en CINCO contests que llega al empate técnico con el campeón,
y el único que gana a algún horizonte (h=2). La hipótesis "ha visto morir
docenas de booms en EE. UU./UK y eso transfiere a España" tiene ya su primera
evidencia — insuficiente bajo la regla, y la regla no se relaja.

## Veredicto y camino declarado

1. Producción sigue siendo drift. Quinto contest, quinta no-adopción; la
   diferencia es que esta vez el margen es 0,006 de MASE, no 0,26.
2. La ruta prometedora es la 1 (corpus regional global), no la 2 (fundacional
   genérico): el dominio importa más que la escala del preentrenamiento.
3. Siguiente paso legítimo: revalidar dl_global cuando existan orígenes 2026+
   (fuera de la ventana ya juzgada). Nada de re-tunear contra la ventana
   actual: sería optimizar contra un examen ya corregido.
4. El interés de dl_global para la defensa: si algún candidato puede anticipar
   un GIRO (el punto ciego estructural del drift), es el que entrenó con giros
   extranjeros. El día que el ciclo español gire, esta apuesta se podrá
   auditar en tiempo real.
