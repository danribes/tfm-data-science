# D1 — Simulador de escenarios fiscales: la deuda española 2024–2050

*2026-07-18. Responde la pregunta D1 del [PLAN_MAESTRO](PLAN_MAESTRO.md) tal como quedó REFORMULADA (§ Bloque D): un MENÚ de sendas con consecuencias modeladas, nunca una prescripción — elegir qué partida priorizar es política, no estadística, y el propio gráfico lo dice. Script: [`analysis/escenarios_d1.py`](../analysis/escenarios_d1.py); salida: `storage/gold/gold_escenarios_deuda.csv`; tests: [`tests/test_escenarios.py`](../tests/test_escenarios.py).*

---

## 1. Mecánica (transparente y auditable)

`d(t+1) = d(t)·(1+r)/(1+g) − pb(t)` con:
- **r**: tipo efectivo (intereses/deuda = 2,28 % en 2023) que converge al tipo de mercado del escenario a velocidad 1/8 (vencimiento medio ~8 años) — la subida de tipos tarda una década en trasladarse del todo.
- **g**: crecimiento nominal = real (palanca) + deflactor 2 %.
- **pb**: saldo primario 2023 (−0,9 %PIB) **menos la presión demográfica del motor de proyección del propio repo**: pensiones y sanidad escalan con la senda 65+ de Eurostat según las elasticidades entrenadas en el panel UE (0,91 y 0,33) → **+3,1 pp de PIB en 2035, +6,6 pp en 2050** (variante base).

## 2. El menú (deuda %PIB en 2050)

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

## 3. Lo que el menú enseña (sin prescribir)

1. **La variable dominante no es ninguna palanca fiscal: es la demografía.** La distancia central↔contrafactual (97 pp) es mayor que el efecto de cualquier palanca individual del menú.
2. **Ninguna palanca aislada estabiliza la deuda**; las sendas que la doblegarían combinan varias (consolidación + crecimiento + gestión del envejecimiento — p. ej. la migración de B13/B16, que es exactamente la variante HMIGR de la banda).
3. **El coste de la propuesta original del proyecto** (más vivienda e infraestructura a déficit) queda cuantificado con su consecuencia (+12 pp de deuda en 2050) en vez de descartado — eso pedía la reformulación del Bloque D.
4. **Advertencia de método:** aritmética determinista con elasticidades constantes y sin retroalimentaciones (r no reacciona al nivel de deuda, g no reacciona a la inversión). Es un mapa de sensibilidades, no un pronóstico. Horizonte cortado en 2050: componer más allá es especulación.

## 4. Encaje en el TFM

Cierra el bloque analítico del plan: **T1** (forecasting con protocolo completo) + **atlas B1–B16** + **A1** (rendimiento ajustado) + **D1** (escenarios). Las piezas comparten capa gold, estilo de figuras, tests y la misma regla: incertidumbre y límites en primera plana.
