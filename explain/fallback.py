"""Deterministic Spanish narration over the same facts the LLM receives.

This is not a degraded mode to apologise for. It runs whenever `narrate` cannot
(no API key, no network, an API error) and it is what the offline mock build and
the Playwright smoke test assert against — so the app is never one failed HTTP
call away from having nothing to say.

Same output shape as `narrate`: resumen / mecanismo / advertencia.
"""
from __future__ import annotations

from explain.facts import ExplanationFacts

_ES_DEC = {0: "{:,.0f}", 1: "{:,.1f}", 2: "{:,.2f}"}
#: Python formats 1,234.5 anglo-style; Spanish wants 1.234,5. maketrans swaps
#: both separators simultaneously, so no intermediate sentinel is needed.
_SWAP = str.maketrans({",": ".", ".": ","})


def nf(value: float, dec: int = 1) -> str:
    """Spanish number formatting: thousands with '.', decimals with ','."""
    return _ES_DEC.get(dec, "{:,.1f}").format(value).translate(_SWAP)


def _signed(value: float, dec: int = 1) -> str:
    sign = "+" if value > 0 else "−" if value < 0 else ""
    return sign + nf(abs(value), dec)


def _sp(unit: str) -> str:
    """A leading space only when there is a unit. Several series are indices
    and carry none; without this they print a double space before «en»."""
    return f" {unit}" if unit else ""


def _lever_phrase(m) -> str:
    return (f"{m.name} de {nf(m.base, m.dec)} a {nf(m.value, m.dec)} {m.unit} "
            f"({_signed(m.delta, m.dec)})")


def _resumen(f: ExplanationFacts) -> str:
    if f.fresh:
        return ("Estás viendo la línea base del vintage "
                f"{f.vintage}: todas las palancas en su valor observado y el "
                "horizonte en el primer año. Nada está proyectado todavía — "
                "mueve una palanca para abrir un escenario.")

    head = next((o for o in f.outcomes if o.key == f.headline_key), None)

    if not f.moved:
        if head is None:
            return "Escenario sin cambios respecto a la línea base."
        return (f"Sin mover ninguna palanca, en {head.year} {head.label.lower()} "
                f"queda en {nf(head.value, head.dec)} {head.unit} según la senda "
                "central del vintage.")

    plural = "s" if len(f.moved) > 1 else ""
    parts = [f"Has movido {len(f.moved)} palanca{plural}: "
             + "; ".join(_lever_phrase(m) for m in f.moved) + "."]

    if head is not None:
        verb = "sube" if head.delta > 0 else "baja" if head.delta < 0 else "no se mueve"
        # head.label, not a fixed string: the headline is whichever series the
        # caller asked about, and naming it «deuda pública» while printing
        # another series' values is the worst kind of wrong — plausible.
        # «puntos» was fixed for the same reason it should not have been: it is
        # the right word for a series measured in percent and nonsense for one
        # measured in euros — a house price does not fall by 104.420 puntos.
        delta_unit = "puntos" if head.unit.startswith("%") else head.unit
        delta = f"{_signed(head.delta, head.dec)} {delta_unit}".strip()
        parts.append(
            f"{head.label} {verb} de {nf(head.base, head.dec)} a "
            f"{nf(head.value, head.dec)}{_sp(head.unit)} en {head.year} "
            f"({delta}).")

    others = [o for o in f.outcomes
              if o.key != f.headline_key and abs(o.delta) > 0.05]
    if others:
        bits = [f"{o.label} {_signed(o.delta, o.dec)}{_sp(o.unit)} en {o.year}"
                for o in others[:3]]
        parts.append("En el mismo escenario: " + "; ".join(bits) + ".")

    return " ".join(parts)


def _mecanismo(f: ExplanationFacts) -> str:
    if not f.moved:
        return ("Sin palancas movidas no hay mecanismo que trazar: las series "
                "son las del vintage congelado.")

    lines: list[str] = []
    for m in f.moved:
        steps = f.mechanism.get(m.id, [])
        if not steps:
            continue
        chain = "; ".join(
            s["step"] + (f" ({s['const']} = {nf(s['value'], 2)})"
                         if s.get("value") is not None else "")
            for s in steps)
        lines.append(f"{m.symbol} · {m.name} → {chain}.")

    if f.contributions:
        hd = next((o for o in f.outcomes if o.key == f.headline_key), None)
        what = hd.label.lower() if hd else "la serie"
        unit = hd.unit if hd else ""
        lines.append(
            f"Descomposición del movimiento de {what} en {f.headline_year} "
            f"({_signed(f.joint_delta, 1)}{_sp(unit)} en total), volviendo a correr el "
            "motor con una sola palanca cada vez:")
        for ct in f.contributions:
            lines.append(
                f"  · {ct.lever_name}: {_signed(ct.delta, 1)}{_sp(unit)} por sí sola "
                f"({nf(ct.share * 100, 0)} % del movimiento bruto).")
        if abs(f.interaction) > 0.05:
            lines.append(
                f"  · Interacción entre palancas: {_signed(f.interaction, 1)}{_sp(unit)}. "
                "El motor no es lineal, así que las palancas por separado no suman "
                "el efecto conjunto — esta diferencia es real, no un error de "
                "redondeo.")

    # Only where it is the mechanism. Under «¿qué parte de mi sueldo se irá en
    # la hipoteca?» the debt identity is true and irrelevant, and a paragraph
    # of irrelevant truth is how an explanation stops being read.
    if f.headline_key in {"b", "int", "saldo", "pb", "ief", "bono", "spread"}:
        lines.append("La identidad que cierra el círculo es b(t+1) = b(t)·(1+r−g) − sp: "
                     "la deuda crece con el tipo, baja con el crecimiento y con el "
                     "superávit primario.")
    return "\n".join(lines)


