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
        return (f"Sin mover ninguna palanca, en {head.year} la deuda pública "
                f"queda en {nf(head.value, head.dec)} {head.unit} según la senda "
                "central del vintage.")

    plural = "s" if len(f.moved) > 1 else ""
    parts = [f"Has movido {len(f.moved)} palanca{plural}: "
             + "; ".join(_lever_phrase(m) for m in f.moved) + "."]

    if head is not None:
        verb = "sube" if head.delta > 0 else "baja" if head.delta < 0 else "no se mueve"
        parts.append(
            f"La deuda pública {verb} de {nf(head.base, head.dec)} a "
            f"{nf(head.value, head.dec)} {head.unit} en {head.year} "
            f"({_signed(head.delta, head.dec)} puntos).")

    others = [o for o in f.outcomes
              if o.key != f.headline_key and abs(o.delta) > 0.05]
    if others:
        bits = [f"{o.label} {_signed(o.delta, o.dec)} {o.unit} en {o.year}"
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
        lines.append(
            f"Descomposición del movimiento de la deuda en {f.headline_year} "
            f"({_signed(f.joint_delta, 1)} %PIB en total), volviendo a correr el "
            "motor con una sola palanca cada vez:")
        for ct in f.contributions:
            lines.append(
                f"  · {ct.lever_name}: {_signed(ct.delta, 1)} %PIB por sí sola "
                f"({nf(ct.share * 100, 0)} % del movimiento bruto).")
        if abs(f.interaction) > 0.05:
            lines.append(
                f"  · Interacción entre palancas: {_signed(f.interaction, 1)} %PIB. "
                "El motor no es lineal, así que las palancas por separado no suman "
                "el efecto conjunto — esta diferencia es real, no un error de "
                "redondeo.")

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


def fallback_narration(facts: ExplanationFacts) -> dict[str, str]:
    """Deterministic narration. Same keys as the LLM path."""
    return {
        "resumen": _resumen(facts),
        "mecanismo": _mecanismo(facts),
        "advertencia": _advertencia(facts),
    }
