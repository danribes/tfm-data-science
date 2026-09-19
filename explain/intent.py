"""Resolve a typed question into a scenario the engine can actually run.

Phase 2 of the LLM layer. Phase 1 lets the model write about a scenario; this
lets it decide *which* scenario, which is the more dangerous half — so the model
never returns prose here, only a choice from a closed vocabulary, and every part
of that choice is validated against the engine before anything runs.

What it may return:
  series   one of ANSWERABLE, nothing else
  year     clamped into the projection window
  levers   real lever ids only, each clamped to its own published range

What it may not do: invent a series, invent a lever, or answer in words. If the
question is outside what the engine computes, the correct output is a refusal,
and the caller shows that rather than a number.

Failure of any kind raises IntentUnavailable, and the caller falls back to the
deterministic keyword matcher in the frontend. The app is never one API call
away from being unable to answer.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from engine.levers import LEVER_SPECS
from engine.spain import Y0, Y1
from explain.narrate import _load_env_file

MODEL = os.environ.get("EVO_INTENT_MODEL", "claude-haiku-4-5-20251001")
MAX_TOKENS = 900

#: The series the UI can render an answer for, with the words a reader would
#: use. This list is the contract: anything outside it is a refusal, not a
#: guess. Kept in step with frontend/src/personas/questions.ts.
ANSWERABLE: dict[str, str] = {
    "b": "deuda pública (% PIB)",
    "saldo": "saldo público, déficit o superávit (% PIB)",
    "int": "intereses de la deuda (% PIB)",
    "bono": "rendimiento del bono a 10 años (%)",
    "spread": "prima de riesgo (pb)",
    "u": "paro total (%)",
    "ujuv": "paro juvenil (%)",
    "temp": "temporalidad (%)",
    "pi": "inflación IPCA (%)",
    "g": "crecimiento del PIB real (%)",
    "r": "tipo de interés de referencia, Euríbor (%)",
    "precio": "precio de la vivienda (€)",
    "cuota": "cuota hipotecaria mensual (€/mes)",
    "esf": "esfuerzo: parte del salario que se va en la hipoteca (%)",
    "sobre": "sobrecarga por coste de vivienda (%)",
    "ipv": "crecimiento del precio de la vivienda (% a/a)",
    "salario": "salario medio anual (€/año)",
    "salmes": "salario medio mensual (€/mes)",
    "wrealIdx": "salario real acumulado (índice, base 100 en 2026)",
    "nomreal": "poder de compra de la nómina o pensión (índice, base 100)",
    "pens": "gasto en pensiones (% PIB)",
    "dep": "tasa de dependencia, mayores por cada 100 en edad de trabajar",
    "arop": "pobreza o exclusión infantil (%)",
    "edu": "gasto público en educación (% PIB)",
    "auton": "peso del autoempleo (% del empleo)",
}

_LEVER_DOC = {s["id"]: f'{s["nm"]} [{s["min"]}, {s["max"]}]' for s in LEVER_SPECS}
_RANGES = {s["id"]: (float(s["min"]), float(s["max"])) for s in LEVER_SPECS}

#: Sentinel rather than null. The API rejects an enum whose values do not all
#: match a nullable union type ("Enum value 'b' does not match declared type
#: ['string','null']"), so "no series fits" is a value in the enum.
NONE_SERIES = "ninguna"

SCHEMA = {
    "type": "object",
    "properties": {
        "series": {"type": "string", "enum": [*ANSWERABLE, NONE_SERIES]},
        # No minimum/maximum: the schema validator rejects them on an integer
        # ("For 'integer' type, properties maximum, minimum are not supported").
        # The window is stated in the prompt and enforced by clamping below,
        # which is where it has to hold anyway — the model is not trusted.
        "year": {"type": "integer"},
        "levers": {
            "type": "object",
            "properties": {k: {"type": "number"} for k in _RANGES},
            "additionalProperties": False,
        },
        "refusal": {"type": "string"},
    },
    # Only `series` is required. `year`, `levers` and `refusal` are omitted when
    # they do not apply, which keeps every field a plain type: the API rejects a
    # nullable union alongside an enum, and mixing the two styles invites the
    # same 400 in a field that happens not to have an enum today.
    "required": ["series"],
    "additionalProperties": False,
}

SYSTEM = f"""\
Traduces preguntas sobre la economía española a una consulta que un motor de \
escenarios puede ejecutar. No respondes a la pregunta: sólo dices qué habría \
que calcular.

