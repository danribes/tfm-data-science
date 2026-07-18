"""TEST FINAL T1 — evaluación de un solo uso sobre 2024Q1–2025Q4.

Protocolo declarado ANTES de mirar (docs/candidatos_t1.md §3 y §5):
- Se evalúan EXACTAMENTE dos métodos: drift (modelo de producción h≤4 según
  validación) y GBM global (hipótesis post-hoc: gana en h≥6). Los SARIMAX
  quedaron eliminados en validación y no reciben evaluación de test.
- Único origen: 2023Q4. Horizontes h=1–8 → 2024Q1–2025Q4. Una sola pasada.
- REGLA DE DECISIÓN (fijada aquí, en el código, antes de ejecutar):
  se adopta el híbrido (drift h≤4 + GBM h≥6) si y solo si el GBM bate al
  drift en MASE medio de h=6–8 en ≥12 de las 17 CCAA (Nacional excluido).
  En caso contrario, producción = drift en todos los horizontes.

    python3 analysis/final_test_t1.py
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from backtest_t1 import OUT, drift, load_series, mase_scale
from candidates_t1 import make_gbm_forecaster

BLUE, GREEN, RED = "#2a78d6", "#008300", "#e34948"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e5e4e0"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "savefig.dpi": 150,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2,
    "ytick.color": INK2, "axes.edgecolor": GRID, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
    "axes.spines.right": False, "font.size": 9, "axes.titlesize": 10,
})

T0 = pd.Period("2023Q4", freq="Q")
H = 8


def main():
    series = load_series()
    gbm = make_gbm_forecaster()
    rows = []
    for ccaa, s in series.items():
        train = s[s.index <= T0]
        scale = mase_scale(train)
        preds = {"drift": drift(train, H), "gbm": gbm(train, H)}
        for name, ps in preds.items():
            for h, yhat in enumerate(ps, start=1):
                t = T0 + h
                if t not in s.index or np.isnan(yhat):
                    continue
                rows.append({"ccaa": ccaa, "h": h, "metodo": name, "periodo": str(t),
                             "y": float(s.loc[t]), "yhat": float(yhat), "scale": scale})
    df = pd.DataFrame(rows)
    df["mase"] = (df.y - df.yhat).abs() / df.scale
    df.to_csv(OUT / "test_final_errores.csv", index=False)

    piv = df.groupby(["metodo", "h"])["mase"].mean().unstack(0).round(3)
    print("MASE por horizonte (test final, origen 2023Q4):")
    print(piv.to_string())

    corto = df[df.h <= 4].groupby("metodo")["mase"].mean().round(3)
    largo = df[df.h >= 6].groupby("metodo")["mase"].mean().round(3)
    print(f"\nMASE medio h<=4: {corto.to_dict()}   h>=6: {largo.to_dict()}")

    per = (df[df.h >= 6].groupby(["ccaa", "metodo"])["mase"].mean().unstack()
           .drop(index="Nacional", errors="ignore"))
    gana = (per["gbm"] < per["drift"])
    print(f"\nREGLA DE DECISIÓN — GBM bate al drift en h=6-8 en {int(gana.sum())}/17 CCAA")
    veredicto = "HÍBRIDO drift h<=4 + GBM h>=6" if gana.sum() >= 12 else "DRIFT en todos los horizontes"
    print(f"→ VEREDICTO: {veredicto}")
    per.round(3).to_csv(OUT / "test_final_por_ccaa_h6_8.csv")

    # figura: MASE por h + trayectoria Nacional
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4))
    for name, color in [("drift", GREEN), ("gbm", RED)]:
        d = piv[name]
        ax1.plot(d.index, d.values, color=color, lw=1.8, marker="o", ms=4, label=name)
    ax1.axhline(1.0, color=INK2, lw=0.8, ls="--")
    ax1.set_xlabel("horizonte (trimestres)")
    ax1.set_ylabel("MASE (media sobre las 18 series)")
    ax1.set_title("Test final 2024Q1–2025Q4 (única pasada)")
    ax1.legend(frameon=False)

    s = series["Nacional"]
    hist = s[(s.index >= pd.Period("2021Q1", freq="Q"))]
    ax2.plot(hist.index.to_timestamp(), hist.values, color=BLUE, lw=1.8, label="IPV observado")
    fut = pd.period_range(T0 + 1, T0 + H, freq="Q").to_timestamp()
    train = s[s.index <= T0]
    ax2.plot(fut, drift(train, H), color=GREEN, lw=1.6, ls="--", label="drift")
    ax2.plot(fut, gbm(train, H), color=RED, lw=1.6, ls="--", label="gbm")
    ax2.axvline(T0.to_timestamp(how="end"), color=INK2, lw=0.8)
    ax2.set_title("Nacional: observado vs pronósticos desde 2023Q4")
    ax2.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "b3_test_final.png")
    plt.close(fig)
    print(f"\n→ {OUT}: test_final_errores.csv, test_final_por_ccaa_h6_8.csv, b3_test_final.png")


if __name__ == "__main__":
    main()
