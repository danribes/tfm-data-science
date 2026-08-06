"""Red-line evaluation (spec §4.5 / §7): crossed / near / safe against known scenarios."""
from engine.levers import Levers, preset_levers
from engine.redlines import NEAR_FRACTION, RED_LINES, evaluate_redlines
from engine.spain import Y0, run_scenario


def _status(results, rid):
    return next(r["status"] for r in results if r["id"] == rid)


def test_definitions_complete():
    assert NEAR_FRACTION == 0.10
    assert [r["id"] for r in RED_LINES] == [
        "bono_rescate", "paro_record", "deficit_maastricht", "deficit_suelo_2009",
        "deuda_105", "deuda_120", "inflacion_10", "esfuerzo_40", "pobreza_infantil_30"]
    for r in RED_LINES:
        assert r["cmp"] in ("gt", "lt") and r["source"].strip()


def test_base_2026_statuses_are_computed():
    # base run at k=0 (2026): b=106.3162, saldo=-4.1801, esf=42.5764, arop=28.5,
    # bono=3.42, u=10.1, pi=3.0 (values from the Task 6/7 pinned battery)
    res = evaluate_redlines(run_scenario(Levers()), 0)
    assert _status(res, "deuda_105") == "crossed"          # 106.32 > 105
    assert _status(res, "deuda_120") == "safe"             # |106.32-120|=13.68 > 12
    assert _status(res, "deficit_maastricht") == "crossed" # -4.18 < -3
    assert _status(res, "deficit_suelo_2009") == "safe"
    assert _status(res, "esfuerzo_40") == "crossed"        # 42.58 > 40
    assert _status(res, "pobreza_infantil_30") == "near"   # |28.5-30|=1.5 <= 3.0
    assert _status(res, "bono_rescate") == "safe"
    assert _status(res, "paro_record") == "safe"
    assert _status(res, "inflacion_10") == "safe"


def test_s7_adverse_2050_crossings():
    # S7 at k=24 (2050): b=349.7973, saldo=-28.7937, bono=6.47 (drafting probe)
    res = evaluate_redlines(run_scenario(preset_levers("S7")), 2050 - Y0)
    assert _status(res, "deuda_105") == "crossed"
    assert _status(res, "deuda_120") == "crossed"
    assert _status(res, "deficit_suelo_2009") == "crossed"
    assert _status(res, "bono_rescate") == "near"          # |6.47-7| = 0.53 <= 0.70


def test_every_status_is_computed_value():
    res = evaluate_redlines(run_scenario(Levers()), 24)
    for r in res:
        assert set(r) == {"id", "label", "series", "value", "threshold", "cmp",
                          "status", "source"}
        assert r["status"] in ("crossed", "near", "safe")
