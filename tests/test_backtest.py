"""Tests del harness de backtesting T1 (analysis/backtest_t1.py).

Verifican las propiedades que el diseño pre-registrado promete: baselines
correctos, sin fuga temporal y test final intocable.
"""
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "analysis"))
from backtest_t1 import TEST_START, backtest, drift, mase_scale, naive, snaive


def _serie(vals, start="2015Q1"):
    idx = pd.period_range(start, periods=len(vals), freq="Q")
    return pd.Series(vals, index=idx, dtype=float)


def test_snaive_devuelve_mismo_trimestre_anyo_anterior():
    s = _serie(range(100, 112))  # 12 trimestres: último año = 108..111
    assert snaive(s, 4) == [108.0, 109.0, 110.0, 111.0]


def test_snaive_recursivo_mas_alla_de_4():
    s = _serie(range(100, 112))
    preds = snaive(s, 8)
    assert preds[4:] == preds[:4], "h=5..8 debe reutilizar los pronósticos h=1..4"


def test_drift_exacto_en_serie_lineal():
    s = _serie(np.arange(50, 90, 2))  # pendiente 2 por trimestre
    assert np.allclose(drift(s, 4), [s.iloc[-1] + 2 * j for j in range(1, 5)])


def test_naive_repite_ultimo_valor():
    s = _serie([1, 2, 3, 7])
    assert naive(s, 3) == [7.0, 7.0, 7.0]


def test_mase_scale_es_diferencia_estacional_media():
    s = _serie(range(100, 112))
    assert mase_scale(s) == 4.0  # serie +1/trimestre → diff(4) constante = 4


def test_backtest_sin_fuga_y_test_intocable():
    vistos = []

    def espia(train, h):
        vistos.append(train.index.max())
        return naive(train, h)

    s = _serie(range(100, 180), start="2006Q1")  # llega hasta 2025Q4
    df = backtest({"Toy": s}, {"espia": espia})
    origen_max = pd.Period("2023Q4", freq="Q")
    assert max(vistos) <= origen_max, "el forecaster vio datos posteriores al origen"
    evaluados = pd.PeriodIndex([pd.Period(o, freq="Q") + h for o, h in zip(df.origen, df.h)])
    assert (evaluados < TEST_START).all(), "se evaluó dentro del test final reservado"


def test_resultados_publicados_no_tocan_test():
    out = pathlib.Path(__file__).resolve().parents[1] / "docs" / "figures" / "backtest"
    if not (out / "backtest_errores.csv").exists():
        return  # aún no ejecutado en este entorno
    df = pd.read_csv(out / "backtest_errores.csv")
    evaluados = pd.PeriodIndex([pd.Period(o, freq="Q") + h for o, h in zip(df.origen, df.h)])
    assert (evaluados < TEST_START).all()
