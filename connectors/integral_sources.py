"""Conectores del programa INTEGRAL (P4 sanidad global, P7 flujos, P8 migración, prólogo).

Cada fetcher es autónomo y degrada a DEFERRED sin romper el resto.
Deferred documentados: GRD (URL movida), WB BOS (catálogo 404), SIPRI (bloquea),
GMD (vía pip package), GFS-COFOG global (vía MCP imf-data), liquidaciones CCAA.
"""
from __future__ import annotations

import shutil
import sys

import pandas as pd
import requests

from base import PROCESSED, RAW, UA, http_json

GHED_URL = "https://apps.who.int/nha/database/Home/IndicatorsDownload/en"
DESA_URL = ("https://www.un.org/development/desa/pd/sites/www.un.org.development."
            "desa.pd/files/undesa_pd_2024_ims_stock_by_sex_and_destination.xlsx")
JST_SCRATCH = ("/tmp/claude-1000/-home-dan-projects/deae5a34-4307-4236-afa8-b0ed15278d74/"
               "scratchpad/jst.xlsx")

GHED_KEEP = {
    # nombres REALES de la hoja Data (inspección 2026-07-18): location/code/year + estos
    "che_gdp": "che_gdp",            # gasto sanitario total %PIB
    "che_pc_usd": "che_pc_usd",      # per cápita USD
    "gghed_che": "public_share",     # público / total
    "gghed_gdp": "public_gdp",       # público %PIB
    "gghed_gge": "health_share_exp", # sanidad % del gasto público total
    "pvtd_che": "private_share",
    "oops_che": "oop_share",         # bolsillo / total (plural real: oops_che)
    "hk_che": "capital_share_che",   # capital sanitario si existe
}


def fetch_ghed() -> None:
    dest_raw = RAW / "ghed.xlsx"
    if not dest_raw.exists():
        r = requests.get(GHED_URL, headers=UA, timeout=300)
        r.raise_for_status()
        assert len(r.content) > 10_000_000, f"GHED sospechosamente pequeño: {len(r.content)}"
        dest_raw.write_bytes(r.content)
    xl = pd.ExcelFile(dest_raw)
    sheet = next(s for s in xl.sheet_names if s.lower().startswith("data"))
    df = xl.parse(sheet)
    cols = {c.lower(): c for c in df.columns}
    base = [cols[c] for c in ("location", "code", "year") if c in cols]
    keep = {cols[k]: v for k, v in GHED_KEEP.items() if k in cols}
    out = df[base + list(keep)].rename(columns={**dict(zip(base, ["country", "iso3", "year"])), **keep})
    long = out.melt(id_vars=["country", "iso3", "year"], var_name="variable", value_name="value").dropna(subset=["value"])
    assert long.query("iso3=='ESP' and year==2022 and variable=='public_gdp'")["value"].between(6, 8).all(), "ancla GHED ES"
    n = long.query("variable=='che_gdp'")["iso3"].nunique()
    assert n > 180, f"cobertura GHED: {n}"
    long.to_csv(PROCESSED / "ghed.csv", index=False)
    print(f"  ghed: {len(long)} filas, {n} países → ghed.csv")


