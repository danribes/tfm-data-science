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
from explain.facts import (HEADLINES, SERIES_META, SIDES, build_facts, decompose,
                           moved_levers)
from explain.fallback import _signed, fallback_narration, nf

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


def test_fallback_always_returns_every_block():
    """Four now, since the answer carries a plain-language closing.

    The deterministic path writes one too, so the UI never has to branch on
    which path produced the text — a colloquial block that only appears when
    the model is reachable would read as a feature that keeps breaking.
    """
    for levers, horizon in [(Levers(), Y0), (RATE_UP, 2030), (ADVERSE, 2050)]:
        blocks = fallback_narration(build_facts(levers, horizon))
        assert set(blocks) == {"resumen", "mecanismo", "advertencia", "coloquial"}
        assert all(v.strip() for v in blocks.values())


def test_fallback_coloquial_says_something_of_its_own():
    """Not a copy of the summary, and it carries the headline number."""
    facts = build_facts(RATE_UP, 2040)
    blocks = fallback_narration(facts)
    head = next(o for o in facts.outcomes if o.key == facts.headline_key)
    assert blocks["coloquial"] != blocks["resumen"]
    assert nf(head.value, head.dec) in blocks["coloquial"]
    # The disclaimer travels with the relaxed register, not only the formal one.
    assert "bola de cristal" in blocks["coloquial"]


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
    import importlib
    narration = importlib.import_module("explain.narrate")
    monkeypatch.setattr(narration, "_load_env_file", lambda: None)
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



def test_fallback_names_the_headline_series_not_always_the_debt():
    """A non-debt headline must be called by its own name.

    The summary printed the headline series' values under the fixed label «la
    deuda pública», so asking about the mortgage effort produced a sentence
    that read as a debt figure and was wrong by a factor of ten. Plausible and
    wrong is the failure mode worth a test.
    """
    facts = build_facts(RATE_UP, 2040, headline="esf")
    blocks = fallback_narration(facts)
    whole = " ".join(blocks.values())

    esf = next(o for o in facts.outcomes if o.key == "esf")
    assert esf.label in blocks["resumen"]
    # The word may still appear when debt is listed among the other outcomes,
    # but never as the subject of the headline sentence.
    assert "la deuda pública queda" not in whole
    assert f"La deuda pública sube de {nf(esf.base, esf.dec)}" not in whole
    assert f"La deuda pública baja de {nf(esf.base, esf.dec)}" not in whole


def test_fallback_decomposition_uses_the_headline_unit():
    """The decomposition line hardcoded %PIB, which is wrong for a % series."""
    facts = build_facts(RATE_UP, 2040, headline="esf")
    mech = fallback_narration(facts)["mecanismo"]
    if facts.contributions:
        esf = next(o for o in facts.outcomes if o.key == "esf")
        assert f"en el cambio de {esf.label.lower()}" in mech


def test_fallback_states_the_change_in_the_series_own_unit():
    """«puntos» is the right word for a percentage and nonsense for a price.

    The summary closed every headline sentence with «(−104.420 puntos)», which
    for the house price is not a rounding slip but a different quantity: the
    sentence had already printed euros two clauses earlier. Third time this
    family of bug appears — a unit or a label fixed in the template while the
    series behind it varies — hence a test per member of the family.
    """
    facts = build_facts(RATE_UP, 2035, headline="precio")
    resumen = fallback_narration(facts)["resumen"]
    precio = next(o for o in facts.outcomes if o.key == "precio")

    assert f"({_signed(precio.delta, precio.dec)} €)" in resumen
    # Only the headline clause: the «En el mismo escenario» list after it
    # carries percentage series, and those do move in puntos.
    assert f"({_signed(precio.delta, precio.dec)} puntos)" not in resumen

    # And still «puntos» where that is the correct word — of GDP, for a ratio.
    deuda = fallback_narration(build_facts(RATE_UP, 2035, headline="b"))["resumen"]
    assert "puntos de PIB)" in deuda


