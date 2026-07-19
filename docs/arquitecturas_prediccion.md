# Cómo se predicen los resultados: directa, encadenada y condicional

Mapa conceptual de las tres arquitecturas de predicción del proyecto, dónde se
usa cada una y por qué. (Origen: pregunta sobre si, sabiendo predecir las
variables independientes, se puede encadenar una regresión que calcule la
dependiente — el ejemplo clásico: predecir el clima y convertirlo en producción
agrícola con una regresión de rendimientos.)

## Las tres arquitecturas

**1. Predicción DIRECTA.** El objetivo se predice desde su propio pasado (y,
como mucho, desde valores YA OBSERVADOS de otras variables, retardados). No se
predice ningún driver.

**2. Predicción ENCADENADA (two-stage).** Primero se predicen los drivers
(etapa 1), después una regresión estructural los convierte en el objetivo
(etapa 2). El ejemplo clima→cosecha. Su error total es:

    error(driver previsto) × sensibilidad de la regresión + error de la regresión

Regla que gobierna la elección: **encadenar solo compensa cuando el driver es
mucho más fácil de predecir que el objetivo.** Si no, la cadena amplifica.

**3. Predicción CONDICIONAL (escenarios).** La misma regresión de la etapa 2,
pero sin predecir el driver: lo fija el usuario ("SI los salarios crecen un
2 %…"). El error de predecir X se le devuelve a quien pregunta, que
normalmente ya sabe qué escenario le importa. Es predicción honesta cuando el
driver es imprevisible.

## Dónde está cada una en el proyecto

| Pieza | Arquitectura | Detalle |
|---|---|---|
| T1 producción (drift + abanico) | Directa pura | Sin variables independientes; incertidumbre = cuantiles de errores reales |
| T1 candidatos (GBM, GBM+demanda, Chronos, DL global) | Directa con drivers RETARDADOS | Compraventas, hipotecas, Δpoblación, crédito, suelo — siempre valores ya observados en el origen; nunca previstos |
| C1b (SARIMAX + Euríbor) | Encadenada degenerada, declarada | Necesitaba Euríbor futuro → se congeló en el último valor ("tipos constantes"); perdió 0/17 |
| A1 salud / educación | La regresión de la etapa 2, usada SOLA | Explica diferencias entre países hoy (frontera gasto→resultado); no predice el futuro |
| **D1 deuda** | **Encadenada completa — el ejemplo clima→cosecha construido** | Etapa 1: proyecciones demográficas de Eurostat (el driver). Etapa 2: elasticidades entrenadas en panel UE (β65: pensiones 0,91±0,19, sanidad 0,33) → presión de gasto → aritmética r−g → senda de deuda |
| Abanico salarial T1, palancas D1, `POST /scenario` | Condicional | El usuario fija salarios/tipos/consolidación; el sistema calcula |

## Por qué D1 encadena y T1 no (la decisión, con evidencia)

**La demografía cumple la regla; los drivers de vivienda no.**

- Los mayores de 65 de 2050 ya han nacido: la estructura de población tiene
  una inercia enorme y se puede proyectar décadas — por eso D1 encadena, y por
  eso su resultado central (deuda 224 % vs 127 % sin envejecimiento) es
  creíble con bandas.
- Para encadenar en T1 harían falta pronósticos a 2 años de hipotecas,
  migración o tipos — tan difíciles o más que predecir el propio precio. Y el
  proyecto midió el caso LÍMITE favorable: dando a los modelos los valores
  verdaderos observados de los drivers (retardados), ninguno batió al drift
  (quinto contest: mejor resultado 0,401 vs 0,395, 7/17 CCAA, no adoptado).
  Una versión encadenada — con drivers previstos en lugar de verdaderos — es
  matemáticamente peor que ese techo. El ejemplo del clima ilustra la trampa:
  a horizonte de campaña, el clima es MÁS difícil de predecir que la cosecha;
  la agronomía real usa normales climáticas o lluvia ya observada — el mismo
  movimiento que hacen nuestros candidatos con los retardos.

## Síntesis para la defensa

1. El proyecto contiene la arquitectura encadenada que sugiere la pregunta —
   construida y publicada donde su precondición se cumple (D1: driver
   predecible), y probada y rechazada donde no (T1: cinco contests).
2. Cuando la regresión estructural vale pero el driver es imprevisible, no se
   tira la regresión: se degrada honestamente a máquina condicional
   ("si X entonces Y") — escenarios del abanico, palancas de deuda, API.
3. Extensión declarada (no construida): encadenar proyecciones de población
   por CCAA (driver predecible) con la regresión de demanda → perspectiva
   CONDICIONAL de demanda de vivienda por CCAA. Pasaría por el protocolo:
   validación primero, adopción solo si la gana.
