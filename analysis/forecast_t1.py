"""Pronóstico de producción T1 (MVP): drift + abanico empírico + escenarios.

Cierra el contrato de salida de la Entrega 4 §5 (gold_forecast_ccaa.csv).

- Modelo: drift (ganador del protocolo completo; ver docs/test_final_t1.md).
- Origen de producción: 2025Q4 (fin de la ventana del panel). h = 1–8.
- Intervalos: cuantiles empíricos de los errores RELATIVOS del drift por
  horizonte, usando validación + test final. El test está gastado para
  SELECCIÓN; reutilizarlo para CALIBRAR anchuras se declara y es deliberado:
  sin sus errores, las bandas ignorarían el único episodio fuera de régimen
  observado (2024–25) y quedarían estrechas de más. Bandas asimétricas por
  construcción (el sesgo de subestimación en booms se hereda del dato).
- Escenarios (sobre el RATIO, no sobre el IPV): sendas de crecimiento
  salarial anual {0 %, 2 %, 4 %} desde el último salario observado (EES
  2024). El IPV pronosticado es el mismo en los tres: el escenario mueve el
  denominador — es herramienta de comunicación, no predicción salarial.

    python3 analysis/forecast_t1.py
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from backtest_t1 import GOLD, OUT, drift, load_series

BLUE, GREEN = "#2a78d6", "#008300"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e5e4e0"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "savefig.dpi": 150,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2,
    "ytick.color": INK2, "axes.edgecolor": GRID, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
    "axes.spines.right": False, "font.size": 9, "axes.titlesize": 10,
})

T0 = pd.Period("2025Q4", freq="Q")
H = 8
ESCENARIOS = {"salarios_0pct": 0.0, "central_salarios_2pct": 0.02, "salarios_4pct": 0.04}
FECHA = "2026-07-18"


def cuantiles_error() -> pd.DataFrame:
    """Cuantiles de error relativo del drift por horizonte (validación + test)."""
    val = pd.read_csv(OUT / "backtest_errores.csv").query("metodo=='drift'")
    tst = pd.read_csv(OUT / "test_final_errores.csv").query("metodo=='drift'")
    err = pd.concat([val[["h", "y", "yhat"]], tst[["h", "y", "yhat"]]])
    err["rel"] = (err.y - err.yhat) / err.yhat
    q = err.groupby("h")["rel"].quantile([0.025, 0.10, 0.90, 0.975]).unstack()
    q.columns = ["q025", "q10", "q90", "q975"]
    q["n"] = err.groupby("h").size()
    return q


def main():
    series = load_series()
    q = cuantiles_error()
    salario = pd.read_csv(GOLD / "gold_asequibilidad_ccaa.csv")
    sal24 = salario[salario.anyo == 2024].set_index("ccaa")["salario_idx"]

    rows = []
    for ccaa, s in series.items():
        train = s[s.index <= T0]
        preds = drift(train, H)
        k = min(8, len(train) - 1)
        slope = (train.iloc[-1] - train.iloc[-1 - k]) / k
        expl = (f"drift: tendencia de los últimos {k} trimestres "
                f"({slope:+.2f} pts/trimestre); banda = cuantiles empíricos de "
                f"los errores de backtesting (validación + test, declarado)")
        for h, yhat in enumerate(preds, start=1):
            t = T0 + h
            anios = (t.year + (t.quarter - 1) / 4) - 2024.0
            for esc, g in ESCENARIOS.items():
                sal = float(sal24.get(ccaa, np.nan)) * (1 + g) ** anios
                rows.append({
                    "ccaa": ccaa, "periodo_origen": str(T0), "periodo_pred": str(t),
                    "h": h, "ipv_pred": round(yhat, 2),
                    "pi_80_low": round(yhat * (1 + q.loc[h, "q10"]), 2),
                    "pi_80_high": round(yhat * (1 + q.loc[h, "q90"]), 2),
                    "pi_95_low": round(yhat * (1 + q.loc[h, "q025"]), 2),
                    "pi_95_high": round(yhat * (1 + q.loc[h, "q975"]), 2),
                    "escenario": esc,
                    "ratio_aseq_pred": round(yhat / sal, 4) if np.isfinite(sal) else np.nan,
                    "modelo": "drift", "fecha_ejecucion": FECHA, "explicacion": expl,
                })
    df = pd.DataFrame(rows)
    assert df.duplicated(subset=["ccaa", "periodo_pred", "escenario"]).sum() == 0
    # las bandas empíricas son asimétricas y en h=8 el cuantil 10 es positivo
    # (el drift se queda corto de forma sistemática): NO se exige que el punto
    # caiga dentro de la banda, solo que las bandas estén bien ordenadas
    assert ((df.pi_95_low <= df.pi_80_low) & (df.pi_80_low <= df.pi_80_high)
            & (df.pi_80_high <= df.pi_95_high)).all()
    df.to_csv(GOLD / "gold_forecast_ccaa.csv", index=False)

    # figura: abanico nacional
    s = series["Nacional"]
    hist = s[s.index >= pd.Period("2019Q1", freq="Q")]
    d = df[(df.ccaa == "Nacional") & (df.escenario == "central_salarios_2pct")].sort_values("h")
    fut = pd.PeriodIndex(d.periodo_pred, freq="Q").to_timestamp()
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    ax.plot(hist.index.to_timestamp(), hist.values, color=BLUE, lw=1.8)
    ax.fill_between(fut, d.pi_95_low, d.pi_95_high, color=BLUE, alpha=0.12, lw=0)
    ax.fill_between(fut, d.pi_80_low, d.pi_80_high, color=BLUE, alpha=0.22, lw=0)
    ax.plot(fut, d.ipv_pred, color=BLUE, lw=1.6, ls="--")
    ax.axvline(T0.to_timestamp(how="end"), color=INK2, lw=0.8)
    ax.annotate("pronóstico drift\n(banda 80/95 % empírica,\nasimétrica al alza)",
                (fut[4], float(d.pi_95_high.iloc[4])), color=INK2, fontsize=8,
                xytext=(0, 8), textcoords="offset points", ha="center")
    ax.set_title("IPV nacional: observado y pronóstico 2026–2027 con incertidumbre empírica")
    fig.tight_layout()
    fig.savefig(OUT / "b4_fan_nacional.png")
    plt.close(fig)

    print(q.round(3).to_string())
    nac = df[(df.ccaa == "Nacional") & (df.escenario == "central_salarios_2pct")]
    print("\nNacional, banda 80% en h=4 y h=8:")
    print(nac[nac.h.isin([4, 8])][["periodo_pred", "ipv_pred", "pi_80_low", "pi_80_high", "ratio_aseq_pred"]].to_string(index=False))
    print(f"\n{len(df)} filas → storage/gold/gold_forecast_ccaa.csv; figura b4_fan_nacional.png")


if __name__ == "__main__":
    main()
