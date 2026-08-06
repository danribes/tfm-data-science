# Design: Consolidated App — Phase 1: Core (data + engine + API)

Status: approved by user 2026-08-06
Author: Claude (session with Daniel Ribes)

## 0. Context & decomposition

The consolidated app merges three prior efforts, and reusing them is now the
explicit goal (this REVERSES the earlier "build independently" constraint of
the MVP spec):

- **Archived MVP** (`archive/mvp-app-v1/`, spec/plan in `docs/superpowers/`):
  country-generic Streamlit explorer, live World Bank/Eurostat/OECD clients
  with a hardened never-raise contract, debt-dynamics engine, fiscal-space
  allocator, ML stress score, Pareto explorer. 67 tests.
- **Plan Predictor / plan_maestro** (`legacy/old` → `evo_final_work_old`):
  working FastAPI (:8010) + Streamlit (:8501) system, raw→processed→gold
  pipeline (27 gold CSVs), Monte Carlo DSA to 2070 (4,000 paths), model
  contests with published losses, conformal fans. Key specs:
  `_old/PLAN_PREDICTOR.md`, `_old/FINAL_PREDICTOR.md` (AC1–AC8),
  `_old/PLAN_ESCENARIOS_CORE.md`.
- **Design lineage v01–v16** (`legacy/design_data` → `evo_final_work_data`):
  `design/v16_perfiles_lab/` is a complete, verified, regenerable single-file
  app — 12 personas, 10 levers, semi-structural JS engine with all constants
  declared, 20/20 anchor checks. `v15` defines the 12 personas; `v14` the
  12-tab IA and design grammar; `v12` the empirically-anchored slider limits
  and red lines.

**The project is decomposed into three phased sub-projects** (user approved
Approach A), each with its own spec → plan → implementation cycle:

1. **Core (THIS SPEC)** — data layer + Python engine + FastAPI. Headless,
   fully testable, freezes the API contract.
2. **Front** — v16-style regenerable self-contained HTML front: 12 Spanish
   persona tabs, levers, presets, red lines, MC fan rendering; client-side JS
   engine mirroring the Python engine via the shared anchor fixture; thin
   English generic-country pages. Separate spec.
3. **Model lab** — ML stress score (after enriching the training panel),
   Pareto explorer, contests/validation page in the FINAL_PREDICTOR AC1–AC8
   spirit. Separate spec.

## 0.1 Locked decisions (user-approved)

| Question | Decision |
|---|---|
| Country scope | Spain-first full experience + thin generic layer for other countries |
| Stack | FastAPI backend + v16-style hand-crafted HTML front (phase 2) |
| Personas | All 12 (v15 set) for Spain; MVP's 3 for generic countries |
| Engine home | Hybrid: client-side JS for instant lever response (phase 2) + server-side Python for heavy compute; both bound to one anchor fixture |
| Data | Curated gold slice (~6 MB) committed in-repo + live-API refresh; the 2.7 GB `legacy/` trees NEVER enter git (`legacy/` is gitignored) |
| Model layers wanted overall | MC debt fan + presets/red lines (phase 1-2), ML stress score + Pareto (phase 3) |
| Language | Spanish for the Spain experience (reuse v15/v16 copy); English for the generic layer; no i18n framework |

## 1. Purpose & scope (phase 1)

Build the Python foundation: data layer, scenario engine, FastAPI service.
No UI. Deliverables:

- `uvicorn api.main:app` serves the full API locally.
- Green pytest suite; API response shapes frozen as phase 2's contract.
- Committed anchor-fixture JSON (`tests/fixtures/engine_anchors.json`) that
  phase 2's JS engine must also satisfy — the dual-engine discipline.

## 2. Repo layout

