"""Tests del empalme histórico fiscal y su control de denominador."""
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOLD = ROOT / "storage" / "gold"
PROCESSED = ROOT / "storage" / "processed"


def test_denominador_jst_reproducible():
    j = pd.read_csv(PROCESSED / "jst_fiscal.csv").dropna(
        subset=["gdp", "expenditure", "exp_gdp"])
    recalc = j.expenditure / j.gdp * 100
    assert (recalc - j.exp_gdp).abs().max() < 0.01, "el ratio debe salir de los niveles"


def test_empalme_canonico():
    d = pd.read_csv(GOLD / "gold_fiscal_historico.csv")
    es = d[d.iso3 == "ESP"].set_index("year").sort_index()
    assert es.index.min() <= 1750 and es.index.max() >= 2023
    assert set(es.fuente) == {"gmd", "eurostat"}, "solo fuentes de perímetro AAPP continuo"
    # sin acantilado artificial en el empalme 1994→1995
    salto = abs(es.loc[1995].exp_gdp - es.loc[1994].exp_gdp)
    assert salto < 5, f"salto de empalme sospechoso: {salto:.1f} pp"
    # historia básica correcta
    assert es.loc[1900].exp_gdp < 15 and es.loc[2023].exp_gdp > 40
    assert es.loc[2012].exp_gdp - es.loc[2012].rev_gdp > 8, "déficit 2012 debe ser grande"


def test_panel_18_paises():
    d = pd.read_csv(GOLD / "gold_fiscal_historico.csv")
    assert d.iso3.nunique() >= 18
    # Irlanda arranca en 1926: el estado no existía antes de 1922
    assert (d.groupby("iso3").year.min().drop("IRL") <= 1900).all()
