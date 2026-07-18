"""Conector multi-dataset Eurostat (T1.2.2, T1.2.3 y capa de ingresos del plan integral).

Un spec por dataset (docs/data_dictionary_master.md §1). Cada uno: raw inmutable
+ processed tidy + smoke básico (no vacío, PK única). Anclas donde se conocen.
"""
from __future__ import annotations

import sys
import time

import pandas as pd

from base import PROCESSED, http_json, jsonstat_to_df, save_raw

API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"

# (dataset, params-multivalor, nombre_salida)
SPECS: list[tuple[str, list[tuple[str, str]], str]] = [
    # --- outcomes vivienda (B2) — dims según diccionario maestro [V]: rskpovth/age/sex ---
    ("ilc_lvho07a", [("unit", "PC"), ("rskpovth", "TOTAL"), ("age", "TOTAL"), ("sex", "T")], "silc_overburden"),
    ("ilc_lvho05a", [("unit", "PC"), ("rskpovth", "TOTAL"), ("age", "TOTAL"), ("sex", "T")], "silc_overcrowding"),
    # --- focalización de transferencias (bolt-on T3.5.2) — statinfo=MED_EI, umbral B_60 ---
    ("ilc_li02", [("unit", "PC"), ("statinfo", "MED_EI"), ("rskpovth", "B_60"), ("age", "TOTAL"), ("sex", "T")], "arop_post"),
    ("ilc_li10", [("unit", "PC"), ("statinfo", "MED_EI"), ("rskpovth", "B_60"), ("age", "TOTAL"), ("sex", "T")], "arop_pre_nopensions"),
    # --- controles ---
    ("ilc_di12", [("statinfo", "GINI_HND"), ("age", "TOTAL")], "gini"),
    ("nama_10_pc", [("unit", "CP_PPS_EU27_2020_HAB"), ("na_item", "B1GQ")], "gdp_pc_pps"),
    ("demo_pjan", [("age", "TOTAL"), ("sex", "T"), ("unit", "NR")], "population"),
    ("demo_mlexpec", [("age", "Y_LT1"), ("sex", "T"), ("unit", "YR")], "life_expectancy_e0"),
    ("hlth_cd_apr", [("mortalit", "TRT"), ("mortalit", "PRVT"), ("unit", "RT"), ("sex", "T"), ("icd10", "TOTAL")], "avoidable_mortality"),
    # --- precios vivienda UE (comparador B2/B3) ---
    ("prc_hpi_q", [("purchase", "TOTAL"), ("unit", "I15_Q")], "house_price_index_q"),
    # --- migración (B4) ---
    ("migr_imm1ctz", [("citizen", "TOTAL"), ("agedef", "COMPLET"), ("age", "TOTAL"), ("sex", "T"), ("unit", "NR")], "immigration"),
    ("migr_emi2", [("agedef", "COMPLET"), ("age", "TOTAL"), ("sex", "T"), ("unit", "NR")], "emigration"),
    # --- lado de INGRESOS + déficit + deuda (objetivo integral) ---
    ("gov_10a_main", [("sector", "S13"), ("unit", "PC_GDP"), ("na_item", "TR"), ("na_item", "B9"),
                      ("na_item", "D2REC"), ("na_item", "D5REC"), ("na_item", "D61REC")], "gov_revenue_deficit"),
    ("gov_10dd_edpt1", [("sector", "S13"), ("unit", "PC_GDP"), ("na_item", "GD")], "gov_debt"),
    # --- protección social (ESSPROS, bolt-on) ---
    ("spr_exp_type", [("spdeps", "TOTAL"), ("unit", "PC_GDP")], "social_protection_exp"),
    # --- reciclaje (bolt-on GF0501) ---
    ("cei_wm011", [], "recycling_rate"),
]

BASE_TIME = [("sinceTimePeriod", "1995")]


def run_one(dataset: str, extra: list[tuple[str, str]], name: str) -> pd.DataFrame:
    params = [("format", "JSON"), ("lang", "EN")] + BASE_TIME + extra
    js = http_json(API + dataset, params=params)
    save_raw(name, js, API + dataset)
    df = jsonstat_to_df(js)
    assert len(df) > 0, f"{dataset}: vacío"
    dims = [c for c in df.columns if c != "value"]
    assert df.duplicated(subset=dims).sum() == 0, f"{dataset}: PK duplicada"
    dest = PROCESSED / f"{name}.csv"
    df.to_csv(dest, index=False)
    print(f"  {name:26s} {dataset:16s} {len(df):7d} filas → {dest.name}")
    return df


def anchors(results: dict[str, pd.DataFrame]) -> None:
    ok = []
    ov = results.get("silc_overburden")
    if ov is not None:
        es = ov.query("geo=='ES' and time=='2023'")["value"]
        assert len(es) and 5 < float(es.iloc[0]) < 15, f"ancla sobrecarga ES 2023: {es.tolist()}"
        ok.append(f"sobrecarga ES 2023={float(es.iloc[0])}")
    dbt = results.get("gov_debt")
    if dbt is not None:
        es = dbt.query("geo=='ES' and time=='2012'")["value"]
        assert len(es) and 80 < float(es.iloc[0]) < 100, f"ancla deuda ES 2012: {es.tolist()}"
        ok.append(f"deuda ES 2012={float(es.iloc[0])}")
    print("ANCLAS OK:", "; ".join(ok) if ok else "(ninguna evaluada)")


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    results = {}
    fails = []
    for dataset, extra, name in SPECS:
        try:
            results[name] = run_one(dataset, extra, name)
        except Exception as e:  # noqa: BLE001 — log y seguir; el fallo se reporta al final
            fails.append((dataset, name, str(e)[:140]))
            print(f"  {name:26s} {dataset:16s} FALLO: {str(e)[:110]}")
        time.sleep(0.4)
    anchors(results)
    print(f"\n{len(results)}/{len(SPECS)} datasets OK; fallos: {len(fails)}")
    for d, n, e in fails:
        print(f"  DEFERRED {d} ({n}): {e}")
