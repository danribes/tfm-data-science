"""A1-A5 anchor battery (spec §4.2). Failure of ANY test here is a build failure."""
import csv
import json
import math
from pathlib import Path

import pytest

from engine.constants import GOLD_DIR, load_central
from engine.levers import LEVER_SPECS, Levers, PRESETS, preset_levers
from engine.montecarlo import run_montecarlo
from engine.spain import SERIES_KEYS, Y0, run_scenario

FIXTURE = Path(__file__).parent / "fixtures" / "engine_anchors.json"
ANCHOR_YEARS = [2026, 2030, 2035, 2050]

# A3 probe values — one in-range non-base value per lever
PROBE = {"r": 4.8, "prima": 150.0, "sp": 1.0, "lam": 1.4, "pm": 50.0,
         "tau": 1.5, "z": -1.0, "ext": 3.0, "dem": 0.6, "idx": -0.5}

# Non-debt series pinned per preset / probe bundle (phase-2 additivity extension).
PINNED_SERIES = ("u", "pi", "wrealIdx", "cuota", "esf", "pens", "saldo")


def test_a1_debt_identity_reproduces_gold_central_to_the_decimal():
    # v16 AC-V3. Tolerance 0.05 = half a printed decimal: the CSV rounds deuda
    # AND its pb/r_efectivo inputs, so exact-to-machine equality is impossible
    # by construction. Measured drift while drafting: 2026 −0.0038, 2030
    # −0.0149, 2035 −0.0375, 2050 −0.0186 (extract S3.1 rows, L868-871).
    base = run_scenario(Levers())
    central = load_central()
    for y in ANCHOR_YEARS:
        assert abs(base["b"][y - Y0] - central[y]["deuda"]) <= 0.05, y


def test_a2_french_amortization_reproduces_gold_cuota():
    # gold_cuota_teorica.csv row-wise median cuota_mensual = 744.89 (the
    # Navarra row — extract L932, median derivation L941-949). Spec: ±1 EUR.
    base = run_scenario(Levers())
    assert abs(base["cuota"][0] - 744.89) <= 1.0


def test_a3_no_lever_is_inert():
    base = run_scenario(Levers())
    assert set(PROBE) == {s["id"] for s in LEVER_SPECS}
    for lever_id, probe_value in PROBE.items():
        assert probe_value != getattr(Levers(), lever_id)
        moved = run_scenario(Levers(**{lever_id: probe_value}))
        max_delta = max(abs(moved[k][i] - base[k][i])
                        for k in SERIES_KEYS for i in (0, 9, 24))
        assert max_delta > 1e-9, f"lever {lever_id} is inert"


def test_a4_all_eight_presets_produce_finite_paths():
    for preset in PRESETS:
        run = run_scenario(preset_levers(preset["id"]))
        for k in SERIES_KEYS:
            assert all(math.isfinite(v) for v in run[k]), (preset["id"], k)


