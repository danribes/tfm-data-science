"""Expansión del corpus + contraste DL bajo el MISMO protocolo (LOOCV).

Con las series nuevas (SPI, gasto militar, gasto educativo, HLO, AOD donante):
1. A1-EDUCACIÓN (módulo nuevo): HLO ~ gasto educativo (retardado) + renta +
   urbanización. Candidatos bajo LOOCV: mediana-cuartil, OLS, LightGBM y un
   MLP (el candidato "deep learning", declarado: red poco profunda — con
   n≈100-160 países, más capas solo añaden varianza).
2. A1-SALUD ampliado: mismos controles + SPI (capacidad estadística) y la
   auditoría declarada residual⊥SPI que faltaba por datos.
Regla de aceptación idéntica al proyecto: el flexible debe batir al OLS por
≥10 % de MAE. Nada de test gastado: todo es validación LOOCV.

    python3 analysis/expansion_dl.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.linear_model import LinearRegression
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from backtest_t1 import GOLD

PROCESSED = GOLD.parent / "processed"
FECHA = "2026-07-19"


def block(df, var, y0, y1):
    d = df[(df.variable == var) & (df.year.between(y0, y1))]
    return d.groupby("iso3").value.mean()


def loocv_mae(t: pd.DataFrame, feats: list[str], y: str) -> dict[str, float]:
    X, yv = t[feats], t[y]
    modelos = {
        "mediana_grupo": None,
        "ols": lambda: make_pipeline(StandardScaler(), LinearRegression()),
        "gbm": lambda: LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=7,
                                     min_child_samples=10, random_state=42, verbose=-1),
        "mlp": lambda: make_pipeline(StandardScaler(), MLPRegressor(
            hidden_layer_sizes=(32, 16), max_iter=4000, random_state=42,
            early_stopping=False, alpha=1e-2)),
    }
    errs = {m: [] for m in modelos}
    for iso in t.index:
        tr = t.index != iso
        med = t.loc[tr].groupby("grupo", observed=True)[y].median()
        errs["mediana_grupo"].append(abs(yv[iso] - med.get(t.loc[iso, "grupo"], yv[tr].median())))
        for m, mk in modelos.items():
            if mk is None:
                continue
            pred = mk().fit(X[tr], yv[tr]).predict(X.loc[[iso]])[0]
            errs[m].append(abs(yv[iso] - pred))
    return {m: float(np.mean(e)) for m, e in errs.items()}


def modulo_educacion() -> None:
    print("=" * 72)
    print("A1-EDUCACIÓN (módulo NUEVO): HLO ~ gasto educativo + renta + urbanización")
    pol = pd.read_csv(PROCESSED / "wdi_policy.csv")
    wdi = pd.read_csv(PROCESSED / "wdi_outcomes.csv")
    urb = pd.read_csv(PROCESSED / "wdi_extras.csv").query("variable=='urban_share'")
    ghed = pd.read_csv(PROCESSED / "ghed.csv")
    paises = set(ghed.iso3.unique())

    hlo = pol[pol.variable == "hlo_score"].sort_values("year").groupby("iso3").value.last()
    t = pd.DataFrame({
        "hlo": hlo,
        "gasto_edu": block(pol, "edu_spend_gdp", 2005, 2015),
        "gdp_pc": block(wdi, "gdp_pc_ppp", 2010, 2018),
        "urban": block(urb, "urban_share", 2010, 2018),
    })
    t = t[t.index.isin(paises)].dropna()
    t["log_gdp"] = np.log(t.gdp_pc)
    t["grupo"] = pd.qcut(t.gdp_pc, 4, labels=["Q1", "Q2", "Q3", "Q4"])
    feats = ["gasto_edu", "log_gdp", "urban"]
    print(f"muestra: {len(t)} países con casos completos")

    mae = loocv_mae(t, feats, "hlo")
    print("MAE LOOCV (puntos HLO):", {k: round(v, 1) for k, v in mae.items()})
    umbral = 0.90 * mae["ols"]
    for m in ("gbm", "mlp"):
        v = "CUMPLE" if mae[m] <= umbral else "NO cumple"
        print(f"  aceptación {m} (<= {umbral:.1f}): {v}")
    ganador = min(("ols", "gbm", "mlp"), key=lambda m: mae[m] if mae[m] <= (umbral if m != "ols" else 9e9) else 9e9)
    ganador = ganador if mae[ganador] <= umbral or ganador == "ols" else "ols"
    print(f"  → modelo publicado: {ganador.upper()}")

    # residuales OOF del ganador + conformal por grupo
    modelo = (lambda: make_pipeline(StandardScaler(), LinearRegression())) if ganador == "ols" else None
    res = {}
    for iso in t.index:
        tr = t.index != iso
        pred = make_pipeline(StandardScaler(), LinearRegression()).fit(t.loc[tr, feats], t.loc[tr, "hlo"]).predict(t.loc[[iso], feats])[0]
        res[iso] = float(t.loc[iso, "hlo"] - pred)
    t["residual"] = pd.Series(res)
    hw = t.residual.abs().groupby(t.grupo, observed=True).quantile(0.90)
    t["semiancho_90"] = t.grupo.map(hw).astype(float)
    t["destacado"] = t.residual.abs() > t.semiancho_90
    out = t.round(2).reset_index().rename(columns={"index": "iso3"})
    out["modelo"], out["fecha_ejecucion"] = ganador, FECHA
    out.to_csv(GOLD / "gold_rendimiento_edu.csv", index=False)

    if "ESP" in t.index:
        e = t.loc["ESP"]
        print(f"  ESP: HLO {e.hlo:.0f}, residual {e.residual:+.1f} ± {e.semiancho_90:.1f} "
              f"({'DESTACADO' if e.destacado else 'dentro de banda'})")
    top = t[t.destacado]
    print(f"  destacados: {len(top)}/{len(t)}; extremos: "
          f"{t.residual.idxmin()} {t.residual.min():+.0f} / {t.residual.idxmax()} {t.residual.max():+.0f}")


def modulo_salud_spi() -> None:
    print("=" * 72)
    print("A1-SALUD ampliado: +SPI como control y auditoría residual⊥SPI")
    r = pd.read_csv(GOLD / "gold_rendimiento_pais.csv").set_index("iso3")
    pol = pd.read_csv(PROCESSED / "wdi_policy.csv")
    spi = block(pol, "spi_overall", 2016, 2023)
    comun = r.index.intersection(spi.index)
    rho = r.loc[comun, "residual"].corr(spi.loc[comun], method="spearman")
    print(f"AUDITORÍA declarada (PLAN §3, antes sin datos): Spearman(residual A1, SPI) = {rho:+.2f} "
          f"sobre {len(comun)} países")
    if abs(rho) < 0.2:
        print("  → sin correlación relevante: el 'rendimiento' NO es un artefacto de capacidad estadística ✅")
    else:
        print("  → correlación no trivial: parte del residual refleja calidad de datos — a declarar ⚠️")

    t = r.copy()
    t["spi"] = spi
    t = t.dropna(subset=["spi"])
    t["log_gdp"] = np.log(t.gdp_pc)
    t["grupo"] = t.grupo_renta
    feats0 = ["gasto", "log_gdp"]
    base = loocv_mae(t, feats0, "e0")
    conspi = loocv_mae(t, feats0 + ["spi"], "e0")
    print(f"MAE LOOCV e0 (n={len(t)}):")
    print("  sin SPI:", {k: round(v, 2) for k, v in base.items()})
    print("  con SPI:", {k: round(v, 2) for k, v in conspi.items()})
    mejor = min(conspi, key=conspi.get)
    print(f"  → mejor con el corpus ampliado: {mejor} ({conspi[mejor]:.2f}); "
          f"el MLP {'sigue sin batir' if conspi['mlp'] > 0.9 * conspi['ols'] else 'BATE'} al OLS por el margen exigido")


if __name__ == "__main__":
    modulo_educacion()
    modulo_salud_spi()
