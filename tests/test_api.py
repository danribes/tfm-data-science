"""API contract tests (spec §5/§7): every endpoint, response-shape snapshots
(the frozen phase-2 contract), range-validation 422s, CORS."""
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_root_redirects_to_docs():
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"] == "/docs"


def test_health_shape():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "vintage": "2026-07-31",
                        "engine_version": "1.0.0", "computed_not_advice": True}


def test_vintage_shape():
    r = client.get("/vintage")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"vintage", "computed_not_advice", "n_files", "files"}
    assert body["vintage"] == "2026-07-31"
    assert body["n_files"] == len(body["files"]) == 141
    assert set(body["files"][0]) == {"name", "url", "fetched_at", "bytes"}


def test_constants_shape():
    r = client.get("/constants")
    body = r.json()
    assert set(body) == {"vintage", "computed_not_advice", "constants"}
    names = {c["name"]: c for c in body["constants"]}
    assert names["MULT"]["value"] == 1.40
    assert names["DIFF"]["value"] == 1.4757
    assert all(c["provenance"] for c in body["constants"])
    assert set(body["constants"][0]) == {"name", "value", "unit", "provenance"}


def test_personas_shape():
    r = client.get("/personas")
    body = r.json()
    assert set(body) == {"vintage", "computed_not_advice", "kpis", "series", "personas"}
    assert len(body["kpis"]) == 42 and len(body["series"]) == 21
    assert [p["id"] for p in body["personas"]] == [f"{i:02d}" for i in range(1, 13)]
    p8 = next(p for p in body["personas"] if p["id"] == "08")
    assert p8["h1"] == "🧒 ¿Qué país hereda quien hoy tiene 8 años?"
    assert set(body["personas"][0]) == {"id", "pill", "foot", "h1", "meta", "hot",
                                        "series_keys", "outs", "headline", "reds"}
    for key in body["personas"][0]["series_keys"]:
        assert key in body["series"]


def test_presets_shape():
    r = client.get("/presets")
    body = r.json()
    assert set(body) == {"vintage", "computed_not_advice", "presets"}
    assert [p["id"] for p in body["presets"]] == [f"S{i}" for i in range(8)]
    s7 = body["presets"][7]
    assert s7["nm"] == "S7 adverso"
    assert s7["set"] == {"r": 4.8, "pm": 50.0, "prima": 150.0}


def test_redlines_shape():
    r = client.get("/redlines")
    body = r.json()
    assert set(body) == {"vintage", "computed_not_advice", "redlines"}
    assert len(body["redlines"]) == 9
    assert set(body["redlines"][0]) == {"id", "label", "series", "threshold", "cmp", "source"}


# ---- Task 12: scenario endpoints ----

def test_scenario_shape_and_zero_deviation():
    r = client.post("/scenario", json={})           # all defaults = base levers
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"vintage", "computed_not_advice", "horizon", "years",
                         "baseline", "scenario", "deltas", "personas", "redlines"}
    assert body["computed_not_advice"] is True
    assert body["horizon"] == 2050
    assert body["years"] == list(range(2026, 2051))
    assert len(body["baseline"]) == len(body["scenario"]) == len(body["deltas"]) == 40
    # deviation semantics: base levers -> scenario equals baseline, deltas all zero
    assert body["scenario"] == body["baseline"]
    assert all(v == 0.0 for series in body["deltas"].values() for v in series)
    assert sorted(body["personas"]) == [f"{i:02d}" for i in range(1, 13)]
    statuses = {rl["id"]: rl["status"] for rl in body["redlines"]}
    # base 2050: b=223.84 -> both debt lines crossed (computed, never hand-written)
    assert statuses["deuda_105"] == "crossed" and statuses["deuda_120"] == "crossed"


