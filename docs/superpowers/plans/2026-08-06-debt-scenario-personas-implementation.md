# Sovereign Fiscal Scenario Explorer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone Streamlit app that projects a country's sovereign debt/fiscal sustainability under user-controlled policy scenarios, using only real data from public APIs, and presents it through 3 persona dashboards (retiree, mortgage banker, house-buyer/landlord) plus a Model Lab and a Data & Methodology tab.

**Architecture:** `data/` fetches and caches real indicators from World Bank/Eurostat/OECD REST APIs behind a common `FetchResult` type; `engine/` implements the deterministic debt-dynamics + satellite equations + fiscal-space allocator, a real offline-trained ML fiscal-stress model, and an NSGA-II Pareto explorer; `personas/` turns engine output into persona-specific views and narratives; `app/` is the Streamlit UI, with country + scenario levers shared via `st.session_state`.

**Tech Stack:** Python 3, Streamlit, requests, pandas/numpy, scikit-learn, pymoo (NSGA-II), joblib, PyYAML, openpyxl, pytest.

## Global Constraints

- Built independently — no code/content reused from `evo_final_work_old` or `evo_final_work_data`.
- Country scope is generic — selectable at runtime, never hardcoded to one country.
- Real data only — World Bank WDI/WGI, Eurostat, OECD SDMX-JSON. Never present illustrative/simulated numbers as if real. Missing data → `"N/A — not available for this country"`, never fabricated or silently interpolated.
- Deliverable is a Python/Streamlit app run locally via `streamlit run app/main.py` — no notebook, no static HTML, no deployment in this phase.
- MVP persona scope: retiree, mortgage banker, house-buyer/landlord (buy-to-live/buy-to-let toggle). All other personas are explicitly out of scope (fast-follow).
- No screen issues a buy/sell/vote recommendation — every output is a labeled conditional projection.
- All model constants (elasticities, spreads, weights) are named, visible in code, and documented in the UI as either sourced or "calibrated default, not country-specific."
- API failure or missing cache → warning banner, block only the affected chart/metric, never the whole app.
- TDD throughout: failing test → run to verify fail → minimal implementation → run to verify pass → commit.

---

### Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `data/__init__.py`, `engine/__init__.py`, `personas/__init__.py`, `app/__init__.py`, `scripts/__init__.py`, `tests/__init__.py`
- Create: `models/.gitkeep`

**Interfaces:**
- Produces: an installable `.venv` and package layout every later task imports from (`data.*`, `engine.*`, `personas.*`, `app.*`).

- [ ] **Step 1: Create the venv and lock the dependency list**

```bash
cd /home/dan/projects/evo_final_work
python3 -m venv .venv
source .venv/bin/activate
```

- [ ] **Step 2: Write `requirements.txt`**

```
streamlit>=1.38
pandas>=2.2
numpy>=1.26
requests>=2.32
scikit-learn>=1.5
pymoo>=0.6.1
pytest>=8.3
pyyaml>=6.0
joblib>=1.4
openpyxl>=3.1
anthropic>=0.34
```

- [ ] **Step 3: Install and verify**

```bash
pip install --upgrade pip
pip install -r requirements.txt
python -c "import streamlit, pandas, numpy, requests, sklearn, pymoo, yaml, joblib, openpyxl, pytest; print('ok')"
```

Expected: prints `ok`.

- [ ] **Step 4: Write `.gitignore`**

```
.venv/
data_cache/
__pycache__/
*.pyc
.pytest_cache/
```

(`models/` is deliberately NOT ignored — the trained model artifact and `METRICS.md` ship with the repo per the design spec §2.)

- [ ] **Step 5: Create package directories and placeholders**

```bash
mkdir -p data engine personas app scripts tests tests/fixtures models
touch data/__init__.py engine/__init__.py personas/__init__.py app/__init__.py scripts/__init__.py tests/__init__.py
touch models/.gitkeep
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .gitignore data engine personas app scripts tests models
git commit -m "chore: project scaffolding"
```

---

### Task 2: Data foundation — models, cache, country list, indicator catalog

**Files:**
- Create: `data/models.py`
- Create: `data/cache.py`
- Create: `data/country_list.py`
- Create: `data/indicator_catalog.yaml`
- Test: `tests/test_data_layer.py` (cache + country-list portions; client portions added in Tasks 3–5)

**Interfaces:**
- Produces: `FetchResult(values: Dict[int,float], source: str, from_cache: bool, fetched_at: Optional[float], error: Optional[str]=None)` with `.available` property — every data-layer function in Tasks 3–6 returns this type.
- Produces: `DiskCache(cache_dir="data_cache").get(country_iso3, indicator_key) -> Optional[FetchResult]` / `.set(country_iso3, indicator_key, result: FetchResult) -> None`.
- Produces: `load_country_list() -> List[dict]` (each `{"iso3", "iso2", "name", "region"}`), `iso3_to_iso2_map() -> Dict[str,str]`.
- Produces: `data/indicator_catalog.yaml` loaded by Task 6's `load_catalog()` as `Dict[str, dict]` keyed by indicator key, each value having `label`, `unit`, `block`, optional `note`, and `sources: [{"type": "worldbank"|"eurostat"|"oecd", ...type-specific fields}]`.

- [ ] **Step 1: Write the failing cache test**

```python
# tests/test_data_layer.py
from data.cache import DiskCache
from data.models import FetchResult


def test_disk_cache_round_trip(tmp_path):
    cache = DiskCache(cache_dir=str(tmp_path))
    result = FetchResult(values={2022: 50.0}, source="worldbank", from_cache=False, fetched_at=1700000000.0)
    cache.set("ESP", "debt_gdp", result)
    loaded = cache.get("ESP", "debt_gdp")
    assert loaded is not None
    assert loaded.values == {2022: 50.0}
    assert loaded.from_cache is True


def test_disk_cache_miss_returns_none(tmp_path):
    cache = DiskCache(cache_dir=str(tmp_path))
    assert cache.get("ESP", "debt_gdp") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_data_layer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'data.cache'` (or `data.models`).

- [ ] **Step 3: Write `data/models.py`**

```python
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class FetchResult:
    values: Dict[int, float]       # year -> value
    source: str                    # "worldbank" | "eurostat" | "oecd"
    from_cache: bool
    fetched_at: Optional[float] = None
    error: Optional[str] = None

    @property
    def available(self) -> bool:
        return len(self.values) > 0 and self.error is None
```

- [ ] **Step 4: Write `data/cache.py`**

```python
import json
import time
from pathlib import Path
from typing import Optional

from data.models import FetchResult


class DiskCache:
    def __init__(self, cache_dir: str = "data_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, country_iso3: str, indicator_key: str) -> Path:
        return self.cache_dir / country_iso3 / f"{indicator_key}.json"

    def get(self, country_iso3: str, indicator_key: str) -> Optional[FetchResult]:
        path = self._path(country_iso3, indicator_key)
        if not path.exists():
            return None
        raw = json.loads(path.read_text())
        return FetchResult(
            values={int(k): v for k, v in raw["values"].items()},
            source=raw["source"],
            from_cache=True,
            fetched_at=raw["fetched_at"],
            error=None,
        )

    def set(self, country_iso3: str, indicator_key: str, result: FetchResult) -> None:
        if not result.available:
            return
        path = self._path(country_iso3, indicator_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "values": result.values,
            "source": result.source,
            "fetched_at": result.fetched_at or time.time(),
        }))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_data_layer.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Write `data/country_list.py`**

```python
import json
from pathlib import Path
from typing import Dict, List

import requests

WORLD_BANK_BASE = "https://api.worldbank.org/v2"
COUNTRY_LIST_CACHE = Path("data_cache/_country_list.json")


