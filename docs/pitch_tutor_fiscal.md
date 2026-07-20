# Propuesta de evolución del TFM — "El precio de lo público"

*Daniel Ribes · TFM Máster en Data Science · 2026-07-17 · 1 página*

Estimado [tutor],

Tras las Entregas 1–3 del proyecto de asequibilidad de vivienda, he seguido explorando el dominio fiscal y he encontrado una pregunta que creo más potente, manteniendo intacta la disciplina que me pediste: alcance radicalmente acotado, una sola línea técnica, datos abiertos y contribución clara de Data Science. Te la propongo aquí en una página; **si no la ves, el proyecto de vivienda sigue en pie tal cual** (rama principal intacta, entregas ya comprometidas).

## La pregunta

**¿Qué gobiernos convierten mejor el dinero de sus contribuyentes en resultados para la población — ajustando por contexto — y qué papel juega la composición del gasto (inversión vs gasto corriente)?**

No es el proyecto "fiscal integral" que descartaste en la Entrega 1 — aquello apilaba siete dominios institucionales. Esto es **un solo método aplicado a 2–3 pares gasto→resultado** (sanidad como núcleo, educación como réplica), con guardarraíles metodológicos explícitos: nada de afirmaciones causales ni "el país X debería reasignar", solo *rendimiento ajustado* con incertidumbre cuantificada.

## Una sola línea técnica

Gradient boosting prediciendo el resultado (p. ej. mortalidad tratable) a partir del gasto (promediado 5 años, con retardo 3–5) y controles (renta, demografía, gobernanza). El "rendimiento ajustado" de cada país = residual del modelo **con intervalo de confianza conformal** — solo se señala a países cuyo intervalo excluye cero, en funnel plot (la misma lógica de los SMR hospitalarios de mi campo, HEOR). Validación leave-country-out + bloques temporales; multiverso de especificaciones para la estabilidad. SHAP para umbrales no lineales: ¿aporta más un euro de inversión que un euro corriente? Sin DEA, sin RAG, sin deep learning (exclusión justificada por escrito).

## Datos: verificados en vivo, no supuestos (comprobaciones HTTP reales, 16–17 jul)

| Fuente | Qué da | Estado |
|---|---|---|
| Eurostat `gov_10a_exp` | gasto por función (COFOG) × tipo económico (inversión P51G vs corriente), 33 países, 1995–2023, API sin clave | ✅ verificado |
| WHO GHED | gasto sanitario ~190 países, 2000–2023, descarga directa | ✅ verificado |
| INE/IGAE | COFOG España 1995–2023 (un xlsx) + series por subsector | ✅ verificado |
| Resultados | mortalidad tratable, esperanza de vida, PISA, EU-SILC | ✅ verificado |

**Muestra de lo que ya sale de estos datos (2023, %PIB):** en vivienda, Italia gasta 4,4 (artefacto *superbonus* — caso de outlier documentado), la UE 1,2 y **España 0,5**; en inversión pública, Estonia 6,5, la UE 3,6 y **España 3,0**. Francia es el mayor gastador corriente (~53). La dimensión inversión/corriente sale directamente del dataset — nadie la explota con ML a nivel función.

## Tres variantes — te pido criterio

| | **A — UE (33 países)** | **B — Global (~180 países)** | **C — Vivienda como caso de consecuencias** |
|---|---|---|---|
| Fortaleza | composición inversión/corriente en TODAS las funciones; datos homogéneos | muestra estadística muy superior para ML; encaje con mi perfil HEOR (sanidad global) | **pivote mínimo**: conserva el proyecto de vivienda que avalaste y le añade la capa fiscal (cuánto/cómo se gasta en vivienda, qué rendimiento obtiene cada país/CCAA) y el amplificador migratorio |
| Debilidad | N=33 justo para ML (mitigado y declarado) | por función solo ~60–90 países; calidad heterogénea (estratifico por renta) | alcance temático más estrecho (una función como hilo conductor) |

Las tres comparten método, calendario y salvaguardas; tengo el plan de trabajo completo de cada una (tareas, semanas, riesgos, criterios de aceptación) por si quieres verlos. Si tuviera que elegir yo, C es la de menor riesgo y mayor continuidad con lo ya entregado.

## Calendario (10 semanas, deadline 30-sep)

S1 aval+conectores · S2–S3 panel gold con tests (= nueva Entrega 3) · S4–S5 módulo sanidad completo · **S5 checkpoint contigo** · S6–S7 réplica + síntesis · S8 app Streamlit · S9 borrador completo a tu revisión · S10 margen.

## Lo que te pido

1. ¿Ves viable el giro, sí o no? — con un "adelante" por email me basta para arrancar.
2. Si sí: ¿variante A (UE) o B (global)?
3. Si no: sigo con vivienda sin coste alguno — nada de lo hecho se pierde.

Gracias,
Daniel
