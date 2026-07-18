"""Harness de backtesting rolling-origin de T1 + baselines (Entrega 4 §7).

Diseño pre-registrado: orígenes 2019Q4→2023Q4, horizontes h=1–8, métrica
principal MASE con escala naive-estacional in-sample. Los ÚLTIMOS 8 trimestres
(2024Q1–2025Q4) son el test final y se evalúan UNA vez con el modelo ganador;
este script solo toca los orígenes de validación.

Los candidatos (SARIMAX, LightGBM) se enchufan con la misma firma que los
baselines: forecaster(train: pd.Series, h: int) -> list[float].

    python3 analysis/backtest_t1.py
"""
from __future__ import annotations

import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOLD = ROOT / "storage" / "gold"
OUT = ROOT / "docs" / "figures" / "backtest"
OUT.mkdir(parents=True, exist_ok=True)

BLUE, GREEN, ORANGE = "#2a78d6", "#008300", "#eb6834"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e5e4e0"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "savefig.dpi": 150,
    "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2,
    "axes.edgecolor": GRID, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 9, "axes.titlesize": 10,
})

H = 8
ORIGINS = pd.period_range("2019Q4", "2023Q4", freq="Q")
TEST_START = pd.Period("2024Q1", freq="Q")  # intocable hasta la evaluación final


# ---------- baselines (misma firma que tendrán los candidatos) ----------

def snaive(train: pd.Series, h: int) -> list[float]:
    """Naive estacional: mismo trimestre del año anterior, recursivo si h>4."""
    out = []
    for k in range(1, h + 1):
        idx = train.index[-1] + k
        while idx > train.index[-1]:
            idx -= 4
        out.append(float(train.loc[idx]) if idx in train.index else np.nan)
        # si h>4, el valor "del año anterior" puede ser a su vez un pronóstico
        if k > 4:
            out[-1] = out[k - 4 - 1]
    return out


def drift(train: pd.Series, h: int) -> list[float]:
    """Tendencia lineal reciente: pendiente de los últimos 8 trimestres."""
    k = min(8, len(train) - 1)
    slope = (train.iloc[-1] - train.iloc[-1 - k]) / k
    return [float(train.iloc[-1] + slope * j) for j in range(1, h + 1)]


def naive(train: pd.Series, h: int) -> list[float]:
    """Último valor (referencia informal, no pre-registrada)."""
    return [float(train.iloc[-1])] * h


BASELINES = {"snaive": snaive, "drift": drift, "naive": naive}


# ---------- harness ----------

def load_series() -> dict[str, pd.Series]:
    q = pd.read_csv(GOLD / "gold_ccaa_trimestral.csv")
    q = q[q["ratio_asequibilidad"].notna() | (q["ccaa"] == "Nacional")]
    q["p"] = pd.PeriodIndex(q["anyo"].astype(str) + "Q" + q["quarter"].astype(str), freq="Q")
    q = q[(q["p"] >= pd.Period("2008Q1", freq="Q")) & (q["p"] <= pd.Period("2025Q4", freq="Q"))]
    out = {}
    for c, d in q.groupby("ccaa"):
        s = d.set_index("p")["ipv_idx15"].dropna().sort_index()
        if len(s) >= 60:
            out[c] = s
    return out


def mase_scale(train: pd.Series) -> float:
    return float(train.diff(4).abs().mean())


def backtest(series: dict[str, pd.Series], forecasters: dict) -> pd.DataFrame:
    rows = []
    for ccaa, s in series.items():
        for t0 in ORIGINS:
            train = s[s.index <= t0]
            scale = mase_scale(train)
            for name, f in forecasters.items():
                preds = f(train, H)
                for h, yhat in enumerate(preds, start=1):
                    t = t0 + h
                    if t not in s.index or t >= TEST_START or np.isnan(yhat):
                        continue  # el test final (2024Q1→) queda intocable
                    rows.append({"ccaa": ccaa, "origen": str(t0), "h": h,
                                 "metodo": name, "y": float(s.loc[t]),
                                 "yhat": yhat, "scale": scale})
    df = pd.DataFrame(rows)
    df["ae"] = (df.y - df.yhat).abs()
    df["e"] = df.y - df.yhat
    return df


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    g = (df.groupby(["metodo", "h"])
           .apply(lambda d: pd.Series({
               "MASE": (d.ae / d.scale).mean(),
               "MAE": d.ae.mean(),
               "RMSE": np.sqrt((d.e ** 2).mean()),
               "sesgo": d.e.mean(),
               "n": len(d)}), include_groups=False)
           .reset_index())
    return g


def main():
    series = load_series()
    df = backtest(series, BASELINES)
    df.to_csv(OUT / "backtest_errores.csv", index=False)
    summ = summarize(df)
    summ.to_csv(OUT / "backtest_resumen.csv", index=False)

    fig, ax = plt.subplots(figsize=(7.5, 4))
    for name, color in [("snaive", BLUE), ("drift", GREEN), ("naive", ORANGE)]:
        d = summ[summ.metodo == name]
        ax.plot(d.h, d.MASE, color=color, lw=1.8, marker="o", ms=4, label=name)
    ax.axhline(1.0, color=INK2, lw=0.8, ls="--")
    ax.set_xlabel("horizonte (trimestres)")
    ax.set_ylabel("MASE (media sobre CCAA × orígenes)")
    ax.set_title("Baselines T1 en validación rolling-origin (2019Q4–2023Q4) — la vara a batir")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "b1_mase_baselines.png")
    plt.close(fig)

    print(f"{len(series)} series; {df.origen.nunique()} orígenes; {len(df)} errores puntuales")
    piv = summ.pivot(index="h", columns="metodo", values="MASE").round(3)
    print(piv.to_string())
    h4 = summ[(summ.h <= 4)].groupby("metodo")["MASE"].mean().round(3)
    print("\nMASE medio h≤4:", h4.to_dict())
    mejor = h4.idxmin()
    print(f"→ vara a batir (criterio de aceptación, h≤4): {mejor} = {h4.min():.3f}")


if __name__ == "__main__":
    main()
