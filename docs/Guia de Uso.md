# Guía de uso — dashboard, escenarios y capacidad de predicción

Cómo se usa la interfaz del proyecto y qué devuelve el modelo cuando el usuario
plantea escenarios. Todos los números de esta guía son salidas REALES del
sistema (capa gold + motor D1), no ilustrativos.

**Demo pública:** https://tfm-data-science-ufgfhpcvydyrswwzm7t6sz.streamlit.app/
**Local:** `docker compose up --build` → dashboard en `localhost:8501`, API en `localhost:8010`.

## Principio que gobierna la interfaz

El sistema **no adivina el futuro incierto: lo pone como palanca del usuario**.
Donde una variable es imprevisible (salarios, tipos, crecimiento), no se
pronostica — se pregunta "¿y SI vale X?" y se devuelve la consecuencia
calculada. Donde una variable es predecible (demografía), sí se proyecta. Cada
respuesta lleva su banda de incertidumbre y su límite de método. Detalle
conceptual en `docs/arquitecturas_prediccion.md`.

---

## Las cinco pestañas

### 🏠 1. Asequibilidad CCAA — pronóstico con escenarios salariales
- **Controles**: territorio (17 CCAA + Nacional) · escenario salarial (0 %, 2 %, 4 %).
- **Devuelve**: el IPV histórico + el abanico empírico 2026–2027 (bandas 80/95 %)
  y el ratio de asequibilidad proyectado bajo el crecimiento salarial elegido.
- **Cómo leerlo**: el salario mueve el RATIO (esfuerzo), no el precio. La banda,
  no el punto, es la parte informativa.

### 🗺️ 2. Atlas fiscal
- **Control**: selector de figura (B1–B19).
- **Devuelve**: España frente a la mediana mundial/UE en gasto, deuda, sanidad,
  pensiones, vivienda pública vs residencial total, suelo, historia 1703–2025.

### ⚕️ 3. Rendimiento A1
- **Devuelve**: funnel de 164 países (residual de esperanza de vida ~ gasto
  sanitario) con banda conformal por cuartil de renta. **No es un ranking**:
  solo importan los países fuera de su banda.

### 📉 4. Deuda: escenarios D1 — el simulador interactivo
- **Palancas (sliders)**: tipo de mercado (2–6 %) · crecimiento real (0–3 %) ·
  ajuste del saldo primario (−2 a +4 pp) · presión demográfica on/off.
- **Devuelve**: "TU SENDA" de deuda 2024–2050 sobre el menú de escenarios base.

### 🔭 5. Horizonte 50 años
- **Controles**: escenario de deuda (Monte Carlo) · horizonte de bienestar (2050/2070).
- **Devuelve**: el abanico probabilístico de deuda a 2070 (bandas 50/90 %) y los
  sobres de mortalidad infantil según crecimiento, con la calibración histórica
  (~13 pp) al pie.

---

## Ejemplos de preguntas y la respuesta del modelo

Cada bloque = una pregunta en lenguaje natural, el escenario que fija el usuario,
y la estimación REAL que devuelve el sistema.

### A. Asequibilidad de la vivienda (pestaña 1)

> **"¿Cómo evoluciona la asequibilidad nacional hasta 2027 según lo que suban los salarios?"**

| Escenario del usuario | Ratio de asequibilidad 2027Q4 (2024 = 1,26) |
|---|---|
| Salarios +0 %/año | **1,77** |
| Salarios +2 %/año (central) | **1,64** |
| Salarios +4 %/año | **1,53** |

Lectura del modelo: aun con salarios subiendo un 4 %, el ratio empeora respecto
a 2024 — la asequibilidad no se corrige sola por la vía salarial. (Indicador
aproximado de evolución relativa; el modelo de producción es el drift, ganador
del protocolo completo.)

### B. Sostenibilidad de la deuda a 2050 (pestaña 4 / `POST /scenario`)

> **"¿Dónde acaba la deuda pública en 2050 según la política que se elija?"**

| Palancas del usuario | Deuda 2050 (% PIB) |
|---|---|
| Por defecto (tipo 3,5 · crec. 1,3 · sin ajuste) | **224** |
| Consolidación +2,5 pp de saldo primario | **156** |
| Crecimiento real 2,5 % | **184** |
| Tipos al 5 % | **275** |
| Sin presión demográfica (contrafactual) | **127** |

