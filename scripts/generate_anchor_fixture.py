#!/usr/bin/env python3
"""Write tests/fixtures/engine_anchors.json — the dual-engine anchor contract.

The committed output binds BOTH engines: tests/test_anchors.py reads it here,
and phase 2's JS engine tests must read THIS SAME file (spec §4.2).
Regenerate (and re-commit) with:  .venv/bin/python scripts/generate_anchor_fixture.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root, for `python scripts/...` invocation

from engine.constants import VINTAGE, load_central
from engine.levers import Levers, PRESETS, preset_levers
from engine.montecarlo import run_montecarlo
from engine.spain import Y0, run_scenario
from tests.test_anchors import PROBE  # single source of truth for the all-ten-levers probe deltas

OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "engine_anchors.json"
ANCHOR_YEARS = (2026, 2030, 2035, 2050)

# Non-debt series pinned per preset / probe (phase-2 additivity: u, pi, wrealIdx,
# cuota, esf, pens, saldo — none of these touch the debt identity directly, so
# they exercise the rest of the engine even where a preset never moves "b").
PINNED_SERIES = ("u", "pi", "wrealIdx", "cuota", "esf", "pens", "saldo")
PINNED_YEARS = (2035, 2050)


def main() -> None:
    base = run_scenario(Levers())
    central = load_central()
    mc = run_montecarlo(Levers(), n_paths=4000, seed=42)

    presets_series_2035_2050 = {}
    for p in PRESETS:
        run = run_scenario(preset_levers(p["id"]))
        presets_series_2035_2050[p["id"]] = {
            str(y): {k: round(run[k][y - Y0], 6) for k in PINNED_SERIES}
            for y in PINNED_YEARS
        }

    # probe_bundle: every one of the ten levers moved at once (the exact A3
    # PROBE deltas from tests/test_anchors.py), pinning the same series plus
    # debt "b" — proves the full chain (not just single-lever probes) reaches
    # every series, including ones no single preset touches (ext, idx).
    probe_run = run_scenario(Levers(**PROBE))
    probe_bundle = {
        str(y): {k: round(probe_run[k][y - Y0], 6) for k in (*PINNED_SERIES, "b")}
        for y in PINNED_YEARS
    }

    # base_gold_identity: at base levers the deviation terms are all zero, so
    # ief/gnom/pb should reproduce the gold central CSV's r_efectivo/g_nominal/pb
    # columns exactly (to float precision) — recording both sides lets the test
    # assert the identity instead of merely trusting it.
    base_gold_identity = {
        str(y): {
            "ief": {"engine": round(base["ief"][y - Y0], 6), "gold_csv": central[y]["r_efectivo"]},
            "gnom": {"engine": round(base["gnom"][y - Y0], 6), "gold_csv": central[y]["g_nominal"]},
            "pb": {"engine": round(base["pb"][y - Y0], 6), "gold_csv": central[y]["pb"]},
        }
        for y in ANCHOR_YEARS
    }

    fixture = {
        "vintage": VINTAGE,
        "generator": "scripts/generate_anchor_fixture.py",
        "debt_central": {str(y): {"engine": round(base["b"][y - Y0], 6),
                                  "gold_csv": central[y]["deuda"]}
                         for y in ANCHOR_YEARS},
        "cuota_2026_base": round(base["cuota"][0], 4),
        "cuota_gold_median": 744.89,
        "presets_debt_2050": {p["id"]: round(run_scenario(preset_levers(p["id"]))["b"][2050 - Y0], 4)
                              for p in PRESETS},
        "montecarlo_seed42": {str(y): {q: round(mc.percentiles[q][y - 2026], 4)
                                       for q in ("p5", "p25", "p50", "p75", "p95")}
                              for y in (2030, 2050, 2070)},
        "base_2026": {k: round(base[k][0], 6) for k in
                      ("u", "pi", "g", "bono", "cuota", "esf", "b", "pens", "dep", "ujuv")},
        "presets_series_2035_2050": presets_series_2035_2050,
        "probe_bundle": probe_bundle,
        "base_gold_identity": base_gold_identity,
    }
    OUT.write_text(json.dumps(fixture, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
