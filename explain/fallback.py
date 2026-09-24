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


def _delta_unit(unit: str) -> str:
    """The unit of a *change* in a series, which is not always the series' own.

    A percentage moves in points: paro juvenil going from 23,4 % to 21,5 % is
    −1,9 puntos, and «−1,9 %» reads as a relative fall of 1,9 %. A share of
    GDP moves in points of GDP. Everything else keeps its unit — a house price
    moves in euros, not in puntos (the bug test_explain pins)."""
    if unit == "%PIB":
        return "puntos de PIB"
    return "puntos" if unit.startswith("%") else unit


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
        delta = f"{_signed(head.delta, head.dec)}{_sp(_delta_unit(head.unit))}"
        parts.append(
            f"{head.label} {verb} de {nf(head.base, head.dec)} a "
            f"{nf(head.value, head.dec)}{_sp(head.unit)} en {head.year} "
            f"({delta}).")

    others = [o for o in f.outcomes
              if o.key != f.headline_key and abs(o.delta) > 0.05]
    if others:
        bits = [f"{o.label} {_signed(o.delta, o.dec)}{_sp(_delta_unit(o.unit))} en {o.year}"
                for o in others[:3]]
        parts.append("En el mismo escenario: " + "; ".join(bits) + ".")

    return " ".join(parts)


#: What each lever does inside the engine, in words a reader without economics
#: can follow. The same chains as facts.MECHANISM — whose constants go to the
#: technical line at the end instead of sitting inside every sentence — and
#: checked against engine/spain.py: a higher Euríbor lowers house-price growth
#: with a fading effect and raises the mortgage payment (r + DIFF).
PLAIN_LEVER: dict[str, str] = {
    "r": ("cambia lo que paga el Estado al renovar su deuda, el interés del bono "
          "a 10 años, la inversión y el consumo, la cuota de la hipoteca y, los "
          "primeros años, cuánto sube el precio de la vivienda"),
    "prima": ("se suma al interés del bono a 10 años y, a medida que el Estado "
              "renueva su deuda, a lo que paga en intereses"),
    "sp": ("resta o suma directamente a la deuda, y además frena o empuja la "
           "economía a través del gasto y los impuestos; con menos actividad las "
           "pensiones pesan más en el PIB, así que parte del ajuste se pierde por ahí"),
    "lam": ("cambia cuánto puede crecer la economía y el paro que tiene de fondo: "
            "con más productividad, los sueldos pueden subir sin que suban los "
            "precios; y como las pensiones suben con los precios y no con la "
            "economía, pesan menos si la economía crece más, lo que mejora el "
            "saldo del Estado (con menos productividad, al revés)"),
    "pm": ("pasa a la inflación durante unos años, cada vez menos, y resta "
           "actividad"),
    "tau": ("son los impuestos y cotizaciones que separan lo que paga la empresa "
            "de lo que cobra el trabajador, y cambian el paro que la economía "
            "tiene de fondo"),
    "z": ("son los convenios, las indemnizaciones y el salario mínimo; cambian el "
          "paro que la economía tiene de fondo, y en el modelo son lo que más "
          "lo mueve"),
    "ext": ("se traslada a la actividad de aquí a través de las exportaciones; y "
            "si la economía crece más, las pensiones pesan menos en el PIB"),
    "dem": ("cambia cuántos mayores hay por cada persona en edad de trabajar, y con "
            "ello el gasto en pensiones"),
    "idx": ("cambia cuánto suben cada año pensiones y nóminas públicas respecto a "
            "la inflación: su poder de compra y lo que le cuestan al Estado"),
}


def _y(names: list[str]) -> str:
    """«A», «A y B», «A, B y C»."""
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " y " + names[-1]


