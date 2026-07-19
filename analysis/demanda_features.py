"""Contest de VALIDACIÓN de las capas de demanda/suelo nuevas (Tier 1+2).

Mismo protocolo pre-registrado que candidatos_t1: orígenes 2019Q4–2023Q4,
h=1–8, test 2024+ intocable, criterio reforzado = batir al drift en ≥12/17
CCAA a h≤4. Candidato único: el MISMO LightGBM global de C2 (hiperparámetros
idénticos, sin tunear) + features nuevas conocidas en el origen:

- compraventas y hipotecas (INE mensual→trimestral, YoY, retardo 1T por
  calendario de publicación),
- Δ población trimestral YoY (ECP, retardo 1T),
- superficie de transacciones de suelo YoY (MITMA, retardo 2T: el Boletín
  publica con ~1-2 trimestres),
- criterios de crédito vivienda (ECB BLS, nacional, retardo 1T),
- Google Trends "comprar piso" (nacional, medias trimestrales, retardo 1T;
  añada congelada, caveat en el conector).

Si no bate al drift, se declara y el modelo de producción NO cambia (igual
que las 3 derrotas anteriores). Si bate, queda como hipótesis para 2026+,
nunca adopción retroactiva.

    python3 analysis/demanda_features.py   (~5 min)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from backtest_t1 import OUT, backtest, load_series, summarize
from candidates_t1 import FEATS, PANEL, PROCESSED


def _q(df: pd.DataFrame, valcol: str = "valor") -> pd.DataFrame:
    df = df.copy()
    df["quarter"] = (df.mes - 1) // 3 + 1
    return df.groupby(["ccaa", "anyo", "quarter"], as_index=False)[valcol].sum()


def build_features() -> pd.DataFrame:
    def pidx(d):
        return pd.PeriodIndex(d.anyo.astype(int).astype(str) + "Q" + d.quarter.astype(int).astype(str), freq="Q")

    cv = _q(pd.read_csv(PROCESSED / "ine_compraventas_ccaa.csv"))
    hip = _q(pd.read_csv(PROCESSED / "ine_hipotecas_ccaa.csv"))
    pob = pd.read_csv(PROCESSED / "ine_poblacion_q_ccaa.csv")
    su = pd.read_csv(PROCESSED / "mitma_suelo_ccaa.csv").query("variable=='superficie_miles_m2'")
    bls = pd.read_csv(PROCESSED / "bls_criterios_vivienda.csv")
    gt = pd.read_csv(PROCESSED / "gtrends_vivienda.csv").query("keyword=='comprar piso'")

    frames = []
    for name, d, col, lag in [("cv_yoy", cv, "valor", 1), ("hip_yoy", hip, "valor", 1),
                              ("pob_yoy", pob, "valor", 1), ("suelo_yoy", su, "valor", 2)]:
        d = d.copy()
        d["p"] = pidx(d)
        s = d.set_index(["ccaa", "p"])[col].sort_index()
        yoy = s.groupby("ccaa").pct_change(4)
        f = yoy.groupby("ccaa").shift(lag).rename(name).reset_index()
        frames.append(f)
    out = frames[0]
    for f in frames[1:]:
        out = out.merge(f, on=["ccaa", "p"], how="outer")

    bls["p"] = pidx(bls)
    b = bls.set_index("p").pct_neto_endurecimiento.shift(1).rename("bls_l1").reset_index()
    gt = gt.copy()
    gt["mes"] = pd.to_datetime(gt.mes)
    gt["p"] = gt.mes.dt.to_period("Q")
    g = gt.groupby("p").indice.mean().pct_change(4).shift(1).rename("gt_yoy_l1").reset_index()
    out = out.merge(b, on="p", how="left").merge(g, on="p", how="left")
    return out


NEW_FEATS = ["cv_yoy", "hip_yoy", "pob_yoy", "suelo_yoy", "bls_l1", "gt_yoy_l1"]


def make_gbm_demanda():
    extra = build_features()
    pan = PANEL.merge(extra, on=["ccaa", "p"], how="left")
    feats = FEATS[:-1] + NEW_FEATS + ["ccaa"]
    cache: dict = {}
    series = load_series()

    def gbm(train: pd.Series, h_total: int) -> list[float]:
        t0 = train.index[-1]
        name = next((c for c, s in series.items()
                     if len(s) and s.index[-1] >= t0 and s[s.index <= t0].equals(train)), None)
        if name is None:
            return [np.nan] * h_total
        out = []
        for h in range(1, h_total + 1):
            key = (t0, h)
            if key not in cache:
                p2 = pan.copy()
                p2["target"] = p2.groupby("ccaa")["logy"].shift(-h) - p2["logy"]
                fit = p2[(p2["p"] + h <= t0) & p2["target"].notna()].dropna(subset=FEATS[:-1])
                m = LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=15,
                                  min_child_samples=20, subsample=0.9, colsample_bytree=0.9,
                                  random_state=42, verbose=-1)
                m.fit(fit[feats].astype({"ccaa": "category"}), fit["target"])
                cache[key] = m
            row = pan[(pan["ccaa"] == name) & (pan["p"] == t0)]
            if row.empty or row[FEATS[:-1]].isna().any(axis=None):
                out.append(np.nan)
                continue
            pred = cache[key].predict(row[feats].astype({"ccaa": "category"}))[0]
            out.append(float(np.exp(np.log(train.iloc[-1]) + pred)))
        return out

    return gbm


def main() -> None:
    series = load_series()
    df = backtest(series, {"gbm_demanda": make_gbm_demanda()})
    df.to_csv(OUT / "demanda_errores.csv", index=False)
    summ = summarize(df)
    print(summ.pivot(index="h", columns="metodo", values="MASE").round(3).to_string())

    be = pd.read_csv(OUT / "backtest_errores.csv")
    drift_ccaa = (be[(be.metodo == "drift") & (be.h <= 4)].assign(m=lambda d: d.ae / d.scale)
                  .groupby("ccaa")["m"].mean())
    cand = (df[df.h <= 4].assign(m=lambda d: d.ae / d.scale).groupby("ccaa")["m"].mean())
    comp = (cand < drift_ccaa).drop(labels=["Nacional"], errors="ignore")
    print(f"\nCriterio reforzado: gbm_demanda bate al drift en {int(comp.sum())}/17 CCAA "
          f"(MASE h<=4 {cand.mean():.3f} vs drift {drift_ccaa.mean():.3f})")
    old = pd.read_csv(OUT / "candidatos_errores.csv")
    gbm_old = (old[(old.metodo == "gbm") & (old.h <= 4)].assign(m=lambda d: d.ae / d.scale)
               .groupby("ccaa")["m"].mean())
    print(f"Referencia GBM sin capas nuevas: MASE h<=4 = {gbm_old.mean():.3f}")
    for h0, h1 in [(5, 8)]:
        c58 = (df[df.h.between(h0, h1)].assign(m=lambda d: d.ae / d.scale)).m.mean()
        d58 = (be[(be.metodo == "drift") & (be.h.between(h0, h1))].assign(m=lambda d: d.ae / d.scale)).m.mean()
        print(f"h{h0}-{h1}: gbm_demanda {c58:.3f} vs drift {d58:.3f} (solo informativo)")


if __name__ == "__main__":
    main()
