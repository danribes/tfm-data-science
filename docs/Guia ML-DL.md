# Guía de aplicaciones ML/DL y del tooling con Claude

Dos capas distintas y complementarias:
1. **El ML/DL DENTRO del modelo** — qué técnica se usa en cada módulo, con qué
   resultado, y bajo qué regla se acepta o rechaza.
2. **El tooling con LLM (Claude + motores)** — cómo se usan los grandes modelos
   de lenguaje para HACER y OPERAR el sistema de forma más eficiente, sin que
   nunca sean la fuente de los números.

Principio que separa las dos capas: **el LLM narra; el sistema calcula.** Los
números salen siempre de código y datos con trazabilidad, nunca del texto de un
LLM. Detalle en `MEMORIA.md` §4.6 y `docs/arquitecturas_prediccion.md`.

---

## Parte 1 — El ML/DL dentro del modelo

### Mapa de técnicas por módulo

| Módulo | Técnica ML/DL | Librería | Papel | Veredicto bajo protocolo |
|---|---|---|---|---|
| T1 baseline | Drift (persistencia con deriva) | numpy | **Campeón de producción** | MASE h≤4 = **0,40** |
| T1 candidato | SARIMAX (± exógena Euríbor) | statsmodels | Retador clásico | 1/17 · 0/17 — no adoptado |
| T1 candidato | LightGBM (Gradient Boosting) | lightgbm | Retador flexible | 0/17 (0,666) — no adoptado |
| T1 candidato | LightGBM + capas de demanda | lightgbm | Retador con features | 0/17 (0,653) — no adoptado |
| T1 candidato | **Chronos-Bolt (modelo fundacional)** | chronos (PyTorch) | DL preentrenado zero-shot | 0/17 (0,460) — no adoptado |
| T1 candidato | **DL global (MLP sobre 1.760 series)** | PyTorch | Red entrenada en booms extranjeros | **empate técnico 0,401**, 7/17 — no adoptado |
| A1 salud/edu/bienestar | OLS vs LightGBM vs MLP | sklearn/lightgbm | Frontera gasto→resultado | **OLS gana 5/5** |
| A2 tipologías | PCA + KMeans | sklearn | Composición del gasto | clusters débiles (silueta 0,20) |
| Motor de proyección | Regresión con FE + errores CR1 (cluster) | numpy | Elasticidades demográficas | β65 pensiones 0,91±0,19 |
| Frontera 50 años | Panel within (FE país+año, CR1) | numpy | Efecto ingreso→bienestar | β retardo 8 = −0,0036±0,0015 |
| D1 horizonte | Monte Carlo (4.000 trayectorias) | numpy | Propagar incertidumbre de parámetros | banda 2070 [272–618] |
| Incertidumbre | Intervalos conformal por cuartil | numpy | Bandas con cobertura comprobable | funnel A1, abanico T1 |
| Validación | LOOCV, rolling-origin, test de un solo uso | sklearn/propio | Selección honesta | 5 contests, todos negativos |
| Asistente | TF-IDF + similitud coseno | sklearn | Recuperación del corpus | RAG offline |

### La lección central: el ML/DL potente perdió, y eso es el resultado

Cinco veces un modelo flexible o profundo compitió contra una alternativa
simple bajo reglas fijadas ANTES de mirar. Ninguno se adoptó. El mejor (el DL
global entrenado con ciclos inmobiliarios extranjeros) llegó al empate técnico
(0,401 vs 0,395) y ganó a un solo horizonte — insuficiente para la regla de
12/17 CCAA, que no se relajó. En las fronteras transversales, el OLS ganó las
cinco veces al GBM y al MLP.

**Por qué**: con ~150–200 países o una ventana de validación sin giros de
ciclo, la señal la captura la estructura simple; más capas añaden varianza, no
información. El DL solo mostró valor donde tenía un corpus de DOMINIO grande
(1.760 series extranjeras con crisis reales) — la pista de que el cuello de
botella era el dato, no la arquitectura. Detalle: `docs/dl_rutas.md`.

### Dónde el DL SÍ aporta (declarado, no fingido)

- **Modelos fundacionales** (Chronos): útiles como retador de coste cero;
  se integran en la misma parrilla y se juzgan igual.
- **Corpus de dominio grande** (ruta 1 DL): la única vía con evidencia
  direccional de que puede anticipar un giro; revalidable solo con datos 2026+.
- **La frontera del DL real** (CNN sobre luces nocturnas para PIB sin datos)
  queda declarada como extensión bloqueada por infraestructura, no simulada.

---

## Parte 2 — El tooling con LLM (Claude y motores)

Los LLM NO producen números del modelo. Se usan en tres papeles de eficiencia:

### 2.1 El asistente RAG del proyecto (`app/rag_assistant.py`)

Recuperación aumentada sobre los 37 documentos del propio proyecto.

- **Sin clave** (modo por defecto): devuelve los pasajes citados más relevantes
  (TF-IDF), sin red. Determinista, auditable.