def fetch_country_list(timeout: int = 30) -> List[dict]:
    resp = requests.get(f"{WORLD_BANK_BASE}/country", params={"format": "json", "per_page": 400}, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()
    countries = payload[1]
    # region.id == "NA" marks aggregates ("World", "OECD members", ...), not real countries
    return [
        {"iso3": c["id"], "iso2": c["iso2Code"], "name": c["name"], "region": c["region"]["value"]}
        for c in countries
        if c["region"]["id"] != "NA"
    ]


def load_country_list() -> List[dict]:
    if COUNTRY_LIST_CACHE.exists():
        return json.loads(COUNTRY_LIST_CACHE.read_text())
    countries = fetch_country_list()
    COUNTRY_LIST_CACHE.parent.mkdir(parents=True, exist_ok=True)
    COUNTRY_LIST_CACHE.write_text(json.dumps(countries))
    return countries


def iso3_to_iso2_map() -> Dict[str, str]:
    return {c["iso3"]: c["iso2"] for c in load_country_list()}
```

Verified live against the real World Bank `/v2/country` endpoint: 295 total entries, 217 real countries after filtering `region.id != "NA"`; each has `id` (iso3, e.g. `"ESP"`) and `iso2Code` (e.g. `"ES"`).

- [ ] **Step 7: Add a mocked test for the country list (no network in CI)**

Append to `tests/test_data_layer.py`:

```python
from unittest.mock import patch, MagicMock
from data.country_list import fetch_country_list


def test_fetch_country_list_filters_aggregates():
    payload = [
        {"page": 1},
        [
            {"id": "ESP", "iso2Code": "ES", "name": "Spain", "region": {"id": "ECS", "value": "Europe & Central Asia"}},
            {"id": "WLD", "iso2Code": "1W", "name": "World", "region": {"id": "NA", "value": "Aggregates"}},
        ],
    ]
    mock = MagicMock()
    mock.json.return_value = payload
    mock.raise_for_status = MagicMock()
    with patch("data.country_list.requests.get", return_value=mock):
        countries = fetch_country_list()
    assert countries == [{"iso3": "ESP", "iso2": "ES", "name": "Spain", "region": "Europe & Central Asia"}]
```

- [ ] **Step 8: Run test to verify it passes**

Run: `pytest tests/test_data_layer.py -v`
Expected: PASS (3 tests).

- [ ] **Step 9: Write `data/indicator_catalog.yaml`**

Every World Bank code below was verified live against the real API for at least one test country (mostly Spain, USA as cross-check) during plan drafting.

```yaml
indicators:
  debt_gdp:
    label: "Central government debt, total (% of GDP)"
    unit: "% of GDP"
    block: debt
    sources:
      - type: worldbank
        code: GC.DOD.TOTL.GD.ZS
  government_revenue_gdp:
    label: "Revenue, excluding grants (% of GDP)"
    unit: "% of GDP"
    block: debt
    note: "General government total revenue proxy -- used as the fiscal-space allocator's revenue baseline."
    sources:
      - type: worldbank
        code: GC.REV.XGRT.GD.ZS
  gdp_growth:
    label: "GDP growth (annual %)"
    unit: "% annual"
    block: macro
    sources:
      - type: worldbank
        code: NY.GDP.MKTP.KD.ZG
  inflation:
    label: "Inflation, consumer prices (annual %)"
    unit: "% annual"
    block: macro
    sources:
      - type: worldbank
        code: FP.CPI.TOTL.ZG
  unemployment:
    label: "Unemployment, total (% of total labor force)"
    unit: "% of labor force"
    block: labor
    sources:
      - type: worldbank
        code: SL.UEM.TOTL.ZS
  net_lending_borrowing:
    label: "General government net lending/borrowing, proxy for primary balance (% GDP)"
    unit: "% of GDP"
    block: debt
    note: "Overall fiscal balance, not primary balance in the strict sense -- documented as a proxy in the UI."
    sources:
      - type: worldbank
        code: GC.NLD.TOTL.GD.ZS
  real_interest_rate:
    label: "Real interest rate (%)"
    unit: "%"
    block: debt
    note: "Whole-economy real interest rate proxy, not a sovereign-specific effective rate -- documented as a proxy in the UI. Sparse for several Eurozone countries under this WDI series' methodology (known gap, not a code error)."
    sources:
      - type: worldbank
        code: FR.INR.RINR
  corruption_control:
    label: "Control of Corruption (Worldwide Governance Indicators estimate)"
    unit: "index, approx. -2.5 (weak) to 2.5 (strong)"
    block: governance
    sources:
      - type: worldbank
        code: GOV_WGI_CC_EST
  net_migration:
    label: "Net migration (people, 5-year total)"
    unit: "people"
    block: demographics
    sources:
      - type: worldbank
        code: SM.POP.NETM
  health_exp_gdp:
    label: "Domestic general government health expenditure (% GDP)"
    unit: "% of GDP"
    block: spending
    sources:
      - type: worldbank
        code: SH.XPD.GHED.GD.ZS
  edu_exp_gdp:
    label: "Government expenditure on education, total (% GDP)"
    unit: "% of GDP"
    block: spending
    sources:
      - type: worldbank
        code: SE.XPD.TOTL.GD.ZS
  public_investment_gdp:
    label: "Gross fixed capital formation (% GDP)"
    unit: "% of GDP"
    block: spending
    note: "Whole-economy GFCF, not government-only -- documented as a proxy in the UI."
    sources:
      - type: worldbank
        code: NE.GDI.FTOT.ZS
  productivity_level:
    label: "GDP per person employed (constant 2021 PPP $)"
    unit: "constant 2021 PPP $"
    block: labor
    note: "Level series; productivity GROWTH is derived as year-over-year %% change where needed, not fetched directly."
    sources:
      - type: worldbank
        code: SL.GDP.PCAP.EM.KD
  public_wage_bill_gdp:
    label: "Compensation of employees, general government (% GDP)"
    unit: "% of GDP"
    block: spending
    note: "EU countries only (Eurostat government finance statistics)."
    sources:
      - type: eurostat
        dataset_id: gov_10a_exp
        dims: {unit: PC_GDP, sector: S13, cofog99: TOTAL, na_item: D1}
  security_exp_gdp:
    label: "Public order and safety expenditure, COFOG GF03 (% GDP)"
    unit: "% of GDP"
    block: spending
    note: "EU countries only (Eurostat government finance statistics)."
    sources:
      - type: eurostat
        dataset_id: gov_10a_exp
        dims: {unit: PC_GDP, sector: S13, cofog99: GF03, na_item: TE}
  welfare_exp_gdp:
    label: "Social protection expenditure, COFOG GF10 (% GDP)"
    unit: "% of GDP"
    block: spending
    note: "EU countries only (Eurostat government finance statistics)."
    sources:
      - type: eurostat
        dataset_id: gov_10a_exp
        dims: {unit: PC_GDP, sector: S13, cofog99: GF10, na_item: TE}
  pension_exp_gdp:
    label: "Old-age expenditure, COFOG GF1002 (% GDP)"
    unit: "% of GDP"
    block: spending
    note: "EU countries only. COFOG old-age sub-function -- pension-specific proxy, not a full actuarial pension-spend figure. Worst case for an unconfirmed sub-code is graceful N/A, not a crash."
    sources:
      - type: eurostat
        dataset_id: gov_10a_exp
        dims: {unit: PC_GDP, sector: S13, cofog99: GF1002, na_item: TE}
  house_price_index:
    label: "House price index (2015=100)"
    unit: "index, 2015=100"
    block: housing
    note: "EU countries only (Eurostat). Verified live for Spain: 2015=100.0 through 2025=180.6."
    sources:
      - type: eurostat
        dataset_id: prc_hpi_a
        dims: {unit: I15_A_AVG, purchase: TOTAL}
  edu_spend_per_student:
    label: "Education expenditure per student, upper secondary+post-secondary non-tertiary (USD, PPP)"
    unit: "USD, PPP-converted"
    block: spending
    note: "OECD countries only. Single OECD indicator carried in this MVP; see Data & Methodology tab."
    sources:
      - type: oecd
        agency: "OECD.EDU.IMEP"
        dataflow_id: "DSD_EAG_UOE_FIN@DF_UOE_INDIC_FIN_PERSTUD"
        version: "3.2"
        dim_order: [MEASURE, EDUCATION_LEV, EXP_SOURCE, EXP_DESTINATION, EXPENDITURE_TYPE, PRICE_BASE, UNIT_MEASURE, Q_SHEET]
        dims: {MEASURE: FIN_PERSTUD, EDUCATION_LEV: ISCED11_35_45, EXP_SOURCE: "_T", EXP_DESTINATION: INST_EDU, EXPENDITURE_TYPE: NORD, PRICE_BASE: Q, UNIT_MEASURE: USD_PPP_ST, Q_SHEET: SOURCE}
```

- [ ] **Step 10: Commit**

```bash
git add data/models.py data/cache.py data/country_list.py data/indicator_catalog.yaml tests/test_data_layer.py
git commit -m "feat: data foundation (FetchResult, disk cache, country list, indicator catalog)"
```

---

### Task 3: World Bank client

**Files:**
- Create: `data/worldbank_client.py`
- Test: `tests/test_data_layer.py` (append)

**Interfaces:**
- Consumes: `FetchResult` from Task 2.
- Produces: `fetch_indicator(country_iso3: str, wb_code: str, start_year: int, end_year: int, timeout: int = 20) -> FetchResult`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_data_layer.py`:

```python
from data import worldbank_client


def _mock_response(payload):
    mock = MagicMock()
    mock.json.return_value = payload
    mock.raise_for_status = MagicMock()
    return mock


def test_worldbank_client_parses_valid_payload():
    payload = [
        {"page": 1, "pages": 1, "total": 2},
        [{"date": "2022", "value": 100.5}, {"date": "2021", "value": None}],
    ]
    with patch("data.worldbank_client.requests.get", return_value=_mock_response(payload)):
        result = worldbank_client.fetch_indicator("ESP", "GC.DOD.TOTL.GD.ZS", 2021, 2022)
    assert result.available
    assert result.values == {2022: 100.5}


def test_worldbank_client_returns_na_sentinel_when_indicator_missing():
    payload = {"message": [{"id": "175", "value": "The indicator was not found."}]}
    with patch("data.worldbank_client.requests.get", return_value=_mock_response(payload)):
        result = worldbank_client.fetch_indicator("ESP", "BOGUS.CODE", 2021, 2022)
    assert not result.available
    assert result.error is not None


def test_worldbank_client_handles_network_error():
    with patch("data.worldbank_client.requests.get", side_effect=ConnectionError("boom")):
        result = worldbank_client.fetch_indicator("ESP", "GC.DOD.TOTL.GD.ZS", 2021, 2022)
    assert not result.available
    assert "boom" in result.error
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_data_layer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'data.worldbank_client'`.

- [ ] **Step 3: Write `data/worldbank_client.py`**

```python
import time
from typing import Dict

import requests

from data.models import FetchResult

WORLD_BANK_BASE = "https://api.worldbank.org/v2"


def fetch_indicator(country_iso3: str, wb_code: str, start_year: int, end_year: int, timeout: int = 20) -> FetchResult:
    url = f"{WORLD_BANK_BASE}/country/{country_iso3}/indicator/{wb_code}"
    params = {"format": "json", "per_page": 1000, "date": f"{start_year}:{end_year}"}
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        return FetchResult(values={}, source="worldbank", from_cache=False, fetched_at=time.time(), error=str(exc))

    if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
        return FetchResult(values={}, source="worldbank", from_cache=False, fetched_at=time.time(),
                            error="no data returned for this country/indicator")

    values: Dict[int, float] = {}
    for row in payload[1]:
        if row.get("value") is not None:
            values[int(row["date"])] = float(row["value"])

    if not values:
        return FetchResult(values={}, source="worldbank", from_cache=False, fetched_at=time.time(),
                            error="indicator has no non-null observations for this country")

    return FetchResult(values=values, source="worldbank", from_cache=False, fetched_at=time.time(), error=None)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_data_layer.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add data/worldbank_client.py tests/test_data_layer.py
git commit -m "feat: World Bank WDI/WGI client"
```

---

### Task 4: Eurostat client

**Files:**
- Create: `data/eurostat_client.py`
- Test: `tests/test_data_layer.py` (append)

**Interfaces:**
- Consumes: `FetchResult` from Task 2.
- Produces: `fetch_indicator(country_iso2: str, dataset_id: str, dims: Dict[str,str], timeout: int = 20) -> FetchResult`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_data_layer.py`:

```python
from data import eurostat_client


def test_eurostat_client_parses_jsonstat_payload():
    payload = {
        "dimension": {"time": {"category": {"index": {"2021": 0, "2022": 1}}}},
        "value": {"0": 100.0, "1": 180.6},
    }
    with patch("data.eurostat_client.requests.get", return_value=_mock_response(payload)):
        result = eurostat_client.fetch_indicator("ES", "prc_hpi_a", {"unit": "I15_A_AVG"})
    assert result.available
    assert result.values == {2021: 100.0, 2022: 180.6}


def test_eurostat_client_returns_na_when_no_observations():
    payload = {"dimension": {"time": {"category": {"index": {}}}}, "value": {}}
    with patch("data.eurostat_client.requests.get", return_value=_mock_response(payload)):
        result = eurostat_client.fetch_indicator("ZZ", "prc_hpi_a", {"unit": "I15_A_AVG"})
    assert not result.available
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_data_layer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'data.eurostat_client'`.

- [ ] **Step 3: Write `data/eurostat_client.py`**

Decoding note (verified against a live Eurostat JSON-stat 2.0 response): the flat `value` dict is keyed by the flat index that equals the time-dimension's own index whenever every other dimension is pinned to a single value — which is always true here since `geo` and every entry in `dims` are pinned to one code each.

```python
import time
from typing import Dict

import requests

from data.models import FetchResult

EUROSTAT_BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"


def fetch_indicator(country_iso2: str, dataset_id: str, dims: Dict[str, str], timeout: int = 20) -> FetchResult:
    url = f"{EUROSTAT_BASE}/{dataset_id}"
    params = {**dims, "geo": country_iso2, "format": "JSON", "lang": "EN"}
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        return FetchResult(values={}, source="eurostat", from_cache=False, fetched_at=time.time(), error=str(exc))

    try:
        time_dim = payload["dimension"]["time"]["category"]["index"]
        time_positions = sorted(time_dim.items(), key=lambda kv: kv[1])
        raw_values = payload["value"]
    except (KeyError, TypeError) as exc:
        return FetchResult(values={}, source="eurostat", from_cache=False, fetched_at=time.time(),
                            error=f"unexpected JSON-stat shape: {exc}")

    values: Dict[int, float] = {}
    for year_str, position in time_positions:
        v = raw_values.get(str(position))
        if v is not None:
            values[int(year_str)] = float(v)

    if not values:
        return FetchResult(values={}, source="eurostat", from_cache=False, fetched_at=time.time(),
                            error="no observations for this geo/dimension combination")

    return FetchResult(values=values, source="eurostat", from_cache=False, fetched_at=time.time(), error=None)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_data_layer.py -v`
Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
git add data/eurostat_client.py tests/test_data_layer.py
git commit -m "feat: Eurostat JSON-stat 2.0 client"
```

---

### Task 5: OECD client

**Files:**
- Create: `data/oecd_client.py`
- Test: `tests/test_data_layer.py` (append)

**Interfaces:**
- Consumes: `FetchResult` from Task 2.
- Produces: `fetch_indicator(country_iso3: str, agency: str, dataflow_id: str, version: str, dims: Dict[str,str], dim_order: List[str], timeout: int = 20) -> FetchResult`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_data_layer.py`:

```python
from data import oecd_client


def test_oecd_client_parses_sdmx_payload():
    payload = {
        "data": {
            "structures": [{"dimensions": {"observation": [{"values": [{"id": "2021"}, {"id": "2022"}]}]}}],
            "dataSets": [{"series": {"0:0:0:0:0:0:0:0": {"observations": {"0": [1234.5], "1": [1300.0]}}}}],
        }
    }
    with patch("data.oecd_client.requests.get", return_value=_mock_response(payload)):
        result = oecd_client.fetch_indicator(
            "ESP", "OECD.EDU.IMEP", "DSD_EAG_UOE_FIN@DF_UOE_INDIC_FIN_PERSTUD", "3.2",
            {"MEASURE": "FIN_PERSTUD"}, ["MEASURE"],
        )
    assert result.available
    assert result.values == {2021: 1234.5, 2022: 1300.0}


def test_oecd_client_returns_na_when_no_series():
    payload = {
        "data": {
            "structures": [{"dimensions": {"observation": [{"values": []}]}}],
            "dataSets": [{"series": {}}],
        }
    }
    with patch("data.oecd_client.requests.get", return_value=_mock_response(payload)):
        result = oecd_client.fetch_indicator(
            "ZZZ", "OECD.EDU.IMEP", "DSD_EAG_UOE_FIN@DF_UOE_INDIC_FIN_PERSTUD", "3.2",
            {"MEASURE": "FIN_PERSTUD"}, ["MEASURE"],
        )
    assert not result.available
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_data_layer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'data.oecd_client'`.

- [ ] **Step 3: Write `data/oecd_client.py`**

```python
import time
from typing import Dict, List

import requests

from data.models import FetchResult

OECD_BASE = "https://sdmx.oecd.org/public/rest/data"


def fetch_indicator(country_iso3: str, agency: str, dataflow_id: str, version: str,
                     dims: Dict[str, str], dim_order: List[str], timeout: int = 20) -> FetchResult:
    key = ".".join([country_iso3] + [dims[d] for d in dim_order])
    url = f"{OECD_BASE}/{agency},{dataflow_id},{version}/{key}"
    params = {"format": "jsondata"}
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        return FetchResult(values={}, source="oecd", from_cache=False, fetched_at=time.time(), error=str(exc))

    try:
        structures = payload["data"]["structures"][0]
        time_values = [v["id"] for v in structures["dimensions"]["observation"][0]["values"]]
        datasets = payload["data"]["dataSets"][0]
        series = datasets["series"]
    except (KeyError, IndexError, TypeError) as exc:
        return FetchResult(values={}, source="oecd", from_cache=False, fetched_at=time.time(),
                            error=f"unexpected SDMX-JSON shape: {exc}")

    if not series:
        return FetchResult(values={}, source="oecd", from_cache=False, fetched_at=time.time(),
                            error="no series returned for this country/dimension combination")

    series_key = next(iter(series))
    observations = series[series_key]["observations"]

    values: Dict[int, float] = {}
    for idx_str, obs in observations.items():
        year = int(time_values[int(idx_str)])
        if obs and obs[0] is not None:
            values[year] = float(obs[0])

    if not values:
        return FetchResult(values={}, source="oecd", from_cache=False, fetched_at=time.time(),
                            error="series present but all observations null")

    return FetchResult(values=values, source="oecd", from_cache=False, fetched_at=time.time(), error=None)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_data_layer.py -v`
Expected: PASS (10 tests).

- [ ] **Step 5: Commit**

```bash
git add data/oecd_client.py tests/test_data_layer.py
git commit -m "feat: OECD SDMX-JSON 2.0 client"
```

---

### Task 6: Country panel builder

**Files:**
- Create: `data/panel_builder.py`
- Test: `tests/test_data_layer.py` (append)

**Interfaces:**
- Consumes: `load_catalog()` reading Task 2's `indicator_catalog.yaml`; `worldbank_client.fetch_indicator`, `eurostat_client.fetch_indicator`, `oecd_client.fetch_indicator` (Tasks 3–5); `DiskCache`, `iso3_to_iso2_map` (Task 2).
- Produces: `load_catalog() -> Dict[str, dict]`; `fetch_one(country_iso3, indicator_key, spec, start_year, end_year, cache, force_refresh=False) -> FetchResult`; `build_country_panel(country_iso3, start_year=2000, end_year=2024, cache=None, force_refresh=False) -> Dict[str, FetchResult]`; `coverage_score(panel: Dict[str, FetchResult]) -> float`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_data_layer.py`:

```python
from data.panel_builder import coverage_score, fetch_one, load_catalog


def test_coverage_score_computes_fraction_available():
    panel = {
        "a": FetchResult(values={2022: 1.0}, source="worldbank", from_cache=False, fetched_at=0.0),
        "b": FetchResult(values={}, source="worldbank", from_cache=False, fetched_at=0.0, error="no data"),
    }
    assert coverage_score(panel) == 0.5


def test_load_catalog_has_expected_keys():
    catalog = load_catalog()
    assert "debt_gdp" in catalog
    assert "government_revenue_gdp" in catalog
    assert catalog["debt_gdp"]["sources"][0]["type"] == "worldbank"


def test_fetch_one_uses_cache_before_network(tmp_path):
    from data.cache import DiskCache
    cache = DiskCache(cache_dir=str(tmp_path))
    cached_result = FetchResult(values={2022: 42.0}, source="worldbank", from_cache=False, fetched_at=0.0)
    cache.set("ESP", "debt_gdp", cached_result)

    spec = {"sources": [{"type": "worldbank", "code": "GC.DOD.TOTL.GD.ZS"}]}
    with patch("data.worldbank_client.requests.get", side_effect=AssertionError("should not hit network")):
        result = fetch_one("ESP", "debt_gdp", spec, 2000, 2024, cache)
    assert result.values == {2022: 42.0}
    assert result.from_cache is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_data_layer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'data.panel_builder'`.

- [ ] **Step 3: Write `data/panel_builder.py`**

```python
import time
from pathlib import Path
from typing import Dict

import yaml

from data.models import FetchResult
from data.cache import DiskCache
from data.country_list import iso3_to_iso2_map
from data import worldbank_client, eurostat_client, oecd_client

CATALOG_PATH = Path(__file__).parent / "indicator_catalog.yaml"


def load_catalog() -> dict:
    return yaml.safe_load(CATALOG_PATH.read_text())["indicators"]


def fetch_one(country_iso3: str, indicator_key: str, spec: dict, start_year: int, end_year: int,
              cache: DiskCache, force_refresh: bool = False) -> FetchResult:
    if not force_refresh:
        cached = cache.get(country_iso3, indicator_key)
        if cached is not None:
            return cached

    source = spec["sources"][0]
    stype = source["type"]

    if stype == "worldbank":
        result = worldbank_client.fetch_indicator(country_iso3, source["code"], start_year, end_year)
    elif stype == "eurostat":
        iso2 = iso3_to_iso2_map().get(country_iso3)
        if iso2 is None:
            result = FetchResult(values={}, source="eurostat", from_cache=False, fetched_at=time.time(),
                                  error="no ISO2 code found for this country")
        else:
            result = eurostat_client.fetch_indicator(iso2, source["dataset_id"], source["dims"])
    elif stype == "oecd":
        result = oecd_client.fetch_indicator(country_iso3, source["agency"], source["dataflow_id"],
                                              source["version"], source["dims"], source["dim_order"])
    else:
        result = FetchResult(values={}, source=stype, from_cache=False, fetched_at=time.time(),
                              error=f"unknown source type: {stype}")

    if result.available:
        cache.set(country_iso3, indicator_key, result)
    return result


def build_country_panel(country_iso3: str, start_year: int = 2000, end_year: int = 2024,
                         cache: DiskCache = None, force_refresh: bool = False) -> Dict[str, FetchResult]:
    cache = cache or DiskCache()
    catalog = load_catalog()
    panel = {}
    for key, spec in catalog.items():
        panel[key] = fetch_one(country_iso3, key, spec, start_year, end_year, cache, force_refresh)
    return panel


def coverage_score(panel: Dict[str, FetchResult]) -> float:
    if not panel:
        return 0.0
    available = sum(1 for r in panel.values() if r.available)
    return available / len(panel)
```

Only `spec["sources"][0]` is used — every catalog entry has exactly one source in this MVP, so there is no multi-source fallback chain to build; a missing/failed single source degrades honestly to N/A via `FetchResult.available`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_data_layer.py -v`
Expected: PASS (13 tests).

- [ ] **Step 5: Commit**

```bash
git add data/panel_builder.py tests/test_data_layer.py
git commit -m "feat: country panel builder + coverage score"
```

---

### Task 7: Debt dynamics engine

**Files:**
- Create: `engine/debt_dynamics.py`
- Create: `tests/fixtures/sample_country_panel.json`
- Test: `tests/test_debt_engine.py`

**Interfaces:**
- Produces: `DebtPathPoint(year, debt_gdp_pct, interest_rate_pct, growth_rate_pct, primary_balance_pct, contingent_shock_pct)`; `project_debt_path(initial_debt_gdp_pct, r_path_pct, g_path_pct, pb_path_pct, start_year, contingent_shocks_pct=None) -> List[DebtPathPoint]`.

- [ ] **Step 1: Write the committed real-data fixture**

Real World Bank WDI data for the USA, verified live during plan drafting (`GC.DOD.TOTL.GD.ZS`, `NY.GDP.MKTP.KD.ZG`, `FR.INR.RINR`, `GC.NLD.TOTL.GD.ZS`).

```python
# tests/fixtures/sample_country_panel.json (write this file directly, not via Python)
```

```json
{
  "country_iso3": "USA",
  "source_note": "Real World Bank WDI data, verified live 2026-08-06. net_lending_borrowing is a documented primary-balance proxy (overall fiscal balance); real_interest_rate is a documented whole-economy proxy for the sovereign effective rate.",
  "debt_gdp": {"2014": 95.6360178458392, "2015": 96.1410808045622, "2016": 98.1169229551873, "2017": 97.2074691432871, "2018": 98.62934291533, "2019": 100.234364169849, "2020": 124.509268439559, "2021": 118.284809538371},
  "gdp_growth": {"2015": 2.94555045227337, "2016": 1.81945147909089, "2017": 2.45762230126449, "2018": 2.96650506701943, "2019": 2.58382533052225, "2020": -2.081375977796, "2021": 6.15202247867526},
  "real_interest_rate": {"2015": 2.31051463833344, "2016": 2.53723230294962, "2017": 2.26529637783859, "2018": 2.55474987113849, "2019": 3.57306216680747, "2020": 2.17024683398691, "2021": -1.25567664234207},
  "net_lending_borrowing": {"2015": -3.19804149971093, "2016": -3.83020224555147, "2017": -2.94418313753416, "2018": -4.77899854941656, "2019": -5.35878674364723, "2020": -14.3855994220614, "2021": -12.7072284020097}
}
```

- [ ] **Step 2: Write the failing tests**

```python
# tests/test_debt_engine.py
import json
from pathlib import Path

from engine.debt_dynamics import project_debt_path

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_country_panel.json"
TOLERANCE_PP = 12.0  # accounts for the documented proxy mismatches (overall balance vs primary balance;
                      # whole-economy real rate vs effective sovereign rate) -- see fixture source_note


def _load_fixture():
    return json.loads(FIXTURE_PATH.read_text())


def test_debt_identity_reproduces_real_one_step_transitions_within_tolerance():
    fixture = _load_fixture()
    debt = {int(y): v for y, v in fixture["debt_gdp"].items()}
    growth = {int(y): v for y, v in fixture["gdp_growth"].items()}
    rate = {int(y): v for y, v in fixture["real_interest_rate"].items()}
    balance = {int(y): v for y, v in fixture["net_lending_borrowing"].items()}

    for year in range(2015, 2022):
        path = project_debt_path(
            initial_debt_gdp_pct=debt[year - 1],
            r_path_pct=[rate[year]],
            g_path_pct=[growth[year]],
            pb_path_pct=[balance[year]],
            start_year=year,
        )
        projected = path[0].debt_gdp_pct
        actual = debt[year]
        assert abs(projected - actual) <= TOLERANCE_PP, (
            f"{year}: projected {projected:.2f} vs actual {actual:.2f} exceeds {TOLERANCE_PP}pp tolerance"
        )


def test_higher_interest_rate_worsens_debt_path_monotonically():
    base = project_debt_path(80.0, [2.0] * 5, [2.0] * 5, [0.0] * 5, start_year=2025)
    higher_r = project_debt_path(80.0, [4.0] * 5, [2.0] * 5, [0.0] * 5, start_year=2025)
    for b, h in zip(base, higher_r):
        assert h.debt_gdp_pct >= b.debt_gdp_pct


def test_lower_growth_worsens_debt_path_monotonically():
    base = project_debt_path(80.0, [2.0] * 5, [2.0] * 5, [0.0] * 5, start_year=2025)
    lower_g = project_debt_path(80.0, [2.0] * 5, [0.5] * 5, [0.0] * 5, start_year=2025)
    for b, l in zip(base, lower_g):
        assert l.debt_gdp_pct >= b.debt_gdp_pct


def test_length_mismatch_raises():
    import pytest
    with pytest.raises(ValueError):
        project_debt_path(80.0, [2.0, 2.0], [2.0], [0.0, 0.0], start_year=2025)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_debt_engine.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.debt_dynamics'`.

- [ ] **Step 4: Write `engine/debt_dynamics.py`**

Implements the standard law of motion `Δd_t = (r_t − g_t)/(1+g_t) × d_{t−1} − pb_t + c_t` (design spec §4.1). All percentage inputs (debt=100.0 means 100%, rate=3.0 means 3%) are converted to ratios internally before the division, then the resulting debt ratio is converted back to percent for the output — this fixes a unit-consistency bug caught during drafting where percent-scale values were fed directly into `(1+g)` without conversion.

```python
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DebtPathPoint:
    year: int
    debt_gdp_pct: float
    interest_rate_pct: float
    growth_rate_pct: float
    primary_balance_pct: float
    contingent_shock_pct: float


def project_debt_path(initial_debt_gdp_pct: float, r_path_pct: List[float], g_path_pct: List[float],
                       pb_path_pct: List[float], start_year: int,
                       contingent_shocks_pct: Optional[List[float]] = None) -> List[DebtPathPoint]:
    n = len(r_path_pct)
    if not (len(g_path_pct) == n and len(pb_path_pct) == n):
        raise ValueError("r_path_pct, g_path_pct, and pb_path_pct must have the same length")
    shocks = contingent_shocks_pct if contingent_shocks_pct is not None else [0.0] * n

    path = []
    debt_ratio = initial_debt_gdp_pct / 100.0
    for i in range(n):
        r = r_path_pct[i] / 100.0
        g = g_path_pct[i] / 100.0
        pb = pb_path_pct[i] / 100.0
        c = shocks[i] / 100.0
        delta = (r - g) / (1 + g) * debt_ratio - pb + c
        debt_ratio = debt_ratio + delta
        path.append(DebtPathPoint(
            year=start_year + i,
            debt_gdp_pct=debt_ratio * 100.0,
            interest_rate_pct=r_path_pct[i],
            growth_rate_pct=g_path_pct[i],
            primary_balance_pct=pb_path_pct[i],
            contingent_shock_pct=shocks[i],
        ))
    return path
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_debt_engine.py -v`
Expected: PASS (4 tests).

- [ ] **Step 6: Commit**

```bash
git add engine/debt_dynamics.py tests/test_debt_engine.py tests/fixtures/sample_country_panel.json
git commit -m "feat: debt dynamics engine + real-data fixture test"
```

---

### Task 8: Satellite equations

**Files:**
- Create: `engine/satellite.py`
- Test: `tests/test_satellite_equations.py`

**Interfaces:**
- Produces: `OKUN_COEFFICIENT: float`, `PHILLIPS_SLOPE: float`; `okun_unemployment_gap(output_gap_pct, okun_coefficient=OKUN_COEFFICIENT) -> float`; `phillips_inflation(base_inflation_pct, unemployment_gap_pp, phillips_slope=PHILLIPS_SLOPE) -> float`; `indexed_growth(inflation_pct, indexation_delta_pp) -> float`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_satellite_equations.py
from engine.satellite import okun_unemployment_gap, phillips_inflation, indexed_growth, OKUN_COEFFICIENT


def test_okun_zero_output_gap_gives_zero_unemployment_gap():
    assert okun_unemployment_gap(0.0) == 0.0


def test_okun_negative_output_gap_raises_unemployment():
    assert okun_unemployment_gap(-2.0) == OKUN_COEFFICIENT * 2.0


def test_phillips_baseline_with_no_gap_returns_base_inflation():
    assert phillips_inflation(2.0, 0.0) == 2.0


def test_phillips_tighter_labor_market_raises_inflation_pressure():
    tighter = phillips_inflation(2.0, -1.0)  # negative gap = unemployment below baseline = tight market
    assert tighter > 2.0


def test_indexed_growth_adds_delta_to_inflation():
    assert indexed_growth(2.5, 0.0) == 2.5
    assert indexed_growth(2.5, 1.0) == 3.5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_satellite_equations.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.satellite'`.

- [ ] **Step 3: Write `engine/satellite.py`**

```python
OKUN_COEFFICIENT = 0.5  # calibrated default (literature range 0.3-0.5 for advanced economies); not country-specific
PHILLIPS_SLOPE = 0.3    # calibrated default: inflation response per point of unemployment gap; not country-specific


def okun_unemployment_gap(output_gap_pct: float, okun_coefficient: float = OKUN_COEFFICIENT) -> float:
    """Okun's law: unemployment gap (pp) implied by an output gap (% of potential GDP)."""
    return -okun_coefficient * output_gap_pct


def phillips_inflation(base_inflation_pct: float, unemployment_gap_pp: float,
                        phillips_slope: float = PHILLIPS_SLOPE) -> float:
    """Phillips curve: inflation (%) given a baseline and an unemployment gap (pp, negative = tight labor market)."""
    return base_inflation_pct - phillips_slope * unemployment_gap_pp


def indexed_growth(inflation_pct: float, indexation_delta_pp: float) -> float:
    """Wage/pension indexation rule: nominal growth (%) = inflation + a policy indexation lever (pp above/below full CPI indexation)."""
    return inflation_pct + indexation_delta_pp
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_satellite_equations.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add engine/satellite.py tests/test_satellite_equations.py
git commit -m "feat: Okun/Phillips/indexation satellite equations"
```

---

### Task 9: Fiscal-space allocator

**Files:**
- Create: `engine/fiscal_space.py`
- Test: `tests/test_fiscal_space.py`

**Interfaces:**
- Produces: `SPENDING_CATEGORIES: List[str]` (`["health","education","welfare","public_wage_bill","security","infrastructure","public_investment"]`); `FiscalSpaceResult(total_revenue_pct_gdp, total_spending_pct_gdp, primary_balance_pct_gdp, allocations_pct_gdp: Dict[str,float])`; `allocate_fiscal_space(gdp_pct_revenue, tax_wedge_delta_pp, primary_balance_target_pct, allocation_shares: Dict[str,float]) -> FiscalSpaceResult`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_fiscal_space.py
import pytest

from engine.fiscal_space import allocate_fiscal_space, SPENDING_CATEGORIES


def _equal_shares():
    return {c: 1.0 / len(SPENDING_CATEGORIES) for c in SPENDING_CATEGORIES}


def test_allocations_sum_to_total_spending():
    result = allocate_fiscal_space(35.0, 0.0, -2.0, _equal_shares())
    assert result.total_revenue_pct_gdp == 35.0
    assert result.total_spending_pct_gdp == pytest.approx(37.0)
    assert sum(result.allocations_pct_gdp.values()) == pytest.approx(37.0)


def test_tax_wedge_delta_shifts_revenue_and_spending():
    result = allocate_fiscal_space(35.0, 2.0, -2.0, _equal_shares())
    assert result.total_revenue_pct_gdp == 37.0
    assert result.total_spending_pct_gdp == pytest.approx(39.0)


def test_rejects_shares_not_summing_to_one():
    bad_shares = _equal_shares()
    bad_shares["health"] += 0.5
    with pytest.raises(ValueError):
        allocate_fiscal_space(35.0, 0.0, -2.0, bad_shares)


def test_rejects_missing_category():
    incomplete = _equal_shares()
    del incomplete["health"]
    with pytest.raises(ValueError):
        allocate_fiscal_space(35.0, 0.0, -2.0, incomplete)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_fiscal_space.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.fiscal_space'`.

- [ ] **Step 3: Write `engine/fiscal_space.py`**

```python
from dataclasses import dataclass
from typing import Dict

SPENDING_CATEGORIES = ["health", "education", "welfare", "public_wage_bill", "security", "infrastructure", "public_investment"]


@dataclass
class FiscalSpaceResult:
    total_revenue_pct_gdp: float
    total_spending_pct_gdp: float
    primary_balance_pct_gdp: float
    allocations_pct_gdp: Dict[str, float]


def allocate_fiscal_space(gdp_pct_revenue: float, tax_wedge_delta_pp: float,
                           primary_balance_target_pct: float,
                           allocation_shares: Dict[str, float]) -> FiscalSpaceResult:
    """allocation_shares: fraction of total spending assigned to each of SPENDING_CATEGORIES, must sum to 1.0."""
    missing = set(SPENDING_CATEGORIES) - set(allocation_shares)
    if missing:
        raise ValueError(f"allocation_shares missing categories: {missing}")
    share_sum = sum(allocation_shares[c] for c in SPENDING_CATEGORIES)
    if abs(share_sum - 1.0) > 1e-6:
        raise ValueError(f"allocation_shares must sum to 1.0, got {share_sum}")

    total_revenue = gdp_pct_revenue + tax_wedge_delta_pp
    total_spending = total_revenue - primary_balance_target_pct

    allocations = {cat: total_spending * allocation_shares[cat] for cat in SPENDING_CATEGORIES}

    return FiscalSpaceResult(
        total_revenue_pct_gdp=total_revenue,
        total_spending_pct_gdp=total_spending,
        primary_balance_pct_gdp=primary_balance_target_pct,
        allocations_pct_gdp=allocations,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_fiscal_space.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add engine/fiscal_space.py tests/test_fiscal_space.py
git commit -m "feat: fiscal-space allocator"
```

---

### Task 10: Scenario orchestrator

**Files:**
- Create: `engine/scenario.py`
- Test: `tests/test_scenario.py`

**Interfaces:**
- Consumes: `FetchResult` (Task 2); `project_debt_path`, `DebtPathPoint` (Task 7); `okun_unemployment_gap`, `phillips_inflation`, `indexed_growth` (Task 8); `allocate_fiscal_space`, `FiscalSpaceResult`, `SPENDING_CATEGORIES` (Task 9).
- Produces: `ScenarioLevers(horizon_years=10, tax_wedge_delta_pp=0.0, primary_balance_target_pct=0.0, output_gap_path_pct=None, contingent_shocks_pct=None, indexation_delta_pp=0.0, allocation_shares=<7-category dict, default even-ish split>)`; `ScenarioResult(country_iso3, debt_path, fiscal_space_by_year, unemployment_path_pct, inflation_path_pct, nominal_wage_growth_path_pct, coverage_score)`; `run_scenario(country_iso3: str, panel: Dict[str, FetchResult], levers: ScenarioLevers) -> ScenarioResult`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_scenario.py
from data.models import FetchResult
from engine.scenario import ScenarioLevers, run_scenario


def _empty_result():
    return FetchResult(values={}, source="worldbank", from_cache=False, fetched_at=0.0, error="no data")


def _panel_with_defaults():
    keys = [
        "debt_gdp", "gdp_growth", "inflation", "unemployment",
        "real_interest_rate", "net_lending_borrowing", "government_revenue_gdp",
    ]
    return {k: _empty_result() for k in keys}


def test_run_scenario_falls_back_to_defaults_when_panel_empty():
    levers = ScenarioLevers(horizon_years=3)
    result = run_scenario("XXX", _panel_with_defaults(), levers)
    assert len(result.debt_path) == 3
    assert result.coverage_score == 0.0


def test_run_scenario_uses_real_revenue_when_available():
    panel = _panel_with_defaults()
    panel["government_revenue_gdp"] = FetchResult(
        values={2023: 29.65}, source="worldbank", from_cache=False, fetched_at=0.0, error=None
    )
    levers = ScenarioLevers(horizon_years=2)
    result = run_scenario("ESP", panel, levers)
    assert result.fiscal_space_by_year[0].total_revenue_pct_gdp == 29.65


def test_higher_indexation_delta_raises_wage_growth():
    panel = _panel_with_defaults()
    low = run_scenario("ESP", panel, ScenarioLevers(horizon_years=2, indexation_delta_pp=0.0))
    high = run_scenario("ESP", panel, ScenarioLevers(horizon_years=2, indexation_delta_pp=1.0))
    assert high.nominal_wage_growth_path_pct[0] > low.nominal_wage_growth_path_pct[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scenario.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.scenario'`.

- [ ] **Step 3: Write `engine/scenario.py`**

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from data.models import FetchResult
from engine.debt_dynamics import project_debt_path, DebtPathPoint
from engine.satellite import okun_unemployment_gap, phillips_inflation, indexed_growth
from engine.fiscal_space import allocate_fiscal_space, FiscalSpaceResult, SPENDING_CATEGORIES


@dataclass
class ScenarioLevers:
    horizon_years: int = 10
    tax_wedge_delta_pp: float = 0.0
    primary_balance_target_pct: float = 0.0
    output_gap_path_pct: Optional[List[float]] = None
    contingent_shocks_pct: Optional[List[float]] = None
    indexation_delta_pp: float = 0.0
    allocation_shares: Dict[str, float] = field(default_factory=lambda: {
        "health": 0.30, "education": 0.20, "welfare": 0.25,
        "public_wage_bill": 0.15, "security": 0.05, "infrastructure": 0.03, "public_investment": 0.02,
    })


@dataclass
class ScenarioResult:
    country_iso3: str
    debt_path: List[DebtPathPoint]
    fiscal_space_by_year: List[FiscalSpaceResult]
    unemployment_path_pct: List[float]
    inflation_path_pct: List[float]
    nominal_wage_growth_path_pct: List[float]
    coverage_score: float


def _latest_value(result: FetchResult, default: float) -> float:
    if not result.available:
        return default
    latest_year = max(result.values)
    return result.values[latest_year]


def run_scenario(country_iso3: str, panel: Dict[str, FetchResult], levers: ScenarioLevers) -> ScenarioResult:
    baseline_debt = _latest_value(panel["debt_gdp"], default=60.0)
    baseline_growth = _latest_value(panel["gdp_growth"], default=1.5)
    baseline_inflation = _latest_value(panel["inflation"], default=2.0)
    baseline_unemployment = _latest_value(panel["unemployment"], default=7.0)
    baseline_rate = _latest_value(panel["real_interest_rate"], default=2.0)
    baseline_pb = _latest_value(panel["net_lending_borrowing"], default=-2.0)
    baseline_revenue = _latest_value(panel["government_revenue_gdp"], default=35.0)

    n = levers.horizon_years
    output_gaps = levers.output_gap_path_pct or [0.0] * n
    shocks = levers.contingent_shocks_pct or [0.0] * n

    unemployment_path = []
    inflation_path = []
    wage_growth_path = []
    for gap in output_gaps:
        u_gap = okun_unemployment_gap(gap)
        unemployment_path.append(baseline_unemployment + u_gap)
        inf = phillips_inflation(baseline_inflation, u_gap)
        inflation_path.append(inf)
        wage_growth_path.append(indexed_growth(inf, levers.indexation_delta_pp))

    r_path = [baseline_rate] * n
    g_path = [baseline_growth + g for g in output_gaps]
    pb_path = [levers.primary_balance_target_pct] * n

    debt_path = project_debt_path(baseline_debt, r_path, g_path, pb_path, start_year=2025,
                                   contingent_shocks_pct=shocks)

    fiscal_space_by_year = [
        allocate_fiscal_space(baseline_revenue, levers.tax_wedge_delta_pp,
                               levers.primary_balance_target_pct, levers.allocation_shares)
        for _ in range(n)
    ]

    coverage = sum(1 for r in panel.values() if r.available) / len(panel) if panel else 0.0

    return ScenarioResult(
        country_iso3=country_iso3,
        debt_path=debt_path,
        fiscal_space_by_year=fiscal_space_by_year,
        unemployment_path_pct=unemployment_path,
        inflation_path_pct=inflation_path,
        nominal_wage_growth_path_pct=wage_growth_path,
        coverage_score=coverage,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add engine/scenario.py tests/test_scenario.py
git commit -m "feat: scenario orchestrator (real government_revenue_gdp baseline, no placeholder)"
```

---

### Task 11: ML fiscal-stress score — training pipeline + wrapper

**Files:**
- Create: `scripts/build_training_panel.py`
- Create: `scripts/train_stress_model.py`
- Create: `engine/ml_stress_score.py`
- Test: `tests/test_ml_model.py`

**Interfaces:**
- Consumes: `fetch_one`, `load_catalog` (Task 6); `load_country_list` (Task 2).
- Produces (training scripts, run once offline, not imported by the app): `download_crisis_labels() -> Dict[Tuple[str,int], int]`, `build_training_panel() -> None` (writes `data_cache/training_panel.csv`); `leave_one_country_out_cv(df: pd.DataFrame) -> dict`, `train_and_save() -> None` (writes `models/fiscal_stress_model.joblib`, `models/feature_order.json`, `models/training_scores.json`, `models/METRICS.md`).
- Produces (app-facing wrapper): `FEATURES: List[str]`; `StressScoreResult(score: Optional[float], percentile: Optional[float], available: bool, error: Optional[str]=None)`; `FiscalStressModel()` with `.available`, `.load_error`, `.score(features: Dict[str,float]) -> StressScoreResult`.

Label source: the Reinhart-Rogoff-Trebesch **"Global Crises Data by Country"** dataset (Harvard Business School, Behavioral Finance & Financial Stability project) — verified live during plan drafting at `https://www.hbs.edu/behavioral-finance-and-financial-stability/Documents/ChartData/MapCharts/20160923_global_crisis_data.xlsx` (200 OK, 1,634,548 bytes, single sheet `Sheet1`, 15,190 country-year rows, 70 countries, years 1800–2016, columns include `CC3`, `Year`, `Domestic_Debt_In_Default`, and `SOVEREIGN EXTERNAL DEBT 1: DEFAULT and RESTRUCTURINGS, 1800-2012...`). This is the closest publicly-available equivalent to a Reinhart-Rogoff crisis-dates list per design spec §4.3.

- [ ] **Step 1: Write the failing tests (synthetic, offline — no network in CI)**

```python
# tests/test_ml_model.py
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier

from scripts.train_stress_model import leave_one_country_out_cv, FEATURES
from engine.ml_stress_score import FiscalStressModel


def _synthetic_panel() -> pd.DataFrame:
    rng = np.random.RandomState(0)
    rows = []
    for country, base_debt, label_rate in [
        ("AAA", 40.0, 0.1), ("BBB", 90.0, 0.6), ("CCC", 60.0, 0.3), ("DDD", 110.0, 0.7),
    ]:
        for year in range(2005, 2013):
            label = 1 if rng.random_sample() < label_rate else 0
            rows.append({
                "country_iso3": country, "year": year, "label": label,
                "debt_gdp": base_debt + rng.normal(0, 5), "gdp_growth": rng.normal(2.0, 1.5),
                "inflation": rng.normal(2.5, 1.0), "unemployment": rng.normal(8.0, 2.0),
                "real_interest_rate": rng.normal(1.5, 1.0),
                "net_lending_borrowing": rng.normal(-2.0, 1.5),
                "corruption_control": rng.normal(0.3, 0.5),
            })
    return pd.DataFrame(rows)


def test_loco_cv_produces_non_degenerate_metrics():
    df = _synthetic_panel()
    metrics = leave_one_country_out_cv(df)
    assert metrics["n_brier_folds"] > 0
    assert 0.0 <= metrics["mean_brier"] <= 1.0
    if metrics["mean_auc"] is not None:
        assert 0.0 <= metrics["mean_auc"] <= 1.0


def test_trained_model_predicts_probabilities_in_unit_interval():
    df = _synthetic_panel()
    model = GradientBoostingClassifier(random_state=0)
    model.fit(df[FEATURES], df["label"])
    probs = model.predict_proba(df[FEATURES])[:, 1]
    assert np.all(probs >= 0.0) and np.all(probs <= 1.0)


def test_model_wrapper_reports_unavailable_when_artifact_missing(tmp_path, monkeypatch):
    import engine.ml_stress_score as mod
    monkeypatch.setattr(mod, "MODEL_PATH", tmp_path / "nonexistent.joblib")
    model = mod.FiscalStressModel()
    result = model.score({f: 0.0 for f in mod.FEATURES})
    assert result.available is False
    assert result.score is None
    assert "not found" in result.error
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ml_model.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.train_stress_model'` (or `engine.ml_stress_score`).

- [ ] **Step 3: Write `scripts/build_training_panel.py`**

```python
"""
Builds the offline training panel for the fiscal-stress model: joins a World
Bank macro panel (2003-2015, the WGI annual-coverage window) for the
countries present in the Reinhart-Rogoff-Trebesch "Global Crises Data by
Country" dataset with a debt-distress label derived from that dataset's
Domestic_Debt_In_Default and Sovereign External Debt Default columns.

Run once, offline: `python scripts/build_training_panel.py`
Writes: data_cache/training_panel.csv
"""
import csv
import io
from pathlib import Path

import openpyxl
import requests

from data.cache import DiskCache
from data.panel_builder import fetch_one, load_catalog
from data.country_list import load_country_list

CRISIS_DATA_URL = (
    "https://www.hbs.edu/behavioral-finance-and-financial-stability/"
    "Documents/ChartData/MapCharts/20160923_global_crisis_data.xlsx"
)
TRAIN_START_YEAR = 2003
TRAIN_END_YEAR = 2015
OUTPUT_PATH = Path("data_cache/training_panel.csv")
FEATURES = [
    "debt_gdp", "gdp_growth", "inflation", "unemployment",
    "real_interest_rate", "net_lending_borrowing", "corruption_control",
]


def download_crisis_labels(timeout: int = 30) -> dict:
    """Returns {(iso3, year): label}; label=1 if that country-year is flagged as a
    domestic or external sovereign debt default/restructuring in the
    Reinhart-Rogoff-Trebesch dataset, else 0."""
    resp = requests.get(CRISIS_DATA_URL, timeout=timeout)
    resp.raise_for_status()
    wb = openpyxl.load_workbook(io.BytesIO(resp.content), read_only=True, data_only=True)
    ws = wb["Sheet1"]
    labels = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        iso3, year = row[1], row[3]
        if iso3 is None or year is None:
            continue
        domestic_default = row[16]
        external_default = row[18]
        is_distress = 1 if (domestic_default == 1 or external_default == 1) else 0
        if TRAIN_START_YEAR <= year <= TRAIN_END_YEAR:
            labels[(iso3, int(year))] = is_distress
    return labels


def build_training_panel() -> None:
    labels = download_crisis_labels()
    label_countries = {iso3 for (iso3, _year) in labels}
    wb_countries = {c["iso3"] for c in load_country_list()}
    target_countries = sorted(label_countries & wb_countries)

    catalog = load_catalog()
    cache = DiskCache()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["country_iso3", "year", "label", *FEATURES])

        for iso3 in target_countries:
            panel = {key: fetch_one(iso3, key, catalog[key], TRAIN_START_YEAR, TRAIN_END_YEAR, cache)
                      for key in FEATURES}
            for year in range(TRAIN_START_YEAR, TRAIN_END_YEAR + 1):
                label = labels.get((iso3, year))
                if label is None:
                    continue
                row_values = [panel[k].values.get(year) for k in FEATURES]
                if any(v is None for v in row_values):
                    continue
                writer.writerow([iso3, year, label, *row_values])

    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    build_training_panel()
```

- [ ] **Step 4: Write `scripts/train_stress_model.py`**

```python
"""
Trains the offline fiscal-stress gradient-boosted model on
data_cache/training_panel.csv (produced by build_training_panel.py),
validates with leave-one-country-out CV, and writes the shipped model
artifact + an honest metrics report.

Run once, offline: `python scripts/train_stress_model.py`
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, brier_score_loss

TRAINING_PANEL_PATH = Path("data_cache/training_panel.csv")
MODELS_DIR = Path("models")
FEATURES = [
    "debt_gdp", "gdp_growth", "inflation", "unemployment",
    "real_interest_rate", "net_lending_borrowing", "corruption_control",
]


def leave_one_country_out_cv(df: pd.DataFrame) -> dict:
    aucs = []
    briers = []
    skipped_countries = []
    for country in sorted(df["country_iso3"].unique()):
        train_df = df[df["country_iso3"] != country]
        test_df = df[df["country_iso3"] == country]
        if test_df["label"].nunique() < 1 or train_df["label"].nunique() < 2:
            skipped_countries.append(country)
            continue
        model = GradientBoostingClassifier(random_state=0)
        model.fit(train_df[FEATURES], train_df["label"])
        probs = model.predict_proba(test_df[FEATURES])[:, 1]
        if test_df["label"].nunique() == 2:
            aucs.append(roc_auc_score(test_df["label"], probs))
        briers.append(brier_score_loss(test_df["label"], probs))
    return {
        "mean_auc": float(np.mean(aucs)) if aucs else None,
        "n_auc_folds": len(aucs),
        "mean_brier": float(np.mean(briers)) if briers else None,
        "n_brier_folds": len(briers),
        "n_skipped_countries": len(skipped_countries),
        "skipped_countries": skipped_countries,
    }


def train_and_save() -> None:
    df = pd.read_csv(TRAINING_PANEL_PATH)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    cv_metrics = leave_one_country_out_cv(df)

    final_model = GradientBoostingClassifier(random_state=0)
    final_model.fit(df[FEATURES], df["label"])
    joblib.dump(final_model, MODELS_DIR / "fiscal_stress_model.joblib")
    (MODELS_DIR / "feature_order.json").write_text(json.dumps(FEATURES))

    training_scores = (final_model.predict_proba(df[FEATURES])[:, 1] * 100.0).tolist()
    (MODELS_DIR / "training_scores.json").write_text(json.dumps(training_scores))

    n_countries = df["country_iso3"].nunique()
    n_rows = len(df)
    n_positive = int(df["label"].sum())
    metrics_md = f"""# Fiscal Stress Model — Metrics

**Training data:** {n_rows} country-year observations, {n_countries} countries,
`data_cache/training_panel.csv`. Labels derived from the Reinhart-Rogoff-Trebesch
"Global Crises Data by Country" dataset (Domestic_Debt_In_Default OR Sovereign
External Debt Default == 1), years 2003-2015 (World Bank Worldwide Governance
Indicators annual coverage window). {n_positive} of {n_rows} rows are labeled
as debt-distress years.

**Validation:** leave-one-country-out cross-validation.
- Mean AUC across {cv_metrics['n_auc_folds']} countries with both classes present
  in their held-out fold: {cv_metrics['mean_auc']}
- Mean Brier score across {cv_metrics['n_brier_folds']} evaluable countries:
  {cv_metrics['mean_brier']}
- Countries skipped (no label variation to evaluate against): {cv_metrics['n_skipped_countries']}

**Honest caveat:** this is a small, imbalanced, historically-labeled panel. The
score is a pattern-matching signal against historical debt-distress episodes,
not a certified predictor of future crises. Treated as such everywhere it is
shown in the app.
"""
    (MODELS_DIR / "METRICS.md").write_text(metrics_md)
    print(metrics_md)


if __name__ == "__main__":
    train_and_save()
```

- [ ] **Step 5: Write `engine/ml_stress_score.py`**

```python
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import numpy as np

MODEL_PATH = Path(__file__).parent.parent / "models" / "fiscal_stress_model.joblib"
TRAINING_DISTRIBUTION_PATH = Path(__file__).parent.parent / "models" / "training_scores.json"

FEATURES = [
    "debt_gdp", "gdp_growth", "inflation", "unemployment",
    "real_interest_rate", "net_lending_borrowing", "corruption_control",
]


@dataclass
class StressScoreResult:
    score: Optional[float]          # 0-100, None if model unavailable
    percentile: Optional[float]     # vs. training cross-country distribution
    available: bool
    error: Optional[str] = None


class FiscalStressModel:
    def __init__(self):
        self._model = None
        self._training_scores: List[float] = []
        self._load_error: Optional[str] = None
        self._load()

    def _load(self) -> None:
        if not MODEL_PATH.exists():
            self._load_error = f"model artifact not found at {MODEL_PATH}"
            return
        try:
            self._model = joblib.load(MODEL_PATH)
            if TRAINING_DISTRIBUTION_PATH.exists():
                self._training_scores = json.loads(TRAINING_DISTRIBUTION_PATH.read_text())
        except Exception as exc:
            self._load_error = f"failed to load model: {exc}"
            self._model = None

    @property
    def available(self) -> bool:
        return self._model is not None

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def score(self, features: Dict[str, float]) -> StressScoreResult:
        if not self.available:
            return StressScoreResult(score=None, percentile=None, available=False, error=self._load_error)

        missing = [f for f in FEATURES if f not in features]
        if missing:
            return StressScoreResult(score=None, percentile=None, available=False,
                                      error=f"missing features for scoring: {missing}")

        x = np.array([[features[f] for f in FEATURES]])
        raw = float(self._model.predict_proba(x)[0, 1])
        score = max(0.0, min(100.0, raw * 100.0))

        percentile = None
        if self._training_scores:
            percentile = 100.0 * sum(1 for s in self._training_scores if s <= score) / len(self._training_scores)

        return StressScoreResult(score=score, percentile=percentile, available=True, error=None)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_ml_model.py -v`
Expected: PASS (3 tests).

- [ ] **Step 7: Commit**

```bash
git add scripts/build_training_panel.py scripts/train_stress_model.py engine/ml_stress_score.py tests/test_ml_model.py
git commit -m "feat: ML fiscal-stress model (Reinhart-Rogoff-Trebesch-labeled training pipeline + wrapper)"
```

- [ ] **Step 8 (offline, run once before using the app's stress score — not part of the automated test suite):**

```bash
python scripts/build_training_panel.py
python scripts/train_stress_model.py
git add models/fiscal_stress_model.joblib models/feature_order.json models/training_scores.json models/METRICS.md
git commit -m "chore: ship trained fiscal-stress model artifact"
```

---

### Task 12: Pareto / multi-objective explorer

**Files:**
- Create: `engine/pareto.py`
- Test: `tests/test_pareto.py`

**Interfaces:**
- Consumes: `ScenarioLevers`, `run_scenario` (Task 10).
- Produces: `LEVER_BOUNDS: Dict[str, Tuple[float,float]]` (`tax_wedge_delta_pp`, `primary_balance_target_pct`, `indexation_delta_pp`, `public_wage_bill_share_delta`); `ParetoPoint(levers: Dict[str,float], objectives: Dict[str,float])`; `compute_pareto_frontier(country_iso3, panel, base_levers, lever_bounds=None, population_size=40, generations=30) -> List[ParetoPoint]`.

Design note: NSGA-II optimizes 3 objectives here — `final_debt_gdp_pct` (minimize), `health_education_funding_pct_gdp` (maximize, i.e. minimize its negation), and `welfare_wagebill_pct_gdp` (maximize, i.e. minimize its negation) — combining the spec's "public headcount" and "welfare spend" objectives into one social-spending-pressure objective for tractability. This simplification is documented here and must also be documented in the Data & Methodology tab (Task 14).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_pareto.py
from data.models import FetchResult
from engine.scenario import ScenarioLevers
from engine.pareto import compute_pareto_frontier, LEVER_BOUNDS


def _panel_with_defaults():
    keys = [
        "debt_gdp", "gdp_growth", "inflation", "unemployment",
        "real_interest_rate", "net_lending_borrowing", "government_revenue_gdp",
    ]
    return {k: FetchResult(values={}, source="worldbank", from_cache=False, fetched_at=0.0, error="no data")
            for k in keys}


def _to_min_vector(point):
    o = point.objectives
    return (o["final_debt_gdp_pct"], -o["health_education_funding_pct_gdp"], -o["welfare_wagebill_pct_gdp"])


def _dominates(a, b):
    return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))


def test_frontier_is_non_dominated():
    panel = _panel_with_defaults()
    base_levers = ScenarioLevers(horizon_years=5)
    frontier = compute_pareto_frontier("ESP", panel, base_levers, population_size=12, generations=5)
    assert len(frontier) > 0
    vectors = [_to_min_vector(p) for p in frontier]
    for i, vi in enumerate(vectors):
        for j, vj in enumerate(vectors):
            if i != j:
                assert not _dominates(vj, vi), f"point {i} dominated by point {j}"


def test_tighter_bounds_never_beat_looser_bounds():
    panel = _panel_with_defaults()
    base_levers = ScenarioLevers(horizon_years=5)
    tight_bounds = {k: (v[0] / 2.0, v[1] / 2.0) for k, v in LEVER_BOUNDS.items()}

    loose_frontier = compute_pareto_frontier("ESP", panel, base_levers, lever_bounds=LEVER_BOUNDS,
                                              population_size=12, generations=5)
    tight_frontier = compute_pareto_frontier("ESP", panel, base_levers, lever_bounds=tight_bounds,
                                              population_size=12, generations=5)

    best_loose = min(p.objectives["final_debt_gdp_pct"] for p in loose_frontier)
    best_tight = min(p.objectives["final_debt_gdp_pct"] for p in tight_frontier)
    assert best_tight >= best_loose - 1e-6
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pareto.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.pareto'`.

- [ ] **Step 3: Write `engine/pareto.py`**

```python
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.optimize import minimize

from data.models import FetchResult
from engine.scenario import ScenarioLevers, run_scenario

LEVER_BOUNDS = {
    "tax_wedge_delta_pp": (-5.0, 5.0),
    "primary_balance_target_pct": (-4.0, 4.0),
    "indexation_delta_pp": (-1.5, 1.0),
    "public_wage_bill_share_delta": (-0.10, 0.10),
}


@dataclass
class ParetoPoint:
    levers: Dict[str, float]
    objectives: Dict[str, float]


def _shift_allocation(base_shares: Dict[str, float], wage_bill_delta: float) -> Dict[str, float]:
    shares = dict(base_shares)
    shares["public_wage_bill"] = max(0.0, shares["public_wage_bill"] + wage_bill_delta)
    other_keys = [k for k in shares if k != "public_wage_bill"]
    remaining = 1.0 - shares["public_wage_bill"]
    other_sum = sum(shares[k] for k in other_keys)
    if other_sum <= 0:
        raise ValueError("allocation shares collapsed to zero while shifting public_wage_bill")
    for k in other_keys:
        shares[k] = shares[k] / other_sum * remaining
    return shares


class _ScenarioProblem(Problem):
    def __init__(self, country_iso3: str, panel: Dict[str, FetchResult], base_levers: ScenarioLevers,
                 lever_bounds: Dict[str, Tuple[float, float]]):
        self.country_iso3 = country_iso3
        self.panel = panel
        self.base_levers = base_levers
        self.lever_keys = list(lever_bounds.keys())
        xl = np.array([lever_bounds[k][0] for k in self.lever_keys])
        xu = np.array([lever_bounds[k][1] for k in self.lever_keys])
        super().__init__(n_var=len(self.lever_keys), n_obj=3, n_ieq_constr=0, xl=xl, xu=xu)

    def _evaluate(self, X, out, *args, **kwargs):
        f1 = np.zeros(X.shape[0])
        f2 = np.zeros(X.shape[0])
        f3 = np.zeros(X.shape[0])

        for i, row in enumerate(X):
            levers = ScenarioLevers(
                horizon_years=self.base_levers.horizon_years,
                tax_wedge_delta_pp=row[self.lever_keys.index("tax_wedge_delta_pp")],
                primary_balance_target_pct=row[self.lever_keys.index("primary_balance_target_pct")],
                indexation_delta_pp=row[self.lever_keys.index("indexation_delta_pp")],
                allocation_shares=_shift_allocation(self.base_levers.allocation_shares,
                                                     row[self.lever_keys.index("public_wage_bill_share_delta")]),
            )
            result = run_scenario(self.country_iso3, self.panel, levers)
            f1[i] = result.debt_path[-1].debt_gdp_pct
            last_alloc = result.fiscal_space_by_year[-1].allocations_pct_gdp
            f2[i] = -(last_alloc["health"] + last_alloc["education"])
            f3[i] = -(last_alloc["welfare"] + last_alloc["public_wage_bill"])

        out["F"] = np.column_stack([f1, f2, f3])


def compute_pareto_frontier(country_iso3: str, panel: Dict[str, FetchResult], base_levers: ScenarioLevers,
                             lever_bounds: Dict[str, Tuple[float, float]] = None,
                             population_size: int = 40, generations: int = 30) -> List[ParetoPoint]:
    bounds = lever_bounds or LEVER_BOUNDS
    problem = _ScenarioProblem(country_iso3, panel, base_levers, bounds)
    algorithm = NSGA2(pop_size=population_size)
    res = minimize(problem, algorithm, ("n_gen", generations), seed=1, verbose=False)

    keys = list(bounds.keys())
    X = res.X if res.X.ndim == 2 else res.X.reshape(1, -1)
    F = res.F if res.F.ndim == 2 else res.F.reshape(1, -1)

    points = []
    for x_row, f_row in zip(X, F):
        levers = {k: float(v) for k, v in zip(keys, x_row)}
        objectives = {
            "final_debt_gdp_pct": float(f_row[0]),
            "health_education_funding_pct_gdp": float(-f_row[1]),
            "welfare_wagebill_pct_gdp": float(-f_row[2]),
        }
        points.append(ParetoPoint(levers=levers, objectives=objectives))
    return points
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_pareto.py -v`
Expected: PASS (2 tests). (NSGA-II is stochastic in general, but `seed=1` makes this deterministic; if the environment's pymoo/numpy version changes the seeded sequence, re-run once — the assertions are about invariants of the algorithm, not exact numbers.)

- [ ] **Step 5: Commit**

```bash
git add engine/pareto.py tests/test_pareto.py
git commit -m "feat: NSGA-II Pareto frontier explorer"
```

---

### Task 13: Personas — retiree, mortgage banker, house-buyer/landlord, narrative

**Files:**
- Create: `personas/retiree.py`
- Create: `personas/mortgage_banker.py`
- Create: `personas/house_buyer_landlord.py`
- Create: `personas/narrative.py`
- Test: `tests/test_personas.py`

**Interfaces:**
- Consumes: `ScenarioResult` (Task 10), `StressScoreResult` (Task 11).
- Produces: `RetireeYearView`, `RetireeDashboard`, `build_retiree_dashboard(scenario, stress, baseline_health_exp_gdp_pct) -> RetireeDashboard`.
- Produces: `MORTGAGE_SPREAD_PP`, `DEFAULT_RISK_UNEMPLOYMENT_WEIGHT`, `DEFAULT_RISK_RATE_WEIGHT`; `french_amortization_payment(principal, annual_rate_pct, term_years) -> float`; `MortgageYearView`, `build_mortgage_dashboard(sovereign_rate_path_pct, unemployment_path_pct, years, loan_principal, loan_term_years, baseline_unemployment_pct) -> List[MortgageYearView]`.
- Produces: `BuyToLiveYearView`, `build_buy_to_live_view(...)`; `BuyToLetYearView`, `build_buy_to_let_view(house_price_index_path: Dict[int,float], years: List[int]) -> List[BuyToLetYearView]`.
- Produces: `render_template_narrative(persona, **kwargs) -> str`; `llm_available() -> bool`; `render_narrative(persona, scenario_summary, **template_kwargs) -> str`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_personas.py
from personas.mortgage_banker import french_amortization_payment, build_mortgage_dashboard
from personas.house_buyer_landlord import build_buy_to_let_view
from personas.retiree import build_retiree_dashboard
from engine.scenario import ScenarioResult
from engine.debt_dynamics import DebtPathPoint
from engine.fiscal_space import allocate_fiscal_space, SPENDING_CATEGORIES
from engine.ml_stress_score import StressScoreResult


def test_french_amortization_known_case():
    payment = french_amortization_payment(200000, 3.0, 25)
    assert 900 < payment < 1000


def test_mortgage_dashboard_risk_increases_with_unemployment():
    views = build_mortgage_dashboard(
        sovereign_rate_path_pct=[2.0, 2.0], unemployment_path_pct=[7.0, 12.0],
        years=[2025, 2026], loan_principal=200000, loan_term_years=25, baseline_unemployment_pct=7.0,
    )
    assert views[1].default_risk_proxy > views[0].default_risk_proxy


def test_buy_to_let_reports_na_rental_yield_and_real_growth():
    views = build_buy_to_let_view({2020: 100.0, 2021: 110.0}, [2020, 2021])
    assert views[1].house_price_growth_pct == 10.0
    assert "N/A" in views[1].rental_yield_pct


def _fake_scenario():
    shares = {c: 1.0 / len(SPENDING_CATEGORIES) for c in SPENDING_CATEGORIES}
    fiscal = [allocate_fiscal_space(35.0, 0.0, -2.0, shares) for _ in range(2)]
    debt_path = [
        DebtPathPoint(2025, 80.0, 2.0, 2.0, -2.0, 0.0),
        DebtPathPoint(2026, 81.0, 2.0, 2.0, -2.0, 0.0),
    ]
    return ScenarioResult(
        country_iso3="ESP", debt_path=debt_path, fiscal_space_by_year=fiscal,
        unemployment_path_pct=[7.0, 7.0], inflation_path_pct=[2.0, 2.0],
        nominal_wage_growth_path_pct=[2.0, 2.0], coverage_score=1.0,
    )


def test_retiree_dashboard_tracks_real_pension_purchasing_power():
    scenario = _fake_scenario()
    stress = StressScoreResult(score=40.0, percentile=50.0, available=True)
    dashboard = build_retiree_dashboard(scenario, stress, baseline_health_exp_gdp_pct=7.0)
    assert len(dashboard.years) == 2
    # wage growth == inflation each year -> real index stays at 100
    assert abs(dashboard.years[-1].real_pension_index - 100.0) < 1e-6
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_personas.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'personas.mortgage_banker'`.

- [ ] **Step 3: Write `personas/mortgage_banker.py`**

```python
from dataclasses import dataclass
from typing import List

MORTGAGE_SPREAD_PP = 1.5  # calibrated default: typical mortgage rate over the sovereign real-rate baseline; not country-specific
DEFAULT_RISK_UNEMPLOYMENT_WEIGHT = 0.6  # calibrated default, not empirically fit
DEFAULT_RISK_RATE_WEIGHT = 0.4          # calibrated default, not empirically fit


@dataclass
class MortgageYearView:
    year: int
    mortgage_rate_pct: float
    monthly_payment: float
    default_risk_proxy: float


def french_amortization_payment(principal: float, annual_rate_pct: float, term_years: int) -> float:
    monthly_rate = (annual_rate_pct / 100.0) / 12.0
    n_payments = term_years * 12
    if monthly_rate == 0:
        return principal / n_payments
    return principal * monthly_rate / (1 - (1 + monthly_rate) ** (-n_payments))


def build_mortgage_dashboard(sovereign_rate_path_pct: List[float], unemployment_path_pct: List[float],
                              years: List[int], loan_principal: float, loan_term_years: int,
                              baseline_unemployment_pct: float) -> List[MortgageYearView]:
    views = []
    baseline_mortgage_rate = sovereign_rate_path_pct[0] + MORTGAGE_SPREAD_PP
    for year, rate, unemployment in zip(years, sovereign_rate_path_pct, unemployment_path_pct):
        mortgage_rate = rate + MORTGAGE_SPREAD_PP
        payment = french_amortization_payment(loan_principal, mortgage_rate, loan_term_years)
        unemployment_gap = unemployment - baseline_unemployment_pct
        rate_gap = mortgage_rate - baseline_mortgage_rate
        risk = (DEFAULT_RISK_UNEMPLOYMENT_WEIGHT * max(0.0, unemployment_gap)
                + DEFAULT_RISK_RATE_WEIGHT * max(0.0, rate_gap))
        views.append(MortgageYearView(year=year, mortgage_rate_pct=mortgage_rate,
                                       monthly_payment=payment, default_risk_proxy=risk))
    return views
```

- [ ] **Step 4: Write `personas/house_buyer_landlord.py`**

```python
from dataclasses import dataclass
from typing import Dict, List, Optional

from personas.mortgage_banker import french_amortization_payment, MORTGAGE_SPREAD_PP


@dataclass
class BuyToLiveYearView:
    year: int
    monthly_payment: float
    payment_to_income_pct: Optional[float]


@dataclass
class BuyToLetYearView:
    year: int
    house_price_index: Optional[float]
    house_price_growth_pct: Optional[float]
    rental_yield_pct: str


def build_buy_to_live_view(sovereign_rate_path_pct: List[float], years: List[int], home_price: float,
                            down_payment_pct: float, loan_term_years: int,
                            monthly_household_income: Optional[float]) -> List[BuyToLiveYearView]:
    principal = home_price * (1 - down_payment_pct / 100.0)
    views = []
    for year, rate in zip(years, sovereign_rate_path_pct):
        mortgage_rate = rate + MORTGAGE_SPREAD_PP
        payment = french_amortization_payment(principal, mortgage_rate, loan_term_years)
        ratio = (payment / monthly_household_income * 100.0) if monthly_household_income else None
        views.append(BuyToLiveYearView(year=year, monthly_payment=payment, payment_to_income_pct=ratio))
    return views


def build_buy_to_let_view(house_price_index_path: Dict[int, float], years: List[int]) -> List[BuyToLetYearView]:
    sorted_years = sorted(house_price_index_path)
    base_value = house_price_index_path.get(sorted_years[0]) if sorted_years else None
    views = []
    for year in years:
        value = house_price_index_path.get(year)
        growth = (value / base_value - 1.0) * 100.0 if (value is not None and base_value) else None
        views.append(BuyToLetYearView(
            year=year, house_price_index=value, house_price_growth_pct=growth,
            rental_yield_pct="N/A -- no rent-price data source integrated in this MVP",
        ))
    return views
```

- [ ] **Step 5: Write `personas/retiree.py`**

```python
from dataclasses import dataclass
from typing import List, Optional

from engine.scenario import ScenarioResult
from engine.ml_stress_score import StressScoreResult


@dataclass
class RetireeYearView:
    year: int
    nominal_pension_index: float
    real_pension_index: float
    health_funding_adequacy_pct: Optional[float]


@dataclass
class RetireeDashboard:
    years: List[RetireeYearView]
    fiscal_stress: StressScoreResult
    health_baseline_pct_gdp: Optional[float]


def build_retiree_dashboard(scenario: ScenarioResult, stress: StressScoreResult,
                             baseline_health_exp_gdp_pct: Optional[float]) -> RetireeDashboard:
    """Pension growth uses the same indexation lever as wages (design spec §4.2's
    wage/pension indexation rule) -- this MVP does not model a separate
    pension-specific indexation rule."""
    nominal_index = 100.0
    real_index = 100.0
    years = []
    for i, wage_growth in enumerate(scenario.nominal_wage_growth_path_pct):
        inflation = scenario.inflation_path_pct[i]
        nominal_index *= (1.0 + wage_growth / 100.0)
        real_index *= (1.0 + wage_growth / 100.0) / (1.0 + inflation / 100.0)

        adequacy = None
        if baseline_health_exp_gdp_pct and baseline_health_exp_gdp_pct > 0:
            allocated = scenario.fiscal_space_by_year[i].allocations_pct_gdp["health"]
            adequacy = allocated / baseline_health_exp_gdp_pct * 100.0

        years.append(RetireeYearView(
            year=scenario.debt_path[i].year,
            nominal_pension_index=nominal_index,
            real_pension_index=real_index,
            health_funding_adequacy_pct=adequacy,
        ))

    return RetireeDashboard(years=years, fiscal_stress=stress, health_baseline_pct_gdp=baseline_health_exp_gdp_pct)
```

- [ ] **Step 6: Write `personas/narrative.py`**

```python
import os
from typing import Optional

TEMPLATES = {
    "retiree": (
        "By {year}, your pension's real purchasing power is projected at {real_index:.1f} "
        "(base=100 today), and health funding sits at {adequacy} of its current level."
    ),
    "mortgage_banker": (
        "By {year}, the projected mortgage rate is {rate:.2f}%, monthly payment "
        "{payment:.0f}, default-risk proxy {risk:.2f}."
    ),
}


def render_template_narrative(persona: str, **kwargs) -> str:
    template = TEMPLATES.get(persona)
    if template is None:
        return "No narrative template available for this persona."
    return template.format(**kwargs)


def llm_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def render_llm_narrative(persona: str, scenario_summary: str) -> Optional[str]:
    if not llm_available():
        return None
    import anthropic
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": (
                f"Write a short (3-4 sentence), plain-English narrative for a {persona} persona "
                f"reading a sovereign fiscal scenario dashboard. Never issue advice or a "
                f"buy/sell/vote recommendation -- describe conditional projections only. "
                f"Scenario summary:\n{scenario_summary}"
            ),
        }],
    )
    return message.content[0].text


