"""Atlas de evolución del gasto público (F2.1) — figuras B1–B15 + proyección.

Una figura por pregunta del bloque B del PLAN_MAESTRO, siempre con España
resaltada frente al contexto (mediana UE del panel o mediana mundial del
histórico GMD/JST). Salida: docs/figures/atlas/*.png y docs/atlas.md como
lectura guiada.

    python3 analysis/atlas.py
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from backtest_t1 import GOLD

PROCESSED = GOLD.parent / "processed"
FIG = GOLD.parents[1] / "docs" / "figures" / "atlas"
FIG.mkdir(parents=True, exist_ok=True)

BLUE, GREEN, ORANGE, VIOLET = "#2a78d6", "#008300", "#eb6834", "#4a3aa7"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e5e4e0"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "savefig.dpi": 150,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2,
    "ytick.color": INK2, "axes.edgecolor": GRID, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
    "axes.spines.right": False, "font.size": 9, "axes.titlesize": 10,
})

CENT = pd.read_csv(GOLD / "gold_century_fiscal.csv")
PANEL = pd.read_csv(GOLD / "gold_panel_anual.csv").query("year<=2023")


def cent_series(iso3: str, var: str) -> pd.Series:
    d = CENT[(CENT.iso3 == iso3) & (CENT.variable == var)]
    return d.set_index("year")["value"].sort_index()


def cent_median(var: str, min_n: int = 30) -> pd.Series:
    d = CENT[CENT.variable == var].groupby("year")["value"]
    m, n = d.median(), d.size()
    return m[n >= min_n]


def pan(geo: str, var: str) -> pd.Series:
    d = PANEL[(PANEL.geo == geo) & (PANEL.variable == var)]
    return d.set_index("year")["value"].sort_index()


def eu_band(var: str):
    d = PANEL[PANEL.variable == var].groupby("year")["value"]
    return d.median(), d.quantile(0.25), d.quantile(0.75)


def new_fig(title: str, ylabel: str = "% del PIB", size=(8.5, 4.2)):
    fig, ax = plt.subplots(figsize=size)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    return fig, ax


def es_vs_eu(var: str, title: str, fname: str, ylabel: str = "% del PIB", scale: float = 1.0):
    """Patrón común: España (azul) sobre banda p25–p75 y mediana del panel."""
    med, q1, q3 = eu_band(var)
    med, q1, q3 = med * scale, q1 * scale, q3 * scale
    fig, ax = new_fig(title, ylabel)
    ax.fill_between(med.index, q1, q3, color=GRID, alpha=0.6, lw=0)
    ax.plot(med.index, med.values, color=INK2, lw=1.4)
    es = pan("ES", var) * scale
    ax.plot(es.index, es.values, color=BLUE, lw=2.0)
    ax.annotate("España", (es.index[-1], es.iloc[-1]), color=BLUE, fontweight="bold",
                xytext=(6, 0), textcoords="offset points", va="center")
    ax.annotate("mediana panel (banda p25–p75)", (med.index[-1], med.iloc[-1]),
                color=INK2, fontsize=8, xytext=(6, 0), textcoords="offset points", va="center")
    fig.tight_layout()
    fig.savefig(FIG / fname)
    plt.close(fig)
    return es


def main():
    # B1 — gasto público total, siglos XX–XXI
    fig, ax = new_fig("B1 · Gasto público total, 1900–2023: el siglo de la expansión")
    wm = cent_median("exp_gdp")
    ax.plot(wm.index, wm.values, color=INK2, lw=1.4)
    for iso, color in [("ESP", BLUE), ("USA", GREEN), ("GBR", ORANGE), ("SWE", VIOLET)]:
        s = cent_series(iso, "exp_gdp")
        ax.plot(s.index, s.values, color=color, lw=1.8 if iso == "ESP" else 1.2,
                alpha=1.0 if iso == "ESP" else 0.75)
        ax.annotate({"ESP": "España", "USA": "EE. UU.", "GBR": "R. Unido", "SWE": "Suecia"}[iso],
                    (s.index[-1], s.iloc[-1]), color=color, fontsize=8,
                    xytext=(6, 0), textcoords="offset points", va="center")
    ax.annotate("mediana mundial", (wm.index[-1], wm.iloc[-1]), color=INK2, fontsize=8,
                xytext=(6, 0), textcoords="offset points", va="center")
    fig.tight_layout(); fig.savefig(FIG / "b01_gasto_total_siglo.png"); plt.close(fig)

    # B2 — composición económica del gasto (España, apilado)
    comp = [("wages", "Salarios (D1)", BLUE), ("goods", "Bienes y servicios (P2)", GREEN),
            ("benefits", "Prestaciones sociales (D62)", ORANGE), ("interest", "Intereses (D41)", VIOLET)]
    years = pan("ES", "te_total").index
    fig, ax = new_fig("B2 · España: composición económica del gasto, 1995–2023")
    bottom = pd.Series(0.0, index=years)
    for var, label, color in comp:
        s = pan("ES", var).reindex(years).fillna(0)
        ax.fill_between(years, bottom, bottom + s, color=color, alpha=0.75, lw=0, label=label)
        bottom = bottom + s
    resto = pan("ES", "te_total").reindex(years) - bottom
    ax.fill_between(years, bottom, bottom + resto, color=GRID, lw=0, label="Resto (subvenciones, capital…)")
    ax.plot(years, pan("ES", "te_total").reindex(years), color=INK, lw=1.2)
    ax.legend(frameon=False, fontsize=8, ncols=2, loc="upper left")
    fig.tight_layout(); fig.savefig(FIG / "b02_composicion_economica.png"); plt.close(fig)

    # B3 — vivienda: inversión pública SIEMPRE junto a la residencial total (Revisión 1)
    dw = pd.read_csv(PROCESSED / "gfcf_dwellings.csv")
    dw_es = dw[dw.geo == "ES"].set_index("time")["value"].sort_index()
    dw_med = dw[dw.geo.isin(PANEL.geo.unique())].groupby("time")["value"].median()
    fig, ax = new_fig("B3 · Vivienda: inversión pública (GF06) frente a inversión residencial TOTAL")
    ax.plot(dw_es.index, dw_es.values, color=BLUE, lw=2.0, label="España — residencial total (FBCF viviendas)")
    ax.plot(dw_med.index, dw_med.values, color=INK2, lw=1.2, label="mediana panel — residencial total")
    ax.plot(pan("ES", "te_gf06").index, pan("ES", "te_gf06").values, color=ORANGE, lw=2.0,
            label="España — gasto público vivienda y comunidad (GF06)")
    med06, _, _ = eu_band("te_gf06")
    ax.plot(med06.index, med06.values, color=ORANGE, lw=1.0, ls="--", alpha=0.7,
            label="mediana panel — GF06")
    ax.legend(frameon=False, fontsize=8)
    ax.annotate("la promoción privada domina la oferta:\nGF06 ≈ 0,5 %PIB vs total ≈ 5–6 %PIB",
                (2013, 8.5), color=INK2, fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "b03_vivienda_publica_vs_total.png"); plt.close(fig)

    # B4 — sanidad (GHED, gasto público en salud %PIB)
    gh = pd.read_csv(PROCESSED / "ghed.csv").query("variable=='public_gdp'")
    med = gh.groupby("year")["value"].median()
    fig, ax = new_fig("B4 · Gasto público en sanidad, 2000–2022 (GHED, 195 países)")
    ax.plot(med.index, med.values, color=INK2, lw=1.4)
    for iso, color, lbl in [("ESP", BLUE, "España"), ("USA", GREEN, "EE. UU."), ("DEU", ORANGE, "Alemania")]:
        s = gh[gh.iso3 == iso].set_index("year")["value"].sort_index()
        ax.plot(s.index, s.values, color=color, lw=1.8 if iso == "ESP" else 1.2)
        ax.annotate(lbl, (s.index[-1], s.iloc[-1]), color=color, fontsize=8,
                    xytext=(6, 0), textcoords="offset points", va="center")
    ax.annotate("mediana mundial", (med.index[-1], med.iloc[-1]), color=INK2, fontsize=8,
                xytext=(6, 0), textcoords="offset points", va="center")
    fig.tight_layout(); fig.savefig(FIG / "b04_sanidad_ghed.png"); plt.close(fig)

    # B5 — inversión pública (FBCF del gobierno) y asuntos económicos
    es_vs_eu("gfcf", "B5 · Inversión pública (FBCF de las AAPP) — el ajuste post-2010 en España",
             "b05_inversion_publica.png")

    # B6 — empleo público
    es_vs_eu("pub_emp_share", "B6 · Empleo público (% del empleo total, WWBI)",
             "b06_empleo_publico.png", ylabel="% del empleo", scale=100)

    # B7 — masa salarial pública
    es_vs_eu("wagebill_gdp", "B7 · Salarios públicos (D1, % del PIB)", "b07_salarios_publicos.png")

    # B8 — deuda pública, siglos XX–XXI
    fig, ax = new_fig("B8 · Deuda pública española, 1900–2023, frente a la mediana mundial")
    wm = cent_median("debt_gdp")
    es = cent_series("ESP", "debt_gdp")
    ax.plot(wm.index, wm.values, color=INK2, lw=1.4)
    ax.plot(es.index, es.values, color=BLUE, lw=2.0)
    for y, txt in [(1900, "≈124 % tras el 98"), (1960, "mínimo ≈30 %"), (2023, f"{es.loc[2023]:.0f} % hoy")]:
        if y in es.index:
            ax.annotate(txt, (y, es.loc[y]), color=BLUE, fontsize=8,
                        xytext=(0, 10), textcoords="offset points", ha="center")
    ax.annotate("mediana mundial", (wm.index[-1], wm.iloc[-1]), color=INK2, fontsize=8,
                xytext=(6, 0), textcoords="offset points", va="center")
    fig.tight_layout(); fig.savefig(FIG / "b08_deuda_siglo.png"); plt.close(fig)

    # B9 — protección social
    es_vs_eu("te_gf10", "B9 · Protección social (GF10, % del PIB)", "b09_proteccion_social.png")

    # B10 — desempleo
    es_vs_eu("unemployment", "B10 · Tasa de paro — la anomalía española persistente",
             "b10_desempleo.png", ylabel="% población activa")

    # B11 — intereses de la deuda
    es_vs_eu("interest", "B11 · Intereses de la deuda (D41, % del PIB)", "b11_intereses.png")

    # B12 — pensiones y envejecimiento (dos paneles, sin doble eje)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.5, 5.6), sharex=True)
    med, q1, q3 = eu_band("pensions_oldage")
    ax1.fill_between(med.index, q1, q3, color=GRID, alpha=0.6, lw=0)
    ax1.plot(med.index, med.values, color=INK2, lw=1.4)
    s = pan("ES", "pensions_oldage"); ax1.plot(s.index, s.values, color=BLUE, lw=2.0)
    ax1.set_title("B12 · Pensiones de vejez (% del PIB)"); ax1.set_ylabel("% del PIB")
    med, q1, q3 = eu_band("pop65_share")
    ax2.fill_between(med.index, q1, q3, color=GRID, alpha=0.6, lw=0)
    ax2.plot(med.index, med.values, color=INK2, lw=1.4)
    s = pan("ES", "pop65_share"); ax2.plot(s.index, s.values, color=BLUE, lw=2.0)
    ax2.set_title("Población 65+ (% del total)"); ax2.set_ylabel("%")
    fig.tight_layout(); fig.savefig(FIG / "b12_pensiones_envejecimiento.png"); plt.close(fig)

    # B13 — migración: stock en España y flujos
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4))
    st = pd.read_csv(PROCESSED / "un_migrant_stock.csv")
    es_st = st[st.destination.str.contains("Spain", case=False, na=False)]
    ax1.plot(es_st.year, es_st.migrant_stock / 1e6, color=BLUE, lw=2.0, marker="o", ms=4)
    ax1.set_title("B13 · Stock de migrantes en España (UN DESA)"); ax1.set_ylabel("millones")
    for var, color, lbl in [("immigration", GREEN, "inmigración"), ("emigration", ORANGE, "emigración")]:
        s = pan("ES", var) / 1e3
        ax2.plot(s.index, s.values, color=color, lw=1.8, label=lbl)
    ax2.set_title("Flujos anuales (España, Eurostat)"); ax2.set_ylabel("miles")
    ax2.legend(frameon=False)
    fig.tight_layout(); fig.savefig(FIG / "b13_migracion.png"); plt.close(fig)

    # B14 — ayuda internacional recibida
    oda = pd.read_csv(PROCESSED / "oda.csv").query("variable=='oda_received_gni'")
    med = oda.groupby("year")["value"].median()
    fig, ax = new_fig("B14 · Ayuda oficial al desarrollo recibida (% de la RNB)", ylabel="% RNB")
    ax.plot(med.index, med.values, color=INK2, lw=1.4)
    ax.annotate("mediana de países receptores", (med.index[-1], med.iloc[-1]), color=INK2,
                fontsize=8, xytext=(6, 0), textcoords="offset points", va="center")
    q9 = oda.groupby("year")["value"].quantile(0.9)
    ax.fill_between(med.index, 0, q9.reindex(med.index), color=GRID, alpha=0.5, lw=0)
    ax.annotate("percentil 90 (países más dependientes)", (2005, float(q9.loc[2005]) + 0.5),
                color=INK2, fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "b14_oda.png"); plt.close(fig)

    # B15 — déficit fiscal, siglos XX–XXI
    fig, ax = new_fig("B15 · Déficit fiscal español, 1900–2023 (− = déficit)")
    es = cent_series("ESP", "deficit_gdp")
    wm = cent_median("deficit_gdp")
    ax.plot(wm.index, wm.values, color=INK2, lw=1.2)
    ax.plot(es.index, es.values, color=BLUE, lw=1.8)
    ax.axhline(0, color=INK2, lw=0.8)
    for y, txt in [(2009, "crisis financiera"), (2020, "COVID")]:
        if y in es.index:
            ax.annotate(txt, (y, es.loc[y]), color=BLUE, fontsize=8,
                        xytext=(0, -14), textcoords="offset points", ha="center")
    ax.annotate("mediana mundial", (wm.index[-1], wm.iloc[-1]), color=INK2, fontsize=8,
                xytext=(6, 0), textcoords="offset points", va="center")
    fig.tight_layout(); fig.savefig(FIG / "b15_deficit_siglo.png"); plt.close(fig)

    # B16 — proyección demográfica 2023–2070 (insumo del motor de pensiones/sanidad)
    pr = pd.read_csv(GOLD / "gold_projections.csv")
    es = pr[pr.geo == "ES"]
    fig, ax = new_fig("B16 · España: población 65+ proyectada, 2023–2070 (6 variantes Eurostat)",
                      ylabel="% de la población")
    for var, d in es.groupby("variant"):
        d = d.sort_values("year")
        is_bsl = var == "BSL"
        ax.plot(d.year, d.share65 * (100 if d.share65.max() < 1 else 1),
                color=BLUE if is_bsl else GRID, lw=2.0 if is_bsl else 1.0)
    ax.annotate("línea base (BSL); grises = variantes\nde fecundidad, migración y mortalidad",
                (2050, float(es[es.variant == 'BSL'].share65.max()) * (100 if es.share65.max() < 1 else 1)),
                color=INK2, fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "b16_proyeccion_65.png"); plt.close(fig)

    print(f"→ {FIG}: {len(list(FIG.glob('*.png')))} figuras")
    # anclas para la lectura del atlas
    print("ES te_total 2023:", pan("ES", "te_total").iloc[-1],
          "| GF06:", pan("ES", "te_gf06").iloc[-1],
          "| viviendas total FBCF ES últl:", dw_es.iloc[-1], f"({dw_es.index[-1]})",
          "| paro últ:", pan("ES", "unemployment").iloc[-1],
          "| pensiones:", pan("ES", "pensions_oldage").iloc[-1],
          "| 65+ 2070 BSL:", float(es[(es.variant == 'BSL')].sort_values('year').share65.iloc[-1]))


if __name__ == "__main__":
    main()
