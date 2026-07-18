# Driver de oferta `oferta_nueva` — primera pata (permisos residenciales)

*2026-07-18. Ejecuta el compromiso de la [Revisión 1 de la Entrega 4](entregas/04_analisis_modelado.md) y la línea de trabajo futuro declarada en [candidatos](candidatos_t1.md) §4: incorporar la construcción privada como señal de oferta. Script: [`analysis/oferta_nueva.py`](../analysis/oferta_nueva.py); datos: `storage/processed/building_permits_q.csv` (Eurostat `sts_cobp_q`, permisos de vivienda nº, residencial excl. residencias colectivas, índice 2021=100, 39 geos, ES 1995Q1–2026Q1).*

---

## 1. Hallazgos

![Permisos vs IPV](figures/eda/f8_oferta_nueva.png)

1. **La serie es un sismógrafo del ciclo:** permisos españoles 1042 (media 2006, índice 2021=100) → **44** (2013), un colapso del 96 %, con caída iniciada en 2006–07 — MUCHO antes que los precios. Hoy: 283 (2025), casi el triple del nivel 2021, en plena aceleración con el boom.
2. **Es la señal adelantada más fuerte encontrada en todo el proyecto:** correlación de los permisos (crecimiento interanual) con el crecimiento futuro del IPV, r = 0,57 con 11 trimestres de adelanto — muy por encima del mejor exógeno anterior (salarios, 0,33; Euríbor, −0,19).
3. **En el único giro de la muestra funcionó:** mínimo de permisos 2013Q2, mínimo del IPV 2014Q1 — 3 trimestres de aviso. Exactamente el punto ciego del drift.
4. **Mecanismo, con honestidad:** la correlación positiva a largo adelanto dice que los permisos suben ANTES de que los precios aceleren — funciona como barómetro de demanda de los promotores tanto como señal de oferta futura. Para pronosticar da igual el canal; para interpretar, no, y se declara.

## 2. Reglas de uso (disciplina post-test)

- El test final 2024–25 está GASTADO: este driver se evaluará en la parrilla de **validación** (feature candidata: crecimiento interanual de permisos con retardos 8–12) y su adopción exigirá confirmación con **datos nuevos de 2026 en adelante**, trimestre a trimestre.
- La pata provincial (visados MITMA, provincial → CCAA) sigue pendiente y daría la variación regional que el índice nacional no tiene ([data_landscape](data_landscape.md)).
