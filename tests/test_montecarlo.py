"""Monte Carlo DSA tests (spec §7): seeded reproducibility, percentile
ordering, envelope tolerance vs the gold fan."""
import csv
import time

from engine.constants import GOLD_DIR
from engine.levers import Levers
from engine.montecarlo import McResult, run_montecarlo

PCTS = ("p5", "p25", "p50", "p75", "p95")


def _gold_central_mc() -> dict[int, dict[str, float]]:
    out = {}
    with (GOLD_DIR / "gold_escenarios_deuda_mc.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["escenario"] == "central":
                out[int(float(row["year"]))] = {p: float(row[p]) for p in PCTS}
    return out


def test_shape_and_years():
    mc = run_montecarlo(Levers(), n_paths=500, seed=1)
    assert isinstance(mc, McResult)
    assert mc.years == list(range(2026, 2071))
    assert set(mc.percentiles) == set(PCTS)
    assert all(len(v) == 45 for v in mc.percentiles.values())
    assert (mc.n_paths, mc.seed) == (500, 1)


def test_seeded_reproducibility():
    a = run_montecarlo(Levers(), n_paths=500, seed=7)
    b = run_montecarlo(Levers(), n_paths=500, seed=7)
    c = run_montecarlo(Levers(), n_paths=500, seed=8)
    assert a.percentiles == b.percentiles
    assert a.percentiles != c.percentiles


def test_percentile_ordering():
    mc = run_montecarlo(Levers(), n_paths=1000, seed=3)
    for i in range(45):
        vals = [mc.percentiles[p][i] for p in PCTS]
        assert vals == sorted(vals), mc.years[i]


def test_envelope_matches_gold_within_2pp():
    # A5 pre-check (also in tests/test_anchors.py): seed 42, 4000 paths
    mc = run_montecarlo(Levers(), n_paths=4000, seed=42)
    gold = _gold_central_mc()
    for y in (2030, 2050, 2070):
        i = y - 2026
        for p in ("p5", "p50", "p95"):
            assert abs(mc.percentiles[p][i] - gold[y][p]) <= 2.0, (y, p)


def test_levers_shift_the_fan():
    base = run_montecarlo(Levers(), n_paths=1000, seed=5)
    s1 = run_montecarlo(Levers(r=4.8), n_paths=1000, seed=5)   # S1 tipos +200 pb
    i = 2050 - 2026
    assert s1.percentiles["p50"][i] > base.percentiles["p50"][i] + 20


def test_runtime_under_one_second():
    start = time.perf_counter()
    run_montecarlo(Levers(), n_paths=4000, seed=42)
    assert time.perf_counter() - start < 1.0     # spec §4.3 target (measured 0.04 s)
