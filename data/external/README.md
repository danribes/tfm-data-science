# `data/external/` — series ajenas al vintage español

Esta carpeta es deliberadamente **distinta de `data/gold/`**. `gold` es el corte
congelado que alimenta el motor y del que salen todas las cifras que la app
enseña. Lo que hay aquí no entra nunca en el motor: son datos extranjeros que
sirven para **entrenar** y para **poner a prueba** modelos que después se juzgan
sobre España.

Mantenerlos separados no es orden por gusto. Si el corpus de entrenamiento
viviera en `gold`, la pregunta «¿el modelo ha visto los datos españoles antes de
predecirlos?» dejaría de tener una respuesta comprobable de un vistazo.

## `hpi_regional_global.csv.gz`

Índices de precio de vivienda regionales fuera de España, trimestrales.

| | |
|---|---|
| Series | 1.760 |
| Observaciones | 208.640 |
| Periodo | 1968–2026 |
| Fuentes | FHFA metro (410), FHFA estado (51), Zillow (894), Reino Unido (405) |
| SHA-256 del CSV sin comprimir | `ed033bb7b1944b70…` |
| Origen | `evo_final_work_old/storage/processed/` (pipeline de la entrega anterior) |

**Ninguna serie es española.** Esa es la propiedad que hace útil el corpus: un
modelo entrenado aquí y evaluado sobre las CCAA no puede estar recordando la
respuesta, sólo puede estar transfiriendo la forma de un ciclo inmobiliario.
Estados Unidos y Reino Unido aportan varias décadas de auges y pinchazos
completos, que es exactamente lo que a España le falta en la muestra.

Se guarda comprimido (1,8 MB frente a 8,2 MB) porque el repositorio es público y
el fichero es siete veces el resto de la capa de datos. `pandas.read_csv` lo lee
tal cual, sin descomprimir a mano.

### Columnas

| Columna | Qué es |
|---|---|
| `fuente` | `fhfa_metro`, `fhfa_state`, `zillow`, `uk` |
| `serie` | identificador de la geografía |
| `anyo`, `quarter` | trimestre de la observación |
| `valor` | índice de precio, base propia de cada serie |

El nivel del índice no es comparable entre series y no hace falta que lo sea: el
protocolo trabaja siempre con diferencias logarítmicas.
