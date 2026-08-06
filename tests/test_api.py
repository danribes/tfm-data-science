"""API contract tests (spec §5/§7): every endpoint, response-shape snapshots
(the frozen phase-2 contract), range-validation 422s, CORS."""
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


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
    assert detail["loc"][-1] == "r"
    assert client.post("/scenario", json={"levers": {"prima": -1}}).status_code == 422
    assert client.post("/scenario", json={"levers": {"idx": 1.2}}).status_code == 422


def test_montecarlo_endpoint_shape_and_bounds():
    r = client.post("/scenario/montecarlo", json={"seed": 42, "n_paths": 500})
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"vintage", "computed_not_advice", "years", "percentiles",
                         "n_paths", "seed"}
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


def test_cors_allows_null_and_localhost_origins():
    r = client.get("/health", headers={"Origin": "null"})
    assert r.headers.get("access-control-allow-origin") == "null"
    r = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
