"""#2+#3 del plan a 50 años: Monte Carlo del simulador de deuda hasta 2070.

Dos mejoras sobre escenarios_d1:
- #2: la incertidumbre de los PARÁMETROS entra en las bandas. Antes las bandas
  eran variantes discretas; ahora cada trayectoria muestrea las elasticidades
  demográficas de su distribución (β65 pensiones N(0,912, 0,194), sanidad
  N(0,325, 0,240) — las SE agrupadas del motor), el tipo de mercado
  N(3,5 %, 0,5) y el crecimiento nominal N(3,3 %, 0,5), con variante
  demográfica uniforme entre las 6 de Eurostat.
- #3: horizonte 2070 (las proyecciones EUROPOP llegan a 2070; el corte 2050
  del D1 original era prudencia — aquí se extiende Y SE DECLARA que la
  aritmética compuesta a 46 años es un sobre condicional, no un pronóstico).

Todo es CONDICIONAL a continuidad institucional: sin reformas, sin crisis,
sin techos. El pseudo-backtest (#5) mide cuánto vale ese supuesto.

Salida: gold_escenarios_deuda_mc.csv (percentiles por año y escenario).

    python3 analysis/mc_d1.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from backtest_t1 import GOLD

ROOT = GOLD.parents[1]
Y0, Y1 = 2024, 2070
N_SIM = 4000
SEED = 42
BASE = {"debt0": 105.2, "r0": 2.28, "pb0": -0.9, "deflactor": 2.0, "vencimiento": 8}

ESCENARIOS = {
    "central": {},
    "consolidacion_2_5pp": {"pb_extra": 2.5, "rampa": 5},
    "crecimiento_alto": {"g_shift": 1.0},
    "tipos_altos": {"r_shift": 1.0},
}


def cargar_demografia() -> tuple[dict[str, pd.Series], dict]:
    p = json.load(open(ROOT / "api" / "models" / "projection_params.json"))
    pr = pd.read_csv(GOLD / "gold_projections.csv").query("geo=='ES'")
    sendas = {}
    for v in pr.variant.unique():
        s = pr[pr.variant == v].set_index("year")["share65"].reindex(range(Y0, Y1 + 1)).interpolate()
        if s.notna().all():
            sendas[v] = s
    return sendas, p


def main() -> None:
    rng = np.random.default_rng(SEED)
    sendas, p = cargar_demografia()
    variantes = list(sendas)
    betas_mu = {"pensions": 0.912, "health": 0.325}
    betas_se = {"pensions": 0.194, "health": 0.240}
    print(f"MC: {N_SIM} trayectorias × {len(ESCENARIOS)} escenarios, {Y0}–{Y1}, "
          f"{len(variantes)} variantes demográficas")

    filas = []
    for nombre, cfg in ESCENARIOS.items():
        fin = {2050: [], 2070: []}
        sendas_all = np.empty((N_SIM, Y1 - Y0 + 1))
        for k in range(N_SIM):
            bp = rng.normal(betas_mu["pensions"], betas_se["pensions"])
            bh = max(rng.normal(betas_mu["health"], betas_se["health"]), 0.0)
            r_mkt = rng.normal(3.5, 0.5) + cfg.get("r_shift", 0.0)
            g = rng.normal(3.3, 0.5) + cfg.get("g_shift", 0.0)
            s65 = sendas[variantes[rng.integers(len(variantes))]]
            # misma forma funcional que el motor: gasto = base·(s65/s65_base)^β
            demog = pd.Series(0.0, index=s65.index)
            for mod, spend_key, beta in [("pensions", "pensions_oldage", bp),
                                         ("health", "te_gf07", bh)]:
                b = p[mod]["base"]["ES"]
                spend = b[spend_key] * (s65 / b["pop65_share"]) ** beta
                demog = demog + (spend - spend.iloc[0])
            debt, r = BASE["debt0"], BASE["r0"]
            for j, y in enumerate(range(Y0, Y1 + 1)):
                r += (r_mkt - r) / BASE["vencimiento"]
                pb = BASE["pb0"] - demog.loc[y]
                if "pb_extra" in cfg:
                    pb += cfg["pb_extra"] * min(1.0, (y - Y0) / cfg["rampa"])
                debt = debt * (1 + r / 100) / (1 + g / 100) - pb
                sendas_all[k, j] = debt
            fin[2050].append(sendas_all[k, 2050 - Y0])
            fin[2070].append(sendas_all[k, 2070 - Y0])
        q = np.percentile(sendas_all, [5, 25, 50, 75, 95], axis=0)
        for j, y in enumerate(range(Y0, Y1 + 1)):
            filas.append({"escenario": nombre, "year": y, "p5": q[0, j], "p25": q[1, j],
                          "p50": q[2, j], "p75": q[3, j], "p95": q[4, j]})
        print(f"  {nombre:22s} 2050: {np.median(fin[2050]):5.0f} [{np.percentile(fin[2050], 5):.0f}–"
              f"{np.percentile(fin[2050], 95):.0f}]  |  2070: {np.median(fin[2070]):5.0f} "
              f"[{np.percentile(fin[2070], 5):.0f}–{np.percentile(fin[2070], 95):.0f}] %PIB")

    out = pd.DataFrame(filas).round(1)
    out.to_csv(GOLD / "gold_escenarios_deuda_mc.csv", index=False)
    print(f"→ gold_escenarios_deuda_mc.csv ({len(out)} filas)")
    central = out.query("escenario=='central' and year==2050")
    print(f"coherencia con D1 discreto (2050 central 224, banda 198–267): "
          f"MC mediana {central.p50.iloc[0]:.0f}, banda 90 % [{central.p5.iloc[0]:.0f}–{central.p95.iloc[0]:.0f}]")


if __name__ == "__main__":
    main()
