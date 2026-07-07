# Análisis de opciones para el TFM — rationale, datos y pros/contras

*Documento de decisión. Fuentes verificadas en vivo el 2026-07-07 (129 comprobaciones HTTP reales sobre APIs y descargas). Complementa la trazabilidad de [01_ideas_producto.md](entregas/01_ideas_producto.md) y [02_datos_necesarios.md](entregas/02_datos_necesarios.md).*

---

## 1. Contexto y criterios de decisión

**Feedback del tutor (Entrega 1):** reducir radicalmente el alcance (viable en 6 meses), evitar combinar demasiadas tecnologías y capas institucionales, datos accesibles, contribución clara de Data Science, y **converger** en una única línea principal.

**Calendario:** Entrega 2 (idea + datos) — 10 de julio. Entrega 3 (modelo de datos + capa gold) — 18 de julio. La Entrega 2 ya está redactada y comprometida en el repo sobre la opción Vivienda; cualquier pivote implica reescribirla en menos de 3 días.

**Criterios de evaluación usados aquí:**
1. Accesibilidad de datos (verificada, no supuesta)
2. Forma y tamaño muestral (¿soporta ML/DL honestamente?)
3. Alineación con el feedback del tutor
4. Riesgo metodológico ante un tribunal
5. Coste de pivote a 3 días de la Entrega 2
6. Contribución clara y diferenciada de Data Science

---

## 2. Arquitectura común (independiente del dominio)

Todas las opciones comparten la misma arquitectura objetivo, que combina la matemática de series temporales (ML/DL) con capacidades LLM:

```
Descargador web (tool) ──> data/raw ──> data/processed ──> data/gold (contrato de datos)
                                                              │
                                          ┌───────────────────┴──────────────────┐
                                          ▼                                      ▼
                              Forecaster ML/DL series temporales        RAG (vector DB de documentos:
                              + motor de escenarios                     informes, notas de prensa, normativa)
                                          │                                      │
                                          └────────────────┬─────────────────────┘
                                                           ▼
                                           LLM: análisis, comparación de escenarios
                                           y conclusiones fundamentadas con citas
```

**Principio de reparto:** lo que tiene serie temporal limpia alimenta el modelo ML (capa gold); lo que es estructural/cualitativo (regulación, fiscalidad, narrativa de mercado) alimenta el RAG. El LLM consume ambos. La arquitectura está decidida; **la única variable de decisión es el dominio**, y debe elegirse por la forma de sus datos.

---

## 3. Opción A — Vivienda extendida (proyecto actual + drivers + ML + RAG)

**Idea:** índice de asequibilidad de vivienda por CCAA (ya construido) extendido con: forecasting del IPV trimestral por CCAA (SARIMAX/gradient boosting + un modelo DL comparativo), motor de escenarios (trayectorias de salarios/IPC/Euríbor) y asistente RAG sobre informes del Banco de España y notas de prensa del INE.

**Rol del ML:** panel de 17 CCAA × ~75 trimestres (~1.275 observaciones) — el único dominio con estructura de panel, que permite modelos de series temporales con regresores exógenos y validación honesta.
**Rol del LLM/RAG:** cualificar escenarios con evidencia recuperada (escasez de suelo, cambios fiscales, demanda extranjera — los drivers sin serie limpia).

### Datos (verificados 2026-07-07)

| Fuente | Serie | Acceso | Historia | Estado |
|---|---|---|---|---|
| INE wstempus | IPV anual (49300) + trimestral (76201), IPC (76136), salarios EES (28191) | API JSON sin clave | 2007–2025 / 2008–2024 | ✅ verificado en vivo (ya en pipeline) |
| Banco de España | Euríbor 12m — `ti_1_7.csv` | CSV directo sin clave | diario, 1999–2026-07-06 (12.403 filas) | ✅ verificado en vivo |
| MITMA Boletín | Precio suelo urbano (€/m², trimestral, provincial, tabla 36400500) | XLS directo | 2004–2026T1 (187,77 €/m² nacional) | ✅ verificado en vivo |
| MITMA Boletín | Índice de Costes de la Construcción (mensual, nacional) | XLS directo | 2005–may 2026 (122,68, base 2021) | ✅ verificado en vivo |
| MITMA Boletín | Valor tasado de la vivienda (trimestral, provincial) — bonus | XLS directo | 1995–2026 | ✅ verificado en vivo |
| Registradores | % compraventas por extranjeros por CCAA (p. ej. Baleares 31,47% 4T2025) | PDF trimestral (WAF: requiere User-Agent de navegador); redistribución XLSX/CSV en datos.gob.es | ~2007+ | ✅ PDF verificado; XLSX por confirmar |
| BdE + INE (RAG) | Doc. Ocasional 2433 "El mercado de la vivienda", IEF Otoño 2025, notas de prensa IPV | PDF público | corpus amplio | ✅ verificado en vivo |