def test_every_change_in_a_percentage_is_said_in_points():
    """«Paro juvenil −1,9 %» reads as a relative fall; it is 1,9 puntos.

    The headline clause already said «puntos»; the «En el mismo escenario»
    list, the per-lever decomposition and the colloquial line still printed
    the level's unit next to a change. A change of a percentage is in points
    and a change of a share of GDP in points of GDP, everywhere."""
    for key in ("u", "ujuv", "b", "saldo"):
        facts = build_facts(RATE_UP, 2035, headline=key)
        blocks = fallback_narration(facts)
        head = next(o for o in facts.outcomes if o.key == key)
        unit = "puntos de PIB" if head.unit == "%PIB" else "puntos"
        assert f"{_signed(head.delta, head.dec)} {unit} frente a no tocar nada" in blocks["coloquial"], key
        for o in facts.outcomes:
            if o.key != key and abs(o.delta) > 0.05 and o.unit.startswith("%"):
                assert f"{_signed(o.delta, o.dec)} {o.unit} en" not in blocks["resumen"], (key, o.key)
        if facts.contributions and head.unit.startswith("%"):
            assert f"{unit} en total" in blocks["mecanismo"], key


def test_fallback_leaves_no_double_space_for_a_unitless_series():
    """Several series are indices and carry no unit."""
    unitless = [k for k, m in SERIES_META.items() if not m["unit"]]
    assert unitless, "the guard is pointless if every series has a unit"
    for key in unitless:
        blocks = fallback_narration(build_facts(RATE_UP, 2035, headline=key))
        for block in blocks.values():
            for line in block.splitlines():
                # lstrip, because the decomposition bullets are indented on
                # purpose; what must not appear is a gap left by an absent unit.
                assert "  " not in line.lstrip(), f"double space for {key}: {line!r}"


def test_headline_year_is_the_year_the_headline_reports():
    """The summary said «en 2030» and the decomposition under it said «2050».

    headline_year was pinned to Y1 while the outcome followed the horizon, so
    one answer spanned two horizons and the shares described a movement other
    than the number printed above them.
    """
    facts = build_facts(RATE_UP, 2030, headline="u")
    head = next(o for o in facts.outcomes if o.key == "u")
    assert facts.headline_year == head.year == 2030
    assert "en 2030" in fallback_narration(facts)["mecanismo"]

    # The series flagged at_end still report the end of the projection.
    debt = build_facts(RATE_UP, 2030, headline="b")
    assert debt.headline_year == Y1


def test_decomposition_is_computed_at_the_headline_year():
    """Shares must describe the movement the summary just stated."""
    facts = build_facts(ADVERSE, 2030, headline="u")
    if facts.contributions:
        head = next(o for o in facts.outcomes if o.key == "u")
        assert facts.joint_delta == pytest.approx(head.delta, abs=1e-9)


def test_reader_relative_series_name_both_sides_instead_of_judging():
    """Persona 03 was told a cheaper house «es peor».

    up_is_bad is one global bit, and for a house price it encodes the owner's
    interest; the buyer reading the same screen was shown the opposite of the
    truth, one sentence away from a mortgage payment judged from their side.
    """
    facts = build_facts(RATE_UP, 2035, headline="precio")
    head = next(o for o in facts.outcomes if o.key == "precio")
    coloquial = fallback_narration(facts)["coloquial"]

    assert head.delta < 0, "the fixture is pointless if the price does not fall"
    assert "quien quiere comprar" in coloquial
    assert "es peor" not in coloquial
    # Falling: the buyer gains and the owner loses, not the other way round.
    assert coloquial.index("quien quiere comprar") < coloquial.index("quien ya tiene piso")


def test_unambiguous_series_keep_their_verdict():
    """Not every series is contested: a rising debt is nobody's good news."""
    coloquial = fallback_narration(build_facts(RATE_UP, 2035, headline="b"))["coloquial"]
    assert "para quien lo vive" in coloquial


def test_every_reader_relative_series_is_a_real_series():
    """A typo here would silently restore the verdict it was meant to replace."""
    known = {h["key"] for h in HEADLINES} | set(SERIES_META)
    assert set(SIDES) <= known, set(SIDES) - known


def test_validate_accepts_the_blocks_the_schema_asks_for():
    """A key the schema requires must not be treated as contamination.

    validate_narration compared the key set for equality, so adding
    `coloquial` to the output schema made every well-formed response fail and
    the endpoint served templates while reporting itself healthy. The failure
    was invisible: `source` said "deterministic", which is also what a missing
    key looks like.
    """
    from explain.narrate import NarrationUnavailable, validate_narration

    facts = build_facts(RATE_UP, 2040)
    good = {"resumen": "Sube.", "mecanismo": "Por el tipo.",
            "advertencia": "Es condicional.", "coloquial": "En corto: sube."}
    validate_narration(good, facts)          # must not raise

    with pytest.raises(NarrationUnavailable):
        validate_narration({k: v for k, v in good.items() if k != "coloquial"}, facts)
    with pytest.raises(NarrationUnavailable):
        validate_narration({**good, "resumen": "  "}, facts)


