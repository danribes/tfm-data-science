# Guion de presentación — 10 minutos

Para decir en voz alta, con la aplicación proyectada. Los tiempos son
acumulados. Los números están calculados con el motor 1.1.0 sobre el vintage
`2026-07-31`; **si la pantalla dice otra cosa, la pantalla tiene razón y este
guion está desactualizado**.

Antes de entrar: despertar el Space diez minutos antes abriendo
<https://danribes-evo-espana-api.hf.space/health> hasta leer `"status":"ok"`.
Arranca en frío en 30–90 segundos y no conviene que eso pase en el minuto 0.

---

## 0:00 – 1:30 · Qué es, y qué no es

> Pantalla: portada de la aplicación.

«España en escenarios es una herramienta para responder a una pregunta
concreta: **qué implica un supuesto**. No qué va a pasar.

La diferencia no es retórica. Un pronóstico afirma algo sobre el futuro y se
puede acertar o fallar. Esto es otra cosa: fijas un supuesto —los tipos suben
dos puntos, las pensiones se revalorizan un punto por encima del IPC— y la
herramienta calcula, con aritmética explícita, qué se sigue de ese supuesto
para la deuda, la vivienda y el bolsillo de doce perfiles distintos.

El trabajo tiene cuatro capas, y la portada dice de cada una qué queda
acreditado. Fijaos en el último bloque, porque es el que más me importa:
**capacidad predictiva, medida y no alcanzada. Identificación causal, no
reclamada.** Están en ámbar, no en rojo, porque no son fallos: son hallazgos, y
los publico.»

---

## 1:30 – 3:00 · Cómo funciona

> Pantalla: bajar a «El futuro, en números» y a «Cómo se ha calculado cada
> cifra».

«Por dentro hay un motor determinista: la identidad contable de la deuda y un
puñado de reglas calibradas —Phillips, Okun, una regla fiscal—. Está escrito
dos veces, en Python y en TypeScript, y hay una prueba que exige que las dos
implementaciones coincidan cifra a cifra en 40 series y 25 años. No es
redundancia: el navegador calcula en local para que la herramienta responda al
instante, y esa prueba es lo que impide que las dos versiones se separen.

De todos los parámetros del motor, **sólo dos están estimados a partir de
datos**, y los dos afectan a la vivienda. El resto son calibraciones tomadas de
la literatura. Cada fila de esta tabla lo dice: «motor» o «motor + panel».

Y estas dos filas —paro e IPCA— llevan la etiqueta **«sin senda propia»**: el
modelo no les da trayectoria, sólo las desplaza en bloque. Lo marco porque ver
una recta plana sin explicación es lo que hace pensar que la herramienta está
rota.»

---

## 3:00 – 6:00 · Ejemplo 1: la indexación de las pensiones

> Pantalla: panel de palancas → «Indexación pensiones/nóminas» a **+1,0**.
> Horizonte 2050.

«Primer ejemplo. Subo la indexación un punto por encima de la inflación y lo
dejo ahí los veinticinco años.

| | base | +1 punto |
|---|---|---|
| Pensiones 2050 | 22,3 %PIB | **28,2 %PIB** |
| Deuda 2050 | 223,8 %PIB | **286,6 %PIB** |

Sesenta y tres puntos de PIB de deuda. **Es la palanca más potente del modelo**:
la productividad, recorriendo todo su rango, mueve diecisiete.

Y aquí viene lo que quiero contar, porque es un error que encontré y corregí.
Hasta hace unos días esta palanca **no movía la deuda en absoluto**. El bloque
de pensiones se calculaba al final del bucle, cuando la deuda del año ya estaba
guardada, así que el gasto se mostraba en pantalla y la identidad contable no
se enteraba. Bajar la indexación punto y medio quitaba 6,6 puntos de PIB de
gasto al año durante veinticinco años y la deuda de 2050 salía idéntica hasta
el tercer decimal.

El arreglo tiene un detalle que sostiene todo lo demás: el gasto entra en el
saldo **por su desviación** respecto a la indexación de referencia, no por su
nivel. El escenario central ya incorpora una senda de pensiones, y restar el
nivel entero contaría dos veces la misma partida. Con la palanca en su
referencia el ajuste es exactamente cero, así que la línea base y los ocho
escenarios preconfigurados salen bit a bit iguales que antes. Lo comprobé
contra el motor anterior sacado del repositorio: diferencia máxima cero en las
cuarenta series.

La memoria publica la curva entera, no dos puntos, porque la relación no es
lineal: la pendiente sube de 48 a 65 puntos de deuda por punto de indexación
según de dónde partas.

**Lo que este número no es:** una predicción de la deuda española. Es
aritmética bajo un supuesto contable explícito —un punto de PIB de gasto es un
punto menos de saldo primario— sin respuesta de política y sin efectos de
segunda ronda sobre actividad o recaudación.»

---

