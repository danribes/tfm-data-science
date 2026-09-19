"""The intent resolver's guardrails, which are the part that must not depend
on a network call to hold.

The model's choice is never trusted: these tests pin the validation that runs
after it. The live path is exercised against the deployed Space, not here.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from engine.levers import LEVER_SPECS
from engine.spain import SERIES_KEYS, Y0, Y1
from explain import intent as it

client = TestClient(app)


def test_every_answerable_series_exists_in_the_engine():
    """A series the model may name but the engine cannot produce would reach
    /explain as an unknown headline and 422 there instead of here."""
    for key in it.ANSWERABLE:
        assert key in SERIES_KEYS, key


def test_schema_enumerates_exactly_the_answerable_series():
    enum = [x for x in it.SCHEMA["properties"]["series"]["enum"] if x is not None]
    assert set(enum) == set(it.ANSWERABLE)


def test_schema_year_is_bounded_to_the_projection():
    year = it.SCHEMA["properties"]["year"]
    assert year["minimum"] == Y0 and year["maximum"] == Y1


def test_schema_offers_only_real_levers():
    real = {s["id"] for s in LEVER_SPECS}
    assert set(it.SCHEMA["properties"]["levers"]["properties"]) == real


@pytest.mark.parametrize("lever,given,expected", [
    ("r", 99.0, 6.0),      # above max
    ("r", -5.0, 0.0),      # below min
    ("prima", 150.0, 150.0),  # inside, untouched
    ("sp", -99.0, -4.0),
])
def test_lever_values_are_clamped_to_their_published_range(lever, given, expected):
    """A model that returns «el Euríbor al 99 %» must not reach the engine with
    it: the published range is the bound, not the suggestion."""
    assert it._clamp(lever, given) == expected


def test_short_question_is_refused_before_any_api_call():
    with pytest.raises(it.IntentUnavailable):
        it.resolve_intent("eh")


def test_endpoint_answers_503_when_the_resolver_cannot_run(monkeypatch):
    """The caller falls back to its own matcher on 503, so this route failing
    must never surface as a 500."""
    def boom(_q, **_kw):
        raise it.IntentUnavailable("no key")

    monkeypatch.setattr("api.main.resolve_intent", boom)
    r = client.post("/ask", json={"question": "¿cuánta deuda habrá en 2050?"})
    assert r.status_code == 503
    assert "no key" in r.json()["detail"]


def test_endpoint_rejects_an_empty_question():
    assert client.post("/ask", json={"question": "x"}).status_code == 422


def test_endpoint_passes_through_a_refusal_as_a_valid_answer(monkeypatch):
    """A refusal is an expected outcome, not an error: 200 with series null."""
    monkeypatch.setattr(
        "api.main.resolve_intent",
        lambda _q, **_kw: it.Intent(None, None, {}, "Fuera del motor.", "test"),
    )
    r = client.post("/ask", json={"question": "¿quién ganará las elecciones?"})
    assert r.status_code == 200
    body = r.json()
    assert body["series"] is None and body["refusal"] == "Fuera del motor."


def test_endpoint_returns_the_resolved_query(monkeypatch):
    monkeypatch.setattr(
        "api.main.resolve_intent",
        lambda _q, **_kw: it.Intent("esf", 2040, {"r": 5.0}, None, "test"),
    )
    body = client.post("/ask", json={"question": "hipoteca si el euríbor sube al 5 en 2040"}).json()
    assert (body["series"], body["year"], body["levers"]) == ("esf", 2040, {"r": 5.0})