def _mecanismo(f: ExplanationFacts) -> str:
    if not f.moved:
        return ("Sin palancas movidas no hay mecanismo que trazar: las series "
                "son las del vintage congelado.")

    hd = next((o for o in f.outcomes if o.key == f.headline_key), None)
    what = hd.label.lower() if hd else "la serie"
    # Every figure in the decomposition is a change, so all of it is in the
    # change's unit: «−43,7 puntos de PIB», not «−43,7 %PIB».
    unit = _delta_unit(hd.unit) if hd else ""

    # A lever that does not reach this figure is named once, not explained:
    # six paragraphs about levers that move it by +0,0 is how the one that
    # matters got lost.
    by_id = {m.id: m for m in f.moved}
    if f.contributions:
        ranked = sorted(f.contributions, key=lambda ct: abs(ct.delta), reverse=True)
        movers = [ct for ct in ranked if abs(ct.delta) >= 0.05]
        idle = [ct.lever_name for ct in ranked if abs(ct.delta) < 0.05]
        explained = [by_id[ct.lever_id] for ct in movers if ct.lever_id in by_id]
    else:
        movers, idle, explained = [], [], list(f.moved)

    lines: list[str] = []
    described = [m for m in explained if m.id in PLAIN_LEVER]
    if described:
        lines.append("Qué hace en el modelo cada palanca que mueve esta cifra:")
        for m in described:
            lines.append(f"  · {m.name}: {PLAIN_LEVER[m.id]}.")

    if f.contributions and not movers:
        lines.append(f"Ninguna de las palancas que has movido cambia {what} en "
                     f"{f.headline_year}: {_y(idle)}.")
    elif f.contributions:
        lines.append(
            f"Cuánto pesa cada una en el cambio de {what} en {f.headline_year} "
            f"({_signed(f.joint_delta, 1)}{_sp(unit)} en total). Para saberlo, el "
            "modelo se vuelve a calcular moviendo una sola palanca cada vez:")
        for ct in movers:
            lines.append(
                f"  · {ct.lever_name}: {_signed(ct.delta, 1)}{_sp(unit)} "
                f"({nf(ct.share * 100, 0)} % del cambio).")
        if idle:
            lines.append(f"  · No mueven esta cifra, o casi nada: {_y(idle)}.")
        if abs(f.interaction) > 0.05:
            lines.append(
                f"  · Interacción entre palancas: {_signed(f.interaction, 1)}{_sp(unit)}. "
                "El modelo no es lineal, así que las palancas por separado no suman "
                "el efecto conjunto: esta diferencia es real, no un error de "
                "redondeo.")

    # Only where it is the mechanism. Under «¿qué parte de mi sueldo se irá en
    # la hipoteca?» the debt identity is true and irrelevant, and a paragraph
    # of irrelevant truth is how an explanation stops being read.
    debt = f.headline_key in {"b", "int", "saldo", "pb", "ief", "bono", "spread"}
    if debt:
        lines.append("La cuenta de la deuda: la de este año es la del anterior, más "
                     "los intereses, menos el efecto de que la economía crezca, "
                     "menos el superávit (o más el déficit) sin contar intereses.")

    # The constants stay — a reviewer checks them — but on one line of their
    # own, labelled, which the page folds into «Detalle técnico».
    consts: dict[str, float] = {}
    notes: dict[str, str] = {}
    for m in explained:
        for s in f.mechanism.get(m.id, []):
            if s.get("value") is not None:
                consts.setdefault(s["const"], s["value"])
                notes.setdefault(s["const"], s.get("note", ""))
    # The IPV constants carry their note: without it «E_IPV_R = 2,60» is an
    # acronym inside an acronym for anyone who has not read the README.
    tech = [f"{k} = {nf(v, 2)}" + (f", {notes[k]}" if "IPV" in k and notes.get(k) else "")
            for k, v in consts.items()]
    if debt:
        tech.append("b(t+1) = b(t)·(1+r−g) − sp")
    if tech:
        lines.append("Detalle técnico: " + " · ".join(tech) + ".")
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
            f"{amount} en {head.year} — {_signed(head.delta, head.dec)}"
            f"{_sp(_delta_unit(head.unit))} frente "
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
