"""Conector de demanda de vivienda (INE wstempus): 3 capas nuevas del Tier 1.

Descubrimiento 2026-07-19 (ids verificados en vivo):
- ETDP tabla 6149  — compraventas de viviendas, MENSUAL por CCAA (2007M01–),
  series "«CCAA». Compraventa. Total viviendas. Número."
- HPT  tabla 76316 — hipotecas constituidas, MENSUAL por CCAA (base nueva),
  series "Viviendas. «CCAA». Número de hipotecas." (nacional invierte el orden:
  "Viviendas. Número de hipotecas. Total Nacional.").
- ECP  tabla 56940 — población residente TRIMESTRAL por CCAA desde 1971,
  series "Total. Todas las edades. «CCAA». Población." (FK 19..22 = Q1..Q4;
  fechas de referencia 1-ene/1-abr/1-jul/1-oct).

Volumen (compraventas, hipotecas) lidera precio en la literatura ES; Δpob
trimestral codifica el shock de demanda 2024-25 que ningún modelo captó.
Cualquier uso predictivo pasa por el protocolo: validación vs drift, nunca
sobre el test gastado.

    python3 connectors/demanda.py
"""
from __future__ import annotations

import re
import sys
import time

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))

import pandas as pd

from base import PROCESSED, http_json
from ine import WS, list_series

# FK_Periodo del INE: mensual 1..12; ECP trimestral 19..22
ECP_Q = {19: 1, 20: 2, 21: 3, 22: 4}

# el nombre de la serie mezcla territorios con otros ejes (sexo, provincias):
# filtro por lista cerrada = mismo criterio que el smoke exacto de gold.py
TERRITORIOS = {
    "Nacional", "Andalucía", "Aragón", "Asturias, Principado de", "Balears, Illes",
    "Canarias", "Cantabria", "Castilla - La Mancha", "Castilla y León", "Cataluña",
    "Comunitat Valenciana", "Extremadura", "Galicia", "Madrid, Comunidad de",
    "Murcia, Región de", "Navarra, Comunidad Foral de", "País Vasco", "Rioja, La",
    "Ceuta", "Melilla",
}

PULLS = {
    # clave: (tabla, regex con grupo ccaa, nult, salida)
    "compraventas": (6149, r"^(?P<ccaa>[^.]+)\. Compraventa\. Total viviendas\. Número",
                     240, "ine_compraventas_ccaa"),
    "hipotecas": (76316, r"^Viviendas\. (?:(?P<ccaa>[^.]+)\. Número de hipotecas|Número de hipotecas\. (?P<nac>Total Nacional))\.",
                  300, "ine_hipotecas_ccaa"),
    "poblacion": (56940, r"^Total(?: Nacional)?\. Todas las edades\. (?P<ccaa>[^.]+)\. Población",
                  230, "ine_poblacion_q_ccaa"),
}


def fetch(key: str) -> pd.DataFrame:
    tabla, pat, nult, name = PULLS[key]
    rows = []
    for s in list_series(tabla):
        m = re.match(pat, s.get("Nombre", ""))
        if not m:
            continue
        ccaa = (m.groupdict().get("ccaa") or "").strip()
        if ccaa in ("", "Total", "Total Nacional"):
            ccaa = "Nacional"
        js = http_json(f"{WS}/DATOS_SERIE/{s['COD']}", params=[("nult", str(nult))])
        for d in js.get("Data", []):
            rows.append({"ccaa": ccaa, "anyo": d.get("Anyo"), "periodo": d.get("FK_Periodo"),
                         "valor": d.get("Valor")})
        time.sleep(0.15)
    df = pd.DataFrame(rows).dropna(subset=["valor"])
    if key == "poblacion":
        df["quarter"] = df.periodo.map(ECP_Q)
        df = df.dropna(subset=["quarter"]).astype({"quarter": int}).drop(columns=["periodo"])
        pk = ["ccaa", "anyo", "quarter"]
    else:
        df = df[df.periodo.between(1, 12)].rename(columns={"periodo": "mes"})
        pk = ["ccaa", "anyo", "mes"]
    df = df[df.ccaa.isin(TERRITORIOS)].drop_duplicates(subset=pk).sort_values(pk)
    faltan = TERRITORIOS - set(df.ccaa)
    # ETDP no publica serie mensual propia para Asturias con nombre corto en
    # todas las vistas; se exige el panel completo salvo justificación impresa
    assert not faltan, f"{key}: faltan territorios {sorted(faltan)}"
    dest = PROCESSED / f"{name}.csv"
    df.to_csv(dest, index=False)
    nac = df[df.ccaa == "Nacional"]
    print(f"  {key}: {df.ccaa.nunique()} territorios, {df.anyo.min()}–{df.anyo.max()}, "
          f"{len(df)} filas (Nacional última: {nac.valor.iloc[-1]:,.0f}) → {dest.name}")
    return df


def main() -> None:
    for key in PULLS:
        fetch(key)


if __name__ == "__main__":
    main()
