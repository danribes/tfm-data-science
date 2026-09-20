"""Narrate precomputed facts with Claude. The model writes; it never computes.

Every figure the model is allowed to use is handed to it in the facts payload.
The system prompt is large and frozen (methodology, coefficients, house style)
so it carries a cache breakpoint; the volatile facts go last, after it. That
ordering is what makes this affordable: the cached prefix reads at 0.1x.

If anything goes wrong — no key, no network, a refusal, a malformed response —
this module raises, and the caller falls back to `explain.fallback`. Successful
responses pass shape and numeric-inventory checks. These checks do
not prove semantic fidelity or that numbers are attached to the right concept.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from engine import constants as c
from explain.facts import ExplanationFacts

_ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


def _load_env_file() -> None:
    """Read KEY=value lines from a gitignored .env, without adding a dependency.

    Only fills names that are not already set, so a real environment variable
    and the Space's secret both win over the file. Deploys set the variable
    directly and never ship a .env.
    """
    try:
        with open(_ENV_FILE, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, _, value = line.partition("=")
                name = name.strip()
                if name.startswith("export "):
                    name = name[len("export "):].strip()
                value = value.strip().strip('"').strip("'")
                if name and name not in os.environ:
                    os.environ[name] = value
    except OSError:
        pass  # no file is the normal case in a deploy

#: Overridable so a demo can run on a cheaper model without a code change.
MODEL = os.environ.get("EVO_EXPLAIN_MODEL", "claude-haiku-4-5-20251001")
#: Empty by default: `effort` is an Opus-family control and sending it to a
#: model that does not take it is a 400, which degrades to templates silently.
#: Set it explicitly alongside EVO_EXPLAIN_MODEL when moving back to Opus.
EFFORT = os.environ.get("EVO_EXPLAIN_EFFORT", "")
MAX_TOKENS = 4000  # headroom: on Opus 5 thinking counts against this too

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "resumen": {
            "type": "string",
            "description": "2-4 frases en lenguaje llano. Qué ha cambiado y qué "
                           "implica. Sin jerga, sin coeficientes, sin fórmulas.",
        },
        "mecanismo": {
            "type": "string",
            "description": "Explicación técnica: la cadena causal de cada palanca "
                           "con sus coeficientes, la descomposición por palanca y "
                           "el residuo de interacción. Puede citar constantes.",
        },
        "advertencia": {
            "type": "string",
            "description": "Líneas rojas cruzadas o próximas, y los límites de "
                           "lectura del resultado.",
        },
        "coloquial": {
            "type": "string",
            "description": "2-4 frases. Lo mismo, contado como se lo contarías "
                           "a un amigo en un bar: llano, relajado, con ironía si "
                           "viene a cuento. Sin cifras nuevas, sin tecnicismos y "
                           "sin dejar de ser cierto.",
        },
    },
    "required": ["resumen", "mecanismo", "advertencia", "coloquial"],
    "additionalProperties": False,
}

SYSTEM = f"""\
Eres el explicador de «España en escenarios», una herramienta abierta de \
proyección fiscal y de vivienda construida sobre datos oficiales españoles y \
europeos. Escribes en español de España, para un lector que puede ser un \
ciudadano curioso o un tribunal académico.

## Tu única regla dura

Los números te llegan calculados. El motor (`engine/spain.py`) ya ha corrido y \
te entrega los resultados en el bloque de hechos. **No calcules nada, no \
estimes nada, no redondees a un número distinto del que recibes y no cites \
ninguna cifra que no esté en los hechos.** Si un dato no está en el bloque de \
hechos, no existe para ti: omítelo. Tu trabajo es elegir las palabras, no las \
magnitudes.

## Qué es el modelo

Un motor macro determinista sobre un corte de datos congelado (el «vintage»). \
Diez palancas mueven una economía calibrada; el resultado es una proyección \
condicional 2026–2050, no una previsión.

La identidad que gobierna la deuda es b(t+1) = b(t)·(1+r−g) − sp: la deuda \
crece con el tipo de interés, baja con el crecimiento nominal y baja con el \
superávit primario.