```
evo_final_work/
  data/
    gold/                 committed curated vintage slice (~6 MB) — see §3
    live/                 live-API clients ported from archive/mvp-app-v1
  engine/
    constants.py          every named constant, single source of truth
    levers.py             Levers dataclass, ranges, presets S0–S7
    spain.py              v16 semi-structural engine port (deviation semantics)
    montecarlo.py         stochastic DSA (4,000 paths, to 2070, percentiles)
    generic.py            MVP chain for non-Spain countries
    redlines.py           v12 red-line definitions + evaluation
  api/
    main.py               FastAPI app, all endpoints
    schemas.py            pydantic response/request models (the frozen contract)
  scripts/
    refresh_vintage.py    re-fetch per manifest → NEW dated vintage dir; never overwrites
  tests/
    fixtures/engine_anchors.json
    (test modules per §7)
  archive/mvp-app-v1/     unchanged (reference + ported-from source)
  legacy/                 gitignored symlinks (read-only source material)
  docs/superpowers/       specs + plans
```

Python 3.12 venv at `.venv` (exists). New dependencies beyond the MVP set:
`fastapi`, `uvicorn`, `httpx` (TestClient transport). `pymoo`/`xgboost` NOT
needed until phase 3.

## 3. Data layer

### 3.1 Committed gold slice (`data/gold/`)

Copied once from `legacy/design_data/data/` (the curated v15/v16 shipping
subset — NOT the 176 MB `legacy/old/storage/` lake):

| File | ~Size | Role |
|---|---|---|
| `kpis_perfiles.json` | 41 KB | 42 KPIs + 21 series with provenance — the persona payload source |
| `gold_escenarios_deuda.csv` | 7 KB | deterministic debt/GDP paths — engine anchor |
| `gold_escenarios_deuda_mc.csv` | 9 KB | MC envelopes p5–p95 to 2070 — MC tolerance anchor |
| `gold_cuota_teorica.csv` | small | theoretical mortgage payment by CCAA — €745 anchor |
| `gold_projections.csv` | 580 KB | population + 65+ dependency to 2070 |
| `gold_ccaa_trimestral.csv` | 226 KB | quarterly CCAA panel (HPI, CPI, wage) |
| `gold_asequibilidad_ccaa.csv` | 51 KB | affordability by CCAA |
| `gold_pobreza_infantil.csv` | small | child poverty series (red line) |
| `gold_bienestar_pais.csv` | 27 KB | welfare panel |
| `gold_fiscal_historico.csv` | 101 KB | fiscal history |
| `manifest.csv` + `provenance_vintage_manifest.csv` | 141 rows | provenance: source, URL, fetch date, bytes |

Vintage: `2026-07-31`, stamped in a `data/gold/VINTAGE` file. The committed
vintage is immutable. `gold_century_fiscal.csv` (2.5 MB) and
`gold_panel_anual.csv` (1.1 MB) are EXCLUDED from phase 1 (no consumer);
phase 3 may add them if contests need them.

### 3.2 Refresh (`scripts/refresh_vintage.py`)

Re-fetches sources listed in the manifest and writes a NEW directory
`data/vintages/<YYYY-MM-DD>/` (gitignored). Never overwrites `data/gold/`.
Promotion of a new vintage into `data/gold/` is a manual, reviewed act.
Network failures per source are recorded in the new vintage's manifest, never
fabricated.

### 3.3 Live layer (`data/live/`)

Port from `archive/mvp-app-v1/data/` unchanged in behavior: `models.py`
(`FetchResult`), `cache.py` (`DiskCache`), `worldbank_client.py`,
`eurostat_client.py`, `oecd_client.py`, `panel_builder.py` (source-priority
routing + fallback + coverage score), `country_list.py`,
`indicator_catalog.yaml` (19 indicators). Contract retained verbatim: clients
NEVER raise; failures return `FetchResult` with `error`; missing data is
explicit N/A, never fabricated or silently interpolated; cache-first with
`data_cache/` gitignored. Their existing tests port with them.

## 4. Engine

### 4.1 Spain engine (`engine/spain.py`) — v16 port, deviation semantics

The baseline freezes the vintage; the engine computes DEVIATIONS from it.
The baseline is not a prediction, and every output carries the baseline
alongside the scenario (phase 2 draws the dotted base line).

**Levers** (symbol, base at vintage, range — from v16/`PLAN_ESCENARIOS_CORE`
§2.1):

