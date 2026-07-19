"""#5 del plan a 50 años: pseudo-backtest de continuidad 1925→1975 y 1975→2025.

¿Cuánto se equivoca una proyección "condicional a continuidad" tras 50 años
REALES? Se sitúa el reloj en 1925 y en 1975 y se proyecta el gasto y el
ingreso público (% PIB) de cada país del panel histórico con las dos reglas
de continuidad que usaría cualquier simulador sin información del futuro:

- congelar el nivel del año base,
- extrapolar la tendencia lineal de los 15 años previos.

El error a +50 años contra lo observado NO valida nada (solo hay 2 ventanas
independientes): CALIBRA la anchura mínima que debe tener cualquier sobre a
50 años. Ese es todo el poder estadístico que existe — y más del que declaran
la mayoría de los ejercicios a 2070.

Salida: gold_backtest_50y.csv + lectura impresa.

    python3 analysis/backtest_50y.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from backtest_t1 import GOLD


def main() -> None:
    d = pd.read_csv(GOLD / "gold_fiscal_historico.csv")
    filas = []
    for (y_base, y_fin) in [(1925, 1975), (1975, 2025)]:
        for iso, g in d.groupby("iso3"):
            g = g.set_index("year").sort_index()
            for lado in ("exp_gdp", "rev_gdp"):
                s = g[lado].dropna()
                fin = s.loc[[y for y in range(y_fin - 2, y_fin + 1) if y in s.index]].mean()
                if y_base not in s.index or pd.isna(fin):
                    continue
                base = s.loc[y_base]
                prev = s.loc[[y for y in range(y_base - 15, y_base + 1) if y in s.index]]
                filas.append({"iso3": iso, "ventana": f"{y_base}->{y_fin}", "lado": lado,
                              "base": base, "observado_fin": fin,
                              "err_congelar": fin - base,
                              "err_tendencia": fin - (base + np.polyfit(prev.index, prev.values, 1)[0] * 50)
                              if len(prev) >= 8 else np.nan})
    t = pd.DataFrame(filas)
    t.round(1).to_csv(GOLD / "gold_backtest_50y.csv", index=False)

    print(f"pseudo-backtest de continuidad: {t.iso3.nunique()} países × 2 ventanas × 2 lados "
          f"= {len(t)} proyecciones a +50 años")
    for v, g in t.groupby("ventana"):
        print(f"\n  {v} (n={len(g)}):")
        for regla in ("err_congelar", "err_tendencia"):
            e = g[regla].dropna().abs()
            print(f"    {regla:14s}: |error| mediana {e.median():5.1f} pp de PIB, "
                  f"p90 {e.quantile(0.9):5.1f} pp")
    es = t[(t.iso3 == "ESP") & (t.ventana == "1975->2025") & (t.lado == "exp_gdp")]
    if len(es):
        r = es.iloc[0]
        print(f"\n  ESP gasto 1975→2025: base {r.base:.1f} → observado {r.observado_fin:.1f} "
              f"(congelar se equivoca {r.err_congelar:+.1f} pp: la transición fiscal es EXACTAMENTE "
              f"lo que la continuidad no puede ver)")
    med = t[t.ventana == "1975->2025"].err_congelar.abs().median()
    print(f"\nCALIBRACIÓN: cualquier sobre a 50 años estrecho de menos de ~{med:.0f} pp de PIB "
          f"finge una certeza que 300 años de datos propios desmienten.")


if __name__ == "__main__":
    main()