def _advertencia(f: ExplanationFacts) -> str:
    nuevas = [r for r in f.redlines
              if r.status == "crossed" and r.base_status != "crossed"]
    cruzadas = [r for r in f.redlines if r.status == "crossed"]
    cerca = [r for r in f.redlines if r.status == "near"]

    parts: list[str] = []
    if nuevas:
        bits = [f"«{r.label}» (valor {nf(r.value, 1)}"
                + (f", primera vez en {r.first_year}" if r.first_year else "") + ")"
                for r in nuevas]
        parts.append("Este escenario cruza líneas rojas que la base no cruzaba: "
                     + "; ".join(bits) + ".")
    elif cruzadas:
        parts.append("Las líneas rojas cruzadas son las mismas que en la línea base: "
                     + "; ".join(f"«{r.label}»" for r in cruzadas) + ".")
    if cerca:
        parts.append("En la banda de aviso (10 % del umbral): "
                     + "; ".join(f"«{r.label}»" for r in cerca) + ".")

    parts.append(f"Proyección condicional sobre el vintage {f.vintage} con el motor "
                 f"v{f.engine_version}. No es una previsión ni una recomendación de "
                 "compra, venta o voto: es lo que el modelo implica si esas palancas "
                 "se mantuvieran en esos valores.")
    return " ".join(parts)


def _coloquial(f: ExplanationFacts) -> str:
    """The same thing without a tie on, from templates.

    Deliberately flatter than what the model writes: a template cannot be funny
    on purpose and a template trying to be funny is worse than one that is not.
    What it can do is drop the register and name the one number that matters.
    """
    if f.fresh:
        return ("Ahora mismo no estás viendo ninguna previsión: son los datos tal "
                "como estaban. Mueve una palanca y empieza lo interesante.")

    head = next((o for o in f.outcomes if o.key == f.headline_key), None)
    if head is None:
        return ("Has tocado algo, pero no lo suficiente como para que se note en "
                "esta pantalla.")

    if not f.moved:
        return (f"Sin tocar nada, en {head.year} esto se queda en "
                f"{nf(head.value, head.dec)} {head.unit}. Ese es el punto de partida.")

    moved_at_all = abs(head.delta) > 1e-9
    if head.sides:
        # For these the sign of the welfare change is a property of the reader,
        # not of the series, so the sentence names both sides instead of
        # picking one. Cheaper than asking who is reading, and more honest than
        # guessing: a cheaper house is good news to a buyer and bad news to an
        # owner, and the engine has no opinion on which of them asked.
        gains, loses = head.sides if head.delta > 0 else head.sides[::-1]
        verdict = f"lo cual es buena noticia para {gains} y mala para {loses}"
    else:
        worse = head.up_is_bad if head.delta > 0 else (not head.up_is_bad)
        verdict = ("y eso, para quien lo vive, es peor" if head.delta and worse
                   else "y eso, para quien lo vive, es mejor")
    lever = (f"«{f.moved[0].name}»" if len(f.moved) == 1
             else f"{len(f.moved)} palancas a la vez")
    # The label is quoted rather than lower-cased into the sentence: its gender
    # varies by series ("el esfuerzo", "la deuda") and a template cannot know
    # which article to put in front of it.
    # An empty unit (an index) must not leave a double space, and a series that
    # did not move needs "se queda en", not "no se mueve hasta".
    amount = f"{nf(head.value, head.dec)} {head.unit}".strip()
    if not moved_at_all:
        return (f"Resumiendo: mueves {lever} y «{head.label}» se queda en "
                f"{amount} en {head.year}: esa palanca no le llega. "
                "Y con la letra pequeña de siempre: esto es lo que saldría si "
                "esos valores se mantuvieran, no una bola de cristal.")
    direction = "sube" if head.delta > 0 else "baja"
    return (f"Resumiendo: mueves {lever} y «{head.label}» {direction} hasta "
            f"{amount} en {head.year} — {_signed(head.delta, head.dec)} frente "
            f"a no tocar nada, {verdict}. "
            "Con la letra pequeña de siempre: esto es lo que saldría si esos "
            "valores se mantuvieran, no una bola de cristal.")


def fallback_narration(facts: ExplanationFacts) -> dict[str, str]:
    """Deterministic narration. Same keys as the LLM path."""
    return {
        "resumen": _resumen(facts),
        "mecanismo": _mecanismo(facts),
        "advertencia": _advertencia(facts),
        "coloquial": _coloquial(facts),
    }
