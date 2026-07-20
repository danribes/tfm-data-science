"""Test de la predecibilidad de la PPA (convergencia verificada)."""
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOLD = ROOT / "storage" / "gold"


def test_ppp_predictibilidad():
    d = pd.read_csv(GOLD / "gold_ppp_predictibilidad.csv").set_index("prueba")
    # nivel muy persistente: naive competitivo con drift a través de shocks
    assert d.loc["nivel_ppa", "naive"] < 0.15
    # crecimiento apenas autocorrelado
    assert abs(d.loc["crecimiento_ar1", "drift"]) < 0.3
    # convergencia negativa (existe), magnitud pequeña (club, no global)
    beta = d.loc["convergencia_beta", "drift"]
    assert -0.01 < beta < 0, f"convergencia beta esperada pequeña y negativa: {beta}"
