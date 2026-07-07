# Entrega 2 — Selección de Idea y Datos Necesarios

## 1. Idea seleccionada

**Índice de Asequibilidad de Vivienda Regional en España** — seleccionada entre las líneas avaladas por el tutor tras la Entrega 1 ([trazabilidad aquí](01_ideas_producto.md)), como versión acotada de "monitorización/forecasting con datos accesibles".

**Problema que resuelve.** El precio de la vivienda en España ha crecido muy por encima de los salarios reales desde 2014, pero este desequilibrio varía enormemente entre comunidades autónomas: Madrid y Baleares concentran la presión máxima mientras que las regiones interiores presentan dinámicas distintas. Este problema afecta a hogares que deciden dónde vivir, a administraciones que diseñan política de vivienda y a analistas que necesitan comparar regiones; sin embargo, no existe un indicador integrado, actualizable y de acceso libre que combine precio de vivienda, salarios e inflación regional en un único índice de asequibilidad. Resolverlo aporta una medida objetiva y comparable de cuánto se ha deteriorado (o recuperado) la capacidad de compra de vivienda en cada comunidad autónoma.

**Solución planteada.** Un pipeline ETL automatizado sobre la API pública del INE que descarga cuatro tablas estadísticas en JSON sin autenticación, las limpia y transforma a DataFrames de pandas, y construye un índice de asequibilidad por comunidad autónoma y año (`ratio = IPV_index / salario_idx`, ambos normalizados a base 2015). Sobre ese índice se apoya el análisis: evolución temporal por CCAA, comparativas regionales, ajuste por inflación con el IPC y una primera capa de modelado predictivo. El enfoque es deliberadamente sobrio — Python, pandas y datos públicos — siguiendo la indicación del tutor de no apilar tecnologías.

**MVP del proyecto final.** Lo que se verá funcionando al final del curso: (1) un pipeline Python ejecutable (`fetch_data.py`) que descarga los datos del INE y genera los datasets procesados de forma reproducible; (2) un notebook de análisis con visualizaciones — heatmap CCAA×año del índice de asequibilidad, series temporales comparadas y ranking regional; y (3) un modelo de regresión inicial (`precio_vivienda ~ salario + IPC + año`) que cuantifica la relación entre salarios, inflación y precio de la vivienda y permite una proyección simple a corto plazo.

---

## 2. Variables y Datos Necesarios

| Variable | Descripción | Granularidad | Fuente INE |
|---|---|---|---|
| IPV general | Índice de precios de vivienda (base 2015=100) | CCAA × año (anual) | Tabla 49300 |
| IPV nueva / segunda mano | Desagregación por tipo de vivienda | CCAA × año | Tabla 49300 |
| IPV trimestral | Evolución intra-anual del precio | CCAA × trimestre | Tabla 76201 |
| IPC general CCAA | Deflactor regional para valores reales | CCAA × mes → media anual | Tabla 76136 |
| Salario bruto anual | Media y percentiles por CCAA | CCAA × año | Tabla 28191 |

**Profundidad histórica necesaria:** 2007–2025 para IPV e IPC (ciclo completo crisis + recuperación + pico actual); los salarios (EES) empiezan en 2008, por lo que el índice de asequibilidad combinado cubre 2008–2024/25 — recorte asumido y sin impacto en el análisis del ciclo  
**Volumen aproximado:** ~1.800 series brutas descargadas (120 IPV anual + 240 IPV trimestral + 1.120 IPC + 324 salarios), de las que se filtran las relevantes → ~3.300 filas procesadas. Volumen ligero, manejable íntegramente en pandas.  
**Datos esenciales:** IPV anual + salarios  
**Datos deseables:** IPV trimestral + IPC para ajuste inflación

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

---

## 4. Privacidad y Protección de Datos

- **Datos personales:** Ninguno. Todas las series son estadísticas agregadas publicadas por el INE.
- **Anonimización:** No requerida — la agregación por CCAA la hace de origen el propio INE.
- **Uso académico:** Seguro. Datos oficiales agregados bajo la licencia de reutilización del INE, aptos para un proyecto académico en un repositorio público de GitHub.
- **RGPD:** Sin implicaciones. Los datos son de uso libre (licencia INE reutilización).
- **Riesgo ético / legal:** Nulo. No hay datos de individuos ni categorías sensibles.
- **Datos evitados por privacidad:** Se descartó deliberadamente trabajar con microdatos (microdatos de la EES o transacciones inmobiliarias individuales del Colegio de Registradores), que darían más granularidad pero introducirían riesgo de reidentificación; el proyecto usa exclusivamente agregados por CCAA.

---

## 5. Viabilidad Inicial

### ✅ Favorable
- Datos 100% disponibles, verificados, descargables sin fricción
- Pipeline EPA del mismo master como referencia directa (misma API INE, mismo esquema JSON)
- Granularidad CCAA suficiente para análisis regional con 17 unidades
- Sin dependencias externas ni costes

### ⚠️ Riesgos identificados
| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Salarios no anualizados al mismo año que IPV | Media | Interpolación lineal o inner join restrictivo |
| IPV base 2015=100 no comparable directamente con salarios | Baja | Índice normalizado sobre año base común |
| Desfase temporal de salarios (encuesta llega a 2024; IPV a 2025) | Media | Último año con ratio parcial o fuente alternativa: Agencia Tributaria IRPF (rendimientos trabajo por CCAA) |

**¿Es desarrollable de forma realista durante el curso?** Sí: el volumen es pequeño (~3.300 filas procesadas, manejable íntegramente en pandas), el pipeline reutiliza el patrón del ejercicio EPA del propio máster (misma API INE, mismo esquema JSON) y el MVP — ETL + notebook de análisis + regresión inicial — se descompone en hitos alcanzables entrega a entrega.

**Parte más arriesgada ahora mismo:** el acoplamiento temporal de las fuentes — los salarios llegan hasta 2024 con ~1,5 años de retraso estructural mientras el IPV ya publica 2025, así que el último año del índice siempre será provisional. Riesgo secundario: la capa de modelado trabaja con pocas observaciones (17 CCAA × ~17 años), lo que limita la complejidad del modelo a regresiones simples — asumido en el diseño del MVP.

### Alternativas de datos
- **Ministerio de Vivienda:** Precios de transacción por m² por provincia (más granular que IPV)
- **Banco de España:** Esfuerzo hipotecario (ratio cuota/renta) — indicador complementario
- **Eurostat:** Comparativa internacional house price index vs salarios (tabla `prc_hpi_a`)
