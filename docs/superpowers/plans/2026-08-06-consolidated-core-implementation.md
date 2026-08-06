# Consolidated App — Phase 1 Core (data + engine + API) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the headless Python foundation of the consolidated app — committed gold data slice, live API clients, the v16 Spain engine port with its A1–A5 anchor battery, Monte Carlo DSA, red lines, and the FastAPI service whose response shapes freeze the phase-2 contract.

**Architecture:** Three layers: (1) a data layer with an immutable committed gold vintage (`data/gold/`, vintage `2026-07-31`) plus live never-raise API clients ported from the archived MVP (`data/live/`); (2) an engine layer where `engine/spain.py` is a faithful Python port of the v16 JS semi-structural engine (deviation semantics: baseline = frozen vintage; all levers at base → outputs equal baseline), alongside a seeded NumPy Monte Carlo DSA calibrated to the inherited gold fan, the generic MVP chain, and v12 red lines; (3) a FastAPI app whose pydantic schemas are the frozen phase-2 contract. A committed anchor fixture (`tests/fixtures/engine_anchors.json`) binds phase 2's JS engine to the same numbers.

**Tech Stack:** Python 3.12 (venv at `.venv`, exists — do not recreate), FastAPI + uvicorn + httpx (new), requests/pandas/numpy/pyyaml/pytest (already installed), pytest with no network.

## Global Constraints

