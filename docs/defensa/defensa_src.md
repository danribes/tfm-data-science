# Dinero público → Resultados

**Defensa del Trabajo de Fin de Máster · Máster en Data Science (Evolve)**

Daniel Ribes · julio 2026

github.com/danribes/tfm-data-science

---

# El problema y la evolución del proyecto

- **Pregunta**: ¿qué obtiene un país (y una CCAA) a cambio de su gasto público?
- Origen avalado: **índice de asequibilidad de vivienda por CCAA** (entregas 1–3)
- Evolución: la vivienda es una partida más (GF06) → el marco general la **contiene y conserva como núcleo**
- El feedback del tutor, convertido en especificación verificable:
  - ratio SIEMPRE como indicador aproximado + medida de esfuerzo real
  - **MVP primero**: nada bloquea el núcleo
  - "el formato de entrega funciona como un contrato" → el repositorio ES la entrega

---

# Arquitectura de datos

```
connectors/ → raw (vintage) → processed (32) → gold (11) → analysis · api · app
```

- Más de **30 fuentes públicas**: INE, BdE, Eurostat, FMI, OMS, Banco Mundial, GMD/JST (1870–2023), UN DESA, MITMA
- `vintage_manifest.csv`: qué versión del dato existía en cada descarga
- **51 tests automáticos** del contrato de datos y modelos
- Nada entra en gold sin clave primaria verificada y smoke test

---

# La calidad de datos como resultado

- **3 bugs de pipeline detectados, corregidos y blindados con test de regresión**:
  - IPC: promediaba 1.120 series en vez de filtrar la general
  - IPV trimestral: se descargaba pero no se persistía
  - `str.split(". ")` de pandas es REGEX → rompía las CCAA compuestas (ratio solo en 8 de 18 territorios)
- El riesgo declarado en la Entrega 2 **se materializó**: el INE renumeró las tablas del IPV (49300/76201 → 80271/80270) — la mitigación prevista funcionó

---

# Metodología: protocolo pre-registrado

**Los criterios se fijan antes de mirar; endurecerlos vale, relajarlos no.**

1. EDA con decisiones vinculantes (transformación, pooling, exógenas)
2. Baselines difíciles ANTES de los candidatos
3. Validación rolling-origin con guardas anti-fuga verificadas por tests
4. **Test final de un solo uso** (2024–2025), regla de decisión escrita en el código
5. Multiverso: sin estabilidad entre especificaciones, no se publica
6. Incertidumbre SIEMPRE visible

---

# T1 · La vara a batir no era la esperada

- Naive estacional: MASE 0,89 — cómodo porque la escala la infla la crisis 2008–14
- **El drift (tendencia reciente): MASE 0,40** — imbatido en las 18 series, COVID incluido
- El criterio de aceptación se **ENDURECIÓ antes de entrenar candidatos**: batir al drift en ≥12 de 17 CCAA
- Sin ese endurecimiento, los tres candidatos habrían "aprobado"

---

# T1 · El test final evitó publicar un desplome

![height:430px](../figures/backtest/b3_test_final.png)

SARIMAX 1/17 · GBM 0/17 en validación corta; la hipótesis "GBM gana a largo" quedó **refutada 0/17**: pronosticó caída en pleno boom (reversión aprendida de la crisis)

---

# T1 · Pronóstico de producción

![height:400px](../figures/backtest/b4_fan_nacional.png)

- Drift + **abanico empírico 80/95 %** (asimétrico: el drift se queda corto en booms)
- **Ratio nacional: 1,26 (2024) → ~1,5–1,6 (2027) incluso con salarios al 2 %**

---

# El driver de oferta: la señal más fuerte del proyecto

![height:360px](../figures/eda/f8_oferta_nueva.png)

- Permisos residenciales: **r = 0,57 con 11 trimestres de adelanto**; avisó del giro 2013–14 con 3 trimestres
- Pata regional (licencias MITMA): colapso **×24** (737.186 → 31.236 viviendas/año)
- Disciplina: se adoptará solo si lo confirman los datos de 2026+

---

# Atlas fiscal · la figura que exige contexto

![height:400px](../figures/atlas/b03_vivienda_publica_vs_total.png)

**La palanca pública de vivienda (0,5 %PIB) es un orden de magnitud menor que la promoción privada (5,8 %PIB)** — contexto obligatorio de cualquier conclusión

---

# A1 · Rendimiento sanitario: nunca una liga

![height:380px](../figures/a1/a1_funnel.png)

- España: **+2,7 ± 3,5 años** — por encima de lo esperado, DENTRO de su banda
- Hallazgo honesto: hasta el OLS empata con la mediana del grupo de renta — **la renta domina**

---

# D1 · Escenarios de deuda: la demografía domina

![height:380px](../figures/d1/d1_deuda_escenarios.png)

- Central 2050: **224 %PIB** (banda 198–267) vs 127 % sin envejecimiento
- Ninguna palanca aislada estabiliza; el menú cuantifica, no prescribe

---

# El producto (MVP)

- **API FastAPI**: pronóstico con abanico, funnel, menú de escenarios, simulador interactivo con palancas r/g/pb
- **Dashboard Streamlit** de 4 pestañas con "TU SENDA" sobre el menú
- La honestidad viaja en el payload: `"no es un ranking"`, `"la banda es la parte informativa"`
- Todo servido desde artefactos gold pre-computados y testeados

---

# ¿Y esto no lo hace un LLM?

(ver tabla en deck.marp.md — fuente autoritativa del render)

---

# Conclusiones

1. Solo con fuentes públicas y código abierto: **datos → modelos → producto**, con trazabilidad profesional
2. **La aportación diferencial es la disciplina**: tres veces el modelo flexible perdió bajo reglas pre-registradas; una vez el protocolo evitó publicar una predicción de desplome en pleno boom
3. Sustantivo: la asequibilidad no se corrige sola; la palanca pública de vivienda es pequeña frente a la privada; la renta domina el rendimiento sanitario; la demografía domina la deuda

---

# Trabajo futuro y cierre

- Driver de oferta en la parrilla de validación con datos 2026+
- Cuota hipotecaria teórica (falta €/m²) · panel quinquenal para A1 · episodios históricos de consolidación
- Actualización trimestral: cada IPV nuevo re-ejecuta pipeline → gold → pronóstico

**Gracias.**

github.com/danribes/tfm-data-science · `docs/MEMORIA.md` · `streamlit run app/dashboard.py`