def render_narrative(persona: str, scenario_summary: str, **template_kwargs) -> str:
    if llm_available():
        llm_text = render_llm_narrative(persona, scenario_summary)
        if llm_text:
            return llm_text
    return render_template_narrative(persona, **template_kwargs)
```

- [ ] **Step 7: Run test to verify it passes**

Run: `pytest tests/test_personas.py -v`
Expected: PASS (4 tests).

- [ ] **Step 8: Commit**

```bash
git add personas/retiree.py personas/mortgage_banker.py personas/house_buyer_landlord.py personas/narrative.py tests/test_personas.py
git commit -m "feat: retiree, mortgage banker, house-buyer/landlord personas + narrative layer"
```

---

### Task 14: Streamlit app shell, README, and manual smoke test

**Files:**
- Create: `app/main.py`
- Create: `app/tab_retiree.py`
- Create: `app/tab_mortgage_banker.py`
- Create: `app/tab_house_buyer_landlord.py`
- Create: `app/tab_model_lab.py`
- Create: `app/tab_methodology.py`
- Create: `README.md`

**Interfaces:**
- Consumes everything from Tasks 2–13.
- Produces: `app/main.py:main()` — the `streamlit run app/main.py` entrypoint; each `app/tab_*.py` exposes a `render(...)` function called from `main()` with `st.session_state["country_iso3"]` and `st.session_state["levers"]` shared across every tab.

- [ ] **Step 1: Write `app/tab_retiree.py`**

```python
import streamlit as st