def test_a5_mc_envelopes_match_gold_within_2pp():
    # seed-42 / 4000-path run vs gold_escenarios_deuda_mc.csv central rows
    # (extract L899-901). Verified while drafting: max |dev| = 1.399 pp.
    mc = run_montecarlo(Levers(), n_paths=4000, seed=42)
    gold = {}
    with (GOLD_DIR / "gold_escenarios_deuda_mc.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["escenario"] == "central" and int(float(row["year"])) in (2030, 2050, 2070):
                gold[int(float(row["year"]))] = row
    for y in (2030, 2050, 2070):
        i = y - 2026
        for q in ("p5", "p50", "p95"):
            assert abs(mc.percentiles[q][i] - float(gold[y][q])) <= 2.0, (y, q)


def test_committed_fixture_matches_regenerated_values():
    # The committed fixture is the phase-2 JS engine contract; it must never
    # drift from what the Python engine actually computes.
    committed = json.loads(FIXTURE.read_text(encoding="utf-8"))
    base = run_scenario(Levers())
    central = load_central()
    for y in ANCHOR_YEARS:
        entry = committed["debt_central"][str(y)]
        assert entry["engine"] == pytest.approx(base["b"][y - Y0], abs=1e-6)
        assert entry["gold_csv"] == central[y]["deuda"]
    assert committed["cuota_2026_base"] == pytest.approx(base["cuota"][0], abs=1e-3)
    assert committed["cuota_gold_median"] == 744.89
    mc = run_montecarlo(Levers(), n_paths=4000, seed=42)
    for y in ("2030", "2050", "2070"):
        for q in ("p5", "p25", "p50", "p75", "p95"):
            assert committed["montecarlo_seed42"][y][q] == pytest.approx(
                mc.percentiles[q][int(y) - 2026], abs=1e-3)
    for pid in ("S0", "S7"):
        assert pid in committed["presets_debt_2050"]

    # presets_series_2035_2050: every preset, {u, pi, wrealIdx, cuota, esf,
    # pens, saldo} at 2035/2050 must match a fresh run_scenario(preset_levers(...)).
    for preset in PRESETS:
        pid = preset["id"]
        run = run_scenario(preset_levers(pid))
        for y in ("2035", "2050"):
            entry = committed["presets_series_2035_2050"][pid][y]
            for k in PINNED_SERIES:
                assert entry[k] == pytest.approx(run[k][int(y) - Y0], abs=1e-6), (pid, y, k)

    # probe_bundle: all ten levers moved at once (same PROBE deltas as A3),
    # pinning the same series plus debt "b" at 2035/2050.
    probe_run = run_scenario(Levers(**PROBE))
    for y in ("2035", "2050"):
        entry = committed["probe_bundle"][y]
        for k in (*PINNED_SERIES, "b"):
            assert entry[k] == pytest.approx(probe_run[k][int(y) - Y0], abs=1e-6), (y, k)

    # base_gold_identity: base-run ief/gnom/pb recorded alongside the gold CSV
    # columns they derive from, at 2026/2030/2035/2050.
    for y in ANCHOR_YEARS:
        entry = committed["base_gold_identity"][str(y)]
        assert entry["ief"]["engine"] == pytest.approx(base["ief"][y - Y0], abs=1e-6), y
        assert entry["gnom"]["engine"] == pytest.approx(base["gnom"][y - Y0], abs=1e-6), y
        assert entry["pb"]["engine"] == pytest.approx(base["pb"][y - Y0], abs=1e-6), y


def test_a6_base_ief_gnom_pb_match_gold_central_exactly():
    # At base levers every deviation term (di, lvl, pi_dev, L.sp-B["sp"],
    # L.dem-B["dem"]) is zero by construction, so ief/gnom/pb must reproduce
    # the gold central CSV's r_efectivo/g_nominal/pb columns exactly — not
    # merely within the printed-decimal debt-identity tolerance used for A1.
    # This is an independent check against a freshly loaded gold CSV, not
    # against the committed fixture's own recorded copy.
    base = run_scenario(Levers())
    central = load_central()
    for y in ANCHOR_YEARS:
        assert base["ief"][y - Y0] == pytest.approx(central[y]["r_efectivo"], abs=1e-9), y
        assert base["gnom"][y - Y0] == pytest.approx(central[y]["g_nominal"], abs=1e-9), y
        assert base["pb"][y - Y0] == pytest.approx(central[y]["pb"], abs=1e-9), y


def test_a7_probe_bundle_debt_diverges_from_s0_at_2050():
    # probe_bundle moves all ten levers at once; its 2050 debt must differ
    # from S0's (base) 2050 debt by more than float noise, proving the bundle
    # actually exercises the debt-identity chain end to end.
    base = run_scenario(Levers())
    probe_run = run_scenario(Levers(**PROBE))
    assert abs(probe_run["b"][2050 - Y0] - base["b"][2050 - Y0]) > 1e-6
