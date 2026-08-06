"""Data-layer tests: gold-slice shape checks (Task 1), ported MVP client tests
(Task 2, appended below), refresh_vintage (Task 14, appended below)."""
import csv
import json
from pathlib import Path


GOLD = Path(__file__).resolve().parents[1] / "data" / "gold"

GOLD_FILES = [
    "gold_escenarios_deuda.csv", "gold_escenarios_deuda_mc.csv",
    "gold_cuota_teorica.csv", "gold_projections.csv", "gold_ccaa_trimestral.csv",
    "gold_asequibilidad_ccaa.csv", "gold_pobreza_infantil.csv",
    "gold_bienestar_pais.csv", "gold_fiscal_historico.csv",
    "kpis_perfiles.json", "manifest.csv", "provenance_vintage_manifest.csv",
    "VINTAGE",
]


def test_gold_slice_files_committed():
    for name in GOLD_FILES:
        assert (GOLD / name).exists(), f"missing {name}"
    # excluded from phase 1 (spec §3.1): no consumer yet
    assert not (GOLD / "gold_century_fiscal.csv").exists()
    assert not (GOLD / "gold_panel_anual.csv").exists()


def test_vintage_stamp():
    assert (GOLD / "VINTAGE").read_text(encoding="utf-8").strip() == "2026-07-31"


def test_kpis_shape():
    kp = json.loads((GOLD / "kpis_perfiles.json").read_text(encoding="utf-8"))
    assert set(kp) == {"vintage", "fuentes", "kpi", "series"}
    assert kp["vintage"] == "2026-07-31"
    assert len(kp["kpi"]) == 42
    assert len(kp["series"]) == 21
    assert kp["kpi"]["euribor12m"]["valor"] == 2.8
    assert kp["kpi"]["cuota_hipoteca_mediana"]["valor"] == 745


def test_central_scenario_rows():
    rows = [r for r in csv.DictReader((GOLD / "gold_escenarios_deuda.csv").open(encoding="utf-8"))
            if r["escenario"] == "central"]
    years = sorted(int(float(r["year"])) for r in rows)
    assert years[0] == 2024 and years[-1] == 2050 and len(years) == 27
    row_2026 = next(r for r in rows if int(float(r["year"])) == 2026)
    # extract L868: central,2026,106.32,-1.35,2.68,3.3,0.45
    assert row_2026["deuda"] == "106.32"


def test_mc_and_cuota_rows():
    mc = [r for r in csv.DictReader((GOLD / "gold_escenarios_deuda_mc.csv").open(encoding="utf-8"))
          if r["escenario"] == "central"]
    mc_years = {int(float(r["year"])) for r in mc}
    assert {2030, 2050, 2070} <= mc_years
    cuota = list(csv.DictReader((GOLD / "gold_cuota_teorica.csv").open(encoding="utf-8")))
    assert len(cuota) == 17
    navarra = next(r for r in cuota if r["ccaa"].startswith("Navarra"))
    assert navarra["cuota_mensual"] == "744.89"     # extract L932
