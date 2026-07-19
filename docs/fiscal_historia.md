# Series históricas de gasto e ingresos: denominador verificado y empalme 1703–2025

Tres preguntas, tres respuestas medidas (`analysis/fiscal_historia.py`).

## 1. ¿Tenemos el PIB para calcular los porcentajes? Sí, y se comprueba

JST Macrohistory (18 países, 1870–2020) publica NIVELES: PIB nominal, ingresos
y gasto en moneda corriente. Se recalculó cada ratio desde los niveles y se
comparó con el publicado: **diferencia máxima 0,000000 pp en 2.516 país-años**.
El denominador existe, es explícito y los porcentajes son reproducibles desde
cifras primarias — no dependemos de ratios opacos.

## 2. ¿Cuadran las series históricas con las modernas (1995–2025)? Depende de la fuente — y la diferencia es el hallazgo

Brechas medias en la ventana de solape 1995–2020 (11 países UE, 286 país-años),
contra Eurostat como canónico:

| Fuente | Gasto | Ingresos | Diagnóstico |
|---|---|---|---|
| GMD (Global Macro Database) | **0,04 pp** | 1,63 pp | continuo en perímetro AAPP |
| WEO histórico | 0,50 pp | 0,49 pp | pero con SALTO de perímetro en 1995 (ES: 12,8→44,5) |
| JST Macrohistory | 21,4 pp | 21,6 pp | es SOLO administración central — no comparable sin decirlo |

La brecha de 21 pp de JST no es un error: es la diferencia entre Estado central
y AAPP totales (CCAA+local+Seguridad Social). Es la trampa clásica de las
series fiscales largas, y queda medida y declarada. Regla fijada: el empalme
canónico usa **Eurostat (1995+) + GMD (antes)** — GMD demuestra continuidad de
perímetro a través de 1995 (ES: 46,4 en 1994 → 44,1 en 1995). WEO se queda
para lo que ya hacía (totales largos comparativos y proyecciones D1); JST,
como capa declarada de "Estado central" y como fuente de niveles.

Caveat honesto: antes de ~1960 el "perímetro AAPP" es en la práctica el Estado
más lo poco que existía de administración territorial; el perímetro crece con
el propio Estado del bienestar y eso forma parte de la historia contada, no de
un error de medición.

## 3. ¿Qué se puede decir? España 1703–2025 (gold_fiscal_historico.csv, figura b19)

| Año | Gasto | Ingresos | Momento |
|---|---|---|---|
| 1850 | 9,1 | 9,2 | Estado liberal mínimo |
| 1900 | 11,0 | 11,5 | el "Estado del 10 %" (referencia del stress test) |
| 1935 | 17,3 | 15,1 | II República |
| 1960 | 17,8 | 15,1 | autarquía tardía |
| 1977 | 29,1 | 27,3 | arranque de la transición fiscal |
| 1995 | 44,1 | 37,3 | Estado del bienestar construido en ~18 años |
| 2007 | 39,2 | 41,1 | superávit del boom |
| 2012 | 49,2 | 37,7 | la tijera de la crisis: 11,5 pp de déficit |
| 2023 | 45,4 | 42,1 | meseta actual |

Lecturas para la defensa: (a) la transformación 1977–1995 (+15 pp en 18 años)
es EL evento fiscal español del siglo, y coincide con el arco del atlas B;
(b) el déficit no es un estado permanente histórico: 1850–1935 ingresos y
gasto van pegados (patrón oro, sin deuda social), la brecha crónica nace con
el Estado del bienestar y se abre en crisis (1993, 2009-13, 2020); (c) el
"Estado del 10 %" del stress test tiene fecha real en España: 1900. Panel
completo de 18 países en el mismo gold (Irlanda desde 1926: no existía antes).
