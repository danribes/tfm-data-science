"""Desglose fiscal mundial + reconciliación cruzada de fuentes.

Responde a "¿estamos usando los valores correctos para cada tipo de gasto (y
de ingreso)?" con la única prueba que vale: comparar fuentes INDEPENDIENTES
sobre el mismo concepto y publicar las brechas.

Piezas:
- Gasto por función: Eurostat COFOG (UE, gov_10a_exp) × IMF GFS_COFOG (89
  países) — para la UE ambos publican y deben coincidir (misma metodología,
  compiladores distintos).
- Ingresos: Eurostat (TR + componentes) × IMF WoRLD (195 países) × OCDE
  Revenue Statistics (146; ojo: la OCDE cuenta cotizaciones como impuesto
  —cabecera 2000—, GFS las separa; se compara like-for-like).
- Totales: ambos lados contra IMF WEO (la fuente que ya usaba D1).

Salidas: gold_fiscal_breakdown.csv (país×año×lado×categoría×%PIB×fuente),
gold_fiscal_reconciliation.csv (todas las brechas) y lectura impresa.

    python3 analysis/fiscal_breakdown.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from backtest_t1 import GOLD

PROCESSED = GOLD.parent / "processed"
GEO2ISO = {"ES": "ESP", "DE": "DEU", "FR": "FRA", "IT": "ITA", "PT": "PRT", "NL": "NLD",
           "SE": "SWE", "PL": "POL", "AT": "AUT", "EL": "GRC", "IE": "IRL", "DK": "DNK",
           "FI": "FIN", "BE": "BEL", "CZ": "CZE", "HU": "HUN", "RO": "ROU"}


def cargar() -> dict[str, pd.DataFrame]:
    d = {}
    eu = pd.read_csv(PROCESSED / "gov_10a_exp.csv")
    d["eu_cofog"] = eu[(eu.na_item == "TE") & (eu.unit == "PC_GDP")]
    d["imf_cofog"] = pd.read_csv(PROCESSED / "gfs_cofog_global.csv")
    d["world"] = pd.read_csv(PROCESSED / "world_revenue_global.csv")
    d["oecd_rs"] = pd.read_csv(PROCESSED / "oecd_tax_global.csv")
    d["weo"] = pd.read_csv(PROCESSED / "weo_fiscal_totals.csv")
    rev = pd.read_csv(PROCESSED / "gov_revenue_detail.csv")
    rev["year"] = rev.time.astype(int)
    d["eu_rev"] = rev
    return d


def main() -> None:
    x = cargar()
    checks = []

    # ---- 1. COFOG por función: Eurostat vs IMF (países UE que reportan a ambos)
    eu = x["eu_cofog"].copy()
    eu["iso3"] = eu.geo.map(GEO2ISO)
    eu = eu.dropna(subset=["iso3"])
    m = (eu[eu.cofog.str.fullmatch("GF\\d\\d")]
         .merge(x["imf_cofog"], left_on=["iso3", "cofog", "year"],
                right_on=["iso3", "funcion", "year"], suffixes=("_eurostat", "_imf")))
    m = m[m.year.between(2015, 2023)]
    m["brecha"] = m.value - m.pct_gdp
    por_fun = m.groupby("cofog").brecha.agg(["mean", lambda s: s.abs().mean(), "count"])
    por_fun.columns = ["media", "abs_media", "n"]
    print("1) COFOG Eurostat vs IMF (UE, 2015-23, pp de PIB):")
    print(por_fun.round(2).to_string())
    for f, r in por_fun.iterrows():
        checks.append({"check": f"cofog_{f}_eurostat_vs_imf", "ambito": "UE",
                       "brecha_abs_media_pp": round(r.abs_media, 3), "n": int(r.n),
                       "veredicto": "OK" if r.abs_media < 0.35 else "REVISAR"})

    # ---- 2. Totales de gasto: Eurostat TOTAL vs WEO
    tot = (eu[eu.cofog == "TOTAL"].merge(
        x["weo"].query("variable=='exp_total'"), on=["iso3", "year"]))
    tot = tot[tot.year.between(2015, 2023)]
    tot["brecha"] = tot.value_x - tot.value_y if "value_x" in tot else tot.value - tot.value_y
    g = tot.brecha.abs().mean()
    print(f"\n2) Gasto TOTAL Eurostat vs WEO (UE 2015-23): brecha |media| = {g:.2f} pp, "
          f"máx = {tot.brecha.abs().max():.2f} pp (n={len(tot)})")
    checks.append({"check": "exp_total_eurostat_vs_weo", "ambito": "UE",
                   "brecha_abs_media_pp": round(g, 3), "n": len(tot),
                   "veredicto": "OK" if g < 1.0 else "REVISAR"})

    # ---- 3. Ingresos totales: Eurostat TR vs WoRLD vs WEO (ESP + UE)
    tr = x["eu_rev"].query("na_item=='TR'").copy()
    tr["iso3"] = tr.geo.map(GEO2ISO)
    wr = x["world"].query("categoria=='rev_total'")
    j = (tr.dropna(subset=["iso3"]).merge(wr, on=["iso3", "year"])
         .merge(x["weo"].query("variable=='rev_total'"), on=["iso3", "year"]))
    j = j[j.year.between(2015, 2023)]
    b1 = (j.value_x - j.pct_gdp).abs().mean()   # Eurostat vs WoRLD
    b2 = (j.value_x - j.value_y).abs().mean()   # Eurostat vs WEO
    print(f"\n3) Ingresos totales (UE 2015-23): |Eurostat−WoRLD| = {b1:.2f} pp; "
          f"|Eurostat−WEO| = {b2:.2f} pp (n={len(j)})")
    checks += [{"check": "rev_total_eurostat_vs_world", "ambito": "UE",
                "brecha_abs_media_pp": round(b1, 3), "n": len(j),
                "veredicto": "OK" if b1 < 1.0 else "REVISAR"},
               {"check": "rev_total_eurostat_vs_weo", "ambito": "UE",
                "brecha_abs_media_pp": round(b2, 3), "n": len(j),
                "veredicto": "OK" if b2 < 1.0 else "REVISAR"}]

    # ---- 4. Impuestos like-for-like: WoRLD (tax+cotiz) vs OCDE-RS (Σ cabeceras)
    w = x["world"].pivot_table(index=["iso3", "year"], columns="categoria", values="pct_gdp")
    w["tax_mas_ss"] = w.tax_total + w.cotizaciones_ss
    rs = x["oecd_rs"].groupby(["iso3", "year"]).pct_gdp.sum().rename("oecd_total")
    c = w.join(rs, how="inner").dropna(subset=["tax_mas_ss", "oecd_total"])
    c = c[c.index.get_level_values("year") >= 2015]
    c["brecha"] = c.tax_mas_ss - c.oecd_total
    print(f"\n4) Presión fiscal like-for-like WoRLD(tax+SSC) vs OCDE-RS (mundo 2015+): "
          f"|media| = {c.brecha.abs().mean():.2f} pp, mediana = {c.brecha.abs().median():.2f} pp "
          f"(n={len(c)}, {c.index.get_level_values('iso3').nunique()} países)")
    esp = c.loc[("ESP", 2022)]
    print(f"   ESP 2022: WoRLD {esp.tax_mas_ss:.1f} vs OCDE {esp.oecd_total:.1f}")
    checks.append({"check": "tax_world_vs_oecd", "ambito": "mundo",
                   "brecha_abs_media_pp": round(c.brecha.abs().mean(), 3), "n": len(c),
                   "veredicto": "OK" if c.brecha.abs().median() < 1.0 else "REVISAR"})

    # ---- 5. Aditividad interna WoRLD: total ≈ impuestos+cotiz+donaciones+otros
    comp = w.dropna(subset=["rev_total", "tax_total", "cotizaciones_ss"])
    suma = comp[["tax_total", "cotizaciones_ss", "donaciones", "otros_ingresos"]].sum(axis=1, min_count=3)
    resid = (comp.rev_total - suma).abs()
    ok = (resid < 1.0).mean() * 100
    print(f"\n5) Aditividad WoRLD (total = Σ componentes): {ok:.0f} % de país-años cuadran a <1 pp "
          f"(n={resid.notna().sum()})")
    checks.append({"check": "world_aditividad", "ambito": "mundo",
                   "brecha_abs_media_pp": round(float(resid.mean()), 3),
                   "n": int(resid.notna().sum()), "veredicto": "OK" if ok > 80 else "REVISAR"})

    # ---- gold unificado
    piezas = []
    imf = x["imf_cofog"].rename(columns={"funcion": "categoria"})
    piezas.append(imf.assign(lado="gasto", fuente="imf_gfs")[["iso3", "year", "lado", "categoria", "pct_gdp", "fuente"]])
    eu2 = eu[eu.cofog.str.startswith("GF")].rename(columns={"cofog": "categoria", "value": "pct_gdp"})
    piezas.append(eu2.assign(lado="gasto", fuente="eurostat")[["iso3", "year", "lado", "categoria", "pct_gdp", "fuente"]])
    piezas.append(x["world"].assign(lado="ingreso", fuente="imf_world")[["iso3", "year", "lado", "categoria", "pct_gdp", "fuente"]])
    piezas.append(x["oecd_rs"].rename(columns={"cabecera": "categoria"})
                  .assign(lado="ingreso", fuente="oecd_rs")[["iso3", "year", "lado", "categoria", "pct_gdp", "fuente"]])
    gold = pd.concat(piezas, ignore_index=True).dropna(subset=["pct_gdp"])
    gold.to_csv(GOLD / "gold_fiscal_breakdown.csv", index=False)
    pd.DataFrame(checks).to_csv(GOLD / "gold_fiscal_reconciliation.csv", index=False)
    print(f"\ngold_fiscal_breakdown.csv: {len(gold):,} filas, {gold.iso3.nunique()} países; "
          f"reconciliación: {sum(1 for c in checks if c['veredicto'] == 'OK')}/{len(checks)} checks OK")


if __name__ == "__main__":
    main()
