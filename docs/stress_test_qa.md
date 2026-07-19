# Stress test — ocho preguntas de usuario real contra el sistema

*2026-07-19. Ejercicio de validación final: preguntas "de ciudadano/analista" disparadas contra los artefactos construidos. Cada respuesta muestra una de las tres conductas de diseño: (a) responder con números y su incertidumbre, (b) REFRAMEAR si la pregunta es normativa (Bloque D: menú, no prescripción), (c) declarar el hueco si los datos no existen. Script reproducible: [`analysis/stress_test.py`](../analysis/stress_test.py).*

---

## Q1 · "¿Cómo evolucionará la deuda el año que viene en los países del mundo?"

**Conducta: responde (con la fuente en la etiqueta).** Proyección 2026→2027 para 207 países (FMI-WEO servido por el pipeline — el "ancla C1-Modo 3" del plan, no un modelo propio): la deuda sube en el 53 % de los países. Grandes economías: China +5,6 pp de PIB, EE. UU. +2,8, Francia +2,1, Alemania +1,9; bajan Japón (−4,3) y **España (−2,0, el denominador nominal trabajando)**. Extremos: Ucrania +14,5; San Marino −18,9. La aritmética r−g propia (con tipo efectivo calibrado) existe solo para España; extenderla a todos exigiría tipos efectivos por país — hueco declarado.

## Q2 · "¿Qué gastos hay que recortar para bajar al 10 % de impuestos en diez años?"

**Conducta: reframe — el sistema cuantifica, no elige.** El tamaño del cambio: España ingresa 42,1 %PIB y gasta 45,4; un Estado del 10 % exige recortar **35,4 pp de PIB — el 78 % de todo el gasto**. El menú COFOG completo: protección social 18,5 + sanidad 6,6 + educación 4,2 = 29,3 pp — **eliminar íntegramente el Estado del bienestar aún no basta**; habría que llevarse además servicios generales (5,6) o asuntos económicos (5,0). Contexto del atlas (B1): un Estado del 10 % es la mediana mundial de 1900–1910 (10,4 %PIB); hoy solo 5 de 195 países gastan ≤12 %. La elección de qué eliminar es política; el sistema entrega la factura y la foto histórica.

## Q3 · "¿Cuánta superficie hace falta para eliminar el déficit de vivienda en diez años?"

**Conducta: aritmética de orden de magnitud con supuestos declarados (y hueco declarado).** Con la proyección demográfica propia (BSL: +1,15 M habitantes 2025–35 → ~459 mil hogares a 2,5 personas/hogar), un déficit inicial de ~600 mil (supuesto EXTERNO, orden BdE) y 40 mil/año de reposición: **~1,46 M de viviendas en la década, ~146 mil/año**. En superficie: ~16 M m² edificados/año ≈ **1.400–1.500 ha de suelo/año (~14 mil ha en la década)**. Factibilidad histórica (licencias MITMA): es 1,8× el ritmo actual (79 mil/año) y solo el 20 % del pico de 2006 (737 mil) — el país supo construir mucho más. El pipeline NO tiene serie de déficit ni de suelo finalista: déficit, tamaño de hogar, m²/vivienda y edificabilidad son supuestos a la vista, no un modelo.

## Q4 · "¿Cuánta esperanza de vida compra +1 pp de PIB en sanidad?"

**Conducta: responde y se niega a sobre-prometer.** Asociación condicional a la renta (164 países): +1 pp de gasto ↔ **+0,44 años de e0** (IC90 bootstrap +0,17 a +0,74). Pero A1 mostró que la renta domina y que hasta el OLS empata con la mediana del grupo de renta: la asociación es de segundo orden y NO causal. El sistema entrega el coeficiente con su intervalo y el descargo en la misma frase.

## Q5 · "¿Y el rendimiento del gasto educativo?"

**Conducta: hueco declarado.** Lo que hay: España gasta 4,2 %PIB en educación (mediana del panel 4,9; en 1995 era 4,3 — estancado). Lo que falta: outcomes educativos (PISA está en la lista deferred con ruta identificada). Un A1-educación es la misma maquinaria con otro outcome — trabajo futuro concreto, no improvisación.

## Q6 · "Volver a la inversión pública del 5 % del PIB, ¿qué cuesta?"

**Conducta: responde con el simulador y expone la apuesta.** +2 pp de FBCF 2025–2035 financiados a deuda: **+24 pp de deuda en 2050** (248 % vs 224 % central). Si la inversión comprara +0,3 pp de crecimiento permanente (supuesto ilustrativo): 236 % — la apuesta política es exactamente esa elasticidad, que el simulador deliberadamente NO fija (sin retroalimentaciones, declarado).

## Q7 · "¿Y si se reduce un 10 % el empleo público?"

**Conducta: responde y dimensiona contra la fuerza dominante.** Masa salarial 10,9 %PIB → −10 % de plantilla ≈ **1,1 pp de PIB/año** de ahorro (a salario medio constante) → la deuda 2050 baja de 224 % a 196 % (−27 pp). Pero la presión demográfica añade +6,6 pp/año en 2050: **el ahorro cubre menos de una quinta parte de lo que el envejecimiento suma**. No modelado y dicho: efectos sobre servicios, paro y demanda — ~350 mil empleos son economía real.

## Q8 · "¿Qué ajuste neutraliza el envejecimiento en pensiones?"

**Conducta: responde con el motor propio.** Presión pensiones+sanidad: +3,1 pp de PIB en 2035, +6,6 en 2050 (elasticidad al 65+: 0,91 ± 0,19, SE agrupado). Neutralizarla sin recortar exige denominador: crecimiento, empleo o migración — la variante HMIGR de la banda D1 es exactamente ese experimento ya calculado.

---

## Veredicto del stress test

| Conducta esperada | Preguntas | ¿Funcionó? |
|---|---|---|
| Responder con números + incertidumbre | Q1, Q4, Q6, Q7, Q8 | ✅ con fuente, IC o banda en cada caso |
| Reframear lo normativo (menú, no prescripción) | Q2, Q6, Q7 | ✅ cuantifica la factura, no elige la víctima |
| Declarar huecos sin improvisar | Q3 (déficit/suelo), Q5 (outcomes educativos), Q1 (r−g global) | ✅ con la ruta de extensión identificada |

El sistema hace lo que la memoria promete: entrega números con su incertidumbre, convierte las preguntas normativas en menús cuantificados y dice "no lo sé, y esto es lo que faltaría" cuando procede.
