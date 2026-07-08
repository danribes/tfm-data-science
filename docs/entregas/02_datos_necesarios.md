# Entrega 2 — Selección de Idea y Datos Necesarios

## 1. Idea seleccionada

**Índice de Asequibilidad de Vivienda Regional en España** — seleccionada entre las líneas avaladas por el tutor tras la Entrega 1 ([trazabilidad aquí](01_ideas_producto.md)), como versión acotada de "monitorización/forecasting con datos accesibles".

**Problema que resuelve.** El precio de la vivienda en España ha crecido muy por encima de los salarios reales desde 2014, pero este desequilibrio varía enormemente entre comunidades autónomas: Madrid y Baleares concentran la presión máxima mientras que las regiones interiores presentan dinámicas distintas. Este problema afecta a hogares que deciden dónde vivir, a administraciones que diseñan política de vivienda y a analistas que necesitan comparar regiones; sin embargo, no existe un indicador integrado, actualizable y de acceso libre que combine precio de vivienda, salarios e inflación regional en un único índice de asequibilidad. Resolverlo aporta una medida objetiva y comparable de cuánto se ha deteriorado (o recuperado) la capacidad de compra de vivienda en cada comunidad autónoma.

**Solución planteada.** Un pipeline ETL automatizado sobre datos públicos que combina la matemática de series temporales con capacidades LLM, con un reparto claro: **lo que tiene serie temporal limpia alimenta el modelo; lo que es estructural y solo existe como texto alimenta un RAG**. La capa numérica descarga las tablas del INE (IPV, salarios, IPC) más el Euríbor del Banco de España, construye el índice de asequibilidad por CCAA (`ratio = IPV_index / salario_idx`, base 2015) y entrena modelos de forecasting del IPV trimestral por comunidad (SARIMAX / gradient boosting, con un modelo de deep learning como comparación) sobre un panel de 17 CCAA × ~75 trimestres, con un motor de escenarios sobre trayectorias de salarios, inflación y tipos. La capa textual indexa en un almacén vectorial los informes públicos del Banco de España y las notas de prensa del INE — donde viven los drivers sin serie utilizable: suelo, fiscalidad, regulación, demanda extranjera — y un LLM genera las conclusiones comparando escenarios y citando la evidencia recuperada. Una única línea de Data Science (forecasting de asequibilidad); el LLM es su capa de entrega, no un segundo pilar tecnológico.

**MVP del proyecto final.** Lo que se verá funcionando al final del curso, por fases. Núcleo: (1) pipeline Python ejecutable (`fetch_data.py`) que descarga INE + Banco de España y genera los datasets procesados de forma reproducible; (2) notebook de análisis con heatmap CCAA×año del índice de asequibilidad, series temporales comparadas y ranking regional; (3) modelos de forecasting del IPV/asequibilidad por CCAA con escenarios (p. ej. salarios +2%, Euríbor 3,5%) y su evaluación honesta contra baselines simples. Extensión: (4) asistente RAG que responde preguntas sobre el mercado y redacta conclusiones de escenarios fundamentadas en los documentos indexados, con citas. El núcleo se sostiene solo: si la extensión LLM se retrasara, el proyecto sigue siendo completo y defendible.

---

## 2. Variables y Datos Necesarios

| Variable | Descripción | Granularidad | Fuente |
|---|---|---|---|
| IPV general | Índice de precios de vivienda (base 2015=100) | CCAA × año (anual) | INE Tabla 49300 |
| IPV nueva / segunda mano | Desagregación por tipo de vivienda | CCAA × año | INE Tabla 49300 |
| IPV trimestral | Base del panel de forecasting | CCAA × trimestre | INE Tabla 76201 |
| IPC general CCAA | Deflactor regional para valores reales | CCAA × mes → media anual | INE Tabla 76136 |
| Salario bruto anual | Media y percentiles por CCAA | CCAA × año | INE Tabla 28191 |
| Euríbor 12m | Driver de demanda (coste hipotecario); exógena en forecasting y palanca de escenarios | Nacional × día → media mensual/trimestral | BdE `ti_1_7.csv` |
| Precio suelo urbano | Driver de oferta (€/m²) | Provincial × trimestre → CCAA | MITMA Boletín, tabla 36400500 |
| Índice de costes de construcción | Driver de costes (materiales + mano de obra) | Nacional × mes | MITMA Boletín, sección 08 |
| % compraventas por extranjeros | Driver de demanda externa | CCAA × trimestre | Registradores (ERI) |
| Corpus documental (RAG) | Drivers estructurales sin serie: suelo, fiscalidad, regulación | Documento (PDF) | BdE informes + notas de prensa INE |