### Pros
- **Coste de pivote cero:** Entrega 2 redactada, pipeline funcionando, fuentes núcleo verificadas dos veces.
- **La mejor forma de datos de las cinco opciones:** panel CCAA×trimestre; ML/DL se justifica sin sonrojo.
- Todos los drivers nuevos verificados en vivo hoy; todos descarga directa sin registro.
- Alineación máxima con el tutor: es la línea "monitorización/forecasting con datos accesibles" que él mismo avaló.
- La complejidad del mercado (suelo, fiscalidad, demanda extranjera) se convierte en argumento del diseño: lo no modelable va al RAG.
- Relevancia social evidente y fácil de defender.

### Contras
- Menos "original" que las cebollas; el mercado de vivienda está muy estudiado (mitigación: el ángulo asequibilidad-por-CCAA + arquitectura híbrida ML+RAG sí es diferencial).
- Ficheros .xls legados de MITMA (parser xlrd) y extracción de tablas PDF para la cuota de compradores extranjeros.
- El desfase salarial (EES ~1,5 años) deja el último año del índice como provisional (ya documentado en Entrega 2).

**Veredicto: RECOMENDADA.** Única opción sin coste de pivote y con estructura de panel.

---

## 4. Opción B — Pensiones (versión acotada del tema fiscal)

**Idea:** sostenibilidad del sistema de pensiones español: forecasting de la ratio afiliados/pensionistas y de la pensión media vs salarios, escenarios demográficos anclados en las proyecciones oficiales del INE, y RAG sobre documentos AIReF / Ageing Report europeo.

**Rol del ML:** forecasting de componentes (afiliación, altas/bajas de pensiones, pensión media) — no del veredicto de sostenibilidad, que es aritmética demográfica.
**Rol del LLM/RAG:** corpus excelente (AIReF, Ageing Report 2024 con proyecciones a 2070, opiniones sobre la reforma 2021-2023).

### Datos (verificados 2026-07-07)

| Fuente | Serie | Acceso | Historia | Estado |
|---|---|---|---|---|
| Seguridad Social EST24 | Nº pensiones + pensión media, mensual, por clase/régimen/CCAA/edad | XLSX abierto (URLs con GUID → scraping ligero de la página) | actual a jun 2026; profundidad ~2005+ (por confirmar en eSTADISS) | ✅ XLSX jun-2026 descargado y parseado |
| Seguridad Social PXWeb | Afiliación mensual | **solo exportación GUI** (API REST desactivada, 404) | ~2009+ | ⚠️ portal confirmado; automatización con fricción |
| INE proyecciones | Población proyectada a 2076, esperanza de vida | API JSON sin clave (t=36775 y afines) | horizonte 2026–2076 | ✅ verificado en vivo |
| AIReF + CE (RAG) | Docs técnicos pensiones, Ageing Report ip279 | PDF público (airef.es con peculiaridad TLS en WSL → CA bundle actualizado) | 2019–2026 | ✅ verificado en vivo |

### Pros
- Versión legítima y acotada del interés fiscal: **un** sistema, no siete.
- Tema de enorme relevancia y actualidad; corpus RAG de primera calidad.
- Proyecciones demográficas oficiales como ancla de escenarios (defendible).
- Datos núcleo abiertos y actuales (junio 2026).

### Contras
- **Pivote completo** a 3 días de la Entrega 2: reescribir 01 (convergencia) y 02 enteros, con fuentes recién verificadas pero sin pipeline.
- Afiliación sin API: exportación manual GUI o replay de postbacks PXWeb (esfuerzo de scraping).
- Profundidad histórica mensual por confirmar (~2005+); una sola unidad (España), sin panel.
- Riesgo metodológico: el tribunal preguntará qué aporta el ML frente al modelo actuarial de AIReF; exige un encuadre muy cuidadoso ("forecasting de componentes", no "veredicto de sostenibilidad").

**Veredicto: SEGUNDA OPCIÓN.** Elegible solo si la motivación personal por el tema fiscal supera el coste de pivote y la fricción de afiliación.

---

## 5. Opción C — PIB de España con escenarios

**Idea:** forecasting del PIB trimestral español con ML clásico/híbrido y simulación de escenarios condicionados a trayectorias exógenas (inflación, paro), comparando contra las proyecciones WEO del FMI.

