"""Indicadores de bienestar, pobreza y pobreza infantil (marco MPI/MODA).

Mapea los 7 bloques del marco bienestar↔pobreza infantil (UN/WB/UNICEF) a
series abiertas descargables, para medir cómo el dinero público se convierte
en bienestar OBJETIVO (la pregunta central del proyecto, ahora con el lado de
resultados sociales):

1. Renta/consumo:   SI.POV.DDAY ($3,00/día 2021 PPP), SI.POV.NAHC (umbral
                    nacional), SI.POV.MDIM (recuento multidimensional WB)
2. Mortalidad <5:   SH.DYN.MORT (por 1.000 nacidos vivos)
3. Privación infantil material: Eurostat ilc_peps01n edad <18 (AROPE niños;
                    la privación específica infantil UE es micro → declarada)
4. Malnutrición:    SH.STA.STNT.ZS (stunting), SH.STA.WAST.ZS (wasting)
5. Educación 2 capas: SE.SEC.CUAT.LO.ZS (adultos 25+ con ≥secundaria baja),
                    SE.PRM.UNER.ZS (niños primaria fuera de la escuela)
6. Protección social: per_allsp.cov_pop_tot (ASPIRE: % población cubierta)
7. Piso de servicios: SH.H2O.SMDW.ZS (agua gestionada de forma segura),
                    SH.STA.SMSS.ZS (saneamiento), EG.ELC.ACCS.ZS
                    (electricidad), EG.CFT.ACCS.ZS (combustibles limpios)

    python3 connectors/bienestar.py
"""
from __future__ import annotations

import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))

import pandas as pd

from base import PROCESSED, http_json

WDI = {
    "SI.POV.DDAY": "pobreza_300",
    "SI.POV.NAHC": "pobreza_nacional",
    "SI.POV.MPUN": "pobreza_multidim",  # MPI UNDP&OPHI (SI.POV.MDIM está archivada)
    "SH.DYN.MORT": "mortalidad_u5",
    "SH.STA.STNT.ZS": "stunting",
    "SH.STA.WAST.ZS": "wasting",
    "SE.SEC.CUAT.LO.ZS": "adultos_secundaria",
    "SE.PRM.UNER.ZS": "ninos_sin_escuela",
    "per_allsp.cov_pop_tot": "cobertura_proteccion",
    "SH.H2O.SMDW.ZS": "agua_segura",
    "SH.STA.SMSS.ZS": "saneamiento_seguro",
    "EG.ELC.ACCS.ZS": "electricidad",
    "EG.CFT.ACCS.ZS": "combustible_limpio",
}


def fetch_wdi_bienestar() -> None:
    frames = []
    for code, vn in WDI.items():
        js = http_json(f"https://api.worldbank.org/v2/country/all/indicator/{code}",
                       params=[("format", "json"), ("per_page", "20000"), ("date", "2000:2024")],
                       timeout=240)
        if len(js) > 1 and js[1]:
            frames.append(pd.DataFrame([
                {"iso3": r["countryiso3code"], "year": int(r["date"]), "variable": vn, "value": r["value"]}
                for r in js[1] if r["value"] is not None and r["countryiso3code"]
            ]))
            print(f"  {code} → {vn}: {len(frames[-1])} filas")
        else:
            print(f"  {code} → {vn}: SIN DATOS (¿archivada?)")
    out = pd.concat(frames, ignore_index=True)
    faltan = set(WDI.values()) - set(out.variable)
    assert not faltan, f"series sin datos: {faltan}"
    out.to_csv(PROCESSED / "wdi_bienestar.csv", index=False)
    es = out[out.iso3 == "ESP"].sort_values("year").groupby("variable").value.last()
    print(f"SMOKE bienestar: {out.variable.nunique()} series, {out.iso3.nunique()} países; "
          f"ESP mortalidad<5 {es.get('mortalidad_u5'):.1f}‰, stunting {es.get('stunting', float('nan')):.1f} % "
          f"→ wdi_bienestar.csv")


def fetch_arope_ninos() -> None:
    from eurostat_multi import run_one

    d = run_one("ilc_peps01n", [("age", "Y_LT18"), ("unit", "PC"), ("sex", "T")], "arope_ninos")
    print(f"SMOKE AROPE niños: {d.geo.nunique()} geos, {d.time.min()}–{d.time.max()} → arope_ninos.csv")


if __name__ == "__main__":
    fetch_wdi_bienestar()
    fetch_arope_ninos()