Lectura del modelo: **la demografía domina cualquier palanca individual**
(224 con envejecimiento vs 127 sin él = 97 pp); ninguna palanca aislada
estabiliza la senda. Determinista, sin retroalimentaciones: mapa de
sensibilidades, no pronóstico.

### C. Deuda a largo plazo con incertidumbre (pestaña 5, Monte Carlo)

> **"¿Y si miramos a 2070, con la incertidumbre de los parámetros?"**

| Escenario | 2050 mediana [banda 90 %] | 2070 mediana [banda 90 %] |
|---|---|---|
| Central | 231 [178–302] | **409 [272–618]** |
| Consolidación +2,5 pp | 172 [121–235] | 298 [174–482] |
| Crecimiento alto | 196 [150–256] | 321 [214–481] |
| Tipos altos | 264 [203–344] | 518 [345–784] |

Lectura del modelo: el ancho de la banda ES el mensaje. Condicional a
continuidad institucional; la calibración histórica dice que ningún sobre a
50 años puede ser más estrecho de ~13 pp de PIB.

### D. Bienestar social a 50 años (pestaña 5, sobres)

> **"¿Cuánto bajaría la mortalidad infantil según el crecimiento de la renta?"**

| Crecimiento (renta pc/año) | Δ mortalidad <5 en 2050 | en 2070 |
|---|---|---|
| Estancamiento 0,5 % | −6,4 % [−7,8, −5,0] | −11,0 % |
| Central 1,0 % | −12,3 % [−14,9, −9,7] | −20,8 % |
| Dinámico 1,5 % | −17,9 % [−21,5, −14,2] | −29,4 % |

Lectura del modelo: **el crecimiento de la renta domina**; subir la capacidad
fiscal ±2,5 pp añade solo ±0,8 % (efecto estructural real, a 8 años de retardo,
pero de segundo orden). Variación relativa a la senda base — la mejora secular
mundial no se extrapola.

### E. Preguntas normativas — el sistema reformula, no prescribe

> **"¿Qué habría que recortar para bajar la presión fiscal al 10 %?"**

El sistema no responde "recorta X". Devuelve la magnitud: un Estado del 10 %
de ingresos implica recortar ~el 78 % del gasto actual (35 pp de PIB); ni
eliminando TODO el Estado del bienestar (29 pp) se llega. Contexto histórico:
España tuvo ese "Estado del 10 %" en 1900. La elección es política; el sistema
pone el precio (ver stress test, `docs/stress_test_qa.md`).

---

## Usar el motor por API (para reproducir los números)

El simulador de deuda es un endpoint. Palancas en el cuerpo JSON:

```bash
curl -X POST localhost:8010/scenario -H "Content-Type: application/json" -d '{
  "r_mercado": 3.5,      # tipo de mercado %
  "g_real": 1.3,         # crecimiento real %
  "pb_palanca_pp": 2.5,  # ajuste permanente del saldo primario, pp
  "con_demografia": true,
  "hasta": 2050
}'
```

Devuelve la senda año a año (`deuda`, `pb`, `r_efectivo`) con la nota "mapa de
sensibilidades, no pronóstico". Otros endpoints:
`/forecast/ccaa/{territorio}` (abanico), `/performance/health` (funnel A1),
`/scenarios/debt` (menú), `/project/{pensions|health}` (elasticidades).

## Preguntar en lenguaje natural — el asistente RAG

```bash
python3 app/rag_assistant.py "¿Qué pasa con la deuda si los tipos suben al 5%?"
```

Responde con pasajes citados de la documentación del proyecto (36 documentos).
Con `--llm --engine kimi` redacta la respuesta a partir SOLO de esos pasajes,
con cita por afirmación; sin clave, devuelve los pasajes tal cual.

---

## Qué NO hace el sistema (y por qué es una virtud)

- **No da un número puntual del futuro incierto**: da sobres condicionales al
  escenario que fija el usuario.
- **No prescribe políticas**: pone precio a cada opción y devuelve la elección.
- **No oculta su incertidumbre ni sus límites**: cada respuesta lleva su banda
  y su advertencia de método. El sistema dice lo que no sabe con la misma
  claridad que lo que sabe. *El LLM narra; el sistema calcula.*
