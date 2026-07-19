"""Tests del desglose fiscal global y su reconciliación."""
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "storage" / "processed"
GOLD = ROOT / "storage" / "gold"


def test_gfs_cofog_global():
    d = pd.read_csv(PROCESSED / "gfs_cofog_global.csv")
    assert d.iso3.nunique() >= 80 and d.funcion.nunique() == 10
    es24 = d.query("iso3=='ESP' and year==2024").set_index("funcion").pct_gdp
    assert 5 < es24["GF07"] < 8, "sanidad ESP fuera de rango"
    assert 15 < es24["GF10"] < 22, "protección social ESP fuera de rango"


def test_world_revenue():
    d = pd.read_csv(PROCESSED / "world_revenue_global.csv")
    assert d.iso3.nunique() >= 150
    es = d.query("iso3=='ESP' and year==2023").set_index("categoria").pct_gdp
    assert 38 < es["rev_total"] < 45
    assert es["tax_total"] + es["cotizaciones_ss"] < es["rev_total"]
    assert es["tax_renta_personas"] > es["tax_renta_sociedades"], "IRPF > IS en España"


def test_oecd_tax_global():
    d = pd.read_csv(PROCESSED / "oecd_tax_global.csv")
    assert d.iso3.nunique() >= 130
    es22 = d.query("iso3=='ESP' and year==2022").pct_gdp.sum()
    assert 34 < es22 < 40


def test_reconciliacion():
    r = pd.read_csv(GOLD / "gold_fiscal_reconciliation.csv")
    assert len(r) >= 14
    assert (r.veredicto == "OK").all(), f"checks fallidos: {r[r.veredicto != 'OK'].check.tolist()}"
    cofog = r[r.check.str.startswith("cofog_")]
    assert (cofog.brecha_abs_media_pp < 0.35).all(), "Eurostat e IMF deben coincidir por función"


def test_gold_breakdown():
    g = pd.read_csv(GOLD / "gold_fiscal_breakdown.csv")
    assert g.iso3.nunique() >= 190
    assert set(g.lado) == {"gasto", "ingreso"}
    assert set(g.fuente) == {"imf_gfs", "eurostat", "imf_world", "oecd_rs"}
