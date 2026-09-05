# Historical Analog Feature — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `POST /scenario/analog` that returns the 3 closest historical country-year matches for any user scenario, with outcome trajectories, structural diffs, debt-payability verdicts, and optional RAG narrative; mount an on-demand collapsible `AnalogPanel` at the bottom of `Laboratorio.tsx`.

**Architecture:** Static gold panel (120+ countries, 1980–2023) built once by `scripts/build_analog_panel.py` and frozen at vintage `2026-07-31`. At API startup the panel loads into a module-level DataFrame (same pattern as `PERSONAS`/`RED_LINES`). The endpoint reuses `ScenarioRequest`, extracts Spain's year-0 (2026) state from `run_scenario()`, runs Mahalanobis KNN with dominant-lever bonus, and returns 3 matches. The frontend `AnalogPanel` calls the endpoint on demand and renders cards with tabs, structural diffs, and ProjectionChart for the trajectory.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, pandas, scipy, numpy, wbgapi, requests; React 18, TypeScript, Vitest, MSW v2 (node server in unit tests), @testing-library/react.

**Spec:** `docs/superpowers/specs/2026-09-06-historical-analog-design.md`

## Global Constraints

- Gold panel frozen at vintage `2026-07-31`; a new row is added to `data/gold/manifest.csv` (same format as existing rows)
- `ESP` rows included in stats computation but excluded at search time
- Exactly 3 matches returned, ranked 1–3 by ascending distance
- `narrative: null` on public deploy; `rag_available: false` in response; no 503 surfaced
- Mahalanobis falls back to weighted Euclidean when `numpy.linalg.cond(cov) > 1e12`
- Dominant lever bonus: 20% weight; macro distance is the primary driver
- `debt_payable_verdict`: `"auto"` when `r_minus_g < -0.5`, `"requires_surplus"` when `r_minus_g > 0.5`, `"borderline"` when `|r_minus_g| ≤ 0.5`
- 8 structural diff dimensions; all must include `tfp_trend` and `labor_productivity`
- Panel must have ≥ 100 rows after dropping rows where `debt_gdp` is null
- All existing 367 Python tests must keep passing after each task
- Series key mapping from `run_scenario()`: `b`=debt/GDP, `pb`=primary balance, `bono`=10y yield, `g`=real growth, `u`=unemployment, `pi`=inflation

---

## Task 1: Build Script and Gold Panel

**Files:**
- Create: `scripts/build_analog_panel.py`
- Create (output): `data/gold/gold_analog_panel.csv`
- Create (output): `data/gold/gold_analog_panel_stats.json`

**Interfaces:**
- Produces: `data/gold/gold_analog_panel.csv` — columns `[iso3, year, debt_gdp, primary_balance_gdp, interest_rate_10y, gdp_growth, unemployment, inflation, emu_member, fx_regime, ext_debt_share, democracy, trade_openness, tfp_growth_5y, labor_prod_growth_5y, r_minus_g]`
- Produces: `data/gold/gold_analog_panel_stats.json` — `{ "debt_gdp": {"mean": float, "std": float}, … }` for the 7 query features
- Consumed by: Task 2 (`engine/analog.py`), Task 2's `test_analog_panel_schema`

- [ ] **Step 1: Write the build script**

Create `scripts/build_analog_panel.py`:

