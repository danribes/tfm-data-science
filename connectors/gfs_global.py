"""IMF GFS global: gasto por función (COFOG) + ingresos por tipo (WoRLD).

Cierra el hueco declarado desde la primera expansión ("GFS-COFOG global vía
IMF pendiente") y añade el lado de INGRESOS que faltaba a escala mundial.
API nueva de datos del FMI (api.imf.org, SDMX 2.1, sin clave; verificada
2026-07-19):

- GFS_COFOG (IMF.STA): gasto de las AAPP por las 10 funciones COFOG, % PIB,
  ~195 países, anual. Clave: {pais}.S13.G2MF.{GF0X_T}.POGDP_PT.A
- WORLD (IMF.FAD, WoRLD): ingresos desde 1980 por tipo — total, impuestos,
  renta (personas/sociedades), propiedad, bienes y servicios (ventas,
  especiales), comercio, cotizaciones sociales, donaciones, no tributarios.
  Clave: {pais}.{IND}_POGDP_PT_R.POGDP_PT.A

    python3 connectors/gfs_global.py
"""
from __future__ import annotations

import re
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))

import pandas as pd
import requests

from base import PROCESSED, UA

API = "https://api.imf.org/external/sdmx/2.1/data"

COFOG = {f"GF{i:02d}_T": f"GF{i:02d}" for i in range(1, 11)}

WORLD_IND = {
    "G1": "rev_total", "G11": "tax_total", "G111": "tax_renta",
    "G1111": "tax_renta_personas", "G1112": "tax_renta_sociedades",
    "G113": "tax_propiedad", "G114": "tax_bienes_servicios",
    "G11412": "tax_ventas", "G1142": "tax_especiales", "G115": "tax_comercio",
    "G121": "cotizaciones_ss", "G13": "donaciones", "G14": "otros_ingresos",
    # NONTAX publicado sin datos en la API (verificado): el residuo no
    # tributario se deriva como rev_total − tax_total − cotizaciones − donaciones
}


def _parse(xml: str) -> list[tuple[str, int, float]]:
    out = []
    for serie in re.split(r"<Series ", xml)[1:]:
        pais = re.search(r'COUNTRY="([A-Z0-9]+)"', serie)
        if not pais:
            continue
        for obs in re.finditer(r'<Obs TIME_PERIOD="(\d{4})" OBS_VALUE="([-\d.eE]+)"', serie):
            out.append((pais.group(1), int(obs.group(1)), float(obs.group(2))))
    return out


def _pull(url: str) -> str:
    r = requests.get(url, headers=UA, timeout=180)
    r.raise_for_status()
    return r.text


def fetch_cofog() -> None:
    rows = []
    for ind, gf in COFOG.items():
        xml = _pull(f"{API}/GFS_COFOG/.S13.G2MF.{ind}.POGDP_PT.A")
        for pais, anyo, v in _parse(xml):
            rows.append({"iso3": pais, "funcion": gf, "year": anyo, "pct_gdp": v})
        print(f"  {gf}: {len({r['iso3'] for r in rows if r['funcion'] == gf})} países")
    df = pd.DataFrame(rows)
    # ~88 reportadores con %PIB: coincide con el rango 60-90 previsto en el PLAN
    assert df.iso3.nunique() >= 80 and df.funcion.nunique() == 10
    assert df.duplicated(subset=["iso3", "funcion", "year"]).sum() == 0
    df.to_csv(PROCESSED / "gfs_cofog_global.csv", index=False)
    es24 = df.query("iso3=='ESP' and year==2024").set_index("funcion").pct_gdp
    print(f"SMOKE GFS-COFOG: {df.iso3.nunique()} países {df.year.min()}–{df.year.max()}; "
          f"ESP 2024 salud {es24.get('GF07', float('nan')):.1f} / protección social "
          f"{es24.get('GF10', float('nan')):.1f} %PIB → gfs_cofog_global.csv")


