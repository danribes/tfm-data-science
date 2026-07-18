"""Tests del simulador D1 (gold_escenarios_deuda.csv)."""
import pathlib
import sys

import pandas as pd
import pytest

GOLD = pathlib.Path(__file__).resolve().parents[1] / "storage" / "gold"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "analysis"))


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(GOLD / "gold_escenarios_deuda.csv")


def test_escenarios_y_horizonte(df):
    assert df.escenario.nunique() == 6
    assert df.year.min() == 2024 and df.year.max() == 2050
    assert df.duplicated(subset=["escenario", "year"]).sum() == 0


def test_ordenacion_economica(df):
    fin = df[df.year == 2050].set_index("escenario")["deuda"]
    assert fin["sin_demografia"] < fin["central"], "la demografía debe empeorar la senda"
    assert fin["consolidacion"] < fin["central"], "consolidar debe mejorar la senda"
    assert fin["tipos_altos"] > fin["central"], "tipos más altos deben empeorarla"
    assert fin["crecimiento"] < fin["central"], "más crecimiento debe mejorarla"
    assert fin["inversion"] > fin["central"], "gasto extra a deuda debe aumentarla"


def test_presion_demografica_monotona(df):
    c = df[df.escenario == "central"].sort_values("year")
    assert (c.presion_demog.diff().dropna() >= -0.01).all(), "la presión 65+ no debe caer"
    assert 5 < c.presion_demog.iloc[-1] < 9, "presión 2050 esperada en torno a +6-7 pp"


def test_convergencia_tipo_efectivo(df):
    c = df[df.escenario == "central"].sort_values("year")
    assert abs(c.r_efectivo.iloc[-1] - 3.5) < 0.15, "el tipo efectivo debe converger al de mercado"


def test_arranque_comun(df):
    y0 = df[df.year == 2024]
    assert y0.deuda.std() < 1.5, "todos los escenarios deben arrancar prácticamente igual"
