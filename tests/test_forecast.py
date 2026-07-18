"""Tests del contrato de salida gold_forecast_ccaa.csv (Entrega 4 §5)."""
import pathlib

import pandas as pd
import pytest

GOLD = pathlib.Path(__file__).resolve().parents[1] / "storage" / "gold"


@pytest.fixture(scope="module")
def fc():
    return pd.read_csv(GOLD / "gold_forecast_ccaa.csv")


def test_dimensiones(fc):
    assert len(fc) == 18 * 8 * 3  # 18 series × h=1..8 × 3 escenarios
    assert fc["escenario"].nunique() == 3
    assert fc.duplicated(subset=["ccaa", "periodo_pred", "escenario"]).sum() == 0


def test_esquema_entrega4(fc):
    for col in ["ccaa", "periodo_origen", "periodo_pred", "ipv_pred", "pi_80_low",
                "pi_80_high", "pi_95_low", "pi_95_high", "escenario",
                "ratio_aseq_pred", "modelo", "fecha_ejecucion", "explicacion"]:
        assert col in fc.columns, f"falta {col}"
    assert (fc["modelo"] == "drift").all()
    assert fc["explicacion"].str.len().gt(20).all()


def test_bandas_ordenadas(fc):
    assert ((fc.pi_95_low <= fc.pi_80_low) & (fc.pi_80_low <= fc.pi_80_high)
            & (fc.pi_80_high <= fc.pi_95_high)).all()


def test_ipv_no_depende_del_escenario(fc):
    piv = fc.pivot_table(index=["ccaa", "periodo_pred"], columns="escenario",
                         values="ipv_pred")
    assert (piv.nunique(axis=1) == 1).all(), "el escenario solo mueve el denominador"


def test_ratio_ordenado_por_escenario(fc):
    piv = fc.pivot_table(index=["ccaa", "periodo_pred"], columns="escenario",
                         values="ratio_aseq_pred")
    ok = (piv["salarios_0pct"] >= piv["central_salarios_2pct"]) & \
         (piv["central_salarios_2pct"] >= piv["salarios_4pct"])
    assert ok.all(), "más crecimiento salarial debe implicar menor ratio"


def test_horizonte_fuera_de_muestra(fc):
    assert (fc["periodo_origen"] == "2025Q4").all()
    assert pd.PeriodIndex(fc["periodo_pred"], freq="Q").min() == pd.Period("2026Q1", freq="Q")