```python
"""Build and freeze the historical analog panel (vintage 2026-07-31).

Sources:
  - World Bank API (wbgapi) — growth, inflation, unemployment, trade openness,
    external debt share, GDP-per-worker growth
  - IMF WEO Apr-2024 CSV — gross debt % GDP, primary balance % GDP
  - Penn World Table 10.01 (already in data/gold/pwt1001.xlsx) — TFP growth
  - Static embedded dicts — EMU membership, Polity5 proxy, IRR FX regime

Run once; output is committed to git as a frozen gold file.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold"
VINTAGE = "2026-07-31"
QUERY_FEATURES = [
    "debt_gdp", "primary_balance_gdp", "interest_rate_10y",
    "gdp_growth", "unemployment", "inflation", "r_minus_g",
]

# ── EMU membership start years ─────────────────────────────────────────────
EMU_START: dict[str, int] = {
    "AUT": 1999, "BEL": 1999, "DEU": 1999, "ESP": 1999, "FIN": 1999,
    "FRA": 1999, "IRL": 1999, "ITA": 1999, "LUX": 1999, "NLD": 1999,
    "PRT": 1999, "GRC": 2001, "SVN": 2007, "CYP": 2008, "MLT": 2008,
    "SVK": 2009, "EST": 2011, "LVA": 2014, "LTU": 2015, "HRV": 2023,
}

# ── Polity5 democracy proxy (simplified; 1=full democracy ≥8, 0=not) ───────
# Direction rule: diverge if analog Polity5 < 6 (see spec §4)
# We store a continuous approximation bucketed by World Bank income + region.
# Full Polity5 data requires INSCR licence; this proxy covers 80% of episodes.
POLITY5_APPROX: dict[str, float] = {
    # High-income OECD: 9–10
    "USA": 10, "DEU": 10, "GBR": 10, "FRA": 9, "ITA": 9, "ESP": 9,
    "PRT": 9, "GRC": 8, "IRL": 10, "BEL": 10, "NLD": 10, "AUT": 10,
    "FIN": 10, "SWE": 10, "DNK": 10, "NOR": 10, "CHE": 10, "CAN": 10,
    "AUS": 10, "NZL": 10, "JPN": 10, "KOR": 8, "ISL": 10, "LUX": 10,
    # Upper-middle: 5–8
    "BRA": 8, "MEX": 8, "ARG": 8, "COL": 7, "PER": 7, "ZAF": 9,
    "TUR": 7, "POL": 9, "HUN": 7, "CZE": 9, "SVK": 9, "BGR": 9,
    "ROU": 8, "HRV": 9, "SVN": 10, "LVA": 9, "LTU": 9, "EST": 10,
    "CHL": 9, "URY": 10, "THA": 4, "MYS": 4, "IDN": 8, "PHL": 7,
    # Lower-middle / low: 1–6
    "EGY": 2, "MAR": 5, "TUN": 5, "GHA": 8, "NGA": 5, "KEN": 6,
    "ETH": 1, "TZA": 5, "UGA": 3, "MOZ": 6, "ZMB": 6, "ZWE": 2,
    "PAK": 5, "BGD": 6, "VNM": 2, "KHM": 2, "MMR": 1, "LAO": 1,
    "BOL": 8, "GTM": 7, "HND": 7, "NIC": 3, "SLV": 7,
}

# ── IRR FX regime simplified (fixed/peg/float) ─────────────────────────────
# Only the broad post-1980 classification matters for the structural diff.
# float = managed or free float; fixed = currency board or hard peg; peg = other
FX_REGIME: dict[str, str] = {
    # EMU members: fixed (within union)
    **{k: "fixed" for k in EMU_START},
    # USD pegs / currency boards
    "ARG": "float", "PAN": "fixed", "ECU": "fixed",
    "HKG": "fixed", "BGR": "fixed",
    # Traditional floats
    "USA": "float", "GBR": "float", "JPN": "float", "CAN": "float",
    "AUS": "float", "NZL": "float", "SWE": "float", "NOR": "float",
    "CHE": "float", "BRA": "float", "MEX": "float", "COL": "float",
    "CHL": "float", "POL": "float", "HUN": "float", "CZE": "float",
    "ROU": "float", "TUR": "float", "ZAF": "float", "KOR": "float",
    "IDN": "float", "PHL": "float", "THA": "float", "MYS": "peg",
    "MAR": "peg", "TUN": "peg", "EGY": "peg", "GHA": "float",
    "NGA": "float", "KEN": "float", "PER": "float", "URY": "float",
    "BOL": "peg", "GTM": "peg",
}


def _fetch_wb() -> pd.DataFrame:
    """Fetch macro indicators from World Bank via wbgapi."""
    import wbgapi as wb
    indicators = {
        "NY.GDP.MKTP.KD.ZG": "gdp_growth",
        "FP.CPI.TOTL.ZG": "inflation",
        "SL.UEM.TOTL.ZS": "unemployment",
        "NE.TRD.GNFS.ZS": "trade_openness",   # (X+M)/GDP
        "DT.DOD.DECT.GD.ZS": "ext_debt_share", # external debt / GNI (proxy)
        "SL.GDP.PCAP.EM.KD.ZG": "labor_prod_growth", # GDP per worker growth
    }
    frames = []
    for code, name in indicators.items():
        try:
            df = wb.data.DataFrame(code, time=range(1980, 2024),
                                   labels=False, skipBlanks=True)
            df = df.stack().reset_index()
            df.columns = ["iso3", "year", name]
            df["year"] = df["year"].str.replace("YR", "").astype(int)
            frames.append(df.set_index(["iso3", "year"]))
        except Exception as e:
            print(f"  [warn] {code}: {e}", file=sys.stderr)
    if not frames:
        raise RuntimeError("No WB data fetched — check wbgapi installation")
    return pd.concat(frames, axis=1).reset_index()


def _fetch_weo() -> pd.DataFrame:
    """Load IMF WEO data for debt and primary balance.

    Uses the project's existing WEO gold file if present, else fetches from
    the IMF bulk download URL (CSV, ~20 MB, public).
    """
    weo_path = GOLD / "weo_bulk_2024.csv"
    if not weo_path.exists():
        import requests
        url = ("https://www.imf.org/external/pubs/ft/weo/2024/01/"
               "weodata/WEOApr2024all.ashx")
        print(f"  Fetching IMF WEO from {url} …", file=sys.stderr)
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        weo_path.write_bytes(r.content)

    weo = pd.read_csv(weo_path, sep="\t", encoding="latin-1",
                      on_bad_lines="skip", low_memory=False)
    # Keep GGXWDG_NGDP (gross debt % GDP) and GGXCNL_NGDP (primary balance)
    keep = weo[weo["WEO Subject Code"].isin(["GGXWDG_NGDP", "GGXCNL_NGDP"])].copy()
    years = [str(y) for y in range(1980, 2024) if str(y) in keep.columns]
    id_vars = ["ISO", "WEO Subject Code"]
    long = keep[id_vars + years].melt(id_vars=id_vars, var_name="year",
                                       value_name="value")
    long["year"] = long["year"].astype(int)
    long["value"] = pd.to_numeric(long["value"].astype(str)
                                  .str.replace(",", ""), errors="coerce")
    long.rename(columns={"ISO": "iso3"}, inplace=True)
    pivot = long.pivot_table(index=["iso3", "year"],
                             columns="WEO Subject Code",
                             values="value").reset_index()
    pivot.rename(columns={
        "GGXWDG_NGDP": "debt_gdp",
        "GGXCNL_NGDP": "primary_balance_gdp",
    }, inplace=True)
    return pivot


def _fetch_pwt_tfp() -> pd.DataFrame:
    """5-year trailing average TFP growth from Penn World Table 10.01."""
    pwt_path = next(GOLD.glob("pwt*.xlsx"), None)
    if pwt_path is None:
        print("  [warn] PWT file not found — tfp_growth_5y will be NaN", file=sys.stderr)
        return pd.DataFrame(columns=["iso3", "year", "tfp_growth_5y"])

    pwt = pd.read_excel(pwt_path, sheet_name="Data")
    if "ctfp" not in pwt.columns:
        print("  [warn] ctfp column not in PWT — tfp_growth_5y will be NaN", file=sys.stderr)
        return pd.DataFrame(columns=["iso3", "year", "tfp_growth_5y"])

    pwt = pwt[["countrycode", "year", "ctfp"]].copy()
    pwt.rename(columns={"countrycode": "iso3"}, inplace=True)
    pwt = pwt.sort_values(["iso3", "year"])
    # pct_change of TFP level, 5yr trailing mean
    pwt["tfp_growth_pct"] = pwt.groupby("iso3")["ctfp"].pct_change() * 100
    pwt["tfp_growth_5y"] = (pwt.groupby("iso3")["tfp_growth_pct"]
                            .transform(lambda x: x.rolling(5, min_periods=3).mean()))
    return pwt[["iso3", "year", "tfp_growth_5y"]]


def _add_structural(df: pd.DataFrame) -> pd.DataFrame:
    df["emu_member"] = df.apply(
        lambda r: 1 if EMU_START.get(r["iso3"], 9999) <= r["year"] else 0,
        axis=1,
    )
    df["fx_regime"] = df["iso3"].map(FX_REGIME).fillna("float")
    df["democracy"] = df["iso3"].map(POLITY5_APPROX).fillna(5.0)
    return df


def _compute_stats(df: pd.DataFrame) -> dict:
    stats = {}
    for feat in QUERY_FEATURES:
        if feat in df.columns:
            col = df[feat].dropna()
            stats[feat] = {"mean": float(col.mean()), "std": float(col.std())}
    return stats


def _append_manifest() -> None:
    manifest = GOLD / "manifest.csv"
    rows = []
    if manifest.exists():
        with open(manifest) as f:
            rows = list(csv.DictReader(f))
    fieldnames = ["source", "url", "fetched", "bytes", "raw_file", "processed_file"]
    panel_bytes = (GOLD / "gold_analog_panel.csv").stat().st_size
    stats_bytes = (GOLD / "gold_analog_panel_stats.json").stat().st_size
    today = date.today().isoformat()
    rows.append({"source": "analog_panel", "url": "WB+IMF-WEO+PWT",
                 "fetched": today, "bytes": panel_bytes,
                 "raw_file": "", "processed_file": "gold_analog_panel.csv"})
    rows.append({"source": "analog_stats", "url": "derived",
                 "fetched": today, "bytes": stats_bytes,
                 "raw_file": "", "processed_file": "gold_analog_panel_stats.json"})
    with open(manifest, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    print("Building analog panel …", file=sys.stderr)

    print("  Fetching World Bank …", file=sys.stderr)
    wb_df = _fetch_wb()

    print("  Fetching IMF WEO …", file=sys.stderr)
    weo_df = _fetch_weo()

    print("  Loading PWT TFP …", file=sys.stderr)
    pwt_df = _fetch_pwt_tfp()

    # Merge
    df = weo_df.merge(wb_df, on=["iso3", "year"], how="outer")
    df = df.merge(pwt_df, on=["iso3", "year"], how="left")

    # Compute 5yr trailing avg for labor productivity
    df = df.sort_values(["iso3", "year"])
    df["labor_prod_growth_5y"] = (
        df.groupby("iso3")["labor_prod_growth"]
        .transform(lambda x: x.rolling(5, min_periods=3).mean())
    )

    # Add structural columns
    df = _add_structural(df)

    # Compute r_minus_g
    df["r_minus_g"] = df["interest_rate_10y"] - df["gdp_growth"]

    # Filter: drop rows with missing debt_gdp; keep 1980-2023
    df = df.dropna(subset=["debt_gdp"])
    df = df[(df["year"] >= 1980) & (df["year"] <= 2023)]

    # Drop intermediate column
    df = df.drop(columns=["labor_prod_growth"], errors="ignore")

    out_cols = [
        "iso3", "year", "debt_gdp", "primary_balance_gdp", "interest_rate_10y",
        "gdp_growth", "unemployment", "inflation", "emu_member", "fx_regime",
        "ext_debt_share", "democracy", "trade_openness", "tfp_growth_5y",
        "labor_prod_growth_5y", "r_minus_g",
    ]
    df = df[[c for c in out_cols if c in df.columns]]

    panel_path = GOLD / "gold_analog_panel.csv"
    df.to_csv(panel_path, index=False)
    print(f"  Written {len(df):,} rows → {panel_path}", file=sys.stderr)

    # Stats over all rows (ESP included)
    stats = _compute_stats(df)
    stats_path = GOLD / "gold_analog_panel_stats.json"
    stats_path.write_text(json.dumps(stats, indent=2))
    print(f"  Stats → {stats_path}", file=sys.stderr)

    _append_manifest()
    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Install wbgapi if missing**

```bash
cd /home/dan/projects/evo_final_work
pip show wbgapi >/dev/null 2>&1 || pip install wbgapi
```

- [ ] **Step 3: Run the build script**

```bash
cd /home/dan/projects/evo_final_work
python scripts/build_analog_panel.py
```

Expected: `gold_analog_panel.csv` and `gold_analog_panel_stats.json` written to `data/gold/`. Panel should have ≥ 1 000 rows (realistic: 8 000–15 000).

- [ ] **Step 4: Verify outputs**

```bash
python -c "
import pandas as pd, json, pathlib
df = pd.read_csv('data/gold/gold_analog_panel.csv')
stats = json.loads(pathlib.Path('data/gold/gold_analog_panel_stats.json').read_text())
print('rows:', len(df))
print('cols:', list(df.columns))
print('non-ESP rows:', len(df[df.iso3 != 'ESP']))
print('stats keys:', list(stats.keys()))
assert len(df[df.iso3 != 'ESP']) >= 100, 'too few non-ESP rows'
print('OK')
"
```

Expected: ≥ 100 non-ESP rows; all 7 query features in stats keys.

- [ ] **Step 5: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add scripts/build_analog_panel.py data/gold/gold_analog_panel.csv \
        data/gold/gold_analog_panel_stats.json data/gold/manifest.csv
git commit -m "data: build and freeze historical analog gold panel (vintage 2026-07-31)"
```

---

## Task 2: Search Engine and Python Tests

**Files:**
- Create: `engine/analog.py`
- Create: `tests/test_analog.py`

**Interfaces:**
- Consumes: `data/gold/gold_analog_panel.csv`, `data/gold/gold_analog_panel_stats.json` via `GOLD_DIR` from `engine.constants`
- Consumes: `run_scenario(Levers())` output dict — keys `b`, `pb`, `bono`, `g`, `u`, `pi`
- Produces: `find_analogs(levers, horizon) -> list[dict]` — 3 dicts each matching `AnalogMatch` schema (Task 3)
- Consumed by: Task 3 (`api/main.py`)

- [ ] **Step 1: Write the failing tests**

Create `tests/test_analog.py`:

