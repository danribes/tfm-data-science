"""#4 del plan a 50 años: sobres CONDICIONALES de bienestar 2050/2070.

Encadena las únicas piezas con legitimidad estadística para ese horizonte:
- crecimiento de la renta → mortalidad infantil vía γ del PANEL within
  (−0,509 ± 0,059 por unidad de log-PIBpc — identificado dentro de país,
  neto de la mejora secular mundial que absorben los efectos de año);
- capacidad fiscal → mortalidad vía el β del panel a RETARDO 8 (−0,0036 ±
  0,0015 por pp de PIB de ingresos: el efecto es estructural, nulo a 2-5
  años — hallazgo del gradiente, declarado);
- la mejora secular (δ_t) NO se extrapola: los sobres son variaciones
  RELATIVAS a la senda base que resulte, no niveles absolutos de mortalidad.

Todo es menú, no pronóstico: el usuario elige crecimiento y capacidad fiscal;
el sistema devuelve el efecto multiplicativo sobre la mortalidad <5 con IC95
de los parámetros (independencia aproximada, declarada).

Salida: gold_bienestar_50.csv + lectura impresa.

    python3 analysis/bienestar_50.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from backtest_t1 import GOLD

ROOT = GOLD.parents[1]

ESCENARIOS_G = {"estancamiento": 0.5, "central": 1.0, "dinamico": 1.5}   # % real pc/año
ESCENARIOS_REV = {"recorte_2_5pp": -2.5, "constante": 0.0, "refuerzo_2_5pp": +2.5}


def main() -> None:
    p = json.load(open(ROOT / "api" / "models" / "bienestar_panel_params.json"))
    g_gdp, se_g = p["beta_loggdp_within"], p["se_loggdp_within_cr1"]
    b_rev, se_rev = p["gradiente_retardos"]["8"]["beta"], p["gradiente_retardos"]["8"]["se"]
    print(f"parámetros panel: γ_PIB {g_gdp:+.3f}±{se_g:.3f}; β_ingresos(lag8) {b_rev:+.4f}±{se_rev:.4f}")

    filas = []
    for year, anios in [(2050, 26), (2070, 46)]:
        for ng, g in ESCENARIOS_G.items():
            for nr, dr in ESCENARIOS_REV.items():
                dlog_gdp = np.log((1 + g / 100) ** anios)
                efecto = g_gdp * dlog_gdp + b_rev * dr
                var = (se_g * dlog_gdp) ** 2 + (se_rev * dr) ** 2
                lo, hi = efecto - 1.96 * np.sqrt(var), efecto + 1.96 * np.sqrt(var)
                filas.append({
                    "year": year, "crecimiento": ng, "ingresos": nr,
                    "delta_mortalidad_pct": (np.exp(efecto) - 1) * 100,
                    "ic95_lo_pct": (np.exp(lo) - 1) * 100,
                    "ic95_hi_pct": (np.exp(hi) - 1) * 100,
                })
    out = pd.DataFrame(filas).round(1)
    out.to_csv(GOLD / "gold_bienestar_50.csv", index=False)

    print("\nSobre condicional (Δ% mortalidad <5 vs senda base, IC95):")
    for year in (2050, 2070):
        print(f"  {year}:")
        for _, r in out[out.year == year].query("ingresos=='constante'").iterrows():
            print(f"    crecimiento {r.crecimiento:14s}: {r.delta_mortalidad_pct:+6.1f} % "
                  f"[{r.ic95_lo_pct:+.1f}, {r.ic95_hi_pct:+.1f}]")
        c = out[(out.year == year) & (out.crecimiento == "central")]
        base = c[c.ingresos == "constante"].delta_mortalidad_pct.iloc[0]
        ref = c[c.ingresos == "refuerzo_2_5pp"].delta_mortalidad_pct.iloc[0]
        print(f"    palanca fiscal ±2,5 pp sobre central: {ref - base:+.1f} % adicional "
              f"(pequeña frente al crecimiento — el hallazgo del panel)")
    print("\nLectura: el crecimiento de la renta domina el sobre; la capacidad fiscal "
          "aporta un efecto estructural real pero de segundo orden a estos retardos. "
          "Niveles absolutos NO se proyectan (la mejora secular no se extrapola).")


if __name__ == "__main__":
    main()
