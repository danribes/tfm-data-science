"""Spain engine tests: constants (Task 4), levers/presets (Task 5),
chain + deviation semantics (Task 6), persona dependents (Task 7)."""
import math

import pytest

from engine import constants as c


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