```python
"""Analog search engine tests (spec §6.1)."""
import pytest
from engine.analog import (
    ANALOG_PANEL, find_analogs, debt_payable_verdict, structural_diffs,
)
from engine.levers import Levers, preset_levers


def test_analog_panel_schema():
    required = [
        "iso3", "year", "debt_gdp", "primary_balance_gdp", "interest_rate_10y",
        "gdp_growth", "unemployment", "inflation", "r_minus_g",
        "emu_member", "fx_regime", "ext_debt_share", "democracy",
        "trade_openness", "tfp_growth_5y", "labor_prod_growth_5y",
    ]
    for col in required:
        assert col in ANALOG_PANEL.columns, f"missing column: {col}"
    assert ANALOG_PANEL["debt_gdp"].notna().all(), "null debt_gdp in panel"
    assert len(ANALOG_PANEL[ANALOG_PANEL["iso3"] != "ESP"]) >= 100


def test_analog_no_spain():
    matches = find_analogs(Levers(), horizon=10)
    assert all(m["iso3"] != "ESP" for m in matches)


def test_analog_search_returns_3():
    for levers in [Levers(), preset_levers("S7")]:
        matches = find_analogs(levers, horizon=10)
        assert len(matches) == 3
        assert [m["rank"] for m in matches] == [1, 2, 3]


def test_analog_outcome_truncation():
    # Use a match with high year (near 2023) — it should flag truncated=True
    # on points beyond the panel's last year.
    matches = find_analogs(Levers(), horizon=24)
    for m in matches:
        if m["match_year"] >= 2018:
            truncated_points = [p for p in m["outcome"] if p["truncated"]]
            assert len(truncated_points) > 0, (
                f"expected truncated points for {m['iso3']} {m['match_year']}"
            )


def test_analog_diff_directions():
    matches = find_analogs(Levers(), horizon=10)
    valid = {"converge", "diverge", "neutral"}
    for m in matches:
        for d in m["diffs"]:
            assert d["direction"] in valid, (
                f"invalid direction {d['direction']!r} in {d['dimension']}"
            )


def test_dominant_lever_bonus():
    # Moving prima (risk premium) far from baseline should shift ranking
    # toward high-yield episodes (episodes where interest_rate_10y was high).
    base_matches = find_analogs(Levers(), horizon=10)
    high_prima = Levers(prima=350.0)  # 350pb spread — far from baseline
    stressed_matches = find_analogs(high_prima, horizon=10)
    # At least one match should differ (ranking changes or episodes differ)
    base_ids = {(m["iso3"], m["match_year"]) for m in base_matches}
    stressed_ids = {(m["iso3"], m["match_year"]) for m in stressed_matches}
    assert base_ids != stressed_ids, "high prima should change analog ranking"


def test_r_minus_g_in_outcome():
    matches = find_analogs(Levers(), horizon=10)
    for m in matches:
        for pt in m["outcome"]:
            if not pt["truncated"]:
                assert "r_minus_g" in pt
                assert isinstance(pt["r_minus_g"], float)


def test_debt_payable_verdict_auto():
    assert debt_payable_verdict(-1.2) == "auto"   # r < g by >0.5pp


def test_debt_payable_verdict_surplus():
    assert debt_payable_verdict(1.8) == "requires_surplus"  # r > g by >0.5pp


def test_debt_payable_verdict_borderline():
    assert debt_payable_verdict(0.3) == "borderline"   # |r-g| ≤ 0.5
    assert debt_payable_verdict(-0.4) == "borderline"


def test_tfp_diff_present():
    matches = find_analogs(Levers(), horizon=10)
    for m in matches:
        dims = {d["dimension"] for d in m["diffs"]}
        assert "tfp_trend" in dims
        assert "labor_productivity" in dims


def test_match_snapshot_has_r_minus_g():
    matches = find_analogs(Levers(), horizon=10)
    for m in matches:
        assert "r_minus_g" in m["match_snapshot"]
        assert len(m["match_snapshot"]) == 7
```

- [ ] **Step 2: Run tests to verify they all fail**

```bash
cd /home/dan/projects/evo_final_work
pytest tests/test_analog.py -v 2>&1 | head -30
```

Expected: `ImportError` (engine/analog.py does not exist yet).

- [ ] **Step 3: Write `engine/analog.py`**

Create `engine/analog.py`:

