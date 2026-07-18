"""Conector T1.2.1 — Eurostat gov_10a_exp (gasto AAPP por función × tipo económico).

Extracción SELECTIVA según docs/data_dictionary_vivienda.md §1.1:
  unit  = PC_GDP + MIO_EUR
  sector = S13
  cofog99 = TOTAL + GF01..GF10 (L1) + GF0601, GF1006 (L2 vivienda)
  na_item = TE, D1, P2, D3, D62, D9, P51G
  geo   = todos (UE+EFTA+UK+agregados), 1995-2023

Una petición por na_item (≈25k celdas) para no reventar la API.
Salida: storage/processed/gov_10a_exp.csv (largo: geo,year,cofog,na_item,unit,value)
"""
from __future__ import annotations

import sys
import time

import pandas as pd

from base import PROCESSED, http_json, jsonstat_to_df, save_raw

API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/gov_10a_exp"

COFOG = ["TOTAL"] + [f"GF{i:02d}" for i in range(1, 11)] + ["GF0601", "GF1006"]
NA_ITEMS = ["TE", "D1", "P2", "D3", "D62", "D9", "P51G"]
UNITS = ["PC_GDP", "MIO_EUR"]


def fetch() -> pd.DataFrame:
    frames = []
    for na in NA_ITEMS:
        params = [
            ("format", "JSON"), ("lang", "EN"),
            ("sector", "S13"), ("na_item", na),
            ("sinceTimePeriod", "1995"), ("untilTimePeriod", "2023"),
        ]
        params += [("unit", u) for u in UNITS]
        params += [("cofog99", c) for c in COFOG]
        js = http_json(API, params=dict_multi(params))
        save_raw(f"gov_10a_exp_{na}", js, API + f"?na_item={na}")
        df = jsonstat_to_df(js)
        frames.append(df)
        print(f"  na_item={na}: {len(df):6d} filas", flush=True)
        time.sleep(0.5)
    out = pd.concat(frames, ignore_index=True)
    out = out.rename(columns={"time": "year", "cofog99": "cofog"})
    out = pd.DataFrame(out[["geo", "year", "cofog", "na_item", "unit", "value"]])
    out["year"] = out["year"].astype(int)
    return out


def dict_multi(pairs):
    """requests admite lista de tuplas para params repetidos."""
    return pairs


def smoke_test(df: pd.DataFrame) -> None:
    pk = ["geo", "year", "cofog", "na_item", "unit"]
    dup = df.duplicated(subset=pk).sum()
    assert dup == 0, f"PK duplicada: {dup} filas"
    pct = df[df.unit == "PC_GDP"]
    assert pct["value"].max() < 70, f"máximo PC_GDP fuera: {pct['value'].max()}"
    # Negativos legítimos y acotados: ventas netas de activos/derechos — HU 1995-96
    # privatización de vivienda (P51G y TE en GF06), SK 2023 defensa/Ucrania,
    # EE 2010-11 venta de permisos Kioto (TE en GF05). Se FLAGuean, no se rechazan.
    neg = pct.loc[pct["value"] < 0]
    grave = neg.loc[(neg["value"] < -0.5) & (~neg["na_item"].isin(["P51G", "D9", "D3"]))]
    assert len(grave) == 0, f"negativos no explicables (<-0.5 fuera de P51G/D9/D3): {grave.to_dict('records')}"
    assert float(pct["value"].min()) > -5, f"negativo extremo: {pct['value'].min()}"
    print(f"  negativos flaggeados (ventas netas de activos, legítimos): {len(neg)}")
    # anclas verificadas en vivo (sesión 2026-07-17)
    es_gf06 = df.query("geo=='ES' and year==2023 and cofog=='GF06' and na_item=='TE' and unit=='PC_GDP'")["value"]
    assert len(es_gf06) == 1 and abs(es_gf06.iloc[0] - 0.5) <= 0.15, f"ancla ES GF06 2023: {es_gf06.tolist()}"
    ee_inv = df.query("geo=='EE' and year==2023 and cofog=='TOTAL' and na_item=='P51G' and unit=='PC_GDP'")["value"]
    assert len(ee_inv) == 1 and abs(ee_inv.iloc[0] - 6.5) <= 0.3, f"ancla EE P51G 2023: {ee_inv.tolist()}"
    it_gf06 = df.query("geo=='IT' and year==2023 and cofog=='GF06' and na_item=='TE' and unit=='PC_GDP'")["value"]
    assert len(it_gf06) == 1 and it_gf06.iloc[0] > 3, f"ancla IT superbonus: {it_gf06.tolist()}"
    print(f"SMOKE OK — {len(df)} filas, PK única, rangos y 3 anclas verificadas")


def rebuild_from_raw() -> pd.DataFrame:
    """Reconstruye desde storage/raw sin tocar la API (idempotente)."""
    import json

    from base import RAW
    frames = []
    for na in NA_ITEMS:
        js = json.loads((RAW / f"gov_10a_exp_{na}.json").read_text())
        frames.append(jsonstat_to_df(js))
    out = pd.concat(frames, ignore_index=True)
    out = out.rename(columns={"time": "year", "cofog99": "cofog"})
    out = pd.DataFrame(out[["geo", "year", "cofog", "na_item", "unit", "value"]])
    out["year"] = out["year"].astype(int)
    return out


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    if "--from-raw" in sys.argv:
        print("Reconstruyendo desde raw (sin API)…")
        df = rebuild_from_raw()
    else:
        print("Extrayendo gov_10a_exp (7 na_item × 13 cofog × 2 unidades × ~40 geo × 29 años)…")
        df = fetch()
    smoke_test(df)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    dest = PROCESSED / "gov_10a_exp.csv"
    df.to_csv(dest, index=False)
    print(f"→ {dest} ({dest.stat().st_size//1024} KB)")