def test_scenario_s7_adverse_crosses_redlines():
    s7 = {"levers": {"r": 4.8, "pm": 50.0, "prima": 150.0}, "horizon": 2050}
    body = client.post("/scenario", json=s7).json()
    statuses = {rl["id"]: rl["status"] for rl in body["redlines"]}
    assert statuses["deuda_120"] == "crossed"           # b 2050 = 349.80
    assert statuses["deficit_suelo_2009"] == "crossed"  # saldo 2050 = -28.79
    assert statuses["bono_rescate"] == "near"           # bono 6.47 vs 7.0
    k = 2050 - 2026
    assert abs(body["scenario"]["b"][k] - 349.7973) < 1e-3


def test_scenario_lever_out_of_range_422():
    r = client.post("/scenario", json={"levers": {"r": 9.0}})
    assert r.status_code == 422
    detail = r.json()["detail"][0]
    assert detail["loc"][-1] == "r" and "less than or equal" in detail["msg"]
    assert client.post("/scenario", json={"levers": {"prima": -1}}).status_code == 422
    assert client.post("/scenario", json={"levers": {"idx": 1.2}}).status_code == 422


def test_montecarlo_endpoint_shape_and_bounds():
    r = client.post("/scenario/montecarlo", json={"seed": 42, "n_paths": 500})
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"vintage", "computed_not_advice", "years", "percentiles",
                         "n_paths", "seed", "paths"}
    assert body["years"][0] == 2026 and body["years"][-1] == 2070
    assert set(body["percentiles"]) == {"p5", "p25", "p50", "p75", "p95"}
    # reproducibility across calls with the same seed
    again = client.post("/scenario/montecarlo", json={"seed": 42, "n_paths": 500}).json()
    assert again["percentiles"] == body["percentiles"]
    # spec §6 bounds
    assert client.post("/scenario/montecarlo", json={"n_paths": 5000}).status_code == 422
    assert client.post("/scenario/montecarlo", json={"horizon": 2080}).status_code == 422


def test_montecarlo_horizon_truncates_years():
    body = client.post("/scenario/montecarlo", json={"n_paths": 300, "horizon": 2050}).json()
    assert body["years"][-1] == 2050
    assert all(len(v) == len(body["years"]) for v in body["percentiles"].values())


def test_sensitivity_matrix_endpoints():
    # GET /scenario/sensitivity
    r_get = client.get("/scenario/sensitivity")
    assert r_get.status_code == 200
    body_get = r_get.json()
    assert body_get["horizons"] == [2030, 2050]
    assert len(body_get["target_series"]) == 6
    assert "r" in body_get["matrix"]

    # POST /scenario/sensitivity with custom levers
    r_post = client.post("/scenario/sensitivity", json={"levers": {"r": 4.0, "sp": 1.0}})
    assert r_post.status_code == 200
    body_post = r_post.json()
    assert body_post["horizons"] == [2030, 2050]
    assert "matrix" in body_post



def test_cors_allows_null_and_localhost_origins():
    r = client.get("/health", headers={"Origin": "null"})
    assert r.headers.get("access-control-allow-origin") == "null"
    r = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


# ---- Task 13: generic-country layer (no network: monkeypatched) ----
import json as _json
import pytest
from pathlib import Path as _Path

from data.live.models import FetchResult

_FIXTURE = _Path(__file__).parent / "fixtures" / "sample_country_panel.json"
_BASELINE_KEYS = ["debt_gdp", "gdp_growth", "inflation", "unemployment",
                  "real_interest_rate", "net_lending_borrowing", "government_revenue_gdp"]


def _fixture_panel():
    raw = _json.loads(_FIXTURE.read_text())
    panel = {}
    for key in _BASELINE_KEYS:
        values = raw.get(key) or {}
        panel[key] = FetchResult(
            values={int(y): v for y, v in values.items()},
            source="worldbank", from_cache=True, fetched_at=0.0,
            error=None if values else "no data")
    return panel


