"""Tests de la expansión del corpus (conectores nuevos + cuota teórica + A1-edu)."""
import pathlib

import pandas as pd
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "storage" / "processed"
GOLD = ROOT / "storage" / "gold"


def test_wdi_policy_cinco_series():
    d = pd.read_csv(PROCESSED / "wdi_policy.csv")
    assert set(d.variable.unique()) == {"spi_overall", "military_gdp", "edu_spend_gdp",
                                        "hlo_score", "oda_donor_gni"}
    es = d[d.iso3 == "ESP"].groupby("variable").value.last()
    assert 3 < es["edu_spend_gdp"] < 6
    assert 400 < es["hlo_score"] < 600
    assert 0 < es["military_gdp"] < 4


def test_valor_tasado_ancla():
    d = pd.read_csv(PROCESSED / "mitma_valor_tasado_ccaa.csv")
    assert d.ccaa.nunique() >= 18
    assert d.duplicated(subset=["ccaa", "anyo", "quarter"]).sum() == 0
    nac14 = d.query("ccaa=='Nacional' and anyo==2014").eur_m2.mean()
    assert 1200 < nac14 < 1800, f"€/m² nacional 2014 fuera de rango: {nac14}"


def test_cuota_teorica_contrato():
    d = pd.read_csv(GOLD / "gold_cuota_teorica.csv")
    for col in ["ccaa", "eur_m2_2024", "precio_vivienda", "cuota_mensual",
                "esfuerzo_pct", "ratio_aseq_2024", "supuestos"]:
        assert col in d.columns
    nac = d[d.ccaa == "Nacional"].iloc[0]
    assert 30 < nac.esfuerzo_pct < 60, "esfuerzo nacional fuera de rango plausible"
    assert d.esfuerzo_pct.max() == d.set_index("ccaa").esfuerzo_pct.get("Balears, Illes"), \
        "Baleares debe ser el territorio con mayor esfuerzo"
    sub = d[d.ccaa != "Nacional"]
    assert sub.esfuerzo_pct.corr(sub.ratio_aseq_2024, method="spearman") > 0.5


def test_rendimiento_edu_contrato():
    f = GOLD / "gold_rendimiento_edu.csv"
    if not f.exists():
        pytest.skip("módulo educación aún no ejecutado")
    d = pd.read_csv(f)
    for col in ["iso3", "hlo", "residual", "semiancho_90", "destacado", "modelo"]:
        assert col in d.columns
    assert len(d) > 80
    assert (d.semiancho_90 > 0).all()
    assert (d.destacado == (d.residual.abs() > d.semiancho_90)).all()