## 6:00 – 8:30 · Ejemplo 2: el Euríbor y la hipoteca

> Pantalla: reiniciar palancas. «Tipo de interés · Euríbor 12m» a **4,8**.
> Horizonte 2035. Bajar a la vivienda.

«Segundo ejemplo, y elijo éste porque tiene dos canales que tiran en direcciones
opuestas.

Subo el Euríbor dos puntos. El tipo hipotecario sube con él, así que la cuota
se encarece. Pero un tipo más alto también enfría el precio de la vivienda, y
un piso más barato significa menos principal. ¿Qué gana?

| | base | Euríbor +2 |
|---|---|---|
| Precio medio 2035 | 279.157 € | 266.290 € |
| Cuota mensual | 1.213 € | **1.409 €** |
| Esfuerzo hipotecario | 49,1 % | **59,0 %** |

Gana el encarecimiento del crédito. El precio baja, pero no lo suficiente para
compensar.

Esto también estaba mal hasta hace dos días, y de una forma instructiva: el
choque de tipos restaba 2,6 puntos al **crecimiento** anual del precio todos
los años y sin decaer. El precio se hundía un 37 % y la cuota bajaba con él, de
modo que **subir el Euríbor abarataba la hipoteca**. La asimetría estaba a la
vista en el mismo fichero: el choque de precios de importación sí decaía desde
siempre. Ahora decae con el mismo factor.

> Pantalla: «El margen del precio de la vivienda».

Y aquí está la única serie del panel con banda de incertidumbre, que es donde
quiero terminar el ejemplo. Los dos parámetros estimados traen error típico, y
esta banda mide **cuánto se mueve la proyección si no los doy por exactos**: se
sortean cuatro mil veces de su distribución. En 2050 la banda abarca un 17 %
del nivel.

**No es un intervalo de predicción**, y lo dice al lado: no incluye el error
del propio modelo, ni cambios estructurales, ni la incertidumbre de las
palancas, que las fija quien usa la herramienta. Un precio fuera de la cinta no
contradice al modelo. Es lo único que puedo afirmar con una banda, así que es
lo único que pongo.»

---

## 8:30 – 10:00 · Qué lo respalda, y el resultado negativo

> Pantalla: Consulta. Pregunta preparada: **«¿qué es el saldo primario?»**

«Termino con dos cosas.

La primera: cada afirmación de economía que hace la aplicación se apoya en un
corpus de 58 obras académicas, y las citas llevan documento y página
comprobables. Aquí responde con el Documento Ocasional 1803 del Banco de España
y con el análisis de sostenibilidad del BCE. La mitad densa de esa búsqueda es
un transformador de 24 capas que codifica cada pregunta; apagarlo cambia los
resultados, sólo tres de ocho pasajes coinciden con la búsqueda por palabras.

La segunda, y es con la que quiero cerrar. Entrené una red neuronal sobre 1.760
series de vivienda extranjeras para proyectar el precio español. **Perdió.**
MASE 0,4000 frente a 0,3953 de una extrapolación de tendencia, ganando en 5 de
17 comunidades cuando la regla exigía 12.

Esa regla la fijé **antes** de ver el resultado. Y el resultado negativo sigue
publicado, en la aplicación y en la memoria, en vez de retirar el componente y
no contarlo.

Creo que eso vale más que un modelo que funcione: la herramienta acredita lo
que puede acreditar, y dice en pantalla lo que no.»

---

## Si algo falla

| Síntoma | Qué decir y qué hacer |
|---|---|
| «Despertando el servidor…» | «El backend es gratuito y se duerme.» Seguir hablando de la portada: el motor corre en el navegador y los escenarios funcionan sin API. |
| Consulta no responde | El corpus depende del Space. Pasar a Biblioteca, que muestra los pasajes sin redactar, o enseñar el hit@8 en Evidencia. |
| Una cifra no coincide con este guion | Decirlo: «el guion es de hace unos días y el motor ha cambiado». La pantalla manda. Es coherente con el resto de la presentación. |
| Se acaba el tiempo | Cortar el ejemplo 2 en la tabla, sin la banda. El minuto final es el que no hay que perder. |

## Preguntas que probablemente caigan

- **«¿Cómo actualizas los datos?»** → `docs/ACTUALIZAR_DATOS.md`. Siete pasos;
  el tercero no tiene comando porque es una decisión. El corte congelado es
  inmutable a propósito.
- **«¿Usas aprendizaje profundo?»** → Dos redes. Una en producción, el
  codificador de la búsqueda. Otra rechazada, la de vivienda.
- **«¿Por qué sólo la vivienda tiene banda?»** → Son los dos únicos parámetros
  estimados. Los demás son calibraciones sin error típico que sortear;
  dibujarles una banda sería inventar una distribución.
- **«¿Esto predice la deuda española?»** → No, y no lo pretende. Proyección
  condicional: dice qué se sigue de unos supuestos que fija quien pregunta.
