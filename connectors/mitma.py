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


VT_ID = "35102000"  # Valor tasado vivienda libre, €/m², trimestral 2010–2014 (serie del Boletín v2)
VT_CCAA = {
    "TOTAL NACIONAL": "Nacional", "Andalucía": "Andalucía", "Aragón": "Aragón",
    "Asturias (Principado de )": "Asturias, Principado de", "Balears (Illes)": "Balears, Illes",
    "Canarias": "Canarias", "Cantabria": "Cantabria", "Castilla y León": "Castilla y León",
    "Castilla-La Mancha": "Castilla - La Mancha", "Cataluña": "Cataluña",
    "Comunitat Valenciana": "Comunitat Valenciana", "Extremadura": "Extremadura",
    "Galicia": "Galicia", "Madrid (Comunidad de)": "Madrid, Comunidad de",
    "Murcia (Región de)": "Murcia, Región de", "Navarra (Comunidad Foral de)": "Navarra, Comunidad Foral de",
    "País Vasco": "País Vasco", "Rioja (La)": "Rioja, La", "Ceuta": "Ceuta", "Melilla": "Melilla",
}


def fetch_valor_tasado() -> None:
    """€/m² tasado por CCAA (ancla 2010–2014; el puente a hoy lo pone el IPV propio)."""
    url = BASE.format(xid=VT_ID).replace("BoletinOnline/", "BoletinOnline2/")
    r = requests.get(url, headers=UA, timeout=90)
    r.raise_for_status()
    save_raw_bytes(f"mitma_valor_tasado_{VT_ID}.xls", r.content, url)
    wb = xlrd.open_workbook(file_contents=r.content)
    sh = wb.sheet_by_index(0)
    rows = []
    for i in range(15, sh.nrows):
        etiqueta = str(sh.cell_value(i, 1)).strip()
        ccaa = VT_CCAA.get(etiqueta)
        if not ccaa:
            continue  # provincias (etiquetas con padding) y filas vacías
        for j in range(2, sh.ncols):
            v = sh.cell_value(i, j)
            if isinstance(v, float) and v > 0:
                q = j - 2
                rows.append({"ccaa": ccaa, "anyo": 2010 + q // 4, "quarter": q % 4 + 1,
                             "eur_m2": v})
    df = pd.DataFrame(rows)
    assert df.duplicated(subset=["ccaa", "anyo", "quarter"]).sum() == 0
    assert df.ccaa.nunique() >= 18, f"solo {df.ccaa.nunique()} territorios"
    df.to_csv(PROCESSED / "mitma_valor_tasado_ccaa.csv", index=False)
    nac14 = df.query("ccaa=='Nacional' and anyo==2014").eur_m2.mean()
    print(f"SMOKE valor tasado: {df.ccaa.nunique()} territorios, 2010–2014; "
          f"Nacional 2014 = {nac14:,.0f} €/m² → mitma_valor_tasado_ccaa.csv")


SUELO_TABLAS = {  # sección 36 del Boletín v2, trimestral 2004Q1– (verificado 2026-07-19)
    "36100500": "transacciones_n",       # número de transacciones de suelo
    "36200500": "valor_miles_eur",       # valor total (miles €)
    "36300500": "superficie_miles_m2",   # superficie transmitida (miles m²)
    "36400500": "precio_eur_m2",         # precio medio suelo urbano (€/m²)
}


def _norm_lab(s: str) -> str:
    return re.sub(r"\s+", " ", s).replace("( ", "(").replace(" )", ")").strip()


VT_NORM = {_norm_lab(k): v for k, v in VT_CCAA.items()}