from personas.retiree import build_retiree_dashboard
from personas.narrative import render_narrative


def render(scenario, stress_result, panel):
    st.header("Retiree view")

    baseline_health = None
    if panel["health_exp_gdp"].available:
        baseline_health = panel["health_exp_gdp"].values[max(panel["health_exp_gdp"].values)]

    dashboard = build_retiree_dashboard(scenario, stress_result, baseline_health)

    years = [y.year for y in dashboard.years]
    real_index = [y.real_pension_index for y in dashboard.years]
    st.subheader("Pension purchasing power (real, base=100 today)")
    st.line_chart({"Real pension index": dict(zip(years, real_index))})

    if stress_result.available:
        st.metric("Fiscal stress score (0-100)", f"{stress_result.score:.0f}",
                  help="Pattern-matching signal vs. historical cross-country debt-distress episodes -- not a certified predictor.")
    else:
        st.info(f"Fiscal stress model unavailable: {stress_result.error}")

    adequacy = dashboard.years[-1].health_funding_adequacy_pct
    if adequacy is not None:
        st.metric(f"Health funding adequacy in {years[-1]} vs. today", f"{adequacy:.0f}%")
    else:
        st.info("N/A -- not available for this country")

    st.caption(render_narrative(
        "retiree",
        scenario_summary=f"real pension index reaches {real_index[-1]:.1f} by {years[-1]}",
        year=years[-1], real_index=real_index[-1],
        adequacy=f"{adequacy:.0f}%" if adequacy is not None else "N/A",
    ))
