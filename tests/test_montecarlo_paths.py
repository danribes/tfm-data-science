"""Individual Monte Carlo trajectories — the spaghetti plot's data.

The percentile bands were already covered by tests/test_montecarlo.py. What is
tested here is the subsample: that it is genuinely a slice of the same seeded
draw (so a strand is a real path, not a resampled artefact), that it is
reproducible, and that the endpoint carries it through.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from engine.constants import BASE_LEVERS, MC_HORIZON, MC_START_YEAR
from engine.levers import Levers
from engine.montecarlo import N_SHOW_DEFAULT, run_montecarlo

client = TestClient(app)


def test_default_subsample_size():
    mc = run_montecarlo(n_paths=300)
    assert len(mc.paths) == N_SHOW_DEFAULT


def test_each_path_spans_the_full_horizon():
    mc = run_montecarlo(n_paths=200, n_show=5)
    assert len(mc.years) == MC_HORIZON - MC_START_YEAR + 1
    for path in mc.paths:
        assert len(path) == len(mc.years)


def test_paths_are_reproducible_for_a_given_seed():
    a = run_montecarlo(n_paths=200, n_show=8, seed=7)
    b = run_montecarlo(n_paths=200, n_show=8, seed=7)
    assert a.paths == b.paths


def test_a_different_seed_gives_different_paths():
    a = run_montecarlo(n_paths=200, n_show=8, seed=7)
    b = run_montecarlo(n_paths=200, n_show=8, seed=8)
    assert a.paths != b.paths


def test_paths_are_distinct_from_one_another():
    """Strands must be separate futures, not the same path repeated."""
    mc = run_montecarlo(n_paths=200, n_show=10)
    finals = {round(p[-1], 6) for p in mc.paths}
    assert len(finals) == 10


def test_paths_sit_inside_the_percentile_envelope():
    """A strand is one draw from the same distribution the bands summarise."""
    mc = run_montecarlo(n_paths=2000, n_show=40)
    for i in range(len(mc.years)):
        lo, hi = mc.percentiles["p5"][i], mc.percentiles["p95"][i]
        inside = sum(1 for p in mc.paths if lo <= p[i] <= hi)
        # p5-p95 covers 90 % of the distribution, so on a 40-strand sample a
        # handful outside is expected; a majority outside would mean the
        # subsample is not from the same draw.
        assert inside >= 0.6 * len(mc.paths)


def test_n_show_zero_returns_no_paths_but_keeps_the_bands():
    mc = run_montecarlo(n_paths=200, n_show=0)
    assert mc.paths == []
    assert len(mc.percentiles["p50"]) == len(mc.years)


def test_n_show_is_capped_at_the_number_of_paths_drawn():
    mc = run_montecarlo(n_paths=5, n_show=50)
    assert len(mc.paths) == 5


def test_raising_rates_shifts_the_whole_bundle_up():
    base = run_montecarlo(Levers(), n_paths=800, n_show=20)
    hi = run_montecarlo(Levers(r=BASE_LEVERS["r"] + 2), n_paths=800, n_show=20)
    base_final = sum(p[-1] for p in base.paths) / len(base.paths)
    hi_final = sum(p[-1] for p in hi.paths) / len(hi.paths)
    assert hi_final > base_final


# ---- endpoint ----

def test_endpoint_returns_paths_truncated_to_the_horizon():
    r = client.post("/scenario/montecarlo",
                    json={"n_paths": 200, "n_show": 6, "horizon": 2050})
    assert r.status_code == 200
    body = r.json()
    n = 2050 - MC_START_YEAR + 1
    assert len(body["paths"]) == 6
    assert all(len(p) == n for p in body["paths"])
    assert len(body["years"]) == n


def test_endpoint_rejects_an_out_of_range_n_show():
    assert client.post("/scenario/montecarlo", json={"n_show": 500}).status_code == 422
    assert client.post("/scenario/montecarlo", json={"n_show": -1}).status_code == 422


def test_endpoint_paths_match_the_engine():
    r = client.post("/scenario/montecarlo",
                    json={"n_paths": 200, "n_show": 3, "horizon": 2070, "seed": 42})
    direct = run_montecarlo(Levers(), n_paths=200, seed=42, n_show=3)
    served = r.json()["paths"]
    assert len(served) == len(direct.paths)
    # approx() takes a flat sequence, so compare one strand at a time.
    for got, want in zip(served, direct.paths):
        assert got == pytest.approx(want)
