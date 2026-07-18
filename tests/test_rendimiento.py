"""Tests del contrato gold_rendimiento_pais.csv (A1, Entrega 4 §5)."""
import pathlib

import pandas as pd
import pytest

GOLD = pathlib.Path(__file__).resolve().parents[1] / "storage" / "gold"


@pytest.fixture(scope="module")
def r():
    return pd.read_csv(GOLD / "gold_rendimiento_pais.csv")


def test_esquema(r):
    for col in ["iso3", "e0", "e0_esperado", "residual", "semiancho_90", "destacado",
                "grupo_renta", "gasto", "modelo", "fecha_ejecucion", "explicacion"]:
        assert col in r.columns, f"falta {col}"
    assert r.iso3.is_unique and len(r) > 140


def test_residual_consistente(r):
    assert ((r.e0 - r.e0_esperado - r.residual).abs() < 0.01).all()


def test_intervalos_positivos_y_destacado_coherente(r):
    assert (r.semiancho_90 > 0).all()
    assert (r.destacado == (r.residual.abs() > r.semiancho_90)).all()


def test_no_es_una_liga(r):
    # el contrato exige incertidumbre SIEMPRE: nada de ranking ordinal seco
    assert "semiancho_90" in r.columns and r.semiancho_90.notna().all()
    assert r.grupo_renta.nunique() == 4


def test_espana_presente(r):
    es = r[r.iso3 == "ESP"]
    assert len(es) == 1
    assert 75 < es.e0.iloc[0] < 90