```

- [ ] **Step 2: Write `app/tab_mortgage_banker.py`**

```python
import streamlit as st

from personas.mortgage_banker import build_mortgage_dashboard
from personas.narrative import render_narrative


def render(scenario, panel):
    st.header("Mortgage banker view")

    loan_principal = st.number_input("Loan principal", min_value=10_000, value=200_000, step=10_000)
    loan_term_years = st.slider("Loan term (years)", 5, 40, 25)

    years = [p.year for p in scenario.debt_path]
    rate_path = [p.interest_rate_pct for p in scenario.debt_path]
    baseline_unemployment = scenario.unemployment_path_pct[0] if scenario.unemployment_path_pct else 0.0

    views = build_mortgage_dashboard(rate_path, scenario.unemployment_path_pct, years,
                                      loan_principal, loan_term_years, baseline_unemployment)

    st.subheader("Projected mortgage rate and monthly payment")
    st.line_chart({"Mortgage rate (%)": {v.year: v.mortgage_rate_pct for v in views}})
    st.line_chart({"Monthly payment": {v.year: v.monthly_payment for v in views}})

    st.subheader("Default-risk proxy (calibrated default weights, not empirically fit)")
    st.line_chart({"Default-risk proxy": {v.year: v.default_risk_proxy for v in views}})

    st.caption(render_narrative(
        "mortgage_banker",
        scenario_summary=f"rate reaches {views[-1].mortgage_rate_pct:.2f}% by {views[-1].year}",
        year=views[-1].year, rate=views[-1].mortgage_rate_pct,
        payment=views[-1].monthly_payment, risk=views[-1].default_risk_proxy,
    ))
