"""A1-BIENESTAR: ¿cuánto bienestar objetivo compra el ingreso público?

Extiende la frontera gasto→resultado (A1 salud, A1 educación) al marco
bienestar/pobreza infantil, con el INGRESO público total (WoRLD) como dinero
de entrada — la formulación literal de "dinero público → resultados":

- Resultado 1: mortalidad <5 (log — rango 2–100‰), el proxy más duro del marco.
- Resultado 2: stunting (malnutrición crónica), el proxy de pobreza profunda.
- Entrada: ingresos públicos % PIB (media 2010–2018, retardo estructural),
  controles renta (log PIB pc PPP) y urbanización.
- Protocolo idéntico: LOOCV, mediana-por-grupo y OLS como varas, GBM como
  flexible (regla ≤0,90×OLS). MLP omitido y DECLARADO: mismo régimen n≈100-150
  donde perdió dos veces bajo reglas idénticas (educación 33,4 vs 32,7; salud
  2,96 vs 2,75) — repetirlo no aporta información nueva.
- Residuales OOF + conformal 90 % por cuartil de renta → funnel, nunca ranking.

Salida: gold_bienestar_pais.csv + lectura impresa (España, extremos, Spearman
del marco completo contra ingresos).

    python3 analysis/bienestar_a1.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from backtest_t1 import GOLD

PROCESSED = GOLD.parent / "processed"
FECHA = "2026-07-19"


def block(df, var, y0, y1, valcol="value"):
    d = df[(df.variable == var) & (df.year.between(y0, y1))]
    return d.groupby("iso3")[valcol].mean()


def loocv(t: pd.DataFrame, feats: list[str], y: str) -> dict[str, float]:
    modelos = {
        "ols": lambda: make_pipeline(StandardScaler(), LinearRegression()),
        "gbm": lambda: LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=7,
                                     min_child_samples=10, random_state=42, verbose=-1),
    }
    errs = {m: [] for m in ["mediana_grupo", *modelos]}
    for iso in t.index:
        tr = t.index != iso
        med = t.loc[tr].groupby("grupo", observed=True)[y].median()
        errs["mediana_grupo"].append(abs(t.loc[iso, y] - med.get(t.loc[iso, "grupo"], t.loc[tr, y].median())))
        for m, mk in modelos.items():
            pred = mk().fit(t.loc[tr, feats], t.loc[tr, y]).predict(t.loc[[iso], feats])[0]
            errs[m].append(abs(t.loc[iso, y] - pred))
    return {m: float(np.mean(e)) for m, e in errs.items()}


def frontera(nombre: str, outcome: pd.Series, log_out: bool) -> pd.DataFrame | None:
    bien = pd.read_csv(PROCESSED / "wdi_bienestar.csv")
    wdi = pd.read_csv(PROCESSED / "wdi_outcomes.csv")
    urb = pd.read_csv(PROCESSED / "wdi_extras.csv").query("variable=='urban_share'")
    world = pd.read_csv(PROCESSED / "world_revenue_global.csv")
    rev = world[world.categoria == "rev_total"].rename(columns={"categoria": "variable", "pct_gdp": "value"})

    t = pd.DataFrame({
        "y": outcome,
        "rev": block(rev, "rev_total", 2010, 2018),
        "gdp_pc": block(wdi, "gdp_pc_ppp", 2010, 2018),
        "urban": block(urb, "urban_share", 2010, 2018),
    }).dropna()
    t = t[t.gdp_pc > 0]
    if log_out:
        t["y"] = np.log(t.y)
    t["log_gdp"] = np.log(t.gdp_pc)
    t["grupo"] = pd.qcut(t.gdp_pc, 4, labels=["Q1", "Q2", "Q3", "Q4"])
    feats = ["rev", "log_gdp", "urban"]
    print(f"\n== {nombre}: n={len(t)} países ==")
    mae = loocv(t, feats, "y")
    unidad = "log" if log_out else "pp"
    print(f"MAE LOOCV ({unidad}):", {k: round(v, 3) for k, v in mae.items()})
    umbral = 0.90 * mae["ols"]
    print(f"  aceptación GBM (<= {umbral:.3f}): {'CUMPLE' if mae['gbm'] <= umbral else 'NO cumple'} "
          f"→ modelo publicado: {'GBM' if mae['gbm'] <= umbral else 'OLS'}")

    res = {}
    for iso in t.index:
        tr = t.index != iso
        pred = (make_pipeline(StandardScaler(), LinearRegression())
                .fit(t.loc[tr, feats], t.loc[tr, "y"]).predict(t.loc[[iso], feats])[0])
        res[iso] = float(t.loc[iso, "y"] - pred)
    t["residual"] = pd.Series(res)
    hw = t.residual.abs().groupby(t.grupo, observed=True).quantile(0.90)
    t["semiancho_90"] = t.grupo.map(hw).astype(float)
    t["destacado"] = t.residual.abs() > t.semiancho_90
    if "ESP" in t.index:
        e = t.loc["ESP"]
        print(f"  ESP: residual {e.residual:+.2f} ± {e.semiancho_90:.2f} "
              f"({'DESTACADO' if e.destacado else 'dentro de banda'}; residual<0 = mejor que lo esperado)")
    print(f"  extremos: mejor {t.residual.idxmin()} {t.residual.min():+.2f} / "
          f"peor {t.residual.idxmax()} {t.residual.max():+.2f}; destacados {int(t.destacado.sum())}/{len(t)}")
    return t.assign(outcome=nombre)


def main() -> None:
    bien = pd.read_csv(PROCESSED / "wdi_bienestar.csv")
    u5 = bien.query("variable=='mortalidad_u5'").sort_values("year").groupby("iso3").value.last()
    stunt = bien.query("variable=='stunting' and year>=2015").sort_values("year").groupby("iso3").value.last()

    t1 = frontera("mortalidad_u5_log", u5, log_out=True)
    t2 = frontera("stunting", stunt, log_out=False)
    gold = pd.concat([d for d in (t1, t2) if d is not None])
    out = gold.round(3).reset_index().rename(columns={"index": "iso3"})
    out["fecha_ejecucion"] = FECHA
    out.to_csv(GOLD / "gold_bienestar_pais.csv", index=False)

    # el marco completo contra el dinero: Spearman de cada dimensión vs ingresos
    world = pd.read_csv(PROCESSED / "world_revenue_global.csv")
    rev = world[world.categoria == "rev_total"].groupby("iso3").pct_gdp.mean()
    print("\n== Marco completo vs ingresos públicos (Spearman, países con dato) ==")
    for var in ["pobreza_300", "pobreza_multidim", "mortalidad_u5", "stunting",
                "ninos_sin_escuela", "cobertura_proteccion", "agua_segura", "electricidad"]:
        s = bien[bien.variable == var].sort_values("year").groupby("iso3").value.last()
        comun = s.index.intersection(rev.index)
        if len(comun) > 30:
            rho = s.loc[comun].corr(rev.loc[comun], method="spearman")
            print(f"  {var:22s} rho={rho:+.2f} (n={len(comun)})")


if __name__ == "__main__":
    main()
