# Guía de defensa: España en escenarios

Leer junto con la [memoria](MEMORIA_TFM.md), la [matriz de evidencia](RESULTS.md)
y el [procedimiento de reproducción](REPRODUCIBILITY.md). La defensa se centra
en preguntas, experimentos y límites, con una demostración breve del sistema.

## Mensaje central

«He construido un sistema que permite inspeccionar supuestos macrofiscales y
contrastar partes de su comportamiento con datos. La aportación combina
implementación reproducible, evaluación con baselines y comunicación de lo
que la evidencia permite afirmar. Algunos experimentos no mejoran el baseline
y se conservan como resultados.»

## Preguntas de investigación y aportaciones

1. ¿Puede implementarse un escenario macrofiscal trazable y coherente en servidor
   y navegador? Se responde con identidades, pruebas y anclas comunes.
2. ¿Qué apoyan los datos sobre la dinámica de vivienda y qué añade un modelo
   neuronal transferido? Se responde con estimación, sensibilidad y backtesting.
3. ¿Qué calidad y límites muestran las explicaciones basadas en recuperación?
   La evidencia existente es de desarrollo; la evaluación independiente queda
   como trabajo pendiente con protocolo ejecutable.

No afirmar que el modelo mide la eficiencia del gasto público, identifica todos
los efectos causales de las palancas o pronostica España hasta 2050/2070.

## Por qué un motor económico y qué significa una palanca

La identidad de deuda utiliza el coste efectivo y el crecimiento nominal:

`b_t = b_(t-1) * (1 + i_t/100) / (1 + g_nom,t/100) - pb_t`.

El saldo primario se expresa en puntos de PIB. La inflación y el crecimiento
real se transforman en desviaciones respecto a un escenario nominal de
referencia. Las elasticidades de comportamiento son principalmente
calibraciones explícitas. Una palanca responde «qué implica este modelo si…»;
no identifica una intervención causal sobre la economía real.

Un tipo inferior al crecimiento ayuda a diluir la deuda heredada. Un déficit
primario puede superar esa ayuda; `r < g` no garantiza una ratio decreciente.

Los intereses y el saldo total deben usar el PIB corriente: los intereses son
`b_(t-1) * (i_t/100) / (1 + g_nom,t/100)`. La caída de la ratio por crecimiento
del denominador no equivale a amortizar deuda nominal. Los diagramas muestran
identidades del escenario; no reconstruyen flujos oficiales de impuestos.
Si una combinación extrema produce deuda negativa, la salida se marca como
fuera del dominio de deuda bruta: no existe aquí un modelo de activos públicos.

## Cómo se conecta la vivienda con la evidencia

La media histórica de crecimiento y la tasa de reversión se estiman en 19
unidades territoriales, sin tratar el total nacional como otra región. Una
reversión de 0,2039 implica persistencia 0,7961. Ambos motores aplican esa
persistencia. El .60 de v16 era persistencia, equivalente a reversión .40.

La comparación LP representa diferencias acumuladas de log-precio y no una
curva decreciente de crecimiento dibujada sobre precios. Normaliza el primer
año para comparar forma, excluye crecimiento ya realizado y no presupone un
choque exógeno identificado.

La media 1,215% tiene banda regional estrecha, pero el bootstrap por bloques
temporales comunes amplía la incertidumbre e incluye 3%. No sostener que la
calibración antigua queda rechazada de manera robusta. Mostrar ambos métodos
y explicar dependencia temporal, choques nacionales y sensibilidad al periodo.

## El resultado negativo de deep learning

La red se entrena con series extranjeras y objetivos hasta 2019Q3; se compara
con naive, seasonal naive y drift usando orígenes móviles y escalas MASE
calculadas con los datos de entrenamiento de cada origen. El resultado
conservado es 5/17 victorias regionales y MASE 0,400 frente a 0,395 de drift.

La conclusión es que esta configuración no supera el baseline principal en ese
protocolo. No prueba que ninguna red pueda mejorar la predicción. El holdout
final y la sensibilidad a semillas requieren resultados adicionales; no
presentarlos como completados.

## Qué dicen Monte Carlo, distress y los análogos

- Monte Carlo produce percentiles bajo choques AR(1) calibrados. La semilla
  asegura repetibilidad; la banda no tiene cobertura predictiva demostrada.
  Mostrar el nuevo análisis de sensibilidad a persistencia y escala.
- El clasificador de distress discrimina modestamente entre observaciones de
  su muestra. El score 0–1 no es una probabilidad calibrada para España.
  GroupKFold por país no equivale a entrenar en el pasado y evaluar el futuro.
- Los análogos usan cinco variables macroeconómicas comparables, completas y
  estandarizadas, en el año elegido. El tipo bancario de préstamo no se trata
  como bono soberano; no se emite un veredicto de sostenibilidad con esos datos.
- Los estados HMM son descripciones retrospectivas; SHAP explica la superficie
  de un predictor, no efectos causales. Un resultado nulo no valida una
  constante del motor.

## Qué se ha demostrado sobre RAG

El 34/35 es recuperación del documento esperado en top-8 sobre preguntas usadas
en desarrollo. No es exactitud de respuesta. Las 10/12 verificaciones cubren
una afirmación muestreada por respuesta y usan otro LLM como juez.

La versión revisada comprueba referencias formales y magnitudes numéricas del
narrador; esto no verifica signos, unidades, correspondencia entre cifra y
concepto o respaldo semántico completo. Los fallos conducen a alternativas
deterministas. La revisión humana independiente y las ablaciones sobre un test
congelado están especificadas, pero todavía pendientes.

Los documentos e índice del corpus académico se almacenan localmente. Los
pasajes seleccionados se envían al proveedor configurado cuando se solicita
generación remota. El paquete público preparado para el Space ofrece otra
biblioteca: seis documentos propios de método, resultados y defensa, con
búsqueda léxica sin embeddings. Sus colecciones y su autoridad se identifican
en la interfaz. Las métricas históricas del corpus académico no evalúan esta
biblioteca pública; una búsqueda en ella demuestra acceso a la documentación
del proyecto. Sin una clave de generación se conservan los pasajes recuperados.

## Demostración de cinco minutos

1. Mostrar la fecha de referencia y distinguir supuesto, dato y resultado.
2. Aplicar S1 y seguir la refinanciación, crecimiento y deuda. Repetir un mismo
   escenario para demostrar paridad, sin confundirla con precisión económica.
3. Abrir Evidencia: persistencia/reversión y bandas regionales/temporales.
4. Mostrar el resultado negativo frente a drift y el score de distress con su
   alcance real. Buscar un análogo en el año seleccionado.
5. Enseñar qué verifica el test RAG y qué evaluación queda pendiente.

Abrir la aplicación antes de la defensa para comprobar el despliegue. Conservar
una alternativa local/simulada claramente identificada. Utilizar únicamente
los artefactos regenerados con motor 1.1.0 y evitar capturas antiguas como
prueba del comportamiento actual.
