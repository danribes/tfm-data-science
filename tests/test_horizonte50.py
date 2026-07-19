"""Tests del sistema a 50 años (panel, MC deuda, sobres bienestar, calibración)."""
import json
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOLD = ROOT / "storage" / "gold"


def test_panel_params():
    p = json.load(open(ROOT / "api" / "models" / "bienestar_panel_params.json"))
    assert p["n_paises"] > 150 and p["n_obs"] > 3000
    # el within debe ser mucho menor que el between (el hallazgo central)
    assert abs(p["beta_rev_within"]) < abs(p["beta_rev_between"]) / 3
    g8 = p["gradiente_retardos"]["8"]
    assert g8["beta"] < 0 and abs(g8["beta"]) > 1.5 * g8["se"], "efecto a lag 8 significativo"
    assert p["beta_loggdp_within"] < -0.3, "la renta debe dominar"


def test_mc_deuda():
    d = pd.read_csv(GOLD / "gold_escenarios_deuda_mc.csv")
    assert d.year.max() == 2070 and d.escenario.nunique() >= 4
    c50 = d.query("escenario=='central' and year==2050").iloc[0]
    assert 200 < c50.p50 < 260, "mediana MC debe ser coherente con el D1 discreto (224)"
    assert c50.p5 < 198 and c50.p95 > 267, "banda MC más ancha que la discreta"
    assert (d.p5 <= d.p50).all() and (d.p50 <= d.p95).all()


def test_sobres_bienestar():
    d = pd.read_csv(GOLD / "gold_bienestar_50.csv")
    assert set(d.year) == {2050, 2070}
    assert (d.delta_mortalidad_pct < 0).all(), "todos los sobres mejoran vs base (crecimiento>0)"
    c = d.query("year==2050 and ingresos=='constante'").set_index("crecimiento").delta_mortalidad_pct
    assert c["dinamico"] < c["central"] < c["estancamiento"], "más crecimiento, más mejora"
    assert (d.ic95_lo_pct <= d.delta_mortalidad_pct).all()


def test_calibracion_50y():
    d = pd.read_csv(GOLD / "gold_backtest_50y.csv")
    assert d.ventana.nunique() == 2 and d.iso3.nunique() >= 15
    med = d.query("ventana=='1975->2025'").err_congelar.abs().median()
    assert med > 8, "la continuidad a 50 años debe fallar por >8 pp (si no, algo está mal)"
    es = d.query("iso3=='ESP' and ventana=='1975->2025' and lado=='exp_gdp'").iloc[0]
    assert es.err_congelar > 15, "ESP: la transición fiscal es invisible para la continuidad"
