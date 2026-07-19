"""Tests del contrato mitma_licencias_ccaa.csv (pata regional del driver de oferta)."""
import pathlib

import pandas as pd
import pytest

PROCESSED = pathlib.Path(__file__).resolve().parents[1] / "storage" / "processed"


@pytest.fixture(scope="module")
def m():
    return pd.read_csv(PROCESSED / "mitma_licencias_ccaa.csv")


def test_esquema(m):
    for c in ["ccaa", "anyo", "viv_nueva", "viv_rehab", "viv_demolicion", "viv_total"]:
        assert c in m.columns
    assert m.duplicated(subset=["ccaa", "anyo"]).sum() == 0
    assert m.ccaa.nunique() == 19


def test_nombres_ine(m):
    gold = pd.read_csv(PROCESSED.parent / "gold" / "gold_ccaa_trimestral.csv")
    fuera = set(m.ccaa.unique()) - set(gold.ccaa.unique())
    assert not fuera, f"nombres no armonizados con el panel INE: {fuera}"


def test_colapso_burbuja(m):
    nac = m.groupby("anyo").viv_nueva.sum()
    assert nac.loc[2006] > 15 * nac.loc[2013], "el colapso 2006→2013 debe ser >x15"


def test_cobertura(m):
    grandes = m[~m.ccaa.isin(["Ceuta", "Melilla"])]
    assert (grandes.groupby("ccaa").anyo.max() >= 2022).all()
    assert (m.groupby("ccaa").anyo.min() <= 2000).all()