### Datos (verificados 2026-07-07)

| Fuente | Serie | Acceso | Historia | Estado |
|---|---|---|---|---|
| INE CNTR | PIB trimestral (tabla 67822, serie CNTR6721) | API JSON sin clave | 1995T1–2026T1 (125 obs) | ✅ verificado en vivo |
| Eurostat | namq_10_gdp (actualizado ayer) | API JSON sin clave | 1995T1–2026T1 | ✅ verificado en vivo |
| OCDE SDMX | PIB niveles + tasas de crecimiento | API sin clave | niveles 1995+; tasas desde 1960T2 | ✅ verificado en vivo |
| FMI DataMapper | WEO: proyecciones 2026–2031 | API abierta | 1980–2031 | ✅ verificado en vivo (anclas de escenarios) |
| Eurostat | HICP mensual (1996+), paro trimestral (2003+, ojo: `age=Y15-74`) | API sin clave | ver notas | ✅ verificado en vivo |

### Pros
- Los datos más limpios y redundantes de las cinco opciones (4 APIs independientes, cero fricción).
- Las proyecciones WEO del FMI dan un benchmark externo elegante para los escenarios.
- Frecuencia única (trimestral), sin alineación multi-frecuencia.

### Contras
- **125 observaciones y una sola unidad**: DL indefendible; incluso el ML clásico compite mal contra un AR simple en PIB — literatura enorme que lo demuestra.
- Contribución de DS difícil de diferenciar: BdE, AIReF, FMI, OCDE y decenas de servicios de estudios ya hacen esto con más medios.
- Pivote completo de las entregas 1-2.
- El RAG queda ornamental: el corpus (informes de coyuntura) no cambia el forecast.

**Veredicto: TERCERA OPCIÓN.** Datos impecables, proyecto débil.

---

## 6. Opción D — Cebollas (precio con proxies de trigo, clima y fertilizantes)

**Idea original "Trigo-a-Cebolla" sin blockchain:** predecir el precio español de la cebolla con su histórico + futuros de trigo + climatología + fertilizantes.

### Datos (verificados 2026-07-07)

| Fuente | Serie | Acceso | Historia | Estado |
|---|---|---|---|---|
| MAPA | Precio medio nacional semanal de cebolla (€/100kg; p. ej. 46,82) | XLSX abierto, 1 fichero/año | **2019–2025 confirmado** (7 años; anterior sin confirmar) | ✅ verificado en vivo |
| Euronext MATIF | Futuros trigo panificable (EBM), diario por contrato | página abierta pero **hostil a scripts** (ajax cifrado); descarga manual CSV por contrato + empalme de contratos | ~10 años | ⚠️ solo página confirmada |
| — | ~~yfinance `EBM=F`~~ | — | — | ❌ **TRAMPA: resuelve a futuros Micro Bitcoin de CME, no a trigo MATIF** |
| Banco Mundial Pink Sheet | Trigo US HRW/SRW + fertilizantes (DAP, urea…), mensual | XLSX abierto (el doc-id de la URL rota: scrapear el enlace vigente) | 1960–jun 2026 | ✅ verificado en vivo |
| AEMET OpenData | Climatología diaria por estación | API con clave gratuita (alta en ~2 min); ventanas de ~6 meses por petición | décadas | ⚠️ modelo de auth confirmado, sin datos aún |

### Pros
- La más original y la de mayor motivación personal (idea propia de la Entrega 1).
- Variable objetivo confirmada como abierta y semanal.
- Covariables de fertilizantes/trigo mensual gratis (Banco Mundial).

### Contras
- **Historia corta confirmada: ~7 años semanales** (~364 puntos) — justo para ML clásico, corto para DL estacional-anual (7 ciclos de cosecha).
- Futuros MATIF resistentes a automatización: descargas manuales por contrato + empalme; el atajo yfinance es directamente erróneo.
- Alineación multi-frecuencia semanal/mensual/diaria de 4 fuentes heterogéneas.
- **El tutor ya relegó esta idea** ("las demás podrían mantenerse como alternativas solo si evolucionan hacia un problema más acotado"). Volver a ella reabre la crítica de la Entrega 1.
- Pivote completo de las entregas 1-2.

**Veredicto: CUARTA OPCIÓN.** Viable a duras penas, pero contradice el feedback recibido y tiene la peor relación esfuerzo/defensa.

---

## 7. Opción E — Sostenibilidad fiscal integral (deuda, pensiones, sanidad, pobreza infantil…)

**Idea:** gasto público + PIB + pobreza infantil + pensiones + sanidad + ingresos fiscales + infraestructuras; escenarios de pago de la deuda y sostenibilidad de pensiones/sanidad.

