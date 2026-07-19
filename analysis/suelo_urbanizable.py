"""Suelo urbanizable por CCAA: stock planificado (SIU) + flujo transmitido (MITMA).

Respuesta a "¿cuánto suelo urbanizable hay y cómo evoluciona?":
- STOCK: SIU (planes municipales), % de la superficie estudiada clasificado
  urbanizable (delimitado + no delimitado), añadas 2021 y 2025. La cobertura
  municipal cambia entre añadas → se comparan PORCENTAJES y la cobertura viaja
  en la tabla (declarado).
- FLUJO: superficie de transacciones de suelo (miles m², trimestral 2004–),
  agregada a años: cuánto suelo cambia de manos — el termómetro vivo.

Salida: gold/gold_suelo_ccaa.csv (stock) + figura evolución del flujo.

    python3 analysis/suelo_urbanizable.py
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from backtest_t1 import GOLD

PROCESSED = GOLD.parent / "processed"
FIGS = GOLD.parents[1] / "docs" / "figures" / "atlas"
BLUE, GREEN, ORANGE, RED = "#2a78d6", "#008300", "#eb6834", "#e34948"
SURFACE = "#fcfcfb"

SIU2INE = {
    "Asturias, Principado de": "Asturias, Principado de", "Balears, Illes": "Balears, Illes",
    "Castilla-La Mancha": "Castilla - La Mancha",
}


def main() -> None:
    siu = pd.read_csv(PROCESSED / "siu_clases_suelo_ccaa.csv")
    siu["ccaa"] = siu.ccaa_siu.map(lambda c: SIU2INE.get(c, c))
    w = siu.pivot_table(index="ccaa", columns="vintage",
                        values=["pct_urbanizable_delimitado", "pct_urbanizable_no_delimitado",
                                "km2_urbanizable", "km2_estudiado", "cobertura_mun_pct"])
    out = pd.DataFrame({
        "pct_urbanizable_2021": w.pct_urbanizable_delimitado[2021] + w.pct_urbanizable_no_delimitado[2021],
        "pct_urbanizable_2025": w.pct_urbanizable_delimitado[2025] + w.pct_urbanizable_no_delimitado[2025],
        "km2_urbanizable_2025": w.km2_urbanizable[2025],
        "km2_estudiado_2025": w.km2_estudiado[2025],
        "cobertura_2021_pct": w.cobertura_mun_pct[2021],
        "cobertura_2025_pct": w.cobertura_mun_pct[2025],
    })
    out["delta_pct_puntos"] = out.pct_urbanizable_2025 - out.pct_urbanizable_2021
    out = out.round(3).reset_index()
    out.to_csv(GOLD / "gold_suelo_ccaa.csv", index=False)

    print("STOCK urbanizable (% superficie estudiada) 2021 → 2025:")
    top = out.sort_values("pct_urbanizable_2025", ascending=False).head(6)
    for _, r in top.iterrows():
        print(f"  {r.ccaa:32s} {r.pct_urbanizable_2021:5.2f}% → {r.pct_urbanizable_2025:5.2f}% "
              f"({r.km2_urbanizable_2025:,.0f} km²; cobertura {r.cobertura_2021_pct:.0f}%→{r.cobertura_2025_pct:.0f}%)")

    su = pd.read_csv(PROCESSED / "mitma_suelo_ccaa.csv").query("variable=='superficie_miles_m2'")
    anual = su.groupby(["ccaa", "anyo"]).valor.sum().div(1000).reset_index()  # → millones m²
    nac = anual.query("ccaa=='Nacional' and anyo<=2025")
    print(f"\nFLUJO nacional (superficie transmitida, millones m²): "
          f"pico {nac.valor.max():,.0f} ({int(nac.loc[nac.valor.idxmax(), 'anyo'])}), "
          f"mínimo {nac.valor.min():,.0f} ({int(nac.loc[nac.valor.idxmin(), 'anyo'])}), "
          f"2024 = {nac.query('anyo==2024').valor.iloc[0]:,.0f}")

    fig, ax = plt.subplots(figsize=(7.5, 4.0), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.plot(nac.anyo, nac.valor, color=BLUE, lw=2, marker="o", ms=3)
    ax.axvspan(2008, 2013, color=RED, alpha=0.08)
    ax.set_title("Superficie de transacciones de suelo, España (millones de m²/año)", fontsize=10)
    ax.grid(alpha=0.3)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGS / "b17_suelo_transacciones.png", dpi=150)
    print(f"figura → {FIGS / 'b17_suelo_transacciones.png'}")


if __name__ == "__main__":
    main()
