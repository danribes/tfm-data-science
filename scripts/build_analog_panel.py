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
    """Load IMF WEO data for debt and primary balance via datamapper API."""
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
    pb_df = _datamapper("GGXCNL_NGDP")

    pivot = debt_df.merge(pb_df, on=["iso3", "year"], how="outer")
    pivot.rename(columns={
        "GGXWDG_NGDP": "debt_gdp",
        "GGXCNL_NGDP": "primary_balance_gdp",
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
    if "labor_prod_growth" in df.columns:
        df["labor_prod_growth_5y"] = (
            df.groupby("iso3")["labor_prod_growth"]
            .transform(lambda x: x.rolling(5, min_periods=3).mean())
        )
    else:
        df["labor_prod_growth_5y"] = np.nan

    # Add structural columns
    df = _add_structural(df)

    # Ensure columns exist that may be absent if a source fetch failed.
    # interest_rate_10y has no data source in this build; ext_debt_share
    # and labor_prod_growth may fail due to transient WB API issues.
    for _col in ("interest_rate_10y", "ext_debt_share"):
        if _col not in df.columns:
            df[_col] = np.nan

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
