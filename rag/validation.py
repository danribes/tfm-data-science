"""Structural checks on generated text, not a test of factual entailment.

Valid references establish that a source exists; they do not establish that it
supports a claim. Semantic fidelity still needs independent evaluation.
"""
from __future__ import annotations

import re
import unicodedata


_CITE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")
_REFUSALS = ("no cubre", "no cubro", "no aparece en el corpus",
             "no contiene informacion", "no contienen informacion",
             "no contienen la respuesta", "no hay informacion",
             "no dispongo de informacion")

CORPUS_REFUSAL = (
    "El corpus recuperado no cubre esta pregunta. Prueba a reformularla "
    "o a consultar otra colección."
)


def is_refusal(text: str) -> bool:
    """Heuristic used for abstention accounting; not a semantic verdict."""
    folded = unicodedata.normalize("NFKD", text.lower())
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    return any(phrase in folded for phrase in _REFUSALS)


def citation_references(text: str) -> list[int]:
    return [int(ref.strip()) for group in _CITE.findall(text)
            for ref in group.split(",")]


def checked_answer(text: str, n_passages: int) -> str:
    """Require references within the supplied context, or a fixed abstention.

An uncited provider refusal is replaced in full, so a disclaimer followed by
unsupported prose cannot bypass the reference check. Per-claim support and
coverage are not established here.
    """
    for bracket in re.findall(r"\[[^\]\n]*\]", text):
        if re.search(r"\d", bracket) and not _CITE.fullmatch(bracket):
            raise ValueError("referencia numérica mal formada")
    refs = citation_references(text)
    if not refs:
        if is_refusal(text):
            return CORPUS_REFUSAL
        raise ValueError("respuesta sin referencias a los pasajes")
    invalid = sorted({ref for ref in refs if not 1 <= ref <= n_passages})
    if invalid:
        raise ValueError(f"referencias fuera de los pasajes: {invalid}")
    return text
