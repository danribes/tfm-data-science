"""Cierre de huecos del PLAN_MAESTRO (F2.0 + controles F3.1 + Euríbor F4.1).

B10 desempleo (UE+mundo) · B11 intereses D41 · B12 pensiones+≥65 ·
controles WGI/urbanización/edad · confusores GHO (obesidad, tabaco) ·
Euríbor 12m vía ECB Data Portal (sustituye CSVs muertos del BdE).
"""
from __future__ import annotations

import io
import sys

import pandas as pd
import requests

from base import PROCESSED, RAW, UA, http_json
from eurostat_multi import run_one

EURO_SPECS = [
    ("une_rt_a", [("unit", "PC_ACT"), ("sex", "T"), ("age", "Y15-74")], "unemployment_eu"),
    ("gov_10a_main", [("sector", "S13"), ("unit", "PC_GDP"), ("na_item", "D41PAY")], "interest_paid"),
    # pensiones %PIB: GF1002 (vejez) del dataset ya validado — ESSPROS no tiene unidad %PIB
    ("gov_10a_exp", [("sector", "S13"), ("unit", "PC_GDP"), ("cofog99", "GF1002"), ("na_item", "TE")], "pensions_oldage"),
    ("demo_pjanbroad", [("sex", "T"), ("unit", "NR"), ("age", "Y_LT15"), ("age", "Y15-64"), ("age", "Y_GE65")], "population_broad_age"),
]

WB_SETS = {
    # WGI: ARCHIVADO en la API v2 (GE.EST "deleted or archived"); descarga en
    # govindicators.org es SPA-gated → DEFERRED (ruta: descarga manual o QoG).

    "wdi_extras": {
        "SL.UEM.TOTL.NE.ZS": "unemployment_global",  # el .ZS clásico está ARCHIVADO en la API
        "SP.URB.TOTL.IN.ZS": "urban_share",
    },
}

GHO_CODES = {
    "NCD_BMI_30A": "obesity",           # adultos IMC>=30, estandarizado
    "M_Est_tob_curr_std": "smoking",    # uso actual de tabaco, estandarizado (smk_ no existe)
}

ECB_EURIBOR = ("https://data-api.ecb.europa.eu/service/data/FM/"
               "M.U2.EUR.RT.MM.EURIBOR1YD_.HSTA?format=csvdata")


def fetch_eurostat_gaps() -> None:
    for ds, extra, name in EURO_SPECS:
        try:
            run_one(ds, extra, name)
        except Exception as e:  # noqa: BLE001
            print(f"  {name}: FALLO {str(e)[:110]}")


def fetch_wb(setname: str) -> None:
    frames = []
    for code, vn in WB_SETS[setname].items():
        js = http_json(f"https://api.worldbank.org/v2/country/all/indicator/{code}",
                       params=[("format", "json"), ("per_page", "20000"), ("date", "1995:2023")], timeout=240)
        if len(js) > 1 and js[1]:
            frames.append(pd.DataFrame([
                {"iso3": r["countryiso3code"], "year": int(r["date"]), "variable": vn, "value": r["value"]}
                for r in js[1] if r["value"] is not None and r["countryiso3code"]
            ]))
            print(f"    {code} → {vn}: {len(frames[-1])} filas")
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(PROCESSED / f"{setname}.csv", index=False)
    print(f"  {setname}: {len(out)} filas → {setname}.csv")


def fetch_gho() -> None:
    frames = []
    for code, vn in GHO_CODES.items():
        url = f"https://ghoapi.azureedge.net/api/{code}?$filter=Dim1%20eq%20%27SEX_BTSX%27"
        try:
            js = http_json(url, timeout=90)
            vals = js.get("value", [])
            if not vals:
                raise ValueError("vacío")
            frames.append(pd.DataFrame([
                {"iso3": r["SpatialDim"], "year": int(r["TimeDim"]), "variable": vn,
                 "value": float(r["NumericValue"])}
                for r in vals if r.get("NumericValue") is not None and r.get("SpatialDimType") == "COUNTRY"
            ]))
            print(f"    GHO {code} → {vn}: {len(frames[-1])} filas")
        except Exception as e:  # noqa: BLE001
            print(f"    GHO {code}: FALLO {str(e)[:90]}")
    if frames:
        out = pd.concat(frames, ignore_index=True)
        out.to_csv(PROCESSED / "gho_confounders.csv", index=False)
        print(f"  gho_confounders: {len(out)} filas → gho_confounders.csv")


def fetch_euribor_ecb() -> None:
    r = requests.get(ECB_EURIBOR, headers=UA, timeout=90)
    r.raise_for_status()
    (RAW / "ecb_euribor12m.csv").write_bytes(r.content)
    df = pd.read_csv(io.BytesIO(r.content))
    tcol = "TIME_PERIOD" if "TIME_PERIOD" in df.columns else df.columns[df.columns.str.contains("TIME", case=False)][0]
    vcol = "OBS_VALUE" if "OBS_VALUE" in df.columns else df.columns[-1]
    out = df[[tcol, vcol]].rename(columns={tcol: "month", vcol: "euribor_12m"}).dropna()
    assert len(out) > 200, f"euríbor corto: {len(out)}"
    out.to_csv(PROCESSED / "euribor_12m.csv", index=False)
    v99 = out[out["month"].astype(str).str.startswith("1999-01")]["euribor_12m"]
    print(f"  euribor_12m: {len(out)} meses (1999-01={float(v99.iloc[0]) if len(v99) else '?'}) → euribor_12m.csv")


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    print("— Eurostat (B10/B11/B12 + edad) —")
    fetch_eurostat_gaps()
    print("— World Bank (WGI + extras) —")
    for s in WB_SETS:
        try:
            fetch_wb(s)
        except Exception as e:  # noqa: BLE001
            print(f"  {s}: FALLO {str(e)[:110]}")
    print("— WHO GHO (confusores) —")
    fetch_gho()
    print("— ECB Euríbor —")
    try:
        fetch_euribor_ecb()
    except Exception as e:  # noqa: BLE001
        print(f"  euribor: FALLO {str(e)[:110]}")
