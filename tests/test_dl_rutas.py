"""Tests de las rutas DL (panel global regional + contests fundacional/global)."""
import pathlib

import pandas as pd
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "storage" / "processed"
OUT = ROOT / "docs" / "figures" / "backtest"


def test_panel_regional_global():
    d = pd.read_csv(PROCESSED / "hpi_regional_global.csv")
    assert d.serie.nunique() > 1500
    assert set(d.fuente) == {"fhfa_metro", "fhfa_state", "zillow", "uk"}
    assert d.anyo.min() <= 1970 and d.anyo.max() >= 2025
    assert d.duplicated(subset=["serie", "anyo", "quarter"]).sum() == 0
    assert (d.valor > 0).all()
    # sin series españolas: el corpus de entrenamiento es exclusivamente extranjero
    assert not d.serie.str.startswith(("ES", "SP")).any()


@pytest.mark.parametrize("archivo,metodo", [("foundation_errores.csv", "chronos"),
                                            ("dl_global_errores.csv", "dl_global")])
def test_contests_ejecutados(archivo, metodo):
    f = OUT / archivo
    if not f.exists():
        pytest.skip(f"{archivo} aún no generado")
    d = pd.read_csv(f)
    assert set(d.metodo) == {metodo}
    assert d.h.max() == 8 and d.ccaa.nunique() >= 17
    # el test final 2024+ sigue intocable: ninguna diana (origen+h) cae ahí
    diana = pd.PeriodIndex(d.origen, freq="Q") + d.h.values
    assert (diana < pd.Period("2024Q1", freq="Q")).all()
