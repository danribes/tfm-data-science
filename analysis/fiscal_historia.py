"""Series históricas de gasto e ingresos: verificación del PIB y empalme 1850–2025.

Tres preguntas y sus pruebas:
1. ¿Tenemos el PIB para calcular los porcentajes? SÍ: JST trae niveles
   (PIB, ingresos, gasto en moneda corriente) → se RECALCULA el % desde
   niveles y se compara con el ratio publicado (control de denominador).
2. ¿Cuadran las series históricas con las modernas 1995–2025? Se mide la
   brecha GMD/WEO/JST vs Eurostat en la ventana de solape.
3. ¿Qué se puede decir? Empalme canónico España 1850–2025 (y panel JST de
   18 países) con la fuente de cada tramo declarada:
   Eurostat (1995+) > WEO (1950–1994) > JST (1870–1949) > GMD (pre-1870).

Salidas: gold_fiscal_historico.csv + figura b19 + lectura impresa.

    python3 analysis/fiscal_historia.py
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from backtest_t1 import GOLD

PROCESSED = GOLD.parent / "processed"
FIGS = GOLD.parents[1] / "docs" / "figures" / "atlas"
BLUE, GREEN, ORANGE, RED, INK2 = "#2a78d6", "#008300", "#eb6834", "#e34948", "#555"
SURFACE = "#fcfcfb"
GEO2ISO = {"ES": "ESP", "DE": "DEU", "FR": "FRA", "IT": "ITA", "PT": "PRT", "NL": "NLD",
           "IE": "IRL", "DK": "DNK", "FI": "FIN", "BE": "BEL", "SE": "SWE"}


def cargar():
    jst = pd.read_csv(PROCESSED / "jst_fiscal.csv")
    gmd = pd.read_csv(PROCESSED / "gmd_fiscal.csv").pivot_table(
        index=["iso3", "year"], columns="variable", values="value").reset_index()
    weo = pd.read_csv(PROCESSED / "weo_fiscal_totals.csv").pivot_table(
        index=["iso3", "year"], columns="variable", values="value").reset_index()
    eu = pd.read_csv(PROCESSED / "gov_10a_exp.csv")
    te = eu[(eu.na_item == "TE") & (eu.unit == "PC_GDP") & (eu.cofog == "TOTAL")].copy()
    te["iso3"] = te.geo.map(GEO2ISO)
    rev = pd.read_csv(PROCESSED / "gov_revenue_detail.csv").query("na_item=='TR'").copy()
    rev["iso3"], rev["year"] = rev.geo.map(GEO2ISO), rev.time.astype(int)
    return jst, gmd, weo, te.dropna(subset=["iso3"]), rev.dropna(subset=["iso3"])


def main() -> None:
    jst, gmd, weo, te, rev = cargar()

    # ---- 1. Control de denominador: recalcular % desde niveles JST
    j = jst.dropna(subset=["gdp", "expenditure", "revenue", "exp_gdp", "rev_gdp"]).copy()
    j["exp_recalc"] = j.expenditure / j.gdp * 100
    j["rev_recalc"] = j.revenue / j.gdp * 100
    d_exp = (j.exp_recalc - j.exp_gdp).abs().max()
    d_rev = (j.rev_recalc - j.rev_gdp).abs().max()
    print(f"1) Denominador JST (18 países, {j.year.min()}–{j.year.max()}, n={len(j)}): "
          f"máx |recalc − publicado| gasto {d_exp:.6f} pp, ingresos {d_rev:.6f} pp "
          f"→ el PIB está y los ratios son reproducibles")

    # ---- 2. Solape histórico vs moderno (España y panel)
    print("\n2) Brechas en ventanas de solape (|media| pp de PIB):")
    filas = []
    mod_exp = te[["iso3", "year", "value"]].rename(columns={"value": "eurostat"})
    for fuente, d, col in [("GMD", gmd, "exp_gdp"), ("WEO", weo, "exp_total"),
                           ("JST", jst.rename(columns={"iso": "iso3"}), "exp_gdp")]:
        m = mod_exp.merge(d[["iso3", "year", col]], on=["iso3", "year"]).dropna()
        m = m[m.year.between(1995, 2020)]
        if len(m):
            b = (m.eurostat - m[col]).abs().mean()
            print(f"   gasto {fuente} vs Eurostat 1995-2020: {b:.2f} pp (n={len(m)})")
            filas.append({"lado": "gasto", "fuente": fuente, "brecha_pp": round(b, 2), "n": len(m)})
    mod_rev = rev[["iso3", "year", "value"]].rename(columns={"value": "eurostat"})
    for fuente, d, col in [("GMD", gmd, "rev_gdp"), ("WEO", weo, "rev_total"),
                           ("JST", jst.rename(columns={"iso": "iso3"}), "rev_gdp")]:
        m = mod_rev.merge(d[["iso3", "year", col]], on=["iso3", "year"]).dropna()
        m = m[m.year.between(1995, 2020)]
        if len(m):
            b = (m.eurostat - m[col]).abs().mean()
            print(f"   ingresos {fuente} vs Eurostat 1995-2020: {b:.2f} pp (n={len(m)})")
            filas.append({"lado": "ingresos", "fuente": fuente, "brecha_pp": round(b, 2), "n": len(m)})

    # ---- 3. Empalme canónico (prioridad declarada por tramo)
    paises = sorted(set(jst.iso) | {"ESP"})
    piezas = []
    for iso in paises:
        marcos = {
            "eurostat": pd.merge(mod_exp[mod_exp.iso3 == iso].rename(columns={"eurostat": "exp"}),
                                 mod_rev[mod_rev.iso3 == iso].rename(columns={"eurostat": "rev"}),
                                 on=["iso3", "year"], how="outer"),
            "weo": weo[weo.iso3 == iso].rename(columns={"exp_total": "exp", "rev_total": "rev"}),
            "jst": jst[jst.iso == iso].rename(columns={"iso": "iso3", "exp_gdp": "exp", "rev_gdp": "rev"}),
            "gmd": gmd[gmd.iso3 == iso].rename(columns={"exp_gdp": "exp", "rev_gdp": "rev"}),
        }
        # Prioridad: Eurostat (1995+) > GMD (todo lo anterior). Hallazgo del
        # solape: GMD es CONTINUO en perímetro AAPP a través de 1995 (ES 1994
        # 46,4 → 1995 44,1), mientras WEO salta 12,8→44,5 (central→general) y
        # JST es SOLO administración central (brecha ~21 pp) → ni WEO ni JST
        # entran en el empalme; JST queda como capa declarada de scope central.
        usados = set()
        for fuente, rango in [("eurostat", (1995, 2025)), ("gmd", (1700, 1994))]:
            d = marcos[fuente]
            if d is None or d.empty:
                continue
            d = d[(d.year.between(*rango)) & (~d.year.isin(usados))]
            for _, r in d.iterrows():
                if pd.notna(r.get("exp")) or pd.notna(r.get("rev")):
                    usados.add(int(r.year))
                    piezas.append({"iso3": iso, "year": int(r.year), "exp_gdp": r.get("exp"),
                                   "rev_gdp": r.get("rev"), "fuente": fuente})
    canon = pd.DataFrame(piezas).sort_values(["iso3", "year"])
    canon.to_csv(GOLD / "gold_fiscal_historico.csv", index=False)

    es = canon[canon.iso3 == "ESP"].set_index("year")
    print(f"\n3) España, empalme {es.index.min()}–{es.index.max()} "
          f"({dict(es.fuente.value_counts())}):")
    for y in [1850, 1900, 1935, 1960, 1977, 1995, 2007, 2012, 2023]:
        if y in es.index:
            r = es.loc[y]
            print(f"   {y}: gasto {r.exp_gdp:5.1f} / ingresos {r.rev_gdp:5.1f} %PIB [{r.fuente}]")

    fig, ax = plt.subplots(figsize=(9.5, 4.6), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.plot(es.index, es.exp_gdp, color=RED, lw=1.6, label="Gasto público")
    ax.plot(es.index, es.rev_gdp, color=BLUE, lw=1.6, label="Ingresos públicos")
    ax.fill_between(es.index, es.rev_gdp, es.exp_gdp, where=es.exp_gdp > es.rev_gdp,
                    color=RED, alpha=0.12, label="Déficit")
    for y, lab in [(1936, "Guerra Civil"), (1977, "Pactos Moncloa"), (2008, "Crisis"), (2020, "COVID")]:
        ax.axvline(y, color=INK2, lw=0.6, ls=":")
        ax.text(y, ax.get_ylim()[1] * 0.02 + 47, lab, rotation=90, fontsize=7, color=INK2, va="bottom")
    ax.set_title(f"España {es.index.min()}–{es.index.max()}: gasto e ingresos públicos (% PIB, fuentes empalmadas)", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGS / "b19_fiscal_historia_es.png", dpi=150)
    print(f"figura → {FIGS / 'b19_fiscal_historia_es.png'}")


if __name__ == "__main__":
    main()