```

- [ ] **Step 3: Write `app/tab_house_buyer_landlord.py`**

```python
import streamlit as st

from personas.house_buyer_landlord import build_buy_to_live_view, build_buy_to_let_view


def render(scenario, panel):
    st.header("House-buyer / Landlord view")
    mode = st.radio("I am a...", ["Buy-to-live", "Buy-to-let"], horizontal=True)

    years = [p.year for p in scenario.debt_path]
    rate_path = [p.interest_rate_pct for p in scenario.debt_path]

    if mode == "Buy-to-live":
        home_price = st.number_input("Home price", min_value=20_000, value=250_000, step=10_000)
        down_payment_pct = st.slider("Down payment (%)", 0, 50, 20)
        loan_term_years = st.slider("Loan term (years)", 5, 40, 25)
        monthly_income = st.number_input("Monthly household income (optional, 0 = skip)", min_value=0, value=0, step=100)

        views = build_buy_to_live_view(rate_path, years, home_price, down_payment_pct, loan_term_years,
                                        monthly_income or None)
        st.line_chart({"Monthly payment": {v.year: v.monthly_payment for v in views}})
        if views[-1].payment_to_income_pct is not None:
            st.metric("Payment-to-income", f"{views[-1].payment_to_income_pct:.1f}%")
        else:
            st.info("Enter monthly household income to see payment-to-income ratio.")
    else:
        house_price_result = panel["house_price_index"]
        if not house_price_result.available:
            st.warning("N/A -- not available for this country")
            return
        views = build_buy_to_let_view(house_price_result.values, years)
        st.line_chart({"House price index": {v.year: v.house_price_index for v in views if v.house_price_index is not None}})
        growth = views[-1].house_price_growth_pct
        st.metric("Cumulative price growth vs. today", f"{growth:.1f}%" if growth is not None else "N/A")
        st.info(f"Rental yield: {views[-1].rental_yield_pct}")
