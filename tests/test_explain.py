"""The explanation layer: facts, deterministic fallback, and the endpoint.

The LLM path is deliberately not exercised here — it needs a network and a key.
What is tested is the contract the LLM path depends on: that the facts are
correct, that the fallback always produces usable prose from them, and that the
endpoint degrades to the fallback instead of failing when narration is off.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from engine.constants import BASE_LEVERS
from engine.levers import Levers
from engine.spain import Y0, Y1, baseline, run_scenario
from explain.facts import build_facts, decompose, moved_levers
from explain.fallback import fallback_narration, nf

client = TestClient(app)

RATE_UP = Levers(r=BASE_LEVERS["r"] + 2.0)
ADVERSE = Levers(r=BASE_LEVERS["r"] + 2.0, pm=50.0, prima=150.0)


# ---- facts ----

def test_baseline_has_no_moved_levers():
    assert moved_levers(Levers()) == []


def test_moved_levers_reports_delta_against_vintage_base():
    moved = moved_levers(RATE_UP)
    assert len(moved) == 1
    assert moved[0].id == "r"
    assert moved[0].base == BASE_LEVERS["r"]
    assert moved[0].delta == pytest.approx(2.0)


def test_fresh_only_when_untouched_and_at_first_year():
    assert build_facts(Levers(), Y0).fresh is True
    assert build_facts(Levers(), 2040).fresh is False
    assert build_facts(RATE_UP, Y0).fresh is False


def test_outcomes_match_the_engine_exactly():
    """The whole design rests on this: facts are the engine, not a re-derivation."""
    facts = build_facts(RATE_UP, 2030)
    run, base = run_scenario(RATE_UP), baseline()
    for out in facts.outcomes:
        k = out.year - Y0
        assert out.value == pytest.approx(run[out.key][k])
        assert out.base == pytest.approx(base[out.key][k])
        assert out.delta == pytest.approx(run[out.key][k] - base[out.key][k])


def test_debt_outcome_is_pinned_to_the_end_of_the_projection():
    """The debt tile reads 2050 whatever the horizon; the rest follow the horizon."""
    facts = build_facts(RATE_UP, 2030)
    by_key = {o.key: o for o in facts.outcomes}
    assert by_key["b"].year == Y1
    assert by_key["u"].year == 2030


def test_direction_accounts_for_which_way_is_bad():
    """Debt up is 'empeora'; the public balance up is 'mejora'. Same sign, opposite reading."""
    facts = build_facts(Levers(sp=1.0), 2030)
    by_key = {o.key: o for o in facts.outcomes}
    assert by_key["b"].delta < 0 and by_key["b"].direction == "mejora"
    assert by_key["saldo"].delta > 0 and by_key["saldo"].direction == "mejora"


def test_single_lever_decomposition_equals_the_joint_run():
    """With one lever moved there is no interaction to account for."""
    contribs, interaction, joint = decompose(RATE_UP, "b", Y1 - Y0)
    assert len(contribs) == 1
    assert contribs[0].delta == pytest.approx(joint)
    assert interaction == pytest.approx(0.0, abs=1e-9)
    assert contribs[0].share == pytest.approx(1.0)


def test_multi_lever_interaction_is_reported_not_absorbed():
    """The engine is non-linear: singles must not be forced to sum to the joint."""
    contribs, interaction, joint = decompose(ADVERSE, "b", Y1 - Y0)
    assert len(contribs) == 3
    singles = sum(ct.delta for ct in contribs)
    assert interaction == pytest.approx(joint - singles)
    # Shares describe the gross single-lever movement, so they close on 1.
    assert sum(ct.share for ct in contribs) == pytest.approx(1.0)


def test_contributions_sorted_by_magnitude():
    contribs, _, _ = decompose(ADVERSE, "b", Y1 - Y0)
    mags = [abs(ct.delta) for ct in contribs]
    assert mags == sorted(mags, reverse=True)


def test_redlines_carry_the_baseline_status_for_comparison():
    facts = build_facts(ADVERSE, Y0)
    assert facts.redlines
    for rl in facts.redlines:
        assert rl.status in {"crossed", "near", "safe"}
        assert rl.base_status in {"crossed", "near", "safe"}


def test_first_crossing_year_is_within_the_projection():
    facts = build_facts(ADVERSE, Y0)
    for rl in facts.redlines:
        if rl.first_year is not None:
            assert Y0 <= rl.first_year <= Y1


def test_mechanism_only_covers_moved_levers():
    facts = build_facts(RATE_UP, Y0)
    assert set(facts.mechanism) == {"r"}
    assert facts.mechanism["r"], "the rate lever must have a documented chain"


# ---- deterministic fallback ----

def test_spanish_number_formatting():
    assert nf(223.8, 1) == "223,8"
    assert nf(1234.5, 1) == "1.234,5"
    assert nf(3.42, 2) == "3,42"


def test_fallback_always_returns_all_three_blocks():
    for levers, horizon in [(Levers(), Y0), (RATE_UP, 2030), (ADVERSE, 2050)]:
        blocks = fallback_narration(build_facts(levers, horizon))
        assert set(blocks) == {"resumen", "mecanismo", "advertencia"}
        assert all(v.strip() for v in blocks.values())


def test_fallback_names_the_lever_and_its_numbers():
    blocks = fallback_narration(build_facts(RATE_UP, Y0))
    assert "Tipo de interés" in blocks["resumen"]
    assert nf(BASE_LEVERS["r"] + 2.0, 2) in blocks["resumen"]


def test_fallback_states_the_interaction_residual():
    blocks = fallback_narration(build_facts(ADVERSE, Y0))
    assert "Interacción entre palancas" in blocks["mecanismo"]
    assert "no es lineal" in blocks["mecanismo"]


def test_fallback_flags_newly_crossed_red_lines():
    blocks = fallback_narration(build_facts(ADVERSE, 2050))
    facts = build_facts(ADVERSE, 2050)
    newly = [r for r in facts.redlines
             if r.status == "crossed" and r.base_status != "crossed"]
    if newly:
        assert "que la base no cruzaba" in blocks["advertencia"]


def test_fallback_always_carries_the_conditional_disclaimer():
    for levers in (Levers(), RATE_UP, ADVERSE):
        blocks = fallback_narration(build_facts(levers, Y0))
        assert "no es una previsión" in blocks["advertencia"].lower()


def test_fresh_state_says_nothing_is_projected_yet():
    blocks = fallback_narration(build_facts(Levers(), Y0))
    assert "línea base" in blocks["resumen"]


# ---- endpoint ----

def test_explain_without_narration_uses_the_deterministic_path():
    r = client.post("/explain", json={"levers": {"r": 4.8}, "horizon": 2030,
                                      "narrate": False})
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "deterministic"
    assert body["model"] is None
    assert body["resumen"] and body["mecanismo"] and body["advertencia"]


def test_explain_returns_the_decomposition_for_charting():
    r = client.post("/explain", json={"levers": {"r": 4.8, "pm": 50.0},
                                      "horizon": 2050, "narrate": False})
    body = r.json()
    assert len(body["contributions"]) == 2
    assert body["headline_key"] == "b"
    assert body["headline_year"] == Y1
    assert {c["lever_id"] for c in body["contributions"]} == {"r", "pm"}


def test_explain_defaults_to_baseline_levers():
    r = client.post("/explain", json={"narrate": False})
    assert r.status_code == 200
    assert r.json()["contributions"] == []


def test_explain_rejects_an_unknown_series():
    r = client.post("/explain", json={"headline": "no_such_series",
                                      "narrate": False})
    assert r.status_code == 422


def test_explain_rejects_a_horizon_outside_the_projection():
    assert client.post("/explain", json={"horizon": 2099}).status_code == 422


def test_explain_carries_the_vintage_meta():
    body = client.post("/explain", json={"narrate": False}).json()
    assert body["vintage"]
    assert body["computed_not_advice"] is True


def test_narration_failure_falls_back_rather_than_erroring(monkeypatch):
    """A dead API key must degrade the text, never break the endpoint."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = client.post("/explain", json={"levers": {"r": 4.8}, "narrate": True})
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "deterministic"
    assert "ANTHROPIC_API_KEY" in body["fallback_reason"]
    assert body["resumen"].strip()


def test_generate_policy_brief_html():
    from explain.report import generate_policy_brief_html
    html_text = generate_policy_brief_html(RATE_UP, horizon=2050)
    assert "<!DOCTYPE html>" in html_text
    assert "España en Escenarios" in html_text
    assert "Deuda Pública" in html_text
    assert "2026-07-31" in html_text


def test_scenario_report_endpoints():
    # GET /scenario/report
    r_get = client.get("/scenario/report")
    assert r_get.status_code == 200
    assert "text/html" in r_get.headers["content-type"]
    assert "España en Escenarios" in r_get.text

    # POST /scenario/report
    r_post = client.post("/scenario/report", json={"levers": {"r": 4.8, "sp": 1.0}, "horizon": 2040})
    assert r_post.status_code == 200
    assert "text/html" in r_post.headers["content-type"]
    assert "2040" in r_post.text

