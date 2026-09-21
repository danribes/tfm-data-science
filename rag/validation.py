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


def checked_answer(text: str, n_passages: int, *,
                   context_only: bool = False) -> str:
    """Require references within the supplied context, or a fixed abstention.

An uncited provider refusal is replaced in full, so a disclaimer followed by
unsupported prose cannot bypass the reference check. Per-claim support and
coverage are not established here.

`context_only` es el caso en que no había NADA que citar: la pregunta se
respondió con documentación del propio trabajo, que por decisión de diseño no
lleva número y por tanto no puede referenciarse. Exigir una cita ahí no
protegía nada —no existía ninguna cita posible— y tiraba a la basura una
respuesta correcta, que es como se descubrió.

Lo que sigue protegiendo: un corchete numérico mal formado sigue siendo un
error, y como `n_passages` vale 0 en ese modo, CUALQUIER referencia numérica
cae fuera del rango y también lo es. Es decir, en modo contexto la respuesta
sólo se acepta si no cita nada en absoluto. Lo que se pierde es la garantía de
que cada frase apunte a un pasaje; queda dicho aquí y en la interfaz, que
muestra esos pasajes bajo su propio epígrafe.
    """
    for bracket in re.findall(r"\[[^\]\n]*\]", text):
        if re.search(r"\d", bracket) and not _CITE.fullmatch(bracket):
            raise ValueError("referencia numérica mal formada")
    if context_only:
        # El modelo cita aunque se le diga que no. Rechazar la respuesta entera
        # por un corchete de más era tirar a la basura una explicación correcta
        # —así fallaban en producción todas las preguntas sobre el método—, y
        # dejar el corchete sería peor: apuntaría a un pasaje que no existe,
        # porque en este modo no hay ninguno numerado.
        #
        # Se quita la referencia y se conserva la prosa. Es una intervención
        # menor que la que ya hacía esta función, que sustituye respuestas
        # enteras; y la interfaz dice, al lado, que la respuesta se apoya en
        # documentación del propio trabajo y no cita fuentes.
        if is_refusal(text):
            return CORPUS_REFUSAL
        limpio = re.sub(r"\s*" + _CITE.pattern, "", text)
        return re.sub(r"\s+([.,;:])", r"\1", limpio).strip()

    refs = citation_references(text)
    if not refs:
        if is_refusal(text):
            return CORPUS_REFUSAL
        raise ValueError("respuesta sin referencias a los pasajes")
    invalid = sorted({ref for ref in refs if not 1 <= ref <= n_passages})
    if invalid:
        raise ValueError(f"referencias fuera de los pasajes: {invalid}")
    return text
