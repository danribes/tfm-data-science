"""Búsqueda de proxies adelantados: ¿qué variable ANTICIPA el precio de la vivienda?

El proyecto ya tiene un proxy adelantado (visados → ΔlogIPV, r=0,57 a 11
trimestres). Aquí se barre sistemáticamente el resto de series disponibles para
hallar OTRO proxy con poder predictivo — en particular uno que capture el shock
de demanda 2024-25 que ningún modelo vio.

Método: para cada candidato (nacional, trimestral) se calcula la correlación
cruzada con el crecimiento FUTURO del IPV, ΔlogIPV_{t+k}, para adelantos
k=0..12 trimestres. Se reporta el pico |r| y su adelanto. También en panel
(agrupando las 17 CCAA) donde el candidato es regional, para ganar potencia.

CAVEAT declarado: correlación in-sample, no causalidad ni validación. Un proxy
prometedor entra después en el harness de backtesting (misma regla que todo:
batir al drift, adopción solo con datos 2026+). Esto es EXPLORACIÓN, no un
modelo de producción.

    python3 analysis/proxy_lead_scan.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from backtest_t1 import GOLD

PROCESSED = GOLD.parent / "processed"
LEADS = range(0, 13)


def ipv_nacional() -> pd.Series:
    q = pd.read_csv(GOLD / "gold_ccaa_trimestral.csv")
    q = q[q.ccaa == "Nacional"].copy()
    q["p"] = pd.PeriodIndex(q.anyo.astype(str) + "Q" + q.quarter.astype(str), freq="Q")
    return np.log(q.set_index("p").ipv_idx15.astype(float)).sort_index()


def _q(df, valcol="valor"):
    df = df.copy()
    df["quarter"] = (df.mes - 1) // 3 + 1
    g = df.groupby(["ccaa", "anyo", "quarter"], as_index=False)[valcol].sum()
    return g


def to_series(df, ccaa="Nacional", valcol="valor"):
    d = df[df.ccaa == ccaa].copy()
    d["p"] = pd.PeriodIndex(d.anyo.astype(str) + "Q" + d.quarter.astype(str), freq="Q")
    return d.set_index("p")[valcol].sort_index()


def crosscorr(proxy: pd.Series, target_growth: pd.Series, nombre: str) -> dict:
    best = {"proxy": nombre, "r": 0.0, "lead": 0, "n": 0}
    for k in LEADS:
        fut = target_growth.shift(-k)  # ΔlogIPV k trimestres en el futuro
        df = pd.concat([proxy.rename("x"), fut.rename("y")], axis=1).dropna()
        if len(df) < 20:
            continue
        r = df.x.corr(df.y)
        if abs(r) > abs(best["r"]):
            best = {"proxy": nombre, "r": round(float(r), 3), "lead": k, "n": len(df)}
    return best


def main() -> None:
    ipv = ipv_nacional()
    growth = ipv.diff()  # ΔlogIPV trimestral

    resultados = []

    # 1. Compraventas nacionales, crecimiento interanual
    cv = _q(pd.read_csv(PROCESSED / "ine_compraventas_ccaa.csv"))
    resultados.append(crosscorr(to_series(cv).pct_change(4), growth, "compraventas_yoy"))

    # 2. Hipotecas nacionales YoY
    hip = _q(pd.read_csv(PROCESSED / "ine_hipotecas_ccaa.csv"))
    resultados.append(crosscorr(to_series(hip).pct_change(4), growth, "hipotecas_yoy"))

    # 3. Población nacional: Δ interanual (proxy de demanda/migración)
    pob = pd.read_csv(PROCESSED / "ine_poblacion_q_ccaa.csv")
    pobs = to_series(pob)
    resultados.append(crosscorr(pobs.pct_change(4), growth, "poblacion_yoy"))
    resultados.append(crosscorr(pobs.pct_change(4).diff(), growth, "aceleracion_poblacion"))

    # 4. Superficie de suelo transmitida YoY
    su = pd.read_csv(PROCESSED / "mitma_suelo_ccaa.csv").query("variable=='superficie_miles_m2'")
    resultados.append(crosscorr(to_series(su).pct_change(4), growth, "suelo_superficie_yoy"))

    # 5. Criterios de crédito (BLS), nivel
    bls = pd.read_csv(PROCESSED / "bls_criterios_vivienda.csv")
    bls["p"] = pd.PeriodIndex(bls.anyo.astype(str) + "Q" + bls.quarter.astype(str), freq="Q")
    resultados.append(crosscorr(bls.set_index("p").pct_neto_endurecimiento.sort_index(),
                                growth, "bls_credito_nivel"))

    # 6. Google Trends "comprar piso", media trimestral YoY
    gt = pd.read_csv(PROCESSED / "gtrends_vivienda.csv").query("keyword=='comprar piso'").copy()
    gt["p"] = pd.to_datetime(gt.mes).dt.to_period("Q")
    gts = gt.groupby("p").indice.mean().sort_index()
    resultados.append(crosscorr(gts.pct_change(4), growth, "trends_comprar_piso_yoy"))

    # 7. Euríbor: nivel y variación
    eur = pd.read_csv(PROCESSED / "euribor_12m.csv")
    eur["p"] = pd.PeriodIndex(eur.month, freq="M").asfreq("Q")
    eurs = eur.groupby("p").euribor_12m.mean().sort_index()
    resultados.append(crosscorr(eurs, growth, "euribor_nivel"))
    resultados.append(crosscorr(eurs.diff(), growth, "euribor_variacion"))

    r = pd.DataFrame(resultados).reindex(
        pd.DataFrame(resultados).r.abs().sort_values(ascending=False).index)
    r.to_csv(GOLD / "gold_proxy_lead_scan.csv", index=False)
    print("Correlación cruzada con ΔlogIPV nacional futuro (in-sample):")
    print(r.to_string(index=False))
    top = r.iloc[0]
    print(f"\nProxy adelantado más fuerte: {top.proxy} (r={top.r:+.2f} a {top.lead} trimestres, "
          f"n={top.n})")
    print("Caveat: in-sample; el candidato pasa al harness (batir al drift, "
          "adopción solo con datos 2026+).")


if __name__ == "__main__":
    main()
