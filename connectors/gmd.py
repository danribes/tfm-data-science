"""Conector Global Macro Database (Müller et al.) — fiscal histórico, 243 países.

Fichero FINAL combinado (ruta descubierta en el loader del paquete oficial):
  {S3}/distribute/GMD_{version}.dta   (versions.csv → última = 2026_06)
Nota: los chainlinked_*.dta de GitHub son INSUMOS del empalme (2000-2023, 48
países) — no confundir (el smoke test lo detectó).
Cubre 1900–1995 para el prólogo (T2.0) y la comparación siglo XX vs XXI.
"""
from __future__ import annotations

import sys

import pandas as pd
import requests

from base import PROCESSED, RAW, UA

S3 = "https://gmd-releases.s3.ap-southeast-2.amazonaws.com/data"
VERSION = "2026_06"

KEEP = {
    "govexp_GDP": "exp_gdp",
    "govrev_GDP": "rev_gdp",
    "govtax_GDP": "tax_gdp",
    "govdebt_GDP": "debt_gdp",
    "govdef_GDP": "deficit_gdp",
}


def fetch() -> pd.DataFrame:
    dest = RAW / f"GMD_{VERSION}.dta"
    if not dest.exists():
        r = requests.get(f"{S3}/distribute/GMD_{VERSION}.dta", headers=UA, timeout=600)
        r.raise_for_status()
        assert len(r.content) > 5_000_000, f"GMD sospechosamente pequeño: {len(r.content)}"
        dest.write_bytes(r.content)
        print(f"  descargado GMD_{VERSION}.dta ({len(r.content)//1024//1024} MB)")
    df = pd.read_stata(dest, convert_categoricals=False)
    cols = {c: c for c in df.columns}
    iso = "ISO3" if "ISO3" in cols else ("iso3" if "iso3" in cols else "countrycode")
    keep = {k: v for k, v in KEEP.items() if k in cols}
    assert len(keep) >= 4, f"columnas fiscales no encontradas; hay: {[c for c in df.columns if 'gov' in c.lower()][:10]}"
    sub = df[[iso, "year"] + list(keep)].rename(columns={iso: "iso3", **keep})
    long = sub.melt(id_vars=["iso3", "year"], var_name="variable", value_name="value").dropna(subset=["value"])
    long["year"] = long["year"].astype(int)
    long = long.drop_duplicates(subset=["iso3", "year", "variable"])
    return long


def smoke(df: pd.DataFrame) -> None:
    exp = df.query("variable=='exp_gdp'")
    pre95 = exp.query("1900 <= year < 1995")
    n_pre = pre95["iso3"].nunique()
    assert n_pre > 60, f"cobertura pre-1995 insuficiente: {n_pre}"
    es60 = exp.query("iso3=='ESP' and year==1960")["value"]
    assert len(es60) and 5 < float(es60.iloc[0]) < 35, f"ESP 1960: {es60.tolist()}"
    es23 = exp.query("iso3=='ESP' and year==2023")["value"]
    assert len(es23) and abs(float(es23.iloc[0]) - 45.4) < 5, f"ESP 2023 vs Eurostat: {es23.tolist()}"
    print(f"SMOKE GMD OK — {len(df)} filas; {n_pre} países con gasto 1900-1994; "
          f"ESP 1960={float(es60.iloc[0]):.1f} / 2023={float(es23.iloc[0]):.1f} %PIB")


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    df = fetch()
    smoke(df)
    df.to_csv(PROCESSED / "gmd_fiscal.csv", index=False)
    print("→ gmd_fiscal.csv")
