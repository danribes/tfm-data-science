"""Answer generation over retrieved passages, with mandatory citation.

The model is given passages and told to answer *only* from them. If retrieval
comes back empty, it says the corpus does not cover the question rather than
answering from its own parametric memory — an uncited answer from a RAG is
worse than no answer, because it looks sourced and is not.

Provider handling follows the old `app/rag_assistant.py`: a list of
OpenAI-compatible endpoints tried in order, so a dead key or an exhausted quota
degrades to the next provider instead of failing the request. Keys stay
server-side.
"""
from __future__ import annotations

import re

import os
from dataclasses import dataclass
from typing import Sequence

from rag import config, retrieve

#: Tried in order. Each is OpenAI-compatible (`/chat/completions`), which is why
#: one client shape covers all of them. Anthropic is deliberately last: the
#: account currently has no credit, and there is no reason to spend a round trip
#: discovering that on every request.
PROVIDERS = [
    {"name": "gemini", "key_env": "GEMINI_API_KEY", "model": "gemini-2.5-flash",
     "base": "https://generativelanguage.googleapis.com/v1beta/openai"},
    {"name": "glm", "key_env": "GLM_API_KEY", "model": "glm-4-plus",
     "base": "https://open.bigmodel.cn/api/paas/v4"},
    {"name": "kimi", "key_env": "KIMI_API_KEY", "model": "moonshot-v1-8k",
     "base": "https://api.moonshot.cn/v1"},
    {"name": "openai", "key_env": "OPENAI_API_KEY", "model": "gpt-4o-mini",
     "base": "https://api.openai.com/v1"},
]

SYSTEM = """\
Eres el bibliotecario de «España en escenarios». Respondes preguntas de \
economía apoyándote EXCLUSIVAMENTE en los pasajes que se te entregan.

Reglas duras:
1. No uses conocimiento propio. Si los pasajes no contienen la respuesta, dilo \
   con claridad: «el corpus no cubre esto». Nunca rellenes el hueco.
2. Cita siempre. Cada afirmación lleva su fuente entre corchetes, con el número \
   del pasaje: [1], [2]. Sin cita, la frase no se escribe.
3. Distingue la autoridad de la fuente. Un manual académico y una transcripción \
   de un canal de YouTube no valen lo mismo: si citas material marcado como \
   «opinion», dilo explícitamente («según el canal…, que es una opinión, no un \
   manual»).
4. Si los pasajes se contradicen, muéstralo en vez de elegir uno en silencio.

Estilo: español de España, frases con verbo, prosa y no listas de viñetas salvo \
que la pregunta pida una enumeración. Nada de «es importante señalar». No des \
consejo de inversión, de compra de vivienda ni de voto.
"""


@dataclass(frozen=True)
class Answer:
    text: str
    passages: list[dict]
    provider: str | None
    model: str | None
    grounded: bool          # False when nothing was retrieved
    error: str | None = None


def _format_passages(passages: Sequence) -> str:
    out = []
    for i, p in enumerate(passages, 1):
        auth = config.COLLECTIONS[p.collection]["authority"]
        out.append(f"[{i}] ({auth}) {p.cite()}\n{p.text}")
    return "\n\n---\n\n".join(out)


def _call(provider: dict, messages: list[dict], max_tokens: int,
          timeout: float) -> str:
    import requests

    key = os.environ.get(provider["key_env"], "")
    if not key:
        raise RuntimeError(f"{provider['key_env']} no configurada")
    r = requests.post(
        f"{provider['base']}/chat/completions",
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"},
        json={"model": provider["model"], "messages": messages,
              "max_tokens": max_tokens, "temperature": 0.2},
        timeout=timeout,
    )
    r.raise_for_status()
    return (r.json()["choices"][0]["message"].get("content") or "").strip()