def test_countries_endpoint(monkeypatch):
    import api.main as m
    monkeypatch.setattr(m.country_list, "load_country_list", lambda: [
        {"iso3": "ESP", "iso2": "ES", "name": "Spain", "region": "Europe & Central Asia"}])
    body = client.get("/countries").json()
    assert set(body) == {"vintage", "computed_not_advice", "countries", "error"}
    assert body["countries"] == [{"iso3": "ESP", "iso2": "ES", "name": "Spain",
                                  "region": "Europe & Central Asia"}]
    assert body["error"] is None


def test_countries_endpoint_degrades_honestly(monkeypatch):
    import api.main as m
    monkeypatch.setattr(m.country_list, "load_country_list", lambda: [])
    body = client.get("/countries").json()
    assert body["countries"] == [] and body["error"] is None    # empty list, no 500


def test_panel_endpoint(monkeypatch):
    import api.main as m
    monkeypatch.setattr(m.panel_builder, "build_country_panel",
                        lambda iso3, **kw: _fixture_panel())
    body = client.get("/panel/esp").json()
    assert set(body) == {"vintage", "computed_not_advice", "iso3", "coverage_score",
                         "indicators"}
    assert body["iso3"] == "ESP"
    assert 0.0 <= body["coverage_score"] <= 1.0
    ind = body["indicators"]["debt_gdp"]
    assert set(ind) == {"available", "source", "from_cache", "error", "values"}


def test_generic_scenario_endpoint(monkeypatch):
    import api.main as m
    monkeypatch.setattr(m.panel_builder, "build_country_panel",
                        lambda iso3, **kw: _fixture_panel())
    body = client.post("/scenario/generic/ESP", json={"horizon_years": 5}).json()
    assert set(body) == {"vintage", "computed_not_advice", "country_iso3",
                         "coverage_score", "defaults_used", "baseline_years",
                         "debt_path", "unemployment_path_pct", "inflation_path_pct",
                         "nominal_wage_growth_path_pct", "fiscal_space_by_year"}
    assert body["country_iso3"] == "ESP"
    assert len(body["debt_path"]) == 5
    assert set(body["debt_path"][0]) == {"year", "debt_gdp_pct", "interest_rate_pct",
                                         "growth_rate_pct", "primary_balance_pct",
                                         "contingent_shock_pct"}
    assert isinstance(body["defaults_used"], list)      # honesty fields present
    assert isinstance(body["baseline_years"], dict)


def test_generic_scenario_validates_horizon():
    assert client.post("/scenario/generic/ESP", json={"horizon_years": 0}).status_code == 422


def test_generic_scenario_invalid_allocation_shares_returns_422(monkeypatch):
    import api.main as m
    from engine import generic

    monkeypatch.setattr(m.panel_builder, "build_country_panel",
                        lambda iso3, **kw: _fixture_panel())
    r = client.post("/scenario/generic/ESP", json={"allocation_shares": {"health": 1.0}})
    assert r.status_code == 422
    try:
        generic.allocate_fiscal_space(0.0, 0.0, 0.0, {"health": 1.0})
        expected_detail = None
    except ValueError as exc:
        expected_detail = str(exc)
    assert expected_detail is not None
    assert r.json()["detail"] == expected_detail


# ---- /evidence: la calibración frente a los datos ----

def test_evidence_shape():
    r = client.get("/evidence")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"vintage", "computed_not_advice", "comparisons", "irf",
                         "fiscal_persistence", "identifiable", "engine_version"}
    assert body["comparisons"]
    row = body["comparisons"][0]
    assert set(row) == {"name", "coef", "se", "n", "n_units", "ci_low", "ci_high",
                        "significant", "constant", "label", "calibrated", "source",
                        "compatible", "verdict", "subperiods"}


def test_evidence_reports_a_calibration_outside_its_band_as_such():
    """The point of the endpoint: it must be able to say no. If every constant
    came back compatible, the page would be decoration."""
    body = client.get("/evidence").json()
    by_const = {c["constant"]: c for c in body["comparisons"]}
    ipv = by_const["IPV_LR"]
    assert ipv["compatible"] is False
    assert "fuera de la banda" in ipv["verdict"]
    assert not (ipv["ci_low"] <= ipv["calibrated"] <= ipv["ci_high"])