Constantes de calibración que puedes citar en el mecanismo (son calibraciones \
de la literatura, no estimaciones sobre estos datos):
- multiplicador fiscal MULT = {c.MULT}
- persistencia del nivel de PIB RHO = {c.RHO}
- respuesta al tipo E_R = {c.E_R} pp de PIB por pp
- canal exterior E_EXT = {c.E_EXT}
- precio de importaciones E_PM = {c.E_PM}
- Okun OKUN = {c.OKUN}, pendiente de Phillips KAPPA = {c.KAPPA}
- pass-through de importaciones GAMMA = {c.GAMMA}
- shifters de u*: instituciones A_Z = {c.A_Z}, cuña fiscal A_TAU = {c.A_TAU}, \
productividad A_LAM = {c.A_LAM}
- refinanciación anual de la deuda REFI = {c.REFI}, prima de plazo TERM = {c.TERM}

## Las tres piezas que devuelves

**resumen** — 2 a 4 frases, lenguaje llano, sin coeficientes ni fórmulas. \
Empieza por lo que ha cambiado y sigue por lo que implica. Un lector sin \
formación económica tiene que entenderlo entero.

**mecanismo** — el porqué técnico. Recorre la cadena causal de cada palanca \
movida citando el coeficiente que fija el tamaño de cada paso. Explica la \
descomposición: cada palanca por separado y el residuo de interacción. **El \
residuo importa** — el motor no es lineal, las palancas por separado no suman \
el efecto conjunto, y eso hay que decirlo, no esconderlo.

**advertencia** — líneas rojas cruzadas o en banda de aviso, con su ancla \
histórica, y los límites de lectura. Si el escenario cruza una línea que la \
base no cruzaba, eso va primero.

## Estilo

Frases con verbo. Prosa, no listas de viñetas, salvo en la descomposición del \
mecanismo, donde una lista corta se lee mejor. Nada de «es importante señalar», \
«cabe destacar» ni relleno equivalente. Números en formato español: 223,8 y \
1.234. Nunca digas que algo «va a» pasar: el modelo dice lo que pasaría si esas \
palancas se mantuvieran.

Nunca des consejo de inversión, de compra de vivienda ni de voto.

## Lenguaje llano

El lector puede no haber estudiado economía. Todo lo serio —tablas, cifras, \
fórmulas, la cadena causal— se mantiene, pero explicado con palabras corrientes. \
Si usas un término técnico, dilo y explícalo en la misma frase: «el saldo \
primario, es decir, lo que ingresa el Estado menos lo que gasta sin contar los \
intereses».

Nada en inglés sin traducir. Si un término no tiene equivalente asentado, pon \
el español primero y el inglés entre paréntesis una sola vez: «la deriva \
(drift)», «el error escalado medio (MASE)». Nunca al revés, y nunca sueltes \
«drift», «gap», «baseline», «forecast» o «spread» como si fueran españolas: \
deriva, brecha, referencia de partida, previsión, prima de riesgo.

## El cierre coloquial