def _call_stream(provider: dict, messages: list[dict], max_tokens: int,
                 timeout: float):
    """Yield text deltas from an OpenAI-compatible SSE stream."""
    import json as _json

    import requests

    key = os.environ.get(provider["key_env"], "")
    if not key:
        raise RuntimeError(f"{provider['key_env']} no configurada")
    with requests.post(
        f"{provider['base']}/chat/completions",
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"},
        json={"model": provider["model"], "messages": messages,
              "max_tokens": max_tokens, "temperature": 0.2, "stream": True},
        timeout=timeout, stream=True,
    ) as r:
        r.raise_for_status()
        # requests falls back to ISO-8859-1 for text/* responses without an
        # explicit charset (an HTTP/1.1 legacy rule), which turned every
        # accented character in the Spanish answers into mojibake — "pública"
        # arrived as "pÃºblica". The payload is always UTF-8 JSON.
        r.encoding = "utf-8"
        for raw in r.iter_lines(decode_unicode=True):
            if not raw:
                continue
            line = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                return
            try:
                delta = _json.loads(payload)["choices"][0].get("delta", {})
            except (ValueError, KeyError, IndexError):
                continue
            piece = delta.get("content")
            if piece:
                yield piece


def stream(question: str, collection: str = "libros", *,
           top_k: int | None = None, scenario_facts: dict | None = None,
           max_tokens: int = 900, timeout: float = 60.0):
    """Generator of events for SSE: passages first, then answer deltas.

    Retrieval finishes in well under a second while generation takes several,
    so the passages are emitted immediately — the reader has the evidence in
    hand before the first word of prose arrives, and the evidence is the part
    that has to be right.

    Yields (event_name, payload) tuples; the endpoint serialises them.
    """
    refusal = refusal_for(question)
    if refusal:
        # No passages at all: showing sources beside a refusal would read as
        # evidence for advice that was just declined.
        yield "passages", {"passages": [], "grounded": False}
        yield "done", {"answer": refusal, "grounded": False,
                       "provider": None, "model": None}
        return

    passages = retrieve.search(question, collection, top_k)
    yield "passages", {"passages": [p.to_dict() for p in passages],
                       "grounded": bool(passages)}

    if not passages:
        yield "done", {"answer": ("El corpus no cubre esta pregunta. Prueba a "
                                  "reformularla o a consultar otra colección."),
                       "grounded": False, "provider": None, "model": None}
        return

    user = f"PREGUNTA:\n{question}\n\nPASAJES:\n{_format_passages(passages)}"
    if scenario_facts:
        import json as _json
        user += ("\n\nESCENARIO ACTIVO DEL USUARIO (calculado por el motor, "
                 "no por ti — cítalo tal cual si es pertinente):\n"
                 + _json.dumps(scenario_facts, ensure_ascii=False, indent=1)[:4000])
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": user}]

    last: str | None = None
    for prov in PROVIDERS:
        parts: list[str] = []
        try:
            for piece in _call_stream(prov, messages, max_tokens, timeout):
                parts.append(piece)
                yield "delta", {"text": piece}
        except Exception as exc:
            if parts:
                # Died mid-stream: the client already rendered these words, so
                # finish with what arrived rather than silently restarting on
                # another provider and duplicating text.
                yield "done", {"answer": "".join(parts), "grounded": True,
                               "provider": prov["name"], "model": prov["model"],
                               "error": f"stream interrumpido: {type(exc).__name__}"}
                return
            last = f"{prov['name']}: {type(exc).__name__}"
            continue
        if parts:
            yield "done", {"answer": "".join(parts), "grounded": True,
                           "provider": prov["name"], "model": prov["model"]}
            return
        last = f"{prov['name']}: respuesta vacía"

    yield "done", {"answer": ("No hay proveedor de lenguaje disponible ahora "
                              "mismo. Arriba están los pasajes relevantes."),
                   "grounded": True, "provider": None, "model": None,
                   "error": last}


# ---- guardrail: personal advice is refused, not answered ---------------------