def fetch_world() -> None:
    rows = []
    for ind, nombre in WORLD_IND.items():
        xml = _pull(f"{API}/WORLD/.{ind}_POGDP_PT_R.POGDP_PT.A")
        for pais, anyo, v in _parse(xml):
            rows.append({"iso3": pais, "categoria": nombre, "year": anyo, "pct_gdp": v})
    df = pd.DataFrame(rows)
    assert df.iso3.nunique() >= 150 and df.categoria.nunique() == len(WORLD_IND)
    assert df.duplicated(subset=["iso3", "categoria", "year"]).sum() == 0
    df.to_csv(PROCESSED / "world_revenue_global.csv", index=False)
    es = df.query("iso3=='ESP' and year==2023").set_index("categoria").pct_gdp
    print(f"SMOKE WoRLD: {df.iso3.nunique()} países {df.year.min()}–{df.year.max()}; "
          f"ESP 2023 total {es.get('rev_total', float('nan')):.1f} = impuestos "
          f"{es.get('tax_total', float('nan')):.1f} + cotizaciones {es.get('cotizaciones_ss', float('nan')):.1f} "
          f"+ resto → world_revenue_global.csv")


OECD_RS = ("https://sdmx.oecd.org/public/rest/data/OECD.CTP.TPS,DSD_REV_COMP_GLOBAL@DF_RSGLOBAL,/"
           ".TAX_REV.S13.T_1000+T_2000+T_3000+T_4000+T_5000+T_6000._T.PT_B1GQ.A?format=csvfile")
RS_HEADS = {"T_1000": "renta", "T_2000": "cotizaciones", "T_3000": "nomina",
            "T_4000": "propiedad", "T_5000": "bienes_servicios", "T_6000": "otros"}


def fetch_oecd_taxes() -> None:
    """OECD Global Revenue Statistics: 6 cabeceras de impuestos, fuente
    INDEPENDIENTE de WoRLD para la reconciliación (clasificación OCDE, no GFS)."""
    r = requests.get(OECD_RS, headers=UA, timeout=300)
    r.raise_for_status()
    import io
    d = pd.read_csv(io.BytesIO(r.content))
    d = d.rename(columns={"REF_AREA": "iso3", "TIME_PERIOD": "year", "OBS_VALUE": "pct_gdp"})
    d["cabecera"] = d.STANDARD_REVENUE.map(RS_HEADS)
    out = d[["iso3", "cabecera", "year", "pct_gdp"]].dropna()
    assert out.iso3.nunique() >= 130
    out.to_csv(PROCESSED / "oecd_tax_global.csv", index=False)
    es = out.query("iso3=='ESP' and year==2022").set_index("cabecera").pct_gdp
    print(f"SMOKE OCDE-RS: {out.iso3.nunique()} países {out.year.min()}–{out.year.max()}; "
          f"ESP 2022 suma cabeceras = {es.sum():.1f} %PIB → oecd_tax_global.csv")


def fetch_eurostat_rev_detail() -> None:
    """Eurostat gov_10a_main: componentes de ingresos que faltaban en
    gov_revenue_deficit (D91, D4, D7, ventas P11+P12+P131, subvenciones D3REC)."""
    from eurostat_multi import run_one

    frames = []
    for item in ["D91REC", "D4REC", "D7REC", "P11_P12_P131", "D39REC", "D2REC", "D5REC", "D61REC", "TR"]:
        d = run_one("gov_10a_main", [("unit", "PC_GDP"), ("sector", "S13"), ("na_item", item)],
                    f"rev_{item}")
        d["na_item"] = item
        frames.append(d)
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(PROCESSED / "gov_revenue_detail.csv", index=False)
    print(f"SMOKE ingresos UE: {out.na_item.nunique()} componentes, "
          f"{out.geo.nunique()} geos → gov_revenue_detail.csv")


if __name__ == "__main__":
    fetch_cofog()
    fetch_world()
    fetch_oecd_taxes()
    fetch_eurostat_rev_detail()