def test_evidence_ships_the_housing_windows_with_disjoint_signs():
    body = client.get("/evidence").json()
    by_const = {c["constant"]: c for c in body["comparisons"]}
    subs = by_const["IPV_LR"]["subperiods"]
    assert len(subs) == 2
    assert subs[0]["coef"] < 0 < subs[1]["coef"]
    assert by_const["IPV_REV"]["subperiods"] == []


def test_evidence_publishes_what_it_cannot_estimate():
    body = client.get("/evidence").json()
    blocked = {k for k, v in body["identifiable"].items() if v.startswith("no")}
    assert {"MULT", "OKUN"} <= blocked
    # Every blocker states a reason; "no" on its own would be an excuse.
    assert all(len(v) > len("no — ") for k, v in body["identifiable"].items()
               if k in blocked)


def test_evidence_ships_the_impulse_response_with_the_engine_on_the_same_axis():
    body = client.get("/evidence").json()
    irf = body["irf"]
    assert irf is not None
    assert len(irf["horizons"]) == len(irf["engine_path"])
    anchor = irf["anchor_h"]
    # Null before the anchor is the contract the chart relies on to leave a gap
    # rather than draw the engine's line down to zero.
    assert all(p["coef"] is None for p in irf["engine_path"] if p["h"] < anchor)
    assert all(p["coef"] is not None for p in irf["engine_path"] if p["h"] >= anchor)
    assert irf["unit"] and irf["note"]


def test_evidence_impulse_response_contradicts_the_calibrated_reversion():
    """The finding, asserted so a change of sign cannot pass silently: in the
    regional panel the shock keeps building while the engine assumes decay."""
    irf = client.get("/evidence").json()["irf"]
    at = {p["h"]: p for p in irf["horizons"]}
    anchor, last = at[irf["anchor_h"]], irf["horizons"][-1]
    assert last["coef"] > anchor["coef"]
    engine_last = irf["engine_path"][-1]["coef"]
    assert engine_last < anchor["coef"]
    assert last["ci_low"] > 0          # and it is distinguishable from nothing


# ---- sensitivity: comparable across levers, or not comparable at all -------

def test_sensitivity_reports_both_the_raw_derivative_and_a_comparable_effect():
    body = client.get("/scenario/sensitivity").json()
    row = body["matrix"]["r"]
    assert set(row) == {"lever_id", "lever_name", "unit", "sensitivities",
                        "lever_span", "span_effects"}
    assert row["lever_span"] > 0
    # span_effect is the derivative scaled by the lever's own range.
    for year in body["horizons"]:
        y = str(year)
        for k, v in row["sensitivities"][y].items():
            assert row["span_effects"][y][k] == pytest.approx(
                v * row["lever_span"], rel=1e-3, abs=1e-3)


def test_raw_derivatives_rank_differently_from_comparable_effects():
    """The reason the second column exists. On the raw derivative demographic
    pressure dwarfs the interest rate; moved end to end, the rate matters more.
    Ranking mixed units is the misreading, not a detail of presentation."""
    m = client.get("/scenario/sensitivity").json()["matrix"]
    raw_r, raw_dem = m["r"]["sensitivities"]["2050"]["b"], m["dem"]["sensitivities"]["2050"]["b"]
    eff_r, eff_dem = m["r"]["span_effects"]["2050"]["b"], m["dem"]["span_effects"]["2050"]["b"]
    assert abs(raw_dem) > abs(raw_r)        # what the raw column says
    assert abs(eff_r) > abs(eff_dem)        # what the comparable column says


def test_every_lever_has_a_span_so_no_row_is_silently_unrankable():
    m = client.get("/scenario/sensitivity").json()["matrix"]
    assert len(m) == 10
    for lid, row in m.items():
        assert row["lever_span"] > 0, lid
        assert row["span_effects"], lid