- Spec of record: `docs/superpowers/specs/2026-08-06-consolidated-core-design.md`. Its §2 layout, §4.1 lever/constant tables, §4.2 anchors, §5 endpoint table and §7 test-module table are binding.
- Verbatim source of all v16 numbers/copy: `docs/superpowers/plans/references/v16-engine-extract.md` (cited below as "extract L<n>").
- Python 3.12 venv at `.venv` exists; install new deps into it, never recreate it.
- New dependencies: `fastapi`, `uvicorn`, `httpx` only (plus the ported clients' existing needs: `requests`, `pandas`, `numpy`, `pyyaml`, `pytest`). NO `pymoo`, NO `xgboost`, NO `scikit-learn`, NO `streamlit` in phase 1.
- `legacy/` and `archive/` are read-only source material — never modified. `legacy/` stays gitignored.
- `data/gold/` is the immutable committed vintage `2026-07-31`; refresh writes only `data/vintages/<YYYY-MM-DD>/` (gitignored).
- No network in tests: gold slice + mocks/monkeypatch only.
- Language: code, comments and API field names in English; persona names, central questions, lever names and preset labels in Spanish, verbatim from the extract.
- Every API response carries `vintage` and `computed_not_advice: true`.
- Engine deviation semantics: with all levers at base, every output series equals the baseline (zero deviation).
- Anchor battery A1–A5 (`tests/test_anchors.py`) — failure of any anchor is a build failure.
- Lever ranges (spec §4.1, binding): r 0–6, prima 0–400, sp −4…+4, lam −0.5…+2.5, pm −50…+100, tau −5…+5, z −2…+2, ext −4…+6, dem −1…+1, idx −1.5…+1.0.
- Run tests as `.venv/bin/python -m pytest <path> -v` from the repo root.
- Commit after each task with a conventional message; never commit `data_cache/` or `data/vintages/`.

## File Structure

```
data/
  __init__.py
  gold/                      # Task 1 — committed vintage slice (9 CSVs + kpis_perfiles.json + 2 manifests + VINTAGE)
  live/                      # Task 2 — ported MVP clients
    __init__.py models.py cache.py worldbank_client.py eurostat_client.py
    oecd_client.py panel_builder.py country_list.py indicator_catalog.yaml
engine/
  __init__.py
  constants.py               # Task 4 — every named constant + gold loaders (V0, BASE_LEVERS, central, olddep)
  levers.py                  # Task 5 — Levers dataclass, LEVER_SPECS, PRESETS
  spain.py                   # Task 6 — v16 chain + debt identity; Task 7 — PERSONAS + persona_dependents
  montecarlo.py              # Task 8 — stochastic DSA to 2070
  generic.py                 # Task 3 — MVP chain (single module per spec §2)
  redlines.py                # Task 9 — red-line definitions + evaluator
api/
  __init__.py
  schemas.py                 # Task 11 — pydantic contract (all endpoints)
  main.py                    # Tasks 11–13 — FastAPI app
scripts/
  __init__.py
  generate_anchor_fixture.py # Task 10 — writes tests/fixtures/engine_anchors.json
  refresh_vintage.py         # Task 14 — new dated vintage dir, never touches data/gold
tests/
  __init__.py
  fixtures/sample_country_panel.json   # Task 3 (copied from archive)
  fixtures/engine_anchors.json         # Task 10 (generated + committed)
  test_data_layer.py         # Tasks 1, 2, 14
  test_generic_engine.py     # Task 3
  test_engine_spain.py       # Tasks 4, 5, 6, 7
  test_montecarlo.py         # Task 8
  test_redlines.py           # Task 9
  test_anchors.py            # Task 10
  test_api.py                # Tasks 11, 12, 13
requirements.txt             # Task 1
```

Numbers pinned in tests below were computed while drafting this plan by executing the verbatim v16 semantics (extract S1, L95–175) against the real gold CSVs with `.venv`'s Python, and the Monte Carlo calibration was fitted and verified the same way (seed 42, 4000 paths → max deviation 1.399 pp vs the gold envelopes). Each pinned block cites its extract lines.

---

### Task 1: Scaffolding, dependencies, gold slice

**Files:**
- Create: `requirements.txt`, `data/__init__.py`, `data/live/__init__.py`, `engine/__init__.py`, `api/__init__.py`, `scripts/__init__.py`, `tests/__init__.py`, `tests/fixtures/` (dir), `data/gold/VINTAGE`
- Create: `data/gold/*` (copied from `legacy/design_data/data/`)
- Modify: `.gitignore`
- Test: `tests/test_data_layer.py` (gold-slice section)

**Interfaces:**
- Consumes: `legacy/design_data/data/` (read-only source), `.venv` (exists)
- Produces: importable empty packages `data`, `data.live`, `engine`, `api`, `scripts`, `tests`; committed `data/gold/` slice used by every later task; `requirements.txt` installed into `.venv`.

- [ ] **Step 1: Write the failing gold-slice tests**

Create `tests/test_data_layer.py`:

```python
"""Data-layer tests: gold-slice shape checks (Task 1), ported MVP client tests
(Task 2, appended below), refresh_vintage (Task 14, appended below)."""
import csv
import json
from pathlib import Path

GOLD = Path(__file__).resolve().parents[1] / "data" / "gold"

GOLD_FILES = [
    "gold_escenarios_deuda.csv", "gold_escenarios_deuda_mc.csv",
    "gold_cuota_teorica.csv", "gold_projections.csv", "gold_ccaa_trimestral.csv",
    "gold_asequibilidad_ccaa.csv", "gold_pobreza_infantil.csv",
    "gold_bienestar_pais.csv", "gold_fiscal_historico.csv",
    "kpis_perfiles.json", "manifest.csv", "provenance_vintage_manifest.csv",
    "VINTAGE",
]


def test_gold_slice_files_committed():
    for name in GOLD_FILES:
        assert (GOLD / name).exists(), f"missing {name}"
    # excluded from phase 1 (spec §3.1): no consumer yet
    assert not (GOLD / "gold_century_fiscal.csv").exists()
    assert not (GOLD / "gold_panel_anual.csv").exists()


def test_vintage_stamp():
    assert (GOLD / "VINTAGE").read_text(encoding="utf-8").strip() == "2026-07-31"


def test_kpis_shape():
    kp = json.loads((GOLD / "kpis_perfiles.json").read_text(encoding="utf-8"))
    assert set(kp) == {"vintage", "fuentes", "kpi", "series"}
    assert kp["vintage"] == "2026-07-31"
    assert len(kp["kpi"]) == 42
    assert len(kp["series"]) == 21
    assert kp["kpi"]["euribor12m"]["valor"] == 2.8
    assert kp["kpi"]["cuota_hipoteca_mediana"]["valor"] == 745


def test_central_scenario_rows():
    rows = [r for r in csv.DictReader((GOLD / "gold_escenarios_deuda.csv").open(encoding="utf-8"))
            if r["escenario"] == "central"]
    years = sorted(int(float(r["year"])) for r in rows)
    assert years[0] == 2024 and years[-1] == 2050 and len(years) == 27
    row_2026 = next(r for r in rows if int(float(r["year"])) == 2026)
    # extract L868: central,2026,106.32,-1.35,2.68,3.3,0.45
    assert row_2026["deuda"] == "106.32"


def test_mc_and_cuota_rows():
    mc = [r for r in csv.DictReader((GOLD / "gold_escenarios_deuda_mc.csv").open(encoding="utf-8"))
          if r["escenario"] == "central"]
    mc_years = {int(float(r["year"])) for r in mc}
    assert {2030, 2050, 2070} <= mc_years
    cuota = list(csv.DictReader((GOLD / "gold_cuota_teorica.csv").open(encoding="utf-8")))
    assert len(cuota) == 17
    navarra = next(r for r in cuota if r["ccaa"].startswith("Navarra"))
    assert navarra["cuota_mensual"] == "744.89"     # extract L932
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_data_layer.py -v`
Expected: FAIL — collection error or `missing gold_escenarios_deuda.csv` (no `data/gold` yet).

- [ ] **Step 3: Scaffold packages, install deps, copy the gold slice**

```bash
cd /home/dan/projects/evo_final_work
mkdir -p data/gold data/live engine api scripts tests/fixtures
touch data/__init__.py data/live/__init__.py engine/__init__.py api/__init__.py \
      scripts/__init__.py tests/__init__.py

cat > requirements.txt <<'EOF'
fastapi>=0.115
uvicorn>=0.30
httpx>=0.27
requests>=2.32
pandas>=2.2
numpy>=1.26
pyyaml>=6.0
pytest>=8.3
EOF
.venv/bin/pip install -r requirements.txt

# gitignore the refresh output (data_cache/ is already ignored)
printf 'data/vintages/\n' >> .gitignore

SRC=legacy/design_data/data
cp $SRC/gold/gold_escenarios_deuda.csv $SRC/gold/gold_escenarios_deuda_mc.csv \
   $SRC/gold/gold_cuota_teorica.csv $SRC/gold/gold_projections.csv \
   $SRC/gold/gold_ccaa_trimestral.csv $SRC/gold/gold_asequibilidad_ccaa.csv \
   $SRC/gold/gold_pobreza_infantil.csv $SRC/gold/gold_bienestar_pais.csv \
   $SRC/gold/gold_fiscal_historico.csv data/gold/
cp $SRC/kpis_perfiles.json $SRC/manifest.csv $SRC/provenance_vintage_manifest.csv data/gold/
printf '2026-07-31\n' > data/gold/VINTAGE
```

(`gold_century_fiscal.csv` and `gold_panel_anual.csv` deliberately NOT copied — spec §3.1.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_data_layer.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .gitignore data/__init__.py data/live/__init__.py \
        engine/__init__.py api/__init__.py scripts/__init__.py tests/__init__.py \
        data/gold tests/test_data_layer.py
git commit -m "feat: scaffold phase-1 packages and commit gold vintage 2026-07-31"
```

---

### Task 2: Live data clients port (`data/live/`)

**Files:**
- Create: `data/live/models.py`, `data/live/cache.py`, `data/live/worldbank_client.py`, `data/live/eurostat_client.py`, `data/live/oecd_client.py`, `data/live/panel_builder.py`, `data/live/country_list.py`, `data/live/indicator_catalog.yaml` — all copied from `archive/mvp-app-v1/data/`
- Modify: `tests/test_data_layer.py` (append ported MVP client tests)

**Interfaces:**
- Consumes: nothing from earlier tasks (self-contained port).
- Produces (used by Tasks 3, 13):
  - `data.live.models.FetchResult` — dataclass `(values: Dict[int, float], source: str, from_cache: bool, fetched_at: Optional[float] = None, error: Optional[str] = None)` with property `available: bool`
  - `data.live.cache.DiskCache(cache_dir: str = "data_cache")` with `.get(iso3, key)` / `.set(iso3, key, result)`
  - `data.live.panel_builder.load_catalog() -> dict`, `fetch_one(...)`, `build_country_panel(country_iso3, start_year=2000, end_year=2024, cache=None) -> Dict[str, FetchResult]`, `coverage_score(panel) -> float`
  - `data.live.country_list.fetch_country_list(timeout=30) -> List[dict]`, `load_country_list() -> List[dict]` (entries `{"iso3","iso2","name","region"}`), `iso3_to_iso2_map()`
  - clients: `worldbank_client.fetch_indicator`, `eurostat_client.fetch_indicator`, `oecd_client.fetch_indicator` — never raise; failures return `FetchResult` with `error`.

This is a copy-with-import-adjustments port (the code was reviewed twice in the MVP). Do NOT rewrite any logic.

- [ ] **Step 1: Append the ported client tests (failing)**

```bash
cd /home/dan/projects/evo_final_work
printf '\n\n# ---- ported from archive/mvp-app-v1/tests/test_data_layer.py (30 tests) ----\n' >> tests/test_data_layer.py
sed -e 's/\bfrom data\./from data.live./g' \
    -e 's/\bfrom data import /from data.live import /g' \
    -e 's/"data\./"data.live./g' \
    -e "s/'data\./'data.live./g" \
    archive/mvp-app-v1/tests/test_data_layer.py >> tests/test_data_layer.py
grep -nE "from data\.|['\"]data\.[a-z]" tests/test_data_layer.py | grep -v "data\.live" \
  && echo "UNPORTED IMPORT FOUND — fix before continuing" || echo "imports clean"
```

The sed rewrites both import lines and `unittest.mock.patch("data.…")` target strings.

- [ ] **Step 2: Run to verify the new tests fail**

Run: `.venv/bin/python -m pytest tests/test_data_layer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'data.live.cache'` (or similar) on collection.

- [ ] **Step 3: Copy the eight modules and adjust the import lines**

```bash
cd /home/dan/projects/evo_final_work
for f in models.py cache.py worldbank_client.py eurostat_client.py oecd_client.py \
         panel_builder.py country_list.py indicator_catalog.yaml; do
  cp archive/mvp-app-v1/data/$f data/live/$f
done
sed -i 's/\bfrom data\./from data.live./g; s/\bfrom data import /from data.live import /g' data/live/*.py
```

Exact lines that change (verify with `grep -n "from data" data/live/*.py`):
- `data/live/cache.py:6` → `from data.live.models import FetchResult`
- `data/live/worldbank_client.py:6` → `from data.live.models import FetchResult`
- `data/live/eurostat_client.py:6` → `from data.live.models import FetchResult`
- `data/live/oecd_client.py:6` → `from data.live.models import FetchResult`
- `data/live/panel_builder.py:7-10` →
  ```python
  from data.live.models import FetchResult
  from data.live.cache import DiskCache
  from data.live.country_list import iso3_to_iso2_map
  from data.live import worldbank_client, eurostat_client, oecd_client
  ```
- `data/live/models.py`, `data/live/country_list.py`, `data/live/indicator_catalog.yaml`: byte-identical copies (no `data.` imports).

Behavior retained verbatim: never-raise contract, cache-first with `data_cache/` (gitignored), explicit N/A, `indicator_catalog.yaml` with 19 indicators, `CATALOG_PATH = Path(__file__).parent / "indicator_catalog.yaml"` still resolves because the yaml moved together with `panel_builder.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_data_layer.py -v`
Expected: 35 passed (5 gold + 30 ported).

- [ ] **Step 5: Commit**

```bash
git add data/live tests/test_data_layer.py
git commit -m "feat: port MVP live data clients to data/live with import-path adjustments"
```

---

### Task 3: Generic engine port (`engine/generic.py`)

**Files:**
- Create: `engine/generic.py` (concatenated port of `archive/mvp-app-v1/engine/{debt_dynamics,satellite,fiscal_space,scenario}.py`)
- Create: `tests/test_generic_engine.py` (concatenated port of the 4 MVP engine test modules)
- Create: `tests/fixtures/sample_country_panel.json` (copied)

**Interfaces:**
- Consumes: `data.live.models.FetchResult` (Task 2).
- Produces (used by Task 13): in `engine.generic` —
  - `DebtPathPoint(year, debt_gdp_pct, interest_rate_pct, growth_rate_pct, primary_balance_pct, contingent_shock_pct)`; `project_debt_path(initial_debt_gdp_pct, r_path_pct, g_path_pct, pb_path_pct, start_year, contingent_shocks_pct=None) -> List[DebtPathPoint]`
  - `OKUN_COEFFICIENT = 0.5`, `PHILLIPS_SLOPE = 0.3` (generic calibration — deliberately distinct from Spain's 0.48/0.22); `okun_unemployment_gap`, `phillips_inflation`, `indexed_growth`
  - `SPENDING_CATEGORIES`, `FiscalSpaceResult`, `allocate_fiscal_space`
  - `ScenarioLevers(horizon_years=10, tax_wedge_delta_pp=0.0, primary_balance_target_pct=0.0, output_gap_path_pct=None, contingent_shocks_pct=None, indexation_delta_pp=0.0, allocation_shares={...})`, `ScenarioResult(country_iso3, debt_path, fiscal_space_by_year, unemployment_path_pct, inflation_path_pct, nominal_wage_growth_path_pct, coverage_score, defaults_used, baseline_years)`, `BASELINE_DEFAULTS`, `BASELINE_INDICATOR_LABELS`, `run_scenario(country_iso3, panel, levers) -> ScenarioResult`

Copy-with-import-adjustments only. Name-collision audit already done: across the four source test modules all test names are unique (4+5+4+8 = 21 tests); `FIXTURE_PATH` is defined twice with the identical value (harmless); no other top-level name repeats.

- [ ] **Step 1: Create the failing ported test module**

```bash
cd /home/dan/projects/evo_final_work
cp archive/mvp-app-v1/tests/fixtures/sample_country_panel.json tests/fixtures/
python3 - <<'EOF'
import re
from pathlib import Path
srcs = ["test_debt_engine.py", "test_satellite_equations.py",
        "test_fiscal_space.py", "test_scenario.py"]
out = ['"""Ported MVP engine tests (spec §7 test_generic_engine.py).\n'
       'Concatenated verbatim from archive/mvp-app-v1/tests/, imports rewritten\n'
       'to engine.generic / data.live.models."""\n']
for name in srcs:
    t = (Path("archive/mvp-app-v1/tests") / name).read_text(encoding="utf-8")
    t = re.sub(r"from engine\.(debt_dynamics|satellite|fiscal_space|scenario) import",
               "from engine.generic import", t)
    t = t.replace("from data.models import", "from data.live.models import")
    out.append(f"\n\n# ---- ported from archive/mvp-app-v1/tests/{name} ----\n" + t)
Path("tests/test_generic_engine.py").write_text("".join(out), encoding="utf-8")
print("written")
EOF
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_generic_engine.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.generic'`.

- [ ] **Step 3: Assemble `engine/generic.py`**

```bash
cd /home/dan/projects/evo_final_work
python3 - <<'EOF'
from pathlib import Path
src = Path("archive/mvp-app-v1/engine")
header = '''"""Generic (non-Spain) country engine — the MVP chain ported verbatim.

Concatenation of archive/mvp-app-v1/engine/{debt_dynamics,satellite,fiscal_space,
scenario}.py with only import-path adjustments (spec §4.4). Generic calibration:
OKUN_COEFFICIENT = 0.5 and PHILLIPS_SLOPE = 0.3 — calibrated defaults, NOT
country-specific, and deliberately DISTINCT from the Spain engine's 0.48 / 0.22.
Honesty fields defaults_used / baseline_years are retained.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from data.live.models import FetchResult


'''
def tail(name: str, skip: int) -> str:
    lines = (src / name).read_text(encoding="utf-8").split("\n")
    return "\n".join(lines[skip:]).strip("\n") + "\n\n\n"
body = (
    tail("debt_dynamics.py", 4)     # skip its 2 imports + 2 blanks; starts at @dataclass
    + tail("satellite.py", 2)       # skip its 1-line module docstring + blank; starts at OKUN_COEFFICIENT
    + tail("fiscal_space.py", 3)    # skip its 2 imports + blank; starts at SPENDING_CATEGORIES
    + tail("scenario.py", 9)        # skip its imports block (lines 1-9); starts at @dataclass ScenarioLevers
)
Path("engine/generic.py").write_text(header + body.rstrip("\n") + "\n", encoding="utf-8")
print("written engine/generic.py")
EOF
# sanity: the module must start each section at the expected symbol
grep -n "^@dataclass\|^class DebtPathPoint\|^OKUN_COEFFICIENT\|^SPENDING_CATEGORIES\|^BASELINE_DEFAULTS\|^def run_scenario" engine/generic.py
```

The four source files' internal cross-imports (`from engine.debt_dynamics import …` etc. inside `scenario.py`) disappear because everything now lives in one module; the header carries the only imports any section needs (`dataclass, field`, `Dict, List, Optional`, `FetchResult`). If the grep shows a leftover `from engine.` or `from data.models` line in `engine/generic.py`, delete that line — nothing else may be edited.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_generic_engine.py -v`
Expected: 21 passed.

- [ ] **Step 5: Commit**

```bash
git add engine/generic.py tests/test_generic_engine.py tests/fixtures/sample_country_panel.json
git commit -m "feat: port MVP generic engine chain into engine/generic.py"
```

---

### Task 4: `engine/constants.py` — every named constant + gold loaders

**Files:**
- Create: `engine/constants.py`
- Test: `tests/test_engine_spain.py` (new file, constants section)

**Interfaces:**
- Consumes: `data/gold/` (Task 1).
- Produces (used by Tasks 5–12): module `engine.constants` exporting exactly these names —
  - `GOLD_DIR: Path`, `VINTAGE: str`, `ENGINE_VERSION: str`
  - Spain constants (floats): `MULT, RHO, E_R, E_EXT, E_PM, OKUN, KAPPA, GAMMA, THETA, PHI, A_Z, A_TAU, A_LAM, REFI, TERM, DIFF, IPV_LR, IPV_REV, E_IPV_R, E_IPV_G, RJUV, PM_DECAY`
  - MC constants: `MC_START_YEAR, MC_HORIZON, MC_N_PATHS, MC_SEED_DEFAULT, MC_RHO, MC_SIG_R, MC_SIG_G, MC_SIG_SP, MC_FB_UP, MC_FB_DN, MC_PB_DRIFT, MC_EXT_SLOPE_R, MC_EXT_SLOPE_PB, MC_EXT_SLOPE_DEMOG`
  - Loaders: `load_kpis() -> dict`, `load_central() -> dict[int, dict[str, float]]`, `load_olddep() -> dict[int, float]` (all `lru_cache`d)
  - Vintage-anchored values: `CAL_SALARIO_MES: float`, `V0: dict[str, float]` (24 keys), `BASE_LEVERS: dict[str, float]` (10 keys)
  - `CONSTANTS_TABLE: list[dict]` — entries `{"name", "value", "unit", "provenance"}` for the `/constants` endpoint.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_engine_spain.py`:

```python
"""Spain engine tests: constants (Task 4), levers/presets (Task 5),
chain + deviation semantics (Task 6), persona dependents (Task 7)."""
import math

import pytest

from engine import constants as c


def test_vintage_and_version():
    assert c.VINTAGE == "2026-07-31"
    assert c.ENGINE_VERSION == "1.0.0"


def test_spain_constants_verbatim_v16():
    # extract L73-91 (`const C` of _v16_template.html)
    assert (c.MULT, c.RHO, c.E_R, c.E_EXT, c.E_PM) == (1.40, 0.62, 0.45, 0.25, 0.012)
    assert (c.OKUN, c.KAPPA, c.GAMMA, c.THETA, c.PHI) == (0.48, 0.22, 0.045, 0.55, 0.30)
    assert (c.A_Z, c.A_TAU, c.A_LAM) == (1.10, 0.30, 0.45)
    assert (c.REFI, c.TERM) == (0.14, 0.17)
    assert c.DIFF == 1.4757            # build_v16.py bisection (extract L1055-1073)
    assert (c.IPV_LR, c.IPV_REV, c.E_IPV_R, c.E_IPV_G) == (3.0, 0.60, 2.6, 1.1)
    assert c.RJUV == 2.317
    assert c.PM_DECAY == 0.45


def test_v0_and_base_levers_from_gold_kpis():
    assert c.V0["u"] == 10.1 and c.V0["pi"] == 3.0 and c.V0["g"] == 2.7
    assert c.V0["bono"] == 3.42 and c.V0["precio"] == 171444 and c.V0["cuota"] == 745
    assert c.V0["salmes"] == 1749.79          # round(24497 / 14, 2) — build_v16 calib
    assert c.V0["pens"] == 13.23 and c.V0["arop"] == 28.5 and c.V0["vida"] == 84.0
    assert c.V0["hip"] == 500906 and c.V0["bls"] == 10.0 and c.V0["sobre"] == 7.2
    assert c.BASE_LEVERS == {"r": 2.8, "prima": 45.0, "sp": 0.0, "lam": 0.9, "pm": 0.0,
                             "tau": 0.0, "z": 0.0, "ext": 1.8, "dem": 0.0, "idx": 0.0}


def test_gold_loaders():
    central = c.load_central()
    assert central[2025]["deuda"] == 105.6         # extract L1083
    assert central[2026] == {"deuda": 106.32, "pb": -1.35, "r_efectivo": 2.68,
                             "g_nominal": 3.3, "presion_demog": 0.45}   # extract L868
    olddep = c.load_olddep()
    assert olddep[2026] == 32.6 and olddep[2050] == 59.0


def test_constants_table_has_provenance_for_every_entry():
    assert len(c.CONSTANTS_TABLE) >= 30
    for entry in c.CONSTANTS_TABLE:
        assert set(entry) == {"name", "value", "unit", "provenance"}
        assert entry["provenance"].strip(), entry["name"]
        assert math.isfinite(float(entry["value"]))
    names = [e["name"] for e in c.CONSTANTS_TABLE]
    for expected in ("MULT", "OKUN", "DIFF", "MC_SIG_R", "GENERIC_OKUN", "GENERIC_PHILLIPS"):
        assert expected in names
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_engine_spain.py -v`
Expected: FAIL — `ImportError: cannot import name 'constants'` / `ModuleNotFoundError`.

- [ ] **Step 3: Implement `engine/constants.py`**

```python
"""Every named engine constant — the single source of truth (spec §4.1).

Spain constants are the v16 calibration, ported verbatim from
docs/superpowers/plans/references/v16-engine-extract.md S1 (extract L69-91:
`const BASE` and `const C`). They are calibrated defaults, NOT estimates —
phase 3 contests may replace them (AC-V6). Vintage-anchored values (V0,
BASE_LEVERS) load from the committed gold slice, never hardcoded twice.
"""
from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path

GOLD_DIR = Path(__file__).resolve().parents[1] / "data" / "gold"
VINTAGE = (GOLD_DIR / "VINTAGE").read_text(encoding="utf-8").strip()
ENGINE_VERSION = "1.0.0"

# ---- Spain semi-structural constants (v16 `const C`, extract L73-91) ----
MULT = 1.40      # fiscal multiplier (CORE Macro U3)
RHO = 0.62       # persistence of the GDP level deviation
E_R = 0.45       # pp of GDP per pp of interest rate (investment/consumption)
E_EXT = 0.25     # external-demand channel weight (U7)
E_PM = 0.012     # pp of GDP per 1 % import-price shock
OKUN = 0.48      # Okun beta, Spain calibration (generic engine uses 0.5)
KAPPA = 0.22     # Phillips slope
GAMMA = 0.045    # import-price pass-through to HICP (2021-23 episode)
THETA = 0.55     # inflation-expectations inertia
PHI = 0.30       # wage-setting: nominal wage response per pp of slack
A_Z = 1.10       # u* shifter: labour institutions (WS-PS)
A_TAU = 0.30     # u* shifter: tax wedge (WS)
A_LAM = 0.45     # u* shifter: productivity (PS)
REFI = 0.14      # share of sovereign debt refinanced each year
TERM = 0.17      # 10y term premium over Euribor (3.42 − 2.80 − 0.45)
DIFF = 1.4757    # implicit mortgage spread pp — build_v16.py bisection to the
                 # €744.89 median of gold_cuota_teorica.csv at Euribor 2.80
IPV_LR = 3.0     # house-price long-run growth (% a/a)
IPV_REV = 0.60   # yearly reversion of IPV toward IPV_LR
E_IPV_R = 2.6    # IPV response to the rate lever
E_IPV_G = 1.1    # IPV response to the growth deviation
RJUV = 2.317     # youth/total unemployment ratio (stable in the 5y series)
PM_DECAY = 0.45  # geometric decay of the import-price Phillips term (extract L116)

# ---- Monte Carlo DSA calibration (fitted against gold_escenarios_deuda_mc.csv;
#      seed-42 / 4000-path verification: max |dev| vs gold p5/p50/p95 at
#      2030/2050/2070 = 1.399 pp — see Task 8 / tests/test_anchors.py A5) ----
MC_START_YEAR = 2026
MC_HORIZON = 2070
MC_N_PATHS = 4000
MC_SEED_DEFAULT = 42
MC_RHO = 0.96          # AR(1) persistence of the r/g/sp shocks
MC_SIG_R = 0.42        # pp — annual innovation, effective interest rate
MC_SIG_G = 0.12        # pp — annual innovation, nominal growth
MC_SIG_SP = 0.30       # pp GDP — annual innovation, primary balance
MC_FB_UP = 0.010       # fiscal-reaction brake when debt runs above the deterministic path
MC_FB_DN = 0.005       # symmetric loosening when debt runs below it
MC_PB_DRIFT = (-0.10884, -0.34459, 0.75410)  # pb calib add-on: ≤2030 / 2031-2050 / 2051-2070
MC_EXT_SLOPE_R = 0.006       # r_efectivo slope after 2050: (3.47 − 3.44) / 5
MC_EXT_SLOPE_PB = -0.136     # pb slope after 2050: (−7.47 − (−6.79)) / 5
MC_EXT_SLOPE_DEMOG = 0.136   # presion_demog slope after 2050: (6.57 − 5.89) / 5

# ---- gold-slice loaders ----
@lru_cache(maxsize=1)
def load_kpis() -> dict:
    return json.loads((GOLD_DIR / "kpis_perfiles.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_central() -> dict[int, dict[str, float]]:
    out: dict[int, dict[str, float]] = {}
    with (GOLD_DIR / "gold_escenarios_deuda.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["escenario"] != "central":
                continue
            out[int(float(row["year"]))] = {
                "deuda": float(row["deuda"]), "pb": float(row["pb"]),
                "r_efectivo": float(row["r_efectivo"]),
                "g_nominal": float(row["g_nominal"]),
                "presion_demog": float(row["presion_demog"]),
            }
    return out


@lru_cache(maxsize=1)
def load_olddep() -> dict[int, float]:
    out: dict[int, float] = {}
    with (GOLD_DIR / "gold_projections.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["geo"] == "ES" and row["variant"] == "BSL":
                out[int(float(row["year"]))] = float(row["olddep"])
    return out


def _kpi(name: str) -> float:
    return float(load_kpis()["kpi"][name]["valor"])


# build_v16.py `calib` block (extract L1031-1040)
CAL_SALARIO_MES = round(_kpi("salario_medio") / 14, 2)   # 1749.79

# v16 `const V0` (extract L41-66): the vintage values anchoring year 0
V0: dict[str, float] = {
    "u": _kpi("paro_total"),                 # 10.1 % (2026-06)
    "pi": _kpi("hicp_es"),                   # 3.0 % a/a (2025-12)
    "g": _kpi("pib_yoy"),                    # 2.7 % a/a (2026-Q2)
    "bono": _kpi("bono10y_es"),              # 3.42 % (2026-06)
    "precio": _kpi("precio_vivienda_mediano"),  # 171444 EUR (2024)
    "cuota": _kpi("cuota_hipoteca_mediana"),    # 745 EUR/mes
    "salmes": CAL_SALARIO_MES,               # 1749.79 EUR (24497/14)
    "salario": _kpi("salario_medio"),        # 24497 EUR/año
    "ipv": _kpi("vivienda_precio_yoy"),      # 12.8 % a/a (2026-Q1)
    "pens": _kpi("gasto_pensiones_pib"),     # 13.23 % PIB (2024)
    "arop": _kpi("arop_infantil"),           # 28.5 % (2025)
    "edu": _kpi("gasto_educacion_pib"),      # 4.1 % PIB
    "d1": _kpi("salarios_publicos_pib"),     # 10.9 % PIB
    "p2": _kpi("consumo_intermedio_pib"),    # 5.7 % PIB
    "d3": _kpi("subvenciones_pib"),          # 1.4 % PIB
    "p51": _kpi("inversion_publica_pib"),    # 3.0 % PIB
    "gtot": _kpi("gasto_total_pib"),         # 45.4 % PIB
    "temp": _kpi("temporalidad"),            # 15.3 %
    "auton": _kpi("autoempleo"),             # 14.5 %
    "bls": _kpi("bls_endurecimiento"),       # 10.0 % neto
    "hip": _kpi("hipotecas_anuales"),        # 500906 /año
    "sobre": _kpi("sobrecarga_vivienda"),    # 7.2 %
    "ujuv": _kpi("paro_juvenil"),            # 23.4 %
    "vida": _kpi("esperanza_vida"),          # 84.0 años
}

# v16 `const BASE` (extract L69-70 / L1598-1599): lever base = the vintage
BASE_LEVERS: dict[str, float] = {
    "r": _kpi("euribor12m"),         # 2.8 % (2026-06)
    "prima": _kpi("spread_es_de"),   # 45 pb (2026-06)
    "sp": 0.0, "lam": 0.9, "pm": 0.0, "tau": 0.0,
    "z": 0.0, "ext": 1.8, "dem": 0.0, "idx": 0.0,
}

_V16 = "v16 calibration — calibrated default, not estimated (phase 3 contests may replace, AC-V6)"
_MC = "MC calibration fitted to gold_escenarios_deuda_mc.csv central envelopes (this repo, phase 1)"

CONSTANTS_TABLE: list[dict] = [
    {"name": "MULT", "value": MULT, "unit": "x", "provenance": _V16 + " · fiscal multiplier, CORE Macro U3"},
    {"name": "RHO", "value": RHO, "unit": "x", "provenance": _V16 + " · GDP-level persistence"},
    {"name": "E_R", "value": E_R, "unit": "pp GDP / pp rate", "provenance": _V16},
    {"name": "E_EXT", "value": E_EXT, "unit": "x", "provenance": _V16 + " · external-demand channel"},
    {"name": "E_PM", "value": E_PM, "unit": "pp GDP / %", "provenance": _V16 + " · import-price channel"},
    {"name": "OKUN", "value": OKUN, "unit": "pp u / pp GDP", "provenance": _V16 + " · Spain Okun (generic engine uses 0.5)"},
    {"name": "KAPPA", "value": KAPPA, "unit": "pp pi / pp gap", "provenance": _V16 + " · Phillips slope"},
    {"name": "GAMMA", "value": GAMMA, "unit": "pp pi / %", "provenance": _V16 + " · pass-through, 2021-23 episode"},
    {"name": "THETA", "value": THETA, "unit": "x", "provenance": _V16 + " · inflation inertia"},
    {"name": "PHI", "value": PHI, "unit": "pp wage / pp gap", "provenance": _V16 + " · wage-setting curve"},
    {"name": "A_Z", "value": A_Z, "unit": "pp u* / index", "provenance": _V16 + " · WS-PS shifter"},
    {"name": "A_TAU", "value": A_TAU, "unit": "pp u* / pp", "provenance": _V16 + " · WS-PS shifter"},
    {"name": "A_LAM", "value": A_LAM, "unit": "pp u* / pp", "provenance": _V16 + " · WS-PS shifter"},
    {"name": "REFI", "value": REFI, "unit": "share/yr", "provenance": _V16 + " · debt refinancing share 14 %/yr"},
    {"name": "TERM", "value": TERM, "unit": "pp", "provenance": _V16 + " · 10y term premium (3.42 − 2.80 − 0.45)"},
    {"name": "DIFF", "value": DIFF, "unit": "pp", "provenance": "build_v16.py bisection vs gold_cuota_teorica.csv €744.89 median at Euribor 2.80"},
    {"name": "IPV_LR", "value": IPV_LR, "unit": "% a/a", "provenance": _V16 + " · house-price long run"},
    {"name": "IPV_REV", "value": IPV_REV, "unit": "x", "provenance": _V16 + " · IPV reversion"},
    {"name": "E_IPV_R", "value": E_IPV_R, "unit": "pp IPV / pp rate", "provenance": _V16},
    {"name": "E_IPV_G", "value": E_IPV_G, "unit": "pp IPV / pp growth", "provenance": _V16},
    {"name": "RJUV", "value": RJUV, "unit": "x", "provenance": _V16 + " · youth/total unemployment ratio, 5y series"},
    {"name": "PM_DECAY", "value": PM_DECAY, "unit": "x", "provenance": _V16 + " · import-price shock decay"},
    {"name": "CAL_SALARIO_MES", "value": CAL_SALARIO_MES, "unit": "EUR/mes", "provenance": "kpis_perfiles.json salario_medio 24497 / 14 (build_v16 calib)"},
    {"name": "GENERIC_OKUN", "value": 0.5, "unit": "pp u / pp GDP", "provenance": "generic engine calibrated default (literature 0.3-0.5), NOT country-specific — distinct from Spain's 0.48"},
    {"name": "GENERIC_PHILLIPS", "value": 0.3, "unit": "pp pi / pp gap", "provenance": "generic engine calibrated default, NOT country-specific — distinct from Spain's 0.22"},
    {"name": "MC_RHO", "value": MC_RHO, "unit": "x", "provenance": _MC},
    {"name": "MC_SIG_R", "value": MC_SIG_R, "unit": "pp", "provenance": _MC},
    {"name": "MC_SIG_G", "value": MC_SIG_G, "unit": "pp", "provenance": _MC},
    {"name": "MC_SIG_SP", "value": MC_SIG_SP, "unit": "pp GDP", "provenance": _MC},
    {"name": "MC_FB_UP", "value": MC_FB_UP, "unit": "1/yr", "provenance": _MC + " · fiscal-reaction brake"},
    {"name": "MC_FB_DN", "value": MC_FB_DN, "unit": "1/yr", "provenance": _MC + " · fiscal-reaction loosening"},
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_engine_spain.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add engine/constants.py tests/test_engine_spain.py
git commit -m "feat: engine constants module — v16 calibration, MC calibration, gold loaders"
```

---

### Task 5: `engine/levers.py` — Levers, LEVER_SPECS, PRESETS

**Files:**
- Create: `engine/levers.py`
- Modify: `tests/test_engine_spain.py` (append levers section)

**Interfaces:**
- Consumes: `engine.constants.BASE_LEVERS`.
- Produces (used by Tasks 6–13):
  - `@dataclass(frozen=True) Levers` with fields `r, prima, sp, lam, pm, tau, z, ext, dem, idx` (floats, defaults = base values; `Levers()` IS the base scenario)
  - `LEVER_SPECS: list[dict]` — 10 entries `{"id","sym","nm","unit","min","max","step","dec","src"}` (Spanish verbatim)
  - `PRESETS: list[dict]` — 8 entries `{"id","nm","set"}` (Spanish verbatim)
  - `preset_levers(preset_id: str) -> Levers`
  - `validate_levers(levers: Levers) -> list[str]` (empty list = valid)

- [ ] **Step 1: Append failing tests to `tests/test_engine_spain.py`**

```python
# ---- Task 5: levers & presets ----
from engine.levers import LEVER_SPECS, PRESETS, Levers, preset_levers, validate_levers

# spec §4.1 table (binding) — (id, min, max, base)
EXPECTED_RANGES = [
    ("r", 0.0, 6.0, 2.8), ("prima", 0.0, 400.0, 45.0), ("sp", -4.0, 4.0, 0.0),
    ("lam", -0.5, 2.5, 0.9), ("pm", -50.0, 100.0, 0.0), ("tau", -5.0, 5.0, 0.0),
    ("z", -2.0, 2.0, 0.0), ("ext", -4.0, 6.0, 1.8), ("dem", -1.0, 1.0, 0.0),
    ("idx", -1.5, 1.0, 0.0),
]


def test_lever_specs_ranges_and_bases():
    assert [s["id"] for s in LEVER_SPECS] == [rid for rid, *_ in EXPECTED_RANGES]
    base = Levers()
    for (rid, lo, hi, base_val), spec in zip(EXPECTED_RANGES, LEVER_SPECS):
        assert (spec["min"], spec["max"]) == (lo, hi), rid
        assert getattr(base, rid) == base_val, rid
    syms = [s["sym"] for s in LEVER_SPECS]
    assert syms == ["r", "σ", "sp", "λ", "pᵐ", "τ", "z", "Y*", "β₆₅", "ι"]
    assert LEVER_SPECS[0]["nm"] == "Tipo de interés · Euríbor 12m"


def test_presets_verbatim_and_within_ranges():
    assert [p["id"] for p in PRESETS] == [f"S{i}" for i in range(8)]
    assert [p["nm"] for p in PRESETS] == [
        "S0 base", "S1 tipos +200 pb", "S2 petróleo +50 %", "S3 consolidación",
        "S4 productividad", "S5 desregulación lab.", "S6 envejecimiento", "S7 adverso"]
    assert PRESETS[0]["set"] == {}
    assert PRESETS[7]["set"] == {"r": 4.8, "pm": 50.0, "prima": 150.0}
    assert preset_levers("S0") == Levers()
    for p in PRESETS:
        assert validate_levers(preset_levers(p["id"])) == [], p["id"]


def test_validate_levers_flags_out_of_range():
    assert validate_levers(Levers(r=9.0)) == ["r=9.0 outside [0.0, 6.0]"]
    assert validate_levers(Levers()) == []
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_engine_spain.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.levers'`.

- [ ] **Step 3: Implement `engine/levers.py`**

```python
"""Levers, ranges and presets — v16 `const LEVERS` / `const PRESETS` ported
verbatim (extract L178-200; template L390-411). Ranges are the empirically
anchored envelopes of v12 (extract S7.2)."""
from __future__ import annotations

from dataclasses import dataclass, fields

from engine.constants import BASE_LEVERS


@dataclass(frozen=True)
class Levers:
    r: float = BASE_LEVERS["r"]          # 2.8
    prima: float = float(BASE_LEVERS["prima"])   # 45.0
    sp: float = 0.0
    lam: float = 0.9
    pm: float = 0.0
    tau: float = 0.0
    z: float = 0.0
    ext: float = 1.8
    dem: float = 0.0
    idx: float = 0.0


# v16 `const LEVERS` — Spanish copy verbatim (template L390-399, extract L178-189)
LEVER_SPECS: list[dict] = [
    {"id": "r", "sym": "r", "nm": "Tipo de interés · Euríbor 12m", "unit": "%",
     "min": 0.0, "max": 6.0, "step": 0.05, "dec": 2, "src": "ecb_euribor12m.csv · 2026-06"},
    {"id": "prima", "sym": "σ", "nm": "Prima de riesgo · spread ES–DE", "unit": "pb",
     "min": 0.0, "max": 400.0, "step": 5.0, "dec": 0, "src": "ecb_bono10y_{es,de}.csv · 2026-06"},
    {"id": "sp", "sym": "sp", "nm": "Saldo primario · Δ vs central", "unit": "pp PIB",
     "min": -4.0, "max": 4.0, "step": 0.1, "dec": 1, "src": "gold_escenarios_deuda.csv (central)"},
    {"id": "lam", "sym": "λ", "nm": "Productividad", "unit": "%/año",
     "min": -0.5, "max": 2.5, "step": 0.1, "dec": 1, "src": "PWT + INE · desplaza la PS"},
    {"id": "pm", "sym": "pᵐ", "nm": "Precio importaciones/energía", "unit": "% a/a",
     "min": -50.0, "max": 100.0, "step": 5.0, "dec": 0, "src": "WEO commodity prices"},
    {"id": "tau", "sym": "τ", "nm": "Presión fiscal · cuña laboral", "unit": "pp",
     "min": -5.0, "max": 5.0, "step": 0.25, "dec": 2, "src": "Eurostat GFS · desplaza la WS"},
    {"id": "z", "sym": "z", "nm": "Instituciones laborales", "unit": "índice",
     "min": -2.0, "max": 2.0, "step": 0.1, "dec": 1, "src": "OECD/Eurostat · desplaza la WS"},
    {"id": "ext", "sym": "Y*", "nm": "Demanda externa", "unit": "% a/a",
     "min": -4.0, "max": 6.0, "step": 0.1, "dec": 1, "src": "WEO · canal exterior (U7)"},
    {"id": "dem", "sym": "β₆₅", "nm": "Presión demográfica", "unit": "×",
     "min": -1.0, "max": 1.0, "step": 0.05, "dec": 2, "src": "gold_projections.csv · variante"},
    {"id": "idx", "sym": "ι", "nm": "Indexación pensiones/nóminas", "unit": "IPC+pp",
     "min": -1.5, "max": 1.0, "step": 0.1, "dec": 1, "src": "regla de revalorización · palanca"},
]

# v16 `const PRESETS` — verbatim (extract L1583-1592); r offsets resolved
# against BASE (S1/S7: BASE.r + 2 = 4.8)
PRESETS: list[dict] = [
    {"id": "S0", "nm": "S0 base", "set": {}},
    {"id": "S1", "nm": "S1 tipos +200 pb", "set": {"r": BASE_LEVERS["r"] + 2}},
    {"id": "S2", "nm": "S2 petróleo +50 %", "set": {"pm": 50.0}},
    {"id": "S3", "nm": "S3 consolidación", "set": {"sp": 1.0}},
    {"id": "S4", "nm": "S4 productividad", "set": {"lam": 1.4}},
    {"id": "S5", "nm": "S5 desregulación lab.", "set": {"z": -1.0, "tau": -1.5}},
    {"id": "S6", "nm": "S6 envejecimiento", "set": {"dem": 0.6}},
    {"id": "S7", "nm": "S7 adverso", "set": {"r": BASE_LEVERS["r"] + 2, "pm": 50.0, "prima": 150.0}},
]

_SPEC_BY_ID = {s["id"]: s for s in LEVER_SPECS}


def preset_levers(preset_id: str) -> Levers:
    preset = next(p for p in PRESETS if p["id"] == preset_id)
    return Levers(**preset["set"])


def validate_levers(levers: Levers) -> list[str]:
    errors: list[str] = []
    for f in fields(Levers):
        spec = _SPEC_BY_ID[f.name]
        value = getattr(levers, f.name)
        if not (spec["min"] <= value <= spec["max"]):
            errors.append(f"{f.name}={value} outside [{spec['min']}, {spec['max']}]")
    return errors
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_engine_spain.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add engine/levers.py tests/test_engine_spain.py
git commit -m "feat: levers dataclass, v16 lever specs and presets S0-S7"
```

---

### Task 6: `engine/spain.py` — v16 chain + debt identity

**Files:**
- Create: `engine/spain.py`
- Modify: `tests/test_engine_spain.py` (append chain section)

**Interfaces:**
- Consumes: `engine.constants` (all Spain constants, `V0`, `BASE_LEVERS`, `load_central`, `load_olddep`), `engine.levers.Levers`.
- Produces (used by Tasks 7, 8, 10, 11, 12):
  - `Y0 = 2026`, `Y1 = 2050`, `N_YEARS = 25`, `YEARS: list[int]`
  - `SERIES_KEYS: list[str]` — the 40 v16 output keys, in v16 order
  - `french(principal: float, annual_rate_pct: float, n_months: int) -> float`
  - `run_scenario(levers: Levers) -> dict[str, list[float]]` — every key in `SERIES_KEYS`, each a list of 25 floats (2026…2050)
  - `baseline() -> dict[str, list[float]]` — `run_scenario(Levers())`

This is a line-faithful Python translation of v16 `run(L)` (extract L95-175). Variable names match the JS so the phase-2 JS engine can be diffed against it.

- [ ] **Step 1: Append failing tests to `tests/test_engine_spain.py`**

```python
# ---- Task 6: chain + debt identity + deviation semantics ----
from engine.spain import N_YEARS, SERIES_KEYS, Y0, baseline, french, run_scenario


def test_series_shape():
    run = run_scenario(Levers())
    assert len(SERIES_KEYS) == 40
    assert set(run) == set(SERIES_KEYS)
    for k in SERIES_KEYS:
        assert len(run[k]) == N_YEARS == 25


def test_deviation_semantics_base_levers_equal_baseline():
    # spec §4.1: baseline freezes the vintage; all levers at base -> zero deviation
    run = run_scenario(Levers())
    base = baseline()
    for k in SERIES_KEYS:
        assert run[k] == base[k], k
    assert all(v == 0.0 for v in run["lvl"])
    assert all(v == 10.1 for v in run["u"])       # V0.u, constant at base
    assert all(v == 3.0 for v in run["pi"])       # V0.pi
    assert all(v == 2.7 for v in run["g"])        # V0.g
    assert all(v == 3.42 for v in run["bono"])    # r + TERM + prima/100
    assert all(v == 100.0 for v in run["nomreal"])
    assert run["wrealIdx"][0] == 100.0


def test_debt_identity_reproduces_gold_central():
    # pre-A1: values measured while drafting (extract S3.1 rows L868-871):
    # 2026 106.316196 vs 106.32 | 2030 112.885096 vs 112.9
    # 2035 129.142456 vs 129.18 | 2050 223.841410 vs 223.86
    run = run_scenario(Levers())
    assert run["b"][2026 - Y0] == pytest.approx(106.316196, abs=1e-4)
    assert run["b"][2030 - Y0] == pytest.approx(112.885096, abs=1e-4)
    assert run["b"][2035 - Y0] == pytest.approx(129.142456, abs=1e-4)
    assert run["b"][2050 - Y0] == pytest.approx(223.841410, abs=1e-4)


def test_french_amortization():
    # extract L93 / L1012-1013: cuota = P*i/(1-(1+i)^-n), i = tipo/1200
    assert french(171444.46 * 0.8, 2.80 + 1.4757, 300) == pytest.approx(744.9991, abs=1e-3)


def test_lever_signs():
    base = baseline()
    k = 2035 - Y0
    assert run_scenario(Levers(r=4.8))["b"][k] > base["b"][k]        # dearer debt
    assert run_scenario(Levers(sp=1.0))["b"][k] < base["b"][k]       # consolidation
    assert run_scenario(Levers(sp=1.0))["u"][k] > base["u"][k]       # its social cost
    assert run_scenario(Levers(pm=50.0))["pi"][0] > base["pi"][0]    # pass-through
    assert run_scenario(Levers(lam=1.4))["wrealIdx"][k] > base["wrealIdx"][k]
    assert run_scenario(Levers(dem=0.6))["pens"][k] > base["pens"][k]
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_engine_spain.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.spain'`.

- [ ] **Step 3: Implement `engine/spain.py`**

```python
"""Spain semi-structural engine — faithful Python port of v16 `run(L)`
(docs/superpowers/plans/references/v16-engine-extract.md S1, L95-175).

Deviation semantics: the baseline freezes the vintage (gold central scenario +
V0 KPIs); the engine computes deviations from it. The baseline is NOT a
prediction. Debt identity: b_t = b_{t-1}(1+i)/(1+g) − sp, anchored to
gold_escenarios_deuda.csv (central). Variable names mirror the JS on purpose.
"""
from __future__ import annotations

from engine import constants as c
from engine.levers import Levers

Y0 = 2026
Y1 = 2050
N_YEARS = Y1 - Y0 + 1          # 25
YEARS = list(range(Y0, Y1 + 1))

# v16 R keys, in template order (extract L97-100)
SERIES_KEYS = [
    "lvl", "u", "pi", "g", "gnom", "wnom", "wreal", "wrealIdx", "b", "ief",
    "int", "pb", "saldo", "ipv", "precio", "cuota", "salmes", "salario", "esf",
    "pens", "dep", "arop", "edu", "d1", "nomreal", "p2", "d3", "p51", "gtot",
    "bls", "temp", "ujuv", "auton", "hip", "sobre", "bono", "spread", "r",
    "deficitAbs", "vida",
]


def french(principal: float, annual_rate_pct: float, n_months: int) -> float:
    """French amortization monthly payment (extract L93)."""
    i = annual_rate_pct / 1200.0
    return principal * i / (1 - (1 + i) ** (-n_months))


def run_scenario(levers: Levers) -> dict[str, list[float]]:
    L, B, V0 = levers, c.BASE_LEVERS, c.V0
    central, olddep = c.load_central(), c.load_olddep()
    R: dict[str, list[float]] = {k: [] for k in SERIES_KEYS}

    bono = L.r + c.TERM + L.prima / 100
    shock = (-(L.sp - B["sp"]) - c.E_R * (L.r - B["r"])
             + c.E_EXT * (L.ext - B["ext"]) - c.E_PM * (L.pm - B["pm"]))
    u_star_dev = c.A_Z * L.z + c.A_TAU * L.tau - c.A_LAM * (L.lam - B["lam"])

    lvl = 0.0; pi_dev = 0.0; di = 0.0
    b = central[Y0 - 1]["deuda"]                      # 105.6 (2025)
    sal_idx = 1.0; wr_idx = 1.0; pens_fac = 1.0; nom_idx = 1.0
    precio = V0["precio"]

    for k in range(N_YEARS):
        y = Y0 + k
        gc = central[y]
        prev = lvl
        lvl = c.RHO * lvl + (1 - c.RHO) * c.MULT * shock       # GDP level deviation (%)
        gap_u = c.OKUN * lvl                                    # slack: u below u*
        u = V0["u"] + u_star_dev - gap_u
        pi_dev = (c.THETA * pi_dev + c.KAPPA * gap_u
                  + c.GAMMA * (L.pm - B["pm"]) * c.PM_DECAY ** k)
        pi = V0["pi"] + pi_dev
        g = V0["g"] + (lvl - prev) + (L.lam - B["lam"])
        gnom = gc["g_nominal"] + (g - V0["g"]) + pi_dev

        # debt identity b_t = b_{t-1}(1+i)/(1+g) − sp, with 14 %/yr refinancing
        di = di + c.REFI * ((bono - V0["bono"]) - di)
        ief = gc["r_efectivo"] + di
        pb = gc["pb"] + L.sp - gc["presion_demog"] * L.dem
        b_prev = b
        b = b_prev * (1 + ief / 100) / (1 + gnom / 100) - pb
        intr = b_prev * ief / 100
        saldo = pb - intr

        # wage setting (WS)
        wnom = pi + L.lam + c.PHI * gap_u
        wreal = wnom - pi
        if k > 0:
            sal_idx *= 1 + wnom / 100
            wr_idx *= 1 + wreal / 100

        # housing
        ipv = (c.IPV_LR + (V0["ipv"] - c.IPV_LR) * c.IPV_REV ** k
               - c.E_IPV_R * (L.r - B["r"]) + c.E_IPV_G * (g - V0["g"]))
        if k > 0:
            precio *= 1 + ipv / 100
        cuota = french(precio * 0.8, L.r + c.DIFF, 300)
        salmes = V0["salmes"] * sal_idx
        esf = cuota / salmes * 100

        # pensions: mechanical identity pension x number / GDP
        if k > 0:
            pens_fac *= (1 + (pi + L.idx) / 100) / (1 + gnom / 100)
            nom_idx *= 1 + L.idx / 100
        dep_idx = 1 + (olddep[y] / olddep[Y0] - 1) * (1 + L.dem)
        dep = olddep[Y0] * dep_idx
        pens = V0["pens"] * dep_idx * pens_fac

        R["lvl"].append(lvl); R["u"].append(u); R["pi"].append(pi); R["g"].append(g)
        R["gnom"].append(gnom); R["wnom"].append(wnom); R["wreal"].append(wreal)
        R["wrealIdx"].append(wr_idx * 100); R["b"].append(b); R["ief"].append(ief)
        R["int"].append(intr); R["pb"].append(pb); R["saldo"].append(saldo)
        R["deficitAbs"].append(abs(min(0.0, saldo)))
        R["ipv"].append(ipv); R["precio"].append(precio); R["cuota"].append(cuota)
        R["salmes"].append(salmes); R["salario"].append(V0["salario"] * sal_idx)
        R["esf"].append(esf); R["pens"].append(pens); R["dep"].append(dep)
        R["nomreal"].append(nom_idx * 100)
        R["arop"].append(V0["arop"] + 0.55 * (u - V0["u"]) + 0.90 * L.sp)
        R["edu"].append(V0["edu"] - 0.090 * L.sp)
        R["d1"].append(V0["d1"] - 0.240 * L.sp)
        R["p2"].append(V0["p2"] - 0.125 * L.sp)
        R["d3"].append(V0["d3"] - 0.031 * L.sp)
        R["p51"].append(V0["p51"] - 0.145 * L.sp)
        R["gtot"].append(V0["gtot"] - 1.0 * L.sp)
        R["bls"].append(V0["bls"] + 12 * (L.r - B["r"]) + 2.5 * (u - V0["u"]))
        R["temp"].append(V0["temp"] + 0.25 * (u - V0["u"]) - 1.5 * L.z)
        R["ujuv"].append(c.RJUV * u)
        R["auton"].append(V0["auton"] + 0.12 * (u - V0["u"]) - 0.40 * (g - V0["g"]))
        R["hip"].append(max(0.0, V0["hip"] * (1 - 1.6 * (esf / (V0["cuota"] / V0["salmes"] * 100) - 1))))
        R["sobre"].append(V0["sobre"] + 0.18 * (esf - V0["cuota"] / V0["salmes"] * 100))
        R["bono"].append(bono); R["spread"].append(L.prima); R["r"].append(L.r)
        R["vida"].append(V0["vida"])
    return R


def baseline() -> dict[str, list[float]]:
    """The frozen-vintage baseline: all levers at base (cheap: 25 iterations)."""
    return run_scenario(Levers())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_engine_spain.py -v`
Expected: 13 passed.

- [ ] **Step 5: Commit**

```bash
git add engine/spain.py tests/test_engine_spain.py
git commit -m "feat: v16 Spain engine port — deviation chain and debt identity"
```

---

### Task 7: Persona static config + `persona_dependents`

**Files:**
- Modify: `engine/spain.py` (append `PERSONAS`, `PERSONA_IDS`, `persona_dependents`)
- Modify: `tests/test_engine_spain.py` (append persona section)

**Interfaces:**
- Consumes: `run_scenario` / `SERIES_KEYS` (Task 6).
- Produces (used by Tasks 11, 12):
  - `PERSONAS: list[dict]` — 12 entries `{"id","pill","foot","h1","meta","hot","series_keys","outs","headline","reds"}`; `outs` entries `{"k","lab"}`; `reds` entries `{"t","thr","k","cmp","d","x"}` (`thr`/`k`/`cmp`/`d` may be `None` for the two persona-07 data-gap rows)
  - `PERSONA_IDS: list[str]` — `["01", …, "12"]`
  - `persona_dependents(scenario: dict[str, list[float]]) -> dict[str, dict]` — keyed by persona id; values `{"pill": str, "headline": str, "series": dict[str, list[float]]}` where `series` holds the persona's five `outs` keys plus its `headline` key.

All Spanish strings below are verbatim from the extract S2 (P array, extract L516-841) and the v16 template persona blocks; reds from extract S7.1 (L1613-1648).

- [ ] **Step 1: Append failing tests to `tests/test_engine_spain.py`**

```python
# ---- Task 7: persona dependents ----
from engine.spain import PERSONA_IDS, PERSONAS, persona_dependents

EXPECTED_PILLS = ["💼 Bonista", "🏦 Banca", "🔑 Comprador", "🚀 Emprendedor",
                  "🏛️ Funcionario", "🗳️ Político", "🕳️ Corrupto", "🧒 Infancia",
                  "🌅 Jubilado", "🎓 Joven", "📋 Indefinido", "🧾 Autónomo"]


def test_twelve_personas_verbatim_identity():
    assert PERSONA_IDS == [f"{i:02d}" for i in range(1, 13)]
    assert [p["pill"] for p in PERSONAS] == EXPECTED_PILLS
    by_id = {p["id"]: p for p in PERSONAS}
    assert by_id["01"]["h1"] == "💼 Inversor en bonos: ¿me pagarán los 10 años?"
    assert by_id["08"]["h1"] == "🧒 ¿Qué país hereda quien hoy tiene 8 años?"
    assert by_id["12"]["foot"] == "🧾 autónomo"
    assert by_id["07"]["foot"] == "🕳️ político corrupto · sátira de transparencia"
    for p in PERSONAS:
        assert len(p["outs"]) == 5
        assert p["headline"] in [o["k"] for o in p["outs"]]
        assert len(p["reds"]) == 3
        for o in p["outs"]:
            assert o["k"] in SERIES_KEYS


def test_persona_dependents_shape():
    deps = persona_dependents(run_scenario(Levers()))
    assert sorted(deps) == PERSONA_IDS
    for pid, d in deps.items():
        assert set(d) == {"pill", "headline", "series"}
        assert d["headline"] in d["series"]
        for series in d["series"].values():
            assert len(series) == 25


# One pinned numeric check per persona at BASE levers. Values computed while
# drafting this plan by executing the verbatim v16 run() semantics (extract
# L95-175) against the committed gold slice; k is the year index (0=2026,
# 4=2030, 9=2035, 24=2050).
BASE_PINS = [
    ("01", "bono", 0, 3.42), ("01", "b", 24, 223.8414), ("01", "int", 4, 3.3436),
    ("02", "cuota", 0, 744.9971), ("02", "bls", 0, 10.0),
    ("03", "esf", 0, 42.5764), ("03", "precio", 4, 217954.5876),
    ("04", "g", 0, 2.7), ("04", "auton", 0, 14.5),
    ("05", "d1", 0, 10.9), ("05", "nomreal", 24, 100.0),
    ("06", "saldo", 4, -5.8136), ("06", "u", 0, 10.1),
    ("07", "p51", 0, 3.0), ("07", "p2", 0, 5.7), ("07", "d3", 0, 1.4),
    ("08", "arop", 0, 28.5), ("08", "edu", 0, 4.1), ("08", "dep", 24, 59.0),
    ("09", "pens", 9, 16.4858), ("09", "dep", 9, 41.7),
    ("10", "ujuv", 0, 23.4017), ("10", "temp", 0, 15.3),
    ("11", "wrealIdx", 4, 103.6489), ("11", "salario", 4, 28547.9608),
    ("12", "auton", 0, 14.5), ("12", "r", 0, 2.8),
]

# One pinned moved-lever check per persona (same provenance).
MOVED_PINS = [
    ("01", {"prima": 150.0}, "bono", 0, 4.47),
    ("02", {"r": 4.8}, "bls", 9, 35.4993),
    ("03", {"r": 4.8}, "esf", 9, 35.7009),
    ("04", {"ext": 3.0}, "lvl", 9, 0.4165),
    ("05", {"sp": 1.0}, "d1", 9, 10.66),
    ("06", {"sp": 1.0}, "b", 24, 210.3118),
    ("07", {"sp": 1.0}, "p51", 9, 2.855),
    ("08", {"sp": 1.0}, "arop", 9, 29.7665),
    ("09", {"idx": -0.5}, "nomreal", 9, 95.589),
    ("10", {"z": -1.0}, "temp", 9, 16.525),
    ("11", {"lam": 1.4}, "wrealIdx", 24, 139.6082),
    ("12", {"pm": 50.0}, "pi", 0, 5.2163),
]


@pytest.mark.parametrize("pid,key,k,expected", BASE_PINS)
def test_persona_base_pins(pid, key, k, expected):
    deps = persona_dependents(run_scenario(Levers()))
    assert deps[pid]["series"][key][k] == pytest.approx(expected, abs=1e-3)


@pytest.mark.parametrize("pid,moved,key,k,expected", MOVED_PINS)
def test_persona_moved_lever_pins(pid, moved, key, k, expected):
    deps = persona_dependents(run_scenario(Levers(**moved)))
    assert deps[pid]["series"][key][k] == pytest.approx(expected, abs=1e-3)
```

Note: `lvl` is not one of persona 04's five `outs` keys — `persona_dependents` includes each persona's `outs` keys, its `headline` key, and its `extra` list; persona 04 carries `"lvl"` in `extra` (v16's persona 04 narrative reads `R.lvl`, extract L622), persona 02 carries `["u", "esf"]`, persona 08 `["int"]`, persona 10 `["u"]`.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_engine_spain.py -v`
Expected: FAIL — `ImportError: cannot import name 'PERSONAS'`.

- [ ] **Step 3: Append to `engine/spain.py`**

```python
# --------------------------------------------------------------------------
# The 12 v15/v16 personas — static config verbatim from the v16 `const P`
# array (extract S2, L516-841). Spanish copy is NOT translated. reds from
# extract S7.1 (L1613-1648). `series_keys` = the persona's historical chart
# series in kpis_perfiles.json; `extra` = engine keys its narrative reads
# beyond the five outs.
PERSONAS: list[dict] = [
    {"id": "01", "pill": "💼 Bonista", "foot": "💼 bonista",
     "h1": "💼 Inversor en bonos: ¿me pagarán los 10 años?",
     "meta": "ecb_bono10y_es.csv · ecb_bono10y_de.csv · eurostat_gov_debt_es.csv · eurostat_gov_deficit_es.csv · interest_paid.csv · gold_escenarios_deuda.csv",
     "hot": ["r", "prima", "sp", "dem"], "series_keys": ["bono10y_es_5a"],
     "outs": [{"k": "bono", "lab": "Bono 10A España"}, {"k": "spread", "lab": "Spread ES–DE"},
              {"k": "b", "lab": "Deuda pública"}, {"k": "saldo", "lab": "Saldo público"},
              {"k": "int", "lab": "Intereses / PIB"}],
     "headline": "b", "extra": [],
     "reds": [
         {"t": "Deuda > 105 %PIB", "thr": 105.0, "k": "b", "cmp": "gt", "d": 1, "x": "narrativa crack23 [comentario]"},
         {"t": "Deuda > 120 %PIB", "thr": 120.0, "k": "b", "cmp": "gt", "d": 1, "x": "techo COVID 2020: 119,3 [hist]"},
         {"t": "Bono 10A > 7 %", "thr": 7.0, "k": "bono", "cmp": "gt", "d": 2, "x": "zona rescate: crisis 2012 [hist]"}]},
    {"id": "02", "pill": "🏦 Banca", "foot": "🏦 banca hipotecaria",
     "h1": "🏦 Banco hipotecario: ¿a quién presto, qué tipo y con qué mora esperada?",
     "meta": "ecb_euribor12m.csv · bls_criterios_vivienda.csv · ine_hipotecas_ccaa.csv · eurostat_hpi_q_es.csv · gold_cuota_teorica.csv",
     "hot": ["r", "z", "tau", "ext"], "series_keys": ["euribor12m_5a"],
     "outs": [{"k": "r", "lab": "Euríbor 12m"}, {"k": "bls", "lab": "BLS endurecimiento"},
              {"k": "hip", "lab": "Nueva producción"}, {"k": "ipv", "lab": "Precio vivienda a/a"},
              {"k": "cuota", "lab": "Cuota mediana"}],
     "headline": "cuota", "extra": ["u", "esf"],
     "reds": [
         {"t": "IPV real a/a > 10 %", "thr": 10.0, "k": "ipvreal", "cmp": "gt", "d": 1, "x": "burbuja 2004-07 [hist] · IPV nominal − IPCA"},
         {"t": "BLS endurecimiento > 20 %", "thr": 20.0, "k": "bls", "cmp": "gt", "d": 0, "x": "nivel de contracción de crédito [hist]"},
         {"t": "Paro > 15 % (motor de mora)", "thr": 15.0, "k": "u", "cmp": "gt", "d": 1, "x": "último nivel visto en 2021-07 (15,2) [hist]"}]},
    {"id": "03", "pill": "🔑 Comprador", "foot": "🔑 comprador de vivienda",
     "h1": "🔑 Comprador de vivienda: ¿qué esfuerzo me exige el techo?",
     "meta": "gold_cuota_teorica.csv · ine_salarios.csv (EAES) · ecb_euribor12m.csv · eurostat_hpi_q_es.csv · eurostat_overburden_es.csv",
     "hot": ["r", "lam", "z", "pm"], "series_keys": ["vivienda_precio_yoy_5a"],
     "outs": [{"k": "precio", "lab": "Precio mediano CCAA"}, {"k": "cuota", "lab": "Cuota mediana"},
              {"k": "esf", "lab": "Esfuerzo cuota/renta"}, {"k": "ipv", "lab": "Precio vivienda a/a"},
              {"k": "sobre", "lab": "Sobrecarga vivienda"}],
     "headline": "esf", "extra": [],
     "reds": [
         {"t": "Esfuerzo cuota/renta > 35 %", "thr": 35.0, "k": "esf", "cmp": "gt", "d": 1, "x": "regla prudencial [regla]"},
         {"t": "Sobrecarga > 40 % renta", "thr": 15.0, "k": "sobre", "cmp": "gt", "d": 1, "x": "definición Eurostat · muerde al flujo nuevo [UE]"},
         {"t": "IPV a/a > 10 %", "thr": 10.0, "k": "ipv", "cmp": "gt", "d": 1, "x": "burbuja 2004-07 [hist]"}]},
    {"id": "04", "pill": "🚀 Emprendedor", "foot": "🚀 emprendedor",
     "h1": "🚀 ¿Aguanta el ciclo lo que tarda mi empresa en nacer?",
     "meta": "eurostat_gdp_q_es.csv · eurostat_hicp_manr_es.csv · ecb_euribor12m.csv · eurostat_une_rt_m_es.csv · wb_self_employment.csv",
     "hot": ["r", "ext", "pm", "sp"], "series_keys": ["pib_yoy_5a"],
     "outs": [{"k": "g", "lab": "Ciclo · PIB real"}, {"k": "u", "lab": "Paro · talento"},
              {"k": "pi", "lab": "IPCA · coste inputs"}, {"k": "r", "lab": "Euríbor · financiación"},
              {"k": "auton", "lab": "Autoempleo"}],
     "headline": "g", "extra": ["lvl"],
     "reds": [
         {"t": "PIB a/a < 0 %", "thr": 0.0, "k": "g", "cmp": "lt", "d": 1, "x": "recesión técnica [regla]"},
         {"t": "IPCA > 4 % sostenido", "thr": 4.0, "k": "pi", "cmp": "gt", "d": 1, "x": "episodio 2022: pico 10,7 % (jul-2022) [hist]"},
         {"t": "Euríbor 12m > 4 %", "thr": 4.0, "k": "r", "cmp": "gt", "d": 2, "x": "techo del ciclo de subidas 2023 [hist]"}]},
    {"id": "05", "pill": "🏛️ Funcionario", "foot": "🏛️ funcionario",
     "h1": "🏛️ ¿Mi nómina real sobrevive al ajuste que viene?",
     "meta": "gov_10a_exp.csv · eurostat_gov_deficit_es.csv · eurostat_gov_debt_es.csv · eurostat_hicp_manr_es.csv",
     "hot": ["sp", "idx", "pm", "dem"], "series_keys": ["deficit_pib_hist"],
     "outs": [{"k": "d1", "lab": "Masa salarial D1"}, {"k": "nomreal", "lab": "Poder de compra nómina"},
              {"k": "pi", "lab": "IPCA · erosión"}, {"k": "saldo", "lab": "Saldo público"},
              {"k": "gtot", "lab": "Gasto total AAPP"}],
     "headline": "nomreal", "extra": [],
     "reds": [
         {"t": "Déficit > 3 % PIB", "thr": -3.0, "k": "saldo", "cmp": "lt", "d": 1, "x": "regla fiscal [UE]"},
         {"t": "Deuda > 105 % PIB", "thr": 105.0, "k": "b", "cmp": "gt", "d": 1, "x": "narrativa crack23 [comentario]"},
         {"t": "Poder de compra < 100", "thr": 100.0, "k": "nomreal", "cmp": "lt", "d": 1, "x": "episodios 2010-15 [hist]"}]},
    {"id": "06", "pill": "🗳️ Político", "foot": "🗳️ político (decisor honesto)",
     "h1": "🗳️ ¿Qué palanca puedo mover sin cruzar una línea roja?",
     "meta": "eurostat_gov_debt_es · eurostat_gov_deficit_es · eurostat_une_rt_m_es · eurostat_gdp_q_es · interest_paid · gold_escenarios_deuda",
     "hot": ["sp", "r", "tau", "z", "lam", "dem"], "series_keys": ["deficit_pib_hist"],
     "outs": [{"k": "b", "lab": "Deuda pública"}, {"k": "saldo", "lab": "Saldo público"},
              {"k": "u", "lab": "Paro total"}, {"k": "g", "lab": "PIB real"},
              {"k": "int", "lab": "Intereses"}],
     "headline": "b", "extra": [],
     "reds": [
         {"t": "Deuda > 120 % PIB", "thr": 120.0, "k": "b", "cmp": "gt", "d": 1, "x": "techo COVID 2020: 119,3 [hist]"},
         {"t": "Déficit > 3 % PIB", "thr": -3.0, "k": "saldo", "cmp": "lt", "d": 1, "x": "regla fiscal UE [UE]"},
         {"t": "Paro > 15 %", "thr": 15.0, "k": "u", "cmp": "gt", "d": 1, "x": "coste social de consolidar [hist]"}]},
    {"id": "07", "pill": "🕳️ Corrupto", "foot": "🕳️ político corrupto · sátira de transparencia",
     "h1": "🕳️ ¿Dónde no mira nadie? — las partidas con más discrecionalidad, señaladas para quien SÍ mira",
     "meta": "gov_10a_exp.csv (P2 · D3 · P51G) · interest_paid.csv",
     "hot": ["sp", "dem"], "series_keys": ["inversion_publica_pib_hist"],
     "outs": [{"k": "p2", "lab": "Consumo intermedio P2"}, {"k": "d3", "lab": "Subvenciones D3"},
              {"k": "p51", "lab": "Inversión pública P51G"}, {"k": "gtot", "lab": "Gasto total"},
              {"k": "int", "lab": "Intereses D41"}],
     "headline": "p51", "extra": [],
     "reds": [
         {"t": "Contratos menores · adjudicación", "thr": None, "k": None, "cmp": None, "d": None, "x": "la señal vive a nivel de contrato — sin serie pública [hueco de datos]"},
         {"t": "WGI control de la corrupción", "thr": None, "k": None, "cmp": None, "d": None, "x": "API archivada: descarga manual en govindicators.org [hueco de datos]"},
         {"t": "Inversión pública < 2 % PIB", "thr": 2.0, "k": "p51", "cmp": "lt", "d": 2, "x": "cruzada en 2016-17 (2,0): obra parada = renegociación [hist]"}]},
    {"id": "08", "pill": "🧒 Infancia", "foot": "🧒 infancia",
     "h1": "🧒 ¿Qué país hereda quien hoy tiene 8 años?",
     "meta": "eurostat_arop_child_es · eurostat_gov_edu_es · eurostat_gov_debt_es · gold_projections · gold_escenarios_deuda",
     "hot": ["sp", "dem", "z", "lam"], "series_keys": ["arop_infantil_hist"],
     "outs": [{"k": "arop", "lab": "AROP infantil (<16)"}, {"k": "edu", "lab": "Gasto en educación"},
              {"k": "b", "lab": "Deuda heredada"}, {"k": "dep", "lab": "Dependencia 65+"},
              {"k": "vida", "lab": "Esperanza de vida"}],
     "headline": "b", "extra": ["int"],
     "reds": [
         {"t": "AROP infantil > 25 %", "thr": 25.0, "k": "arop", "cmp": "gt", "d": 1, "x": "peor cuartil UE — cruzada de forma persistente [UE]"},
         {"t": "Educación < 4,8 % PIB (UE27)", "thr": 4.8, "k": "edu", "cmp": "lt", "d": 2, "x": "0,7 pp por debajo de la media UE27 [UE]"},
         {"t": "Dependencia > 50/100", "thr": 50.0, "k": "dep", "cmp": "gt", "d": 1, "x": "sin precedente histórico [hist inédito]"}]},
    {"id": "09", "pill": "🌅 Jubilado", "foot": "🌅 jubilado",
     "h1": "🌅 ¿Mi pensión sigue al IPC — y quién la paga en 2035?",
     "meta": "eurostat_pensions_pcgdp_es.csv · eurostat_hicp_manr_es.csv · gold_projections.csv · life_expectancy_e0.csv",
     "hot": ["idx", "dem", "pm", "sp"], "series_keys": ["hicp_es_5a"],
     "outs": [{"k": "pens", "lab": "Gasto en pensiones"}, {"k": "nomreal", "lab": "Poder de compra"},
              {"k": "pi", "lab": "IPCA · la referencia"}, {"k": "dep", "lab": "Dependencia 65+"},
              {"k": "vida", "lab": "Esperanza de vida"}],
     "headline": "pens", "extra": [],
     "reds": [
         {"t": "Gasto pensiones > 15 % PIB", "thr": 15.0, "k": "pens", "cmp": "gt", "d": 2, "x": "nunca alcanzado en la serie [hist inédito]"},
         {"t": "Dependencia 65+ > 50/100", "thr": 50.0, "k": "dep", "cmp": "gt", "d": 1, "x": "se cruza entre 2035 y 2050 [hist inédito]"},
         {"t": "Poder de compra < 100", "thr": 100.0, "k": "nomreal", "cmp": "lt", "d": 1, "x": "la palanca ι es la que decide, no el IPC [regla]"}]},
    {"id": "10", "pill": "🎓 Joven", "foot": "🎓 joven que entra al mercado laboral",
     "h1": "🎓 ¿Primer contrato o cola del paro — y podré irme de casa?",
     "meta": "eurostat_une_rt_m_es.csv · eurostat_temp_share_es.csv · eurostat_hpi_q_es.csv · eurostat_overburden_es.csv · ine_salarios.csv",
     "hot": ["z", "tau", "ext", "r", "sp"], "series_keys": ["paro_juvenil_5a", "paro_total_5a"],
     "outs": [{"k": "ujuv", "lab": "Paro juvenil <25"}, {"k": "temp", "lab": "Temporalidad"},
              {"k": "ipv", "lab": "Precio vivienda a/a"}, {"k": "sobre", "lab": "Sobrecarga vivienda"},
              {"k": "salario", "lab": "Salario medio"}],
     "headline": "ujuv", "extra": ["u"],
     "reds": [
         {"t": "Paro juvenil > 40 %", "thr": 40.0, "k": "ujuv", "cmp": "gt", "d": 1, "x": "cota del ciclo anterior; 2013 la superó [hist]"},
         {"t": "Temporalidad > 25 %", "thr": 25.0, "k": "temp", "cmp": "gt", "d": 1, "x": "nivel pre-reforma 2022-Q1 [hist]"},
         {"t": "IPV > +10 % a/a", "thr": 10.0, "k": "ipv", "cmp": "gt", "d": 1, "x": ">10 % anual aleja la emancipación [hist]"}]},
    {"id": "11", "pill": "📋 Indefinido", "foot": "📋 trabajador indefinido",
     "h1": "📋 ¿Crece mi salario por encima del IPC?",
     "meta": "ine_salarios.csv · eurostat_hicp_manr_es.csv · eurostat_une_rt_m_es.csv · eurostat_temp_share_es.csv · eurostat_gdp_q_es.csv",
     "hot": ["lam", "z", "pm", "tau"], "series_keys": ["hicp_es_5a"],
     "outs": [{"k": "wrealIdx", "lab": "Salario real acumulado"}, {"k": "salario", "lab": "Salario medio"},
              {"k": "pi", "lab": "IPCA · el listón"}, {"k": "u", "lab": "Paro total"},
              {"k": "temp", "lab": "Temporalidad"}],
     "headline": "wrealIdx", "extra": [],
     "reds": [
         {"t": "IPCA > 4 % sostenido", "thr": 4.0, "k": "pi", "cmp": "gt", "d": 1, "x": "episodios de erosión 2022-23 [hist]"},
         {"t": "Paro > 15 %", "thr": 15.0, "k": "u", "cmp": "gt", "d": 1, "x": "el poder insider se sostiene bajo el 15 % [hist]"},
         {"t": "Salario real < 100", "thr": 100.0, "k": "wrealIdx", "cmp": "lt", "d": 1, "x": "perder poder de compra desde 2026 [regla]"}]},
    {"id": "12", "pill": "🧾 Autónomo", "foot": "🧾 autónomo",
     "h1": "🧾 ¿Caja, cuota y ciclo — en qué orden me golpean?",
     "meta": "wb_self_employment.csv · eurostat_gdp_q_es.csv · eurostat_hicp_manr_es.csv · ecb_euribor12m.csv · eurostat_une_rt_m_es.csv",
     "hot": ["r", "pm", "ext", "sp"], "series_keys": ["autoempleo_hist"],
     "outs": [{"k": "auton", "lab": "Autoempleo"}, {"k": "g", "lab": "Ciclo · demanda"},
              {"k": "pi", "lab": "IPCA · coste inputs"}, {"k": "r", "lab": "Euríbor · póliza"},
              {"k": "u", "lab": "Paro · repliegue"}],
     "headline": "g", "extra": [],
     "reds": [
         {"t": "PIB a/a < 0 %", "thr": 0.0, "k": "g", "cmp": "lt", "d": 1, "x": "recesión técnica [regla]"},
         {"t": "IPCA > 4 % sostenido", "thr": 4.0, "k": "pi", "cmp": "gt", "d": 1, "x": "episodio 2022: 10,7 [hist]"},
         {"t": "Euríbor 12m > 4 %", "thr": 4.0, "k": "r", "cmp": "gt", "d": 2, "x": "techo del ciclo 2023 [hist]"}]},
]

PERSONA_IDS = [p["id"] for p in PERSONAS]


def persona_dependents(scenario: dict[str, list[float]]) -> dict[str, dict]:
    """Per-persona headline series (spec §4.1): dict keyed by the 12 persona ids."""
    out: dict[str, dict] = {}
    for p in PERSONAS:
        keys = [o["k"] for o in p["outs"]] + [p["headline"]] + p["extra"]
        seen: list[str] = []
        for k in keys:
            if k not in seen:
                seen.append(k)
        out[p["id"]] = {"pill": p["pill"], "headline": p["headline"],
                        "series": {k: scenario[k] for k in seen}}
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_engine_spain.py -v`
Expected: 54 passed (13 prior + 2 persona shape tests + 27 base pins + 12 moved pins).

- [ ] **Step 5: Commit**

```bash
git add engine/spain.py tests/test_engine_spain.py
git commit -m "feat: 12 v15/v16 personas — static config and persona_dependents with pinned values"
```

---

### Task 8: `engine/montecarlo.py` — stochastic DSA to 2070

**Files:**
- Create: `engine/montecarlo.py`
- Test: `tests/test_montecarlo.py` (new)

**Interfaces:**
- Consumes: `engine.constants` (MC_* constants, Spain chain constants, `V0`, `BASE_LEVERS`, `load_central`), `engine.levers.Levers`.
- Produces (used by Tasks 10, 12):
  - `@dataclass McResult`: `years: list[int]` (2026…2070), `percentiles: dict[str, list[float]]` (keys `"p5","p25","p50","p75","p95"`), `n_paths: int`, `seed: int`
  - `mc_input_paths(levers: Levers) -> tuple[list[int], np.ndarray, np.ndarray, np.ndarray]` — deterministic (years, ief, gnom, pb) to 2070 under the levers
  - `run_montecarlo(levers: Levers = Levers(), n_paths: int = 4000, seed: int = 42) -> McResult`

Design (plan_maestro-style, spec §4.3): normal AR(1) shocks on the effective rate, nominal growth and the primary balance around the deterministic path; the central path is the gold central scenario to 2050 extended linearly to 2070; a small piecewise pb drift and an asymmetric fiscal-reaction term are calibration constants fitted (while drafting this plan) so the seed-42 / 4000-path envelope reproduces the inherited gold fan: max |dev| vs gold p5/p50/p95 at 2030/2050/2070 = **1.399 pp** (tolerance ±2 pp), runtime 0.04 s. Verified seed-42 values: 2030 p5/p50/p95 = 107.2674 / 113.3000 / 119.7131; 2050 = 176.4991 / 231.2999 / 303.8985; 2070 = 271.9047 / 408.8999 / 619.4770 (gold: 106.9/113.3/120.2, 177.7/231.3/302.5, 271.8/408.9/618.5 — extract L899-901).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_montecarlo.py`:

```python
"""Monte Carlo DSA tests (spec §7): seeded reproducibility, percentile
ordering, envelope tolerance vs the gold fan."""
import csv
import time

from engine.constants import GOLD_DIR
from engine.levers import Levers
from engine.montecarlo import McResult, run_montecarlo

PCTS = ("p5", "p25", "p50", "p75", "p95")


def _gold_central_mc() -> dict[int, dict[str, float]]:
    out = {}
    with (GOLD_DIR / "gold_escenarios_deuda_mc.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["escenario"] == "central":
                out[int(float(row["year"]))] = {p: float(row[p]) for p in PCTS}
    return out


def test_shape_and_years():
    mc = run_montecarlo(Levers(), n_paths=500, seed=1)
    assert isinstance(mc, McResult)
    assert mc.years == list(range(2026, 2071))
    assert set(mc.percentiles) == set(PCTS)
    assert all(len(v) == 45 for v in mc.percentiles.values())
    assert (mc.n_paths, mc.seed) == (500, 1)


def test_seeded_reproducibility():
    a = run_montecarlo(Levers(), n_paths=500, seed=7)
    b = run_montecarlo(Levers(), n_paths=500, seed=7)
    c = run_montecarlo(Levers(), n_paths=500, seed=8)
    assert a.percentiles == b.percentiles
    assert a.percentiles != c.percentiles


def test_percentile_ordering():
    mc = run_montecarlo(Levers(), n_paths=1000, seed=3)
    for i in range(45):
        vals = [mc.percentiles[p][i] for p in PCTS]
        assert vals == sorted(vals), mc.years[i]


def test_envelope_matches_gold_within_2pp():
    # A5 pre-check (also in tests/test_anchors.py): seed 42, 4000 paths
    mc = run_montecarlo(Levers(), n_paths=4000, seed=42)
    gold = _gold_central_mc()
    for y in (2030, 2050, 2070):
        i = y - 2026
        for p in ("p5", "p50", "p95"):
            assert abs(mc.percentiles[p][i] - gold[y][p]) <= 2.0, (y, p)


def test_levers_shift_the_fan():
    base = run_montecarlo(Levers(), n_paths=1000, seed=5)
    s1 = run_montecarlo(Levers(r=4.8), n_paths=1000, seed=5)   # S1 tipos +200 pb
    i = 2050 - 2026
    assert s1.percentiles["p50"][i] > base.percentiles["p50"][i] + 20


def test_runtime_under_one_second():
    start = time.perf_counter()
    run_montecarlo(Levers(), n_paths=4000, seed=42)
    assert time.perf_counter() - start < 1.0     # spec §4.3 target (measured 0.04 s)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_montecarlo.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.montecarlo'`.

- [ ] **Step 3: Implement `engine/montecarlo.py`**

```python
"""Stochastic DSA (spec §4.3) — plan_maestro-style Monte Carlo around the
deterministic path: normal AR(1) shocks on r, g and sp, 4,000 paths to 2070.

The deterministic backbone applies the same lever-deviation chain as
engine/spain.py to the gold central scenario, extended past 2050 with the
MC_EXT_* slopes. MC_PB_DRIFT and the MC_FB_* fiscal-reaction terms are
calibration constants fitted so the seed-42/4000-path envelope reproduces the
inherited gold fan (gold_escenarios_deuda_mc.csv central) within ±2 pp at
2030/2050/2070 — the fan is a calibrated reproduction of plan_maestro's
stochastic identity, not a new forecasting claim.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from engine import constants as c
from engine.levers import Levers


@dataclass
class McResult:
    years: list[int]
    percentiles: dict[str, list[float]]
    n_paths: int
    seed: int


_PCT_LEVELS = (5, 25, 50, 75, 95)


def mc_input_paths(levers: Levers) -> tuple[list[int], np.ndarray, np.ndarray, np.ndarray]:
    """Deterministic (years, ief, gnom, pb) to 2070 under `levers`.

    Mirrors the engine/spain.py deviation chain (extract L95-175) for the three
    debt-identity inputs, over 45 years instead of 25.
    """
    L, B, V0 = levers, c.BASE_LEVERS, c.V0
    central = c.load_central()
    years = list(range(c.MC_START_YEAR, c.MC_HORIZON + 1))

    bono = L.r + c.TERM + L.prima / 100
    shock = (-(L.sp - B["sp"]) - c.E_R * (L.r - B["r"])
             + c.E_EXT * (L.ext - B["ext"]) - c.E_PM * (L.pm - B["pm"]))

    ief, gnom, pb = [], [], []
    lvl = pi_dev = di = 0.0
    for k, y in enumerate(years):
        if y <= 2050:
            c_r, c_g = central[y]["r_efectivo"], central[y]["g_nominal"]
            c_pb, c_dm = central[y]["pb"], central[y]["presion_demog"]
        else:
            c_r = central[2050]["r_efectivo"] + c.MC_EXT_SLOPE_R * (y - 2050)
            c_g = central[2050]["g_nominal"]
            c_pb = central[2050]["pb"] + c.MC_EXT_SLOPE_PB * (y - 2050)
            c_dm = central[2050]["presion_demog"] + c.MC_EXT_SLOPE_DEMOG * (y - 2050)
        prev = lvl
        lvl = c.RHO * lvl + (1 - c.RHO) * c.MULT * shock
        gap_u = c.OKUN * lvl
        pi_dev = (c.THETA * pi_dev + c.KAPPA * gap_u
                  + c.GAMMA * (L.pm - B["pm"]) * c.PM_DECAY ** k)
        g = V0["g"] + (lvl - prev) + (L.lam - B["lam"])
        di = di + c.REFI * ((bono - V0["bono"]) - di)
        drift = (c.MC_PB_DRIFT[0] if y <= 2030
                 else c.MC_PB_DRIFT[1] if y <= 2050 else c.MC_PB_DRIFT[2])
        ief.append(c_r + di)
        gnom.append(c_g + (g - V0["g"]) + pi_dev)
        pb.append(c_pb + L.sp - c_dm * L.dem + drift)
    return years, np.asarray(ief), np.asarray(gnom), np.asarray(pb)


def run_montecarlo(levers: Levers = Levers(), n_paths: int = c.MC_N_PATHS,
                   seed: int = c.MC_SEED_DEFAULT) -> McResult:
    years, ief, gnom, pb = mc_input_paths(levers)
    b0 = c.load_central()[c.MC_START_YEAR - 1]["deuda"]     # 105.6 (2025)

    # deterministic reference path (anchor for the fiscal-reaction brake)
    b_det: list[float] = []
    b = b0
    for i in range(len(years)):
        b = b * (1 + ief[i] / 100) / (1 + gnom[i] / 100) - pb[i]
        b_det.append(b)

    rng = np.random.default_rng(seed)
    paths = np.full(n_paths, b0, dtype=float)
    b_det_prev = b0
    e_r = np.zeros(n_paths); e_g = np.zeros(n_paths); e_sp = np.zeros(n_paths)
    percentiles: dict[str, list[float]] = {f"p{p}": [] for p in _PCT_LEVELS}
    for i in range(len(years)):
        e_r = c.MC_RHO * e_r + rng.normal(0.0, c.MC_SIG_R, n_paths)
        e_g = c.MC_RHO * e_g + rng.normal(0.0, c.MC_SIG_G, n_paths)
        e_sp = c.MC_RHO * e_sp + rng.normal(0.0, c.MC_SIG_SP, n_paths)
        dev = paths - b_det_prev
        pb_eff = (pb[i] + e_sp + c.MC_FB_UP * np.maximum(0.0, dev)
                  + c.MC_FB_DN * np.minimum(0.0, dev))
        paths = (paths * (1 + (ief[i] + e_r) / 100) / (1 + (gnom[i] + e_g) / 100)
                 - pb_eff)
        b_det_prev = b_det[i]
        q = np.percentile(paths, _PCT_LEVELS)
        for j, p in enumerate(_PCT_LEVELS):
            percentiles[f"p{p}"].append(float(q[j]))
    return McResult(years=years, percentiles=percentiles, n_paths=n_paths, seed=seed)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_montecarlo.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add engine/montecarlo.py tests/test_montecarlo.py
git commit -m "feat: Monte Carlo DSA to 2070 calibrated to the inherited gold fan"
```

---

### Task 9: `engine/redlines.py` — red-line definitions + evaluator

**Files:**
- Create: `engine/redlines.py`
- Test: `tests/test_redlines.py` (new)

**Interfaces:**
- Consumes: nothing beyond a scenario dict (Task 6 shape).
- Produces (used by Tasks 11, 12):
  - `NEAR_FRACTION = 0.10`
  - `RED_LINES: list[dict]` — 9 entries `{"id","label","series","threshold","cmp","source"}` (spec §4.5 set)
  - `evaluate_redlines(scenario: dict[str, list[float]], k: int) -> list[dict]` — entries `{"id","label","series","value","threshold","cmp","status","source"}` with `status ∈ {"crossed","near","safe"}`, computed — never hand-written (v16 "semáforo vivo" rule).

Status rule (spec §4.5): `crossed` when the comparison trips (`gt`: value > threshold; `lt`: value < threshold); else `near` when `|value − threshold| <= NEAR_FRACTION * |threshold|` (for the `g < 0` line, whose threshold is 0, `near` uses an absolute band of 0.5 pp); else `safe`. Note: v16's `statusOf` used a 12 % band (extract L337-344); the spec's 10 % overrides it for this global evaluator — documented deviation.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_redlines.py`:

```python
"""Red-line evaluation (spec §4.5 / §7): crossed / near / safe against known scenarios."""
from engine.levers import Levers, preset_levers
from engine.redlines import NEAR_FRACTION, RED_LINES, evaluate_redlines
from engine.spain import Y0, run_scenario


def _status(results, rid):
    return next(r["status"] for r in results if r["id"] == rid)


def test_definitions_complete():
    assert NEAR_FRACTION == 0.10
    assert [r["id"] for r in RED_LINES] == [
        "bono_rescate", "paro_record", "deficit_maastricht", "deficit_suelo_2009",
        "deuda_105", "deuda_120", "inflacion_10", "esfuerzo_40", "pobreza_infantil_30"]
    for r in RED_LINES:
        assert r["cmp"] in ("gt", "lt") and r["source"].strip()


def test_base_2026_statuses_are_computed():
    # base run at k=0 (2026): b=106.3162, saldo=-4.1801, esf=42.5764, arop=28.5,
    # bono=3.42, u=10.1, pi=3.0 (values from the Task 6/7 pinned battery)
    res = evaluate_redlines(run_scenario(Levers()), 0)
    assert _status(res, "deuda_105") == "crossed"          # 106.32 > 105
    assert _status(res, "deuda_120") == "safe"             # |106.32-120|=13.68 > 12
    assert _status(res, "deficit_maastricht") == "crossed" # -4.18 < -3
    assert _status(res, "deficit_suelo_2009") == "safe"
    assert _status(res, "esfuerzo_40") == "crossed"        # 42.58 > 40
    assert _status(res, "pobreza_infantil_30") == "near"   # |28.5-30|=1.5 <= 3.0
    assert _status(res, "bono_rescate") == "safe"
    assert _status(res, "paro_record") == "safe"
    assert _status(res, "inflacion_10") == "safe"


def test_s7_adverse_2050_crossings():
    # S7 at k=24 (2050): b=349.7973, saldo=-28.7937, bono=6.47 (drafting probe)
    res = evaluate_redlines(run_scenario(preset_levers("S7")), 2050 - Y0)
    assert _status(res, "deuda_105") == "crossed"
    assert _status(res, "deuda_120") == "crossed"
    assert _status(res, "deficit_suelo_2009") == "crossed"
    assert _status(res, "bono_rescate") == "near"          # |6.47-7| = 0.53 <= 0.70


def test_every_status_is_computed_value():
    res = evaluate_redlines(run_scenario(Levers()), 24)
    for r in res:
        assert set(r) == {"id", "label", "series", "value", "threshold", "cmp",
                          "status", "source"}
        assert r["status"] in ("crossed", "near", "safe")
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_redlines.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.redlines'`.

- [ ] **Step 3: Implement `engine/redlines.py`**

```python
"""v12 empirically-anchored red lines as data + evaluator (spec §4.5).

Thresholds and anchors from design/v12_limites_fuentes.md (extract S7.2,
L1655-1691). Statuses are COMPUTED from the scenario — never hand-written
(v16 'semáforo vivo' rule). near = within 10 % of the threshold (spec §4.5;
v16's statusOf used 12 % — the spec overrides for this global evaluator).
"""
from __future__ import annotations

NEAR_FRACTION = 0.10
_ZERO_THRESHOLD_BAND = 0.5   # pp — absolute near-band for the g < 0 line

RED_LINES: list[dict] = [
    {"id": "bono_rescate", "label": "Bono 10A > 7 %", "series": "bono",
     "threshold": 7.0, "cmp": "gt",
     "source": "zona rescate: GRC/PRT/IRL pidieron rescate con bonos ≈7 %; ES tocó 7,6 % en jul-2012 [hist]"},
    {"id": "paro_record", "label": "Paro > 26,9 %", "series": "u",
     "threshold": 26.9, "cmp": "gt",
     "source": "máximo histórico ES (T1-2013) [hist]"},
    {"id": "deficit_maastricht", "label": "Déficit > 3 % PIB", "series": "saldo",
     "threshold": -3.0, "cmp": "lt", "source": "umbral Maastricht [regla UE]"},
    {"id": "deficit_suelo_2009", "label": "Déficit > 11,3 % PIB", "series": "saldo",
     "threshold": -11.3, "cmp": "lt", "source": "suelo 2009: ES −11,3 % PIB [hist]"},
    {"id": "deuda_105", "label": "Deuda > 105 % PIB", "series": "b",
     "threshold": 105.0, "cmp": "gt",
     "source": "crack23: «deuda brutal que ya está por encima del 105 %» [comentario]"},
    {"id": "deuda_120", "label": "Deuda > 120 % PIB", "series": "b",
     "threshold": 120.0, "cmp": "gt", "source": "≈ pico COVID ES 2020: 119,3 [hist]"},
    {"id": "inflacion_10", "label": "Inflación > 10 %", "series": "pi",
     "threshold": 10.0, "cmp": "gt",
     "source": "ola inflacionaria 2022: ES pico 10,8 % jul-2022 [hist]"},
    {"id": "esfuerzo_40", "label": "Esfuerzo vivienda > 40 %", "series": "esf",
     "threshold": 40.0, "cmp": "gt",
     "source": "definición Eurostat de sobrecarga (housing cost overburden) [UE]"},
    {"id": "pobreza_infantil_30", "label": "Pobreza infantil > 30 %", "series": "arop",
     "threshold": 30.0, "cmp": "gt",
     "source": "ES 27–28 % crónico, 30 % en picos post-2013; media UE ≈19 % [hist]"},
]


def evaluate_redlines(scenario: dict[str, list[float]], k: int) -> list[dict]:
    """Evaluate every red line at year index k. Returns computed statuses."""
    out = []
    for rl in RED_LINES:
        value = scenario[rl["series"]][k]
        thr = rl["threshold"]
        crossed = value > thr if rl["cmp"] == "gt" else value < thr
        band = NEAR_FRACTION * abs(thr) if thr != 0 else _ZERO_THRESHOLD_BAND
        status = "crossed" if crossed else ("near" if abs(value - thr) <= band else "safe")
        out.append({"id": rl["id"], "label": rl["label"], "series": rl["series"],
                    "value": value, "threshold": thr, "cmp": rl["cmp"],
                    "status": status, "source": rl["source"]})
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_redlines.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add engine/redlines.py tests/test_redlines.py
git commit -m "feat: v12 red lines as data with computed crossed/near/safe evaluator"
```

---

### Task 10: Anchor battery A1–A5 + committed fixture generator

**Files:**
- Create: `scripts/generate_anchor_fixture.py`
- Create: `tests/fixtures/engine_anchors.json` (generated by the script, then committed)
- Test: `tests/test_anchors.py` (new)

**Interfaces:**
- Consumes: `run_scenario`, `SERIES_KEYS`, `Y0` (Task 6), `Levers`, `PRESETS`, `preset_levers`, `LEVER_SPECS` (Task 5), `run_montecarlo` (Task 8), `load_central`, `GOLD_DIR`, `VINTAGE` (Task 4).
- Produces: `tests/fixtures/engine_anchors.json` — the dual-engine contract phase 2's JS engine tests must also satisfy (spec §4.2). Regeneration command: `.venv/bin/python scripts/generate_anchor_fixture.py`.

- [ ] **Step 1: Write the failing anchor tests**

Create `tests/test_anchors.py`:

```python
"""A1-A5 anchor battery (spec §4.2). Failure of ANY test here is a build failure."""
import csv
import json
import math
from pathlib import Path

import pytest

from engine.constants import GOLD_DIR, load_central
from engine.levers import LEVER_SPECS, Levers, PRESETS, preset_levers
from engine.montecarlo import run_montecarlo
from engine.spain import SERIES_KEYS, Y0, run_scenario

FIXTURE = Path(__file__).parent / "fixtures" / "engine_anchors.json"
ANCHOR_YEARS = [2026, 2030, 2035, 2050]

# A3 probe values — one in-range non-base value per lever
PROBE = {"r": 4.8, "prima": 150.0, "sp": 1.0, "lam": 1.4, "pm": 50.0,
         "tau": 1.5, "z": -1.0, "ext": 3.0, "dem": 0.6, "idx": -0.5}


def test_a1_debt_identity_reproduces_gold_central_to_the_decimal():
    # v16 AC-V3. Tolerance 0.05 = half a printed decimal: the CSV rounds deuda
    # AND its pb/r_efectivo inputs, so exact-to-machine equality is impossible
    # by construction. Measured drift while drafting: 2026 −0.0038, 2030
    # −0.0149, 2035 −0.0375, 2050 −0.0186 (extract S3.1 rows, L868-871).
    base = run_scenario(Levers())
    central = load_central()
    for y in ANCHOR_YEARS:
        assert abs(base["b"][y - Y0] - central[y]["deuda"]) <= 0.05, y


def test_a2_french_amortization_reproduces_gold_cuota():
    # gold_cuota_teorica.csv row-wise median cuota_mensual = 744.89 (the
    # Navarra row — extract L932, median derivation L941-949). Spec: ±1 EUR.
    base = run_scenario(Levers())
    assert abs(base["cuota"][0] - 744.89) <= 1.0


def test_a3_no_lever_is_inert():
    base = run_scenario(Levers())
    assert set(PROBE) == {s["id"] for s in LEVER_SPECS}
    for lever_id, probe_value in PROBE.items():
        assert probe_value != getattr(Levers(), lever_id)
        moved = run_scenario(Levers(**{lever_id: probe_value}))
        max_delta = max(abs(moved[k][i] - base[k][i])
                        for k in SERIES_KEYS for i in (0, 9, 24))
        assert max_delta > 1e-9, f"lever {lever_id} is inert"


def test_a4_all_eight_presets_produce_finite_paths():
    for preset in PRESETS:
        run = run_scenario(preset_levers(preset["id"]))
        for k in SERIES_KEYS:
            assert all(math.isfinite(v) for v in run[k]), (preset["id"], k)


def test_a5_mc_envelopes_match_gold_within_2pp():
    # seed-42 / 4000-path run vs gold_escenarios_deuda_mc.csv central rows
    # (extract L899-901). Verified while drafting: max |dev| = 1.399 pp.
    mc = run_montecarlo(Levers(), n_paths=4000, seed=42)
    gold = {}
    with (GOLD_DIR / "gold_escenarios_deuda_mc.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["escenario"] == "central" and int(float(row["year"])) in (2030, 2050, 2070):
                gold[int(float(row["year"]))] = row
    for y in (2030, 2050, 2070):
        i = y - 2026
        for q in ("p5", "p50", "p95"):
            assert abs(mc.percentiles[q][i] - float(gold[y][q])) <= 2.0, (y, q)


def test_committed_fixture_matches_regenerated_values():
    # The committed fixture is the phase-2 JS engine contract; it must never
    # drift from what the Python engine actually computes.
    committed = json.loads(FIXTURE.read_text(encoding="utf-8"))
    base = run_scenario(Levers())
    central = load_central()
    for y in ANCHOR_YEARS:
        entry = committed["debt_central"][str(y)]
        assert entry["engine"] == pytest.approx(base["b"][y - Y0], abs=1e-6)
        assert entry["gold_csv"] == central[y]["deuda"]
    assert committed["cuota_2026_base"] == pytest.approx(base["cuota"][0], abs=1e-3)
    assert committed["cuota_gold_median"] == 744.89
    mc = run_montecarlo(Levers(), n_paths=4000, seed=42)
    for y in ("2030", "2050", "2070"):
        for q in ("p5", "p25", "p50", "p75", "p95"):
            assert committed["montecarlo_seed42"][y][q] == pytest.approx(
                mc.percentiles[q][int(y) - 2026], abs=1e-3)
    for pid in ("S0", "S7"):
        assert pid in committed["presets_debt_2050"]
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_anchors.py -v`
Expected: A1–A5 PASS (engine + MC already built); `test_committed_fixture_matches_regenerated_values` FAILS with `FileNotFoundError` (fixture not generated yet). If any of A1–A5 fails here, STOP — that is an engine bug, not a fixture problem.

- [ ] **Step 3: Implement `scripts/generate_anchor_fixture.py` and generate the fixture**

```python
#!/usr/bin/env python3
"""Write tests/fixtures/engine_anchors.json — the dual-engine anchor contract.

The committed output binds BOTH engines: tests/test_anchors.py reads it here,
and phase 2's JS engine tests must read THIS SAME file (spec §4.2).
Regenerate (and re-commit) with:  .venv/bin/python scripts/generate_anchor_fixture.py
"""
from __future__ import annotations

import json
from pathlib import Path

from engine.constants import VINTAGE, load_central
from engine.levers import Levers, PRESETS, preset_levers
from engine.montecarlo import run_montecarlo
from engine.spain import Y0, run_scenario

OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "engine_anchors.json"
ANCHOR_YEARS = (2026, 2030, 2035, 2050)


def main() -> None:
    base = run_scenario(Levers())
    central = load_central()
    mc = run_montecarlo(Levers(), n_paths=4000, seed=42)
    fixture = {
        "vintage": VINTAGE,
        "generator": "scripts/generate_anchor_fixture.py",
        "debt_central": {str(y): {"engine": round(base["b"][y - Y0], 6),
                                  "gold_csv": central[y]["deuda"]}
                         for y in ANCHOR_YEARS},
        "cuota_2026_base": round(base["cuota"][0], 4),
        "cuota_gold_median": 744.89,
        "presets_debt_2050": {p["id"]: round(run_scenario(preset_levers(p["id"]))["b"][2050 - Y0], 4)
                              for p in PRESETS},
        "montecarlo_seed42": {str(y): {q: round(mc.percentiles[q][y - 2026], 4)
                                       for q in ("p5", "p25", "p50", "p75", "p95")}
                              for y in (2030, 2050, 2070)},
        "base_2026": {k: round(base[k][0], 6) for k in
                      ("u", "pi", "g", "bono", "cuota", "esf", "b", "pens", "dep", "ujuv")},
    }
    OUT.write_text(json.dumps(fixture, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
```

Generate:

```bash
.venv/bin/python scripts/generate_anchor_fixture.py
```

Expected fixture spot-values (from the drafting verification, all seed 42 / 4000 paths): `debt_central.2026.engine` = 106.316196, `.2050.engine` = 223.84141, `cuota_2026_base` = 744.9971, `montecarlo_seed42.2030` = p5 107.2674 / p50 113.3 / p95 119.7131, `.2050` = 176.4991 / 231.2999 / 303.8985, `.2070` = 271.9047 / 408.8999 / 619.477. If the MC values differ by more than 1e-3 the NumPy version differs from `.venv`'s 2.5.1 — investigate before committing.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_anchors.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit (fixture INCLUDED — it is the phase-2 contract)**

```bash
git add scripts/generate_anchor_fixture.py tests/fixtures/engine_anchors.json tests/test_anchors.py
git commit -m "feat: A1-A5 anchor battery and committed dual-engine anchor fixture"
```

---

### Task 11: `api/schemas.py` + static GET endpoints

**Files:**
- Create: `api/schemas.py`, `api/main.py`
- Test: `tests/test_api.py` (new)

**Interfaces:**
- Consumes: `engine.constants` (`VINTAGE`, `ENGINE_VERSION`, `CONSTANTS_TABLE`, `GOLD_DIR`, `load_kpis`, `BASE_LEVERS`), `engine.levers` (`Levers`, `PRESETS`), `engine.spain.PERSONAS`, `engine.redlines.RED_LINES`.
- Produces (used by Tasks 12, 13): `api.schemas` — the frozen contract models listed below; `api.main.app` (FastAPI) with CORS and `GET /health /vintage /constants /personas /presets /redlines`.

- [ ] **Step 1: Write the failing shape-snapshot tests**

Create `tests/test_api.py`:

```python
"""API contract tests (spec §5/§7): every endpoint, response-shape snapshots
(the frozen phase-2 contract), range-validation 422s, CORS."""
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_shape():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "vintage": "2026-07-31",
                        "engine_version": "1.0.0", "computed_not_advice": True}


def test_vintage_shape():
    r = client.get("/vintage")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"vintage", "computed_not_advice", "n_files", "files"}
    assert body["vintage"] == "2026-07-31"
    assert body["n_files"] == len(body["files"]) == 141
    assert set(body["files"][0]) == {"name", "url", "fetched_at", "bytes"}


def test_constants_shape():
    r = client.get("/constants")
    body = r.json()
    assert set(body) == {"vintage", "computed_not_advice", "constants"}
    names = {c["name"]: c for c in body["constants"]}
    assert names["MULT"]["value"] == 1.40
    assert names["DIFF"]["value"] == 1.4757
    assert all(c["provenance"] for c in body["constants"])
    assert set(body["constants"][0]) == {"name", "value", "unit", "provenance"}


def test_personas_shape():
    r = client.get("/personas")
    body = r.json()
    assert set(body) == {"vintage", "computed_not_advice", "kpis", "series", "personas"}
    assert len(body["kpis"]) == 42 and len(body["series"]) == 21
    assert [p["id"] for p in body["personas"]] == [f"{i:02d}" for i in range(1, 13)]
    p8 = next(p for p in body["personas"] if p["id"] == "08")
    assert p8["h1"] == "🧒 ¿Qué país hereda quien hoy tiene 8 años?"
    assert set(body["personas"][0]) == {"id", "pill", "foot", "h1", "meta", "hot",
                                        "series_keys", "outs", "headline", "reds"}
    for key in body["personas"][0]["series_keys"]:
        assert key in body["series"]


def test_presets_shape():
    r = client.get("/presets")
    body = r.json()
    assert set(body) == {"vintage", "computed_not_advice", "presets"}
    assert [p["id"] for p in body["presets"]] == [f"S{i}" for i in range(8)]
    s7 = body["presets"][7]
    assert s7["nm"] == "S7 adverso"
    assert s7["set"] == {"r": 4.8, "pm": 50.0, "prima": 150.0}


def test_redlines_shape():
    r = client.get("/redlines")
    body = r.json()
    assert set(body) == {"vintage", "computed_not_advice", "redlines"}
    assert len(body["redlines"]) == 9
    assert set(body["redlines"][0]) == {"id", "label", "series", "threshold", "cmp", "source"}
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_api.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'api.main'`.

- [ ] **Step 3: Implement `api/schemas.py`**

```python
"""Pydantic response/request models — the FROZEN phase-2 contract (spec §5).
Do not change field names or shapes without a spec revision."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from engine.constants import BASE_LEVERS, VINTAGE


class ApiMeta(BaseModel):
    vintage: str = VINTAGE
    computed_not_advice: bool = True   # no-recommendation rule — phase 2 must render it


class HealthResponse(ApiMeta):
    status: str
    engine_version: str


class VintageFileOut(BaseModel):
    name: str
    url: str
    fetched_at: str
    bytes: int


class VintageResponse(ApiMeta):
    n_files: int
    files: list[VintageFileOut]


class ConstantOut(BaseModel):
    name: str
    value: float
    unit: str
    provenance: str


class ConstantsResponse(ApiMeta):
    constants: list[ConstantOut]


class KpiOut(BaseModel):
    # `valor` is numeric for 39 of the 42 KPIs; deuda_mc_2030, deuda_mc_2050 and
    # cuota_hipoteca_max carry a structured dict valor (verified against the
    # gold kpis_perfiles.json while drafting) — hence Any, not float.
    valor: Optional[Any] = None
    unidad: Optional[str] = None
    fuente: Optional[str] = None
    periodo: Optional[str] = None


class SeriesOut(BaseModel):
    puntos: list[list]           # [[period, value], ...] — period is str or number
    fuente: Optional[str] = None


class PersonaOutItem(BaseModel):
    k: str
    lab: str


class PersonaRedOut(BaseModel):
    t: str
    thr: Optional[float] = None
    k: Optional[str] = None
    cmp: Optional[str] = None
    d: Optional[int] = None
    x: str


class PersonaCard(BaseModel):
    id: str
    pill: str
    foot: str
    h1: str
    meta: str
    hot: list[str]
    series_keys: list[str]
    outs: list[PersonaOutItem]
    headline: str
    reds: list[PersonaRedOut]


class PersonasResponse(ApiMeta):
    kpis: dict[str, KpiOut]
    series: dict[str, SeriesOut]
    personas: list[PersonaCard]


class PresetOut(BaseModel):
    id: str
    nm: str
    set: dict[str, float]


class PresetsResponse(ApiMeta):
    presets: list[PresetOut]


class RedLineOut(BaseModel):
    id: str
    label: str
    series: str
    threshold: float
    cmp: str
    source: str


class RedLinesResponse(ApiMeta):
    redlines: list[RedLineOut]


class LeverValues(BaseModel):
    """The 10 levers — bounds are spec §4.1 ranges; out-of-range -> 422."""
    r: float = Field(default_factory=lambda: BASE_LEVERS["r"], ge=0.0, le=6.0)
    prima: float = Field(default_factory=lambda: float(BASE_LEVERS["prima"]), ge=0.0, le=400.0)
    sp: float = Field(0.0, ge=-4.0, le=4.0)
    lam: float = Field(0.9, ge=-0.5, le=2.5)
    pm: float = Field(0.0, ge=-50.0, le=100.0)
    tau: float = Field(0.0, ge=-5.0, le=5.0)
    z: float = Field(0.0, ge=-2.0, le=2.0)
    ext: float = Field(1.8, ge=-4.0, le=6.0)
    dem: float = Field(0.0, ge=-1.0, le=1.0)
    idx: float = Field(0.0, ge=-1.5, le=1.0)


class ScenarioRequest(BaseModel):
    levers: LeverValues = Field(default_factory=LeverValues)
    horizon: int = Field(2050, ge=2026, le=2050)


class RedLineStatusOut(BaseModel):
    id: str
    label: str
    series: str
    value: float
    threshold: float
    cmp: str
    status: str          # "crossed" | "near" | "safe" — always computed
    source: str


class PersonaDependentsOut(BaseModel):
    pill: str
    headline: str
    series: dict[str, list[float]]


class ScenarioResponse(ApiMeta):
    horizon: int
    years: list[int]
    baseline: dict[str, list[float]]
    scenario: dict[str, list[float]]
    deltas: dict[str, list[float]]
    personas: dict[str, PersonaDependentsOut]
    redlines: list[RedLineStatusOut]


class MonteCarloRequest(BaseModel):
    levers: LeverValues = Field(default_factory=LeverValues)
    seed: int = Field(42, ge=0)
    n_paths: int = Field(4000, ge=100, le=4000)      # spec §6: capped at 4,000
    horizon: int = Field(2070, ge=2030, le=2070)     # spec §6: capped at 2070


class MonteCarloResponse(ApiMeta):
    years: list[int]
    percentiles: dict[str, list[float]]
    n_paths: int
    seed: int


class CountryOut(BaseModel):
    iso3: str
    iso2: str
    name: str
    region: str


class CountriesResponse(ApiMeta):
    countries: list[CountryOut]
    error: Optional[str] = None


class IndicatorOut(BaseModel):
    available: bool
    source: Optional[str] = None
    from_cache: bool = False
    error: Optional[str] = None
    values: dict[int, float]


class PanelResponse(ApiMeta):
    iso3: str
    coverage_score: float
    indicators: dict[str, IndicatorOut]


class GenericScenarioRequest(BaseModel):
    horizon_years: int = Field(10, ge=1, le=50)
    tax_wedge_delta_pp: float = 0.0
    primary_balance_target_pct: float = 0.0
    indexation_delta_pp: float = 0.0
    output_gap_path_pct: Optional[list[float]] = None
    contingent_shocks_pct: Optional[list[float]] = None
    allocation_shares: Optional[dict[str, float]] = None


class DebtPointOut(BaseModel):
    year: int
    debt_gdp_pct: float
    interest_rate_pct: float
    growth_rate_pct: float
    primary_balance_pct: float
    contingent_shock_pct: float


class FiscalSpaceOut(BaseModel):
    total_revenue_pct_gdp: float
    total_spending_pct_gdp: float
    primary_balance_pct_gdp: float
    allocations_pct_gdp: dict[str, float]


class GenericScenarioResponse(ApiMeta):
    country_iso3: str
    coverage_score: float
    defaults_used: list[str]
    baseline_years: dict[str, int]
    debt_path: list[DebtPointOut]
    unemployment_path_pct: list[float]
    inflation_path_pct: list[float]
    nominal_wage_growth_path_pct: list[float]
    fiscal_space_by_year: list[FiscalSpaceOut]
```

- [ ] **Step 4: Implement `api/main.py` (static GETs + CORS)**

```python
"""FastAPI service — all endpoints (spec §5). Shapes live in api/schemas.py."""
from __future__ import annotations

import csv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (ConstantsResponse, ConstantOut, HealthResponse,
                         PersonaCard, PersonasResponse, PresetOut, PresetsResponse,
                         RedLineOut, RedLinesResponse, VintageFileOut, VintageResponse)
from engine.constants import (CONSTANTS_TABLE, ENGINE_VERSION, GOLD_DIR, VINTAGE,
                              load_kpis)
from engine.levers import PRESETS
from engine.redlines import RED_LINES
from engine.spain import PERSONAS

app = FastAPI(title="evo core API", version=ENGINE_VERSION)

# spec §5 conventions: CORS allows localhost + the file:// "null" origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["null"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", engine_version=ENGINE_VERSION)


@app.get("/vintage", response_model=VintageResponse)
def vintage() -> VintageResponse:
    with (GOLD_DIR / "provenance_vintage_manifest.csv").open(encoding="utf-8") as fh:
        files = [VintageFileOut(name=row["name"], url=row["url"],
                                fetched_at=row["fetched_at"], bytes=int(row["bytes"]))
                 for row in csv.DictReader(fh)]
    return VintageResponse(n_files=len(files), files=files)


@app.get("/constants", response_model=ConstantsResponse)
def constants() -> ConstantsResponse:
    return ConstantsResponse(constants=[ConstantOut(**e) for e in CONSTANTS_TABLE])


@app.get("/personas", response_model=PersonasResponse)
def personas() -> PersonasResponse:
    kp = load_kpis()
    return PersonasResponse(kpis=kp["kpi"], series=kp["series"],
                            personas=[PersonaCard(**p) for p in PERSONAS])


@app.get("/presets", response_model=PresetsResponse)
def presets() -> PresetsResponse:
    return PresetsResponse(presets=[PresetOut(**p) for p in PRESETS])


@app.get("/redlines", response_model=RedLinesResponse)
def redlines() -> RedLinesResponse:
    return RedLinesResponse(redlines=[RedLineOut(**r) for r in RED_LINES])
```

(`PersonaCard(**p)` silently drops the internal `extra` key — pydantic v2 ignores unknown constructor kwargs by default, and `extra` is an engine detail, not contract.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_api.py -v`
Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add api/schemas.py api/main.py tests/test_api.py
git commit -m "feat: frozen API schemas and static GET endpoints with CORS"
```

---

### Task 12: `POST /scenario` + `POST /scenario/montecarlo` + validation + CORS tests

**Files:**
- Modify: `api/main.py` (append the two POST endpoints)
- Modify: `tests/test_api.py` (append scenario-endpoint tests)

**Interfaces:**
- Consumes: `run_scenario`, `baseline`, `persona_dependents`, `Y0`, `Y1` (Tasks 6–7), `run_montecarlo` (Task 8), `evaluate_redlines` (Task 9), schemas (Task 11).
- Produces: `POST /scenario` → `ScenarioResponse`; `POST /scenario/montecarlo` → `MonteCarloResponse`; out-of-range levers → 422.

- [ ] **Step 1: Append failing tests to `tests/test_api.py`**

```python
# ---- Task 12: scenario endpoints ----

def test_scenario_shape_and_zero_deviation():
    r = client.post("/scenario", json={})           # all defaults = base levers
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"vintage", "computed_not_advice", "horizon", "years",
                         "baseline", "scenario", "deltas", "personas", "redlines"}
    assert body["computed_not_advice"] is True
    assert body["horizon"] == 2050
    assert body["years"] == list(range(2026, 2051))
    assert len(body["baseline"]) == len(body["scenario"]) == len(body["deltas"]) == 40
    # deviation semantics: base levers -> scenario equals baseline, deltas all zero
    assert body["scenario"] == body["baseline"]
    assert all(v == 0.0 for series in body["deltas"].values() for v in series)
    assert sorted(body["personas"]) == [f"{i:02d}" for i in range(1, 13)]
    statuses = {rl["id"]: rl["status"] for rl in body["redlines"]}
    # base 2050: b=223.84 -> both debt lines crossed (computed, never hand-written)
    assert statuses["deuda_105"] == "crossed" and statuses["deuda_120"] == "crossed"


def test_scenario_s7_adverse_crosses_redlines():
    s7 = {"levers": {"r": 4.8, "pm": 50.0, "prima": 150.0}, "horizon": 2050}
    body = client.post("/scenario", json=s7).json()
    statuses = {rl["id"]: rl["status"] for rl in body["redlines"]}
    assert statuses["deuda_120"] == "crossed"           # b 2050 = 349.80
    assert statuses["deficit_suelo_2009"] == "crossed"  # saldo 2050 = -28.79
    assert statuses["bono_rescate"] == "near"           # bono 6.47 vs 7.0
    k = 2050 - 2026
    assert abs(body["scenario"]["b"][k] - 349.7973) < 1e-3


def test_scenario_lever_out_of_range_422():
    r = client.post("/scenario", json={"levers": {"r": 9.0}})
    assert r.status_code == 422
    detail = r.json()["detail"][0]
    assert detail["loc"][-1] == "r" and "less than or equal" in detail["msg"]
    assert client.post("/scenario", json={"levers": {"prima": -1}}).status_code == 422
    assert client.post("/scenario", json={"levers": {"idx": 1.2}}).status_code == 422


def test_montecarlo_endpoint_shape_and_bounds():
    r = client.post("/scenario/montecarlo", json={"seed": 42, "n_paths": 500})
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"vintage", "computed_not_advice", "years", "percentiles",
                         "n_paths", "seed"}
    assert body["years"][0] == 2026 and body["years"][-1] == 2070
    assert set(body["percentiles"]) == {"p5", "p25", "p50", "p75", "p95"}
    # reproducibility across calls with the same seed
    again = client.post("/scenario/montecarlo", json={"seed": 42, "n_paths": 500}).json()
    assert again["percentiles"] == body["percentiles"]
    # spec §6 bounds
    assert client.post("/scenario/montecarlo", json={"n_paths": 5000}).status_code == 422
    assert client.post("/scenario/montecarlo", json={"horizon": 2080}).status_code == 422


def test_montecarlo_horizon_truncates_years():
    body = client.post("/scenario/montecarlo", json={"n_paths": 300, "horizon": 2050}).json()
    assert body["years"][-1] == 2050
    assert all(len(v) == len(body["years"]) for v in body["percentiles"].values())


def test_cors_allows_null_and_localhost_origins():
    r = client.get("/health", headers={"Origin": "null"})
    assert r.headers.get("access-control-allow-origin") == "null"
    r = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_api.py -v`
Expected: new tests FAIL with 404/405 (`POST /scenario` not registered yet); Task 11 tests still pass.

- [ ] **Step 3: Append to `api/main.py`**

Add to the imports block:

```python
from api.schemas import (MonteCarloRequest, MonteCarloResponse,
                         PersonaDependentsOut, RedLineStatusOut,
                         ScenarioRequest, ScenarioResponse)
from engine.levers import Levers
from engine.montecarlo import run_montecarlo
from engine.redlines import evaluate_redlines
from engine.spain import Y0, Y1, baseline, persona_dependents, run_scenario
```

Append the endpoints:

```python
@app.post("/scenario", response_model=ScenarioResponse)
def scenario(req: ScenarioRequest) -> ScenarioResponse:
    levers = Levers(**req.levers.model_dump())
    run = run_scenario(levers)
    base = baseline()
    deltas = {k: [s - b for s, b in zip(run[k], base[k])] for k in run}
    k = req.horizon - Y0
    return ScenarioResponse(
        horizon=req.horizon,
        years=list(range(Y0, Y1 + 1)),
        baseline=base,
        scenario=run,
        deltas=deltas,
        personas={pid: PersonaDependentsOut(**dep)
                  for pid, dep in persona_dependents(run).items()},
        redlines=[RedLineStatusOut(**st) for st in evaluate_redlines(run, k)],
    )


@app.post("/scenario/montecarlo", response_model=MonteCarloResponse)
def scenario_montecarlo(req: MonteCarloRequest) -> MonteCarloResponse:
    levers = Levers(**req.levers.model_dump())
    mc = run_montecarlo(levers, n_paths=req.n_paths, seed=req.seed)
    n = req.horizon - 2026 + 1
    return MonteCarloResponse(
        years=mc.years[:n],
        percentiles={p: v[:n] for p, v in mc.percentiles.items()},
        n_paths=mc.n_paths,
        seed=mc.seed,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_api.py -v`
Expected: 12 passed.

- [ ] **Step 5: Commit**

```bash
git add api/main.py tests/test_api.py
git commit -m "feat: scenario and montecarlo POST endpoints with range validation"
```

---

### Task 13: Generic-country endpoints

**Files:**
- Modify: `api/main.py` (append `/countries`, `/panel/{iso3}`, `/scenario/generic/{iso3}`)
- Modify: `tests/test_api.py` (append generic-layer tests)

**Interfaces:**
- Consumes: `data.live.country_list` / `data.live.panel_builder` (Task 2), `engine.generic` (Task 3), schemas (Task 11).
- Produces: the three generic endpoints of spec §5. `api.main` must reference `country_list.load_country_list` and `panel_builder.build_country_panel` as MODULE ATTRIBUTES (not `from … import` of the functions) so tests can monkeypatch them.

- [ ] **Step 1: Append failing tests to `tests/test_api.py`**

```python
# ---- Task 13: generic-country layer (no network: monkeypatched) ----
import json as _json
from pathlib import Path as _Path

from data.live.models import FetchResult

_FIXTURE = _Path(__file__).parent / "fixtures" / "sample_country_panel.json"
_BASELINE_KEYS = ["debt_gdp", "gdp_growth", "inflation", "unemployment",
                  "real_interest_rate", "net_lending_borrowing", "government_revenue_gdp"]


def _fixture_panel():
    raw = _json.loads(_FIXTURE.read_text())
    panel = {}
    for key in _BASELINE_KEYS:
        values = raw.get(key) or {}
        panel[key] = FetchResult(
            values={int(y): v for y, v in values.items()},
            source="worldbank", from_cache=True, fetched_at=0.0,
            error=None if values else "no data")
    return panel


def test_countries_endpoint(monkeypatch):
    import api.main as m
    monkeypatch.setattr(m.country_list, "load_country_list", lambda: [
        {"iso3": "ESP", "iso2": "ES", "name": "Spain", "region": "Europe & Central Asia"}])
    body = client.get("/countries").json()
    assert set(body) == {"vintage", "computed_not_advice", "countries", "error"}
    assert body["countries"] == [{"iso3": "ESP", "iso2": "ES", "name": "Spain",
                                  "region": "Europe & Central Asia"}]
    assert body["error"] is None


def test_countries_endpoint_degrades_honestly(monkeypatch):
    import api.main as m
    monkeypatch.setattr(m.country_list, "load_country_list", lambda: [])
    body = client.get("/countries").json()
    assert body["countries"] == [] and body["error"] is None    # empty list, no 500


def test_panel_endpoint(monkeypatch):
    import api.main as m
    monkeypatch.setattr(m.panel_builder, "build_country_panel",
                        lambda iso3, **kw: _fixture_panel())
    body = client.get("/panel/esp").json()
    assert set(body) == {"vintage", "computed_not_advice", "iso3", "coverage_score",
                         "indicators"}
    assert body["iso3"] == "ESP"
    assert 0.0 <= body["coverage_score"] <= 1.0
    ind = body["indicators"]["debt_gdp"]
    assert set(ind) == {"available", "source", "from_cache", "error", "values"}


def test_generic_scenario_endpoint(monkeypatch):
    import api.main as m
    monkeypatch.setattr(m.panel_builder, "build_country_panel",
                        lambda iso3, **kw: _fixture_panel())
    body = client.post("/scenario/generic/ESP", json={"horizon_years": 5}).json()
    assert set(body) == {"vintage", "computed_not_advice", "country_iso3",
                         "coverage_score", "defaults_used", "baseline_years",
                         "debt_path", "unemployment_path_pct", "inflation_path_pct",
                         "nominal_wage_growth_path_pct", "fiscal_space_by_year"}
    assert body["country_iso3"] == "ESP"
    assert len(body["debt_path"]) == 5
    assert set(body["debt_path"][0]) == {"year", "debt_gdp_pct", "interest_rate_pct",
                                         "growth_rate_pct", "primary_balance_pct",
                                         "contingent_shock_pct"}
    assert isinstance(body["defaults_used"], list)      # honesty fields present
    assert isinstance(body["baseline_years"], dict)


def test_generic_scenario_validates_horizon():
    assert client.post("/scenario/generic/ESP", json={"horizon_years": 0}).status_code == 422
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_api.py -v`
Expected: new tests FAIL with 404 (endpoints not registered); earlier tests still pass.

- [ ] **Step 3: Append to `api/main.py`**

Add to the imports block:

```python
from dataclasses import asdict

from api.schemas import (CountriesResponse, CountryOut, DebtPointOut,
                         FiscalSpaceOut, GenericScenarioRequest,
                         GenericScenarioResponse, IndicatorOut, PanelResponse)
from data.live import country_list, panel_builder
from engine import generic
```

Append the endpoints:

```python
@app.get("/countries", response_model=CountriesResponse)
def countries() -> CountriesResponse:
    try:
        entries = country_list.load_country_list()   # never raises; cache-first
        return CountriesResponse(countries=[CountryOut(**e) for e in entries])
    except Exception as exc:                          # belt and braces: no 500s
        return CountriesResponse(countries=[], error=str(exc))


@app.get("/panel/{iso3}", response_model=PanelResponse)
def panel(iso3: str) -> PanelResponse:
    iso3 = iso3.upper()
    p = panel_builder.build_country_panel(iso3)
    indicators = {
        key: IndicatorOut(available=res.available, source=res.source,
                          from_cache=res.from_cache, error=res.error,
                          values=res.values)
        for key, res in p.items()
    }
    return PanelResponse(iso3=iso3, coverage_score=panel_builder.coverage_score(p),
                         indicators=indicators)


@app.post("/scenario/generic/{iso3}", response_model=GenericScenarioResponse)
def scenario_generic(iso3: str, req: GenericScenarioRequest) -> GenericScenarioResponse:
    iso3 = iso3.upper()
    p = panel_builder.build_country_panel(iso3)
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    levers = generic.ScenarioLevers(**kwargs)
    result = generic.run_scenario(iso3, p, levers)
    return GenericScenarioResponse(
        country_iso3=result.country_iso3,
        coverage_score=result.coverage_score,
        defaults_used=result.defaults_used,
        baseline_years=result.baseline_years,
        debt_path=[DebtPointOut(**asdict(pt)) for pt in result.debt_path],
        unemployment_path_pct=result.unemployment_path_pct,
        inflation_path_pct=result.inflation_path_pct,
        nominal_wage_growth_path_pct=result.nominal_wage_growth_path_pct,
        fiscal_space_by_year=[FiscalSpaceOut(**asdict(fs)) for fs in result.fiscal_space_by_year],
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_api.py -v`
Expected: 17 passed.

- [ ] **Step 5: Commit**

```bash
git add api/main.py tests/test_api.py
git commit -m "feat: generic-country endpoints — countries, panel, generic scenario"
```

---

### Task 14: `scripts/refresh_vintage.py` + full suite + manual smoke

**Files:**
- Create: `scripts/refresh_vintage.py`
- Modify: `tests/test_data_layer.py` (append refresh test)

**Interfaces:**
- Consumes: `data/gold/manifest.csv` (columns `source,url,fetched,bytes,raw_file,processed_file` — 16 rows).
- Produces: `refresh(manifest_path=Path("data/gold/manifest.csv"), out_root=Path("data/vintages"), fetch=requests.get, today=None) -> Path` — writes `data/vintages/<YYYY-MM-DD>/raw/*` + a new `manifest.csv` with a `status` column; NEVER touches `data/gold/`. Kept deliberately thin — vintage promotion and heavier provenance discipline are phase 3.

- [ ] **Step 1: Append the failing test to `tests/test_data_layer.py`**

```python
# ---- Task 14: refresh_vintage ----

def test_refresh_vintage_writes_new_dir_and_records_failures(tmp_path):
    from scripts.refresh_vintage import refresh

    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        "source,url,fetched,bytes,raw_file,processed_file\n"
        "SrcOK,https://example.org/ok.json,2026-07-31,10,ok.json,ok.csv\n"
        "SrcFail,https://example.org/fail.json,2026-07-31,10,fail.json,fail.csv\n")

    class FakeResp:
        content = b"{}"
        def raise_for_status(self):
            pass

    def fake_fetch(url, timeout):
        if "fail" in url:
            raise RuntimeError("boom")
        return FakeResp()

    out_dir = refresh(manifest_path=manifest, out_root=tmp_path / "vintages",
                      fetch=fake_fetch, today="2099-01-01")
    assert out_dir == tmp_path / "vintages" / "2099-01-01"
    assert (out_dir / "raw" / "ok.json").read_bytes() == b"{}"
    rows = list(csv.DictReader((out_dir / "manifest.csv").open()))
    assert rows[0]["status"] == "ok" and rows[0]["bytes"] == "2"
    assert rows[1]["status"].startswith("error:")        # recorded, never fabricated
    assert not (out_dir / "raw" / "fail.json").exists()
    # the committed vintage is untouched
    assert (GOLD / "VINTAGE").read_text(encoding="utf-8").strip() == "2026-07-31"
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_data_layer.py -v`
Expected: the new test FAILS with `ModuleNotFoundError: No module named 'scripts.refresh_vintage'`.

- [ ] **Step 3: Implement `scripts/refresh_vintage.py`**

```python
#!/usr/bin/env python3
"""Re-fetch the sources listed in data/gold/manifest.csv into a NEW dated
vintage directory data/vintages/<YYYY-MM-DD>/ (gitignored).

NEVER writes into data/gold/ — the committed vintage is immutable (spec §3.2);
promoting a new vintage into data/gold/ is a manual, reviewed act. Per-source
network failures are recorded in the new vintage's manifest, never fabricated.
"""
from __future__ import annotations

import csv
import datetime
from pathlib import Path

import requests

GOLD_MANIFEST = Path("data/gold/manifest.csv")
VINTAGES_ROOT = Path("data/vintages")


def refresh(manifest_path: Path = GOLD_MANIFEST, out_root: Path = VINTAGES_ROOT,
            fetch=requests.get, today: str | None = None) -> Path:
    today = today or datetime.date.today().isoformat()
    out_dir = out_root / today
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    new_rows = []
    with manifest_path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            entry = {"source": row["source"], "url": row["url"],
                     "fetched": datetime.datetime.now().isoformat(timespec="seconds"),
                     "bytes": 0, "raw_file": "", "status": ""}
            try:
                resp = fetch(row["url"], timeout=30)
                resp.raise_for_status()
                name = Path(row["raw_file"]).name or f"{row['source']}.bin"
                (raw_dir / name).write_bytes(resp.content)
                entry.update(bytes=len(resp.content), raw_file=f"raw/{name}", status="ok")
            except Exception as exc:
                entry["status"] = f"error: {exc}"
            new_rows.append(entry)

    with (out_dir / "manifest.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["source", "url", "fetched",
                                                "bytes", "raw_file", "status"])
        writer.writeheader()
        writer.writerows(new_rows)
    return out_dir


if __name__ == "__main__":
    print(f"vintage written to {refresh()}")
```

- [ ] **Step 4: Run the new test, then the FULL suite**

Run: `.venv/bin/python -m pytest tests/test_data_layer.py -v`
Expected: all pass (36 + 1).

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: EVERYTHING green — 7 test modules, 100+ tests, 0 failures, no network access.

- [ ] **Step 5: Manual smoke (spec §7)**

```bash
.venv/bin/uvicorn api.main:app --port 8000 &
sleep 2
curl -s http://127.0.0.1:8000/health
# expect {"vintage":"2026-07-31","computed_not_advice":true,"status":"ok","engine_version":"1.0.0"}
curl -s -X POST http://127.0.0.1:8000/scenario \
     -H 'Content-Type: application/json' \
     -d '{"levers": {"r": 4.8, "pm": 50.0, "prima": 150.0}, "horizon": 2050}' \
  | python3 -c "import json,sys; b=json.load(sys.stdin); print([ (r['id'], r['status']) for r in b['redlines'] ])"
# expect deuda_105/deuda_120/deficit_maastricht/deficit_suelo_2009 crossed, bono_rescate near
kill %1
```

Confirm the red-line crossings appear before proceeding.

- [ ] **Step 6: Commit**

```bash
git add scripts/refresh_vintage.py tests/test_data_layer.py
git commit -m "feat: refresh_vintage script writing dated vintages, never touching gold"
```

---

## Self-Review — Spec Coverage Map

| Spec item | Task |
|---|---|
| §2 repo layout (all dirs/files) | 1 (scaffold), 2–14 (each file) |
| §3.1 gold slice, vintage stamp, exclusions | 1 |
| §3.2 refresh_vintage — new dated dir, failures recorded | 14 |
| §3.3 live layer port, contract retained, tests ported | 2 |
| §4.1 levers table, presets, constants + provenance, chain, persona dependents | 5 (levers/presets), 4 (constants), 6 (chain), 7 (personas) |
| §4.2 anchors A1–A5 + committed fixture generator | 10 (battery), 6/8 (pre-checks) |
| §4.3 Monte Carlo DSA — 4,000 paths, 2070, percentiles, seeded, <1 s, pure NumPy | 8 |
| §4.4 generic engine + honesty fields, distinct calibration labeled | 3 (port), 4 (labels in CONSTANTS_TABLE) |
| §4.5 red lines as data + computed evaluator | 9 |
| §5 all 11 endpoints + pydantic contract + 422 + CORS + computed_not_advice | 11, 12, 13 |
| §6 no-500 degradation, cache-first, read-only gold, MC bounds | 13 (countries/panel), 14 (gold untouched), 12 (bounds) |
| §7 seven test modules + no-network + manual smoke | 1–14 (modules as mapped in File Structure), 14 (smoke) |
| §8 out of scope: no UI/JS, no ML deps, no docker, no legacy modification | respected throughout (requirements.txt, Task 1) |

Known deviations (deliberate, documented in code):
1. **A1 tolerance 0.05** — the gold CSV rounds both `deuda` and the identity's inputs, so "to the decimal" is implemented as ±0.05 with the drafting-measured drift (max 0.0375) recorded in the test comment; the fixture additionally pins the engine's exact values at 1e-6.
2. **MC calibration** — plain σ-shocks cannot reproduce the inherited fan's median drift and tail shape; `MC_PB_DRIFT` + asymmetric fiscal reaction (`MC_FB_UP`/`MC_FB_DN`) are declared calibration constants (spec §4.3 allows "calibrated to reproduce the gold MC envelopes"). A5 is verified for the fixed anchor run (seed 42, 4000 paths, max dev 1.399 pp); at other seeds the 2070 p95 sampling noise (±10–15 pp) can exceed 2 pp.
3. **near-band 10 %** (spec §4.5) is used in `engine/redlines.py`, not v16's 12 % `statusOf` band — noted in the module docstring.
4. **`engine/generic.py` is one module** (spec §2 layout) assembled from the four MVP files (spec §4.4 names them); assembly is mechanical concatenation with import rewrites only.


