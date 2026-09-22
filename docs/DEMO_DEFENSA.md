# Guion de demostración — defensa del 28 de septiembre de 2026

> Seis minutos, centrado en operar la aplicación. Para la presentación de
> diez minutos con dos ejemplos hablados, ver
> [PRESENTACION_10MIN.md](PRESENTACION_10MIN.md).

Seis minutos de aplicación en directo, con lo que debe aparecer en pantalla en
cada paso y qué hacer cuando no aparezca. Los números están calculados con el
motor 1.1.0 sobre el vintage 2026-07-31; si la pantalla dice otra cosa, la
pantalla tiene razón y este guion está desactualizado.

- Aplicación: <https://danribes.github.io/tfm-data-science>
- API: <https://danribes-evo-espana-api.hf.space>

---

## Antes de empezar (10 minutos antes, no 1)

1. **Despertar el Space.** Es gratuito y se duerme. Abrir
   <https://danribes-evo-espana-api.hf.space/health> y esperar a leer
   `{"status":"ok", ...,"engine_version":"1.1.0"}`. El primer arranque en frío
   tarda entre 30 y 90 segundos. Si se hace en el minuto 0 de la defensa, la
   primera pantalla dice «Despertando el servidor…» delante del tribunal.
2. **Abrir las cuatro pestañas** ya cargadas, en este orden: Inicio ·
   `/persona/03` · `/laboratorio` · `/consulta`.
3. **Comprobar el token de revisión** si se va a enseñar el corpus: la pestaña
   Biblioteca debe listar `libros` y `crack23`. Sin token sólo se ven `metodo`
   y `defensa_tfm`, que es lo correcto pero no es lo que se quiere enseñar.
4. **Plan B descargado.** El motor corre entero en el navegador; lo único que
   necesita red es `/consulta` y el corpus. Si cae la red, los pasos 1 a 4
   siguen funcionando — decirlo en voz alta es, de hecho, parte del argumento.

---

## El recorrido (≈6 min)

### 1 · Dato, supuesto y resultado — Inicio (45 s)

Abrir Inicio con todo en la línea base.

> «Esto no es una previsión. Es el vintage congelado del 31 de julio de 2026:
> las palancas están en su valor observado y no hay nada proyectado todavía.»

**Debe verse:** el sello del vintage y el aviso de que nada está proyectado.

**Por qué está aquí:** establece que el punto de partida es un dato, no una
opinión, antes de que se mueva nada.

### 2 · Una palanca, una cadena — `/laboratorio`, preset S1 (90 s)

Aplicar **S1 · tipos +200 pb** (Euríbor 2,80 → 4,80 %).

**Debe verse — deuda en 2050:**

| | deuda 2050 (%PIB) |
|---|---|
| S0 base | **223,8** |
| S1 tipos +200 pb | **306,9** |

Abrir la descomposición y enseñar que la subida se atribuye a la palanca
movida, con el residuo de interacción declarado aparte.

> «El motor no es lineal. Las palancas por separado no suman el efecto
> conjunto, y esa diferencia se muestra en vez de repartirse.»

### 3 · El resultado incómodo — `/persona/03` (2 min)

Éste es el centro de la demostración. Perfil «quien quiere comprar vivienda».

Pulsar la pregunta sugerida **«¿Cuánto costará una vivienda media?»**.

**Debe verse** (el horizonte salta solo a 2035; en 2026 no ha pasado nada):

| escenario | precio 2035 |
|---|---|
| base | **279.157 €** |
| con S1 (Euríbor 4,80 %) | **175.702 €** |

Y la cuota mensual en 2035: **1.213 €** en base, **929 €** con S1.

> «Subir los tipos 200 puntos básicos abarata la cuota. Parece un error y no lo
> es: el precio cae más de lo que sube el tipo, y la hipoteca se calcula sobre
> el 80 % de un precio más bajo. El modelo no está siendo amable con nadie —
> está encadenando dos efectos de signo contrario.»

Enseñar el bloque coloquial:

> «buena noticia para quien quiere comprar y mala para quien ya tiene piso»

