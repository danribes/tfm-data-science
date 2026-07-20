# ¿Se puede predecir la pobreza y la pobreza infantil?

Respuesta corta: **depende del tipo de pobreza, y solo como escenario
condicional — nunca como pronóstico automático.** El experimento
(`analysis/pobreza_infantil.py` → `gold/gold_pobreza_infantil.csv`) lo separa
con datos.

## Dos pobrezas distintas, dos respuestas

| Tipo | Qué es | ¿Predecible? | Vía |
|---|---|---|---|
| **Absoluta** (mundo en desarrollo, 3 $/día) | vivir por debajo de un umbral fijo | **Sí**, vía crecimiento de la renta | La frontera ya mostró que la renta domina; los sobres a 50 años la proyectan condicionada al crecimiento |
| **Relativa** (UE, AROPE, incl. infantil) | por debajo del 60 % de la mediana | **No desde el ciclo**; **sí desde la redistribución** | Palanca de transferencias (medida abajo) |

## Lo que NO predice la pobreza relativa: el ciclo económico

Panel de la UE (35 países, 2006–2025, 509 observaciones), efectos fijos de país
y año, errores agrupados: **el paro NO anticipa la pobreza relativa** dentro de
cada país (β ≈ +0,02 por punto de paro, no significativo, ni contemporáneo ni
con un año de retardo). No es un fallo del modelo: es la naturaleza de una
medida RELATIVA — en una recesión bajan a la vez los ingresos de los pobres y la
mediana, así que el umbral se mueve con ellos y la tasa apenas cambia. Un dato
que un LLM a pelo no daría: intuitivamente "más paro → más pobreza", y los datos
dicen que para la pobreza *relativa* no, dentro de cada país.

## Lo que SÍ la predice: la redistribución (palanca medida)

Comparando el AROPE antes y después de transferencias (sin pensiones):
- **España**: las transferencias quitan **5,9 pp** de pobreza total hoy.
- **Media UE**: **8,0 pp**.
- La pobreza infantil se mueve con la total (correlación 0,74 en niveles) y es
  de media **×1,47** — así que las transferencias quitan **~9 pp de pobreza
  infantil** en España.

Esa es la variable con poder predictivo: no el ciclo, sino cuánto redistribuye
el Estado.

## Sobre condicional de pobreza infantil (España, base 33,8 %)

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

## Encaje con el resto del proyecto

- Misma arquitectura que la deuda y el bienestar a 50 años: predicción =
  escenario condicional encadenado por una palanca (`docs/arquitecturas_prediccion.md`).
- Refuerza el mensaje central para el tribunal: el sistema no "adivina" la
  pobreza; identifica QUÉ la mueve (la redistribución, no el ciclo — un
  resultado medido, contraintuitivo) y cuantifica cada opción.

## Límites declarados

- In-sample UE; un uso predictivo real pasaría por validación con datos futuros.
- AROPE infantil solo desde 2015 (serie corta); el efecto ×1,47 se estima sobre
  el solape con la total.
- La pobreza absoluta mundial es predecible vía renta, pero con el mismo caveat
  de las fronteras: la renta domina y la capacidad fiscal es de segundo orden a
  estos horizontes (`docs/bienestar_indicadores.md`, `docs/horizonte_50.md`).