El motor proyecta 2026-2050 sobre un vintage congelado. Es un motor de \
escenarios condicionales, no un oráculo: responde «si esta palanca valiera X, \
esta serie saldría Y».

## Series que puedes pedir
{chr(10).join(f"  {k} — {v}" for k, v in ANSWERABLE.items())}

## Palancas que puedes mover (con su rango)
{chr(10).join(f"  {k} — {v}" for k, v in _LEVER_DOC.items())}

## Reglas
- `series`: la que responde a la pregunta. Sólo de la lista. Si ninguna encaja, \
pon `"{NONE_SERIES}"` y explica por qué en `refusal`.
- `year`: si la pregunta menciona un año, úsalo, entre {Y0} y {Y1}. Si no, \
omite el campo.
- `levers`: sólo si la pregunta plantea un supuesto explícito («si el Euríbor \
sube al 5 %», «con una consolidación de 2 puntos»). Usa el valor absoluto que \
tendría la palanca, no el incremento. Si no hay supuesto, `{{}}`.
- `refusal`: rellénalo cuando la pregunta pida algo que el motor no calcula \
(quién ganará unas elecciones, qué debería hacer el usuario con su dinero, \
datos de otro país, hechos históricos concretos). Una frase, en español, \
diciendo qué es lo que no se puede responder.
- Nunca inventes una serie ni una palanca que no estén arriba.
- Una pregunta que pide consejo («¿me conviene comprar?») no se responde con \
consejo, pero sí puede resolverse a la serie que da el dato relevante.
"""


class IntentUnavailable(RuntimeError):
    """The resolver could not run. The caller falls back to keyword matching."""


@dataclass(frozen=True)
class Intent:
    series: str | None
    year: int | None
    levers: dict[str, float] = field(default_factory=dict)
    refusal: str | None = None
    model: str | None = None


def _clamp(lever: str, value: float) -> float:
    lo, hi = _RANGES[lever]
    return max(lo, min(hi, float(value)))


def resolve_intent(question: str, *, timeout: float = 20.0) -> Intent:
    """Map free text to a runnable query, or to a refusal.

    Everything the model returns is checked here rather than trusted: an
    unknown series becomes a refusal, an unknown lever is dropped, and a lever
    value outside its published range is clamped to it. The model chooses; the
    engine's own bounds decide what is admissible.
    """
    text = question.strip()
    if len(text) < 3:
        raise IntentUnavailable("question too short")

    _load_env_file()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise IntentUnavailable("ANTHROPIC_API_KEY not set")
    try:
        import anthropic
    except ImportError as exc:
        raise IntentUnavailable("anthropic SDK not installed") from exc

    client = anthropic.Anthropic(timeout=timeout, max_retries=1)
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=[{
                "type": "text",
                "text": SYSTEM,
                # The vocabulary never changes; only the question does.
                "cache_control": {"type": "ephemeral"},
            }],
            output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content": text}],
        )
    except Exception as exc:
        raise IntentUnavailable(f"{type(exc).__name__}: {exc}") from exc

    if response.stop_reason == "refusal":
        raise IntentUnavailable("model declined the request")

    try:
        raw = json.loads("".join(b.text for b in response.content if b.type == "text"))
    except (ValueError, AttributeError) as exc:
        raise IntentUnavailable(f"unparseable response: {exc}") from exc

    series = raw.get("series")
    if series == NONE_SERIES:
        series = None
    if series is not None and series not in ANSWERABLE:
        # Schema should prevent this; treat a breach as a refusal rather than
        # passing an unknown key to the engine.
        return Intent(None, None, {}, "El motor no calcula esa serie.", MODEL)

    year = raw.get("year")
    if isinstance(year, int):
        year = max(Y0, min(Y1, year))
    else:
        year = None

    levers = {
        k: _clamp(k, v)
        for k, v in (raw.get("levers") or {}).items()
        if k in _RANGES and isinstance(v, (int, float))
    }

    refusal = raw.get("refusal") or None
    if series is None and refusal is None:
        refusal = "Esa pregunta queda fuera de lo que calcula el motor."

    return Intent(series, year, levers, refusal, MODEL)
