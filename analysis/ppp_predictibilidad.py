"""¿Es predecible la renta en paridad de poder adquisitivo (PPA/PPP)?

Misma disección que el resto del proyecto: NIVEL vs EVOLUCIÓN, y predicción
solo como algo condicional o con vara honesta.

PPA aquí = PIB per cápita en dólares internacionales (gdp_pc_ppp, WDI, 242
países 1995–2023). Tres pruebas:

1. NIVEL: ¿cuán persistente es? (drift como vara, error out-of-sample 2019–23).
2. CRECIMIENTO: ¿es predecible el crecimiento en sí? (autocorrelación AR(1)).
3. CONVERGENCIA (beta): ¿los países pobres crecen más rápido y "alcanzan"?
   La regresión clásica crecimiento ~ nivel inicial, con la CAUTELA declarada
   de la falacia de Galton (reversión a la media puede fingir convergencia).

Salida: gold/gold_ppp_predictibilidad.csv + lectura impresa.

    python3 analysis/ppp_predictibilidad.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from backtest_t1 import GOLD

PROCESSED = GOLD.parent / "processed"


# códigos agregados WDI (no son países): se excluyen para un recuento honesto
WDI_AGREGADOS = {
    "AFE", "AFW", "ARB", "CEB", "CSS", "EAP", "EAR", "EAS", "ECA", "ECS", "EMU",
    "EUU", "FCS", "HIC", "HPC", "IBD", "IBT", "IDA", "IDB", "IDX", "INX", "LAC",
    "LCN", "LDC", "LIC", "LMC", "LMY", "LTE", "MEA", "MIC", "MNA", "NAC", "OED",
    "OSS", "PRE", "PSS", "PST", "SAS", "SSA", "SSF", "SST", "TEA", "TEC", "TLA",
    "TMN", "TSA", "TSS", "UMC", "WLD", "EAR", "V1", "V2", "V3", "V4", "XKX",
}


def panel() -> pd.DataFrame:
    d = pd.read_csv(PROCESSED / "wdi_outcomes.csv").query("variable=='gdp_pc_ppp' and value>0")
    d = d[~d.iso3.isin(WDI_AGREGADOS)]
    d = d[["iso3", "year", "value"]].copy()
    d["log"] = np.log(d.value)
    n = d.groupby("iso3").size()
    return d[d.iso3.isin(n[n >= 20].index)].sort_values(["iso3", "year"])


def main() -> None:
    d = panel()
    d["growth"] = d.groupby("iso3").log.diff()
    filas = []

    # --- 1. NIVEL: drift vs naive out-of-sample (2019-2023) ---
    errs_drift, errs_naive = [], []
    for iso, g in d.groupby("iso3"):
        g = g.dropna(subset=["log"]).set_index("year").log
        if g.index.max() < 2023 or 2018 not in g.index:
            continue
        train = g[g.index <= 2018]
        drift = (train.iloc[-1] - train.iloc[0]) / (len(train) - 1)
        for h, y in enumerate(range(2019, 2024), start=1):
            if y not in g.index:
                continue
            pred_drift = train.iloc[-1] + drift * h
            pred_naive = train.iloc[-1]
            errs_drift.append(abs(g[y] - pred_drift))
            errs_naive.append(abs(g[y] - pred_naive))
    mae_d, mae_n = np.mean(errs_drift), np.mean(errs_naive)
    print(f"1) NIVEL (log PPA), pronóstico 2019–23 fuera de muestra:")
    print(f"   MAE drift {mae_d:.4f} vs naive {mae_n:.4f} → el nivel es MUY predecible "
          f"(persistencia extrema); el drift {'gana' if mae_d < mae_n else 'no gana'}")
    filas.append({"prueba": "nivel_ppa", "metrica": "MAE_log", "drift": round(mae_d, 4),
                  "naive": round(mae_n, 4)})

    # --- 2. CRECIMIENTO: ¿autocorrelación? ---
    g2 = d.dropna(subset=["growth"]).copy()
    g2["growth_l1"] = g2.groupby("iso3").growth.shift(1)
    gg = g2.dropna(subset=["growth", "growth_l1"])
    # within-country: quitar media país
    gg = gg.assign(gd=gg.growth - gg.groupby("iso3").growth.transform("mean"),
                   gl=gg.growth_l1 - gg.groupby("iso3").growth_l1.transform("mean"))
    ar1 = gg.gd.corr(gg.gl)
    print(f"\n2) CRECIMIENTO: autocorrelación AR(1) within-country = {ar1:+.2f} "
          f"(n={len(gg)}) → el crecimiento en sí es {'algo' if abs(ar1)>0.2 else 'poco'} predecible")
    filas.append({"prueba": "crecimiento_ar1", "metrica": "corr", "drift": round(float(ar1), 3),
                  "naive": None})

    # --- 3. CONVERGENCIA beta ---
    piv = d.pivot_table(index="iso3", columns="year", values="log")
    y0, y1 = 1995, 2023
    c = piv[[y0, y1]].dropna()
    c.columns = ["l0", "l1"]
    c["growth_total"] = (c.l1 - c.l0) / (y1 - y0)  # crecimiento medio anual
    beta = np.polyfit(c.l0, c.growth_total, 1)[0]
    rho = c.l0.corr(c.growth_total)
    # media-vida de convergencia si beta<0
    conv = -beta
    print(f"\n3) CONVERGENCIA (1995→2023, {len(c)} países): pendiente crecimiento~nivel_inicial "
          f"= {beta:+.4f} (corr {rho:+.2f})")
    if beta < 0:
        print(f"   → convergencia beta ~{conv*100:.1f} pp/año por unidad de log-renta. "
              "VERIFICADO adversarialmente (docs/ppp_predictibilidad.md): real y robusta a "
              "Galton, outliers y ventana, PERO es convergencia de CLUB — los países más "
              "pobres NO convergen (p=0,37); media-vida ~147 años.")
    else:
        print("   → divergencia: los ricos crecen más (no hay catch-up incondicional)")
    filas.append({"prueba": "convergencia_beta", "metrica": "pendiente", "drift": round(float(beta), 4),
                  "naive": round(float(rho), 3)})

    esp = c.loc["ESP"] if "ESP" in c.index else None
    if esp is not None:
        print(f"\n   España: log-renta 1995 {esp.l0:.2f} → 2023 {esp.l1:.2f}; "
              f"crecimiento medio {esp.growth_total*100:.1f} %/año")

    out = pd.DataFrame(filas)
    out.to_csv(GOLD / "gold_ppp_predictibilidad.csv", index=False)
    print("\nSÍNTESIS: la PPA es MUY predecible como NIVEL (persistencia, drift), "
          "POCO como crecimiento año a año, y PARCIALMENTE vía convergencia (con la cautela "
          "de Galton). Como todo en el proyecto: nivel trivial, giros difíciles, "
          "escenario condicional el uso honesto. → gold_ppp_predictibilidad.csv")


if __name__ == "__main__":
    main()