```

- [ ] **Step 4: Write `app/tab_model_lab.py`**

```python
import streamlit as st

from engine.pareto import compute_pareto_frontier


def render(country_iso3, panel, levers):
    st.header("Model Lab -- Pareto frontier explorer")
    st.caption(
        "NSGA-II over policy levers vs. objectives (final debt/GDP; health+education "
        "funding; welfare+public-wage-bill spending, combined into one social-spending-"
        "pressure objective for tractability). Click a frontier point to load its levers."
    )

    if st.button("Compute Pareto frontier"):
        with st.spinner("Running NSGA-II..."):
            frontier = compute_pareto_frontier(country_iso3, panel, levers)
        st.session_state["pareto_frontier"] = frontier

    frontier = st.session_state.get("pareto_frontier")
    if not frontier:
        st.info("Click 'Compute Pareto frontier' to generate the trade-off explorer.")
        return

    rows = [{**p.levers, **p.objectives} for p in frontier]
    st.dataframe(rows)

    options = list(range(len(frontier)))
    chosen = st.selectbox("Load a frontier point into the main scenario controls", options,
                           format_func=lambda i: f"Point {i}: debt/GDP={frontier[i].objectives['final_debt_gdp_pct']:.1f}%")
    if st.button("Load selected point"):
        point = frontier[chosen]
        levers.tax_wedge_delta_pp = point.levers["tax_wedge_delta_pp"]
        levers.primary_balance_target_pct = point.levers["primary_balance_target_pct"]
        levers.indexation_delta_pp = point.levers["indexation_delta_pp"]
        st.success("Levers updated -- see the sidebar.")
