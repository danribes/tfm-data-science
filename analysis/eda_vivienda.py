"""EDA §2-A de la Entrega 4: análisis exploratorio del panel de vivienda.

Produce las figuras del MVP (docs/figures/eda/) y los diagnósticos que fijan
las tres decisiones de especificación de T1 (transformación, pooling, exógenas).
Los resultados numéricos se guardan junto a las figuras (adf_table.csv,
xcorr_table.csv) para que el documento de hallazgos sea trazable.

    python3 analysis/eda_vivienda.py
"""
from __future__ import annotations

import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import adfuller

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOLD = ROOT / "storage" / "gold"
PROCESSED = ROOT / "storage" / "processed"
FIG = ROOT / "docs" / "figures" / "eda"
FIG.mkdir(parents=True, exist_ok=True)

# paleta (referencia dataviz, validada): azul serie-1, verde serie-2
BLUE, GREEN = "#2a78d6", "#008300"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e5e4e0"
CCAA_ORD = None  # se fija tras cargar (orden por ratio 2024, reutilizado en todas las figuras)

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "savefig.dpi": 150,
    "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2,
    "axes.edgecolor": GRID, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 9, "axes.titlesize": 10, "figure.titlesize": 12,
})


def load():
    q = pd.read_csv(GOLD / "gold_ccaa_trimestral.csv")
    q["t"] = pd.PeriodIndex(q["anyo"].astype(str) + "Q" + q["quarter"].astype(str), freq="Q").to_timestamp()
    a = pd.read_csv(GOLD / "gold_asequibilidad_ccaa.csv")
    eur = pd.read_csv(PROCESSED / "euribor_12m.csv")
    eur["t"] = pd.PeriodIndex(eur["month"], freq="M").to_timestamp()
    eur = (eur.set_index("t")["euribor_12m"].resample("QS").mean()
           .rename("euribor").reset_index())
    return q, a, eur


def fig1_heatmap(a: pd.DataFrame, order: list[str]):
    piv = a.pivot(index="ccaa", columns="anyo", values="ratio_asequibilidad").loc[order]
    cmap = LinearSegmentedColormap.from_list("seq_blue", ["#f2f7fd", BLUE, "#123a6b"])
    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    im = ax.imshow(piv.values, aspect="auto", cmap=cmap)
    ax.set_xticks(range(len(piv.columns)), piv.columns, rotation=45)
    ax.set_yticks(range(len(piv.index)), piv.index)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.85)
    cb.set_label("IPV / salario (índices 2015=100)", color=INK2)
    ax.set_title("Ratio de asequibilidad por CCAA y año (2008–2024) — mayor = menos asequible")
    fig.tight_layout()
    fig.savefig(FIG / "f1_heatmap_ratio_ccaa.png")
    plt.close(fig)


def fig2_nacional(q: pd.DataFrame):
    nac = q[q.ccaa == "Nacional"].sort_values("t")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.5, 5.6), sharex=True,
                                   height_ratios=[2, 1])
    obs = nac.salario_flag == "observado"
    ax1.plot(nac.t, nac.ipv_idx15, color=BLUE, lw=1.8)
    ax1.plot(nac.t[obs], nac.salario_idx15[obs], color=GREEN, lw=1.8)
    ax1.plot(nac.t[~obs & (nac.t >= nac.t[obs].max())], nac.salario_idx15[~obs & (nac.t >= nac.t[obs].max())],
             color=GREEN, lw=1.5, ls=(0, (3, 3)))
    ax1.annotate("provisional\n(EES publica con ~1,5 años de retraso)",
                 (nac.t.iloc[-1], nac.salario_idx15.iloc[-1]), color=GREEN, fontsize=7,
                 xytext=(-10, -22), textcoords="offset points", ha="right")
    ax1.annotate("IPV", (nac.t.iloc[-1], nac.ipv_idx15.iloc[-1]), color=BLUE,
                 xytext=(6, 0), textcoords="offset points", va="center", fontweight="bold")
    ax1.annotate("Salario", (nac.t.iloc[-1], nac.salario_idx15.iloc[-1]), color=GREEN,
                 xytext=(6, 0), textcoords="offset points", va="center", fontweight="bold")
    ax1.legend(["IPV (2015=100)", "Salario indexado (2015=100)"], frameon=False, loc="upper left")
    ax1.set_title("España: precio de la vivienda vs salario (índices, 2015=100)")
    ax2.plot(nac.t, nac.ratio_asequibilidad, color=BLUE, lw=1.8)
    ax2.axhline(1.0, color=INK2, lw=0.8, ls="--")
    ax2.set_title("Ratio de asequibilidad (IPV/salario) — indicador aproximado")
    fig.tight_layout()
    fig.savefig(FIG / "f2_nacional_ipv_salario.png")
    plt.close(fig)