`coloquial` es lo mismo dicho de otra manera, no un resumen más corto ni un \
adorno. Tono de sobremesa: llano, tranquilo, irónico cuando el dato lo merece. \
Puedes usar la segunda persona. No introduzcas ni una cifra que no esté ya \
arriba, no contradigas nada, y no conviertas la ironía en consejo ni en \
militancia: sigue siendo lo que el modelo implica, contado sin corbata.
"""


@dataclass(frozen=True)
class NarrationResult:
    resumen: str
    mecanismo: str
    advertencia: str
    coloquial: str
    model: str
    cached_input_tokens: int
    input_tokens: int
    output_tokens: int


class NarrationUnavailable(RuntimeError):
    """Raised for every failure path so the caller can fall back cleanly."""


_NUMBER = re.compile(r"(?<![\w])[-+−]?\d+(?:[.,]\d+)*(?![\w])")


def _number_values(token: str) -> set[Decimal]:
    """Accept ES/EN decimal and grouping marks; compare magnitudes only."""
    token = token.replace("−", "-")
    candidates = {token}
    if "," in token and "." in token:
        decimal, grouping = ((",", ".") if token.rfind(",") > token.rfind(".")
                             else (".", ","))
        candidates = {token.replace(grouping, "").replace(decimal, ".")}
    elif "," in token or "." in token:
        sep = "," if "," in token else "."
        candidates = {token.replace(sep, ".")}
        if all(len(part) == 3 for part in token.split(sep)[1:]):
            candidates.add(token.replace(sep, ""))
    out = set()
    for candidate in candidates:
        try:
            out.add(abs(Decimal(candidate)))
        except InvalidOperation:
            continue
    return out


def validate_narration(data: dict, facts: ExplanationFacts) -> None:
    """Reject new numeric magnitudes, allowing 0–4 decimal-place rounding.

    This is an inventory check only: signs, units, associations, written-out
    numbers and causal claims still need semantic/human evaluation. Ambiguous
    decimal separators accept either conventional interpretation. The caller
    falls back to deterministic prose on failure.
    """
    # Required, not exact: the schema gained `coloquial` and an equality check
    # here rejected every well-formed response, silently serving templates.
    # Extra keys the schema permits are not a reason to discard the answer.
    keys = {"resumen", "mecanismo", "advertencia", "coloquial"}
    if not isinstance(data, dict) or not keys <= set(data) or any(
        not isinstance(data[k], str) or not data[k].strip() for k in keys
    ):
        raise NarrationUnavailable("malformed narration fields")

    allowed: set[Decimal] = set()

    def collect(value):
        if isinstance(value, dict):
            for v in value.values():
                collect(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                collect(v)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            number = abs(Decimal(str(value)))
            if number.is_finite():
                allowed.add(number)
                for decimals in range(5):
                    allowed.add(Decimal(str(round(value, decimals))).copy_abs())
        elif isinstance(value, str):
            for token in _NUMBER.findall(value):
                allowed.update(_number_values(token))

    collect(facts.to_dict())
    collect(SYSTEM)
    for block in data.values():
        # Remove ordinal list labels, which are formatting rather than facts.
        block = re.sub(r"(?m)^\s*\d+[.)]\s+", "", block)
        for token in _NUMBER.findall(block):
            if not (_number_values(token) & allowed):
                raise NarrationUnavailable(f"number absent from supplied facts: {token}")


def _facts_block(facts: ExplanationFacts) -> str:
    return json.dumps(facts.to_dict(), ensure_ascii=False, indent=1, sort_keys=True)


def narrate(facts: ExplanationFacts, *, timeout: float = 30.0) -> NarrationResult:
    """Send facts to Claude, return the three narration blocks.

    Raises NarrationUnavailable on any failure — missing SDK, missing key,
    network error, refusal, or a response that isn't the expected shape.
    """
    _load_env_file()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise NarrationUnavailable("ANTHROPIC_API_KEY not set")

    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover - import guard
        raise NarrationUnavailable("anthropic SDK not installed") from exc

    client = anthropic.Anthropic(timeout=timeout, max_retries=1)

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=[{
                "type": "text",
                "text": SYSTEM,
                # Frozen prefix: the facts below change every call, this never
                # does. Cache reads at 0.1x are what make per-interaction
                # narration affordable.
                "cache_control": {"type": "ephemeral"},
            }],
            output_config={
                **({"effort": EFFORT} if EFFORT else {}),
                "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
            },
            messages=[{
                "role": "user",
                "content": ("Explica este escenario. Hechos calculados por el "
                            "motor:\n\n" + _facts_block(facts)),
            }],
        )
    except Exception as exc:  # network, auth, rate limit, bad request
        raise NarrationUnavailable(f"{type(exc).__name__}: {exc}") from exc

    if response.stop_reason in {"refusal", "max_tokens"}:
        raise NarrationUnavailable("model declined or truncated the response")

    text = next((b.text for b in response.content if b.type == "text"), None)
    if not text:
        raise NarrationUnavailable(f"no text block (stop_reason={response.stop_reason})")

    try:
        data = json.loads(text)
        validate_narration(data, facts)
        return NarrationResult(
            resumen=data["resumen"],
            mecanismo=data["mecanismo"],
            advertencia=data["advertencia"],
            coloquial=data.get("coloquial", ""),
            model=response.model,
            cached_input_tokens=getattr(response.usage, "cache_read_input_tokens", 0) or 0,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise NarrationUnavailable(f"malformed response: {exc}") from exc