| Lever | Symbol | Base | Range |
|---|---|---|---|
| Interest rate (Euríbor 12m) | r | 2.80 % | 0–6 |
| Risk premium (ES–DE spread, bp) | σ | 45 | 0–400 |
| Primary balance delta (pp GDP) | sp | 0.0 | −4…+4 |
| Productivity (%/yr) | λ | 0.9 | −0.5…+2.5 |
| Import/energy prices (% yoy) | pᵐ | 0 | −50…+100 |
| Tax wedge (pp) | τ | 0.0 | −5…+5 |
| Labour institutions (index) | z | 0.0 | −2…+2 |
| External demand (% yoy) | Y* | 1.8 | −4…+6 |
| Demographic pressure (×) | β₆₅ | 0.0 | −1…+1 |
| Indexation (pp vs CPI) | ι | 0.0 | −1.5…+1.0 |

**Presets S0–S7**: base, rates +200 bp, oil +50 %, consolidation,
productivity, labour deregulation, ageing, adverse — lever bundles copied
from v16's `const PRESETS`.

**Constants** (in `engine/constants.py`, exported by the API, shown in the
phase-2 rail): multiplier 1.40 · persistence 0.62 · rate elasticity 0.45 ·
Okun 0.48 · Phillips κ 0.22 · import pass-through 0.045 · inertia θ 0.55 ·
wage-setting φ 0.30 · debt refinancing share 14 %/yr · term premium 0.17 pp ·
mortgage spread 1.4757 pp. Each carries a provenance label (v16 calibration,
"calibrated default, not estimated"; AC-V6's promise — replace with contest
estimates when available — belongs to phase 3).

**Chain** (per v16): levers → GDP level deviation → Okun → unemployment →
Phillips → CPI → wage-setting → wages → debt identity
`bₜ = bₜ₋₁(1+i)/(1+g) − sp` → per-persona dependents.

**Per-persona dependents**: the 12 v15 personas' headline series (bond yield
& payment probability proxy, mortgage rate & French payment, housing effort,
firm-cycle indicator, civil-servant real wage, politician red-line distances,
transparency mirror, child poverty, pension real value & dependency, youth
unemployment, permanent-employee real wage, self-employed cash/quota) —
computed exactly as v16's JS does, translated to Python. The engine exposes
`persona_dependents(scenario) -> dict[str, dict]` keyed by the 12 persona ids.

### 4.2 Anchors — the non-negotiable acceptance battery

Ported from v16's verified checks; failure of any is a build failure:

- **A1**: with all levers at base, the debt identity reproduces
  `gold_escenarios_deuda.csv`'s central scenario at 2026, 2030, 2035, 2050
  **to the decimal** (v16 AC-V3).
- **A2**: French amortization at Euríbor 2.80 % + spread 1.4757 pp reproduces
  the €745/month of `gold_cuota_teorica.csv` (±€1).
- **A3**: no lever is inert — each lever moved alone from base changes at
  least one output series (v16 battery).
- **A4**: all 8 presets produce finite paths (no NaN/inf).
- **A5**: MC envelopes (§4.3) match `gold_escenarios_deuda_mc.csv` p5/p50/p95
  at 2030/2050/2070 within ±2 pp of debt/GDP.
- The computed anchor values are written to
  `tests/fixtures/engine_anchors.json` by a committed generator script and
  the file is committed — phase 2's JS engine tests read THIS file.

### 4.3 Monte Carlo DSA (`engine/montecarlo.py`)

plan_maestro-style stochastic DSA: shocks on r, g, sp (normal, calibrated to
reproduce the gold MC envelopes), 4,000 paths, horizon to 2070, returns
p5/p25/p50/p75/p95 per year. Seeded RNG parameter for reproducibility; the
anchor test uses a fixed seed. Pure NumPy; target < 1 s per run.

### 4.4 Generic engine (`engine/generic.py`)

The MVP chain reused with its tests: `debt_dynamics`, `satellite`
(Okun 0.5 / Phillips 0.3 — generic calibration, DISTINCT from Spain's 0.48 /
0.22 and labeled as such), `fiscal_space`, `scenario` orchestrator including
`defaults_used` / `baseline_years` honesty fields. Calibrated per country
from the live panel.

### 4.5 Red lines (`engine/redlines.py`)

