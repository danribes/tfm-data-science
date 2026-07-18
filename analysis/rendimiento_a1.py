"""A1 — Rendimiento ajustado del gasto sanitario público (F3.1, módulo salud).

¿Qué país obtiene más esperanza de vida de la que "le tocaría" por su renta,
demografía y factores de riesgo, dado su gasto? NUNCA una liga: residual con
intervalo, en funnel.

Diseño (Entrega 4 §3/§7, declarado antes de mirar resultados):
- Unidad: país. Outcome: esperanza de vida al nacer, media 2015–2019
  (pre-COVID a propósito, declarado). Gasto: sanidad pública %PIB (GHED),
  media 2010–2014 — retardo de 5 años (plan §3: retardos 3–5a).
- Controles: log PIB pc PPP, obesidad, tabaquismo, % urbano (medias 2015–19).
- Muestra: casos completos (misma muestra para todos los modelos).
- Grupos de renta: cuartiles de PIB pc PPP (proxy declarado).
- Baselines: mediana del cuartil de renta; OLS. Candidatos: spline en log-PIB
  (GAM-lite) y LightGBM. Validación: leave-one-country-out (MAE).
- ACEPTACIÓN (pre-registrada): MAE(GBM) <= MAE(OLS)·0,90 Y estabilidad del
  residual entre 3 definiciones de gasto (public_gdp, che_gdp, public_share):
  Spearman >= 0,8. Si falla, se publica el modelo simple mejor (parsimonia
  ante empate <=5 %).
- Incertidumbre: residuales out-of-fold (jackknife); semiancho conformal por
  cuartil de renta = cuantil 90 de |residual OOF| del grupo. "Destacado" solo
  si |residual| supera su semiancho de grupo.

    python3 analysis/rendimiento_a1.py
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler

from backtest_t1 import GOLD

PROCESSED = GOLD.parent / "processed"
FIG = GOLD.parents[1] / "docs" / "figures" / "a1"
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

FECHA = "2026-07-18"
OUT_Y, OUT_Y2 = (2015, 2019), (2010, 2014)
CONTROLES = ["log_gdp", "obesity", "smoking", "urban_share"]


def block_mean(df, var, y0, y1, col="value"):
    d = df[(df.variable == var) & (df.year.between(y0, y1))]
    return d.groupby("iso3")[col].mean()


def build_table(spend_var: str) -> pd.DataFrame:
    ghed = pd.read_csv(PROCESSED / "ghed.csv")
    wdi = pd.read_csv(PROCESSED / "wdi_outcomes.csv")
    gho = pd.read_csv(PROCESSED / "gho_confounders.csv")
    urb = pd.read_csv(PROCESSED / "wdi_extras.csv").query("variable=='urban_share'")
    paises = set(ghed.iso3.unique())  # solo países reales (GHED), sin agregados WB
    t = pd.DataFrame({
        "e0": block_mean(wdi, "e0_global", *OUT_Y),
        "gasto": block_mean(ghed, spend_var, *OUT_Y2),
        "gdp_pc": block_mean(wdi, "gdp_pc_ppp", *OUT_Y),
        "obesity": block_mean(gho, "obesity", *OUT_Y),
        "smoking": block_mean(gho, "smoking", *OUT_Y),
        "urban_share": block_mean(urb, "urban_share", *OUT_Y),
    })
    t = t[t.index.isin(paises)].dropna()
    t["log_gdp"] = np.log(t.gdp_pc)
    t["grupo_renta"] = pd.qcut(t.gdp_pc, 4, labels=["Q1 (baja)", "Q2", "Q3", "Q4 (alta)"])
    return t


FEATS = ["gasto"] + CONTROLES


def loocv_residuals(t: pd.DataFrame, model_key: str) -> pd.Series:
    """Residual out-of-fold de cada país (y_obs − y_esperado)."""
    res = {}
    X, y = t[FEATS], t["e0"]
    for iso in t.index:
        tr = t.index != iso
        if model_key == "mediana_grupo":
            pred = float(t.loc[tr].groupby("grupo_renta", observed=True)["e0"]
                         .median().get(t.loc[iso, "grupo_renta"], y[tr].median()))
        elif model_key == "ols":
            m = make_pipeline(StandardScaler(), LinearRegression()).fit(X[tr], y[tr])
            pred = float(m.predict(X.loc[[iso]])[0])
        elif model_key == "spline":
            m = make_pipeline(StandardScaler(),
                              SplineTransformer(degree=3, n_knots=5),
                              LinearRegression()).fit(X[tr], y[tr])
            pred = float(m.predict(X.loc[[iso]])[0])
        elif model_key == "gbm":
            m = LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=7,
                              min_child_samples=10, subsample=0.9, colsample_bytree=0.9,
                              random_state=42, verbose=-1).fit(X[tr], y[tr])
            pred = float(m.predict(X.loc[[iso]])[0])
        res[iso] = float(y[iso] - pred)
    return pd.Series(res, name=model_key)


def main():
    t = build_table("public_gdp")
    print(f"muestra: {len(t)} países con casos completos")

    modelos = ["mediana_grupo", "ols", "spline", "gbm"]
    res = pd.DataFrame({m: loocv_residuals(t, m) for m in modelos})
    mae = res.abs().mean().round(3)
    print("MAE LOOCV (años de e0):", mae.to_dict())

    # multiverso: estabilidad del residual GBM entre 3 definiciones de gasto
    rhos = []
    base_res = res["gbm"]
    for alt in ["che_gdp", "public_share"]:
        t_alt = build_table(alt)
        comun = t_alt.index.intersection(base_res.index)
        r_alt = loocv_residuals(t_alt.loc[comun], "gbm")
        rho = spearmanr(base_res.loc[comun], r_alt)[0]
        rhos.append(rho)
        print(f"multiverso gasto={alt}: Spearman {rho:.3f} (n={len(comun)})")

    acepta_gbm = (mae["gbm"] <= 0.90 * mae["ols"]) and all(r >= 0.8 for r in rhos)
    if acepta_gbm:
        ganador = "gbm"
    else:
        simple = mae[["ols", "spline"]]
        ganador = "ols" if mae["ols"] <= simple.min() * 1.05 else simple.idxmin()
    print(f"criterio GBM (MAE<=0,9·OLS y Spearman>=0,8): {'CUMPLE' if acepta_gbm else 'NO cumple'} → ganador: {ganador}")

    resid = res[ganador]
    t["e0_esperado"] = t["e0"] - resid
    t["residual"] = resid
    hw = resid.abs().groupby(t["grupo_renta"], observed=True).quantile(0.90)
    t["semiancho_90"] = t["grupo_renta"].map(hw).astype(float)
    t["destacado"] = t.residual.abs() > t.semiancho_90

    # top-3 factores (contribuciones del modelo ganador, full-fit solo para explicar)
    if ganador == "gbm":
        m = LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=7,
                          min_child_samples=10, random_state=42, verbose=-1).fit(t[FEATS], t.e0)
        contrib = pd.DataFrame(m.predict(t[FEATS], pred_contrib=True)[:, :-1],
                               index=t.index, columns=FEATS)
    else:
        m = make_pipeline(StandardScaler(), LinearRegression()).fit(t[FEATS], t.e0)
        z = StandardScaler().fit_transform(t[FEATS])
        contrib = pd.DataFrame(z * m[-1].coef_, index=t.index, columns=FEATS)
    t["explicacion"] = contrib.abs().apply(
        lambda r: "factores dominantes: " + ", ".join(r.nlargest(3).index), axis=1)

    out = t.reset_index().rename(columns={"index": "iso3"})
    out["modelo"], out["fecha_ejecucion"] = ganador, FECHA
    cols = ["iso3", "e0", "e0_esperado", "residual", "semiancho_90", "destacado",
            "grupo_renta", "gasto", "gdp_pc", "modelo", "fecha_ejecucion", "explicacion"]
    out[cols].round(3).to_csv(GOLD / "gold_rendimiento_pais.csv", index=False)

    # funnel: residual vs gasto, coloreado por grupo de renta, con semiancho
    colores = dict(zip(hw.index, [BLUE, GREEN, ORANGE, VIOLET]))
    fig, ax = plt.subplots(figsize=(9, 5))
    for g, d in t.groupby("grupo_renta", observed=True):
        ax.errorbar(d.gasto, d.residual, yerr=d.semiancho_90, fmt="o", ms=4.5,
                    color=colores[g], ecolor=colores[g], elinewidth=0.7, alpha=0.75,
                    capsize=0, label=str(g))
    ax.axhline(0, color=INK2, lw=0.9)
    for iso in ["ESP", "USA", "JPN", "CHE", "NGA", "IND", "CHN", "BRA"]:
        if iso in t.index:
            ax.annotate(iso, (t.loc[iso, "gasto"], t.loc[iso, "residual"]),
                        fontsize=8, color=INK, fontweight="bold" if iso == "ESP" else "normal",
                        xytext=(5, 4), textcoords="offset points")
    ax.set_xlabel("gasto sanitario público 2010–2014 (% del PIB, GHED)")
    ax.set_ylabel("residual de esperanza de vida 2015–2019 (años)")
    ax.set_title(f"A1 · Años de vida sobre lo esperado por renta, riesgo y urbanización\n"
                 f"({ganador.upper()}, residuales LOOCV; intervalo 90 % por cuartil de renta — no es una liga)")
    ax.legend(frameon=False, fontsize=8, title="cuartil de PIB pc")
    fig.tight_layout()
    fig.savefig(FIG / "a1_funnel.png")
    plt.close(fig)

    imp = contrib.abs().mean().sort_values()
    fig, ax = plt.subplots(figsize=(6.5, 3))
    ax.barh(range(len(imp)), imp.values, color=BLUE, height=0.6)
    ax.set_yticks(range(len(imp)), imp.index)
    ax.set_title("Contribución media |años de e0| por variable (modelo ganador)")
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(FIG / "a1_contribuciones.png")
    plt.close(fig)

    es = t.loc["ESP"]
    print(f"\nESP: e0 obs {es.e0:.1f}, esperado {es.e0_esperado:.1f}, residual "
          f"{es.residual:+.2f} ± {es.semiancho_90:.2f} años ({es.grupo_renta}, "
          f"{'DESTACADO' if es.destacado else 'dentro de banda'})")
    top = t[t.destacado].sort_values("residual")
    print(f"destacados: {len(top)}/{len(t)} países fuera de su banda de grupo")
    print(top["residual"].head(4).round(2).to_dict(), "…", top["residual"].tail(4).round(2).to_dict())


if __name__ == "__main__":
    main()
