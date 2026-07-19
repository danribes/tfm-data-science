"""Panel internacional de vivienda: precios, esfuerzo y consumo de suelo.

Une las cuatro fuentes de connectors/vivienda_global.py en un gold por país:
- crecimiento REAL de precios 2000→último y 2015→último (BIS, índice real),
- precio/renta disponible último (OECD HPI_YDH, 2015=100): la medida
  comparable de esfuerzo — >100 = la vivienda corre más que la renta,
- consumo de suelo: superficie artificial 2000→2022 (OECD/ESA, km² y %),
- % de suelo artificial (LUCAS 2022, encuesta, solo UE).

Salida: gold/gold_vivienda_global.csv + figura b18 + lectura impresa.

    python3 analysis/vivienda_global.py
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from backtest_t1 import GOLD

PROCESSED = GOLD.parent / "processed"
FIGS = GOLD.parents[1] / "docs" / "figures" / "atlas"
BLUE, GREEN, ORANGE, VIOLET, RED = "#2a78d6", "#008300", "#eb6834", "#4a3aa7", "#e34948"
SURFACE, INK2 = "#fcfcfb", "#555"

BIS2ISO = {"ES": "ESP", "DE": "DEU", "FR": "FRA", "IT": "ITA", "PT": "PRT", "US": "USA",
           "IE": "IRL", "GB": "GBR", "NL": "NLD", "JP": "JPN"}


def main() -> None:
    bis = pd.read_csv(PROCESSED / "bis_precios_vivienda.csv").query("serie=='real'")
    bis["p"] = bis.anyo * 4 + bis.quarter
    ult = bis.sort_values("p").groupby("area").tail(1).set_index("area")
    b2000 = bis.query("anyo==2000").groupby("area").indice.mean()
    b2015 = bis.query("anyo==2015").groupby("area").indice.mean()
    precios = pd.DataFrame({
        "real_desde_2000_pct": (ult.indice / b2000 - 1) * 100,
        "real_desde_2015_pct": (ult.indice / b2015 - 1) * 100,
    })

    oecd = pd.read_csv(PROCESSED / "oecd_precios_vivienda.csv")
    oecd["p"] = oecd.anyo * 4 + oecd.quarter
    pti = (oecd.query("medida=='HPI_YDH'").sort_values("p").groupby("iso3").tail(1)
           .set_index("iso3").valor.rename("precio_renta_2015_100"))

    su = pd.read_csv(PROCESSED / "oecd_suelo_artificial.csv").query("medida=='LC_SUR_ART'")
    s00 = su.query("anyo==2000").set_index("iso3").valor
    s22 = su.query("anyo==2022").set_index("iso3").valor
    suelo = pd.DataFrame({"artificial_2022_km2": s22,
                          "artificial_2000_2022_pct": (s22 / s00 - 1) * 100})

    lucas = pd.read_csv(PROCESSED / "lucas_artificial.csv")
    lu = lucas[lucas.time.astype(str) == "2022"].set_index("geo").value.rename("lucas_artificial_pct")

    iso_bis = {v: k for k, v in BIS2ISO.items()}
    t = pti.to_frame().join(suelo, how="outer")
    t["real_desde_2000_pct"] = t.index.map(lambda i: precios.real_desde_2000_pct.get(iso_bis.get(i, i[:2])))
    t["real_desde_2015_pct"] = t.index.map(lambda i: precios.real_desde_2015_pct.get(iso_bis.get(i, i[:2])))
    t["lucas_artificial_pct"] = t.index.map(lambda i: lu.get(iso_bis.get(i, i[:2])))
    t = t.dropna(subset=["precio_renta_2015_100", "artificial_2022_km2"], how="all")
    out = t.round(2).reset_index().rename(columns={"index": "iso3"})
    out.to_csv(GOLD / "gold_vivienda_global.csv", index=False)

    print(f"panel: {len(out)} países → gold_vivienda_global.csv")
    sel = ["ESP", "DEU", "FRA", "ITA", "PRT", "IRL", "NLD", "USA"]
    cols = ["precio_renta_2015_100", "real_desde_2015_pct", "artificial_2000_2022_pct"]
    print(t.loc[[c for c in sel if c in t.index], cols].round(1).to_string())
    comun = t.dropna(subset=["precio_renta_2015_100", "artificial_2000_2022_pct"])
    rho = comun.precio_renta_2015_100.corr(comun.artificial_2000_2022_pct, method="spearman")
    print(f"\nSpearman(precio/renta, crecimiento suelo artificial 2000-22) = {rho:+.2f} "
          f"sobre {len(comun)} países (descriptivo, no causal)")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), facecolor=SURFACE)
    ax = axes[0]
    ax.set_facecolor(SURFACE)
    colores = {"ES": RED, "DE": BLUE, "FR": VIOLET, "IT": ORANGE, "PT": GREEN, "IE": "#888"}
    for a, c in colores.items():
        d = bis[(bis.area == a) & (bis.anyo >= 1995)].sort_values("p")
        base = d.query("anyo==2015").indice.mean()
        ax.plot(d.anyo + (d.quarter - 1) / 4, d.indice / base * 100, color=c, lw=1.6, label=a)
    ax.axhline(100, color=INK2, lw=0.7, ls="--")
    ax.legend(ncol=3, fontsize=8, frameon=False)
    ax.set_title("Precio REAL de la vivienda (2015=100, BIS)", fontsize=10)
    ax.grid(alpha=0.3)

    ax = axes[1]
    ax.set_facecolor(SURFACE)
    top = pti.dropna().sort_values(ascending=False)
    top = pd.concat([top.head(10), top[top.index == "ESP"]]).drop_duplicates()
    ax.barh(top.index[::-1], top.values[::-1],
            color=[RED if i == "ESP" else BLUE for i in top.index[::-1]])
    ax.axvline(100, color=INK2, lw=0.7, ls="--")
    ax.set_title("Precio / renta disponible, último dato (2015=100, OCDE)", fontsize=10)
    ax.grid(alpha=0.3, axis="x")
    for a in axes:
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGS / "b18_vivienda_global.png", dpi=150)
    print(f"figura → {FIGS / 'b18_vivienda_global.png'}")


if __name__ == "__main__":
    main()
