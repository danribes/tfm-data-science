"""Conector EUROPOP2023 (proj_23ndbi) — demografía proyectada 2023–2070 × 6 variantes.

Variantes: BSL (base), LFRT (fertilidad baja), LMRT (mortalidad baja),
HMIGR / LMIGR / NMIGR (migración alta / baja / NULA) — la palanca migratoria
que pide el análisis viene de serie en las proyecciones oficiales.
Salida en GOLD (la consume la API): gold_projections.csv
"""
from __future__ import annotations

import sys

import pandas as pd

from base import GOLD, http_json, save_raw

API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/proj_23ndbi"
INDICS = ["JAN", "NMIGRAT", "OLDDEP1", "PC_Y0_14", "PC_Y15_64"]


def fetch() -> pd.DataFrame:
    params = [("format", "JSON"), ("lang", "EN"), ("sinceTimePeriod", "2023"), ("untilTimePeriod", "2070")]
    params += [("indic_de", i) for i in INDICS]
    js = http_json(API, params=params, timeout=120)
    save_raw("proj_23ndbi", js, API)
    from base import jsonstat_to_df
    df = jsonstat_to_df(js)
    df = df.rename(columns={"time": "year", "indic_de": "indicator", "projection": "variant"})
    df["year"] = df["year"].astype(int)
    wide = df.pivot_table(index=["geo", "variant", "year"], columns="indicator", values="value").reset_index()
    wide["share65"] = 100.0 - wide["PC_Y0_14"] - wide["PC_Y15_64"]
    wide = wide.rename(columns={"JAN": "population", "NMIGRAT": "net_migration", "OLDDEP1": "olddep"})
    return wide


def smoke(df: pd.DataFrame) -> None:
    es = df.query("geo=='ES' and variant=='BSL'")
    s23 = float(es.query("year==2023")["share65"].iloc[0])
    s50 = float(es.query("year==2050")["share65"].iloc[0])
    assert 18 < s23 < 23, f"share65 ES 2023: {s23}"
    assert s50 > s23 + 5, f"envejecimiento ES no visible: {s23}->{s50}"
    nm = df.query("geo=='ES' and variant=='NMIGR' and year==2050")["share65"]
    assert float(nm.iloc[0]) > s50, "sin-migración debería envejecer MÁS"
    print(f"SMOKE PROJ OK — {len(df)} filas, {df.geo.nunique()} geos, 6 variantes; "
          f"ES share65: 2023={s23:.1f} → 2050 BSL={s50:.1f} / NMIGR={float(nm.iloc[0]):.1f}")


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    df = fetch()
    smoke(df)
    df.to_csv(GOLD / "gold_projections.csv", index=False)
    print("→ gold_projections.csv")