# ---- /prediction: el backtest T1 servido desde el artefacto ----

def test_prediction_serves_the_committed_evaluation():
    body = client.get("/prediction").json()
    assert body["available"] is True
    assert set(body["methods"]) == {"dl_global", "drift", "naive", "snaive"}
    assert [r["h"] for r in body["rows"]] == list(range(1, 9))
    assert body["protocol"]["test_start"] == "2024Q1"
    assert body["protocol"]["train_cutoff"] == "2019Q3"
    assert body["protocol"]["n_ccaa"] == 17


def test_prediction_reports_the_loss_rather_than_omitting_it():
    """The endpoint's contract includes being able to say the model lost. A
    shape that could only express a win would make the page decoration."""
    v = client.get("/prediction").json()["verdict"]
    assert v["wins"] is False
    assert v["beaten_ccaa"] < v["required"]
    assert v["mase_candidate"] > v["mase_drift"]
    assert "no bate" in v["verdict"]


def test_prediction_says_so_when_the_evaluation_has_not_been_run(monkeypatch):
    """A missing artifact must not render as a model with no error."""
    import api.main as m
    from pathlib import Path

    monkeypatch.setattr(m, "_T1_REPORT", Path("/nonexistent/t1.json"))
    body = client.get("/prediction").json()
    assert body["available"] is False
    assert body["rows"] == [] and body["verdict"] is None
    assert "research.dl_global" in body["note"]


# ---- /distress: el complemento probabilístico del 7 % ----

def test_distress_serves_the_committed_evaluation():
    body = client.get("/distress").json()
    assert body["available"] is True
    assert body["n_positive"] > 300
    assert 0.5 < body["auc"] < 1.0
    assert body["years"] == [1960, 2023]
    assert body["importances"][0]["label"]


def test_distress_scores_spain_as_out_of_sample():
    """Spain is not in the default database, and the endpoint must say so:
    that fact is what makes the probability an honest out-of-sample number."""
    esp = client.get("/distress").json()["spain"]
    assert esp is not None
    assert esp["iso3"] == "ESP"
    assert esp["in_label_set"] is False
    assert 0.0 < esp["probability"] < 0.5


def test_distress_says_so_when_the_model_has_not_been_trained(monkeypatch):
    import api.main as m
    from pathlib import Path

    monkeypatch.setattr(m, "_DISTRESS_REPORT", Path("/nonexistent/d.json"))
    body = client.get("/distress").json()
    assert body["available"] is False
    assert body["spain"] is None
    assert "research.distress" in body["note"]


# ---- /state-dependence: ¿E_R constante? ----

def test_state_dependence_serves_the_committed_contrast():
    body = client.get("/state-dependence").json()
    assert body["available"] is True
    assert len(body["regimes"]) == 3
    assert body["engine_e_r"] == 0.45
    assert len(body["diff_ci"]) == 2


def test_state_dependence_reports_the_null_and_the_zero_r2():
    """Both honesty markers must survive serialisation: the interval that
    includes zero, and the R² that says the model has no out-of-country skill."""
    body = client.get("/state-dependence").json()
    lo, hi = body["diff_ci"]
    assert lo < 0 < hi
    assert body["state_dependent"] is False
    assert body["r2_grouped"] < 0.1
    assert "WDI" in body["spain_excluded_reason"]


def test_state_dependence_says_so_when_not_run(monkeypatch):
    import api.main as m
    from pathlib import Path

    monkeypatch.setattr(m, "_STATE_DEP_REPORT", Path("/nonexistent/s.json"))
    body = client.get("/state-dependence").json()
    assert body["available"] is False
    assert "research.state_dependence" in body["note"]


# ---- /rag/eval: las notas de la biblioteca ----

def test_rag_eval_serves_both_evaluation_layers():
    body = client.get("/rag/eval").json()
    assert body["available"] is True
    assert body["n_questions"] >= 30
    assert body["hit_rate"] > 0.9
    assert body["unanswerable_refused"] == body["unanswerable_total"] == 4
    assert body["dangling_answers"] == 0
    assert body["isolation_clean"] is True and body["guardrail_clean"] is True