```

- [ ] **Step 5: Write `app/tab_methodology.py`**

```python
import streamlit as st

from data.panel_builder import load_catalog
from engine.satellite import OKUN_COEFFICIENT, PHILLIPS_SLOPE
from personas.mortgage_banker import MORTGAGE_SPREAD_PP, DEFAULT_RISK_UNEMPLOYMENT_WEIGHT, DEFAULT_RISK_RATE_WEIGHT


def render(panel, coverage, stress_model):
    st.header("Data & Methodology")

    st.subheader("Indicator coverage for this country")
    catalog = load_catalog()
    rows = []
    for key, spec in catalog.items():
        result = panel.get(key)
        rows.append({
            "indicator": spec["label"],
            "block": spec["block"],
            "available": result.available if result else False,
            "note": spec.get("note", ""),
        })
    st.dataframe(rows)
    st.metric("Overall coverage score", f"{coverage*100:.0f}%")

    st.subheader("Engine constants")
    st.write({
        "Okun coefficient": f"{OKUN_COEFFICIENT} (calibrated default, literature range 0.3-0.5, not country-specific)",
        "Phillips slope": f"{PHILLIPS_SLOPE} (calibrated default, not country-specific)",
        "Mortgage spread over sovereign real rate (pp)": f"{MORTGAGE_SPREAD_PP} (calibrated default, not country-specific)",
        "Default-risk proxy weights": (
            f"unemployment={DEFAULT_RISK_UNEMPLOYMENT_WEIGHT}, rate={DEFAULT_RISK_RATE_WEIGHT} "
            "(calibrated defaults, not empirically fit)"
        ),
    })

    st.subheader("ML fiscal-stress model")
    if stress_model.available:
        try:
            st.markdown(open("models/METRICS.md").read())
        except FileNotFoundError:
            st.info("Model loaded but models/METRICS.md not found.")
    else:
        st.warning(f"Model unavailable: {stress_model.load_error}")

    st.subheader("Known gaps")
    st.markdown(
        "- COFOG functional spending detail (public wage bill, security, welfare, pensions) "
        "is EU/OECD-only.\n"
        "- Rental yield is not modeled -- no rent-price data source integrated in this MVP.\n"
        "- Infrastructure maintenance vs. renovation split is not available for any country "
        "in this MVP's catalog.\n"
        "- The Model Lab's Pareto explorer combines public-headcount and welfare-spend "
        "objectives into one social-spending-pressure objective (see engine/pareto.py).\n"
    )
```

- [ ] **Step 6: Write `app/main.py`**

```python
import streamlit as st

from data.cache import DiskCache
from data.country_list import load_country_list
from data.panel_builder import build_country_panel, coverage_score
from engine.scenario import ScenarioLevers, run_scenario
from engine.ml_stress_score import FiscalStressModel
from app import tab_retiree, tab_mortgage_banker, tab_house_buyer_landlord, tab_model_lab, tab_methodology

st.set_page_config(page_title="Sovereign Fiscal Scenario Explorer", layout="wide")


def _init_session_state():
    if "country_iso3" not in st.session_state:
        st.session_state.country_iso3 = "ESP"
    if "levers" not in st.session_state:
        st.session_state.levers = ScenarioLevers()


def main():
    _init_session_state()
    cache = DiskCache()
    stress_model = FiscalStressModel()

    countries = load_country_list()
    country_names = {c["iso3"]: c["name"] for c in countries}
    sorted_iso3 = sorted(country_names)

    st.sidebar.title("Country & scenario")
    default_index = sorted_iso3.index(st.session_state.country_iso3) if st.session_state.country_iso3 in country_names else 0
    selected_iso3 = st.sidebar.selectbox(
        "Country", options=sorted_iso3, format_func=lambda iso3: country_names[iso3], index=default_index,
    )
    st.session_state.country_iso3 = selected_iso3

    force_refresh = st.sidebar.button("Refresh data")
    panel = build_country_panel(selected_iso3, cache=cache, force_refresh=force_refresh)
    score = coverage_score(panel)
    if score < 0.6:
        st.sidebar.warning(f"Limited data coverage for this country ({score*100:.0f}%) -- "
                            "several metrics will show as unavailable.")
    else:
        st.sidebar.caption(f"Data coverage: {score*100:.0f}%")

    levers = st.session_state.levers
    levers.horizon_years = st.sidebar.slider("Horizon (years)", 1, 25, levers.horizon_years)
    levers.tax_wedge_delta_pp = st.sidebar.slider("Tax wedge delta (pp)", -5.0, 5.0, levers.tax_wedge_delta_pp)
    levers.primary_balance_target_pct = st.sidebar.slider(
        "Primary balance target (% GDP)", -4.0, 4.0, levers.primary_balance_target_pct)
    levers.indexation_delta_pp = st.sidebar.slider(
        "Pension/wage indexation delta (pp)", -1.5, 1.0, levers.indexation_delta_pp)

    scenario = run_scenario(selected_iso3, panel, levers)

    corruption = panel["corruption_control"]
    corruption_value = corruption.values[max(corruption.values)] if corruption.available else 0.0
    stress_result = stress_model.score({
        "debt_gdp": scenario.debt_path[-1].debt_gdp_pct,
        "gdp_growth": scenario.debt_path[-1].growth_rate_pct,
        "inflation": scenario.inflation_path_pct[-1] if scenario.inflation_path_pct else 0.0,
        "unemployment": scenario.unemployment_path_pct[-1] if scenario.unemployment_path_pct else 0.0,
        "real_interest_rate": scenario.debt_path[-1].interest_rate_pct,
        "net_lending_borrowing": scenario.debt_path[-1].primary_balance_pct,
        "corruption_control": corruption_value,
    })

    tabs = st.tabs(["Retiree", "Mortgage Banker", "House-buyer/Landlord", "Model Lab", "Data & Methodology"])
    with tabs[0]:
        tab_retiree.render(scenario, stress_result, panel)
    with tabs[1]:
        tab_mortgage_banker.render(scenario, panel)
    with tabs[2]:
        tab_house_buyer_landlord.render(scenario, panel)
    with tabs[3]:
        tab_model_lab.render(selected_iso3, panel, levers)
    with tabs[4]:
        tab_methodology.render(panel, score, stress_model)


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: Write `README.md`**

```markdown
# Sovereign Fiscal Scenario Explorer

Prototype: explore a country's fiscal sustainability under user-controlled
policy scenarios, through persona-specific dashboards. Real data only
(World Bank, Eurostat, OECD public APIs) -- see the in-app "Data &
Methodology" tab for sources, coverage, and known gaps.

## Setup

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

## Train the ML fiscal-stress model (one-time, offline)

    python scripts/build_training_panel.py
    python scripts/train_stress_model.py

This writes `models/fiscal_stress_model.joblib`, `models/feature_order.json`,
`models/training_scores.json`, and `models/METRICS.md`. Requires network
access (World Bank API + the Reinhart-Rogoff-Trebesch crisis dataset). The
app runs without this step -- the fiscal-stress score just shows
"model unavailable" until it's done.

## Run

    streamlit run app/main.py

## Manual smoke test

Run the app locally for two countries with very different data coverage and
confirm graceful degradation, all 5 tabs render, and nothing crashes:

1. Select **Spain (ESP)** in the sidebar -- expect a high coverage badge, all
   tabs populated, house-price and COFOG-derived metrics present.
2. Select a smaller/poorer, non-EU/OECD country (e.g. **Haiti (HTI)** or
   **Chad (TCD)**) -- expect a lower coverage badge, several metrics showing
   "N/A -- not available for this country" instead of fabricated numbers,
   and every tab still rendering without error.
3. Click "Refresh data" in the sidebar for both -- confirm it re-fetches
   without crashing.
4. Move each scenario lever to its extremes and confirm every tab updates
   consistently (shared `session_state`).
5. In the House-buyer/Landlord tab, toggle to "Buy-to-let" for a non-EU
   country -- confirm it shows "N/A -- not available for this country"
   rather than a fabricated rental yield.

## Tests

    pytest
```

- [ ] **Step 8: Automated smoke check — app boots without a Python exception**

```bash
streamlit run app/main.py --server.headless true &
sleep 5
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8501
kill %1
```

Expected: prints `200`.

- [ ] **Step 9: Run the full test suite one more time**

Run: `pytest -v`
Expected: PASS (all tests across every task).

- [ ] **Step 10: Commit**

```bash
git add app/main.py app/tab_retiree.py app/tab_mortgage_banker.py app/tab_house_buyer_landlord.py app/tab_model_lab.py app/tab_methodology.py README.md
git commit -m "feat: Streamlit app shell, 5 tabs, README with manual smoke test"
```

---

## Self-Review

**1. Spec coverage.**
- §3.1 catalog + fallback semantics → Task 2 (single-source-per-key, honestly degrades to N/A — documented deviation from the "fallback column" framing, still meets the no-fabrication constraint).
- §3.2 coverage badge → Task 6 (`coverage_score`) + Task 14 (`app/main.py` sidebar banner).
- §3.3 caching → Task 2 (`DiskCache`, JSON not Parquet — both allowed by spec) + Task 14 ("Refresh data" button).
- §4.1 debt dynamics → Task 7.
- §4.2 satellite equations + fiscal-space allocator → Tasks 8–9; constants surfaced in Task 14's methodology tab.
- §4.3 ML stress score → Task 11 (real Reinhart-Rogoff-Trebesch-labeled training pipeline, LOCO-CV, honest `METRICS.md`).
- §4.4 Pareto explorer → Task 12 (documented 3-objective simplification).
- §4.5 GenAI narrative layer → Task 13 (`personas/narrative.py`, template default + `ANTHROPIC_API_KEY`-gated LLM hook).
- §5 personas/UI → Tasks 13–14 (retiree, mortgage banker, house-buyer/landlord with buy-to-live/buy-to-let toggle, Model Lab, Data & Methodology).
- §6 error handling → N/A sentinels throughout Tasks 2–6; cache fallback in Task 2; coverage banner in Task 14; model-unavailable path in Task 11.
- §7 testing → `test_debt_engine.py` (Task 7), `test_satellite_equations.py` (Task 8), `test_ml_model.py` (Task 11), `test_pareto.py` (Task 12), `test_data_layer.py` (Tasks 2–6); manual smoke test documented in Task 14's README.
- §8 out of scope → respected: no other personas, no deployment, no live streaming, no individual tax personalization.

**2. Placeholder scan.** The original `baseline_revenue = baseline_pb + 40.0` magic-number hack (caught during drafting) is fixed in Task 10 via a real `government_revenue_gdp` catalog entry (Task 2, `GC.REV.XGRT.GD.ZS`, live-verified). No other TBD/placeholder patterns remain — every step has real, runnable code.

**3. Type/signature consistency.** Checked across tasks: `FetchResult` (Task 2) is the sole return type for every client (Tasks 3–6); `ScenarioLevers`/`ScenarioResult`/`run_scenario` (Task 10) signatures match their use in Task 12 (Pareto) and Task 14 (app); `StressScoreResult`/`FiscalStressModel` (Task 11) match their use in Task 13 (retiree persona) and Task 14 (main.py); `DebtPathPoint` fields match between Task 7's producer and Task 10/13/14's consumers.

---

**Plan complete and saved to `docs/superpowers/plans/2026-08-06-debt-scenario-personas-implementation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