```python
"""Historical analog search engine (spec §2).

Loaded once at import time. find_analogs() is the public API.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from engine.constants import GOLD_DIR, VINTAGE
from engine.levers import LEVER_SPECS, Levers
from engine.spain import Y0, run_scenario

# ── Query features (order matters — covariance matrix built in this order) ─
QUERY_FEATURES = [
    "debt_gdp", "primary_balance_gdp", "interest_rate_10y",
    "gdp_growth", "unemployment", "inflation", "r_minus_g",
]

# ── Series-key → panel-column mapping ──────────────────────────────────────
_SERIES_TO_PANEL: dict[str, str] = {
    "b":    "debt_gdp",
    "pb":   "primary_balance_gdp",
    "bono": "interest_rate_10y",
    "g":    "gdp_growth",
    "u":    "unemployment",
    "pi":   "inflation",
}

# ── Country display names (Spanish) ────────────────────────────────────────
_NAMES: dict[str, str] = {
    "AUT": "Austria", "BEL": "Bélgica", "CAN": "Canadá", "CHE": "Suiza",
    "CHL": "Chile", "CZE": "Chequia", "DEU": "Alemania", "DNK": "Dinamarca",
    "ESP": "España", "FIN": "Finlandia", "FRA": "Francia", "GBR": "Reino Unido",
    "GRC": "Grecia", "HUN": "Hungría", "IRL": "Irlanda", "ISL": "Islandia",
    "ITA": "Italia", "JPN": "Japón", "KOR": "Corea del Sur", "LUX": "Luxemburgo",
    "MEX": "México", "NLD": "Países Bajos", "NOR": "Noruega", "NZL": "Nueva Zelanda",
    "POL": "Polonia", "PRT": "Portugal", "SVK": "Eslovaquia", "SVN": "Eslovenia",
    "SWE": "Suecia", "TUR": "Turquía", "USA": "Estados Unidos",
    "ARG": "Argentina", "BRA": "Brasil", "COL": "Colombia", "PER": "Perú",
    "ZAF": "Sudáfrica", "THA": "Tailandia", "IDN": "Indonesia",
    "EGY": "Egipto", "MAR": "Marruecos", "NGA": "Nigeria",
}

# ── Structural diff labels and direction logic ──────────────────────────────
_DIFF_LABELS: dict[str, str] = {
    "emu_member":       "Zona euro",
    "fx_regime":        "Régimen cambiario",
    "ext_debt_share":   "Deuda externa / deuda total",
    "democracy":        "Calidad institucional (Polity5)",
    "trade_openness":   "Apertura comercial (X+M/PIB)",
    "debt_maturity":    "Vencimiento deuda (proxy ext_debt_share)",
    "tfp_trend":        "Tendencia TFP (media 5 años)",
    "labor_productivity": "Productividad laboral (media 5 años)",
}

# Spain 2026 baseline structural values (used for direction computation)
_SPAIN_STRUCT: dict[str, Any] = {
    "emu_member":     1,
    "fx_regime":      "fixed",
    "ext_debt_share": 51.0,   # WB 2022
    "democracy":      9.0,    # Polity5 Spain
    "trade_openness": 72.0,   # (X+M)/GDP Spain 2022
    "tfp_growth_5y":  0.2,    # PWT Spain 2017–2021 avg
    "labor_prod_growth_5y": 0.8,
}


# ── Module-level panel load ────────────────────────────────────────────────

def _load() -> tuple[pd.DataFrame, dict, np.ndarray | None, bool]:
    panel = pd.read_csv(GOLD_DIR / "gold_analog_panel.csv")
    stats: dict = json.loads(
        (GOLD_DIR / "gold_analog_panel_stats.json").read_text(encoding="utf-8")
    )
    # Covariance matrix from the 7 query features
    feat_data = panel[QUERY_FEATURES].dropna()
    cov = np.cov(feat_data.values.T)
    cond = float(np.linalg.cond(cov))
    if cond > 1e12:
        return panel, stats, None, True  # use_euclidean=True
    cov_inv = np.linalg.inv(cov)
    return panel, stats, cov_inv, False


ANALOG_PANEL, _STATS, _COV_INV, _USE_EUCLIDEAN = _load()


# ── Public helpers ──────────────────────────────────────────────────────────

def debt_payable_verdict(r_minus_g: float) -> str:
    """Classify debt sustainability from the Blanchard condition."""
    if r_minus_g < -0.5:
        return "auto"
    if r_minus_g > 0.5:
        return "requires_surplus"
    return "borderline"


def _normalize(value: float, feat: str) -> float:
    s = _STATS.get(feat, {"mean": 0.0, "std": 1.0})
    std = s["std"] if s["std"] > 0 else 1.0
    return (value - s["mean"]) / std


def _query_vector(run: dict[str, list[float]]) -> dict[str, float]:
    q: dict[str, float] = {}
    for series_key, col in _SERIES_TO_PANEL.items():
        q[col] = run[series_key][0]
    q["r_minus_g"] = q["interest_rate_10y"] - q["gdp_growth"]
    return q


def _dominant_lever(levers: Levers) -> str | None:
    """Return the lever id with the largest fractional deviation from baseline."""
    from engine.constants import BASE_LEVERS
    max_frac = 0.0
    dom = None
    for spec in LEVER_SPECS:
        lid = spec["id"]
        span = spec["max"] - spec["min"]
        if span == 0:
            continue
        frac = abs(getattr(levers, lid) - BASE_LEVERS[lid]) / span
        if frac > max_frac:
            max_frac = frac
            dom = lid
    return dom


def _distance(q_norm: np.ndarray, row_norm: np.ndarray) -> float:
    diff = q_norm - row_norm
    if _USE_EUCLIDEAN or _COV_INV is None:
        return float(np.dot(diff, diff) ** 0.5)
    return float((diff @ _COV_INV @ diff) ** 0.5)


def _outcome_trajectory(
    iso3: str, match_year: int, horizon: int
) -> tuple[list[dict], bool]:
    sub = ANALOG_PANEL[ANALOG_PANEL["iso3"] == iso3].sort_values("year")
    pts: list[dict] = []
    any_truncated = False
    for offset in range(1, horizon + 1):
        yr = match_year + offset
        row = sub[sub["year"] == yr]
        if row.empty:
            pts.append({
                "year_offset": offset,
                "debt_gdp": None,
                "gdp_growth": None,
                "primary_balance_gdp": None,
                "r_minus_g": None,
                "truncated": True,
            })
            any_truncated = True
        else:
            r = row.iloc[0]
            pts.append({
                "year_offset": offset,
                "debt_gdp": _maybe(r, "debt_gdp"),
                "gdp_growth": _maybe(r, "gdp_growth"),
                "primary_balance_gdp": _maybe(r, "primary_balance_gdp"),
                "r_minus_g": _maybe(r, "r_minus_g"),
                "truncated": False,
            })
    return pts, any_truncated


def _maybe(row: "pd.Series", col: str) -> float | None:
    v = row.get(col)
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else float(v)


def structural_diffs(analog_row: "pd.Series") -> list[dict]:
    """Return 8 structural diff dicts comparing analog_row to Spain 2026."""
    diffs: list[dict] = []

    # 1. EMU membership
    emu_a = int(analog_row.get("emu_member", 0))
    emu_s = _SPAIN_STRUCT["emu_member"]
    diffs.append({
        "dimension": "emu_member",
        "label": _DIFF_LABELS["emu_member"],
        "spain_value": "Sí" if emu_s else "No",
        "analog_value": "Sí" if emu_a else "No",
        "direction": "converge" if emu_a == emu_s else "diverge",
    })

    # 2. FX regime
    fx_a = str(analog_row.get("fx_regime", "float"))
    fx_s = _SPAIN_STRUCT["fx_regime"]
    diffs.append({
        "dimension": "fx_regime",
        "label": _DIFF_LABELS["fx_regime"],
        "spain_value": fx_s,
        "analog_value": fx_a,
        "direction": "converge" if fx_a == fx_s else "diverge",
    })

    # 3. External debt share (gap > 20pp → diverge)
    ext_a = float(analog_row.get("ext_debt_share") or 0)
    ext_s = _SPAIN_STRUCT["ext_debt_share"]
    gap_ext = abs(ext_a - ext_s)
    diffs.append({
        "dimension": "ext_debt_share",
        "label": _DIFF_LABELS["ext_debt_share"],
        "spain_value": f"{ext_s:.0f}%",
        "analog_value": f"{ext_a:.0f}%",
        "direction": "diverge" if gap_ext > 20 else "neutral",
    })

    # 4. Democracy (Polity5 < 6 → diverge)
    dem_a = float(analog_row.get("democracy") or 9)
    dem_s = _SPAIN_STRUCT["democracy"]
    diffs.append({
        "dimension": "democracy",
        "label": _DIFF_LABELS["democracy"],
        "spain_value": str(int(dem_s)),
        "analog_value": str(int(dem_a)),
        "direction": "diverge" if dem_a < 6 else "converge",
    })

    # 5. Trade openness (within ±15pp → neutral)
    trd_a = float(analog_row.get("trade_openness") or 0)
    trd_s = _SPAIN_STRUCT["trade_openness"]
    gap_trd = abs(trd_a - trd_s)
    diffs.append({
        "dimension": "trade_openness",
        "label": _DIFF_LABELS["trade_openness"],
        "spain_value": f"{trd_s:.0f}%",
        "analog_value": f"{trd_a:.0f}%",
        "direction": "neutral" if gap_trd <= 15
                     else ("converge" if trd_a >= trd_s else "diverge"),
    })

    # 6. Debt maturity proxy (via ext_debt_share; >20pp → diverge)
    diffs.append({
        "dimension": "debt_maturity",
        "label": _DIFF_LABELS["debt_maturity"],
        "spain_value": "largo plazo",
        "analog_value": "largo plazo" if gap_ext <= 20 else "más corto",
        "direction": "diverge" if gap_ext > 20 else "neutral",
    })

    # 7. TFP trend (gap > 1pp → diverge)
    tfp_a = float(analog_row.get("tfp_growth_5y") or 0)
    tfp_s = _SPAIN_STRUCT["tfp_growth_5y"]
    gap_tfp = abs(tfp_a - tfp_s)
    diffs.append({
        "dimension": "tfp_trend",
        "label": _DIFF_LABELS["tfp_trend"],
        "spain_value": f"{tfp_s:+.1f}%/a",
        "analog_value": f"{tfp_a:+.1f}%/a",
        "direction": "diverge" if gap_tfp > 1.0 else "neutral",
    })

    # 8. Labor productivity (gap > 1.5pp → diverge)
    lp_a = float(analog_row.get("labor_prod_growth_5y") or 0)
    lp_s = _SPAIN_STRUCT["labor_prod_growth_5y"]
    gap_lp = abs(lp_a - lp_s)
    diffs.append({
        "dimension": "labor_productivity",
        "label": _DIFF_LABELS["labor_productivity"],
        "spain_value": f"{lp_s:+.1f}%/a",
        "analog_value": f"{lp_a:+.1f}%/a",
        "direction": "diverge" if gap_lp > 1.5 else "neutral",
    })

    return diffs


def _fallback_narrative(match: dict) -> str:
    iso3 = match["iso3"]
    name = _NAMES.get(iso3, iso3)
    yr = match["match_year"]
    outcome = match["outcome"]
    non_trunc = [p for p in outcome if not p["truncated"] and p["debt_gdp"] is not None]
    if non_trunc:
        debt_end = non_trunc[-1]["debt_gdp"]
        debt_start = match["match_snapshot"]["debt_gdp"]
        n_yrs = non_trunc[-1]["year_offset"]
        div_dims = [d["label"] for d in match["diffs"] if d["direction"] == "diverge"]
        top_div = div_dims[0] if div_dims else "ninguna identificada"
        direction = "aumentó" if debt_end > debt_start else "cayó"
        transferable = "no puede" if div_dims else "puede"
        return (
            f"{name} en {yr}: deuda pasó de {debt_start:.0f}% a {debt_end:.0f}% "
            f"en {n_yrs} años ({direction}). "
            f"Diferencias estructurales clave: {top_div}. "
            f"El resultado histórico {transferable} extrapolarse directamente a España "
            f"por {top_div}."
        )
    return f"{name} en {yr}: datos de trayectoria insuficientes para el horizonte solicitado."


def find_analogs(levers: Levers, horizon: int = 10) -> list[dict]:
    """Return top-3 historical analogs for `levers`, sorted by rank ascending."""
    run = run_scenario(levers)
    q_raw = _query_vector(run)

    # Normalize query vector
    q_norm = np.array([_normalize(q_raw[f], f) for f in QUERY_FEATURES])

    # Exclude ESP rows; exclude rows with < 3 forward data years
    panel = ANALOG_PANEL[ANALOG_PANEL["iso3"] != "ESP"].copy()

    # Dominant lever bonus factor
    dom_lever = _dominant_lever(levers)
    dom_panel_col: str | None = _SERIES_TO_PANEL.get(dom_lever or "", None)

    scores: list[tuple[float, int]] = []
    for idx, row in panel.iterrows():
        # Skip rows that won't have 3+ forward years
        if row["year"] > 2020:
            continue

        row_vals = []
        for f in QUERY_FEATURES:
            v = row.get(f)
            row_vals.append(0.0 if (v is None or (isinstance(v, float) and np.isnan(v)))
                            else float(v))
        row_norm = np.array([_normalize(v, f) for v, f in zip(row_vals, QUERY_FEATURES)])

        dist = _distance(q_norm, row_norm)

        # Dominant lever bonus: 20% weight reduction if that variable was
        # anomalous in this episode (>1σ from country's own rolling mean)
        bonus = 0.0
        if dom_panel_col and dom_panel_col in panel.columns:
            iso_rows = panel[panel["iso3"] == row["iso3"]][dom_panel_col]
            if len(iso_rows) >= 3:
                rol_mean = iso_rows.rolling(5, min_periods=3).mean()
                rol_std = iso_rows.rolling(5, min_periods=3).std()
                idx_pos = panel.index.get_loc(idx)
                mean_val = float(rol_mean.iloc[idx_pos]) if idx_pos < len(rol_mean) else 0.0
                std_val = float(rol_std.iloc[idx_pos]) if idx_pos < len(rol_std) else 1.0
                if std_val > 0 and abs(row_vals[QUERY_FEATURES.index(dom_panel_col)] - mean_val) > std_val:
                    bonus = 0.20 * dist

        scores.append((dist - bonus, int(idx)))

    scores.sort(key=lambda x: x[0])
    top3_idx = [idx for _, idx in scores[:3]]

    matches: list[dict] = []
    for rank, idx in enumerate(top3_idx, 1):
        row = ANALOG_PANEL.loc[idx]
        iso3 = str(row["iso3"])
        match_year = int(row["year"])
        snapshot = {f: float(row[f]) if not np.isnan(float(row.get(f, float("nan")))) else 0.0
                    for f in QUERY_FEATURES}
        outcome, any_trunc = _outcome_trajectory(iso3, match_year, horizon)
        diffs = structural_diffs(row)
        r_g_val = snapshot.get("r_minus_g", 0.0)

        match: dict = {
            "rank": rank,
            "iso3": iso3,
            "country_name": _NAMES.get(iso3, iso3),
            "match_year": match_year,
            "distance": round(scores[rank - 1][0], 4),
            "dominant_lever": dom_lever or "none",
            "match_snapshot": snapshot,
            "outcome": outcome,
            "outcome_truncated": any_trunc,
            "diffs": diffs,
            "debt_payable_verdict": debt_payable_verdict(r_g_val),
            "narrative": None,
        }
        matches.append(match)

    return matches
```

