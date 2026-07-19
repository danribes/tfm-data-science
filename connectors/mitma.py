"""Conector MITMA — licencias municipales de obra por CCAA (BoletinOnline v1).

Pata regional del driver de oferta (Revisión 1 de la Entrega 4). Las series de
visados de aparejadores NO están en BoletinOnline2 (comprobado 2026-07-19); lo
que sí publica el Boletín histórico (v1) son las LICENCIAS municipales por CCAA:
tabla "N.º de viviendas según tipo de obra" (sufijo XX30), anual 2000–2022.
CAVEAT declarado: las licencias publican con ~2 años de retraso → sirven para
modelización histórica regional (giros, features de panel), NO como señal viva;
la señal viva sigue siendo Eurostat sts_cobp_q (nacional, hasta 2026Q1).

    python3 -m mitma            (desde connectors/)
    python3 connectors/mitma.py
"""
from __future__ import annotations

import re
import sys

import pandas as pd
import requests
import xlrd

from base import PROCESSED, RAW, UA, save_raw_bytes

BASE = "https://apps.fomento.gob.es/BoletinOnline/sedal/{xid}.XLS"
IDS = [f"1002{i:02d}30" for i in range(1, 20)]  # 19 territorios, tabla viviendas

# nombre del título MITMA → nombre INE del panel gold
INE = {
    "ANDALUCÍA": "Andalucía", "ARAGÓN": "Aragón", "ASTURIAS, PRINCIPADO DE": "Asturias, Principado de",
    "BALEARS, ILLES": "Balears, Illes", "CANARIAS": "Canarias", "CANTABRIA": "Cantabria",
    "CASTILLA-LA MANCHA": "Castilla - La Mancha", "CASTILLA Y LEÓN": "Castilla y León",
    "CATALUÑA": "Cataluña", "COMUNIDAD VALENCIANA": "Comunitat Valenciana",
    "EXTREMADURA": "Extremadura", "GALICIA": "Galicia", "MADRID, COMUNIDAD DE": "Madrid, Comunidad de",
    "MURCIA, REGIÓN DE": "Murcia, Región de", "NAVARRA, COMUNIDAD FORAL DE": "Navarra, Comunidad Foral de",
    "PAÍS VASCO": "País Vasco", "RIOJA, LA": "Rioja, La",
    "CEUTA, CIUDAD AUTÓNOMA DE": "Ceuta", "MELILLA, CIUDAD AUTÓNOMA DE": "Melilla",
    # variantes de título del Boletín ("HISTÓRICA DEL/DE LA ...")
    "PRINCIPADO DE ASTURIAS": "Asturias, Principado de", "ILLES BALEARS": "Balears, Illes",
    "L PRINCIPADO DE ASTURIAS": "Asturias, Principado de",
    "COMUNIDAD DE MADRID": "Madrid, Comunidad de", "REGIÓN DE MURCIA": "Murcia, Región de",
    "LA RIOJA": "Rioja, La", "RIOJA": "Rioja, La",
    "COMUNIDAD FORAL DE NAVARRA": "Navarra, Comunidad Foral de",
    "CIUDAD AUTÓNOMA DE CEUTA": "Ceuta", "CIUDAD AUTÓNOMA DE MELILLA": "Melilla",
    "CIUDAD DE CEUTA": "Ceuta", "CIUDAD DE MELILLA": "Melilla",
    "CASTILLA-LEÓN": "Castilla y León", "CASTILLA LA MANCHA": "Castilla - La Mancha",
    "C. VALENCIANA": "Comunitat Valenciana", "COMUNITAT VALENCIANA": "Comunitat Valenciana",
    "EUSKADI": "País Vasco", "CEUTA": "Ceuta", "MELILLA": "Melilla",
    "C. FORAL DE NAVARRA": "Navarra, Comunidad Foral de", "NAVARRA": "Navarra, Comunidad Foral de",
    "C. DE MADRID": "Madrid, Comunidad de", "R. DE MURCIA": "Murcia, Región de",
}


def parse_tabla(content: bytes, xid: str) -> pd.DataFrame:
    wb = xlrd.open_workbook(file_contents=content)
    sh = wb.sheet_by_index(0)
    titulo = str(sh.cell_value(1, 0)).upper()
    # el título termina en el nombre del territorio con variantes ("DE X",
    # "DEL PRINCIPADO DE X"...): se busca el sufijo más largo del mapa
    limpio = re.sub(r"\s+", " ", titulo).strip().rstrip(". ")
    ccaa = None
    for clave in sorted(INE, key=len, reverse=True):
        if limpio.endswith(clave):
            ccaa = INE[clave]
            break
    assert ccaa, f"{xid}: CCAA no mapeada en título: {limpio!r}"
    rows = []
    for i in range(sh.nrows):
        y = sh.cell_value(i, 0)
        if isinstance(y, float) and 1990 < y < 2035 and sh.cell_value(i, 1) == "":
            rows.append({
                "ccaa": ccaa, "anyo": int(y),
                "viv_nueva": sh.cell_value(i, 2) or 0.0,
                "viv_rehab": sh.cell_value(i, 7) or 0.0,
                "viv_demolicion": sh.cell_value(i, 8) or 0.0,
                "viv_total": sh.cell_value(i, 9) or 0.0,
            })
    assert len(rows) >= 15, f"{xid} ({ccaa}): solo {len(rows)} filas anuales"
    df = pd.DataFrame(rows)
    for c in ["viv_nueva", "viv_rehab", "viv_demolicion", "viv_total"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)  # celdas '-' en Ceuta/Melilla
    return df


def main() -> None:
    frames = []
    for xid in IDS:
        url = BASE.format(xid=xid)
        r = requests.get(url, headers=UA, timeout=90)
        r.raise_for_status()
        save_raw_bytes(f"mitma_licencias_{xid}.xls", r.content, url)
        df = parse_tabla(r.content, xid)
        frames.append(df)
        print(f"  {xid} → {df.ccaa.iloc[0]}: {df.anyo.min()}–{df.anyo.max()} "
              f"(nueva {df.viv_nueva.sum():.0f} viviendas acumuladas)")
    out = pd.concat(frames, ignore_index=True).sort_values(["ccaa", "anyo"])
    assert out.duplicated(subset=["ccaa", "anyo"]).sum() == 0, "PK duplicada"
    assert out.ccaa.nunique() == 19, f"esperados 19 territorios, hay {out.ccaa.nunique()}"
    out.to_csv(PROCESSED / "mitma_licencias_ccaa.csv", index=False)
    tot06 = out.query("anyo==2006").viv_nueva.sum()
    tot13 = out.query("anyo==2013").viv_nueva.sum()
    print(f"SMOKE: {out.ccaa.nunique()} CCAA; nueva planta nacional 2006={tot06:,.0f} "
          f"vs 2013={tot13:,.0f} (colapso x{tot06 / max(tot13, 1):.0f}) → mitma_licencias_ccaa.csv")


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    main()
