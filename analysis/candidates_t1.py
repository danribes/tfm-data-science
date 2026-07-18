"""Candidatos T1 sobre la parrilla pre-registrada (Entrega 4 §3, EDA D1–D3).

C1a  SARIMAX univariante sobre log-IPV: órdenes {(1,1,1),(2,1,0)} con deriva,
     elegido por AIC dentro de cada train (sin tocar validación).
C1b  SARIMAX + exógena Euríbor en t−3 (D3). Para h>3 el valor futuro de la
     exógena no existe en el origen: se congela en el último conocido
     (pronóstico condicionado a "tipos constantes", declarado).
C2   LightGBM global directo por horizonte: objetivo log(y[t+h]) − log(y[t]),
     features en t (conocidas en t): Δlog IPV rezagos 0–3, trimestre, CCAA
     (categórica), Euríbor nivel y Δ, Δlog IPC, crecimiento salarial
     interanual en t−6 (rango D3, retardo compatible con la publicación EES).

Mismos orígenes/horizontes que los baselines; el test final sigue intocable.

    python3 analysis/candidates_t1.py     (~3-5 min)
"""
from __future__ import annotations

import pathlib
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from statsmodels.tsa.statespace.sarimax import SARIMAX

from backtest_t1 import GOLD, OUT, ORIGINS, TEST_START, H, backtest, load_series, summarize

warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "storage" / "processed"

BLUE, GREEN, ORANGE, VIOLET, RED = "#2a78d6", "#008300", "#eb6834", "#4a3aa7", "#e34948"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e5e4e0"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "savefig.dpi": 150,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2,
    "ytick.color": INK2, "axes.edgecolor": GRID, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
    "axes.spines.right": False, "font.size": 9, "axes.titlesize": 10,
})

ORDERS = [(1, 1, 1), (2, 1, 0)]


def load_exog() -> pd.Series:
    eur = pd.read_csv(PROCESSED / "euribor_12m.csv")
    eur["p"] = pd.PeriodIndex(eur["month"], freq="M").asfreq("Q")
    return eur.groupby("p")["euribor_12m"].mean().sort_index()


EUR = load_exog()


# ---------- C1a: SARIMAX univariante ----------

def sarimax_u(train: pd.Series, h: int) -> list[float]:
    y = np.log(train.astype(float))
    best, best_aic = None, np.inf
    for order in ORDERS:
        try:
            r = SARIMAX(y, order=order, trend="c").fit(disp=False, maxiter=200)
            if r.aic < best_aic:
                best, best_aic = r, r.aic
        except Exception:
            continue
    if best is None:
        return [np.nan] * h
    return list(np.exp(best.forecast(h)))


# ---------- C1b: SARIMAX + Euríbor t−3 (congelado más allá de lo conocido) ----------

def sarimax_x(train: pd.Series, h: int) -> list[float]:
    y = np.log(train.astype(float))
    t0 = train.index[-1]
    x_train = EUR.shift(3).reindex(train.index)
    if x_train.isna().any():
        return [np.nan] * h
    fut_idx = pd.period_range(t0 + 1, t0 + h, freq="Q")
    x_fut = EUR.shift(3).reindex(fut_idx)
    x_fut = x_fut.where(fut_idx <= t0 + 3, np.nan).fillna(float(EUR.loc[t0]))
    best, best_aic = None, np.inf
    for order in ORDERS:
        try:
            r = SARIMAX(y, exog=x_train, order=order, trend="c").fit(disp=False, maxiter=200)
            if r.aic < best_aic:
                best, best_aic = r, r.aic
        except Exception:
            continue
    if best is None:
        return [np.nan] * h
    return list(np.exp(best.forecast(h, exog=x_fut)))


# ---------- C2: LightGBM global, estrategia directa por horizonte ----------

def build_panel() -> pd.DataFrame:
    q = pd.read_csv(GOLD / "gold_ccaa_trimestral.csv")
    q["p"] = pd.PeriodIndex(q["anyo"].astype(str) + "Q" + q["quarter"].astype(str), freq="Q")
    q = q[(q["p"] >= pd.Period("2008Q1", freq="Q")) & (q["p"] <= pd.Period("2025Q4", freq="Q"))]
    rows = []
    for c, d in q.groupby("ccaa"):
        d = d.sort_values("p").set_index("p")
        if d["ipv_idx15"].dropna().shape[0] < 60:
            continue
        f = pd.DataFrame(index=d.index)
        ly = np.log(d["ipv_idx15"])
        f["ccaa"] = c
        f["logy"] = ly
        for k in range(4):
            f[f"dlog_l{k}"] = ly.diff().shift(k)
        f["q"] = f.index.quarter
        f["eur"] = EUR.reindex(f.index)
        f["d_eur"] = EUR.diff().reindex(f.index)
        f["dlog_ipc"] = np.log(d["ipc"]).diff()
        f["sal_yoy_l6"] = d["salario_idx15"].pct_change(4).shift(6)
        rows.append(f.reset_index().rename(columns={"index": "p"}))
    return pd.concat(rows, ignore_index=True)


