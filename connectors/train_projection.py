"""Entrena las elasticidades del motor de proyección (pensiones + sanidad).

Modelo within (demeaning por país) sobre el panel UE 1995–2023:
  log(gasto %PIB) ~ β65·log(share65) + βg·log(pib_pc) + βu·paro + βob·obesidad(sanidad)
TODOS los drivers del modelo (petición del autor), no solo demografía:
los proyectables se proyectan (share65 por variante), el resto entra como
palanca de escenario (crecimiento PIB) o se mantiene con sensibilidad (paro).

Artefacto → api/models/projection_params.json (rellena el hueco 501).
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd

from base import GOLD

MODELS = pathlib.Path(__file__).resolve().parents[1] / "api" / "models"

SPECS = {
    "pensions": {"y": "pensions_oldage", "drivers": ["pop65_share", "gdp_pc_pps", "unemployment"]},
    "health": {"y": "te_gf07", "drivers": ["pop65_share", "gdp_pc_pps", "unemployment", "obesity"]},
}


def within_ols(df: pd.DataFrame, y: str, xs: list[str]) -> dict:
    d = df[["geo", y] + xs].dropna().copy()
    d = d[(d[y] > 0)]
    d["ly"] = np.log(d[y])
    cols = []
    for x in xs:
        if x in ("pop65_share", "gdp_pc_pps"):
            d[f"l_{x}"] = np.log(d[x])
            cols.append(f"l_{x}")
        else:
            cols.append(x)
    # demeaning por país (efectos fijos)
    for c in ["ly"] + cols:
        d[c + "_w"] = d[c] - d.groupby("geo")[c].transform("mean")
    X = d[[c + "_w" for c in cols]].values
    yv = d["ly_w"].values
    beta, res, *_ = np.linalg.lstsq(X, yv, rcond=None)
    resid = yv - X @ beta
    dof = max(len(d) - len(cols) - d["geo"].nunique(), 1)
    sigma = float(np.sqrt((resid ** 2).sum() / dof))
    se = np.sqrt(np.diag(sigma ** 2 * np.linalg.pinv(X.T @ X)))
    return {
        "drivers": cols, "beta": beta.tolist(), "se": se.tolist(),
        "sigma": sigma, "n": int(len(d)), "countries": int(d["geo"].nunique()),
    }


def base_values(wide: pd.DataFrame, y: str, drivers: list[str]) -> dict:
    out = {}
    for geo, grp in wide.groupby("geo"):
        grp = grp.sort_values("year")
        last = grp[grp[y].notna()].tail(1)
        if last.empty:
            continue
        row = last.iloc[0]
        vals = {"year": int(row["year"]), y: float(row[y])}
        okall = True
        for x in drivers:
            v = row.get(x)
            if pd.isna(v):
                okall = False
                break
            vals[x] = float(v)
        if okall:
            out[geo] = vals
    return out


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    wide = pd.read_csv(GOLD / "gold_panel_wide.csv")
    params = {}
    for module, spec in SPECS.items():
        drivers = [d for d in spec["drivers"] if d in wide.columns]
        fit = within_ols(wide, spec["y"], drivers)
        fit["y"] = spec["y"]
        fit["base"] = base_values(wide, spec["y"], drivers)
        params[module] = fit
        b65 = fit["beta"][fit["drivers"].index("l_pop65_share")] if "l_pop65_share" in fit["drivers"] else None
        print(f"{module}: n={fit['n']} ({fit['countries']} países) β_share65={b65:.2f} "
              f"σ={fit['sigma']:.3f} | drivers={fit['drivers']} | bases={len(fit['base'])} geos")
        assert b65 is not None and 0 < b65 < 3, f"elasticidad demográfica rara: {b65}"
    MODELS.mkdir(parents=True, exist_ok=True)
    (MODELS / "projection_params.json").write_text(json.dumps(params, indent=1))
    print("→ api/models/projection_params.json")