def fig3_ranking(a: pd.DataFrame, order: list[str]):
    r24 = a[a.anyo == 2024].set_index("ccaa").loc[order, "ratio_asequibilidad"]
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    y = np.arange(len(r24))[::-1]
    ax.barh(y, r24.values, color=BLUE, height=0.62)
    ax.set_yticks(y, r24.index)
    for yi, v in zip(y, r24.values):
        ax.annotate(f"{v:.2f}", (v, yi), xytext=(4, 0), textcoords="offset points",
                    va="center", fontsize=8, color=INK2)
    ax.axvline(1.0, color=INK2, lw=0.8, ls="--")
    ax.set_xlim(0, r24.max() * 1.12)
    ax.grid(axis="y", visible=False)
    ax.set_title("Ratio de asequibilidad 2024 por CCAA (2015=100; >1 = peor que en 2015)")
    fig.tight_layout()
    fig.savefig(FIG / "f3_ranking_2024.png")
    plt.close(fig)


def fig4_small_multiples(q: pd.DataFrame, order: list[str]):
    nac = q[q.ccaa == "Nacional"].sort_values("t")
    ccaa17 = [c for c in order if c != "Nacional"]
    fig, axes = plt.subplots(5, 4, figsize=(10.5, 9), sharex=True, sharey=True)
    for ax, c in zip(axes.flat, ccaa17):
        d = q[q.ccaa == c].sort_values("t")
        ax.plot(nac.t, nac.ratio_asequibilidad, color=GRID, lw=1.2)
        ax.plot(d.t, d.ratio_asequibilidad, color=BLUE, lw=1.6)
        ax.set_title(c, fontsize=8)
        ax.axhline(1.0, color=INK2, lw=0.5, ls="--")
    for ax in axes.flat[len(ccaa17):]:
        ax.axis("off")
    fig.suptitle("Ratio de asequibilidad por CCAA (azul) frente a Nacional (gris), 2008–2025",
                 y=0.995)
    fig.tight_layout()
    fig.savefig(FIG / "f4_small_multiples_ratio.png")
    plt.close(fig)


def diagnostics(q: pd.DataFrame) -> pd.DataFrame:
    """ADF por CCAA en nivel y en Δlog del IPV → decisión de transformación."""
    rows = []
    for c, d in q.sort_values("t").groupby("ccaa"):
        s = d.set_index("t")["ipv_idx15"].dropna()
        if len(s) < 40:
            continue
        p_lvl = adfuller(s, autolag="AIC")[1]
        p_dlog = adfuller(np.log(s).diff().dropna(), autolag="AIC")[1]
        rows.append({"ccaa": c, "n": len(s), "adf_p_nivel": round(p_lvl, 3),
                     "adf_p_dlog": round(p_dlog, 3)})
    t = pd.DataFrame(rows)
    t.to_csv(FIG / "adf_table.csv", index=False)
    return t


