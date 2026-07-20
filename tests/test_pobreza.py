"""Test del módulo de predecibilidad de pobreza infantil."""
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOLD = ROOT / "storage" / "gold"


def test_pobreza_infantil():
    d = pd.read_csv(GOLD / "gold_pobreza_infantil.csv")
    assert {"palanca", "d_pobreza_infantil_pp", "nivel_proyectado"} <= set(d.columns)
    # el hallazgo: el ciclo NO predice (relativa); la redistribución sí
    assert not bool(d.ciclo_predice.iloc[0]), "el ciclo no debe predecir la pobreza relativa"
    assert d.efecto_transferencias_infantil_pp.iloc[0] > 5, "las transferencias quitan >5pp infantil"
    # monotonía: menos transferencias -> más pobreza
    sin = d[d.palanca == "sin transferencias"].d_pobreza_infantil_pp.iloc[0]
    mas = d[d.palanca == "transferencias +25 %"].d_pobreza_infantil_pp.iloc[0]
    assert sin > 0 > mas
