"""Tests del panel internacional de vivienda y suelo (BIS/OCDE/LUCAS)."""
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "storage" / "processed"
GOLD = ROOT / "storage" / "gold"


def test_bis_precios():
    d = pd.read_csv(PROCESSED / "bis_precios_vivienda.csv")
    assert d.area.nunique() >= 55
    assert set(d.serie) == {"nominal", "real"}
    es = d.query("area=='ES' and serie=='real'")
    assert es.anyo.min() <= 1971
    # burbuja y caída visibles en términos reales
    assert es.query("anyo==2007").indice.mean() > 1.5 * es.query("anyo==1998").indice.mean()
    assert es.query("anyo==2013").indice.mean() < 0.72 * es.query("anyo==2007").indice.mean()


def test_oecd_precio_renta():
    d = pd.read_csv(PROCESSED / "oecd_precios_vivienda.csv")
    assert d.iso3.nunique() >= 45
    pti = d.query("iso3=='ESP' and medida=='HPI_YDH'").sort_values(["anyo", "quarter"])
    assert 110 < pti.valor.iloc[-1] < 160, "precio/renta ESP fuera de rango plausible"


def test_oecd_suelo_artificial():
    d = pd.read_csv(PROCESSED / "oecd_suelo_artificial.csv")
    esp = d.query("iso3=='ESP' and medida=='LC_SUR_ART'").sort_values("anyo")
    assert esp.anyo.min() == 2000 and esp.anyo.max() >= 2020
    assert esp.valor.iloc[-1] > 1.5 * esp.valor.iloc[0], "ESP debe mostrar crecimiento fuerte del suelo artificial"


def test_gold_panel_global():
    g = pd.read_csv(GOLD / "gold_vivienda_global.csv")
    t = g.set_index("iso3")
    assert t.loc["ESP", "precio_renta_2015_100"] > 120
    assert t.loc["ITA", "real_desde_2015_pct"] < 5, "Italia real plano/negativo es el contraste esperado"
    assert t.loc["PRT", "precio_renta_2015_100"] > t.loc["ESP", "precio_renta_2015_100"]
