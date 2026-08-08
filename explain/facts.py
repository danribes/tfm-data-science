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
    ],
    "lam": [
        {"step": "desplaza la curva PS (paro estructural)",
         "const": "A_LAM", "value": c.A_LAM, "note": "productividad sobre u*"},
        {"step": "crecimiento potencial",
         "const": "MULT", "value": c.MULT, "note": "vía nivel de PIB"},
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


@dataclass(frozen=True)
class Contribution:
    """How much of the headline movement this lever accounts for on its own."""
    lever_id: str
    lever_name: str
    delta: float
    share: float  # of the sum of |single-lever deltas|, not of the joint delta


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
    contributions = [
        Contribution(lever_id=lid, lever_name=name, delta=d,
                     share=(abs(d) / total_abs) if total_abs > 1e-12 else 0.0)
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
        ))

    contributions, interaction, joint_delta = (
        decompose(levers, headline, Y1 - Y0) if moved else ([], 0.0, 0.0)
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
        headline_key=headline, headline_year=Y1,
        contributions=contributions, interaction=interaction,
        joint_delta=joint_delta, redlines=redlines,
        mechanism={m.id: MECHANISM.get(m.id, []) for m in moved},
    )
