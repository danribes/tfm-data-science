"""Encuesta de Préstamos Bancarios — criterios de crédito vivienda ES (Tier 2).

La serie histórica del BdE (pb_1_1.csv) muere en DIC 2021 (cambio de sistema de
publicación); la continuación viva y estable es el ECB Data Portal, dataset BLS:
ES, criterios de aprobación de préstamos a hogares para adquisición de vivienda,
porcentaje neto de endurecimiento, trimestral 2003Q1–. Positivo = se endurece.

    python3 connectors/credito.py
"""
from __future__ import annotations

import io
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))

import pandas as pd
import requests

from base import PROCESSED, UA, save_raw_bytes

KEY = "BLS.Q.ES.ALL.Z.H.H.B3.ST.S.FNET"
URL = f"https://data-api.ecb.europa.eu/service/data/BLS/{KEY.split('.', 1)[1]}?format=csvdata"


def main() -> None:
    r = requests.get(URL, headers=UA, timeout=120)
    r.raise_for_status()
    save_raw_bytes("ecb_bls_es_vivienda.csv", r.content, URL)
    d = pd.read_csv(io.BytesIO(r.content))
    d = d[["TIME_PERIOD", "OBS_VALUE"]].rename(columns={"TIME_PERIOD": "periodo", "OBS_VALUE": "pct_neto_endurecimiento"})
    d[["anyo", "quarter"]] = d.periodo.str.split("-Q", expand=True).astype(int)
    d = d.drop(columns=["periodo"]).sort_values(["anyo", "quarter"])
    assert len(d) > 80 and d.anyo.min() <= 2003
    d.to_csv(PROCESSED / "bls_criterios_vivienda.csv", index=False)
    print(f"SMOKE BLS: {len(d)} trimestres {d.anyo.min()}Q{d.quarter.iloc[0]}–{d.anyo.max()}Q{d.quarter.iloc[-1]}; "
          f"último %neto = {d.pct_neto_endurecimiento.iloc[-1]:+.0f} → bls_criterios_vivienda.csv")


if __name__ == "__main__":
    main()
