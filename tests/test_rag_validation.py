"""Offline checks for generated-output rejection; no provider/model needed."""
from unittest.mock import Mock

import pytest

from rag import chat, retrieve
from rag.validation import CORPUS_REFUSAL, checked_answer


@pytest.mark.parametrize("answer", ["Afirmación sin cita.", "Afirmación [0].", "Afirmación [2].",
                                    "Texto [1] y otra cita [1-999]."])
def test_invalid_references_are_rejected(answer):
    with pytest.raises(ValueError):
        checked_answer(answer, 1)


def test_grouped_citations_are_checked_individually():
    assert checked_answer("Texto [1, 2].", 2) == "Texto [1, 2]."
    with pytest.raises(ValueError):
        checked_answer("Texto [1, 3].", 2)


def test_refusal_does_not_smuggle_uncited_prose():
    answer = "El corpus no cubre esto. La deuda será 999999 % del PIB."
    assert checked_answer(answer, 1) == CORPUS_REFUSAL


@pytest.fixture()
def context(monkeypatch):
    passage = retrieve.Passage(1, "La deuda depende del saldo primario.", "Manual", "libros",
                               "academico", 1, None, 1.0, 0, 0)
    monkeypatch.setattr(retrieve, "search", lambda *a, **kw: [passage])
    monkeypatch.setattr(chat, "PROVIDERS", [{"name": "fake", "model": "fake"}])


def test_uncited_generated_answer_is_replaced_by_context_fallback(context, monkeypatch):
    monkeypatch.setattr(chat, "_call", lambda *a: "Cifra inventada 999999.")
    answer = chat.ask("¿Qué dice el manual?")
    assert "999999" not in answer.text
    assert answer.provider is None and answer.error
    assert answer.grounded is True  # compatibility field means context exists
    assert answer.passages


def test_valid_reference_does_not_claim_semantic_verification(context, monkeypatch):
    monkeypatch.setattr(chat, "_call", lambda *a: "Esta afirmación podría ser falsa [1].")
    answer = chat.ask("¿Qué dice el manual?")
    assert answer.provider == "fake"
    assert answer.grounded is True  # Structural validation is deliberately limited.


def test_invalid_stream_never_publishes_unchecked_deltas(context, monkeypatch):
    monkeypatch.setattr(chat, "_call_stream", lambda *a: iter(["Inventado ", "[99]."]))
    events = list(chat.stream("¿Qué dice el manual?"))
    assert [name for name, _ in events] == ["passages", "done"]
    assert "Inventado" not in events[-1][1]["answer"]


def test_interrupted_stream_does_not_publish_partial_answer(context, monkeypatch):
    def broken_stream(*args):
        yield "Respuesta parcial [1]."
        raise RuntimeError("interrupted")
    monkeypatch.setattr(chat, "_call_stream", broken_stream)
    events = list(chat.stream("¿Qué dice el manual?"))
    assert [name for name, _ in events] == ["passages", "done"]
    assert events[-1][1]["error"]


def test_valid_stream_publishes_after_reference_check(context, monkeypatch):
    monkeypatch.setattr(chat, "_call_stream", lambda *a: iter(["El saldo ", "importa [1]."]))
    events = list(chat.stream("¿Qué dice el manual?"))
    assert [name for name, _ in events] == ["passages", "delta", "done"]
    assert events[1][1]["text"] == events[2][1]["answer"]


def test_narration_accepts_known_rounding_and_rejects_new_magnitude():
    from engine.levers import Levers
    from explain.facts import build_facts
    from explain.narrate import NarrationUnavailable, validate_narration

    facts = build_facts(Levers(r=4.8), 2030)
    debt = next(out.value for out in facts.outcomes if out.key == "b")
    blocks = {"resumen": f"Deuda: {debt:.1f}.".replace(".", ",", 1),
              "mecanismo": "Respuesta condicional al tipo de interés.",
              "advertencia": "No es una previsión."}
    validate_narration(blocks, facts)
    blocks["resumen"] = "Deuda: 987654321 %."
    with pytest.raises(NarrationUnavailable, match="number absent"):
        validate_narration(blocks, facts)


def test_narration_does_not_accept_empty_fields():
    from explain.narrate import NarrationUnavailable, validate_narration

    with pytest.raises(NarrationUnavailable, match="malformed"):
        validate_narration({"resumen": "", "mecanismo": "texto", "advertencia": "texto"}, Mock())