def test_contribution_share_is_supplied_as_a_percentage_too():
    """The model may not compute, so anything prose needs must be handed over.

    It wrote "99,6 %" from a share of 0,9963 — correct, and rejected by the
    numeric-inventory check, which dropped the whole narration to templates.
    The percentage is now a fact, so no multiplication is required.
    """
    facts = build_facts(ADVERSE, 2040)
    assert facts.contributions
    for ct in facts.contributions:
        assert ct.share_pct == pytest.approx(round(ct.share * 100, 1))
    payload = facts.to_dict()
    assert all("share_pct" in c for c in payload["contributions"])


def test_narration_is_opt_in_not_the_default():
    """Templates are the reliable path, so they are what an unasked request gets.

    The model honours "write, never compute" about four times in five; the rest
    trip the numeric check and fall back. Falling back is invisible from
    outside, so the default is the path that always works and the nicer prose
    is switched on deliberately.
    """
    from explain.narrate import NARRATE_BY_DEFAULT

    assert NARRATE_BY_DEFAULT is False, "narration must not default on"
    body = client.post("/explain", json={"levers": {"r": 4.8}, "horizon": 2040}).json()
    assert body["source"] == "deterministic"
    assert body["fallback_reason"] is None, "not asking is not a failure"
    assert body["coloquial"].strip(), "the two-part answer survives without the model"


def test_every_answerable_series_narrates_about_itself():
    """The answer panel asks about whichever series its question resolved to.

    Only five series were ever built into outcomes, so a question about
    pensions was answered about the deficit and the colloquial line claimed
    nothing had moved — for twenty-two of the twenty-seven series the profiles
    ask about. Each must now name itself in both registers.
    """
    from explain.facts import SERIES_META, HEADLINES

    known = {h["key"] for h in HEADLINES} | set(SERIES_META)
    levers = Levers(r=4.8, idx=-0.5)
    for key in sorted(known):
        facts = build_facts(levers, 2040, headline=key)
        head = next((o for o in facts.outcomes if o.key == key), None)
        assert head is not None, f"{key}: no outcome for the requested series"
        blocks = fallback_narration(facts)
        assert head.label in blocks["resumen"], f"{key}: formal block omits it"
        assert head.label in blocks["coloquial"], f"{key}: colloquial block omits it"
        assert "no lo suficiente" not in blocks["coloquial"], f"{key}: generic filler"


def test_series_metadata_matches_the_engine():
    """A label here is user-facing prose; a key that is not a series is a
    silent KeyError the moment someone asks about it."""
    from engine.spain import SERIES_KEYS
    from explain.facts import SERIES_META

    for key, meta in SERIES_META.items():
        assert key in SERIES_KEYS, key
        assert meta["label"].strip() and meta["label"][0].isupper(), key
        assert isinstance(meta["dec"], int) and isinstance(meta["up_is_bad"], bool), key


def test_mecanismo_explains_in_plain_words_and_folds_the_constants():
    """«r · Tipo de interés → coste de refinanciación (REFI = 0,14); …» for all
    six moved levers, including the ones that move temporalidad by +0,0, was
    unreadable. The plain text explains only the levers that move the figure,
    names the rest once, and keeps the constants on one «Detalle técnico» line."""
    levers = Levers(r=BASE_LEVERS["r"] - 2.65, prima=105.0, idx=-0.8, z=-1.6, tau=-1.0)
    mech = fallback_narration(build_facts(levers, 2050, headline="temp"))["mecanismo"]
    lines = mech.splitlines()
    tech = [ln for ln in lines if ln.startswith("Detalle técnico:")]
    assert len(tech) == 1 and "A_Z = 1,10" in tech[0]
    body = "\n".join(ln for ln in lines if not ln.startswith("Detalle técnico:"))
    for jargon in ("REFI", "TERM", "E_R", "curva WS", "curva PS", "→", "(1+r−g)"):
        assert jargon not in body, jargon
    assert "convenios, las indemnizaciones y el salario mínimo" in body
    assert "No mueven esta cifra, o casi nada:" in body
    assert "Prima de riesgo" in body.split("No mueven esta cifra")[1]


def test_mecanismo_says_so_when_no_moved_lever_reaches_the_figure():
    levers = Levers(r=BASE_LEVERS["r"] - 0.85, prima=105.0, idx=-0.8)
    mech = fallback_narration(build_facts(levers, 2050, headline="d1"))["mecanismo"]
    assert mech.startswith("Ninguna de las palancas que has movido cambia salarios públicos")
    assert "Cuánto pesa" not in mech
