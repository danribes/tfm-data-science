"""Levers, ranges and presets — v16 `const LEVERS` / `const PRESETS` ported
verbatim (extract L178-200; template L390-411). Ranges are the empirically
anchored envelopes of v12 (extract S7.2)."""
from __future__ import annotations

from dataclasses import dataclass, fields

from engine.constants import BASE_LEVERS


@dataclass(frozen=True)
class Levers:
    r: float = BASE_LEVERS["r"]
    prima: float = BASE_LEVERS["prima"]
    sp: float = BASE_LEVERS["sp"]
    lam: float = BASE_LEVERS["lam"]
    pm: float = BASE_LEVERS["pm"]
    tau: float = BASE_LEVERS["tau"]
    z: float = BASE_LEVERS["z"]
    ext: float = BASE_LEVERS["ext"]
    dem: float = BASE_LEVERS["dem"]
    idx: float = BASE_LEVERS["idx"]


# v16 `const LEVERS` — Spanish copy verbatim (template L390-399, extract L178-189)
LEVER_SPECS: list[dict] = [
    {"id": "r", "sym": "r", "nm": "Tipo de interés · Euríbor 12m", "unit": "%",
     "min": 0.0, "max": 6.0, "step": 0.05, "dec": 2, "src": "ecb_euribor12m.csv · 2026-06"},
    {"id": "prima", "sym": "σ", "nm": "Prima de riesgo · spread ES–DE", "unit": "pb",
     "min": 0.0, "max": 400.0, "step": 5.0, "dec": 0, "src": "ecb_bono10y_{es,de}.csv · 2026-06"},
    {"id": "sp", "sym": "sp", "nm": "Saldo primario · Δ vs central", "unit": "pp PIB",
     "min": -4.0, "max": 4.0, "step": 0.1, "dec": 1, "src": "gold_escenarios_deuda.csv (central)"},
    {"id": "lam", "sym": "λ", "nm": "Productividad", "unit": "%/año",
     "min": -0.5, "max": 2.5, "step": 0.1, "dec": 1, "src": "PWT + INE · desplaza la PS"},
    {"id": "pm", "sym": "pᵐ", "nm": "Precio importaciones/energía", "unit": "% a/a",
     "min": -50.0, "max": 100.0, "step": 5.0, "dec": 0, "src": "WEO commodity prices"},
    {"id": "tau", "sym": "τ", "nm": "Presión fiscal · cuña laboral", "unit": "pp",
     "min": -5.0, "max": 5.0, "step": 0.25, "dec": 2, "src": "Eurostat GFS · desplaza la WS"},
    {"id": "z", "sym": "z", "nm": "Instituciones laborales", "unit": "índice",
     "min": -2.0, "max": 2.0, "step": 0.1, "dec": 1, "src": "OECD/Eurostat · desplaza la WS"},
    {"id": "ext", "sym": "Y*", "nm": "Demanda externa", "unit": "% a/a",
     "min": -4.0, "max": 6.0, "step": 0.1, "dec": 1, "src": "WEO · canal exterior (U7)"},
    {"id": "dem", "sym": "β₆₅", "nm": "Presión demográfica", "unit": "×",
     "min": -1.0, "max": 1.0, "step": 0.05, "dec": 2, "src": "gold_projections.csv · variante"},
    {"id": "idx", "sym": "ι", "nm": "Indexación pensiones/nóminas", "unit": "IPC+pp",
     "min": -1.5, "max": 1.0, "step": 0.1, "dec": 1, "src": "regla de revalorización · palanca"},
]

# v16 `const PRESETS` — verbatim (extract L1583-1592); r offsets resolved
# against BASE (S1/S7: BASE.r + 2 = 4.8)
PRESETS: list[dict] = [
    {"id": "S0", "nm": "S0 base", "set": {}},
    {"id": "S1", "nm": "S1 tipos +200 pb", "set": {"r": BASE_LEVERS["r"] + 2}},
    {"id": "S2", "nm": "S2 petróleo +50 %", "set": {"pm": 50.0}},
    {"id": "S3", "nm": "S3 consolidación", "set": {"sp": 1.0}},
    {"id": "S4", "nm": "S4 productividad", "set": {"lam": 1.4}},
    {"id": "S5", "nm": "S5 desregulación lab.", "set": {"z": -1.0, "tau": -1.5}},
    {"id": "S6", "nm": "S6 envejecimiento", "set": {"dem": 0.6}},
    {"id": "S7", "nm": "S7 adverso", "set": {"r": BASE_LEVERS["r"] + 2, "pm": 50.0, "prima": 150.0}},
]

_SPEC_BY_ID = {s["id"]: s for s in LEVER_SPECS}


def preset_levers(preset_id: str) -> Levers:
    try:
        preset = next(p for p in PRESETS if p["id"] == preset_id)
    except StopIteration:
        raise ValueError(f"unknown preset id: {preset_id!r} (valid: S0..S7)")
    return Levers(**preset["set"])


def validate_levers(levers: Levers) -> list[str]:
    errors: list[str] = []
    for f in fields(Levers):
        spec = _SPEC_BY_ID[f.name]
        value = getattr(levers, f.name)
        if not (spec["min"] <= value <= spec["max"]):
            errors.append(f"{f.name}={value} outside [{spec['min']}, {spec['max']}]")
    return errors
