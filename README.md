# España en escenarios

**¿Qué recibe un país —y cada comunidad autónoma— a cambio del dinero público que gasta?**

Herramienta abierta construida sobre datos oficiales: reúne un siglo de cuentas
públicas, proyecta cómo evolucionan la deuda y la vivienda, y deja probar
escenarios («¿y si los tipos suben 200 pb?») con su margen de error explícito.

TFM de Data Science · motor `1.0.0` · vintage de datos **2026-07-31**

---

## La idea

Casi todo el debate público sobre gasto, deuda y vivienda se hace con cifras
sueltas y sin margen de error. Este proyecto hace lo contrario: fija un corte de
datos oficiales (*vintage*), lo congela, y sobre él monta un motor macro
transparente donde cualquiera puede mover diez palancas y ver —con bandas de
incertidumbre y umbrales históricos— qué le pasa a la deuda, al paro, a la
inflación y al esfuerzo de compra de vivienda.

Tres reglas que atraviesan todo el repositorio:

1. **Nada se escribe a mano.** Los semáforos, los estados de las líneas rojas y
   los titulares se *calculan* desde el escenario. No hay estados cosidos.
2. **Todo dato lleva su fecha y su fuente.** El vintage está sellado en
   `data/gold/VINTAGE` y cada descarga queda registrada en los manifiestos de
   procedencia.
3. **Los dos motores tienen que coincidir.** El motor Python y su port a
   TypeScript están atados por un fixture de anclas: si divergen, los tests
   fallan.

## Arquitectura

```
data/gold/  ──►  engine/  ──►  api/  ──►  frontend/
 (vintage      (motor macro   (FastAPI)   (React + Vite + TS)
  congelado)    determinista                    │
                + Monte Carlo)                  └── frontend/src/engine/
                                                    (port TS del motor)
```

- **`data/`** — la *gold slice*: CSV y JSON derivados de fuentes oficiales, más
  la capa `data/live/` que consulta World Bank y Eurostat para el modo
  multi-país.
- **`engine/`** — el motor. `spain.py` (escenario determinista de España),
  `montecarlo.py` (bandas de incertidumbre), `redlines.py` (umbrales históricos
  evaluados), `levers.py` (palancas y presets), `generic.py` (motor genérico
  para cualquier país), `constants.py` (única fuente de verdad de constantes).
- **`api/`** — FastAPI. Expone el motor sin lógica propia: valida, llama, serializa.
- **`frontend/`** — el panel. React 19 + Vite + Recharts + Zustand, en español.

### El contrato de doble motor

`frontend/src/engine/` es un port línea a línea de `engine/spain.py`. Existe para
que mover una palanca en el navegador sea instantáneo, sin ida y vuelta al
servidor. El riesgo obvio es que los dos motores se separen con el tiempo, así
que están atados por un contrato ejecutable:

`tests/fixtures/engine_anchors.json` guarda los valores que fijó el motor
Python: la línea base, los ocho presets `S0`–`S7` y una sonda con las diez
palancas movidas a la vez. Ambos lados lo leen —`tests/test_anchors.py` en
Python, `src/engine/__tests__/anchors.test.ts` en TypeScript— y comprueban que
reproducen los mismos números dentro de tolerancia.

Tras cambiar el motor o el vintage, hay que regenerarlo:

```bash
.venv/bin/python scripts/generate_anchor_fixture.py
```

## Arranque rápido

Requisitos: **Python 3.12+** y **Node 20+** (desarrollado con 3.12 y Node 22).

### 1. La API

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn api.main:app --reload --port 8000
```

Documentación interactiva en `http://localhost:8000/docs`.

### 2. El panel

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173
```

`VITE_API_BASE` cambia la URL de la API (por defecto `http://localhost:8000`).

Para verlo **sin levantar la API**, el build simulado intercepta la red con MSW
en el propio navegador:

```bash
npm run build:mock && npm run preview
```

## La API

| Método | Ruta | Qué devuelve |
|---|---|---|
| `GET` | `/health` | estado y versión del motor |
| `GET` | `/vintage` | fecha del corte de datos y su procedencia |
| `GET` | `/constants` | todas las constantes calibradas del motor |
| `GET` | `/personas` | catálogo de perfiles |
| `GET` | `/presets` | escenarios predefinidos `S0`–`S7` |
| `GET` | `/redlines` | definiciones de las líneas rojas y sus anclas |
| `POST` | `/scenario` | escenario determinista 2026–2050 dadas 10 palancas |
| `POST` | `/scenario/montecarlo` | mismo escenario con bandas p5–p95 |
| `GET` | `/countries` | países disponibles en el motor genérico |
| `GET` | `/panel/{iso3}` | panel de indicadores de un país |
| `POST` | `/scenario/generic/{iso3}` | escenario genérico para ese país |

Las palancas fuera de rango devuelven `422` con el detalle de qué se salió y de
qué envolvente.

## El motor

### Las diez palancas

| Símbolo | Palanca | Unidad | Rango |
|---|---|---|---|
| `r` | Tipo de interés · Euríbor 12m | % | 0 – 6 |
| `σ` | Prima de riesgo · spread ES–DE | pb | 0 – 400 |
| `sp` | Saldo primario · Δ vs central | pp PIB | −4 – 4 |
| `λ` | Productividad | %/año | −0,5 – 2,5 |
| `pᵐ` | Precio importaciones/energía | % a/a | −50 – 100 |
| `τ` | Presión fiscal · cuña laboral | pp | −5 – 5 |
| `z` | Instituciones laborales | índice | −2 – 2 |
| `Y*` | Demanda externa | % a/a | −4 – 6 |
| `β₆₅` | Presión demográfica | × | −1 – 1 |
| `ι` | Indexación pensiones/nóminas | IPC+pp | −1,5 – 1 |

