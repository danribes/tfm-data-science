# Expansión del corpus de evidencia (2026-07-19)

Cierre de los conectores pendientes declarados tras la Entrega 4. Criterio: se
implementa todo lo alcanzable por rutas ya probadas (API pública, XLS estático);
lo que exige registro, scraping o dependencias geoespaciales se documenta como
bloqueado con su motivo, no se simula.

## 1. Conectores implementados en esta expansión

| Fuente | Serie | Cobertura | Archivo | Uso |
|---|---|---|---|---|
| MITMA BoletinOnline2 (35102000) | Valor tasado vivienda libre, €/m² por CCAA | 2010–2014, trimestral | `processed/mitma_valor_tasado_ccaa.csv` | Ancla de niveles para la cuota teórica (puente: × IPV propio de cada CCAA) |
| World Bank SPI (IQ.SPI.OVRL) | Statistical Performance Indicators | 2016– , ~170 países | `processed/wdi_policy.csv` | Auditoría residual⊥capacidad estadística del A1 (declarada en el PLAN, antes sin datos) |
| World Bank / SIPRI (MS.MIL.XPND.GD.ZS) | Gasto militar % PIB | 1960– | `processed/wdi_policy.csv` | Contexto de composición del gasto (atlas / RAG) |
| World Bank / UIS (SE.XPD.TOTL.GD.ZS) | Gasto educativo público % PIB | 1970– | `processed/wdi_policy.csv` | Input del módulo A1-educación |
| World Bank HCI (HD.HCI.HLOS) | Harmonized Learning Outcomes | ~170 países | `processed/wdi_policy.csv` | Outcome del módulo A1-educación (sustituye a PISA: cobertura mundial armonizada) |
| World Bank / OCDE-CAD (DC.ODA.TOTL.GN.ZS) | AOD neta donante % RNB | 1960– | `processed/wdi_policy.csv` | Contexto donante (RAG / atlas) |

Derivados analíticos nuevos:

- `analysis/cuota_teorica.py` → `gold/gold_cuota_teorica.csv`. Cuota hipotecaria
  teórica por CCAA (90 m², LTV 80 %, 25 años, Euríbor12m medio 2024 + 1 pp).
  Cierra el compromiso del PLAN_MAESTRO §7.2 con el tutor.
- `analysis/expansion_dl.py` → `gold/gold_rendimiento_edu.csv`. Módulo
  A1-educación (HLO ~ gasto + renta + urbanización) con contraste DL bajo LOOCV,
  y auditoría SPI del A1-salud. Resultados en `docs/MEMORIA.md` y en la salida
  del script.

## 2. Sobre "deep learning" en este corpus — decisión declarada

Se contrasta un MLP (perceptrón multicapa, 32×16, regularizado) como candidato
"deep" bajo el MISMO protocolo que el resto del proyecto: LOOCV y regla de
aceptación (batir al OLS por ≥10 % de MAE). No se usan arquitecturas mayores
porque el cuello de botella es n (~100–160 países por módulo), no la capacidad
del modelo: con esas muestras, más capas añaden varianza, no señal. La única vía
donde DL aporta de verdad valor diferencial (CNN sobre luces nocturnas para PIB
sin datos) queda bloqueada por dependencias (ver §3) y se declara como extensión.

## 3. Conectores bloqueados (motivo declarado)

| Fuente | Qué aportaría | Bloqueo |
|---|---|---|
| VIIRS/DMSP nightlights (Earth Engine / NOAA) | PIB estimado sin estadística oficial (CNN) | Registro Earth Engine + stack geoespacial (GDAL/rasterio) no presente; descarga masiva raster |
| UNU-WIDER GRD | Ingresos fiscales armonizados largos | Descarga manual con formulario (sin API) |
| CEPEJ (justicia) | Eficiencia judicial europea | Solo tablas HTML/PDF; requiere scraping frágil |
| Liquidaciones presupuestarias CCAA (MinHac) | Gasto autonómico funcional fino | Ficheros heterogéneos por año/CCAA sin esquema estable |
| Cohesion Open Data (UE) | Fondos de cohesión por región | API SPARQL compleja; prioridad baja para las preguntas del TFM |
| World Bank BOS (Bureaucracy) | Empleo/salarios públicos micro | Microdatos con licencia por país |
| BdE informes / INE PDFs | Corpus textual regulatorio | Pipeline PDF→md aparte; pospuesto (post-TFM, vía ai_library) |
| BOE | Series normativas | Post-TFM |
| GFS-COFOG global (IMF) | Gasto funcional mundial | Vía MCP IMF disponible pero pendiente de priorizar; COFOG-Eurostat ya cubre la UE |
| ECB Euríbor | Ya cubierto | Redundante: `processed/euribor_12m.csv` existe |
| GNI* (Irlanda) | PIB corregido | Ajuste puntual de un país; no cambia conclusiones |

## 4. Qué mejora con el corpus ampliado (medido, no prometido)

1. **Cuota teórica** (antes imposible: faltaba el nivel €/m²): esfuerzo nacional
   2024 = 41,6 % del salario bruto; Baleares 60,6 %, Madrid 56,0 %. El ratio
   índice y el esfuerzo real ordenan las CCAA con Spearman 0,79 — el ratio
   aproximado del panel era un buen proxy ordinal, y ahora hay medida en euros.
2. **A1-educación**: módulo nuevo completo (frontera gasto→aprendizaje) con
   residuales conformal por cuartil de renta, replicando el diseño del A1-salud.
3. **Auditoría SPI**: la comprobación residual⊥capacidad estadística declarada
   en el PLAN ya está ejecutada con datos reales (resultado en el script).
4. **Contraste DL honesto**: el MLP compite bajo las mismas reglas
   pre-registradas que GBM; el veredicto (gane o pierda) se publica sin retocar
   el criterio.
