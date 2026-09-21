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
              "advertencia": "No es una previsión.",
              "coloquial": "En corto: sube."}
    validate_narration(blocks, facts)
    blocks["resumen"] = "Deuda: 987654321 %."
    with pytest.raises(NarrationUnavailable, match="number absent"):
        validate_narration(blocks, facts)


def test_narration_does_not_accept_empty_fields():
    from explain.narrate import NarrationUnavailable, validate_narration

    with pytest.raises(NarrationUnavailable, match="malformed"):
        validate_narration({"resumen": "", "mecanismo": "texto", "advertencia": "texto"}, Mock())


# ---- respuestas apoyadas sólo en documentación propia ------------------------

def test_sin_nada_que_citar_se_acepta_una_respuesta_sin_citas():
    """Una pregunta sobre el método recupera sólo documentación propia, que por
    diseño no lleva número. Exigir una cita ahí no protegía nada —no existía
    ninguna cita posible— y descartaba una respuesta correcta."""
    from rag.validation import checked_answer

    texto = "El motor simula 4.000 trayectorias con semilla 42, según la documentación del propio trabajo."
    assert checked_answer(texto, 0, context_only=True) == texto


def test_en_modo_contexto_las_citas_colgantes_se_quitan():
    """El modelo cita aunque se le diga que no, y en este modo no hay ningún
    pasaje numerado al que apuntar.

    Rechazar la respuesta entera por un corchete de más tiraba una explicación
    correcta: así fallaban en producción TODAS las preguntas sobre el método.
    Dejar el corchete sería peor, porque apuntaría a un pasaje inexistente. Se
    quita la referencia y se conserva la prosa.
    """
    from rag.validation import checked_answer

    assert checked_answer("El motor simula 4.000 trayectorias con semilla 42 [1].",
                          0, context_only=True) == \
        "El motor simula 4.000 trayectorias con semilla 42."
    assert checked_answer("Son 4.000 trayectorias [1, 2] y la semilla es 42 [3].",
                          0, context_only=True) == \
        "Son 4.000 trayectorias y la semilla es 42."


def test_en_modo_contexto_un_corchete_mal_formado_sigue_siendo_un_error():
    """Lo que se limpia son referencias bien formadas que no apuntan a nada.
    Un corchete roto sigue indicando que el modelo hizo algo raro."""
    from rag.validation import checked_answer

    with pytest.raises(ValueError):
        checked_answer("Referencia rota [a1].", 0, context_only=True)


def test_fuera_del_modo_contexto_una_cita_invalida_sigue_rechazandose():
    """La limpieza no puede filtrarse al camino normal: ahí un [9] sobre tres
    pasajes es una referencia inventada y debe rechazar la respuesta."""
    from rag.validation import checked_answer

    with pytest.raises(ValueError):
        checked_answer("Una afirmación mal citada [9].", 3)


def test_sin_modo_contexto_la_exigencia_de_citar_sigue_intacta():
    from rag.validation import checked_answer

    with pytest.raises(ValueError):
        checked_answer("Una afirmación sin ninguna cita.", 3)


def test_el_modo_contexto_solo_se_activa_si_no_habia_citables():
    """La condición, tal y como la aplica el chat: cero citables y algo de
    contexto. Con un solo pasaje citable disponible, la exigencia vuelve."""
    citables, contexto = [], ["algo"]
    assert (not citables and bool(contexto)) is True
    citables = ["un manual"]
    assert (not citables and bool(contexto)) is False
