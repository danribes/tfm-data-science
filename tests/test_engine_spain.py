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


# ---- Task 6: chain + debt identity + deviation semantics ----
from engine.spain import N_YEARS, SERIES_KEYS, Y0, baseline, french, run_scenario


def test_series_shape():
    run = run_scenario(Levers())
    assert len(SERIES_KEYS) == 40
    assert set(run) == set(SERIES_KEYS)
    for k in SERIES_KEYS:
        assert len(run[k]) == N_YEARS == 25


def test_deviation_semantics_base_levers_equal_baseline():
    # spec §4.1: baseline freezes the vintage; all levers at base -> zero deviation
    run = run_scenario(Levers())
    base = baseline()
    for k in SERIES_KEYS:
        assert run[k] == base[k], k
    assert all(v == 0.0 for v in run["lvl"])
    assert all(v == 10.1 for v in run["u"])       # V0.u, constant at base
    assert all(v == 3.0 for v in run["pi"])       # V0.pi
    assert all(v == 2.7 for v in run["g"])        # V0.g
    assert all(v == 3.42 for v in run["bono"])    # r + TERM + prima/100
    assert all(v == 100.0 for v in run["nomreal"])
    assert run["wrealIdx"][0] == 100.0


def test_debt_identity_reproduces_gold_central():
    # pre-A1: values measured while drafting (extract S3.1 rows L868-871):
    # 2026 106.316196 vs 106.32 | 2030 112.885096 vs 112.9
    # 2035 129.142456 vs 129.18 | 2050 223.841410 vs 223.86
    run = run_scenario(Levers())
    assert run["b"][2026 - Y0] == pytest.approx(106.316196, abs=1e-4)
    assert run["b"][2030 - Y0] == pytest.approx(112.885096, abs=1e-4)
    assert run["b"][2035 - Y0] == pytest.approx(129.142456, abs=1e-4)
    assert run["b"][2050 - Y0] == pytest.approx(223.841410, abs=1e-4)


def test_french_amortization():
    # extract L93 / L1012-1013: cuota = P*i/(1-(1+i)^-n), i = tipo/1200
    assert french(171444.46 * 0.8, 2.80 + 1.4757, 300) == pytest.approx(744.9991, abs=1e-3)


def test_lever_signs():
    base = baseline()
    k = 2035 - Y0
    assert run_scenario(Levers(r=4.8))["b"][k] > base["b"][k]        # dearer debt
    assert run_scenario(Levers(sp=1.0))["b"][k] < base["b"][k]       # consolidation
    assert run_scenario(Levers(sp=1.0))["u"][k] > base["u"][k]       # its social cost
    assert run_scenario(Levers(pm=50.0))["pi"][0] > base["pi"][0]    # pass-through
    assert run_scenario(Levers(lam=1.4))["wrealIdx"][k] > base["wrealIdx"][k]
    assert run_scenario(Levers(dem=0.6))["pens"][k] > base["pens"][k]


# ---- Task 7: persona dependents ----
from engine.spain import PERSONA_IDS, PERSONAS, persona_dependents

EXPECTED_PILLS = ["💼 Bonista", "🏦 Banca", "🔑 Comprador", "🚀 Emprendedor",
                  "🏛️ Funcionario", "🗳️ Político", "🕳️ Corrupto", "🧒 Infancia",
                  "🌅 Jubilado", "🎓 Joven", "📋 Indefinido", "🧾 Autónomo"]


