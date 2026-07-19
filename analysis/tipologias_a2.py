"""A2 — Tipologías de gasto público (PCA + clustering sobre composición COFOG).

Pregunta A2 del PLAN_MAESTRO: ¿qué tipologías de gasto existen entre países?
Análisis DESCRIPTIVO: composición funcional del gasto (10 funciones COFOG como
% del gasto total, media 2019–2023, panel europeo), PCA para el mapa y KMeans
con k elegido por silueta. Sin outcome, sin ranking: un mapa de parecidos.

    python3 analysis/tipologias_a2.py
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from backtest_t1 import GOLD

FIG = GOLD.parents[1] / "docs" / "figures" / "a1"

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

GF = [f"te_gf{i:02d}" for i in range(1, 11)]
GF_LABEL = {"te_gf01": "servicios generales", "te_gf02": "defensa", "te_gf03": "orden público",
            "te_gf04": "asuntos económicos", "te_gf05": "medio ambiente", "te_gf06": "vivienda",
            "te_gf07": "sanidad", "te_gf08": "ocio y cultura", "te_gf09": "educación",
            "te_gf10": "protección social"}
AGREGADOS = {"EU27_2020", "EA19", "EA20", "EU28"}


def build_shares() -> pd.DataFrame:
    p = pd.read_csv(GOLD / "gold_panel_anual.csv").query("2019 <= year <= 2023")
    w = (p[p.variable.isin(GF + ["te_total"])]
         .pivot_table(index=["geo", "year"], columns="variable", values="value")
         .dropna())
    geos = w.index.get_level_values("geo")
    w = w[~(geos.isin(AGREGADOS) | geos.str.startswith("EU") | geos.str.startswith("EA"))]
    shares = w[GF].div(w["te_total"], axis=0) * 100
    m = shares.groupby("geo").mean()
    return m[m.notna().all(axis=1)]


def main():
    t = build_shares()
    print(f"{len(t)} países, 10 funciones (shares del gasto total, media 2019–2023)")

    z = StandardScaler().fit_transform(t)
    pca = PCA(n_components=2, random_state=42).fit(z)
    xy = pca.transform(z)

    sils = {}
    for k in range(2, 7):
        km = KMeans(n_clusters=k, n_init=25, random_state=42).fit(z)
        sils[k] = silhouette_score(z, km.labels_)
    k_best = max(sils, key=sils.get)
    km = KMeans(n_clusters=k_best, n_init=25, random_state=42).fit(z)
    print("silueta por k:", {k: round(v, 3) for k, v in sils.items()}, "→ k =", k_best)

    out = t.round(2).copy()
    out["pc1"], out["pc2"] = xy[:, 0].round(3), xy[:, 1].round(3)
    out["cluster"] = km.labels_
    out["silhouette_k"] = k_best
    out.reset_index().to_csv(GOLD / "gold_tipologias_gasto.csv", index=False)

    # perfil de cada clúster: función más sobre-representada vs media
    medias = t.mean()
    perfiles = {}
    for c in range(k_best):
        diff = (t[km.labels_ == c].mean() - medias)
        top = diff.nlargest(2)
        perfiles[c] = " + ".join(f"{GF_LABEL[i]} ({v:+.1f} pp)" for i, v in top.items())
        print(f"clúster {c} ({(km.labels_ == c).sum()} países): {perfiles[c]}")

    colores = [BLUE, GREEN, ORANGE, VIOLET][:k_best]
    fig, ax = plt.subplots(figsize=(9, 6))
    for c in range(k_best):
        m = km.labels_ == c
        ax.scatter(xy[m, 0], xy[m, 1], color=colores[c], s=46,
                   label=f"clúster {c}: {perfiles[c]}")
    for i, geo in enumerate(t.index):
        ax.annotate(geo, (xy[i, 0], xy[i, 1]), fontsize=7.5, color=INK,
                    xytext=(4, 3), textcoords="offset points",
                    fontweight="bold" if geo == "ES" else "normal")
    for j, var in enumerate(GF):
        lo = pca.components_[:, j] * 3.2
        if np.hypot(*lo) > 1.2:
            ax.annotate(GF_LABEL[var], (lo[0], lo[1]), color=INK2, fontsize=7.5,
                        ha="center", style="italic")
            ax.plot([0, lo[0] * 0.85], [0, lo[1] * 0.85], color=GRID, lw=0.9)
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.0%} de la varianza)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.0%})")
    ax.set_title(f"A2 · Tipologías de composición del gasto (COFOG, medias 2019–23) — "
                 f"k={k_best} por silueta ({sils[k_best]:.2f}); mapa descriptivo, no ranking")
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG / "a2_tipologias.png")
    plt.close(fig)

    es = out.loc["ES"]
    print(f"ES: clúster {int(es.cluster)}, PC1 {es.pc1:+.2f}, PC2 {es.pc2:+.2f}; "
          f"proteccion social {es.te_gf10:.1f}% del gasto, sanidad {es.te_gf07:.1f}%")


if __name__ == "__main__":
    main()
