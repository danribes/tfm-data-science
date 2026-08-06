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