def test_rag_eval_says_so_when_artifacts_are_missing(monkeypatch):
    import api.main as m
    from pathlib import Path

    monkeypatch.setattr(m, "_RAG_CHAT_EVAL", Path("/nonexistent/x.json"))
    body = client.get("/rag/eval").json()
    assert body["available"] is False
    assert "rag.eval_chat" in body["note"]


# ---- /regimes: crisis detectadas por el HMM ----

def test_regimes_serves_both_series_with_aligned_arrays():
    body = client.get("/regimes").json()
    assert body["available"] is True
    for k in ("fiscal", "housing"):
        s = body[k]
        assert len(s["periods"]) == len(s["values"]) == len(s["p_crisis"])
        assert s["episodes"]
        # The wire format uses "from", which pydantic can only carry via alias.
        assert set(s["episodes"][0]) == {"from", "to"}


def test_regimes_finds_the_history_everyone_can_check():
    fiscal = client.get("/regimes").json()["fiscal"]
    spans = [(e["from"], e["to"]) for e in fiscal["episodes"]]
    assert any(a <= 1945 <= b for a, b in spans)     # posguerra civil
    assert any(a <= 2012 <= b for a, b in spans)     # la Gran Recesión
    housing = client.get("/regimes").json()["housing"]
    assert str(housing["episodes"][0]["from"]).startswith("2008")


def test_regimes_says_so_when_not_generated(monkeypatch):
    import api.main as m
    from pathlib import Path

    monkeypatch.setattr(m, "_REGIMES_REPORT", Path("/nonexistent/r.json"))
    body = client.get("/regimes").json()
    assert body["available"] is False
    assert "research.regimes" in body["note"]


# ---- /demography: variantes EUROPOP como valores de la palanca dem ----

def test_demography_maps_every_vintage_variant_to_a_dem_value():
    body = client.get("/demography").json()
    ids = {v["id"] for v in body["variants"]}
    assert ids == {"BSL", "HMIGR", "LMIGR", "NMIGR", "LFRT", "LMRT"}
    by_id = {v["id"]: v for v in body["variants"]}
    # The baseline maps to the lever's resting value by construction.
    assert by_id["BSL"]["dem_equivalent"] == 0.0
    # More ageing pressure → higher dem; the ordering is the sanity check.
    assert by_id["HMIGR"]["dem_equivalent"] < 0 < by_id["NMIGR"]["dem_equivalent"]
    assert by_id["NMIGR"]["dem_equivalent"] > by_id["LMIGR"]["dem_equivalent"]


def test_demography_equivalents_fit_inside_the_lever_bounds():
    """A chip that sets the lever outside its own slider would be rejected by
    validation and read as a bug. If a future vintage breaks this, the mapping
    needs a clamp and a caption, not silence."""
    body = client.get("/demography").json()
    for v in body["variants"]:
        assert -1.0 <= v["dem_equivalent"] <= 1.0, v["id"]


def test_demography_equivalent_reproduces_the_variant_growth():
    """The claim the tooltip makes: setting dem to the equivalent gives the
    engine the variant's dependency growth over the horizon, exactly at the
    endpoint."""
    from engine.constants import load_olddep_variants
    from engine.spain import Y0, Y1

    body = client.get("/demography").json()
    variants = load_olddep_variants()
    bsl = variants["BSL"]
    for v in body["variants"]:
        path = variants[v["id"]]
        target_growth = path[Y1] / path[Y0] - 1.0
        # The engine's rule: dep growth scales as (1 + dem) times BSL growth.
        engine_growth = (bsl[Y1] / bsl[Y0] - 1.0) * (1.0 + v["dem_equivalent"])
        assert engine_growth == pytest.approx(target_growth, abs=2e-3), v["id"]
