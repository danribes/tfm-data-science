"""Cuota hipotecaria teórica por CCAA — el complemento que pidió el tutor.

Cierra el compromiso del PLAN_MAESTRO §7.2 y la Entrega 4 con todos los
ingredientes ya en casa:
- €/m²: valor tasado MITMA 2010–2014 (ancla) llevado a 2024 con el IPV PROPIO
  de cada CCAA (puente declarado: eur_m2_2024 = eur_m2_2014 × IPV24/IPV14).
- Hipoteca tipo declarada: 90 m², LTV 80 %, 25 años, tipo = Euríbor 12m medio
  del año + 1,0 pp de diferencial.
- Esfuerzo = cuota mensual / salario bruto mensual (EES/12).

Salida: storage/gold/gold_cuota_teorica.csv + contraste con el ratio índice.

    python3 analysis/cuota_teorica.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from backtest_t1 import GOLD

PROCESSED = GOLD.parent / "processed"

M2, LTV, ANIOS, DIFERENCIAL = 90.0, 0.80, 25, 1.0
ANIO_REF = 2024


def cuota_mensual(principal: float, tipo_anual_pct: float, anios: int) -> float:
    i = tipo_anual_pct / 100 / 12
    n = anios * 12
    return principal * i / (1 - (1 + i) ** -n)


def main() -> None:
    vt = pd.read_csv(PROCESSED / "mitma_valor_tasado_ccaa.csv")
    ancla = vt[vt.anyo == 2014].groupby("ccaa").eur_m2.mean().rename("eur_m2_2014")

    q = pd.read_csv(GOLD / "gold_ccaa_trimestral.csv")
    ipv14 = q[q.anyo == 2014].groupby("ccaa").ipv_idx15.mean()
    ipv24 = q[q.anyo == ANIO_REF].groupby("ccaa").ipv_idx15.mean()
    sal24 = q[(q.anyo == ANIO_REF) & (q.salario_flag == "observado")].groupby("ccaa").salario_anual.first()

    eur = pd.read_csv(PROCESSED / "euribor_12m.csv")
    eur["anyo"] = eur.month.str[:4].astype(int)
    euribor24 = eur[eur.anyo == ANIO_REF].euribor_12m.mean()
    tipo = euribor24 + DIFERENCIAL

    t = pd.concat([ancla, ipv14.rename("ipv14"), ipv24.rename("ipv24"), sal24.rename("salario")], axis=1).dropna()
    t["eur_m2_2024"] = t.eur_m2_2014 * t.ipv24 / t.ipv14
    t["precio_vivienda"] = t.eur_m2_2024 * M2
    t["cuota_mensual"] = [cuota_mensual(p * LTV, tipo, ANIOS) for p in t.precio_vivienda]
    t["esfuerzo_pct"] = t.cuota_mensual / (t.salario / 12) * 100

    ratio = pd.read_csv(GOLD / "gold_asequibilidad_ccaa.csv").query("anyo==@ANIO_REF").set_index("ccaa").ratio_asequibilidad
    t["ratio_aseq_2024"] = ratio

    out = t.round(2).reset_index().rename(columns={"index": "ccaa"})
    out["supuestos"] = f"{M2:.0f}m2 LTV{LTV:.0%} {ANIOS}a Euribor24({euribor24:.2f})+{DIFERENCIAL}pp; ancla MITMA 2014 x IPV propio"
    out.to_csv(GOLD / "gold_cuota_teorica.csv", index=False)

    print(f"tipo hipotecario supuesto: {tipo:.2f} % (Euríbor12m medio {ANIO_REF} = {euribor24:.2f})")
    cols = ["eur_m2_2024", "precio_vivienda", "cuota_mensual", "esfuerzo_pct", "ratio_aseq_2024"]
    print(out.set_index("ccaa")[cols].sort_values("esfuerzo_pct", ascending=False).head(8).to_string())
    nac = out[out.ccaa == "Nacional"].iloc[0]
    print(f"\nNACIONAL: {nac.eur_m2_2024:,.0f} €/m² → vivienda tipo {nac.precio_vivienda:,.0f} € → "
          f"cuota {nac.cuota_mensual:,.0f} €/mes = {nac.esfuerzo_pct:.1f} % del salario bruto")
    sub = out[~out.ccaa.isin(["Nacional"])]
    rho = sub.esfuerzo_pct.corr(sub.ratio_aseq_2024, method="spearman")
    print(f"Spearman(esfuerzo teórico, ratio índice) entre CCAA: {rho:.2f} — "
          "el ratio aproximado y la medida de esfuerzo real ordenan las CCAA de forma "
          f"{'muy similar' if rho > 0.7 else 'solo parcialmente coincidente'}")


if __name__ == "__main__":
    main()
