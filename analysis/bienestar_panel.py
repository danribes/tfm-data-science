"""#1 del plan a 50 años: la frontera ingreso→bienestar re-estimada como PANEL.

La frontera transversal dice "los países con más ingresos tienen menos
mortalidad infantil" (efecto ENTRE países). Para simular a décadas hace falta
el efecto DENTRO de cada país: "cuando un país sube su ingreso público, ¿baja
su mortalidad?". Diseño:

    log(mort<5)_it = β·ingresos_{i,t−2} + γ·log(PIBpc)_it + α_i + δ_t + ε_it

Efectos fijos de país (α_i: absorbe todo lo estructural) y de año (δ_t:
absorbe la tendencia mundial de supervivencia — la mejora secular NO se le
atribuye al dinero), errores agrupados por país (CR1, mismo patrón que las
elasticidades del motor demográfico). Se publica el contraste entre-vs-dentro:
si el "dentro" es menor (lo normal), usar el transversal en simulación
sobrestimaría lo que compra el dinero.

Salida: api/models/bienestar_panel_params.json (para la cadena de #4)
+ lectura impresa.

    python3 analysis/bienestar_panel.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from backtest_t1 import GOLD

PROCESSED = GOLD.parent / "processed"
ROOT = GOLD.parents[1]
LAG = 2


def panel() -> pd.DataFrame:
    u5 = (pd.read_csv(PROCESSED / "wdi_bienestar.csv").query("variable=='mortalidad_u5'")
          .rename(columns={"value": "u5"})[["iso3", "year", "u5"]])
    rev = (pd.read_csv(PROCESSED / "world_revenue_global.csv").query("categoria=='rev_total'")
           .rename(columns={"pct_gdp": "rev"})[["iso3", "year", "rev"]])
    rev["year"] = rev.year + LAG  # ingresos de t−LAG explican el resultado de t
    gdp = (pd.read_csv(PROCESSED / "wdi_outcomes.csv").query("variable=='gdp_pc_ppp'")
           .rename(columns={"value": "gdp"})[["iso3", "year", "gdp"]])
    t = u5.merge(rev, on=["iso3", "year"]).merge(gdp, on=["iso3", "year"]).dropna()
    t = t[(t.u5 > 0) & (t.gdp > 0)]
    t["log_u5"], t["log_gdp"] = np.log(t.u5), np.log(t.gdp)
    n_por_pais = t.groupby("iso3").size()
    return t[t.iso3.isin(n_por_pais[n_por_pais >= 10].index)]


def fe_cr1(t: pd.DataFrame, feats: list[str], y: str) -> tuple[np.ndarray, np.ndarray]:
    """Within de país + dummies de año; SE agrupadas por país (CR1)."""
    d = t.copy()
    for c in [y, *feats]:
        d[c] = d[c] - d.groupby("iso3")[c].transform("mean")
    anio = pd.get_dummies(d.year, drop_first=True, dtype=float)
    X = np.column_stack([d[feats].values, anio.values])
    Y = d[y].values
    beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
    resid = Y - X @ beta
    XtX_inv = np.linalg.pinv(X.T @ X)
    meat = np.zeros((X.shape[1], X.shape[1]))
    for _, g in pd.DataFrame({"iso3": t.iso3.values}).assign(i=range(len(t))).groupby("iso3"):
        Xg, ug = X[g.i.values], resid[g.i.values]
        s = Xg.T @ ug
        meat += np.outer(s, s)
    G = t.iso3.nunique()
    vcov = XtX_inv @ meat @ XtX_inv * G / (G - 1)
    return beta[:len(feats)], np.sqrt(np.diag(vcov))[:len(feats)]


def main() -> None:
    global LAG
    t = panel()
    print(f"panel: {t.iso3.nunique()} países × {t.year.min()}–{t.year.max()} = {len(t)} obs "
          f"(ingresos con retardo {LAG} años)")

    # ENTRE países (el diseño transversal de la frontera, como referencia)
    m = t.groupby("iso3")[["log_u5", "rev", "log_gdp"]].mean()
    Xb = np.column_stack([m[["rev", "log_gdp"]].values, np.ones(len(m))])
    bb, *_ = np.linalg.lstsq(Xb, m.log_u5.values, rcond=None)

    # DENTRO de país (FE país + año, CR1)
    beta, se = fe_cr1(t, ["rev", "log_gdp"], "log_u5")
    print(f"β ingresos (log-mortalidad por pp de PIB):")
    print(f"  ENTRE países (transversal): {bb[0]:+.4f}")
    print(f"  DENTRO de país (FE país+año, CR1): {beta[0]:+.4f} ± {se[0]:.4f} "
          f"(IC95 [{beta[0] - 1.96 * se[0]:+.4f}, {beta[0] + 1.96 * se[0]:+.4f}])")
    ratio = beta[0] / bb[0] if bb[0] else float("nan")
    print(f"  → el efecto dentro es {ratio:.0%} del entre: simular con el transversal "
          f"{'SOBRESTIMARÍA' if abs(ratio) < 1 else 'infraestimaría'} lo que compra el dinero")
    print(f"  γ log-PIBpc dentro: {beta[1]:+.3f} ± {se[1]:.3f}")

    # gradiente de retardos: el efecto del ingreso es estructural, no inmediato
    gradiente = {}
    for lag in (2, 5, 8):
        LAG = lag
        tl = panel()
        bl, sl = fe_cr1(tl, ["rev", "log_gdp"], "log_u5")
        gradiente[str(lag)] = {"beta": float(bl[0]), "se": float(sl[0]), "n": int(len(tl))}
        print(f"  gradiente lag {lag}: β_rev {bl[0]:+.4f} ± {sl[0]:.4f}")
    LAG = 2

    out = {
        "outcome": "log_mortalidad_u5", "lag_ingresos": LAG,
        "beta_rev_within": float(beta[0]), "se_rev_within_cr1": float(se[0]),
        "beta_rev_between": float(bb[0]),
        "beta_loggdp_within": float(beta[1]), "se_loggdp_within_cr1": float(se[1]),
        "gradiente_retardos": gradiente,
        "n_paises": int(t.iso3.nunique()), "n_obs": int(len(t)),
        "anios": [int(t.year.min()), int(t.year.max())],
        "nota": ("FE pais+anio, CR1 por pais; delta_t absorbe la mejora secular mundial. "
                 "El efecto del ingreso es nulo a 2-5 anios y aparece a 8 (estructural): "
                 "la cadena a 50 anios usa el lag 8 y lo declara."),
    }
    dest = ROOT / "api" / "models" / "bienestar_panel_params.json"
    dest.write_text(json.dumps(out, indent=2))
    print(f"→ {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
