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


def ask(question: str, collection: str = "libros", *, top_k: int | None = None,
        scenario_facts: dict | None = None, max_tokens: int = 900,
        timeout: float = 60.0) -> Answer:
    """Retrieve, then answer with citations. Never answers ungrounded."""
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
