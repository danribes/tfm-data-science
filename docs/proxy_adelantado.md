# Proxies adelantados: variables que anticipan el precio de la vivienda

Búsqueda sistemática de un proxy — una variable observable HOY que anticipe la
evolución FUTURA de otra difícil de prever. El proyecto ya tenía uno (visados de
obra → crecimiento del precio, r=0,57 a 11 trimestres). Este barrido
(`analysis/proxy_lead_scan.py` → `gold/gold_proxy_lead_scan.csv`) encuentra dos
más, uno de ellos especialmente valioso porque ataca el punto ciego del modelo.

Método: correlación cruzada de cada candidato con ΔlogIPV_{t+k} (crecimiento
del precio k trimestres en el futuro), k=0..12, nacional. **Caveat declarado:
es correlación in-sample, no causalidad ni validación.** Un proxy prometedor
pasa después al harness de backtesting bajo la regla de siempre (batir al drift,
adopción solo con datos 2026+).

## Ranking (|correlación| con el precio futuro)

| Proxy | r | Adelanto | n | Lectura |
|---|---|---|---|---|
| **Aceleración de población** | **+0,59** | **10 trim.** | 39 | El proxy del SHOCK DE DEMANDA |
| **Hipotecas (interanual)** | **+0,65** | **1 trim.** | 76 | El proxy de crédito, robusto y corto |
| Compraventas (interanual) | +0,49 | 1 trim. | 72 | Volumen lidera precio |
| Google Trends "comprar piso" | +0,47 | 4 trim. | 73 | Interés de búsqueda |
| Euríbor (nivel) | −0,46 | 12 trim. | 65 | Tipos altos → precio futuro más flojo |
| Población interanual | −0,68 | 12 trim. | 37 | Fuerte pero FRÁGIL (ver abajo) |

## El hallazgo clave: la aceleración de la población

**Cuando el crecimiento de la población se ACELERA, el precio de la vivienda
sube ~10 trimestres (2,5 años) después.** Con datos 2007–2023:

- trimestres con aceleración positiva → ΔlogIPV a +10 trim. = **+1,7 % de media**
- trimestres con aceleración negativa → ΔlogIPV a +10 trim. = **−0,5 % de media**

Por qué importa para el poder de predicción: **este es exactamente el régimen
que el modelo campeón (drift) no puede ver.** La subida de precios de 2024–25
fue un shock de demanda que ningún candidato anticipó — y la aceleración
demográfica de los años previos lo venía señalando. No es un proxy más: es el
candidato a convertir el punto ciego estructural del drift (los giros) en algo
anticipable. La población es además el driver MÁS predecible a medio plazo (los
residentes de dentro de 2,5 años ya están casi todos aquí), lo que lo hace
idóneo para una cadena condicional (ver `docs/arquitecturas_prediccion.md`).

## El compañero robusto: las hipotecas

Las hipotecas constituidas (interanual) lideran el precio en 1 trimestre, y la
correlación decae de forma SUAVE con el adelanto (r = 0,63 → 0,65 → 0,61 → 0,56
→ 0,43 a leads 0–4), señal de robustez, no de un pico espurio. Muestra completa
(n=76). El crédito que fluye hoy es precio mañana: el termómetro de corto plazo.

## Lo que NO se adopta sin más

- La **población interanual** a 12 trimestres (r=−0,68) es la correlación más
  alta pero la más frágil: n=37, adelanto en el borde de la muestra, y el signo
  negativo lo domina un único episodio (el boom migratorio 2005–07 que precedió
  al desplome de 2011–13). Se reporta, no se destaca.
- Ningún proxy es todavía un modelo de producción. El contest previo
  (`docs/demanda_suelo.md`) ya probó hipotecas/compraventas/población como
  features de un GBM y NO batieron al drift a corto plazo — recordatorio de que
  correlación adelantada in-sample ≠ ganar out-of-sample. La aceleración de
  población NO se había probado a su adelanto natural de 10 trimestres; es el
  próximo candidato legítimo para el harness, evaluado en validación y adoptado
  solo si gana con datos 2026+.

## Uso propuesto

1. Añadir `aceleracion_poblacion` (retardo 10 trim.) como feature al candidato
   T1 y correr la parrilla pre-registrada — su valor está en los GIROS, que la
   ventana de validación 2019–2023 apenas contiene, así que su prueba real
   llegará con los datos de 2026+.
2. Como cadena condicional: proyección de población (driver predecible) →
   aceleración → señal de presión de precios a 2,5 años, con su banda.
