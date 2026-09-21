# Cómo se actualizan los datos del modelo

El modelo no se actualiza solo, y eso es una decisión, no una carencia. Todo lo
que publica este trabajo —las cifras de la memoria, las anclas de las pruebas,
los artefactos de evaluación— está calculado sobre un corte de datos congelado,
el *vintage*, que hoy es **2026-07-31**. Si esos datos cambiaran por debajo sin
que nadie lo advirtiera, cada número publicado dejaría de ser reproducible y
nadie se enteraría.

De ahí la regla que gobierna todo lo que sigue: **`data/gold/` es inmutable**.
Se descarga a otro sitio, se compara, y promover el resultado es un acto humano
y revisado.

Este documento es el procedimiento completo. Siete pasos; los seis primeros se
pueden deshacer.

---

## 0. Antes de empezar

```bash
.venv/bin/python -m pip install -r requirements-regenerate.txt
```

Las dependencias de adquisición están aparte a propósito: la comprobación
offline del repositorio no las necesita, y quien sólo quiera verificar lo
publicado no debería tener que instalar nada que hable con la red.

---

## 1. Descargar un vintage nuevo

```bash
python scripts/refresh_vintage.py
# vintage written to data/vintages/2026-09-22
```

Trae las URL HTTP(S) registradas en `data/gold/manifest.csv` a
`data/vintages/<fecha>/raw/`, que está fuera del control de versiones. **No
toca `data/gold/`.** Cada fuente recibe un `status` en el manifiesto nuevo: si
una URL ha muerto, aparece como `error: …` y no como un fichero viejo que se
queda ahí sin avisar.

Los artefactos derivados se omiten con su motivo. No son descargables: se
reconstruyen en el paso 4.

## 2. Comparar contra el vintage anterior

```bash
python scripts/diff_vintage.py data/vintages/2026-09-22 data/vintages/2026-10-04
```

Dice qué se ha movido en el origen: fuentes cambiadas, altas, bajas y fallos de
red. Devuelve 1 si hay algo que revisar, de modo que encadena en un script.

Aquí hay una limitación heredada que conviene conocer antes de que la encuentre
otro. El vintage congelado **no guarda el sha256 de sus descargas originales**
—16 de las 18 filas de `data/gold/manifest.csv` lo tienen vacío— y los ficheros
crudos de entonces no se conservaron. Contra ese vintage no existe comparación
posible, y la herramienta no la finge: exige dos directorios de
`data/vintages/` y declara «no comparable» cualquier fuente sin huella en
alguno de los dos lados. La comparación es posible desde el primer refresco en
adelante.

Por la misma razón, `observation_cutoff` está poblado en sólo 2 de las 18
filas: el manifiesto congelado no registra qué periodo cubría cada fuente. Al
promover, ese campo se rellena a mano (paso 3).

## 3. Decidir, y dejar escrito por qué

No hay comando. Es el paso que da sentido a los demás.

Para cada fuente que el paso 2 marque como cambiada, hay que responder a tres
preguntas y anotar la respuesta en el manifiesto del vintage nuevo:

1. **¿Es una revisión o es un dato nuevo?** Un organismo que revisa el PIB de
   2024 no es lo mismo que uno que publica el de 2026. Lo primero cambia el
   pasado del modelo; lo segundo lo alarga.
2. **¿Hasta dónde llega ahora la serie?** Ése es el `observation_cutoff`, y
   determina qué se puede afirmar. Sin él, una serie que se corta en 2025 se
   lee como si llegara a hoy.
3. **¿Cambia el alcance de alguna afirmación publicada?** Si una serie usada
   para estimar `IPV_LR` se revisa, el intervalo de la memoria se mueve.

Una fuente desaparecida no se sustituye por otra parecida sin dejarlo escrito.
Es exactamente así como un trabajo acaba diciendo que usa una fuente que ya no
usa.

## 4. Promover el vintage

Copiar los ficheros procesados a `data/gold/`, actualizar `data/gold/VINTAGE`
con la fecha nueva y rellenar en `data/gold/manifest.csv` las columnas
`sha256`, `observation_cutoff` y `acquired_at` de cada fuente traída.

Rellenar el `sha256` **es el paso que cierra el agujero descrito en el paso 2**:
a partir del primer vintage promovido con huellas, cualquier actualización
posterior es comparable.

## 5. Recalcular lo que depende de los datos

En este orden, porque cada uno consume lo anterior:

```bash
PYTHONPATH=. python tools/gen_estimated_params.py      # IPV_LR, IPV_REV y sus bandas
PYTHONPATH=. python research/validate.py               # calibrado frente a estimado
PYTHONPATH=. python research/uncertainty.py            # sensibilidad Monte Carlo
PYTHONPATH=. python research/pension_sensitivity.py    # curva deuda / indexación
PYTHONPATH=. python tools/evaluate_analogs.py          # métrica de análogos
PYTHONPATH=. python scripts/generate_anchor_fixture.py # contrato de los dos motores
PYTHONPATH=. python docs/deck/build_deck.py            # figuras de la memoria
PYTHONPATH=. python tools/build_frontmatter.py         # portada e índice
```

El primero es el que importa: si el panel cambia, cambian los dos únicos
parámetros del motor que vienen de datos, y con ellos la cadena de vivienda
entera y su banda de incertidumbre.

## 6. Comprobar qué se ha movido, y que sólo eso

```bash
python -m pytest -q                       # el motor y todo lo que depende de él
python scripts/check_data_integrity.py    # los 41 artefactos congelados
cd frontend && npx vitest run             # la interfaz y la paridad de motores
```

**Aquí es donde se gana o se pierde la confianza.** Las pruebas no están para
dar el visto bueno, sino para decir qué ha cambiado:

- Si fallan anclas de `tests/fixtures/engine_anchors.json`, el motor produce
  cifras distintas. Es lo esperado tras un cambio de datos —pero el diff del
  fichero tiene que explicarse serie por serie, no regenerarse a ciegas.
- Si `check_data_integrity.py` protesta, un artefacto cambió sin que se
  registrara. Se revisa el diff **antes** de `--update`; que toque exactamente
  los ficheros esperados y ninguno más es la señal de que nada se coló.
- Si falla la paridad Python/TypeScript, uno de los dos motores se quedó atrás.

## 7. Volver a escribir lo que ya no es cierto

Un vintage nuevo deja frases obsoletas repartidas por la memoria: tamaños
muestrales, intervalos, el propio corte de datos. Hay pruebas que recalculan
algunas tablas de la memoria contra el motor y fallarán solas; el resto es
lectura.

Como mínimo: `docs/RESULTS.md`, las secciones de resultados de
`docs/MEMORIA_TFM.md` y la fecha de corte que aparece en la portada, en el pie
de la aplicación y en `/health`.

---

## Lo que este procedimiento no hace

Vale la pena decirlo tan claro como lo demás:

- **No reconstruye los gold desde cero.** El paso 1 trae los datos crudos; las
  transformaciones que los convirtieron en las tablas gold vienen del proyecto
  anterior y no están todas incorporadas. Está anotado como pendiente en
  `REPRODUCIBILITY.md`.
- **No recupera revisiones históricas.** Si un organismo sustituyó una serie,
  la versión anterior se perdió salvo que estuviera descargada.
- **No fija por sí solo un corte de observaciones.** Eso es el paso 3, y es
  humano.
- **No actualiza el corpus documental del RAG.** Es otro pipeline, descrito en
  el README.

Ninguna de estas ausencias es un descuido de la automatización: son los puntos
donde automatizar significaría afirmar algo que nadie ha comprobado.