**Profundidad histórica necesaria:** 2007–2025 para IPV e IPC (ciclo completo crisis + recuperación + pico actual); los salarios (EES) empiezan en 2008, por lo que el índice de asequibilidad combinado cubre 2008–2024/25 — recorte asumido y sin impacto en el análisis del ciclo. Drivers: Euríbor desde 1999, suelo urbano desde 2004, costes desde 2005, extranjeros desde ~2007 — todos cubren de sobra la ventana del panel.  
**Volumen aproximado:** ~1.800 series brutas del INE (120 IPV anual + 240 IPV trimestral + 1.120 IPC + 324 salarios) más 4 ficheros de drivers → ~3.300 filas procesadas + panel de modelado de ~1.300 filas (17 CCAA × ~76 trimestres). Corpus RAG: ~20-40 PDFs. Volumen ligero, manejable íntegramente en pandas.  
**Datos esenciales:** IPV (anual y trimestral) + salarios + IPC + Euríbor — índice, forecasting y escenarios se sostienen con estos.  
**Datos deseables:** suelo urbano, costes de construcción y % extranjeros (drivers V2 del modelo); corpus RAG (capa de conclusiones — extensión que no bloquea el núcleo).

---

## 3. Fuentes de Datos

### INE — Instituto Nacional de Estadística

| Atributo | Detalle |
|---|---|
| URL API | `https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{id}` |
| Acceso | Público, sin registro, sin API key |
| Formato | JSON (formato Tempus del INE: lista de series, cada una con array `Data` de pares año/valor) |
| Descarga | Vía HTTP GET; parámetro `nult=N` para últimos N periodos |
| Disponibilidad histórica | IPV desde 2007; IPC desde 1961; salarios desde 2008 |
| Estabilidad | INE es organismo estatutario; URLs y esquema estables >10 años |
| Mantenimiento | Actualizaciones trimestrales (IPV) y anuales (salarios) |

