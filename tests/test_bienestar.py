"""Tests del marco de bienestar/pobreza infantil y su frontera."""
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "storage" / "processed"
GOLD = ROOT / "storage" / "gold"


def test_series_marco():
    d = pd.read_csv(PROCESSED / "wdi_bienestar.csv")
    assert d.variable.nunique() == 13
    es = d[d.iso3 == "ESP"].sort_values("year").groupby("variable").value.last()
    assert es["mortalidad_u5"] < 5, "mortalidad <5 ESP debe ser baja"
    assert es["agua_segura"] > 95 and es["electricidad"] > 99


def test_arope_ninos():
    d = pd.read_csv(PROCESSED / "arope_ninos.csv")
    es = d[d.geo == "ES"].sort_values("time")
    assert 25 < es.value.iloc[-1] < 40, "AROPE infantil ESP ~30-35% (de los peores de la UE)"


def test_frontera_bienestar():
    g = pd.read_csv(GOLD / "gold_bienestar_pais.csv")
    assert set(g.outcome) == {"mortalidad_u5_log", "stunting"}
    assert (g.modelo == "OLS").all() if "modelo" in g.columns else True
    u5 = g[g.outcome == "mortalidad_u5_log"].set_index("iso3")
    assert len(u5) > 150
    assert (u5.destacado == (u5.residual.abs() > u5.semiancho_90)).all()
    assert not u5.loc["ESP", "destacado"], "ESP dentro de banda"
    assert u5.residual.idxmax() == "GNQ", "Guinea Ecuatorial = peor conversor renta→supervivencia"