### Datos (verificados 2026-07-07)

| Fuente | Serie | Acceso | Historia | Estado |
|---|---|---|---|---|
| Eurostat | Déficit/deuda EDP (gov_10dd_edpt1): -6,8% (1995) → -2,4% (2025) | API sin clave | 1995–2025 anual | ✅ verificado en vivo |
| Eurostat | Gasto COFOG (gov_10a_exp): sanidad 5,2%→6,5% PIB | API sin clave | 1995–2024 anual | ✅ verificado en vivo |
| Eurostat | AROPE infantil (ilc_peps01n): 33,8% (2025) | API sin clave | 2015–2025 (+empalme 2004–2020 con **ruptura metodológica**) | ✅ verificado en vivo |
| IGAE | Cuentas de las AAPP, detalle subsectores | XLSX dispersos; **bloquea clientes no-navegador** (User-Agent) | ~1995+ | ⚠️ página confirmada |
| BdE | Deuda PDE | portal datos.bde.es (los CSV legados están **muertos**); API con clave | ~1995+ | ⚠️ página confirmada |

### Pros
- El núcleo Eurostat es descargable en una tarde, sin clave.
- Tema de peso.

### Contras — dominantes
- **Contradice frontalmente el feedback del tutor**: siete dominios institucionales cuando pidió evitar "capas institucionales" y reducir radicalmente.
- **Desajuste metodológico de fondo:** "¿se puede pagar la deuda?" es una identidad contable (saldo primario + diferencial r−g); "¿son sostenibles las pensiones?" es demografía a 30 años. Ninguna es aprendible de ~30-45 puntos anuales. O el ML sobra (simulador contable) o sobrepromete (ML sobre 30 puntos) — en ambos casos el tribunal lo desmonta.
- Series anuales cortas, ruptura metodológica en pobreza infantil (2015), fricción IGAE/BdE.
- Pivote completo + el proyecto con mayor alcance de los cinco, con el plazo más corto.

**Veredicto: DESCARTAR.** Si el tema fiscal motiva, la vía es la Opción B (pensiones, acotada).

---

## 8. Matriz comparativa

| Criterio | A. Vivienda ext. | B. Pensiones | C. PIB | D. Cebollas | E. Fiscal integral |
|---|---|---|---|---|---|
| Datos verificados en vivo | ✅ todos | ✅ núcleo (afiliación ⚠️) | ✅ todos | ⚠️ futuros con fricción | ✅ núcleo (IGAE/BdE ⚠️) |
| Forma/tamaño muestral | **Panel 17×75 (~1.275)** | 1 unidad, mensual ~2005+ | 1 unidad, 125 obs | 1 unidad, ~364 obs (7 ciclos) | 1 unidad, ~30-45 obs anuales |
| Soporta ML/DL honesto | ✅ ML sí, DL comparativo | ~ componentes sí | ⚠️ justo | ⚠️ justo | ❌ |
| Alineación con tutor | ✅ línea avalada | ~ acotada, defendible | ~ neutra | ❌ relegada por tutor | ❌ crítica frontal |
| Coste de pivote (E2 el 10-jul) | **Cero** | Alto | Alto | Alto | Alto |
| Riesgo ante tribunal | Bajo | Medio | Medio-alto | Medio-alto | Alto |
| Papel del RAG | ✅ estructural (suelo, fiscalidad) | ✅ excelente corpus | ⚠️ ornamental | ~ boletines agrarios | ✅ corpus, pero da igual |
| Originalidad | Media | Media-alta | Baja | **Alta** | Media |

## 9. Recomendación

**Opción A (Vivienda extendida), sin dudas materiales.** Es la única con estructura de panel (el ML se defiende solo), la única sin coste de pivote a 3 días de la Entrega 2, la línea explícitamente avalada por el tutor, y todos sus drivers nuevos quedaron verificados en vivo hoy. La arquitectura ML+escenarios+RAG que motiva las demás opciones se implementa íntegra aquí.

**Plan B documentado:** Opción B (Pensiones) si la motivación fiscal pesa más — pivote asumible solo decidiéndolo hoy mismo. Las opciones C, D y E quedan registradas con su evidencia para la trazabilidad del proceso de convergencia.

**Impacto en entregas:** con la Opción A, la Entrega 2 necesita solo una edición menor (MVP extendido con forecasting+escenarios+RAG, fila Euríbor/BdE en fuentes); la Entrega 3 hereda una capa gold más rica (panel trimestral + drivers) ya diseñable sobre fuentes verificadas.
