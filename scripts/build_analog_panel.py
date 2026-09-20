"""Rebuild historical analog data (observations through 2023).

Sources:
  - World Bank API (wbgapi) — growth, inflation, unemployment, trade openness,
    external debt share, GDP-per-worker growth
  - IMF DataMapper cached/downloaded release — gross debt and overall balance (% GDP)
  - Penn World Table 10.01 (already in data/gold/pwt1001.xlsx) — TFP growth
  - Static embedded dicts — EMU membership, Polity5 proxy, IRR FX regime

Run once; output is committed to git as a frozen gold file.
"""
from __future__ import annotations

import csv
import hashlib
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
    "debt_gdp", "overall_balance_gdp", "gdp_growth", "unemployment", "inflation",
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
# These are hand-assigned, time-invariant legacy proxies, not observed Polity5 scores.
# They are excluded from current matching and structural conclusions.
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
# Time-invariant legacy categories: excluded from historical structural conclusions.
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
        "FR.INR.LEND": "lending_rate",  # private bank lending rate; context only, not sovereign yield
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
    """Use overall balance consistently; never substitute a primary balance."""
    import requests

    def _datamapper(indicator: str) -> pd.DataFrame:
        cache = GOLD / f"imf_{indicator}.json"
        if cache.exists():
            import json as _json
            data = _json.loads(cache.read_text())
        else:
            url = (f"https://www.imf.org/external/datamapper/api/v1/{indicator}")
            print(f"  Fetching IMF datamapper {indicator} …", file=sys.stderr)
            r = requests.get(url, timeout=120)
            r.raise_for_status()
            data = r.json()
            cache.write_text(r.text)
        vals = data.get("values", {}).get(indicator, {})
        rows = []
        for iso3, yr_vals in vals.items():
            for yr_str, v in yr_vals.items():
                rows.append({"iso3": iso3, "year": int(yr_str), indicator: v})
        return pd.DataFrame(rows)

    debt_df = _datamapper("GGXWDG_NGDP")

    pb_indicator = "GGXCNL_NGDP"
    pb_df = _datamapper(pb_indicator)
    if pb_df.empty:
        raise ValueError("IMF overall balance unavailable; cannot substitute primary balance")

    pivot = debt_df.merge(pb_df, on=["iso3", "year"], how="outer")
    pivot.rename(columns={
        "GGXWDG_NGDP": "debt_gdp",
        pb_indicator: "overall_balance_gdp",
    }, inplace=True)
    # Keep only historical years (1980-2023)
    pivot = pivot[(pivot["year"] >= 1980) & (pivot["year"] <= 2023)]
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
    # Descriptive source statistics only. Runtime fits its complete candidate population.
    stats = {}
    for feat in QUERY_FEATURES:
        if feat in df.columns:
            col = df[feat].dropna()
            mean_val = float(col.mean()) if len(col) > 0 else None
            std_val = float(col.std()) if len(col) > 0 else None
            stats[feat] = {"mean": mean_val, "std": std_val}
    return stats


def _append_manifest() -> None:
    manifest = GOLD / "manifest.csv"
    rows = []
    if manifest.exists():
        with open(manifest) as f:
            rows = list(csv.DictReader(f))
    fieldnames = ["source", "url", "acquired_at", "observation_cutoff", "built_at",
                  "bytes", "raw_file", "processed_file", "kind", "sha256"]
    derived = {"gold_analog_panel.csv": "analog_panel", "gold_analog_panel_stats.json": "analog_stats"}
    rows = [r for r in rows if r.get("processed_file") not in derived]
    today = date.today().isoformat()
    for filename, source in derived.items():
        path = GOLD / filename
        rows.append({"source": source, "url": "", "acquired_at": "",
                     "observation_cutoff": "2023", "built_at": today,
                     "bytes": path.stat().st_size, "raw_file": "",
                     "processed_file": filename, "kind": "derived",
                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    with manifest.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
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
    if "labor_prod_growth" in df.columns:
        df["labor_prod_growth_5y"] = (
            df.groupby("iso3")["labor_prod_growth"]
            .transform(lambda x: x.rolling(5, min_periods=3).mean())
        )
    else:
        df["labor_prod_growth_5y"] = np.nan

    # Add structural columns
    df = _add_structural(df)

    # Missing auxiliary rates stay missing; they cannot identify sovereign r−g.
    for col in ("lending_rate", "ext_debt_share"):
        if col not in df.columns:
            df[col] = np.nan

    # Filter: drop rows with missing debt_gdp; keep 1980-2023
    df = df.dropna(subset=["debt_gdp"])
    df = df[(df["year"] >= 1980) & (df["year"] <= 2023)]

    # Drop intermediate column
    df = df.drop(columns=["labor_prod_growth"], errors="ignore")

    missing = set(QUERY_FEATURES) - set(df.columns)
    if missing:
        raise ValueError(f"Incomplete acquisition; missing required analog columns: {sorted(missing)}")
    complete = df[(df.iso3 != "ESP") & (df.year <= 2020)].dropna(subset=QUERY_FEATURES)
    if len(complete) <= len(QUERY_FEATURES):
        raise ValueError("Insufficient complete historical candidates; existing gold panel retained")

    out_cols = [
        "iso3", "year", "debt_gdp", "overall_balance_gdp", "lending_rate",
        "gdp_growth", "unemployment", "inflation", "emu_member", "fx_regime",
        "ext_debt_share", "democracy", "trade_openness", "tfp_growth_5y",
        "labor_prod_growth_5y",
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
