# Entrega 1 — Ideas de Producto

Esta entrega recoge el proceso completo de ideación del proyecto: las cinco ideas propuestas inicialmente, el feedback del tutor y la convergencia hacia la idea finalmente seleccionada (desarrollada en detalle en [02_datos_necesarios.md](02_datos_necesarios.md)).

---

## 1. Ideas propuestas inicialmente

Se plantearon cinco propuestas orientadas a resolver problemas a gran escala mediante ciencia de datos:

### Idea 1 — Arquitectura de Data Science para una Red Energética Global 24/7
**Problema:** la intermitencia de las energías renovables (el sol no siempre brilla, el viento no siempre sopla) obliga a las redes a recurrir a combustibles fósiles durante las "sequías energéticas".
**Propuesta:** tratar la Tierra como un único sistema eléctrico y construir una capa de software inteligente — Deep Learning para pronósticos de generación y Reinforcement Learning para el enrutamiento dinámico de energía limpia entre zonas horarias — con ahorros estimados de hasta el 46% frente a sistemas aislados.

### Idea 2 — Modelo "Trigo-a-Cebolla": ecosistema IA-Blockchain para cultivos perecederos
**Problema:** los agricultores de perecederos sufren gran volatilidad de precios y pierden hasta el 35% de las cosechas al estar excluidos de los mercados de futuros (no pueden almacenar el producto).
**Propuesta:** un contrato de futuros puramente digital: Transfer Learning (CNN-LSTM) entrenado con décadas de datos de trigo para predecir cosechas de cebolla, combinado con Smart Contracts que garanticen liquidez desde la siembra.

### Idea 3 — Blockchain Fiscal Circular y Auditoría Autónoma
**Problema:** déficit de confianza fiscal por la desconexión entre recaudación y gasto público; sistemas fiscales lentos, opacos y con grandes brechas recaudatorias.
**Propuesta:** motor fiscal bidireccional con Zero-Knowledge Proofs para verificar pagos preservando la privacidad, tokens trazables para que el ciudadano rastree el gasto, y Redes Neuronales de Grafos (GNN) para detección activa de fraude.

### Idea 4 — Extractor de Datos Científicos: liberando la "data oscura"
**Problema:** gran parte de los datos científicos (p. ej. resultados de ensayos clínicos) queda atrapada en documentos no estructurados (PDFs, imágenes) ilegibles para los sistemas informáticos.
**Propuesta:** arquitectura automatizada con LLMs y visión por computador que extraiga, digitalice e interprete gráficos, tablas y entidades clave del texto científico, reduciendo extracciones manuales de meses a minutos.

### Idea 5 — Refactorizando el Estado: hacia una burocracia impulsada por IA
**Problema:** la burocracia gubernamental funciona como "código heredado": alta latencia, coste de hasta el 20% del PIB mundial y baja satisfacción ciudadana.
**Propuesta:** hoja de ruta estratégica a 30 años para sustituir procesos burocráticos por IA, desde automatización simple hasta gobernanza adaptativa, con salvaguardas codificadas (transparencia radical, humano en el bucle, apelaciones garantizadas).

---

## 2. Feedback del tutor

El tutor valoró positivamente la ambición intelectual, la orientación a problemas relevantes y el encaje conceptual con datos, modelado y automatización, pero señaló que la entrega estaba "todavía bastante verde" para el criterio del TFM. Sus indicaciones clave:

> «El siguiente paso es **reducir radicalmente el alcance** para que sea viable en seis meses y **evitar combinar demasiadas tecnologías y capas institucionales**. La línea que hoy veo mejor alineada con los criterios del proyecto es **el extractor de datos científicos, o una versión muy reducida de monitorización/forecasting con datos accesibles**; las demás podrían mantenerse como alternativas solo si evolucionan hacia un problema más acotado, con datos accesibles y una contribución clara de Data Science.»

Criterios extraídos del feedback:
1. Alcance radicalmente reducido — viable en seis meses
2. Una sola línea principal, sin apilar tecnologías (descarta los componentes blockchain)
3. Datos accesibles
4. Contribución clara de Data Science

---

## 3. Convergencia: idea seleccionada

Siguiendo la línea de **monitorización/forecasting con datos accesibles** avalada por el tutor, la idea se concreta en:

### Índice de Asequibilidad de Vivienda Regional en España

**Problema:** el precio de la vivienda en España crece muy por encima de los salarios, con divergencias marcadas entre comunidades autónomas, y no existe una herramienta pública que integre precio de vivienda, salarios e inflación en un único índice de asequibilidad regional actualizable.

**Enfoque:** pipeline ETL sobre la API pública del INE (IPV, salarios e IPC por CCAA) que construye un índice de asequibilidad (ratio precio/salario) por comunidad autónoma para la serie 2007–2025, con análisis exploratorio, visualizaciones comparativas e inicio de modelado predictivo.

**Por qué cumple los criterios del tutor:**
| Criterio | Cumplimiento |
|---|---|
| Alcance viable en 6 meses | 4 tablas estadísticas, ~1.800 series, pipeline Python acotado |
| Una sola línea tecnológica | Python + pandas; sin blockchain ni arquitecturas multicapa |
| Datos accesibles | API INE pública, sin registro ni API key, verificada en vivo |
| Contribución clara de DS | ETL reproducible + índice derivado + EDA + modelo predictivo |

**Alternativa de reserva:** el extractor de datos científicos (Idea 4), segunda línea avalada por el tutor, se mantiene como plan B si la fuente principal fallara — riesgo muy bajo dado el carácter estatutario del INE.

El desarrollo completo de la idea seleccionada (datos necesarios, fuentes, privacidad y viabilidad) se encuentra en la [Entrega 2](02_datos_necesarios.md).