Los rangos no son decorativos: son las envolventes empíricas de lo que esas
variables han hecho históricamente.

### Los ocho presets

`S0` base · `S1` tipos +200 pb · `S2` petróleo +50 % · `S3` consolidación ·
`S4` productividad · `S5` desregulación laboral · `S6` envejecimiento ·
`S7` adverso (tipos + petróleo + prima a la vez).

### Las nueve líneas rojas

Umbrales anclados a episodios reales, no a intuiciones. Cada uno cita su origen:

| Línea | Ancla |
|---|---|
| Bono 10A > 7 % | zona de rescate: GRC/PRT/IRL pidieron rescate ahí; ES tocó 7,6 % en jul-2012 |
| Paro > 26,9 % | máximo histórico de España (T1-2013) |
| Déficit > 3 % PIB | umbral de Maastricht |
| Déficit > 11,3 % PIB | suelo de 2009 |
| Deuda > 105 % PIB | nivel de partida actual |
| Deuda > 120 % PIB | ≈ pico COVID 2020 (119,3) |
| Inflación > 10 % | pico de julio 2022 (10,8 %) |
| Esfuerzo vivienda > 40 % | definición Eurostat de sobrecarga |
| Pobreza infantil > 30 % | picos post-2013; media UE ≈19 % |

El estado (`crossed` / `near` / `safe`) se **calcula** desde el escenario en cada
año. `near` es el 10 % del umbral.

### Monte Carlo

4.000 trayectorias, 2026–2070, choques AR(1) con persistencia 0,96 sobre tipo,
crecimiento y saldo primario. Semilla fija (42) para que los resultados sean
reproducibles. El panel dibuja la banda p5–p95 como abanico: la anchura es el
mensaje, no la mediana.

## Los perfiles

La misma economía cambia de significado según quién la mire. El motor define
doce perfiles y el panel tiene publicados cuatro:

**💼 Bonista** · **🏦 Banca** · **🔑 Comprador de vivienda** · **🗳️ Político**

Cada uno trae sus propias cadenas causales (de qué palanca a qué consecuencia),
su narrativa generada desde los números del escenario, y sus líneas rojas
relevantes. Los perfiles pendientes —emprendedor, funcionario, infancia,
jubilado, joven, autónomo y otros— sólo necesitan configuración: el renderizador
ya es genérico.

## Datos y procedencia

El vintage `2026-07-31` está congelado en `data/gold/`:

| Archivo | Contenido |
|---|---|
| `gold_fiscal_historico.csv` | serie larga de cuentas públicas |
| `gold_projections.csv` | proyecciones demográficas por variante |
| `gold_escenarios_deuda.csv` | sendas de deuda (central y alternativas) |
| `gold_escenarios_deuda_mc.csv` | trayectorias Monte Carlo |
| `gold_ccaa_trimestral.csv` | panel trimestral por comunidad autónoma |
| `gold_asequibilidad_ccaa.csv` | asequibilidad de vivienda por CCAA |
| `gold_cuota_teorica.csv` | cuota hipotecaria teórica |
| `gold_bienestar_pais.csv` | indicadores de bienestar |
| `gold_pobreza_infantil.csv` | pobreza infantil |
| `kpis_perfiles.json` | KPIs y series por perfil |

Fuentes: **Eurostat**, **INE**, **BCE**, **World Bank**, **OECD**, **Penn World
Table** y **WEO**. Cada descarga —URL exacta, fecha, tamaño— queda en
`manifest.csv` y `provenance_vintage_manifest.csv`. Para refrescar a un vintage
nuevo sin tocar el actual:

```bash
.venv/bin/python scripts/refresh_vintage.py
```

## Tests

```bash
.venv/bin/pytest                 # 113 tests: motor, API, datos, anclas, MC, líneas rojas
cd frontend && npm test          # Vitest: paridad de motores, store/URL, componentes, rutas
cd frontend && npm run e2e       # Playwright smoke sobre un preview con API simulada
```

Todo corre offline. La primera vez en una máquina nueva, Playwright necesita su
navegador: `npx playwright install chromium`.

## Estructura

```
engine/      motor macro (Python) — constantes, palancas, escenario, MC, líneas rojas
api/         FastAPI: 11 endpoints sobre el motor
data/gold/   vintage congelado + manifiestos de procedencia
data/live/   clientes World Bank / Eurostat para el modo multi-país
frontend/    panel React + Vite + TS (incluye el port TS del motor)
tests/       suite Python + fixture de anclas compartido con el frontend
scripts/     regeneración de vintage y de anclas
docs/        especificaciones de diseño y planes de implementación
archive/     MVP anterior, conservado como referencia
```

## Limitaciones conocidas

Se declaran en la propia pestaña **Metodología** del panel, no sólo aquí:

- Las constantes del motor son **calibraciones, no estimaciones**. Vienen de la
  literatura y de la calibración v16; no se han estimado sobre estos datos.
- La **mora bancaria** (NPL, Banco de España) todavía no está conectada: el
  riesgo de crédito del perfil 🏦 se lee por proxy (paro más colateral).
- Ocho de los doce perfiles están pendientes de configuración.
- El escenario determinista llega a 2050; sólo el Monte Carlo se extiende a 2070.

## Licencia

Trabajo académico (TFM). Los datos proceden de fuentes públicas oficiales y
conservan las condiciones de uso de cada organismo emisor.
