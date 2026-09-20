# Revisión metodológica del motor 1.1.0

Esta revisión corrige implementación e interpretación. No convierte las
simulaciones en previsiones ni atribuye independencia retrospectiva a los
experimentos existentes. Los cambios permanecen locales hasta su revisión.

## Vivienda y coherencia de los motores

`IPV_REV` es ahora inequívocamente una tasa anual de reversión. La persistencia
que multiplica la desviación de crecimiento es `1 - IPV_REV` en Python y
TypeScript. El valor `.60` del motor v16 era persistencia: para reproducirlo se
pasa `ipv_rev=.40`, junto con `ipv_lr=3.0`.

La estimación excluye `Nacional`; usa 17 comunidades y Ceuta/Melilla. Los valores
regenerados son media histórica 1,2151% y reversión 0,2039. El fixture compartido
se regenera desde los defaults actuales; una prueba separada conserva el
comportamiento legado. La comparación LP acumula cambios de log-precio y
muestra el modelo sólo en horizontes anuales, normalizado en el primer año.
No convierte la variación observada en un choque exógeno.

El bootstrap temporal sincronizado conserva la comovilidad entre regiones.
Sus bandas incluyen 3%, aunque la banda regional primaria lo excluya. Por eso
la afirmación «los datos rechazan 3%» no es robusta a la inferencia considerada.

## Análogos descriptivos

La matriz de covarianza y las distancias utilizan las mismas coordenadas
estandarizadas y la misma población: observaciones completas, ajenas a España,
hasta 2020. Se elimina el bonus arbitrario por palanca. La consulta usa el año
elegido y compara saldo total con saldo total.

El tipo de préstamo bancario de World Bank se identifica como `lending_rate`.
No se usa como bono soberano ni en un diferencial nominal–real. La tabla fuente
legada permanece intacta; el cargador adapta su antiguo nombre incorrecto.
Las estadísticas legadas tampoco se usan en el cálculo: la normalización real
queda en `docs/eval/analog-metric.json`.

No se imputan datos ausentes como observaciones medias ni ceros en gráficos.
Política, régimen cambiario y vencimiento no se deducen de proxies estáticos:
se muestran como no disponibles cuando faltan mediciones comparables. La
similitud histórica no justifica extrapolación directa o causal.

## Comprobación contable adicional

Los intereses se expresan sobre el PIB del año corriente:
`int_t = b_(t-1) × (i_t/100) / (1 + gnom_t/100)`.
La versión anterior omitía el último denominador al calcular intereses y saldo
total, aunque sí lo aplicaba en la identidad de deuda. Python y TypeScript se
corrigen conjuntamente. En la base de 2026, los intereses son 2,73967% del PIB
y el saldo total −4,08967%. La trayectoria de deuda base no cambia.

La sensibilidad opcional de prima soberana en Python también corrige unidades:
`alpha_spread=.04` significa cuatro puntos básicos por cada punto porcentual de
deuda sobre el umbral; 20 puntos producen 80 pb, no 0,8 pb. Es una sensibilidad
ilustrativa. `omega=0` elimina la persistencia de la desviación de inflación
alrededor de la referencia congelada; no impone un objetivo del BCE del 2%.

Las regresiones nuevas reconstruyen deuda nominal, intereses y saldo con un
PIB inicial independiente. La comprobación navegador/API ahora contrasta las
40 series y todos los años; comparar sólo deuda no detectaba diferencias en
vivienda o saldo. Las anclas y los vecinos históricos se han regenerado.

Las combinaciones extremas pueden agotar la deuda y continuar a valores
negativos. Se conserva el resultado calculado y se avisa que queda fuera del
dominio de deuda bruta: no se modelan activos ni una reacción de política al
alcanzar cero. No se interpreta como una predicción de activos públicos.

El diagrama presupuestario utiliza agregados del escenario y explicita el
superávit o déficit; se retiran asignaciones fiscales inventadas y la etiqueta
de flujo oficial. El puente de deuda separa saldo fiscal y efecto del crecimiento
del PIB sobre la ratio, evitando llamar amortización a una caída del cociente.

## Incertidumbre, distress y RAG

- Monte Carlo informa percentiles de simulaciones condicionales. El informe de
  sensibilidad no mide cobertura real. Su reproducción de la envolvente legada
  sigue siendo una prueba de implementación.
- Distress se muestra como score sin calibrar, con validación geográfica
  retrospectiva. Sus métricas antiguas no se recalcularon ni se reinterpretan
  como riesgo prospectivo para España. El cruce de países queda congelado.
- RAG distingue resultados de desarrollo de un futuro test independiente. La
  presencia de una referencia válida no prueba respaldo semántico. Las nuevas
  comprobaciones formales no disponen todavía de una evaluación humana real.
- Las nuevas plantillas y protocolos no son evaluaciones completadas.

## Revisión del contrato API

Cambios intencionados respecto al contrato de fase 2, autorizados como parte de
la corrección metodológica:

| Respuesta | Cambio |
|---|---|
| `/health` | `engine_version=1.1.0` |
| `/scenario` | Intereses y saldo sobre PIB corriente; `warnings` identifica trayectorias fuera del dominio de deuda bruta. |
| `/scenario/analog` | Consulta en el año solicitado; `query_year`, `features`, `limitations`; snapshots admiten `null`; `lending_rate` se etiqueta correctamente; `debt_payable_verdict=not_assessed`; `r_minus_g` e `interest_rate_10y` históricos no identificables son `null`. Narrativa determinista disponible. |
| `/scenario/montecarlo` | Metadatos `uncertainty_kind=conditional_simulation` y `empirical_coverage_validated=false`; `warnings` identifica valores negativos en bandas/trayectorias devueltas. Defaults de simulación conservados. |
| `/evidence` | IRF añade tasa de reversión y nota de comparación; valores del modelo sólo en horizontes anuales. |
| `/distress` | Conserva `probability` por compatibilidad, añade metadatos de score, población y alcance de validación. |
| RAG | Conserva `grounded` por compatibilidad: indica contexto recuperado, no corrección semántica. |

Los consumidores Python y TypeScript y sus pruebas se actualizan conjuntamente.
No se cambian resultados históricos para hacerlos parecer mejores; los nuevos
artefactos distinguen mediciones nuevas de cambios de documentación.