def fig5_stl_acf(q: pd.DataFrame):
    nac = q[q.ccaa == "Nacional"].sort_values("t").set_index("t")
    dlog = np.log(nac["ipv_idx15"]).diff().dropna()
    stl = STL(nac["ipv_idx15"].dropna(), period=4).fit()
    fig = stl.plot()
    fig.set_size_inches(8.5, 6)
    for ax in fig.axes:
        for line in ax.get_lines():
            line.set_color(BLUE)
            line.set_linewidth(1.4)
    fig.suptitle("STL del IPV nacional (periodo 4): tendencia domina, estacionalidad débil", y=1.0)
    fig.tight_layout()
    fig.savefig(FIG / "f5_stl_nacional.png")
    plt.close(fig)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.5, 3.2))
    plot_acf(dlog, ax=ax1, lags=16, color=BLUE, vlines_kwargs={"colors": BLUE})
    plot_pacf(dlog, ax=ax2, lags=16, method="ywm", color=BLUE, vlines_kwargs={"colors": BLUE})
    ax1.set_title("ACF de Δlog IPV nacional")
    ax2.set_title("PACF de Δlog IPV nacional")
    fig.tight_layout()
    fig.savefig(FIG / "f6_acf_pacf_dlog.png")
    plt.close(fig)
    return dlog


def xcorr(q: pd.DataFrame, eur: pd.DataFrame) -> pd.DataFrame:
    """Correlación cruzada de Δlog IPV nacional con las exógenas candidatas."""
    nac = q[q.ccaa == "Nacional"].sort_values("t").set_index("t")
    df = pd.DataFrame({
        "dlog_ipv": np.log(nac["ipv_idx15"]).diff(),
        "dlog_ipc": np.log(nac["ipc"]).diff(),
        "d_salario": nac["salario_idx15"].pct_change(),
    })
    df = df.join(eur.set_index("t")["euribor"]).assign(d_euribor=lambda x: x.euribor.diff())
    rows = []
    for var in ["euribor", "d_euribor", "dlog_ipc", "d_salario"]:
        for lag in range(0, 9):
            r = df["dlog_ipv"].corr(df[var].shift(lag))
            rows.append({"exogena": var, "retardo_trimestres": lag, "corr": round(r, 3)})
    t = pd.DataFrame(rows)
    t.to_csv(FIG / "xcorr_table.csv", index=False)

    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    for var, color, label in [("euribor", BLUE, "Euríbor (nivel)"),
                              ("d_euribor", GREEN, "Δ Euríbor")]:
        d = t[t.exogena == var]
        ax.plot(d.retardo_trimestres, d["corr"], color=color, lw=1.8, marker="o", ms=4, label=label)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xlabel("retardo (trimestres): exógena en t−k frente a Δlog IPV en t")
    ax.set_title("Correlación cruzada del crecimiento del IPV nacional con el Euríbor")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "f7_xcorr_euribor.png")
    plt.close(fig)
    return t


def main():
    q, a, eur = load()
    order = (a[a.anyo == 2024].sort_values("ratio_asequibilidad", ascending=False)["ccaa"].tolist())
    fig1_heatmap(a, order)
    fig2_nacional(q)
    fig3_ranking(a, order)
    fig4_small_multiples(q, order)
    adf = diagnostics(q)
    fig5_stl_acf(q)
    xc = xcorr(q, eur)

    n_lvl = (adf["adf_p_nivel"] > 0.05).sum()
    n_dlog = (adf["adf_p_dlog"] <= 0.05).sum()
    print(f"ADF: {n_lvl}/{len(adf)} series NO estacionarias en nivel (p>0.05); "
          f"{n_dlog}/{len(adf)} estacionarias en Δlog (p<=0.05)")
    top = a[a.anyo == 2024].nlargest(3, "ratio_asequibilidad")[["ccaa", "ratio_asequibilidad"]]
    print("Top-3 presión 2024:", top.to_dict("records"))
    best = xc.loc[xc.groupby("exogena")["corr"].apply(lambda s: s.abs().idxmax())]
    print("Mejor retardo por exógena:\n", best.to_string(index=False))
    disp = a[a.anyo == 2024]["ratio_asequibilidad"]
    print(f"Dispersión regional 2024: min {disp.min():.2f} — max {disp.max():.2f}")
    print(f"→ {FIG.relative_to(ROOT)}: 7 figuras + adf_table.csv + xcorr_table.csv")


if __name__ == "__main__":
    main()