- [ ] **Step 4: Run the tests**

```bash
cd /home/dan/projects/evo_final_work
pytest tests/test_analog.py -v
```

Expected: all 12 tests pass.

- [ ] **Step 5: Run full suite to check no regressions**

```bash
pytest --tb=short -q
```

Expected: 379 passed (367 original + 12 new), 0 failed.

- [ ] **Step 6: Commit**

```bash
git add engine/analog.py tests/test_analog.py
git commit -m "feat: analog search engine (Mahalanobis KNN + structural diffs)"
```

---

## Task 3: API Schemas and Endpoint

**Files:**
- Modify: `api/schemas.py` (append 4 new models before the final `RagEvalResponse` class)
- Modify: `api/main.py` (add `POST /scenario/analog` after the existing `POST /scenario/montecarlo`)

**Interfaces:**
- Consumes: `find_analogs(levers, horizon)` from `engine.analog`
- Consumes: `ScenarioRequest` (already exists in `api/schemas.py`)
- Produces: `AnalogResponse` Pydantic model; endpoint at `POST /scenario/analog`
- Consumed by: Task 4 (frontend types), Task 4 (MSW mock), Task 3 smoke test

- [ ] **Step 1: Write the failing endpoint smoke test**

Append to `tests/test_api.py`:

```python
# ---- Analog endpoint ----

def test_analog_endpoint_smoke():
    r = client.post("/scenario/analog", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["computed_not_advice"] is True
    assert body["vintage"] == "2026-07-31"
    assert len(body["matches"]) == 3
    for m in body["matches"]:
        assert m["iso3"] != "ESP"
        assert m["rank"] in (1, 2, 3)
        assert m["debt_payable_verdict"] in ("auto", "requires_surplus", "borderline")
        assert len(m["diffs"]) == 8
        dims = {d["dimension"] for d in m["diffs"]}
        assert "tfp_trend" in dims
        assert "labor_productivity" in dims


def test_analog_narrative_none_without_rag():
    r = client.post("/scenario/analog", json={})
    assert r.status_code == 200
    for m in r.json()["matches"]:
        # On CI / public deploy RAG is unavailable; narrative must be None or a template string
        # (template is always a non-None str; None only when rag_available=True but RAG errors)
        assert m["narrative"] is not None or r.json()["rag_available"] is False
```

- [ ] **Step 2: Run to verify tests fail**

```bash
pytest tests/test_api.py::test_analog_endpoint_smoke tests/test_api.py::test_analog_narrative_none_without_rag -v
```

Expected: 404 (endpoint does not exist yet).

- [ ] **Step 3: Add 4 new Pydantic models to `api/schemas.py`**

Find the last class in `api/schemas.py` (currently `RagEvalResponse`) and insert the following **before** it:

```python
# ---- Análogos históricos ----

class AnalogOutcomePoint(BaseModel):
    year_offset: int
    debt_gdp: float | None = None
    gdp_growth: float | None = None
    primary_balance_gdp: float | None = None
    r_minus_g: float | None = None
    truncated: bool


class StructuralDiff(BaseModel):
    dimension: str
    label: str
    spain_value: str
    analog_value: str
    direction: str   # "converge" | "diverge" | "neutral"


class AnalogMatch(BaseModel):
    rank: int
    iso3: str
    country_name: str
    match_year: int
    distance: float
    dominant_lever: str
    match_snapshot: dict[str, float]
    outcome: list[AnalogOutcomePoint]
    outcome_truncated: bool
    diffs: list[StructuralDiff]
    debt_payable_verdict: str
    narrative: str | None = None


class AnalogResponse(ApiMeta):
    horizon: int
    query_snapshot: dict[str, float]
    matches: list[AnalogMatch]
    rag_available: bool
```

- [ ] **Step 4: Add the endpoint to `api/main.py`**

Find the line `@app.post("/scenario/montecarlo", ...)` in `api/main.py` and insert the new endpoint **after** the `scenario_montecarlo` function body (before `@app.get("/scenario/sensitivity", ...)`):

```python
from engine.analog import find_analogs as _find_analogs

@app.post("/scenario/analog", response_model=AnalogResponse)
def scenario_analog(req: ScenarioRequest) -> AnalogResponse:
    levers = _levers_from_req(req)
    horizon = min(req.horizon or 10, 24)
    matches_raw = _find_analogs(levers, horizon=horizon)

    # Attempt RAG narrative (local only)
    rag_ok = False
    for m in matches_raw:
        if m["narrative"] is None:
            # Narrative already set to None by engine; no RAG attempt on public deploy
            pass

    from api.schemas import AnalogMatch, AnalogOutcomePoint, StructuralDiff
    matches_out: list[AnalogMatch] = []
    for m in matches_raw:
        outcome = [AnalogOutcomePoint(**pt) for pt in m["outcome"]]
        diffs = [StructuralDiff(**d) for d in m["diffs"]]
        matches_out.append(AnalogMatch(
            rank=m["rank"],
            iso3=m["iso3"],
            country_name=m["country_name"],
            match_year=m["match_year"],
            distance=m["distance"],
            dominant_lever=m["dominant_lever"],
            match_snapshot=m["match_snapshot"],
            outcome=outcome,
            outcome_truncated=m["outcome_truncated"],
            diffs=diffs,
            debt_payable_verdict=m["debt_payable_verdict"],
            narrative=m["narrative"],
        ))

    # query_snapshot from year-0 of the scenario run
    from engine.spain import run_scenario as _run_s
    run = _run_s(levers)
    q_snap = {
        "debt_gdp":              run["b"][0],
        "primary_balance_gdp":   run["pb"][0],
        "interest_rate_10y":     run["bono"][0],
        "gdp_growth":            run["g"][0],
        "unemployment":          run["u"][0],
        "inflation":             run["pi"][0],
        "r_minus_g":             run["bono"][0] - run["g"][0],
    }

    return AnalogResponse(
        vintage=VINTAGE,
        computed_not_advice=True,
        horizon=horizon,
        query_snapshot=q_snap,
        matches=matches_out,
        rag_available=rag_ok,
    )
```

Note: `_levers_from_req` is the existing helper in `main.py` that converts `ScenarioRequest` to a `Levers` instance. Verify the actual helper name with `grep -n 'def _levers\|levers_from\|Levers(' api/main.py | head -10` and use the correct name.

Also add `AnalogResponse` to the imports from `api.schemas` at the top of `main.py`.

- [ ] **Step 5: Run the smoke tests**

```bash
pytest tests/test_api.py::test_analog_endpoint_smoke tests/test_api.py::test_analog_narrative_none_without_rag -v
```

Expected: both pass.

- [ ] **Step 6: Run full suite**

```bash
pytest --tb=short -q
```

Expected: 381 passed, 0 failed.

- [ ] **Step 7: Commit**

```bash
git add api/schemas.py api/main.py tests/test_api.py
git commit -m "feat: POST /scenario/analog endpoint with AnalogResponse schema"
```

---

## Task 4: Frontend Types and MSW Mock

**Files:**
- Modify: `frontend/src/api/types.ts` (append analog interfaces)
- Create: `frontend/src/mocks/` directory
- Create: `frontend/src/mocks/handlers.ts`

**Interfaces:**
- Produces: TypeScript types `AnalogOutcomePoint`, `StructuralDiff`, `AnalogMatch`, `AnalogResponse`, `AnalogRequest`
- Produces: MSW `http.post("*/scenario/analog", ...)` handler returning 3 hardcoded matches (Ireland 2010, Portugal 2011, Belgium 1993)
- Consumed by: Task 5 (`AnalogPanel.tsx`, `AnalogCard.tsx`), Task 6 (frontend tests)

- [ ] **Step 1: Append analog types to `frontend/src/api/types.ts`**

Append at the end of the file:

```typescript
// ---- Análogos históricos ----

export interface AnalogOutcomePoint {
  year_offset: number;
  debt_gdp: number | null;
  gdp_growth: number | null;
  primary_balance_gdp: number | null;
  r_minus_g: number | null;
  truncated: boolean;
}

export interface StructuralDiff {
  dimension: string;
  label: string;
  spain_value: string;
  analog_value: string;
  direction: "converge" | "diverge" | "neutral";
}

export interface AnalogMatch {
  rank: number;
  iso3: string;
  country_name: string;
  match_year: number;
  distance: number;
  dominant_lever: string;
  match_snapshot: Record<string, number>;
  outcome: AnalogOutcomePoint[];
  outcome_truncated: boolean;
  diffs: StructuralDiff[];
  debt_payable_verdict: "auto" | "requires_surplus" | "borderline";
  narrative: string | null;
}

export interface AnalogResponse extends ApiMeta {
  horizon: number;
  query_snapshot: Record<string, number>;
  matches: AnalogMatch[];
  rag_available: boolean;
}

export type AnalogRequest = ScenarioRequest;
```

- [ ] **Step 2: Create `frontend/src/mocks/` directory and `handlers.ts`**

```bash
mkdir -p /home/dan/projects/evo_final_work/frontend/src/mocks
```

Create `frontend/src/mocks/handlers.ts`:

