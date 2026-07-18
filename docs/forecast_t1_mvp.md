# Pronóstico de producción T1 — abanico empírico y escenarios (MVP)

*2026-07-18. Cierra el contrato de salida de la [Entrega 4 §5](entregas/04_analisis_modelado.md): `storage/gold/gold_forecast_ccaa.csv` (432 filas = 18 series × h 1–8 × 3 escenarios), generado por [`analysis/forecast_t1.py`](../analysis/forecast_t1.py) y verificado por [`tests/test_forecast.py`](../tests/test_forecast.py). Modelo: drift, el ganador del [protocolo completo](test_final_t1.md).*

---

## 1. Cómo se construye

- **Punto:** drift puro (tendencia de los últimos 8 trimestres) desde el origen 2025Q4, h=1–8 (2026Q1–2027Q4).
- **Bandas 80/95 %:** cuantiles empíricos del error RELATIVO del drift por horizonte, sobre validación + test final (486 → 180 errores según h). El test está gastado para seleccionar; reutilizarlo para calibrar anchuras se declara: sin sus errores, las bandas ignorarían el único episodio fuera de régimen observado (2024–25).
- **Asimetría honesta:** la mediana del error es positiva y crece con el horizonte (+0,5 % en h=2 → +4,9 % en h=8): históricamente el drift SE QUEDA CORTO en este mercado. Las bandas lo heredan (h=8: −2,5 % / +18 %), y en h=8 el cuantil 10 ya es positivo — el punto cae marginalmente por debajo de su propia banda 80 %. No se corrige el punto (sería re-seleccionar tras el test); se muestra tal cual con su banda.
- **Escenarios (mueven el denominador, no el IPV):** sendas salariales anuales {0 %, 2 % central, 4 %} desde el último salario observado (EES 2024) → `ratio_aseq_pred`. Herramienta de comunicación, no predicción salarial.

## 2. Lectura central (escenario salarial 2 %)

| Periodo | IPV nacional (2015=100) | banda 80 % | ratio asequibilidad |
|---|---|---|---|
| 2026Q4 (h=4) | 205,8 | 200,4 – 218,1 | 1,54 |
| 2027Q4 (h=8) | 224,8 | 225,7 – 253,8 | 1,64 |

Si la tendencia 2024–25 continúa, el ratio nacional pasaría de 1,26 (2024 observado) a ~1,5–1,6 en 2027 incluso con salarios creciendo al 2 %: la brecha no se cierra sin un cambio de régimen (de tipos, de oferta o salarial). Con salarios al 4 %, el ratio 2027Q4 baja solo unas centésimas — el mensaje del MVP es que el denominador no puede compensar por sí solo el ritmo actual del numerador.

![Abanico nacional](figures/backtest/b4_fan_nacional.png)

## 3. Advertencias que acompañan SIEMPRE a esta salida

1. El ratio es un **indicador aproximado** de evolución relativa (feedback del tutor, [PLAN_MAESTRO §7](PLAN_MAESTRO.md)); el complemento de esfuerzo real (cuota teórica) llegará con el precio por m².
2. El drift es ciego a giros de ciclo y 2024–25 demostró que también se queda corto en aceleraciones: la banda es la parte informativa del pronóstico, no el punto.
3. Actualización trimestral: cada IPV nuevo del INE re-ejecuta pipeline → gold → pronóstico; los errores frente a 2026 en adelante serán la primera validación verdaderamente out-of-sample del protocolo.