def fetch_desa() -> None:
    dest_raw = RAW / "undesa_ims_2024.xlsx"
    if not dest_raw.exists():
        r = requests.get(DESA_URL, headers=UA, timeout=120)
        r.raise_for_status()
        dest_raw.write_bytes(r.content)
    xl = pd.ExcelFile(dest_raw)
    sheet = next((s for s in xl.sheet_names if "Table 1" in s), xl.sheet_names[0])
    df = xl.parse(sheet, header=None)
    # localizar fila de cabecera (contiene 1990) y columna de nombres
    hdr = None
    for i in range(min(20, len(df))):
        if (df.iloc[i] == 1990).any():
            hdr = i
            break
    assert hdr is not None, "cabecera DESA no encontrada"
    years = [int(v) for v in df.iloc[hdr] if isinstance(v, (int, float)) and 1980 < v < 2030]
    year_cols = [j for j, v in enumerate(df.iloc[hdr]) if isinstance(v, (int, float)) and 1980 < v < 2030][:len(set(years))]
    name_col = 1 if df.iloc[hdr + 2 :, 1].notna().any() else 0
    rows = []
    for i in range(hdr + 1, len(df)):
        name = df.iat[i, name_col]
        if not isinstance(name, str) or not name.strip():
            continue
        for j, y in zip(year_cols, sorted(set(years))):
            v = df.iat[i, j]
            if isinstance(v, (int, float)) and pd.notna(v):
                rows.append({"destination": name.strip(), "year": int(y), "migrant_stock": float(v)})
    out = pd.DataFrame(rows)
    es = out[out.destination.str.contains("Spain", case=False, na=False)]
    assert len(es) >= 5, "España no encontrada en DESA"
    out.to_csv(PROCESSED / "un_migrant_stock.csv", index=False)
    print(f"  un_migrant_stock: {len(out)} filas, {out.destination.nunique()} destinos → un_migrant_stock.csv")


def fetch_oda() -> None:
    frames = []
    for code, vn in [("DT.ODA.ODAT.GN.ZS", "oda_received_gni"), ("DT.ODA.ODAT.KD", "oda_received_usd")]:
        js = http_json(f"https://api.worldbank.org/v2/country/all/indicator/{code}",
                       params=[("format", "json"), ("per_page", "20000"), ("date", "1995:2023")])
        if len(js) > 1 and js[1]:
            frames.append(pd.DataFrame([
                {"iso3": r["countryiso3code"], "year": int(r["date"]), "variable": vn, "value": r["value"]}
                for r in js[1] if r["value"] is not None and r["countryiso3code"]
            ]))
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(PROCESSED / "oda.csv", index=False)
    print(f"  oda: {len(out)} filas → oda.csv (ayuda RECIBIDA; matriz donante→receptor = DAC CRS, deferred)")


def fetch_jst() -> None:
    dest_raw = RAW / "jst_r6.xlsx"
    if not dest_raw.exists():
        try:
            shutil.copy(JST_SCRATCH, dest_raw)
        except FileNotFoundError:  # scratchpad limpiado — re-descarga (URL verificada)
            r = requests.get("https://www.macrohistory.net/app/download/9834512569/JSTdatasetR6.xlsx",
                             headers=UA, timeout=120, allow_redirects=True)
            r.raise_for_status()
            dest_raw.write_bytes(r.content)
    df = pd.read_excel(dest_raw)
    keep = df[["iso", "year", "gdp", "revenue", "expenditure", "debtgdp"]].dropna(subset=["revenue", "expenditure"], how="all")
    keep = keep.assign(exp_gdp=keep.expenditure / keep.gdp * 100, rev_gdp=keep.revenue / keep.gdp * 100)
    keep.to_csv(PROCESSED / "jst_fiscal.csv", index=False)
    print(f"  jst_fiscal: {len(keep)} filas ({keep.iso.nunique()} países, {keep.year.min()}–{keep.year.max()}) → jst_fiscal.csv")


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    ok, fail = [], []
    for name, fn in [("ghed", fetch_ghed), ("desa", fetch_desa), ("oda", fetch_oda), ("jst", fetch_jst)]:
        try:
            fn()
            ok.append(name)
        except Exception as e:  # noqa: BLE001
            fail.append((name, str(e)[:130]))
            print(f"  {name}: FALLO {str(e)[:120]}")
    print(f"\nOK: {ok} | fallos: {fail if fail else 'ninguno'}")
    print("DEFERRED documentados: GRD, WB BOS, SIPRI, GMD(pip), GFS-COFOG(MCP), liquidaciones CCAA, DAC CRS, cohesiondata")
