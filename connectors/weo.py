"""Conector IMF WEO datamapper — totales fiscales GLOBALES (tier mundial).

GGX_NGDP  = gasto total AAPP %PIB     GGR_NGDP = ingresos totales %PIB
GGXCNL_NGDP = déficit/superávit %PIB  GGXWDG_NGDP = deuda bruta %PIB
~190 países, 1980→ + proyecciones. API JSON libre, sin clave.
El DESGLOSE global (COFOG/económico) va aparte vía FMI GFS (subconjunto reporters).
"""
from __future__ import annotations

import sys

import pandas as pd

from base import PROCESSED, http_json, save_raw

API = "https://www.imf.org/external/datamapper/api/v1/"
INDICATORS = {
    # códigos reales del datamapper (los GGX_NGDP/GGR_NGDP clásicos devuelven vacío ahí)
    "exp": "exp_total",
    "rev": "rev_total",
    "GGXCNL_NGDP": "balance",
    "GGXWDG_NGDP": "debt",
}


def fetch() -> pd.DataFrame:
    rows = []
    for code, vn in INDICATORS.items():
        js = http_json(API + code, timeout=90)
        save_raw(f"weo_{code}", js, API + code)
        data = js.get("values", {}).get(code, {})
        for iso3, series in data.items():
            for year, val in series.items():
                if val is not None:
                    rows.append({"iso3": iso3, "year": int(year), "variable": vn, "value": float(val)})
        n = sum(1 for _ in data)
        print(f"  {code} ({vn}): {n} países")
    df = pd.DataFrame(rows)
    # solo países ISO3 (el datamapper mezcla agregados tipo ADVEC/OEMDC)
    df = df[df["iso3"].str.fullmatch(r"[A-Z]{3}")]
    pk = ["iso3", "year", "variable"]
    assert df.duplicated(subset=pk).sum() == 0, "PK duplicada"
    return df


def smoke(df: pd.DataFrame) -> None:
    es = df.query("iso3=='ESP' and year==2023")
    exp = float(es.query("variable=='exp_total'")["value"].iloc[0])
    rev = float(es.query("variable=='rev_total'")["value"].iloc[0])
    assert abs(exp - 45.4) < 2.0, f"gasto ES 2023 no cuadra con Eurostat: {exp}"
    assert abs(rev - 42.1) < 2.0, f"ingresos ES 2023 no cuadra: {rev}"
    ncountries = df.query("variable=='exp_total' and 2000<=year<=2023")["iso3"].nunique()
    assert ncountries > 150, f"cobertura global insuficiente: {ncountries}"
    print(f"SMOKE WEO OK — {len(df)} filas; ES 2023 exp={exp} rev={rev} (cruza con Eurostat ±2); "
          f"{ncountries} países con gasto total 2000-2023")


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    df = fetch()
    smoke(df)
    dest = PROCESSED / "weo_fiscal_totals.csv"
    df.to_csv(dest, index=False)
    print(f"→ {dest.name}")
