# Test final T1 — única pasada sobre 2024Q1–2025Q4

*2026-07-18. La evaluación de un solo uso reservada desde la [Entrega 4 §7](entregas/04_analisis_modelado.md). Protocolo y regla de decisión fijados en el código ANTES de ejecutar ([`analysis/final_test_t1.py`](../analysis/final_test_t1.py)): se evalúan exactamente drift y GBM (los SARIMAX quedaron eliminados en validación), origen único 2023Q4, h=1–8; el híbrido drift+GBM solo se adoptaría si el GBM batiera al drift en h=6–8 en ≥12 de 17 CCAA.*

---

## 1. Resultados

MASE (media sobre las 18 series; escala in-sample hasta 2023Q4):

| h | drift | gbm |
|---|---|---|
| 1 | 0,39 | 1,29 |
| 2 | 0,96 | 1,33 |
| 4 | 1,51 | 4,58 |
| 6 | 3,02 | 7,88 |
| 8 | 3,85 | 9,27 |

Medias: h≤4 drift 1,05 / gbm 2,69 · h≥6 drift 3,48 / gbm 8,71.
**Regla de decisión: el GBM bate al drift en 0 de 17 CCAA → VEREDICTO: drift en todos los horizontes. Hipótesis del híbrido REFUTADA.**

![Test final](figures/backtest/b3_test_final.png)

## 2. Lecturas

1. **La ventaja del GBM en validación no generalizó — y la disciplina evitó un desastre.** En el panel derecho se ve el fallo: el GBM pronosticó una CAÍDA del IPV nacional (≈145→127) justo cuando el mercado subía de 152 a 187. El modelo aprendió reversión a la media de los años de crisis 2008–14 ("tras rachas calientes vienen caídas") y la aplicó al inicio del mayor boom de la muestra. Si el hallazgo post-hoc de validación se hubiera adoptado sin test final, el MVP habría publicado una predicción de desplome en pleno auge. Este es el argumento definitivo a favor del protocolo pre-registrado.
2. **2024–2025 fue una aceleración fuera de régimen para TODOS los métodos.** Hasta el drift, ganador claro, queda en MASE 1,05 en h≤4 (frente a 0,40 en validación) y 3,85 en h=8: el mercado creció por encima de cualquier extrapolación de su tendencia 2022–23. Conclusión honesta: a 2 años vista, en cambios de régimen, ningún método entrenado con esta información acota bien el nivel — la incertidumbre comunicada importa más que la predicción puntual.
3. **Consecuencia para el MVP:** producción = drift en h=1–8 con INTERVALOS EMPÍRICOS anchos derivados de los errores de backtesting (por horizonte), presentados como abanico. La predicción puntual se acompaña siempre del intervalo y de la advertencia de régimen; el motor de escenarios (Euríbor/salarios) pasa a ser la herramienta principal de comunicación, no la predicción central.
4. **El test está gastado.** No habrá más selección de modelos contra 2024–2025. Las mejoras futuras (driver `oferta_nueva`, features de régimen) se evalúan en validación y solo se confirmarán con datos nuevos (2026 en adelante), que irán llegando trimestre a trimestre.

## 3. Registro

- Ejecutado una única vez el 2026-07-18; errores completos en `figures/backtest/test_final_errores.csv` y desglose h=6–8 por CCAA en `test_final_por_ccaa_h6_8.csv`.
- Cadena completa del protocolo: [baselines](backtest_t1_baselines.md) → [candidatos](candidatos_t1.md) → este test. Cada endurecimiento o decisión quedó declarado antes de mirar el dato siguiente.