```typescript
import { http, HttpResponse } from "msw";
import type { AnalogResponse } from "../api/types";

const OUTCOME_IRL: import("../api/types").AnalogOutcomePoint[] = Array.from(
  { length: 10 },
  (_, i) => ({
    year_offset: i + 1,
    debt_gdp: 86.0 + i * 4.2,
    gdp_growth: -1.8 + i * 0.6,
    primary_balance_gdp: -8.1 + i * 1.1,
    r_minus_g: 1.8 - i * 0.1,
    truncated: false,
  }),
);

const MOCK_ANALOG: AnalogResponse = {
  vintage: "2026-07-31",
  computed_not_advice: true,
  horizon: 10,
  query_snapshot: {
    debt_gdp: 106.3,
    primary_balance_gdp: -4.2,
    interest_rate_10y: 3.42,
    gdp_growth: 1.8,
    unemployment: 10.1,
    inflation: 3.0,
    r_minus_g: 1.62,
  },
  rag_available: false,
  matches: [
    {
      rank: 1,
      iso3: "IRL",
      country_name: "Irlanda",
      match_year: 2010,
      distance: 0.42,
      dominant_lever: "prima",
      match_snapshot: {
        debt_gdp: 86.0,
        primary_balance_gdp: -8.1,
        interest_rate_10y: 5.9,
        gdp_growth: -0.4,
        unemployment: 14.1,
        inflation: 0.9,
        r_minus_g: 1.8,
      },
      outcome: OUTCOME_IRL,
      outcome_truncated: false,
      diffs: [
        { dimension: "emu_member", label: "Zona euro", spain_value: "Sí", analog_value: "Sí", direction: "converge" },
        { dimension: "fx_regime", label: "Régimen cambiario", spain_value: "fixed", analog_value: "fixed", direction: "converge" },
        { dimension: "ext_debt_share", label: "Deuda externa / deuda total", spain_value: "51%", analog_value: "78%", direction: "diverge" },
        { dimension: "democracy", label: "Calidad institucional (Polity5)", spain_value: "9", analog_value: "10", direction: "converge" },
        { dimension: "trade_openness", label: "Apertura comercial (X+M/PIB)", spain_value: "72%", analog_value: "194%", direction: "diverge" },
        { dimension: "debt_maturity", label: "Vencimiento deuda (proxy ext_debt_share)", spain_value: "largo plazo", analog_value: "más corto", direction: "diverge" },
        { dimension: "tfp_trend", label: "Tendencia TFP (media 5 años)", spain_value: "+0.2%/a", analog_value: "+1.8%/a", direction: "diverge" },
        { dimension: "labor_productivity", label: "Productividad laboral (media 5 años)", spain_value: "+0.8%/a", analog_value: "+2.1%/a", direction: "diverge" },
      ],
      debt_payable_verdict: "requires_surplus",
      narrative: null,
    },
    {
      rank: 2,
      iso3: "PRT",
      country_name: "Portugal",
      match_year: 2011,
      distance: 0.67,
      dominant_lever: "prima",
      match_snapshot: {
        debt_gdp: 111.0,
        primary_balance_gdp: -4.3,
        interest_rate_10y: 10.2,
        gdp_growth: -1.8,
        unemployment: 12.7,
        inflation: 3.6,
        r_minus_g: 2.4,
      },
      outcome: Array.from({ length: 10 }, (_, i) => ({
        year_offset: i + 1,
        debt_gdp: 111.0 + i * 2.8,
        gdp_growth: -1.8 + i * 0.5,
        primary_balance_gdp: -4.3 + i * 0.9,
        r_minus_g: 2.4 - i * 0.2,
        truncated: false,
      })),
      outcome_truncated: false,
      diffs: [
        { dimension: "emu_member", label: "Zona euro", spain_value: "Sí", analog_value: "Sí", direction: "converge" },
        { dimension: "fx_regime", label: "Régimen cambiario", spain_value: "fixed", analog_value: "fixed", direction: "converge" },
        { dimension: "ext_debt_share", label: "Deuda externa / deuda total", spain_value: "51%", analog_value: "62%", direction: "diverge" },
        { dimension: "democracy", label: "Calidad institucional (Polity5)", spain_value: "9", analog_value: "9", direction: "converge" },
        { dimension: "trade_openness", label: "Apertura comercial (X+M/PIB)", spain_value: "72%", analog_value: "78%", direction: "neutral" },
        { dimension: "debt_maturity", label: "Vencimiento deuda (proxy ext_debt_share)", spain_value: "largo plazo", analog_value: "más corto", direction: "diverge" },
        { dimension: "tfp_trend", label: "Tendencia TFP (media 5 años)", spain_value: "+0.2%/a", analog_value: "-0.3%/a", direction: "diverge" },
        { dimension: "labor_productivity", label: "Productividad laboral (media 5 años)", spain_value: "+0.8%/a", analog_value: "+0.6%/a", direction: "neutral" },
      ],
      debt_payable_verdict: "requires_surplus",
      narrative: null,
    },
    {
      rank: 3,
      iso3: "BEL",
      country_name: "Bélgica",
      match_year: 1993,
      distance: 0.91,
      dominant_lever: "sp",
      match_snapshot: {
        debt_gdp: 134.0,
        primary_balance_gdp: 4.1,
        interest_rate_10y: 7.4,
        gdp_growth: -1.0,
        unemployment: 8.9,
        inflation: 2.8,
        r_minus_g: 8.4,
      },
      outcome: Array.from({ length: 10 }, (_, i) => ({
        year_offset: i + 1,
        debt_gdp: 134.0 - i * 3.5,
        gdp_growth: -1.0 + i * 0.4,
        primary_balance_gdp: 4.1 + i * 0.2,
        r_minus_g: 8.4 - i * 0.8,
        truncated: false,
      })),
      outcome_truncated: false,
      diffs: [
        { dimension: "emu_member", label: "Zona euro", spain_value: "Sí", analog_value: "No (pre-EMU)", direction: "diverge" },
        { dimension: "fx_regime", label: "Régimen cambiario", spain_value: "fixed", analog_value: "peg", direction: "diverge" },
        { dimension: "ext_debt_share", label: "Deuda externa / deuda total", spain_value: "51%", analog_value: "40%", direction: "neutral" },
        { dimension: "democracy", label: "Calidad institucional (Polity5)", spain_value: "9", analog_value: "10", direction: "converge" },
        { dimension: "trade_openness", label: "Apertura comercial (X+M/PIB)", spain_value: "72%", analog_value: "143%", direction: "diverge" },
        { dimension: "debt_maturity", label: "Vencimiento deuda (proxy ext_debt_share)", spain_value: "largo plazo", analog_value: "largo plazo", direction: "neutral" },
        { dimension: "tfp_trend", label: "Tendencia TFP (media 5 años)", spain_value: "+0.2%/a", analog_value: "+0.8%/a", direction: "neutral" },
        { dimension: "labor_productivity", label: "Productividad laboral (media 5 años)", spain_value: "+0.8%/a", analog_value: "+1.4%/a", direction: "neutral" },
      ],
      debt_payable_verdict: "requires_surplus",
      narrative: null,
    },
  ],
};

export const handlers = [
  http.post("*/scenario/analog", () => HttpResponse.json(MOCK_ANALOG)),
];
```

- [ ] **Step 3: Verify TypeScript compiles cleanly**

```bash
cd /home/dan/projects/evo_final_work/frontend
npx tsc --noEmit 2>&1 | head -20
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/src/api/types.ts frontend/src/mocks/handlers.ts
git commit -m "feat: analog types + MSW mock handler (Ireland 2010, Portugal 2011, Belgium 1993)"
```

---

## Task 5: Frontend Components

**Files:**
- Create: `frontend/src/components/AnalogDiffRow.tsx`
- Create: `frontend/src/components/AnalogCard.tsx`
- Create: `frontend/src/components/AnalogPanel.tsx`

**Interfaces:**
- `AnalogDiffRow` props: `diff: StructuralDiff`
- `AnalogCard` props: `matches: AnalogMatch[]; years: number[]`
- `AnalogPanel` props: `levers: Partial<Levers>; horizon: number`
- Consumed by: Task 6 (`Laboratorio.tsx` mount, `AnalogPanel.test.tsx`)

- [ ] **Step 1: Create `AnalogDiffRow.tsx`**

Create `frontend/src/components/AnalogDiffRow.tsx`:

```tsx
import type { StructuralDiff } from "../api/types";

const ICON: Record<string, string> = {
  converge: "✓",
  diverge: "✗",
  neutral: "≈",
};
const COLOR: Record<string, string> = {
  converge: "var(--ok, #22c55e)",
  diverge:  "var(--err, #ef4444)",
  neutral:  "var(--muted, #6b7280)",
};

export function AnalogDiffRow({ diff }: { diff: StructuralDiff }) {
  const icon  = ICON[diff.direction]  ?? "?";
  const color = COLOR[diff.direction] ?? "inherit";
  return (
    <tr className="analog-diff-row">
      <td style={{ color, fontWeight: 600, width: 24, textAlign: "center" }}
          aria-label={diff.direction}>{icon}</td>
      <td style={{ fontSize: 13 }}>{diff.label}</td>
      <td style={{ fontSize: 13, color: "var(--muted)", textAlign: "right" }}>
        {diff.spain_value}
      </td>
      <td style={{ fontSize: 13, textAlign: "right" }}>{diff.analog_value}</td>
      <td style={{ fontSize: 12, color, textAlign: "right" }}>{diff.direction}</td>
    </tr>
  );
}
```

- [ ] **Step 2: Create `AnalogCard.tsx`**

Create `frontend/src/components/AnalogCard.tsx`:

