"""Conectores menores: BdE Euríbor (CSV directo) + WWBI (API BM source=64).

WWBI: los 6 indicadores del diccionario (empleo público, masa salarial, prima,
sanitarios, docentes). El código exacto de la prima se resuelve en caliente
buscando 'PREM' en el listado del source 64.
"""
from __future__ import annotations


import sys

import pandas as pd
import requests

from base import PROCESSED, RAW, UA, http_json

BDE_URLS = [
    "https://www.bde.es/webbde/es/estadis/infoest/series/ti_1_7.csv",
    "https://www.bde.es/webbde/es/estadis/infoest/ti_1_7.csv",
]

WWBI_FIXED = [
    "BI.EMP.TOTL.PB.ZS",      # empleo público / empleo remunerado
    "BI.WAG.TOTL.GD.ZS",      # masa salarial %PIB
    "BI.WAG.TOTL.PB.ZS",      # masa salarial % gasto público
    "BI.EMP.FRML.HE.PB.ZS",   # sanitarios / empleados públicos
    "BI.EMP.FRML.TS.PB.ZS",   # docentes / empleados públicos
]


def fetch_euribor() -> pd.DataFrame | None:
    for url in BDE_URLS:
        try:
            r = requests.get(url, headers=UA, timeout=40)
            if r.status_code != 200 or len(r.content) < 1000:
                continue
            (RAW / "bde_ti_1_7.csv").write_bytes(r.content)
            raw = r.content.decode("latin-1").splitlines()
            rows = []
            for line in raw:
                parts = [p.strip('" ') for p in line.split(",")]
                # filas de datos: fecha estilo '02 ENE 1999' o 'DD MMM YYYY'
                if len(parts) >= 2 and re_date(parts[0]):
                    val = parts[1].replace(",", ".")
                    try:
                        rows.append({"fecha": parts[0], "euribor_12m": float(val)})
                    except ValueError:
                        pass
            df = pd.DataFrame(rows)
            if len(df) > 1000:
                df.to_csv(PROCESSED / "bde_euribor.csv", index=False)
                print(f"  euribor: {len(df)} filas → bde_euribor.csv")
                return df
        except Exception as e:  # noqa: BLE001
            print(f"  euribor {url}: {str(e)[:90]}")
    print("  euribor: DEFERRED (URLs muertas — usar portal datos.bde.es con clave, ver landscape)")
    return None


def re_date(s: str) -> bool:
    import re
    return bool(re.match(r"^\d{1,2} [A-Z]{3} \d{4}$", s))


def fetch_wwbi() -> pd.DataFrame:
    # resolver código de la prima salarial
    js = http_json("https://api.worldbank.org/v2/indicator", params=[("source", "64"), ("format", "json"), ("per_page", "400")])
    prem = [i["id"] for i in js[1] if "PREM" in i["id"] and "PB" in i["id"]]
    codes = WWBI_FIXED + prem[:2]
    print(f"  wwbi: prima resuelta -> {prem[:2]}")
    frames = []
    for code in codes:
        js = http_json(f"https://api.worldbank.org/v2/country/all/indicator/{code}",
                       params=[("source", "64"), ("format", "json"), ("per_page", "20000")])
        if len(js) < 2 or not js[1]:
            print(f"    {code}: vacío"); continue
        df = pd.DataFrame([
            {"iso3": r["countryiso3code"], "country": r["country"]["value"],
             "year": int(r["date"]), "indicator": code, "value": r["value"]}
            for r in js[1] if r["value"] is not None
        ])
        frames.append(df)
        print(f"    {code}: {len(df)} filas")
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(PROCESSED / "wwbi.csv", index=False)
    print(f"  wwbi: {len(out)} filas → wwbi.csv")
    return out


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    fetch_euribor()
    df = fetch_wwbi()
    es = df.query("iso3=='ESP' and indicator=='BI.EMP.TOTL.PB.ZS' and year==2020")["value"]
    assert len(es) and abs(float(es.iloc[0]) - 0.248) < 0.02, f"ancla WWBI ES: {es.tolist()}"
    print("SMOKE OK — ancla WWBI España 2020 ≈ 24,8% verificada")