> «El motor calcula el número. Quién sale ganando depende de quién pregunta, y
> eso el motor no lo decide: lo dice.»

**Si el tribunal interrumpe aquí, dejarle interrumpir.** Es la pregunta que se
quiere recibir.

### 4 · Lo que el sistema se niega a hacer — `/persona/03`, texto libre (60 s)

Escribir **«¿debería comprar ahora?»** (decisión personal) o **«¿qué va a pasar
con el bitcoin?»** (fuera del dominio).

**Debe verse:** una negativa que nombra lo que concretamente no puede
calcularse, no un error genérico.

**No usar «¿cuándo bajarán los bonos a 10 años?» como ejemplo de negativa:** el
resolutor la acepta y la contesta con la serie `bono`, porque el rendimiento
del bono sí es una serie del motor. Lo que no puede es decir *cuándo* — devuelve
el nivel condicional, con una nota que lo explica. Es un buen ejemplo de matiz,
no de rechazo.

> «El conjunto de respuestas es acotado a propósito. Una caja de texto libre
> sobre un motor de escenarios invita a preguntas que el motor no puede
> responder, y responderlas igualmente es cómo una herramienta empieza a
> inventar.»

### 5 · Trazabilidad hasta la fuente — `/consulta` (60 s)

Preguntar algo que el corpus sí cubre, por ejemplo **«¿qué son las expectativas
adaptativas?»**.

**Debe verse:** respuesta con pasajes citados, título y página.

> «El modelo escribe; no calcula. Las cifras vienen del motor y pasan por un
> inventario numérico antes de mostrarse; el texto sólo las envuelve.»

**Aviso honesto que conviene dar sin que lo pregunten:** el `hit@8` del informe
se midió sobre 35 preguntas que participaron en el ajuste, así que es una cota
superior de desarrollo, no una medida independiente. El despliegue sí resuelve
hoy con la fusión híbrida: cada respuesta publica el recuperador que de verdad
la resolvió.

### 6 · Cierre (30 s)

Volver a Inicio.

> «Tres capas: un motor determinista que se puede auditar, una capa empírica
> que publica también los resultados negativos, y una capa de lenguaje que
> narra sin calcular. Lo que no se ha medido, está dicho que no se ha medido.»

---

## Preguntas que esta demostración invita

**«¿No es raro que subir tipos abarate la hipoteca?»**
Es el resultado de dos efectos encadenados: el tipo sube la cuota por euro
prestado, y el precio cae, lo que reduce el principal. En este motor domina el
segundo a 2035. La reversión del precio está estimada, no calibrada a mano
(IPV_REV = 0,2039 anual, persistencia = 0,7961), y el intervalo está publicado.

**«¿Por qué la deuda siempre habla de 2050 y lo demás de 2035?»**
La deuda es una variable de stock: su interés está en el final de la
trayectoria. Las de flujo se leen en el horizonte que elija quien pregunta.
Está explícito en el modelo, no es una inconsistencia de la interfaz.

**«¿El LLM puede inventarse una cifra?»**
Puede intentarlo; por eso la narración generada se valida contra un inventario
de las magnitudes que el motor calculó, y por eso la narración por defecto está
apagada y lo que se ve son plantillas deterministas sobre los mismos hechos.

**«¿Esto predice?»**
No. Es una proyección condicional: lo que implica el modelo si esas palancas se
mantuvieran en esos valores. La aplicación lo dice en cada respuesta.

---

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| «Despertando el servidor…» | Seguir con los pasos 1–4: el motor corre en el navegador. Volver a `/consulta` al final. |
| `/consulta` da 503 | Decir que la generación remota está caída y enseñar `/biblioteca`: los pasajes se recuperan igual. |
| Biblioteca no lista `libros` | El token de revisión no está puesto. No improvisar: pasar al paso 6. |
| Un número no coincide con este guion | Leer el de la pantalla. El guion se calculó con el vintage congelado; si difiere, decirlo y seguir. |
| No hay red | Pasos 1–4 completos desde el navegador. Es el argumento de reproducibilidad, hecho en directo. |