- **`--llm`**: un LLM redacta la respuesta a partir SOLO de esos pasajes, con
  cita por afirmación y reformulación de lo normativo. Motores configurables:

| Motor | Modelo | Endpoint | Nota |
|---|---|---|---|
| `kimi` (defecto) | kimi-k2.6 | api.moonshot.ai | Sin "tasa de razonamiento", rápido |
| `glm` | glm-5.2 | api.z.ai (Coding Plan) | max_tokens≥4000 |
| `mimo` | mimo-v2.5-pro | xiaomimimo | Reasoner |

Uso:
```bash
python3 app/rag_assistant.py "¿Por qué el drift gana a los modelos de ML?"
python3 app/rag_assistant.py --llm --engine kimi "Resume el sistema a 50 años"
```
Regla estricta del prompt: solo números que aparezcan textualmente en los
pasajes; nunca inventa cifras; si la pregunta es normativa, reformula.

### 2.2 Claude como herramienta de proceso (construcción)

Declarado en la memoria (uso de IA): el LLM se usó para escribir código,
redactar documentación y explorar diseño — nunca como fuente de datos ni de
resultados. Cada número del repositorio es reproducible desde `analysis/` sin
ningún LLM en el camino.

### 2.3 Consejo de LLMs para decisiones de diseño (segunda opinión)

Para decisiones de arquitectura (qué módulos, qué códigos de datos, qué
riesgos) se consultó un consejo de varios LLM y se TRIANGULÓ, verificando cada
afirmación contra las fuentes primarias — porque los LLM se equivocan en
códigos y detalles. Ejemplo real: un consejo recomendó códigos COFOG y ESSPROS,
la verificación pilló 5 códigos erróneos antes de usarlos.

---

## Parte 3 — Ejemplos para sacar el máximo al ML/DL con Claude

Cómo un usuario (o el tribunal) exprime la combinación modelo + LLM. Cada
ejemplo respeta la separación: **el sistema calcula, Claude explica/orquesta.**

### Ejemplo 1 — Interrogar un resultado del modelo
> Usuario: *"¿Por qué el modelo profundo perdió contra el drift?"*
- El asistente RAG recupera `dl_rutas.md` y explica los cinco contests con sus
  MASE reales, citados. Claude narra; los 0,401/0,395 vienen del gold.

### Ejemplo 2 — Explorar un escenario y su consecuencia
> Usuario: *"Si los tipos suben al 5 % y no hay consolidación, ¿dónde acaba la deuda?"*
- El motor D1 (`POST /scenario`, `r_mercado=5`) calcula la senda → **275 % en
  2050**. Claude puede envolver la cifra en lenguaje natural, pero el 275 es
  aritmética r−g, no lenguaje.

### Ejemplo 3 — Pedir un contraste ML honesto sobre datos nuevos
> Usuario: *"He añadido una variable nueva. ¿Bate al drift?"*
- Se enchufa como `forecaster(train,h)` en `backtest_t1.py` y corre la misma
  parrilla pre-registrada. El veredicto es 0–17/17, no una opinión del LLM.
- **Sacar el máximo**: usar Claude para escribir el nuevo `forecaster` y los
  tests; usar el HARNESS para juzgarlo. División de trabajo correcta.

### Ejemplo 4 — Ampliar el corpus DL (la vía prometedora)
> Usuario: *"¿Mejoraría el DL con más series regionales?"*
- El hallazgo dice que el cuello de botella es el dato. Claude ayuda a escribir
  el conector (p. ej. más países con historia de crisis) → `hpi_regional_global`
  crece → se reentrena el MLP global → se revalida en 2026+. El sistema decide
  si se adopta, no el LLM.

### Ejemplo 5 — Encadenar predicción condicional (clima→cosecha)
> Usuario: *"Proyecta el bienestar según el crecimiento de la renta."*
- Cadena legítima: crecimiento (palanca) → panel within (γ) → sobre de
  mortalidad con IC95. 2050: crecimiento 1 % → **−12,3 %**. Claude explica la
  cadena; los parámetros y las bandas son del panel.

### Ejemplo 6 — Auditar la honestidad del sistema
> Usuario: *"Enséñame los tres backtests que el modelo suspendió."*
- El sistema los publica (`test_final_t1.md`, contests). Claude los resume; la
  prueba de que son reales es que están en el repo con sus números, no en la
  memoria de un modelo.

---

## Regla de oro para el usuario

Para exprimir ML/DL + Claude sin engañarse:
1. **Deja calcular al sistema** (motor, harness, gold) — ahí están los números.
2. **Deja narrar y orquestar a Claude** (RAG, código, diseño) — ahí está la
   eficiencia.
3. **Nunca aceptes una cifra de un LLM sin su fuente en el gold.** Si el
   asistente no puede citar el pasaje, la cifra no entra.
4. **Todo candidato nuevo pasa por el protocolo**, gánelo un GBM, un MLP o un
   modelo fundacional. La regla no se relaja para lo que está de moda.
