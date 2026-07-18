"""Tests de la capa gold (contrato de datos de la Entrega 3 + anexo).

Se ejecutan sobre los CSV ya construidos en storage/gold — sin red, sin
reconstruir: verifican el ARTEFACTO entregado, no el proceso.
    pytest tests/ -q
"""
import pathlib

import pandas as pd
import pytest

GOLD = pathlib.Path(__file__).resolve().parents[1] / "storage" / "gold"

TERRITORIOS = {"Nacional", "Andalucía", "Aragón", "Asturias, Principado de",
               "Balears, Illes", "Canarias", "Cantabria", "Castilla y León",
               "Castilla - La Mancha", "Cataluña", "Comunitat Valenciana",
               "Extremadura", "Galicia", "Madrid, Comunidad de",
               "Murcia, Región de", "Navarra, Comunidad Foral de",
               "País Vasco", "Rioja, La"}


@pytest.fixture(scope="module")
def ccaa_q():
    return pd.read_csv(GOLD / "gold_ccaa_trimestral.csv")


@pytest.fixture(scope="module")
def anual():
    return pd.read_csv(GOLD / "gold_asequibilidad_ccaa.csv")


def test_ficheros_gold_presentes():
    esperados = ["gold_panel_anual.csv", "gold_panel_wide.csv",
                 "gold_ccaa_trimestral.csv", "gold_asequibilidad_ccaa.csv",
                 "gold_century_fiscal.csv", "gold_projections.csv"]
    faltan = [f for f in esperados if not (GOLD / f).exists()]
    assert not faltan, f"faltan en storage/gold: {faltan}"


def test_pk_unica_trimestral(ccaa_q):
    assert ccaa_q.duplicated(subset=["ccaa", "anyo", "quarter"]).sum() == 0


def test_pk_unica_anual(anual):
    assert anual.duplicated(subset=["ccaa", "anyo"]).sum() == 0


def test_territorios_completos(ccaa_q):
    faltan = TERRITORIOS - set(ccaa_q["ccaa"].unique())
    assert not faltan, f"territorios ausentes: {faltan}"


def test_sin_nombres_truncados(ccaa_q):
    # regresión del bug de regex en el split del IPV: producía "Balears",
    # "Madrid" etc. como territorios truncados junto a columnas basura
    truncados = {"Balears", "Madrid", "Murcia", "Navarra", "Asturias", "Rioja"}
    assert not truncados & set(ccaa_q["ccaa"].unique())
    assert "Unnamed: 3" not in ccaa_q.columns and "Viviend" not in ccaa_q.columns


def test_cobertura_ratio_2024(ccaa_q):
    en_ambito = ccaa_q[ccaa_q["ccaa"].isin(TERRITORIOS)].query("anyo==2024")
    assert en_ambito["ratio_asequibilidad"].notna().all()


def test_ancla_ratio_nacional_2024(ccaa_q):
    r = ccaa_q.query("ccaa=='Nacional' and anyo==2024")["ratio_asequibilidad"].mean()
    assert 1.0 < r < 2.0


def test_rangos_indices(ccaa_q):
    v = ccaa_q["ipv_idx15"].dropna()
    assert v.between(40, 250).all(), "IPV re-basado 2015=100 fuera de rango plausible"
    s = ccaa_q["salario_anual"].dropna()
    assert s.between(12_000, 45_000).all(), "salario anual fuera de rango plausible"


def test_salario_flag_valores(ccaa_q):
    assert set(ccaa_q["salario_flag"].unique()) <= {"observado", "provisional_ffill", "faltante"}


def test_anual_solo_salario_observado(anual):
    assert anual["anyo"].max() <= 2024, "el gold anual no debe rebasar el tope EES"
    assert anual["ratio_asequibilidad"].notna().all()
    assert anual["ratio_real"].notna().all()


def test_anual_consistente_con_trimestral(ccaa_q, anual):
    ra = anual.query("ccaa=='Nacional' and anyo==2024")["ratio_asequibilidad"].iloc[0]
    rq = ccaa_q.query("ccaa=='Nacional' and anyo==2024")["ratio_asequibilidad"].mean()
    assert abs(ra - rq) < 0.05


def test_century_eras():
    c = pd.read_csv(GOLD / "gold_century_fiscal.csv")
    assert c["iso3"].nunique() > 150, "el histórico debe cubrir >150 países"
