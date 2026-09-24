"""What changed, what it did, and which lever is responsible for how much.

Everything here is computed from `engine.spain`. Nothing is written by hand and
nothing is estimated — the contribution decomposition re-runs the engine one
lever at a time, which is cheap (25 iterations per run) and exact for the
question it answers: "what would this scenario look like if only this lever had
moved?"

The engine is non-linear, so those single-lever deltas do not sum to the joint
delta. The gap is reported as `interaction`, never hidden by normalising the
shares to 100 % — the residual is a real property of the model and a reader who
is shown a tidy pie chart of a non-additive decomposition has been misled.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from engine import constants as c
from engine.levers import LEVER_SPECS, Levers
from engine.redlines import evaluate_redlines
from engine.spain import Y0, Y1, baseline, run_scenario

#: The series the explanation leads with, and how to render it. `up_is_bad`
#: matches the frontend's UP_IS_BAD set so prose and colour never disagree.
HEADLINES: list[dict] = [
    {"key": "b", "label": "Deuda pública", "unit": "%PIB", "dec": 1,
     "up_is_bad": True, "at_end": True},
    {"key": "saldo", "label": "Saldo público", "unit": "%PIB", "dec": 1,
     "up_is_bad": False, "at_end": False},
    {"key": "u", "label": "Paro", "unit": "%", "dec": 1,
     "up_is_bad": True, "at_end": False},
    {"key": "pi", "label": "IPCA", "unit": "%", "dec": 1,
     "up_is_bad": True, "at_end": False},
    {"key": "esf", "label": "Esfuerzo de vivienda", "unit": "%", "dec": 1,
     "up_is_bad": True, "at_end": False},
]

#: Series whose welfare sign is not a property of the series but of who is
#: reading it, as (who gains when it rises, who loses when it rises).
#:
#: `up_is_bad` is one global bit, and for these it was answering a question it
#: cannot answer. Persona 03 is «quien quiere comprar vivienda», and it was
#: shown that a falling house price «es peor» while a falling mortgage payment
#: «es mejor» — the owner's view and the buyer's view, one sentence apart, to
#: the same reader. Naming both sides is the honest form: the engine computes
#: the number, and it is not the engine's business whose side the reader is on.
SIDES: dict[str, tuple[str, str]] = {
    "precio": ("quien ya tiene piso", "quien quiere comprar"),
    "ipv": ("quien ya tiene piso", "quien quiere comprar"),
    "salario": ("quien cobra un sueldo", "quien paga nóminas"),
    "salmes": ("quien cobra un sueldo", "quien paga nóminas"),
    "wrealIdx": ("quien cobra un sueldo", "quien paga nóminas"),
    "pens": ("quien cobra una pensión", "quien la paga con sus impuestos"),
}

#: The transmission chain each lever travels, with the engine constant that
#: sets the size of each step. Sourced from engine/constants.py at import time
#: so a recalibration can never leave the prose describing the old coefficients.
MECHANISM: dict[str, list[dict]] = {
    "r": [
        {"step": "coste de refinanciación de la deuda viva",
         "const": "REFI", "value": c.REFI,
         "note": f"cada año se refinancia el {c.REFI:.0%} de la deuda"},
        {"step": "prima de plazo sobre el Euríbor",
         "const": "TERM", "value": c.TERM, "note": "bono 10A = r + TERM + prima/100"},
        {"step": "inversión y consumo (nivel de PIB)",
         "const": "E_R", "value": c.E_R,
         "note": "pp de PIB por cada pp de tipo"},
        {"step": "precio de la vivienda",
         "const": "E_IPV_R", "value": c.E_IPV_R, "note": "respuesta del IPV al tipo"},
        {"step": "peso de las pensiones en el PIB (saldo primario)",
         "const": "—", "value": None,
         "note": "un tipo más alto frena el crecimiento y las pensiones pesan algo más en el PIB; el efecto es pequeño"},
    ],
    "prima": [
        {"step": "cupón exigido al bono a 10 años",
         "const": "TERM", "value": c.TERM, "note": "la prima entra en pb sobre el bono"},
        {"step": "carga de intereses sobre el saldo público",
         "const": "REFI", "value": c.REFI, "note": "vía refinanciación anual"},
    ],
    "sp": [
        {"step": "saldo primario (efecto directo en la identidad de deuda)",
         "const": "—", "value": None, "note": "b(t+1) = b(t)·(1+r−g) − sp"},
        {"step": "demanda agregada (multiplicador fiscal)",
         "const": "MULT", "value": c.MULT, "note": "multiplicador fiscal CORE U3"},
        {"step": "peso de las pensiones en el PIB (saldo primario)",
         "const": "—", "value": None,
         "note": "consolidar frena el crecimiento: las pensiones pesan más en el PIB y el saldo primario devuelve parte del ajuste"},
    ],
    "lam": [
        {"step": "desplaza la curva PS (paro estructural)",
         "const": "A_LAM", "value": c.A_LAM, "note": "productividad sobre u*"},
        {"step": "crecimiento potencial",
         "const": "MULT", "value": c.MULT, "note": "vía nivel de PIB"},
        {"step": "peso de las pensiones en el PIB (saldo primario)",
         "const": "—", "value": None,
         "note": "las pensiones siguen al IPC y no al PIB: crecer más que la base las abarata en proporción al PIB y el ahorro llega al saldo primario; crecer menos, al revés"},
    ],
    "pm": [
        {"step": "inflación importada (pass-through a HICP)",
         "const": "GAMMA", "value": c.GAMMA, "note": "episodio 2021-23"},
        {"step": "nivel de PIB (shock de términos de intercambio)",
         "const": "E_PM", "value": c.E_PM, "note": "pp de PIB por 1 % de precio"},
        {"step": "decaimiento del término Phillips de importaciones",
         "const": "PM_DECAY", "value": c.PM_DECAY, "note": "decaimiento geométrico"},
    ],
    "tau": [
        {"step": "desplaza la curva WS (cuña laboral)",
         "const": "A_TAU", "value": c.A_TAU, "note": "cuña fiscal sobre u*"},
    ],
    "z": [
        {"step": "desplaza la curva WS (instituciones laborales)",
         "const": "A_Z", "value": c.A_Z, "note": "el mayor de los tres shifters de u*"},
    ],
    "ext": [
        {"step": "canal exterior sobre el nivel de PIB",
         "const": "E_EXT", "value": c.E_EXT, "note": "peso de la demanda externa"},
        {"step": "peso de las pensiones en el PIB (saldo primario)",
         "const": "—", "value": None,
         "note": "más demanda externa, más crecimiento: las pensiones pesan menos en el PIB y mejora el saldo primario; menos, al revés"},
    ],
    "dem": [
        {"step": "tasa de dependencia y gasto en pensiones",
         "const": "—", "value": None, "note": "variante de gold_projections.csv"},
    ],
    "idx": [
        {"step": "revalorización de pensiones y nóminas sobre el IPC",
         "const": "THETA", "value": c.THETA, "note": "inercia de expectativas"},
    ],
}


#: Label, unit and polarity for every series a persona question can ask about.
#:
#: HEADLINES is the fixed set of five outcomes each narration reports. This is
#: the wider vocabulary: the answer panel asks /explain about whichever series
#: its question resolves to, and twenty-two of those are not among the five.
#: Without an entry here the narration described debt, deficit, unemployment,
#: inflation and housing effort whatever had been asked — a pensions question
#: answered about the deficit, and the colloquial line claimed nothing had
#: moved. Units and decimals mirror the frontend's SERIES_FORMAT so prose and
#: tiles cannot disagree.
SERIES_META: dict[str, dict] = {
    "arop": {"label": "Pobreza infantil (menores de 16)", "unit": "%", "dec": 1, "up_is_bad": True},
    "auton": {"label": "Peso del autoempleo", "unit": "%", "dec": 1, "up_is_bad": False},
    "bono": {"label": "Rendimiento del bono a 10 años", "unit": "%", "dec": 2, "up_is_bad": True},
    "cuota": {"label": "Cuota hipotecaria mensual", "unit": "€/mes", "dec": 0, "up_is_bad": True},
    "d1": {"label": "Salarios públicos", "unit": "%PIB", "dec": 2, "up_is_bad": False},
    "d3": {"label": "Subvenciones", "unit": "%PIB", "dec": 2, "up_is_bad": False},
    "dep": {"label": "Tasa de dependencia", "unit": "/100", "dec": 1, "up_is_bad": True},
    "edu": {"label": "Gasto público en educación", "unit": "%PIB", "dec": 2, "up_is_bad": False},
    "g": {"label": "Crecimiento del PIB real", "unit": "%", "dec": 1, "up_is_bad": False},
    "int": {"label": "Intereses de la deuda", "unit": "%PIB", "dec": 1, "up_is_bad": True},
    "ipv": {"label": "Crecimiento del precio de la vivienda", "unit": "% a/a", "dec": 1, "up_is_bad": False},
    "nomreal": {"label": "Poder de compra de la nómina", "unit": "", "dec": 1, "up_is_bad": False},
    "p2": {"label": "Consumo intermedio", "unit": "%PIB", "dec": 2, "up_is_bad": False},
    "p51": {"label": "Inversión pública", "unit": "%PIB", "dec": 2, "up_is_bad": False},
    "pens": {"label": "Gasto en pensiones", "unit": "%PIB", "dec": 2, "up_is_bad": True},
    "precio": {"label": "Precio de la vivienda", "unit": "€", "dec": 0, "up_is_bad": False},
    "r": {"label": "Tipo de interés de referencia", "unit": "%", "dec": 2, "up_is_bad": True},
    "salario": {"label": "Salario medio anual", "unit": "€/año", "dec": 0, "up_is_bad": False},
    "salmes": {"label": "Salario medio mensual", "unit": "€/mes", "dec": 0, "up_is_bad": False},
    "sobre": {"label": "Sobrecarga por coste de vivienda", "unit": "%", "dec": 1, "up_is_bad": True},
    "spread": {"label": "Prima de riesgo", "unit": "pb", "dec": 0, "up_is_bad": True},
    "temp": {"label": "Temporalidad", "unit": "%", "dec": 1, "up_is_bad": True},
    "ujuv": {"label": "Paro juvenil", "unit": "%", "dec": 1, "up_is_bad": True},
    "wrealIdx": {"label": "Salario real acumulado", "unit": "", "dec": 1, "up_is_bad": False},
}


@dataclass(frozen=True)
class MovedLever:
    id: str
    name: str
    symbol: str
    unit: str
    base: float
    value: float
    delta: float
    dec: int
    source: str


@dataclass(frozen=True)
class Outcome:
    key: str
    label: str
    unit: str
    year: int
    base: float
    value: float
    delta: float
    dec: int
    up_is_bad: bool
    direction: str  # "mejora" | "empeora" | "sin cambio"
    #: Who gains and who loses when this series rises, for the series where
    #: that depends on the reader. See SIDES.
    sides: tuple[str, str] | None = None


@dataclass(frozen=True)
class Contribution:
    """How much of the headline movement this lever accounts for on its own."""
    lever_id: str
    lever_name: str
    delta: float
    share: float  # of the sum of |single-lever deltas|, not of the joint delta
    #: The same share as a percentage, already rounded.
    #:
    #: Prose wants "99,6 %", the model is forbidden to compute, and the
    #: numeric-inventory check rejects any figure not in these facts — so a
    #: model multiplying 0,9963 by 100 was correct, obedient to the prompt and
    #: rejected anyway, dropping the whole narration to templates. Handing it
    #: the percentage removes the arithmetic instead of widening the check.
    share_pct: float = 0.0


@dataclass(frozen=True)
class RedLineChange:
    id: str
    label: str
    status: str
    base_status: str
    value: float
    threshold: float
    source: str
    first_year: int | None  # first year the line is crossed, None if never


@dataclass(frozen=True)
class ExplanationFacts:
    vintage: str
    engine_version: str
    horizon: int
    fresh: bool
    moved: list[MovedLever]
    outcomes: list[Outcome]
    headline_key: str
    headline_year: int
    contributions: list[Contribution]
    interaction: float
    joint_delta: float
    redlines: list[RedLineChange]
    mechanism: dict[str, list[dict]]

    def to_dict(self) -> dict:
        return asdict(self)


def _k(horizon: int) -> int:
    return max(0, min(Y1 - Y0, horizon - Y0))


def moved_levers(levers: Levers) -> list[MovedLever]:
    """Every lever that differs from its vintage base, in LEVER_SPECS order."""
    out: list[MovedLever] = []
    for spec in LEVER_SPECS:
        lid = spec["id"]
        base = c.BASE_LEVERS[lid]
        value = getattr(levers, lid)
        if abs(value - base) < 1e-9:
            continue
        out.append(MovedLever(
            id=lid, name=spec["nm"], symbol=spec["sym"], unit=spec["unit"],
            base=base, value=value, delta=value - base, dec=spec["dec"],
            source=spec["src"],
        ))
    return out


def _single_lever(lid: str, value: float) -> Levers:
    return Levers(**{lid: value})


def decompose(levers: Levers, key: str, k: int) -> tuple[list[Contribution], float, float]:
    """Re-run the engine once per moved lever to attribute the joint movement.

    Returns (contributions, interaction, joint_delta). `interaction` is the
    joint delta minus the sum of the single-lever deltas — the part of the
    movement that exists only because the levers were moved together.
    """
    base = baseline()
    joint = run_scenario(levers)
    joint_delta = joint[key][k] - base[key][k]

    moved = moved_levers(levers)
    singles: list[tuple[str, str, float]] = []
    for m in moved:
        solo = run_scenario(_single_lever(m.id, m.value))
        singles.append((m.id, m.name, solo[key][k] - base[key][k]))

    total_abs = sum(abs(d) for _, _, d in singles)

    def _share(d: float) -> float:
        return (abs(d) / total_abs) if total_abs > 1e-12 else 0.0

    contributions = [
        Contribution(lever_id=lid, lever_name=name, delta=d,
                     share=_share(d), share_pct=round(_share(d) * 100, 1))
        for lid, name, d in singles
    ]
    contributions.sort(key=lambda x: abs(x.delta), reverse=True)
    interaction = joint_delta - sum(d for _, _, d in singles)
    return contributions, interaction, joint_delta


def _first_crossing(scenario: dict[str, list[float]], rl: dict) -> int | None:
    """First year the line is crossed, scanning the whole projection."""
    series = scenario[rl["series"]]
    for i, v in enumerate(series):
        crossed = v > rl["threshold"] if rl["cmp"] == "gt" else v < rl["threshold"]
        if crossed:
            return Y0 + i
    return None


def build_facts(levers: Levers, horizon: int, headline: str = "b") -> ExplanationFacts:
    """The complete, engine-derived input to a narration. No LLM involved."""
    k = _k(horizon)
    base = baseline()
    run = run_scenario(levers)
    moved = moved_levers(levers)
    fresh = not moved and horizon == Y0

    outcomes: list[Outcome] = []
    for h in HEADLINES:
        kk = (Y1 - Y0) if h["at_end"] else k
        year = Y0 + kk
        b_val, s_val = base[h["key"]][kk], run[h["key"]][kk]
        delta = s_val - b_val
        if abs(delta) < 1e-9:
            direction = "sin cambio"
        elif (delta > 0) == h["up_is_bad"]:
            direction = "empeora"
        else:
            direction = "mejora"
        outcomes.append(Outcome(
            key=h["key"], label=h["label"], unit=h["unit"], year=year,
            base=b_val, value=s_val, delta=delta, dec=h["dec"],
            up_is_bad=h["up_is_bad"], direction=direction,
            sides=SIDES.get(h["key"]),
        ))

    # The caller may ask about a series outside the five. Add it, first, so the
    # narration is about what was asked: without this the headline had no
    # matching outcome and every block described the standing five instead.
    if headline not in {o.key for o in outcomes} and headline in SERIES_META:
        m = SERIES_META[headline]
        b_val, s_val = base[headline][k], run[headline][k]
        delta = s_val - b_val
        outcomes.insert(0, Outcome(
            key=headline, label=m["label"], unit=m["unit"], year=Y0 + k,
            base=b_val, value=s_val, delta=delta, dec=m["dec"],
            up_is_bad=m["up_is_bad"],
            direction=("sin cambio" if abs(delta) < 1e-9
                       else "empeora" if (delta > 0) == m["up_is_bad"]
                       else "mejora"),
            sides=SIDES.get(headline),
        ))

    # The year the headline outcome actually reports, which is the end of the
    # projection only for the series flagged `at_end`. Pinning both of these to
    # Y1 made the summary say «en 2030» and the decomposition under it say «en
    # 2050», splitting one answer across two horizons — and the shares were the
    # 2050 shares, so they did not describe the number above them either.
    head_out = next((o for o in outcomes if o.key == headline), None)
    head_k = (head_out.year - Y0) if head_out is not None else (Y1 - Y0)

    contributions, interaction, joint_delta = (
        decompose(levers, headline, head_k) if moved else ([], 0.0, 0.0)
    )

    base_status = {r["id"]: r["status"] for r in evaluate_redlines(base, k)}
    redlines = [
        RedLineChange(
            id=r["id"], label=r["label"], status=r["status"],
            base_status=base_status.get(r["id"], r["status"]),
            value=r["value"], threshold=r["threshold"], source=r["source"],
            first_year=_first_crossing(run, r),
        )
        for r in evaluate_redlines(run, k)
    ]

    return ExplanationFacts(
        vintage=c.VINTAGE, engine_version=c.ENGINE_VERSION, horizon=horizon,
        fresh=fresh, moved=moved, outcomes=outcomes,
        headline_key=headline, headline_year=Y0 + head_k,
        contributions=contributions, interaction=interaction,
        joint_delta=joint_delta, redlines=redlines,
        mechanism={m.id: MECHANISM.get(m.id, []) for m in moved},
    )
