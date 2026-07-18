"""D1 — Simulador de escenarios fiscales para España (deuda, aritmética r−g).

Responde la pregunta D1 reformulada del PLAN_MAESTRO: dadas sendas
alternativas (composición del gasto, consolidación, tipos, crecimiento),
¿qué trayectorias de deuda proyecta la aritmética estándar, con qué
incertidumbre? Es un MENÚ con consecuencias modeladas — elegir es política,
no estadística, y el propio output lo dice.

Mecánica: d_{t+1} = d_t·(1+r_t)/(1+g_t) − pb_t
- r_t: tipo efectivo (intereses/deuda, 2,3 % en 2023) que converge al tipo
  de mercado del escenario con velocidad 1/8 (vencimiento medio ~8 años).
- g_t: crecimiento nominal = real (palanca) + deflactor 2 %.
- pb_t: saldo primario = estructural 2024 (−0,9 %PIB) − presión demográfica
  + palanca del escenario. La presión demográfica sale del MOTOR DE
  PROYECCIÓN del repo: pensiones y sanidad escalan con la senda de
  población 65+ de Eurostat (variante BSL; las 6 variantes dan la banda)
  con las elasticidades entrenadas en el panel UE (0,91 y 0,33).

Horizonte 2024–2050 (más allá, la aritmética compuesta es especulación).

    python3 analysis/escenarios_d1.py
"""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from backtest_t1 import GOLD

ROOT = GOLD.parents[1]
FIG = ROOT / "docs" / "figures" / "d1"
FIG.mkdir(parents=True, exist_ok=True)

BLUE, GREEN, ORANGE, VIOLET, AQUA, RED = "#2a78d6", "#008300", "#eb6834", "#4a3aa7", "#1baf7a", "#e34948"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e5e4e0"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "savefig.dpi": 150,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2,
    "ytick.color": INK2, "axes.edgecolor": GRID, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
    "axes.spines.right": False, "font.size": 9, "axes.titlesize": 10,
})

Y0, Y1 = 2024, 2050
BASE = {
    "debt0": 105.2,        # %PIB 2023 (gold_panel_anual)
    "r0": 2.4 / 105.2 * 100,  # tipo efectivo = intereses/deuda ≈ 2,28 %
    "pb0": -3.3 + 2.4,     # saldo primario 2023 = déficit + intereses = −0,9
    "deflactor": 2.0,
    "vencimiento": 8,      # años (velocidad de traslado del tipo de mercado)
}


def presion_demografica(variant: str = "BSL") -> pd.Series:
    """Δ(pensiones+sanidad) %PIB respecto a 2024, por año, según el motor."""
    p = json.load(open(ROOT / "api" / "models" / "projection_params.json"))
    pr = pd.read_csv(GOLD / "gold_projections.csv").query("geo=='ES'")
    s65 = pr[pr.variant == variant].set_index("year")["share65"]
    s65 = s65.reindex(range(Y0, Y1 + 1)).interpolate()
    out = pd.Series(0.0, index=s65.index)
    for mod, spend_key in [("pensions", "pensions_oldage"), ("health", "te_gf07")]:
        b = p[mod]["base"]["ES"]
        beta65 = p[mod]["beta"][p[mod]["drivers"].index("l_pop65_share")]
        spend = b[spend_key] * (s65 / b["pop65_share"]) ** beta65
        out = out + (spend - spend.iloc[0])
    return out


def simula(nombre: str, r_mkt: float, g_real: float, pb_palanca,
           variant: str = "BSL", con_demografia: bool = True) -> pd.DataFrame:
    """pb_palanca: función year -> ajuste en pp sobre el pb estructural."""
    demog = presion_demografica(variant) if con_demografia else pd.Series(0.0, index=range(Y0, Y1 + 1))
    d, r = BASE["debt0"], BASE["r0"]
    g = g_real + BASE["deflactor"]
    rows = []
    for y in range(Y0, Y1 + 1):
        r = r + (r_mkt - r) / BASE["vencimiento"]
        pb = BASE["pb0"] - demog.loc[y] + pb_palanca(y)
        d = d * (1 + r / 100) / (1 + g / 100) - pb
        rows.append({"escenario": nombre, "year": y, "deuda": d, "pb": pb,
                     "r_efectivo": r, "g_nominal": g, "presion_demog": demog.loc[y]})
    return pd.DataFrame(rows)


def main():
    cero = lambda y: 0.0
    escenarios = {
        # nombre: (r_mercado, crecimiento_real, palanca_pb, color, etiqueta)
        "central": (3.5, 1.3, cero, BLUE, "central: presión demográfica sin respuesta"),
        "sin_demografia": (3.5, 1.3, cero, INK2, "contrafactual sin envejecimiento"),
        "consolidacion": (3.5, 1.3, lambda y: min(0.25 * max(y - 2025, 0), 2.5), GREEN,
                          "consolidación gradual (+0,25 pp/año hasta +2,5)"),
        "inversion": (3.5, 1.3, lambda y: -1.0 if y <= 2035 else 0.0, ORANGE,
                      "+1 pp inversión (vivienda+FBCF) 2025–35 a deuda"),
        "tipos_altos": (4.5, 1.3, cero, RED, "tipos de mercado al 4,5 %"),
        "crecimiento": (3.5, 2.0, cero, AQUA, "crecimiento real 2 % (productividad/migración)"),
    }
    frames = []
    for k, (rm, gr, pal, _, _) in escenarios.items():
        frames.append(simula(k, rm, gr, pal, con_demografia=(k != "sin_demografia")))
    df = pd.concat(frames, ignore_index=True)

    # banda de incertidumbre del central: 6 variantes demográficas × tipos ±0,5
    paths = []
    for v in ["BSL", "HMIGR", "LFRT", "LMIGR", "LMRT", "NMIGR"]:
        for rm in [3.0, 3.5, 4.0]:
            paths.append(simula("central", rm, 1.3, cero, variant=v).set_index("year")["deuda"])
    banda = pd.concat(paths, axis=1)
    lo, hi = banda.min(axis=1), banda.max(axis=1)

    df.round(2).to_csv(GOLD / "gold_escenarios_deuda.csv", index=False)

    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    ax.fill_between(lo.index, lo, hi, color=BLUE, alpha=0.10, lw=0)
    for k, (_, _, _, color, lbl) in escenarios.items():
        d = df[df.escenario == k]
        ax.plot(d.year, d.deuda, color=color, lw=2.0 if k == "central" else 1.5,
                ls="--" if k == "sin_demografia" else "-", label=lbl)
    ax.axhline(60, color=INK2, lw=0.8, ls=":")
    ax.annotate("referencia 60 % (Maastricht)", (2025.2, 61), fontsize=7.5, color=INK2)
    ax.set_ylabel("deuda pública (% del PIB)")
    ax.set_title("D1 · España 2024–2050: menú de escenarios de deuda (aritmética r−g +\n"
                 "presión demográfica del motor de proyección) — elegir es política, no estadística")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG / "d1_deuda_escenarios.png")
    plt.close(fig)

    fin = df[df.year == Y1].set_index("escenario")["deuda"].round(0)
    print("Deuda 2050 por escenario (%PIB):", fin.to_dict())
    print(f"banda central 2050 (variantes demográficas × tipos ±0,5): {lo.loc[Y1]:.0f}–{hi.loc[Y1]:.0f}")
    dm = presion_demografica()
    print(f"presión demográfica BSL: +{dm.loc[2035]:.1f} pp (2035), +{dm.loc[2050]:.1f} pp (2050)")


if __name__ == "__main__":
    main()
