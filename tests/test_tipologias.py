"""Tests del contrato gold_tipologias_gasto.csv (A2)."""
import pathlib

import pandas as pd
import pytest

GOLD = pathlib.Path(__file__).resolve().parents[1] / "storage" / "gold"


@pytest.fixture(scope="module")
def t():
    return pd.read_csv(GOLD / "gold_tipologias_gasto.csv")


def test_esquema(t):
    gf = [f"te_gf{i:02d}" for i in range(1, 11)]
    for col in ["geo", "pc1", "pc2", "cluster", "silhouette_k"] + gf:
        assert col in t.columns, f"falta {col}"
    assert t.geo.is_unique and len(t) >= 28


def test_sin_agregados(t):
    assert not t.geo.str.startswith(("EU", "EA")).any()


def test_shares_suman_aprox_100(t):
    gf = [f"te_gf{i:02d}" for i in range(1, 11)]
    suma = t[gf].sum(axis=1)
    assert suma.between(93, 103).all(), "los shares COFOG deben sumar ~100% del gasto"


def test_clusters_validos(t):
    assert t.cluster.nunique() >= 2
    assert set(t.cluster.unique()) == set(range(t.cluster.nunique()))


def test_espana(t):
    es = t[t.geo == "ES"]
    assert len(es) == 1
    assert es.te_gf10.iloc[0] > 35, "protección social debe ser la mayor partida española"
