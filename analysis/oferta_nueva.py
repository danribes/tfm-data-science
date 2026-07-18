"""Driver de oferta `oferta_nueva` — visados/permisos de obra residencial (ES).

Primera pata (Revisión 1 de la Entrega 4): permisos de vivienda Eurostat
`sts_cobp_q` (nº de viviendas, residencial excl. residencias colectivas,
índice 2021=100, NSA), nacional 1995Q1–2026Q1. La pata provincial (visados
MITMA) queda declarada como refinamiento.

Pregunta de este análisis: ¿los permisos ANTICIPAN el ciclo del IPV con el
retardo constructivo de 18–24 meses? Si sí, son el candidato a arreglar el
punto ciego del drift (los giros) en la PRÓXIMA ronda de validación — nunca
contra el test gastado (2024–25); la adopción exigirá datos nuevos de 2026+.

    python3 analysis/oferta_nueva.py
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from backtest_t1 import GOLD

PROCESSED = GOLD.parent / "processed"
FIG = GOLD.parents[1] / "docs" / "figures" / "eda"

BLUE, GREEN = "#2a78d6", "#008300"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e5e4e0"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "savefig.dpi": 150,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2,
    "ytick.color": INK2, "axes.edgecolor": GRID, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
    "axes.spines.right": False, "font.size": 9, "axes.titlesize": 10,
})


def main():
    perm = pd.read_csv(PROCESSED / "building_permits_q.csv").query("geo=='ES'")
    perm["p"] = pd.PeriodIndex(perm["time"].str.replace("-", ""), freq="Q")
    perm = perm.set_index("p")["value"].sort_index()

    q = pd.read_csv(GOLD / "gold_ccaa_trimestral.csv")
    q["p"] = pd.PeriodIndex(q["anyo"].astype(str) + "Q" + q["quarter"].astype(str), freq="Q")
    ipv = q[q.ccaa == "Nacional"].set_index("p")["ipv_idx15"].sort_index()

    df = pd.DataFrame({"dlog_ipv": np.log(ipv).diff(),
                       "perm_yoy": perm.pct_change(4)}).dropna()

    leads = range(0, 13)
    xc = pd.Series({k: df["dlog_ipv"].corr(df["perm_yoy"].shift(k)) for k in leads})
    xc.rename_axis("adelanto_trimestres").rename("corr").to_csv(FIG / "oferta_nueva_xcorr.csv")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2), width_ratios=[3, 2])
    ax1.set_yscale("log")
    ax1.plot(perm.index.to_timestamp(), perm.values, color=GREEN, lw=1.8)
    ax1.plot(ipv.index.to_timestamp(), ipv.values, color=BLUE, lw=1.8)
    ax1.annotate("permisos de vivienda\n(2021=100, escala log)",
                 (perm.index[-30].to_timestamp(), 60), color=GREEN, fontsize=8)
    ax1.annotate("IPV (2015=100)", (ipv.index[8].to_timestamp(), 150), color=BLUE, fontsize=8)
    ax1.annotate("mínimo de permisos 2013Q2;\nmínimo del IPV 3 trimestres después (2014Q1)",
                 (pd.Period("2011Q1", freq="Q").to_timestamp(), 700), color=INK2, fontsize=8)
    ax1.set_title("Permisos residenciales vs IPV — el colapso 1042→44 precede al suelo de precios")
    ax2.bar(xc.index, xc.values, color=GREEN, width=0.7)
    ax2.axhline(0, color=INK2, lw=0.8)
    ax2.set_xlabel("adelanto de los permisos (trimestres)")
    ax2.set_ylabel("corr con Δlog IPV")
    best = int(xc.idxmax())
    ax2.set_title(f"Correlación adelantada: máximo r={xc.max():.2f} con {best} trimestres")
    fig.tight_layout()
    fig.savefig(FIG / "f8_oferta_nueva.png")
    plt.close(fig)

    print("xcorr permisos→ΔlogIPV por adelanto:", xc.round(3).to_dict())
    print(f"máximo: r={xc.max():.3f} en k={best} trimestres (≈{best*3} meses)")
    giro_perm = perm.loc["2012Q1":"2015Q4"].idxmin()
    giro_ipv = ipv.loc["2012Q1":"2016Q4"].idxmin()
    print(f"mínimo de permisos: {giro_perm}; mínimo del IPV: {giro_ipv} → adelanto {(giro_ipv - giro_perm)}")


if __name__ == "__main__":
    main()