PANEL = build_panel()
FEATS = ["dlog_l0", "dlog_l1", "dlog_l2", "dlog_l3", "q", "eur", "d_eur",
         "dlog_ipc", "sal_yoy_l6", "ccaa"]


def make_gbm_forecaster():
    cache: dict = {}

    def gbm(train: pd.Series, h_total: int) -> list[float]:
        t0 = train.index[-1]
        ccaa = [c for c, s in _SERIES.items()
                if len(s) and s.index[-1] >= t0 and s[s.index <= t0].equals(train)]
        name = ccaa[0] if ccaa else None
        if name is None:
            return [np.nan] * h_total
        out = []
        for h in range(1, h_total + 1):
            key = (t0, h)
            if key not in cache:
                pan = PANEL.copy()
                pan["target"] = pan.groupby("ccaa")["logy"].shift(-h) - pan["logy"]
                fit = pan[(pan["p"] + h <= t0) & pan["target"].notna()].dropna(subset=FEATS[:-1])
                m = LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=15,
                                  min_child_samples=20, subsample=0.9, colsample_bytree=0.9,
                                  random_state=42, verbose=-1)
                m.fit(fit[FEATS].astype({"ccaa": "category"}), fit["target"])
                cache[key] = m
            row = PANEL[(PANEL["ccaa"] == name) & (PANEL["p"] == t0)]
            if row.empty or row[FEATS[:-1]].isna().any(axis=None):
                out.append(np.nan)
                continue
            pred = cache[key].predict(row[FEATS].astype({"ccaa": "category"}))[0]
            out.append(float(np.exp(np.log(train.iloc[-1]) + pred)))
        return out

    return gbm


_SERIES = load_series()


def main():
    forecasters = {"sarimax": sarimax_u, "sarimax_eur": sarimax_x, "gbm": make_gbm_forecaster()}
    df = backtest(_SERIES, forecasters)
    df.to_csv(OUT / "candidatos_errores.csv", index=False)
    summ = summarize(df)
    summ.to_csv(OUT / "candidatos_resumen.csv", index=False)

    base = pd.read_csv(OUT / "backtest_resumen.csv")
    todo = pd.concat([base, summ])
    piv = todo.pivot(index="h", columns="metodo", values="MASE").round(3)
    print(piv.to_string())

    # criterio reforzado: batir al drift por CCAA en h<=4 (17 CCAA, sin Nacional)
    be = pd.read_csv(OUT / "backtest_errores.csv")
    drift_ccaa = (be[(be.metodo == "drift") & (be.h <= 4)].assign(m=lambda d: d.ae / d.scale)
                  .groupby("ccaa")["m"].mean())
    print("\nCriterio reforzado (batir al drift, h<=4, por CCAA, sin Nacional):")
    for name in forecasters:
        cand = (df[(df.metodo == name) & (df.h <= 4)].assign(m=lambda d: d.ae / d.scale)
                .groupby("ccaa")["m"].mean())
        comp = (cand < drift_ccaa).drop(labels=["Nacional"], errors="ignore")
        print(f"  {name}: bate al drift en {int(comp.sum())}/17 CCAA "
              f"(MASE medio h<=4 = {cand.mean():.3f} vs drift {drift_ccaa.mean():.3f})")

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    colors = {"drift": GREEN, "snaive": BLUE, "sarimax": VIOLET,
              "sarimax_eur": ORANGE, "gbm": RED}
    for name, color in colors.items():
        d = todo[todo.metodo == name]
        if d.empty:
            continue
        ax.plot(d.h, d.MASE, color=color, lw=1.8, marker="o", ms=4, label=name)
    ax.axhline(1.0, color=INK2, lw=0.8, ls="--")
    ax.set_xlabel("horizonte (trimestres)")
    ax.set_ylabel("MASE (media sobre CCAA × orígenes)")
    ax.set_title("Candidatos T1 vs baselines — validación rolling-origin")
    ax.legend(frameon=False, ncols=2)
    fig.tight_layout()
    fig.savefig(OUT / "b2_mase_candidatos.png")
    plt.close(fig)
    print(f"\n→ {OUT.relative_to(ROOT)}: candidatos_errores.csv, candidatos_resumen.csv, b2_mase_candidatos.png")


if __name__ == "__main__":
    main()
