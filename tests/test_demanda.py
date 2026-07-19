"""Tests de las capas de demanda/crédito/suelo (Tier 1-2, 2026-07-19)."""
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "storage" / "processed"
GOLD = ROOT / "storage" / "gold"

TERRITORIOS = {
    "Nacional", "Andalucía", "Aragón", "Asturias, Principado de", "Balears, Illes",
    "Canarias", "Cantabria", "Castilla - La Mancha", "Castilla y León", "Cataluña",
    "Comunitat Valenciana", "Extremadura", "Galicia", "Madrid, Comunidad de",
    "Murcia, Región de", "Navarra, Comunidad Foral de", "País Vasco", "Rioja, La",
    "Ceuta", "Melilla",
}


def test_compraventas_panel():
    d = pd.read_csv(PROCESSED / "ine_compraventas_ccaa.csv")
    assert set(d.ccaa) == TERRITORIOS
    assert d.duplicated(subset=["ccaa", "anyo", "mes"]).sum() == 0
    nac = d[(d.ccaa == "Nacional") & (d.anyo == 2024)].valor.sum()
    assert 550_000 < nac < 750_000, f"compraventas nacionales 2024 fuera de rango: {nac}"


def test_hipotecas_panel():
    d = pd.read_csv(PROCESSED / "ine_hipotecas_ccaa.csv")
    assert set(d.ccaa) == TERRITORIOS
    nac = d[(d.ccaa == "Nacional") & (d.anyo == 2024)].valor.sum()
    assert 350_000 < nac < 550_000, f"hipotecas nacionales 2024 fuera de rango: {nac}"


def test_poblacion_trimestral():
    d = pd.read_csv(PROCESSED / "ine_poblacion_q_ccaa.csv")
    assert set(d.ccaa) == TERRITORIOS
    assert d.anyo.min() <= 1972 and d.anyo.max() >= 2026
    nac = d[(d.ccaa == "Nacional") & (d.anyo == 2025)].valor
    assert (nac > 49_000_000).all()
    suma = d[(d.ccaa != "Nacional") & (d.anyo == 2025) & (d.quarter == 1)].valor.sum()
    nac1 = d[(d.ccaa == "Nacional") & (d.anyo == 2025) & (d.quarter == 1)].valor.iloc[0]
    assert abs(suma / nac1 - 1) < 0.01, "las CCAA no suman la población nacional"


def test_suelo_mercado():
    d = pd.read_csv(PROCESSED / "mitma_suelo_ccaa.csv")
    assert set(d.variable) == {"transacciones_n", "valor_miles_eur", "superficie_miles_m2", "precio_eur_m2"}
    assert d.duplicated(subset=["ccaa", "anyo", "quarter", "variable"]).sum() == 0
    sup = d.query("variable=='superficie_miles_m2' and ccaa=='Nacional'").groupby("anyo").valor.sum()
    assert sup.loc[2006] > 3 * sup.loc[2012], "el colapso 2008-13 del mercado de suelo debe ser visible"


def test_siu_stock():
    d = pd.read_csv(PROCESSED / "siu_clases_suelo_ccaa.csv")
    assert d.vintage.nunique() == 2 and d.ccaa_siu.nunique() >= 19
    assert d.pct_urbanizable_delimitado.between(0, 100).all()
    g = pd.read_csv(GOLD / "gold_suelo_ccaa.csv")
    assert g.ccaa.nunique() >= 19
    assert g.set_index("ccaa").pct_urbanizable_2025.idxmax() == "Murcia, Región de"


def test_bls_criterios():
    d = pd.read_csv(PROCESSED / "bls_criterios_vivienda.csv")
    assert d.anyo.min() <= 2003 and len(d) > 85
    assert d.pct_neto_endurecimiento.between(-100, 100).all()
    y2008 = d[d.anyo == 2008].pct_neto_endurecimiento.mean()
    assert y2008 > 20, "2008 debe mostrar endurecimiento fuerte del crédito"


def test_gtrends_vintage():
    d = pd.read_csv(PROCESSED / "gtrends_vivienda.csv")
    assert d.keyword.nunique() == 3
    assert "fecha_descarga" in d.columns, "la añada congelada debe viajar en el CSV"
    assert d.groupby("keyword").size().min() > 1000, "resolución mensual encadenada esperada"
