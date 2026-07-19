"""Tests de la API MVP (api/main.py) servida desde la capa gold."""
import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.environ["GOLD_DIR"] = str(ROOT / "storage" / "gold")
sys.path.insert(0, str(ROOT / "api"))

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_forecast_contrato(client):
    r = client.get("/forecast/ccaa/Nacional?h=8")
    assert r.status_code == 200
    js = r.json()
    assert js["modelo"] == "drift" and len(js["puntos"]) == 8
    p = js["puntos"][0]
    for k in ["ipv_pred", "pi_80_low", "pi_80_high", "pi_95_low", "pi_95_high", "ratio_aseq_pred"]:
        assert k in p
    assert "banda" in js["advertencia"]


def test_forecast_404(client):
    assert client.get("/forecast/ccaa/Atlantis").status_code == 404


def test_performance_no_es_liga(client):
    r = client.get("/performance/health")
    assert r.status_code == 200
    js = r.json()
    assert "no es un ranking" in js["nota"]
    assert len(js["paises"]) > 140
    assert all("semiancho_90" in p for p in js["paises"][:5])


def test_scenarios_debt_menu(client):
    r = client.get("/scenarios/debt")
    assert r.status_code == 200
    assert len(r.json()["escenarios"]) == 6


def test_scenario_interactivo_coherente(client):
    base = client.post("/scenario", json={}).json()["senda"][-1]["deuda"]
    mejor = client.post("/scenario", json={"pb_palanca_pp": 2.0}).json()["senda"][-1]["deuda"]
    peor = client.post("/scenario", json={"r_mercado": 5.0}).json()["senda"][-1]["deuda"]
    sin_demo = client.post("/scenario", json={"con_demografia": False}).json()["senda"][-1]["deuda"]
    assert mejor < base < peor
    assert sin_demo < base, "la demografía debe empeorar la senda"


def test_project_sigue_vivo(client):
    r = client.get("/project/pensions?geo=ES&variant=BSL&to_year=2050")
    assert r.status_code == 200