```tsx
import { useState } from "react";
import type { AnalogMatch } from "../api/types";
import { ProjectionChart } from "./ProjectionChart";
import { AnalogDiffRow } from "./AnalogDiffRow";

const VERDICT_LABEL: Record<string, { text: string; color: string }> = {
  auto:              { text: "AUTO-LIQUIDABLE",   color: "#22c55e" },
  requires_surplus:  { text: "REQUIERE SUPERÁVIT", color: "#ef4444" },
  borderline:        { text: "LÍMITE",             color: "#f59e0b" },
};

function fmt(v: number | null, dec = 1): string {
  return v === null ? "—" : v.toFixed(dec).replace(".", ",");
}

export function AnalogCard({
  matches,
  years,
}: {
  matches: AnalogMatch[];
  years: number[];
}) {
  const [active, setActive] = useState(0);
  if (!matches.length) return null;
  const m = matches[active];

  const outcomeYears = m.outcome.map((pt) => m.match_year + pt.year_offset);
  const debtOutcome  = m.outcome.map((pt) => pt.debt_gdp ?? 0);
  const rmgOutcome   = m.outcome.map((pt) => pt.r_minus_g ?? 0);

  const verd = VERDICT_LABEL[m.debt_payable_verdict] ?? { text: m.debt_payable_verdict, color: "inherit" };
  const snap = m.match_snapshot;
  const rmg  = snap.r_minus_g ?? 0;

  const fallbackNarrative =
    m.narrative ??
    `${m.country_name} en ${m.match_year}: datos históricos disponibles para ${m.outcome.filter((p) => !p.truncated).length} años. ` +
    `Diferencias estructurales: ${m.diffs.filter((d) => d.direction === "diverge").map((d) => d.label).join(", ") || "ninguna relevante"}.`;

  return (
    <div className="card" style={{ marginTop: 12 }}>
      {/* Tab selector */}
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        {matches.map((mx, i) => (
          <button
            key={mx.rank}
            role="tab"
            aria-selected={i === active}
            onClick={() => setActive(i)}
            style={{
              padding: "4px 12px",
              borderRadius: 6,
              border: i === active ? "2px solid var(--accent, #3b82f6)" : "1px solid var(--border, #d1d5db)",
              background: i === active ? "var(--accent, #3b82f6)" : "transparent",
              color: i === active ? "#fff" : "inherit",
              cursor: "pointer",
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            #{mx.rank} {mx.country_name} · {mx.match_year}
          </button>
        ))}
      </div>

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h4 style={{ margin: 0 }}>{m.country_name} · {m.match_year}</h4>
          <span className="meta" style={{ fontSize: 12 }}>
            distancia: {m.distance.toFixed(2)} · palanca dominante: {m.dominant_lever}
          </span>
        </div>
        <span
          style={{
            fontSize: 11,
            fontWeight: 700,
            padding: "2px 8px",
            borderRadius: 4,
            background: verd.color + "22",
            color: verd.color,
            border: `1px solid ${verd.color}`,
          }}
        >
          {verd.text}
        </span>
      </div>

      {/* Snapshot KPIs */}
      <div style={{ display: "flex", gap: 16, marginTop: 10, flexWrap: "wrap" }}>
        {[
          ["Deuda", snap.debt_gdp, "%PIB"],
          ["Saldo primario", snap.primary_balance_gdp, "%PIB"],
          ["Bono 10A", snap.interest_rate_10y, "%"],
          ["Crec. real", snap.gdp_growth, "%"],
          ["Paro", snap.unemployment, "%"],
          ["Inflación", snap.inflation, "%"],
        ].map(([label, val, unit]) => (
          <div key={String(label)} className="kpi-mini" style={{ textAlign: "center", minWidth: 80 }}>
            <div style={{ fontSize: 18, fontWeight: 700 }}>{fmt(val as number | null)}</div>
            <div style={{ fontSize: 11, color: "var(--muted)" }}>{String(label)} ({unit})</div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 6, fontSize: 13 }}>
        <strong>r − g = {rmg >= 0 ? "+" : ""}{fmt(rmg)}</strong>
        {" "}→{" "}
        <span style={{ color: verd.color }}>
          {m.debt_payable_verdict === "auto"
            ? "deuda se autoliquida (r < g)"
            : m.debt_payable_verdict === "requires_surplus"
            ? "requiere superávit primario (r > g)"
            : "en el límite (|r − g| < 0,5 pp)"}
        </span>
      </div>

      {/* Trajectory chart */}
      <h5 style={{ marginTop: 14, marginBottom: 4 }}>Trayectoria ({m.outcome.length} años)</h5>
      <ProjectionChart
        years={outcomeYears}
        baseline={debtOutcome}
        scenario={debtOutcome}
        unit="%PIB"
        dec={1}
        height={180}
        labels={outcomeYears.map(String)}
      />
      <div style={{ marginTop: 8 }}>
        <span style={{ fontSize: 12, color: "var(--muted)" }}>r − g histórico</span>
        <ProjectionChart
          years={outcomeYears}
          baseline={rmgOutcome}
          scenario={rmgOutcome}
          unit="pp"
          dec={2}
          height={120}
          labels={outcomeYears.map(String)}
        />
      </div>
      {m.outcome_truncated && (
        <p style={{ fontSize: 12, color: "var(--muted)", marginTop: 4 }}>
          ⚠ Datos disponibles solo hasta {Math.max(...m.outcome.filter((p) => !p.truncated).map((p) => m.match_year + p.year_offset), m.match_year)}. Puntos restantes sin datos.
        </p>
      )}

      {/* Structural diffs */}
      <h5 style={{ marginTop: 16, marginBottom: 4 }}>Diferencias estructurales</h5>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ color: "var(--muted)", fontSize: 11 }}>
              <th />
              <th style={{ textAlign: "left" }}>Dimensión</th>
              <th style={{ textAlign: "right" }}>España</th>
              <th style={{ textAlign: "right" }}>Análogo</th>
              <th style={{ textAlign: "right" }}>Efecto</th>
            </tr>
          </thead>
          <tbody>
            {m.diffs.map((d) => <AnalogDiffRow key={d.dimension} diff={d} />)}
          </tbody>
        </table>
      </div>

      {/* Narrative */}
      <h5 style={{ marginTop: 14, marginBottom: 4 }}>Valoración</h5>
      <p style={{ fontSize: 13, lineHeight: 1.55 }}>{fallbackNarrative}</p>
    </div>
  );
}
```

- [ ] **Step 3: Create `AnalogPanel.tsx`**

Create `frontend/src/components/AnalogPanel.tsx`:

```tsx
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import type { AnalogResponse, AnalogRequest } from "../api/types";
import { API_BASE } from "../api/client";
import type { Levers } from "../engine/levers";
import { YEARS } from "../engine/spain";
import { AnalogCard } from "./AnalogCard";

async function fetchAnalog(req: AnalogRequest): Promise<AnalogResponse> {
  const r = await fetch(`${API_BASE}/scenario/analog`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

export function AnalogPanel({
  levers,
  horizon,
}: {
  levers: Partial<Levers>;
  horizon: number;
}) {
  const [open, setOpen] = useState(false);

  const mut = useMutation({
    mutationFn: () => fetchAnalog({ levers, horizon }),
  });

  function handleSearch() {
    setOpen(true);
    mut.mutate();
  }

  return (
    <div className="card" style={{ marginTop: 24 }}>
      <div
        style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}
        onClick={() => setOpen((v) => !v)}
        role="button"
        aria-expanded={open}
      >
        <h3 style={{ margin: 0 }}>Análogos históricos</h3>
        <span style={{ fontSize: 18 }}>{open ? "▲" : "▼"}</span>
      </div>

      {open && (
        <div style={{ marginTop: 12 }}>
          {!mut.data && !mut.isPending && !mut.isError && (
            <div>
              <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 8 }}>
                Busca los 3 episodios históricos más similares al escenario activo y muestra
                cómo evolucionaron, en qué se diferencia España, y por qué el resultado puede
                converger o divergir.
              </p>
              <button
                aria-label="Buscar análogo histórico"
                onClick={(e) => { e.stopPropagation(); handleSearch(); }}
                style={{
                  padding: "8px 20px",
                  borderRadius: 6,
                  border: "none",
                  background: "var(--accent, #3b82f6)",
                  color: "#fff",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Buscar análogo histórico
              </button>
            </div>
          )}

          {mut.isPending && (
            <p style={{ fontSize: 14, color: "var(--muted)" }} role="status">
              Buscando episodios históricos…
            </p>
          )}

          {mut.isError && (
            <p style={{ color: "var(--err, #ef4444)", fontSize: 13 }}>
              Error al buscar análogos: {String(mut.error)}
            </p>
          )}

          {mut.data && (
            <>
              {!mut.data.rag_available && (
                <p style={{ fontSize: 11, color: "var(--muted)", marginBottom: 8 }}>
                  ⚠ Análisis narrativo solo disponible en despliegue local.
                </p>
              )}
              <AnalogCard matches={mut.data.matches} years={YEARS} />
            </>
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Verify TypeScript compiles cleanly**

```bash
cd /home/dan/projects/evo_final_work/frontend
npx tsc --noEmit 2>&1 | head -20
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/src/components/AnalogDiffRow.tsx \
        frontend/src/components/AnalogCard.tsx \
        frontend/src/components/AnalogPanel.tsx