def test_twelve_personas_verbatim_identity():
    assert PERSONA_IDS == [f"{i:02d}" for i in range(1, 13)]
    assert [p["pill"] for p in PERSONAS] == EXPECTED_PILLS
    by_id = {p["id"]: p for p in PERSONAS}
    assert by_id["01"]["h1"] == "💼 Inversor en bonos: ¿me pagarán los 10 años?"
    assert by_id["08"]["h1"] == "🧒 ¿Qué país hereda quien hoy tiene 8 años?"
    assert by_id["12"]["foot"] == "🧾 autónomo"
    assert by_id["07"]["foot"] == "🕳️ político corrupto · sátira de transparencia"
    for p in PERSONAS:
        assert len(p["outs"]) == 5
        assert p["headline"] in [o["k"] for o in p["outs"]]
        assert len(p["reds"]) == 3
        for o in p["outs"]:
            assert o["k"] in SERIES_KEYS


def test_persona_dependents_shape():
    deps = persona_dependents(run_scenario(Levers()))
    assert sorted(deps) == PERSONA_IDS
    for pid, d in deps.items():
        assert set(d) == {"pill", "headline", "series"}
        assert d["headline"] in d["series"]
        for series in d["series"].values():
            assert len(series) == 25


# One pinned numeric check per persona at BASE levers. Values computed while
# drafting this plan by executing the verbatim v16 run() semantics (extract
# L95-175) against the committed gold slice; k is the year index (0=2026,
# 4=2030, 9=2035, 24=2050).
BASE_PINS = [
    ("01", "bono", 0, 3.42), ("01", "b", 24, 223.8414), ("01", "int", 4, 3.3436),
    ("02", "cuota", 0, 744.9971), ("02", "bls", 0, 10.0),
    ("03", "esf", 0, 42.5764), ("03", "precio", 4, 217954.5876),
    ("04", "g", 0, 2.7), ("04", "auton", 0, 14.5),
    ("05", "d1", 0, 10.9), ("05", "nomreal", 24, 100.0),
    ("06", "saldo", 4, -5.8136), ("06", "u", 0, 10.1),
    ("07", "p51", 0, 3.0), ("07", "p2", 0, 5.7), ("07", "d3", 0, 1.4),
    ("08", "arop", 0, 28.5), ("08", "edu", 0, 4.1), ("08", "dep", 24, 59.0),
    ("09", "pens", 9, 16.4858), ("09", "dep", 9, 41.7),
    ("10", "ujuv", 0, 23.4017), ("10", "temp", 0, 15.3),
    ("11", "wrealIdx", 4, 103.6489), ("11", "salario", 4, 28547.9608),
    ("12", "auton", 0, 14.5), ("12", "r", 0, 2.8),
]

# One pinned moved-lever check per persona (same provenance).
MOVED_PINS = [
    ("01", {"prima": 150.0}, "bono", 0, 4.47),
    ("02", {"r": 4.8}, "bls", 9, 35.4993),
    ("03", {"r": 4.8}, "esf", 9, 35.7009),
    ("04", {"ext": 3.0}, "lvl", 9, 0.4165),
    ("05", {"sp": 1.0}, "d1", 9, 10.66),
    ("06", {"sp": 1.0}, "b", 24, 210.3118),
    ("07", {"sp": 1.0}, "p51", 9, 2.855),
    ("08", {"sp": 1.0}, "arop", 9, 29.7665),
    ("09", {"idx": -0.5}, "nomreal", 9, 95.589),
    ("10", {"z": -1.0}, "temp", 9, 16.525),
    ("11", {"lam": 1.4}, "wrealIdx", 24, 139.6082),
    ("12", {"pm": 50.0}, "pi", 0, 5.2163),
]


@pytest.mark.parametrize("pid,key,k,expected", BASE_PINS)
def test_persona_base_pins(pid, key, k, expected):
    deps = persona_dependents(run_scenario(Levers()))
    assert deps[pid]["series"][key][k] == pytest.approx(expected, abs=1e-3)


@pytest.mark.parametrize("pid,moved,key,k,expected", MOVED_PINS)
def test_persona_moved_lever_pins(pid, moved, key, k, expected):
    deps = persona_dependents(run_scenario(Levers(**moved)))
    assert deps[pid]["series"][key][k] == pytest.approx(expected, abs=1e-3)
