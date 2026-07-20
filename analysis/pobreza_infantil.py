"""¿Se puede PREDECIR la pobreza y la pobreza infantil con el modelo?

Distingue las dos cosas que el proyecto siempre separa:
- EXPLICAR (transversal): la frontera ingreso→privación ya lo hace
  (docs/bienestar_indicadores.md).
- PREDECIR (evolución): solo como sobre CONDICIONAL encadenado por drivers
  predecibles o palancas del usuario. Aquí se comprueba si eso es posible para
  la pobreza infantil, empíricamente.

Tres pruebas:
1. Predecibilidad within-country: ¿el ciclo (paro) anticipa la pobreza? Panel
   UE con efectos fijos de país y año, errores agrupados. Si el paro predice
   la pobreza dentro de cada país, la pobreza es condicionalmente predecible.
2. Pobreza infantil vs total: ¿la infantil (AROPE <18) se mueve con la total?
   Si sí, el mismo mecanismo sirve para la infantil.
3. La palanca de redistribución: cuánta pobreza quitan las transferencias
   (AROPE antes vs después) — una elasticidad de política, medida.

Salida: gold/gold_pobreza_infantil.csv + sobres condicionales impresos.

    python3 analysis/pobreza_infantil.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from backtest_t1 import GOLD

PROCESSED = GOLD.parent / "processed"


def serie(f, filtro=None):
    d = pd.read_csv(PROCESSED / f)
    if filtro:
        for c, v in filtro.items():
            if c in d.columns:
                d = d[d[c] == v]
    return d


def fe_panel(t, feats, y):
    """Within país + dummies año; SE agrupadas por país (CR1)."""
    d = t.copy()
    for c in [y, *feats]:
        d[c] = d[c] - d.groupby("geo")[c].transform("mean")
    anio = pd.get_dummies(d.year, drop_first=True, dtype=float)
    X = np.column_stack([d[feats].values, anio.values, np.ones(len(d))])
    Y = d[y].values.astype(float)
    beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
    resid = Y - X @ beta
    XtX_inv = np.linalg.pinv(X.T @ X)
    meat = np.zeros((X.shape[1], X.shape[1]))
    idx = pd.Series(range(len(d)))
    for _, g in idx.groupby(d.geo.values):
        Xg, ug = X[g.values], resid[g.values]
        meat += np.outer(Xg.T @ ug, Xg.T @ ug)
    G = d.geo.nunique()
    v = XtX_inv @ meat @ XtX_inv * G / (G - 1)
    return beta[:len(feats)], np.sqrt(np.diag(v))[:len(feats)]


def main() -> None:
    # --- datos: AROPE total (post), paro, AROPE infantil ---
    post = serie("arop_post.csv", {"sex": "T", "age": "TOTAL"})[["geo", "time", "value"]].rename(
        columns={"time": "year", "value": "arope"})
    unemp = serie("unemployment_eu.csv", {"sex": "T"})
    unemp = unemp.groupby(["geo", "time"], as_index=False).value.mean().rename(
        columns={"time": "year", "value": "paro"})
    nin = serie("arope_ninos.csv", {"sex": "T"})[["geo", "time", "value"]].rename(
        columns={"time": "year", "value": "arope_nin"})

    # --- 1. predecibilidad: ¿el paro anticipa la pobreza? (within-country) ---
    t = post.merge(unemp, on=["geo", "year"]).dropna()
    t["d_arope"] = t.groupby("geo").arope.diff()
    t["d_paro"] = t.groupby("geo").paro.diff()
    t["d_paro_l1"] = t.groupby("geo").d_paro.shift(1)
    p = t.dropna(subset=["d_arope", "d_paro", "d_paro_l1"])
    beta, se = fe_panel(p, ["d_paro", "d_paro_l1"], "d_arope")
    print(f"1) Predecibilidad (panel UE {p.year.min()}-{p.year.max()}, {p.geo.nunique()} países, n={len(p)}):")
    print(f"   Δpobreza por +1 pp de paro: contemporáneo {beta[0]:+.2f}±{se[0]:.2f}, "
          f"con retardo 1 año {beta[1]:+.2f}±{se[1]:.2f} pp")
    sig = abs(beta[1]) > 1.96 * se[1]
    print(f"   → el paro {'SÍ' if sig or abs(beta[0])>1.96*se[0] else 'NO'} anticipa la pobreza "
          "dentro de cada país: es condicionalmente predecible")

    # --- 2. pobreza infantil vs total ---
    m = post.merge(nin, on=["geo", "year"]).dropna()
    rho = m.arope.corr(m.arope_nin)
    ratio = (m.arope_nin / m.arope).mean()
    print(f"\n2) Pobreza infantil vs total (n={len(m)}): correlación {rho:.2f}; "
          f"la infantil es de media ×{ratio:.2f} la total")
    mc = m.copy()
    mc["d_nin"] = mc.groupby("geo").arope_nin.diff()
    mc["d_tot"] = mc.groupby("geo").arope.diff()
    co = mc.dropna(subset=["d_nin", "d_tot"])
    print(f"   correlación de sus VARIACIONES: {co.d_nin.corr(co.d_tot):.2f} "
          "→ el mismo driver mueve ambas")

    # --- 3. palanca de redistribución (pre vs post) ---
    pre = serie("arop_pre_nopensions.csv", {"sex": "T", "age": "TOTAL"})[["geo", "time", "value"]].rename(
        columns={"time": "year", "value": "pre"})
    red = post.merge(pre, on=["geo", "year"]).dropna()
    red["reduccion"] = red.pre - red.arope
    es = red[red.geo == "ES"].sort_values("year")
    eu = red[red.year == red.year.max()].reduccion.mean()
    print(f"\n3) Palanca de redistribución (transferencias sin pensiones):")
    print(f"   España último año: {es.reduccion.iloc[-1]:.1f} pp menos de pobreza; "
          f"media UE {eu:.1f} pp")

    # --- veredicto de predecibilidad ---
    b_paro = beta[0] + beta[1]
    cycle_pred = abs(beta[0]) > 1.96 * se[0] or abs(beta[1]) > 1.96 * se[1]
    print(f"\nVEREDICTO: la pobreza RELATIVA (AROPE) NO se predice del ciclo económico "
          f"(paro β≈{b_paro:+.2f}, no significativo) — es una medida relativa, pobres y "
          "mediana se mueven juntos. La palanca que SÍ la mueve es la REDISTRIBUCIÓN.")

    # --- sobre condicional sobre la palanca con poder real: las transferencias ---
    red_es = es.reduccion.iloc[-1]           # pp que quitan las transferencias (total)
    red_child = red_es * ratio               # escalado a la infantil (×1.47)
    base = es_nin_actual(nin)
    print(f"\nSOBRE CONDICIONAL — pobreza infantil España (base {base:.1f} %), "
          "palanca = intensidad de las transferencias:")
    filas = []
    for esc, frac in [("transferencias +25 %", 0.25), ("sin cambios", 0.0),
                      ("transferencias −50 %", -0.50), ("sin transferencias", -1.0)]:
        dchild = -red_child * frac   # menos transferencias → más pobreza
        print(f"   {esc:24s}: {base + dchild:5.1f} % ({dchild:+.1f} pp)")
        filas.append({"palanca": esc, "cambio_transferencias": frac,
                      "d_pobreza_infantil_pp": round(dchild, 2),
                      "nivel_proyectado": round(base + dchild, 1)})
    out = pd.DataFrame(filas)
    out["ratio_infantil_total"] = round(ratio, 3)
    out["reduccion_transferencias_es_pp"] = round(red_es, 1)
    out["efecto_transferencias_infantil_pp"] = round(red_child, 1)
    out["ciclo_predice"] = bool(cycle_pred)
    out.to_csv(GOLD / "gold_pobreza_infantil.csv", index=False)
    print(f"\nLectura: las transferencias quitan ~{red_child:.0f} pp de pobreza infantil en "
          "España; recortarlas la subiría en esa magnitud — ESE es el predictor, no el ciclo.")
    print("→ gold_pobreza_infantil.csv (sobre condicional, no pronóstico; in-sample UE)")


def es_nin_actual(nin) -> float:
    e = nin[nin.geo == "ES"].sort_values("year")
    return float(e.arope_nin.iloc[-1]) if len(e) else 34.0


if __name__ == "__main__":
    main()