#: The system prompt already tells the model not to give advice. A prompt is a
#: request: it holds until a provider fails over to a weaker model, or a user
#: phrases the question as a hypothetical, or the passages themselves read like
#: a recommendation. The app's own footer promises "no es recomendación de
#: compra, venta o voto" on every page, and a promise printed under a chat that
#: can be talked into a stock tip is worth nothing. So the check runs before
#: retrieval and does not consult a model.
#:
#: Deliberately narrow. It fires on a *personal* decision — first person plus a
#: transaction — and not on the economics. "¿Es mayor el multiplicador en
#: recesión?" and "¿Cómo afecta el Euríbor a las hipotecas?" are the questions
#: this library exists to answer, and a guardrail that swallows them would do
#: more damage than the one it prevents.
_PERSONAL = re.compile(
    r"\b(me|mis|mi|nos|nuestros?|yo)\b|\b(deber[ií]a|debo|compro|vendo|invierto)\b",
    re.IGNORECASE)
_TRANSACTION = re.compile(
    r"\b(compr|vend|invert|invier|hipotec|contrat|amortiz|cartera|"
    r"acciones|fondos?|bolsa|ahorros?|plan de pensiones)", re.IGNORECASE)
_VOTE = re.compile(r"\b(vot(ar|o|e)|partido|elecciones)\b", re.IGNORECASE)
_RECOMMEND = re.compile(r"\b(recomiend|aconsej|qu[eé] hago|dame una cartera)",
                        re.IGNORECASE)

REFUSAL = (
    "No doy consejo de inversión, de compra de vivienda ni de voto — ni aquí ni "
    "en el resto de la aplicación, que es una proyección condicional y no una "
    "recomendación.\n\n"
    "Lo que sí puedo hacer es explicarte el mecanismo con las fuentes del "
    "corpus: qué dice la literatura sobre cómo se transmite un cambio de tipos "
    "a las hipotecas, qué determina el precio de la vivienda a largo plazo, o "
    "cómo se lee un escenario de deuda. Reformula la pregunta en esos términos "
    "y la respondo con citas."
)


def refusal_for(question: str) -> str | None:
    """The refusal text if the question asks for personal advice, else None."""
    if _VOTE.search(question) and (_PERSONAL.search(question)
                                   or _RECOMMEND.search(question)):
        return REFUSAL
    if not _TRANSACTION.search(question):
        return None
    if _PERSONAL.search(question) or _RECOMMEND.search(question):
        return REFUSAL
    return None


def ask(question: str, collection: str = "libros", *, top_k: int | None = None,
        scenario_facts: dict | None = None, max_tokens: int = 900,
        timeout: float = 60.0) -> Answer:
    """Retrieve, then answer with citations. Never answers ungrounded."""
    refusal = refusal_for(question)
    if refusal:
        return Answer(text=refusal, passages=[], provider=None, model=None,
                      grounded=False, error=None)

    passages = retrieve.search(question, collection, top_k)
    if not passages:
        return Answer(
            text=("El corpus no cubre esta pregunta. Prueba a reformularla o a "
                  "consultar otra colección."),
            passages=[], provider=None, model=None, grounded=False,
        )

    user = f"PREGUNTA:\n{question}\n\nPASAJES:\n{_format_passages(passages)}"
    if scenario_facts:
        # The differentiator: the reader's live scenario travels with the
        # question, so the answer can connect textbook theory to the numbers
        # actually on screen.
        import json
        user += ("\n\nESCENARIO ACTIVO DEL USUARIO (calculado por el motor, "
                 "no por ti — cítalo tal cual si es pertinente):\n"
                 + json.dumps(scenario_facts, ensure_ascii=False, indent=1)[:4000])

    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": user}]
    dicts = [p.to_dict() for p in passages]

    last: str | None = None
    for prov in PROVIDERS:
        try:
            text = _call(prov, messages, max_tokens, timeout)
            if text:
                return Answer(text=text, passages=dicts, provider=prov["name"],
                              model=prov["model"], grounded=True)
            last = f"{prov['name']}: respuesta vacía"
        except Exception as exc:
            last = f"{prov['name']}: {type(exc).__name__}"
            continue

    # Every provider failed. Return the passages anyway — they are the valuable
    # part, and the reader can judge them without a generated summary.
    return Answer(
        text=("No hay proveedor de lenguaje disponible ahora mismo. Estos son "
              "los pasajes relevantes del corpus, sin redactar:"),
        passages=dicts, provider=None, model=None, grounded=True, error=last,
    )
