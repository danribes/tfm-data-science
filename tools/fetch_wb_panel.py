"""Fetch the cross-country macro panel for the distress classifier.

Resumable on purpose. The World Bank API times out often enough that a
one-shot script reliably dies part-way through and throws away the indicators
it had already pulled; each indicator is cached to its own file as it lands, so
a rerun costs only what is still missing.

    python -m tools.fetch_wb_panel            # fetch what is missing
    python -m tools.fetch_wb_panel --rebuild  # re-pull everything

Writes data/external/wb_macro_panel.csv.gz.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data_cache" / "wb_panel"
OUT = ROOT / "data" / "external" / "wb_macro_panel.csv.gz"

#: The standard sovereign early-warning set: external solvency, liquidity, and
#: the macro conditions that precede a stop. Chosen for coverage in the
#: countries that actually default rather than for what a rich country reports
#: well — central-government debt is the obvious omission-by-necessity, since it
#: is missing for most of the panel exactly where the positives are.
INDICATORS = {
    "ext_debt_gni":   "DT.DOD.DECT.GN.ZS",   # external debt stocks, % GNI
    "debt_service_x": "DT.TDS.DECT.EX.ZS",   # debt service, % of exports
    "reserves_mo":    "FI.RES.TOTL.MO",      # reserves, months of imports
    "reserves_debt":  "FI.RES.TOTL.DT.ZS",   # reserves, % of external debt
    "cab_gdp":        "BN.CAB.XOKA.GD.ZS",   # current account, % GDP
    "gdp_growth":     "NY.GDP.MKTP.KD.ZG",
    "inflation":      "FP.CPI.TOTL.ZG",
    "gdp_pc":         "NY.GDP.PCAP.KD",
    "exports_gdp":    "NE.EXP.GNFS.ZS",
    "gov_debt_gdp":   "GC.DOD.TOTL.GD.ZS",
}

START, END = 1960, 2024


def fetch_indicator(code: str, attempts: int = 4) -> pd.DataFrame:
    rows: list[dict] = []
    page = 1
    while True:
        for attempt in range(attempts):
            try:
                r = requests.get(
                    f"https://api.worldbank.org/v2/country/all/indicator/{code}",
                    params={"format": "json", "per_page": 20000,
                            "date": f"{START}:{END}", "page": page},
                    timeout=120)
                r.raise_for_status()
                payload = r.json()
                break
            except Exception as exc:
                if attempt == attempts - 1:
                    raise
                # Linear backoff: the API's failures are load, not rate limits,
                # so waiting longer helps and hammering does not.
                wait = 5 * (attempt + 1)
                print(f"      reintento {attempt + 1}/{attempts - 1} en {wait}s "
                      f"({type(exc).__name__})", flush=True)
                time.sleep(wait)

        if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
            break
        for obs in payload[1]:
            if obs.get("value") is None:
                continue
            rows.append({"iso3": obs["countryiso3code"], "year": int(obs["date"]),
                         "value": float(obs["value"])})
        if page >= payload[0]["pages"]:
            break
        page += 1
        time.sleep(0.3)

    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rebuild", action="store_true", help="ignora la caché")
    args = ap.parse_args()

    CACHE.mkdir(parents=True, exist_ok=True)
    frames: dict[str, pd.DataFrame] = {}

    for key, code in INDICATORS.items():
        path = CACHE / f"{key}.csv"
        if path.exists() and not args.rebuild:
            frames[key] = pd.read_csv(path)
            print(f"{key:16} {len(frames[key]):6,} obs  (caché)")
            continue
        print(f"{key:16} descargando {code}…", flush=True)
        d = fetch_indicator(code)
        d.to_csv(path, index=False)
        frames[key] = d
        print(f"{key:16} {len(d):6,} obs")

    merged = None
    for key, d in frames.items():
        d = d[d.iso3.astype(str).str.len() == 3].rename(columns={"value": key})
        merged = d if merged is None else merged.merge(d, on=["iso3", "year"], how="outer")

    assert merged is not None
    merged = merged.sort_values(["iso3", "year"]).reset_index(drop=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUT, index=False, compression="gzip")

    print(f"\n{OUT.relative_to(ROOT)}  {OUT.stat().st_size / 1e6:.2f} MB")
    print(f"{len(merged):,} país-año · {merged.iso3.nunique()} países · "
          f"{int(merged.year.min())}-{int(merged.year.max())}")
    cover = merged.notna().mean().drop(["iso3", "year"]).sort_values(ascending=False)
    print("\ncobertura por variable:")
    for k, v in cover.items():
        print(f"  {k:16} {v:5.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
