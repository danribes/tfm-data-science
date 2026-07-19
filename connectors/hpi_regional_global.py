"""Panel mundial de índices de precios de vivienda REGIONALES (Ruta 1 DL).

Tres fuentes abiertas, ~1.300 series subnacionales con ciclos completos:
- FHFA (EE. UU.): índice trimestral por estado (1975–) y por área metro
  (1975–, NSA). Incluye el boom-bust 2000-2012 completo.
- Zillow ZHVI (EE. UU.): valor medio mensual por metro (2000–), suavizado SA.
- UK Land Registry: precio medio mensual por región/autoridad local (1968–).

Uso declarado: corpus de ENTRENAMIENTO para el modelo global DL (T1 Ruta 1).
Las series españolas NUNCA entran en el entrenamiento; el corte temporal de
entrenamiento es 2019Q3 (antes del primer origen de validación) para que el
modelo no vea NADA posterior a los orígenes desde ninguna geografía.

    python3 connectors/hpi_regional_global.py
"""
from __future__ import annotations

import io
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))

import pandas as pd
import requests

from base import PROCESSED, UA, save_raw_bytes

URLS = {
    "fhfa_metro": "https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_metro.csv",
    "fhfa_state": "https://www.fhfa.gov/hpi/download/quarterly_datasets/hpi_at_state.csv",
    "zillow_metro": "https://files.zillowstatic.com/research/public_csvs/zhvi/Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
    "uk_avg": "http://publicdata.landregistry.gov.uk/market-trend-data/house-price-index-data/Average-prices-2025-05.csv",
}


def _get(key: str) -> bytes:
    r = requests.get(URLS[key], headers=UA, timeout=300)
    r.raise_for_status()
    save_raw_bytes(f"{key}.csv", r.content, URLS[key])
    return r.content


def main() -> None:
    frames = []

    d = pd.read_csv(io.BytesIO(_get("fhfa_metro")), header=None,
                    names=["nombre", "cbsa", "anyo", "quarter", "idx", "idx2"], na_values=["-"])
    d["valor"] = pd.to_numeric(d.idx, errors="coerce")
    d = d.dropna(subset=["valor"])
    frames.append(d.assign(fuente="fhfa_metro", serie="US_M_" + d.cbsa.astype(str))[
        ["fuente", "serie", "anyo", "quarter", "valor"]])

    d = pd.read_csv(io.BytesIO(_get("fhfa_state")), header=None,
                    names=["estado", "anyo", "quarter", "valor"])
    frames.append(d.assign(fuente="fhfa_state", serie="US_S_" + d.estado)[
        ["fuente", "serie", "anyo", "quarter", "valor"]])

    d = pd.read_csv(io.BytesIO(_get("zillow_metro")))
    meses = [c for c in d.columns if c[:2] == "20"]
    z = d.melt(id_vars=["RegionID"], value_vars=meses, var_name="mes", value_name="valor").dropna()
    z["mes"] = pd.to_datetime(z.mes)
    z["anyo"], z["quarter"] = z.mes.dt.year, z.mes.dt.quarter
    z = z.groupby(["RegionID", "anyo", "quarter"], as_index=False).valor.mean()
    frames.append(z.assign(fuente="zillow", serie="US_Z_" + z.RegionID.astype(str))[
        ["fuente", "serie", "anyo", "quarter", "valor"]])

    d = pd.read_csv(io.BytesIO(_get("uk_avg")))
    d["fecha"] = pd.to_datetime(d.Date)
    d["anyo"], d["quarter"] = d.fecha.dt.year, d.fecha.dt.quarter
    u = d.groupby(["Area_Code", "anyo", "quarter"], as_index=False).Average_Price.mean()
    frames.append(u.assign(fuente="uk", serie="UK_" + u.Area_Code,
                           valor=u.Average_Price)[["fuente", "serie", "anyo", "quarter", "valor"]])

    out = pd.concat(frames, ignore_index=True)
    out = out[out.valor > 0]
    assert out.duplicated(subset=["serie", "anyo", "quarter"]).sum() == 0
    largo = out.groupby("serie").size()
    out = out[out.serie.isin(largo[largo >= 40].index)]  # ≥10 años por serie
    out.to_csv(PROCESSED / "hpi_regional_global.csv", index=False)
    print(f"SMOKE panel global: {out.serie.nunique()} series "
          f"({dict(out.groupby('fuente').serie.nunique())}), {out.anyo.min()}–{out.anyo.max()}, "
          f"{len(out):,} filas → hpi_regional_global.csv")


if __name__ == "__main__":
    main()