**Operaciones y tablas utilizadas (enlaces):**
- Op. 15 — Índice de Precios de la Vivienda (IPV): [tabla 49300, anual](https://www.ine.es/jaxiT3/Tabla.htm?t=49300) · [tabla 76201, trimestral](https://www.ine.es/jaxiT3/Tabla.htm?t=76201)
- Op. 25 — Índice de Precios de Consumo (IPC): [tabla 76136, por CCAA](https://www.ine.es/jaxiT3/Tabla.htm?t=76136)
- Op. 140 — Encuesta Anual de Estructura Salarial: [tabla 28191](https://www.ine.es/jaxiT3/Tabla.htm?t=28191)
- Endpoint API por tabla: `https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{id}` ([documentación del servicio](https://www.ine.es/dyngs/DAB/index.htm?cid=1099))

**Verificación de disponibilidad (última: 2026-07-07, en vivo contra la API):**
```
Tabla 49300 → 120 series OK, IPV nacional hasta 2025 (índice 179,9; base 2015=100)
Tabla 76201 → 240 series OK, IPV trimestral por CCAA
Tabla 76136 → 1.120 series OK, IPC por CCAA (se usan las 20 de índice general)
Tabla 28191 → 324 series OK, salario medio nacional 29.540 € (2024)
```

**Riesgos detectados en la fuente:**
- Cambio de esquema o de IDs de tabla en la API del INE (histórico muy estable, pero sin garantía) → mitigable congelando snapshots CSV en `data/processed/`
- Servicio wstempus sin SLA ni límites de descarga documentados → descargas espaciadas con reintentos en el cliente
- Retraso estructural de publicación de la EES (~1,5 años: salario 2024 publicado en 2026) → el último año del índice siempre irá con desfase (ver tabla de riesgos en §5)
- Cobertura incompleta de Ceuta y Melilla en salarios y en desagregaciones del IPV → análisis restringido a las 17 CCAA

### Fuentes complementarias (drivers y corpus RAG)

| Fuente | Datos | Acceso | Formato | Verificación (2026-07-07) |
|---|---|---|---|---|
| [Banco de España](https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/ti_1_7.csv) | Euríbor 12m diario | CSV directo, sin clave | CSV (Latin-1, cabecera BdE) | ✅ descargado: 12.403 filas, 1999–2026-07-06 |
| [MITMA Boletín Estadístico](https://apps.fomento.gob.es/BoletinOnline2/?nivel=2&orden=36000000) | Precio suelo urbano trimestral provincial | XLS directo, sin registro | .xls legado (xlrd) | ✅ descargado: 2004T1–2026T1 (187,77 €/m² nacional) |
| [MITMA Boletín (sección 08)](https://apps.fomento.gob.es/Boletinonline/?nivel=2&orden=08000000) | Índice de costes de construcción mensual | XLS directo | .xls legado | ✅ descargado: 2005–may 2026 (122,68, base 2021) |
| [Registradores — ERI](https://registradores.org/actualidad/portal-estadistico-registral/estadisticas-de-propiedad) | % compraventas por extranjeros, CCAA trimestral | PDF trimestral (requiere User-Agent de navegador); redistribución XLSX/CSV en [datos.gob.es](https://datos.gob.es/es/catalogo/a16003011-tablas-estadisticas-de-la-estadistica-registral-inmobiliaria) | PDF / XLSX | ✅ PDF 4T2025 descargado (Baleares 31,47%) |
| [BdE publicaciones](https://www.bde.es) + [notas de prensa INE](https://www.ine.es/dyngs/Prensa/IPV1T26.pdf) | Corpus RAG: informes de mercado de vivienda, IEF, notas IPV | PDF público | PDF | ✅ do2433.pdf, IEF Otoño 2025 e IPV1T26.pdf descargados |

**Riesgos de las fuentes complementarias:** ficheros .xls legados del MITMA (parser `xlrd`, formato ancho por año); web de Registradores tras WAF (descarga con cabecera de navegador; alternativa machine-readable en datos.gob.es); extracción de tablas desde PDF para la serie histórica de extranjeros. Todos los drivers son deseables, no imprescindibles: su fallo no bloquea el núcleo.

---

## 4. Privacidad y Protección de Datos

- **Datos personales:** Ninguno. Todas las series son estadísticas agregadas publicadas por el INE.
- **Anonimización:** No requerida — la agregación por CCAA la hace de origen el propio INE.
- **Uso académico:** Seguro. Datos oficiales agregados bajo la licencia de reutilización del INE, aptos para un proyecto académico en un repositorio público de GitHub.
- **RGPD:** Sin implicaciones. Los datos son de uso libre (licencia INE reutilización).
- **Riesgo ético / legal:** Nulo. No hay datos de individuos ni categorías sensibles.
- **Datos evitados por privacidad:** Se descartó deliberadamente trabajar con microdatos (microdatos de la EES o transacciones inmobiliarias individuales del Colegio de Registradores), que darían más granularidad pero introducirían riesgo de reidentificación; el proyecto usa exclusivamente agregados por CCAA.
- **Corpus RAG:** Solo publicaciones institucionales públicas (Banco de España, INE) sin datos personales; se indexan documentos oficiales completos, con cita a la fuente en cada respuesta generada.

---

## 5. Viabilidad Inicial

### ✅ Favorable
- Datos 100% disponibles, verificados, descargables sin fricción
- Todas las fuentes (INE, BdE, MITMA, Registradores, corpus RAG) verificadas en vivo el 2026-07-07 con descargas reales — ver [análisis de opciones](../analisis_opciones_tfm.md)
- Pipeline EPA del mismo master como referencia directa (misma API INE, mismo esquema JSON)
- Granularidad CCAA suficiente para análisis regional con 17 unidades; el IPV trimestral aporta un panel de ~1.300 observaciones para el forecasting
- Sin dependencias externas ni costes

### ⚠️ Riesgos identificados
| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Salarios no anualizados al mismo año que IPV | Media | Interpolación lineal o inner join restrictivo |
| IPV base 2015=100 no comparable directamente con salarios | Baja | Índice normalizado sobre año base común |
| Desfase temporal de salarios (encuesta llega a 2024; IPV a 2025) | Media | Último año con ratio parcial o fuente alternativa: Agencia Tributaria IRPF (rendimientos trabajo por CCAA) |

**¿Es desarrollable de forma realista durante el curso?** Sí: el volumen es pequeño (~3.300 filas procesadas más un panel de ~1.300, manejable íntegramente en pandas), el pipeline reutiliza el patrón del ejercicio EPA del propio máster (misma API INE, mismo esquema JSON) y el MVP está faseado — el núcleo (ETL + índice + forecasting con escenarios) se descompone en hitos alcanzables entrega a entrega, y la extensión RAG solo se aborda con el núcleo cerrado, de modo que un retraso en ella no compromete el proyecto.

**Parte más arriesgada ahora mismo:** el acoplamiento temporal de las fuentes — los salarios llegan hasta 2024 con ~1,5 años de retraso estructural mientras el IPV ya publica 2025, así que el último año del índice siempre será provisional. Riesgo secundario: la fusión del panel de drivers (frecuencias diaria/mensual/trimestral/anual y geografías nacional/provincial/CCAA), acotada porque todos los drivers son deseables, no imprescindibles.

### Alternativas de datos
- **Ministerio de Vivienda:** Precios de transacción por m² por provincia (más granular que IPV)
- **Banco de España:** Esfuerzo hipotecario (ratio cuota/renta) — indicador complementario
- **Eurostat:** Comparativa internacional house price index vs salarios (tabla `prc_hpi_a`)