v12's empirically-anchored thresholds as data + evaluator: 10Y yield 7.0 %
(rescue zone — GRC/PRT/IRL precedent, ES 7.6 % Jul-2012), unemployment
26.9 % (Q1-2013 record), deficit −3 % (Maastricht) and −11.3 % (2009 floor),
debt/GDP 105/120, inflation 10 %, housing effort 40 % (Eurostat overburden),
child poverty 30 %. Each with source label. Evaluator returns per-scenario
status: crossed / near (within 10 % of threshold) / safe, computed — never
hand-written (v16 "semáforo vivo" rule).

## 5. API (`api/main.py`)

All response shapes defined in `api/schemas.py` (pydantic) — this is the
frozen phase-2 contract. Endpoints:

| Endpoint | Returns |
|---|---|
| `GET /health` | `{status, vintage, engine_version}` |
| `GET /vintage` | vintage id + per-file provenance summary from the manifest |
| `GET /constants` | every engine constant with value + provenance label |
| `GET /personas` | the 12 Spain persona payloads: id, name, central question (Spanish, verbatim v15), KPIs + historical series from `kpis_perfiles.json` |
| `GET /presets` | S0–S7 lever bundles with Spanish labels |
| `GET /redlines` | red-line definitions with anchors + sources |
| `POST /scenario` | body: 10 levers + horizon → baseline paths, scenario paths (GDP dev, unemployment, CPI, wages, debt), per-persona dependents, red-line statuses, deltas vs base |
| `POST /scenario/montecarlo` | body: levers + seed? → fan percentiles per year to 2070 |
| `GET /countries` | generic layer: selectable countries (live country list) |
| `GET /panel/{iso3}` | live panel + coverage score + per-indicator availability |
| `POST /scenario/generic/{iso3}` | MVP-style scenario for a non-Spain country (its lever set), incl. `defaults_used`/`baseline_years` |

Conventions: lever values validated against §4.1 ranges (422 with a clear
message outside range); CORS allows localhost + file:// null origin;
responses carry `vintage` and `computed_not_advice: true` (the no-
recommendation rule is a data-level flag phase 2 must render).

## 6. Error handling

- No endpoint returns 500 for missing data: unavailable fields are explicit
  (`null` + `availability` maps), inherited from the MVP contract.
- Live-fetch failure → disk-cache fallback (with `from_cache` + fetch date)
  → declared error field; only the affected fields degrade.
- Committed vintage files are read-only at runtime; refresh writes elsewhere.
- MC endpoint bounds: paths capped at 4,000, horizon at 2070 — validated.

## 7. Testing

| Test module | Covers |
|---|---|
| `tests/test_anchors.py` | A1–A5 battery (§4.2), decimal-exact where v16 was |
| `tests/test_engine_spain.py` | lever monotonicities/signs, deviation semantics (base levers → zero deviation), persona dependents present for all 12 ids |
| `tests/test_montecarlo.py` | seeded reproducibility, percentile ordering (p5≤p50≤p95), envelope tolerance |
| `tests/test_redlines.py` | crossed/near/safe evaluation against known scenarios |
| `tests/test_api.py` | TestClient: every endpoint, response-shape snapshots (the frozen contract), range validation 422s |
| `tests/test_data_layer.py` | ported MVP client tests (mocked HTTP) + gold-slice load/shape checks |
| `tests/test_generic_engine.py` | ported MVP engine tests |

No network in tests (gold slice + mocks). Manual smoke: `uvicorn api.main:app`,
`curl /health`, `curl -X POST /scenario` with S7 (adverse) and confirm
red-line crossings appear.

## 8. Out of scope (phase 1)

- Any HTML/UI and the JS engine (phase 2 spec).
- ML stress score, Pareto explorer, contests/validation page (phase 3 spec);
  `xgboost`/`pymoo` deps not installed.
- Docker/compose, deployment.
- CCAA-level microsimulation beyond what the gold slice already carries
  (blocks F/G of FINAL_PREDICTOR remain future work).
- Conformal fans / model contests (phase 3; MC fan here is the v16-style
  stochastic identity, not a forecasting claim).
- Any modification to `legacy/` or `archive/` content.
