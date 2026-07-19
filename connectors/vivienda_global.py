"""Panel internacional de vivienda y suelo (BIS + OECD + Eurostat).

Endpoints verificados en vivo 2026-07-19:
- BIS WS_SPP (stats.bis.org API v2): precios residenciales, 61 áreas,
  trimestral; nominal (N) y real (R), índice 2010=100 (serie 628). Núcleo
  avanzado desde los años 70 (ES real desde 1971; US desde 1927).
- OECD DSD_AN_HOUSE_PRICES@DF_HOUSE_PRICES (sdmx.oecd.org): 50 áreas,
  trimestral: HPI nominal, RHP real, HPI_YDH (precio/renta disponible = la
  medida comparable de asequibilidad) y HPI_RPI (precio/alquiler), 2015=100.
- OECD DSD_LAND@DF_LAND_COVER (ENV.EPI): superficie artificial LC_SUR_ART
  (km², épocas 2000–2022, ESA CCI) — el proxy de "suelo consumido"; el suelo
  urbanizable LEGAL no existe armonizado internacionalmente (ver
  docs/demanda_suelo.md §2: SIU es rareza española).
- Eurostat lan_lcv_ovw (LUCAS): % de suelo artificial por país, oleadas
  2009–2022 — proxy encuesta, complementa el satélite.

    python3 connectors/vivienda_global.py
"""
from __future__ import annotations

import io
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))

import pandas as pd
import requests

from base import PROCESSED, UA, save_raw_bytes
from eurostat_multi import run_one

BIS = "https://stats.bis.org/api/v2/data/dataflow/BIS/WS_SPP/1.0/Q..{val}.628?format=csv"
OECD = "https://sdmx.oecd.org/public/rest/data/{flow},/{key}?format=csvfile"


def _get(url: str, raw_name: str) -> pd.DataFrame:
    r = requests.get(url, headers=UA, timeout=300)
    r.raise_for_status()
    save_raw_bytes(raw_name, r.content, url)
    return pd.read_csv(io.BytesIO(r.content))


def fetch_bis() -> None:
    frames = []
    for val, name in [("N", "nominal"), ("R", "real")]:
        d = _get(BIS.format(val=val), f"bis_spp_{val}.csv")
        d = d.rename(columns={"REF_AREA": "area", "TIME_PERIOD": "periodo", "OBS_VALUE": "indice"})
        d["serie"] = name
        frames.append(d[["area", "periodo", "serie", "indice"]])
    out = pd.concat(frames, ignore_index=True).dropna(subset=["indice"])
    out[["anyo", "quarter"]] = out.periodo.str.split("-Q", expand=True).astype(int)
    out = out.drop(columns=["periodo"])
    assert out.area.nunique() >= 55 and out.anyo.min() < 1975
    out.to_csv(PROCESSED / "bis_precios_vivienda.csv", index=False)
    es = out.query("area=='ES' and serie=='real'")
    print(f"SMOKE BIS: {out.area.nunique()} áreas, {out.anyo.min()}–{out.anyo.max()}; "
          f"ES real {es.anyo.min()}– ({len(es)} trimestres) → bis_precios_vivienda.csv")


def fetch_oecd_precios() -> None:
    d = _get(OECD.format(flow="OECD.ECO.MPD,DSD_AN_HOUSE_PRICES@DF_HOUSE_PRICES", key="all"),
             "oecd_house_prices.csv")
    d = d[d.MEASURE.isin(["HPI", "RHP", "HPI_YDH", "HPI_RPI"]) & d.TIME_PERIOD.str.contains("-Q")]
    d = d.rename(columns={"REF_AREA": "iso3", "MEASURE": "medida", "OBS_VALUE": "valor"})
    d[["anyo", "quarter"]] = d.TIME_PERIOD.str.split("-Q", expand=True).astype(int)
    out = d[["iso3", "medida", "anyo", "quarter", "valor"]].dropna()
    assert out.iso3.nunique() >= 45 and set(out.medida) >= {"HPI", "HPI_YDH"}
    out.to_csv(PROCESSED / "oecd_precios_vivienda.csv", index=False)
    pti = out.query("iso3=='ESP' and medida=='HPI_YDH'").sort_values(["anyo", "quarter"])
    print(f"SMOKE OECD precios: {out.iso3.nunique()} países {out.anyo.min()}–{out.anyo.max()}; "
          f"ESP precio/renta último = {pti.valor.iloc[-1]:.1f} (2015=100) → oecd_precios_vivienda.csv")


def fetch_oecd_suelo() -> None:
    d = _get(OECD.format(flow="OECD.ENV.EPI,DSD_LAND@DF_LAND_COVER", key="._O.LC_SUR_ART+LCC_SUR_ART_GAIN."),
             "oecd_land_cover.csv")
    d = d.rename(columns={"REF_AREA": "iso3", "MEASURE": "medida", "TIME_PERIOD": "anyo", "OBS_VALUE": "valor"})
    d = d[d.UNIT_MEASURE == "KM2"]  # el comodín final trae también % del total
    d = d[d.iso3.str.fullmatch(r"[A-Z]{3}")]  # países (el flujo trae también agregados/regiones)
    out = d[["iso3", "medida", "anyo", "valor"]].dropna()
    assert out.iso3.nunique() >= 50
    out.to_csv(PROCESSED / "oecd_suelo_artificial.csv", index=False)
    esp = out.query("iso3=='ESP' and medida=='LC_SUR_ART'").sort_values("anyo")
    print(f"SMOKE OECD suelo: {out.iso3.nunique()} países, {out.anyo.min()}–{out.anyo.max()}; "
          f"ESP artificial {esp.valor.iloc[0]:,.0f}→{esp.valor.iloc[-1]:,.0f} km² → oecd_suelo_artificial.csv")


def fetch_lucas() -> None:
    d = run_one("lan_lcv_ovw", [("landcover", "A00"), ("unit", "PC")], "lucas_artificial")
    print(f"SMOKE LUCAS: {d.geo.nunique()} geos, oleadas {sorted(d.time.unique())} → lucas_artificial.csv")


def main() -> None:
    fetch_bis()
    fetch_oecd_precios()
    fetch_oecd_suelo()
    fetch_lucas()


if __name__ == "__main__":
    main()
