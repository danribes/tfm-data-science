"""Spain engine tests: constants (Task 4), levers/presets (Task 5),
chain + deviation semantics (Task 6), persona dependents (Task 7)."""
import math

import pytest

from engine import constants as c
from engine import generic as g


def test_vintage_and_version():
    assert c.VINTAGE == "2026-07-31"
    assert c.ENGINE_VERSION == "1.0.0"


def test_spain_constants_verbatim_v16():
    # extract L73-91 (`const C` of _v16_template.html)
    assert (c.MULT, c.RHO, c.E_R, c.E_EXT, c.E_PM) == (1.40, 0.62, 0.45, 0.25, 0.012)
    assert (c.OKUN, c.KAPPA, c.GAMMA, c.THETA, c.PHI) == (0.48, 0.22, 0.045, 0.55, 0.30)
    assert (c.A_Z, c.A_TAU, c.A_LAM) == (1.10, 0.30, 0.45)
    assert (c.REFI, c.TERM) == (0.14, 0.17)
    assert c.DIFF == 1.4757            # build_v16.py bisection (extract L1055-1073)
    assert (c.IPV_LR, c.IPV_REV, c.E_IPV_R, c.E_IPV_G) == (3.0, 0.60, 2.6, 1.1)
    assert c.RJUV == 2.317
    assert c.PM_DECAY == 0.45


def test_v0_and_base_levers_from_gold_kpis():
    assert c.V0["u"] == 10.1 and c.V0["pi"] == 3.0 and c.V0["g"] == 2.7
    assert c.V0["bono"] == 3.42 and c.V0["precio"] == 171444 and c.V0["cuota"] == 745
    assert c.V0["salmes"] == 1749.79          # round(24497 / 14, 2) — build_v16 calib
    assert c.V0["pens"] == 13.23 and c.V0["arop"] == 28.5 and c.V0["vida"] == 84.0
    assert c.V0["hip"] == 500906 and c.V0["bls"] == 10.0 and c.V0["sobre"] == 7.2
    assert c.BASE_LEVERS == {"r": 2.8, "prima": 45.0, "sp": 0.0, "lam": 0.9, "pm": 0.0,
                             "tau": 0.0, "z": 0.0, "ext": 1.8, "dem": 0.0, "idx": 0.0}


def test_gold_loaders():
    central = c.load_central()
    assert central[2025]["deuda"] == 105.6         # extract L1083
    assert central[2026] == {"deuda": 106.32, "pb": -1.35, "r_efectivo": 2.68,
                             "g_nominal": 3.3, "presion_demog": 0.45}   # extract L868
    olddep = c.load_olddep()
    assert olddep[2026] == 32.6 and olddep[2050] == 59.0


def test_constants_table_has_provenance_for_every_entry():
    assert len(c.CONSTANTS_TABLE) >= 30
    for entry in c.CONSTANTS_TABLE:
        assert set(entry) == {"name", "value", "unit", "provenance"}
        assert entry["provenance"].strip(), entry["name"]
        assert math.isfinite(float(entry["value"]))
    names = [e["name"] for e in c.CONSTANTS_TABLE]
    for expected in ("MULT", "OKUN", "DIFF", "MC_SIG_R", "GENERIC_OKUN", "GENERIC_PHILLIPS"):
        assert expected in names


def test_generic_engine_constants_sourced_not_hardcoded():
    """Verify CONSTANTS_TABLE generic defaults are imported from engine.generic,
    not hardcoded, to keep CONSTANTS_TABLE in sync with canonical runtime values."""
    generic_okun_entry = next(e for e in c.CONSTANTS_TABLE if e["name"] == "GENERIC_OKUN")
    generic_phillips_entry = next(e for e in c.CONSTANTS_TABLE if e["name"] == "GENERIC_PHILLIPS")
    assert generic_okun_entry["value"] == g.OKUN_COEFFICIENT
    assert generic_phillips_entry["value"] == g.PHILLIPS_SLOPE


# ---- Task 5: levers & presets ----
from dataclasses import asdict
from engine.levers import LEVER_SPECS, PRESETS, Levers, preset_levers, validate_levers

# spec §4.1 table (binding) — (id, min, max, base)
EXPECTED_RANGES = [
    ("r", 0.0, 6.0, 2.8), ("prima", 0.0, 400.0, 45.0), ("sp", -4.0, 4.0, 0.0),
    ("lam", -0.5, 2.5, 0.9), ("pm", -50.0, 100.0, 0.0), ("tau", -5.0, 5.0, 0.0),
    ("z", -2.0, 2.0, 0.0), ("ext", -4.0, 6.0, 1.8), ("dem", -1.0, 1.0, 0.0),
    ("idx", -1.5, 1.0, 0.0),
]


def test_lever_specs_ranges_and_bases():
    assert [s["id"] for s in LEVER_SPECS] == [rid for rid, *_ in EXPECTED_RANGES]
    base = Levers()
    for (rid, lo, hi, base_val), spec in zip(EXPECTED_RANGES, LEVER_SPECS):
        assert (spec["min"], spec["max"]) == (lo, hi), rid
        assert getattr(base, rid) == base_val, rid
    syms = [s["sym"] for s in LEVER_SPECS]
    assert syms == ["r", "σ", "sp", "λ", "pᵐ", "τ", "z", "Y*", "β₆₅", "ι"]
    assert LEVER_SPECS[0]["nm"] == "Tipo de interés · Euríbor 12m"
    # Verify all Levers defaults come from BASE_LEVERS (single source of truth)
    assert asdict(Levers()) == c.BASE_LEVERS


def test_presets_verbatim_and_within_ranges():
    assert [p["id"] for p in PRESETS] == [f"S{i}" for i in range(8)]
    assert [p["nm"] for p in PRESETS] == [
        "S0 base", "S1 tipos +200 pb", "S2 petróleo +50 %", "S3 consolidación",
        "S4 productividad", "S5 desregulación lab.", "S6 envejecimiento", "S7 adverso"]
    assert PRESETS[0]["set"] == {}
    assert PRESETS[7]["set"] == {"r": 4.8, "pm": 50.0, "prima": 150.0}
    assert preset_levers("S0") == Levers()
    for p in PRESETS:
        assert validate_levers(preset_levers(p["id"])) == [], p["id"]


def test_validate_levers_flags_out_of_range():
    assert validate_levers(Levers(r=9.0)) == ["r=9.0 outside [0.0, 6.0]"]
    assert validate_levers(Levers()) == []


def test_preset_levers_raises_on_unknown_id():
    with pytest.raises(ValueError) as exc_info:
        preset_levers("S9")
    assert "unknown preset id: 'S9'" in str(exc_info.value)
    assert "valid: S0..S7" in str(exc_info.value)
