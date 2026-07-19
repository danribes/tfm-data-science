"""Google Trends ES — interés de búsqueda de compra de vivienda (Tier 2).

CAVEAT DECLARADO (por eso es Tier 2, no Tier 1): Google Trends devuelve un
índice 0-100 normalizado POR PETICIÓN sobre una muestra — dos descargas en
fechas distintas no son idénticas. Tratamiento igual que el salario provisional:
vintage congelado en CSV con fecha de descarga; cualquier uso predictivo cita
la añada. Sin API oficial; pytrends (no oficial) con rate-limit.

    python3 connectors/tendencias.py
"""
from __future__ import annotations

import datetime as dt
import sys
import time

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))

import pandas as pd
from pytrends.request import TrendReq

from base import PROCESSED

KEYWORDS = ["comprar piso", "hipoteca", "alquiler"]


def main() -> None:
    # retries de pytrends rotos con urllib3 v2 (method_whitelist): bucle manual.
    # Google solo da resolución MENSUAL en rangos <=5 años: se descargan ventanas
    # de 5 años con 12 meses de solape y se re-escala cada ventana a la anterior
    # por la mediana del ratio en el solape (encadenado; declarado en el CSV).
    pt = TrendReq(hl="es-ES", tz=60)
    ventanas = [("2004-01-01", "2009-01-01"), ("2008-01-01", "2013-01-01"),
                ("2012-01-01", "2017-01-01"), ("2016-01-01", "2021-01-01"),
                ("2020-01-01", "2025-01-01"), ("2024-01-01", "2026-07-01")]
    frames = []
    for kw in KEYWORDS:
        serie = None
        for v0, v1 in ventanas:
            d = None
            for intento in range(3):
                try:
                    pt.build_payload([kw], geo="ES", timeframe=f"{v0} {v1}")
                    d = pt.interest_over_time()
                    break
                except Exception:
                    if intento == 2:
                        raise
                    time.sleep(20 * (intento + 1))
            if d is None or d.empty:
                raise RuntimeError(f"Trends vacío para {kw!r} en {v0}–{v1}")
            s = d[~d.get("isPartial", False)][kw].astype(float)
            if serie is None:
                serie = s
            else:
                solape = serie.index.intersection(s.index)
                comun = (serie.loc[solape] / s.loc[solape]).replace([float("inf")], pd.NA).dropna()
                factor = comun.median() if len(comun) else 1.0
                serie = pd.concat([serie, (s * factor)[~s.index.isin(serie.index)]])
            time.sleep(8)
        d = serie.rename("indice").reset_index()
        d["keyword"] = kw
        frames.append(d)
    out = pd.concat(frames, ignore_index=True)
    out["fecha_descarga"] = dt.date.today().isoformat()
    out = out.rename(columns={"date": "mes"})
    assert out.keyword.nunique() == len(KEYWORDS)
    out.to_csv(PROCESSED / "gtrends_vivienda.csv", index=False)
    print(f"SMOKE trends: {len(out)} filas mensuales, {out.mes.min()}–{out.mes.max()}, "
          f"{out.keyword.nunique()} términos → gtrends_vivienda.csv")


if __name__ == "__main__":
    main()