def fetch_suelo() -> None:
    """Mercado de suelo por CCAA (flujo trimestral): nº, valor, superficie, precio.

    La superficie transmitida es la medida viva de suelo urbanizable que cambia
    de manos; el STOCK planificado lo cubre fetch_siu(). Cabecera: fila 10
    "Año YYYY" cada 4 columnas; la última columna es "Variación" y se excluye
    parando en el primer año no declarado. Filas 13+: TOTAL NACIONAL, CCAA y
    provincias (solo se conservan las CCAA del mapa; "Ceuta y Melilla" agregado
    se salta porque ya vienen por separado).
    """
    frames = []
    for xid, var in SUELO_TABLAS.items():
        url = BASE.format(xid=xid).replace("BoletinOnline/", "BoletinOnline2/")
        r = requests.get(url, headers=UA, timeout=90)
        r.raise_for_status()
        save_raw_bytes(f"mitma_suelo_{xid}.xls", r.content, url)
        wb = xlrd.open_workbook(file_contents=r.content)
        sh = wb.sheet_by_index(0)
        # columnas de trimestre: bajo cada "Año YYYY" de la fila 10 hay 4
        qcols = []
        for j in range(2, sh.ncols):
            head = str(sh.cell_value(10, j))
            m = re.search(r"Año (\d{4})", head)
            if m:
                y = int(m.group(1))
                qcols += [(j + k, y, k + 1) for k in range(4)]
        assert qcols, f"{xid}: cabecera de años no encontrada"
        for i in range(13, sh.nrows):
            ccaa = VT_NORM.get(_norm_lab(str(sh.cell_value(i, 1))))
            if not ccaa:
                continue
            for j, y, q in qcols:
                v = sh.cell_value(i, j) if j < sh.ncols else ""
                if isinstance(v, float):
                    frames.append({"ccaa": ccaa, "anyo": y, "quarter": q,
                                   "variable": var, "valor": v})
    df = pd.DataFrame(frames)
    assert df.duplicated(subset=["ccaa", "anyo", "quarter", "variable"]).sum() == 0
    assert df.ccaa.nunique() >= 18 and df.variable.nunique() == 4
    df.to_csv(PROCESSED / "mitma_suelo_ccaa.csv", index=False)
    sup24 = df.query("ccaa=='Nacional' and anyo==2024 and variable=='superficie_miles_m2'").valor.sum()
    print(f"SMOKE suelo: {df.ccaa.nunique()} territorios, {df.anyo.min()}–{df.anyo.max()}, "
          f"4 variables; superficie nacional 2024 = {sup24 / 1000:,.1f} millones m² → mitma_suelo_ccaa.csv")


SIU_VINTAGES = {
    # el paquete 2021 desapareció del CDN; se rescata del Wayback (declarado)
    2021: "http://web.archive.org/web/20220302050749/https://cdn.mitma.gob.es/portal-web-drupal/siu/datos_alfanumericos_siu_-_excel_-_20210709.zip",
    2025: "https://cdn.mivau.gob.es/portal-web-mivau/urbanismo-suelo/Datos%20alfanumericos%20SIU%20-%20Excel%20-%2020250527.zip",
}


def fetch_siu() -> None:
    """STOCK de suelo por clases urbanísticas (SIU, planes municipales).

    Única fuente machine-readable del suelo urbanizable PLANIFICADO por CCAA.
    Dos añadas (2021 y 2025); la cobertura municipal difiere (49 %→71 % en
    Andalucía p. ej.), así que la comparación honesta es entre PORCENTAJES de
    la superficie estudiada, no entre km² absolutos — ambos se publican y la
    cobertura viaja en la tabla. CPrSuzDe/Nd = % urbanizable delimitado/no
    delimitado; CTotSue = km² de los municipios estudiados.
    """
    import io
    import zipfile

    rows = []
    for vintage, url in SIU_VINTAGES.items():
        r = requests.get(url, headers=UA, timeout=300)
        r.raise_for_status()
        zf = zipfile.ZipFile(io.BytesIO(r.content))
        with zf.open("clases_suelo_ccaa.xlsx") as f:
            d = pd.read_excel(f)
        for _, x in d.iterrows():
            cob = re.search(r"\((\d+)%\)", str(x.MunEstud))
            rows.append({
                "ccaa_siu": x.DenCA, "vintage": vintage,
                "km2_estudiado": x.CTotSue,
                "cobertura_mun_pct": int(cob.group(1)) if cob else None,
                "pct_urbano_consolidado": x.CPrSuCon,
                "pct_urbanizable_delimitado": x.CPrSuzDe,
                "pct_urbanizable_no_delimitado": x.CPrSuzNd,
                "km2_urbanizable": x.CTotSue * (x.CPrSuzDe + x.CPrSuzNd) / 100,
            })
        save_raw_bytes(f"siu_clases_suelo_{vintage}.zip", r.content, url)
    df = pd.DataFrame(rows)
    assert df.vintage.nunique() == 2 and df.ccaa_siu.nunique() >= 19
    df.to_csv(PROCESSED / "siu_clases_suelo_ccaa.csv", index=False)
    nac = df.groupby("vintage").km2_urbanizable.sum()
    print(f"SMOKE SIU: {df.ccaa_siu.nunique()} CCAA × 2 añadas; urbanizable estudiado "
          f"{nac[2021]:,.0f} km² (2021) → {nac[2025]:,.0f} km² (2025) → siu_clases_suelo_ccaa.csv")


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    main()
    fetch_valor_tasado()
    fetch_suelo()
    fetch_siu()
