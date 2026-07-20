# Comparativa detallada: asistente de IA solo vs modelo completo

Informe completo, pregunta a pregunta, del experimento de ablación
(`docs/ablacion_llm.md`). Muestra qué responde un asistente de IA **por sí solo**
frente a qué responde **el mismo asistente apoyado en el modelo completo**
(sus datos y sus cálculos), y cuál es el valor verdadero que produce el sistema.

Todos los números salen de `storage/gold/gold_ablacion_llm.csv`, generado por
`analysis/ablacion_llm.py` con Gemini 2.5 Pro el 2026-07-19.

## Qué significan las tres columnas

- **Modelo completo (verdad)**: el número que calcula el sistema — la capa de
  datos + los modelos estadísticos + los motores de simulación. Es la respuesta
  correcta contra la que se compara todo.
- **IA sola**: el asistente de IA respondiendo de memoria, sin acceso al
  proyecto. Simula "preguntar a alguien muy leído, sin dejarle consultar nada".
- **IA + modelo**: el mismo asistente, pero al que primero se le entregan los
  resultados calculados del proyecto y solo puede responder a partir de ellos.

Un acierto = caer dentro de una tolerancia razonable del valor verdadero
(entre 5 % y 25 % según la pregunta; para la correlación, ±0,05 absoluto).

## Marcador global

| | Aciertos | Error relativo mediano |
|---|---|---|
| **IA sola** | **3 / 12** | 27 % |
| **IA + modelo completo** | **11 / 12** | 0 % |

La diferencia es masiva y en la dirección que exige el tutor: la capa de
matemáticas y datos es la que produce los resultados; el asistente, sin ella,
no los reproduce.

---

## Detalle pregunta a pregunta

### 1. Ratio de asequibilidad de la vivienda en España, 2024
- **Verdad (modelo):** 1,26 · **IA sola:** 1,32 ✅ · **IA + modelo:** 1,26 ✅
- Ambos aciertan. Es un dato razonablemente conocido (los precios han subido más
  que los salarios desde 2015), así que la IA lo estima bien de memoria. Cuando
  la respuesta es "de cultura general", la IA sola basta — pero son la minoría.

### 2. Ratio de asequibilidad proyectado a finales de 2027
- **Verdad:** 1,64 · **IA sola:** 40,7 ❌ · **IA + modelo:** 1,64 ✅
- El fallo más aparatoso de la IA sola: da 40,7, un disparate de escala (confunde
  un índice con un porcentaje). El modelo, que arrastra la definición correcta y
  el pronóstico, da 1,64. Muestra que en cuanto la pregunta exige el resultado
  concreto de un cálculo, la IA sola descarrila.

### 3. Precisión del modelo campeón en la validación (MASE, horizonte ≤4)
- **Verdad:** 0,395 · **IA sola:** 0,87 ❌ · **IA + modelo:** sin respuesta ❌
- El único punto donde el modelo completo NO acierta: la IA, aun con el documento
  delante, no supo elegir entre dos cifras muy próximas (0,40 titular y 0,395 a
  horizonte corto) y prefirió no responder. Lo reportamos abierto: 11 de 12, no
  12. La IA sola, por su parte, se inventa un 0,87.

### 4. Deuda pública proyectada para 2050 (escenario central)
- **Verdad:** 224 % · **IA sola:** 135 % ❌ · **IA + modelo:** 224 % ✅
- Clave. La IA sola proyecta 135 % — no "ve" la presión del envejecimiento, que
  el motor del proyecto cuantifica en +97 puntos. Es justo el conocimiento que
  aportan los datos demográficos y las elasticidades entrenadas.

### 5. Deuda 2050 SIN presión demográfica (contrafactual)
- **Verdad:** 127 % · **IA sola:** 6,5 % ❌ · **IA + modelo:** 127 % ✅
- La IA sola da 6,5 %, absurdo. No puede reproducir un contrafactual que solo
  existe dentro del simulador del proyecto.

### 6. Deuda mediana en 2070 (simulación Monte Carlo)
- **Verdad:** 409 % · **IA sola:** 181 % ❌ · **IA + modelo:** 409 % ✅
- Una proyección a 46 años con incertidumbre propagada: imposible de memoria.
  La IA sola se queda a menos de la mitad.

### 7. Esfuerzo hipotecario nacional en 2024 (% del salario bruto)
- **Verdad:** 41,6 % · **IA sola:** 37,0 % ❌ · **IA + modelo:** 41,6 % ✅
- La IA sola se acerca pero falla: no tiene el €/m² concreto ni los supuestos de
  la hipoteca tipo que usa el proyecto.

### 8. Gasto público de España en 1900 (% del PIB)
- **Verdad:** 11,0 % · **IA sola:** 8,7 % ❌ · **IA + modelo:** 11,0 % ✅
- Dato histórico fino que exige la serie empalmada del proyecto; la IA sola lo
  subestima.

### 9. Rendimiento sanitario de España sobre lo esperado (años de vida)
- **Verdad:** 2,72 · **IA sola:** 3,2 ✅ · **IA + modelo:** 2,7 ✅
- Ambos dentro de la tolerancia amplia de esta pregunta (±25 %), pero el modelo
  clava el valor de la frontera; la IA sola acierta por aproximación.

### 10. Efecto en la mortalidad infantil a 2050 (crecimiento de renta 1 %)
- **Verdad:** −12,3 % · **IA sola:** −8,2 % ❌ · **IA + modelo:** −12,3 % ✅
- La IA sola intuye el signo (menos pobreza → menos mortalidad) pero falla la
  magnitud, que sale del panel estadístico del proyecto.

### 11. Elasticidad del gasto en pensiones al envejecimiento
- **Verdad:** 0,912 · **IA sola:** 1,0 ✅ · **IA + modelo:** 0,91 ✅
- La IA sola da un "1,0" de libro; el modelo aporta el valor estimado real con su
  incertidumbre (0,91 ± 0,19). Ambos dentro de tolerancia, pero solo el modelo
  puede defender de dónde sale.

### 12. Relación entre suelo urbanizado y precios de la vivienda (correlación)
- **Verdad:** 0,01 · **IA sola:** 0,35 ❌ · **IA + modelo:** 0,01 ✅
- El fallo más instructivo: la IA sola **inventa** una relación moderada (0,35)
  porque "suena lógico" que urbanizar más abarate. El dato real del proyecto,
  sobre 40 países, es 0,01 — no hay relación. La IA reproduce el prejuicio; el
  modelo, la evidencia.

---

## Conclusión

- **En 8 de 12 preguntas la IA sola falla y el modelo acierta.** En 3 aciertan
  ambos (preguntas de "cultura general"). En 1 falla el modelo por prudencia
  (no eligió entre dos cifras casi iguales).
- **Los errores de la IA sola no son ruido: son sesgo plausible.** Ignora el
  envejecimiento, inventa correlaciones que "suenan bien", confunde escalas.
  Son exactamente los errores que la capa de datos + validación existe para
  evitar.
- **Confirma el diseño del proyecto**: el sistema calcula, el asistente narra.
  La prueba está automatizada (`tests/test_ablacion.py`): si algún día la IA
  sola empezara a igualar al modelo, el test fallaría y avisaría de que la capa
  de matemáticas ha dejado de aportar.
