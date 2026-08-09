# Fuentes de la alerta temprana de distress

## `bocboe_default_labels.csv.gz`

Etiquetas de impago soberano derivadas de la **BoC–BoE Sovereign Default
Database** (Bank of Canada / Bank of England), edición 2025, hoja `Debt_2025`
de `BoC-BoE-Database-2025.xlsx`.

| | |
|---|---|
| País-año | 10.790 |
| Países | 166 |
| Periodo | 1960–2024 |
| En impago | 5.254 (48,7 %) |
| **Inicios de impago** | **418 (3,9 %)** |

La columna `onset` es derivada, no original: marca el **primer** año de cada
episodio. Es la que se usa como etiqueta. La original (`in_default`) vale casi
la mitad de las filas porque un impago dura años, y predecir eso se parece
demasiado a leer el valor del año pasado.

España no aparece en la base: no ha impagado en el periodo cubierto. Eso la
convierte en un caso genuinamente fuera de muestra para el clasificador.

Fuente: Beers, Ndukwe y Berry (2025), *BoC–BoE Sovereign Default Database:
What's new in 2025?*, Staff Analytical Note 2025-24, Bank of Canada.
Reproducido con atribución según los términos de uso del Bank of Canada.

## `wb_macro_panel.csv.gz`

Diez indicadores macro del World Bank WDI para 257 países, 1960–2024, 14.495
país-año. Se regenera con `python -m tools.fetch_wb_panel`.

Cobertura desigual a propósito: la deuda externa (% RNB) llega al 41 % y el
servicio de la deuda al 36 %, porque son series que los países ricos no
reportan y los que impagan sí. El modelo trata los huecos como huecos —
`HistGradientBoostingClassifier` admite NaN de forma nativa — en vez de
imputarlos, que sería inventar justo la variable en la que más se apoya.

La deuda pública central (12 % de cobertura) se descarga pero no se usa: con
esa cobertura, incluirla equivaldría a entrenar sobre el subconjunto de países
que la publican.