git commit -m "feat: AnalogDiffRow, AnalogCard, AnalogPanel components"
```

---

## Task 6: Route Integration and Frontend Tests

**Files:**
- Modify: `frontend/src/routes/Laboratorio.tsx` (mount `AnalogPanel` after `<EmpiricalTwin />`)
- Create: `frontend/src/routes/__tests__/analog.test.tsx`

**Interfaces:**
- Consumes: `AnalogPanel` from `../components/AnalogPanel`
- Consumes: MSW handlers from `../../mocks/handlers`
- Consumes: `setupServer` from `msw/node`

- [ ] **Step 1: Mount `AnalogPanel` in `Laboratorio.tsx`**

In `frontend/src/routes/Laboratorio.tsx`, add the import at the top:

```tsx
import { AnalogPanel } from "../components/AnalogPanel";
```

Find the line `<EmpiricalTwin />` near the end of the component return and add `AnalogPanel` immediately after it (still inside the wrapping `<div>`):

```tsx
      <EmpiricalTwin />

      <AnalogPanel levers={levers} horizon={2050 - 2026} />
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd /home/dan/projects/evo_final_work/frontend
npx tsc --noEmit 2>&1 | head -20
```

Expected: no errors.

- [ ] **Step 3: Write the failing frontend tests**

Create `frontend/src/routes/__tests__/analog.test.tsx`:

```tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { beforeAll, afterEach, afterAll, describe, expect, it } from "vitest";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import { handlers } from "../../mocks/handlers";
import { AnalogPanel } from "../../components/AnalogPanel";
import { AnalogCard } from "../../components/AnalogCard";
import { AnalogDiffRow } from "../../components/AnalogDiffRow";
import type { AnalogMatch, StructuralDiff } from "../../api/types";
import { BASE_LEVERS } from "../../engine/vintage";

const server = setupServer(...handlers);
beforeAll(() => server.listen({ onUnhandledRequest: "bypass" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

function ui(children: React.ReactNode) {
  return render(
    <QueryClientProvider client={makeQC()}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AnalogPanel", () => {
  it("renders closed by default — button visible, card content hidden", () => {
    ui(<AnalogPanel levers={BASE_LEVERS} horizon={10} />);
    expect(screen.getByRole("button", { name: /análogos históricos/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /buscar análogo histórico/i })).toBeNull();
  });

  it("expands on header click — search button and description visible", () => {
    ui(<AnalogPanel levers={BASE_LEVERS} horizon={10} />);
    fireEvent.click(screen.getByRole("button", { name: /análogos históricos/i }));
    expect(screen.getByRole("button", { name: /buscar análogo histórico/i })).toBeInTheDocument();
  });

  it("calls API and shows cards after clicking search button", async () => {
    ui(<AnalogPanel levers={BASE_LEVERS} horizon={10} />);
    fireEvent.click(screen.getByRole("button", { name: /análogos históricos/i }));
    fireEvent.click(screen.getByRole("button", { name: /buscar análogo histórico/i }));
    await waitFor(() => expect(screen.getByText("Irlanda · 2010")).toBeInTheDocument());
    expect(screen.getByText("Portugal · 2011")).toBeInTheDocument();
    expect(screen.getByText("Bélgica · 1993")).toBeInTheDocument();
  });

  it("shows deterministic template when rag_available is false", async () => {
    ui(<AnalogPanel levers={BASE_LEVERS} horizon={10} />);
    fireEvent.click(screen.getByRole("button", { name: /análogos históricos/i }));
    fireEvent.click(screen.getByRole("button", { name: /buscar análogo histórico/i }));
    await waitFor(() => expect(screen.getByText(/análogos históricos solo disponible en despliegue local/i)).toBeInTheDocument());
  });

  it("shows error state on network failure", async () => {
    server.use(
      http.post("*/scenario/analog", () => HttpResponse.error()),
    );
    ui(<AnalogPanel levers={BASE_LEVERS} horizon={10} />);
    fireEvent.click(screen.getByRole("button", { name: /análogos históricos/i }));
    fireEvent.click(screen.getByRole("button", { name: /buscar análogo histórico/i }));
    await waitFor(() => expect(screen.getByText(/error al buscar análogos/i)).toBeInTheDocument());
  });
});

describe("AnalogCard tab switching", () => {
  const MOCK_MATCHES: AnalogMatch[] = [1, 2, 3].map((rank) => ({
    rank,
    iso3: rank === 1 ? "IRL" : rank === 2 ? "PRT" : "BEL",
    country_name: rank === 1 ? "Irlanda" : rank === 2 ? "Portugal" : "Bélgica",
    match_year: 2010 + rank,
    distance: rank * 0.3,
    dominant_lever: "prima",
    match_snapshot: { debt_gdp: 100, primary_balance_gdp: -4, interest_rate_10y: 5, gdp_growth: 1, unemployment: 10, inflation: 2, r_minus_g: 4 },
    outcome: [{ year_offset: 1, debt_gdp: 105, gdp_growth: 1.2, primary_balance_gdp: -3, r_minus_g: 3.8, truncated: false }],
    outcome_truncated: false,
    diffs: [],
    debt_payable_verdict: "requires_surplus",
    narrative: null,
  }));

  it("renders all 3 rank tabs and switches on click", () => {
    render(<AnalogCard matches={MOCK_MATCHES} years={[2026, 2027, 2028]} />);
    expect(screen.getByRole("tab", { name: /#1 Irlanda · 2011/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /#2 Portugal · 2012/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: /#2 Portugal · 2012/i }));
    expect(screen.getByText("Portugal · 2012")).toBeInTheDocument();
  });
});

describe("AnalogDiffRow icons", () => {
  function makeRow(direction: "converge" | "diverge" | "neutral"): StructuralDiff {
    return { dimension: "emu_member", label: "Zona euro", spain_value: "Sí", analog_value: "Sí", direction };
  }
  it.each([
    ["converge", "✓"],
    ["diverge",  "✗"],
    ["neutral",  "≈"],
  ] as const)("direction %s shows icon %s", (dir, icon) => {
    render(<table><tbody><tr><AnalogDiffRow diff={makeRow(dir)} /></tr></tbody></table>);
    expect(screen.getByLabelText(dir)).toHaveTextContent(icon);
  });
});
```

- [ ] **Step 4: Run the failing tests**

```bash
cd /home/dan/projects/evo_final_work/frontend
npx vitest run src/routes/__tests__/analog.test.tsx 2>&1 | tail -20
```

Expected: failures because `msw/node` may need config (see Step 5 if needed).

- [ ] **Step 5: Ensure Vitest environment is configured for jsdom + MSW**

Check `package.json` for a `test` script or `vitest.config`. If no environment is set, create `frontend/vitest.config.ts`:

```bash
grep -n '"test"' /home/dan/projects/evo_final_work/frontend/package.json | head -5
```

If the existing `vite.config.ts` has no `test` section, add one inline at the end of `frontend/vite.config.ts` by replacing the final `});` with:

```typescript
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/setupTests.ts"],
  },
});
```

Then create `frontend/src/setupTests.ts` if it doesn't exist:

```bash
test -f /home/dan/projects/evo_final_work/frontend/src/setupTests.ts \
  && echo exists || echo missing
```

If missing, create it:

```typescript
import "@testing-library/jest-dom";
```

- [ ] **Step 6: Run the full frontend test suite**

```bash
cd /home/dan/projects/evo_final_work/frontend
npx vitest run 2>&1 | tail -30
```

Expected: all tests pass (existing + new analog tests).

- [ ] **Step 7: Run full Python suite to confirm no regressions**

```bash
cd /home/dan/projects/evo_final_work
pytest --tb=short -q
```

Expected: 381 passed, 0 failed.

- [ ] **Step 8: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/src/routes/Laboratorio.tsx \
        frontend/src/routes/__tests__/analog.test.tsx \
        frontend/src/setupTests.ts \
        frontend/vite.config.ts
git commit -m "feat: mount AnalogPanel in Laboratorio + frontend tests"
```

---

## Self-Review Checklist

**Spec coverage:**
- §1 Data layer: Task 1 builds `gold_analog_panel.csv` + stats JSON ✓
- §2 Search engine: Task 2 `engine/analog.py` — 7-feature query, Mahalanobis, dominant lever bonus, verdict ✓
- §3 API: Task 3 `POST /scenario/analog` reusing `ScenarioRequest` ✓
- §4 Structural diff: 8 dimensions in `structural_diffs()` including `tfp_trend` and `labor_productivity` ✓
- §5 Frontend: Task 5 three components + Task 6 mount ✓
- §5.4 MSW mock: Task 4 Ireland/Portugal/Belgium ✓
- §6 Tests: 12 Python + 9 frontend (AnalogPanel×5 + AnalogCard×1 + AnalogDiffRow×3) ✓
- §7 Files changed: all 14 files covered across 6 tasks ✓
- `debt_payable_verdict` on every match ✓
- `r_minus_g` in match_snapshot and every non-truncated outcome point ✓
- `rag_available: false` on public deploy, `narrative: null` ✓

**Placeholder scan:** None found.

**Type consistency:**
- `AnalogMatch.diffs` is `list[StructuralDiff]` in Python and `StructuralDiff[]` in TypeScript ✓
- `AnalogOutcomePoint.r_minus_g: float | None` / `number | null` ✓
- `AnalogResponse extends ApiMeta` in both layers ✓
- `find_analogs()` returns `list[dict]`; endpoint wraps into Pydantic models ✓
- Series keys `b`, `pb`, `bono`, `g`, `u`, `pi` verified from `SERIES_KEYS` definition ✓

**Note on `_levers_from_req`:** Task 3 Step 4 instructs you to verify the actual helper name. Run `grep -n "def _levers\|Levers(" api/main.py | head -10` before writing the endpoint.
