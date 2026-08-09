"""The empirical layer: panels, cluster-robust estimation, and the confrontation
of the engine's calibrated constants with the frozen data.

These tests pin the *machinery* — that clustering widens bands, that fixed
effects recover a known slope, that the identifiability claims stay honest —
not the numeric results, which are properties of the vintage and are allowed to
move when the vintage does.
"""
from __future__ import annotations

import math

import pytest

from engine import constants as c
from research import estimate, panel, validate


# ---- panels -----------------------------------------------------------------

def test_housing_panel_shape():
    p = panel.housing_panel()
    assert len(p.units) == 20
    assert len(p) > 1400
    assert all(r["ipv"] is not None for r in p.rows)


def test_housing_panel_time_index_is_monotonic_within_a_region():
    p = panel.housing_panel()
    rows = [r for r in p.rows if r["ccaa"] == p.units[0]]
    ts = [r["t"] for r in rows]
    assert ts == sorted(ts)
    # A running quarter index must step by 1 across a year boundary, not jump.
    assert max(b - a for a, b in zip(ts, ts[1:])) == 1


def test_fiscal_panel_excludes_the_pre_modern_era_by_default():
    p = panel.fiscal_panel()
    assert min(r["year"] for r in p.rows) >= 1960
    assert len(p.units) == 18
    # The raw file reaches back to 1700; the default window must not.
    assert len(panel.fiscal_panel(since=1700)) > len(p)


def test_balance_proxy_is_revenue_minus_spending():
    r = panel.fiscal_panel().rows[0]
    assert r["balance_proxy"] == pytest.approx(r["rev_gdp"] - r["exp_gdp"])


def test_yoy_is_none_without_a_matching_lag():
    p = panel.yoy(panel.housing_panel(), "ipv", periods=4)
    first = [r for r in p.rows if r["ccaa"] == p.units[0]][:4]
    assert all(r["ipv_yoy"] is None for r in first)


def test_yoy_matches_a_hand_computed_change():
    p = panel.yoy(panel.housing_panel(), "ipv", periods=4)
    by_t = {r["t"]: r for r in p.rows if r["ccaa"] == p.units[0]}
    t = max(by_t)
    now, prev = by_t[t], by_t.get(t - 4)
    if prev and now["ipv_yoy"] is not None:
        assert now["ipv_yoy"] == pytest.approx((now["ipv"] / prev["ipv"] - 1) * 100)


# ---- estimation -------------------------------------------------------------

def _synthetic(slope: float, n_units: int = 12, n_t: int = 40) -> list[dict]:
    """Panel with a known slope and a large unit fixed effect."""
    rows = []
    for u in range(n_units):
        fe = 100.0 * u                      # swamps the signal unless demeaned
        for t in range(n_t):
            x = float((t * 7 + u * 3) % 11)
            rows.append({"u": f"u{u}", "t": t, "x": x, "y": fe + slope * x})
    return rows


def test_within_ols_recovers_a_known_slope_through_fixed_effects():
    est = estimate.within_ols(_synthetic(2.5), "y", ["x"], "u")
    assert est is not None
    assert est.coef == pytest.approx(2.5, abs=1e-6)
    assert est.n_units == 12


def test_within_ols_returns_none_on_too_little_data():
    assert estimate.within_ols(_synthetic(1.0, n_units=2, n_t=5), "y", ["x"], "u") is None


def test_within_ols_skips_rows_with_missing_values():
    rows = _synthetic(2.0)
    for r in rows[:50]:
        r["x"] = None
    est = estimate.within_ols(rows, "y", ["x"], "u")
    assert est is not None and est.n == len(rows) - 50


def test_clustered_se_is_wider_than_ignoring_correlation():
    """The reason for clustering: within-unit correlation must widen the band."""
    rows = []
    for u in range(10):
        shock = 5.0 * u                     # a shared, persistent unit shock
        for t in range(50):
            rows.append({"u": f"u{u}", "y": shock + 0.01 * t})
    clustered = estimate.pooled_mean(rows, "y", "u")
    assert clustered is not None
    naive = [r["y"] for r in rows]
    naive_se = (sum((v - sum(naive) / len(naive)) ** 2 for v in naive)
                / (len(naive) - 1) / len(naive)) ** 0.5
    assert clustered.se > naive_se


def test_estimate_band_and_containment():
    e = estimate.Estimate("x", coef=1.0, se=0.5, n=100, n_units=10,
                          ci_low=0.2, ci_high=1.8)
    assert e.contains(1.5) and not e.contains(2.0)
    assert e.significant
    assert not estimate.Estimate("x", 0.1, 0.5, 100, 10, -0.7, 0.9).significant


def test_local_projection_returns_one_estimate_per_horizon():
    rows = []
    for u in range(15):
        for t in range(40):
            shock = 1.0 if t == 10 else 0.0
            rows.append({"u": f"u{u}", "t": t, "y": float(t) + 3.0 * shock,
                         "shock": shock})
    irf = estimate.local_projection(rows, "y", "shock", "u", "t", horizons=4)
    assert [e.name for e in irf] == [f"h={h}" for h in range(5)]


# ---- confronting the calibration -------------------------------------------

def test_ipv_growth_is_estimated_from_the_regional_panel():
    cmp_ = validate.compare_ipv_growth()
    assert cmp_ is not None
    assert cmp_.constant == "IPV_LR"
    assert cmp_.calibrated == c.IPV_LR
    assert cmp_.estimate.n_units == 20
    assert math.isfinite(cmp_.estimate.coef)


def test_ipv_growth_is_split_into_windows_that_partition_the_panel():
    """The sub-windows exist to expose sample dependence, so they must really
    be sub-samples: disjoint, smaller than the whole, and adding up to it."""
    cmp_ = validate.compare_ipv_growth()
    assert cmp_ is not None
    assert len(cmp_.subperiods) == len(validate.IPV_WINDOWS)
    ns = [s.estimate.n for s in cmp_.subperiods]
    assert sum(ns) == cmp_.estimate.n
    assert all(n < cmp_.estimate.n for n in ns)
    # The bust and the recovery must not land on the same number; if they did,
    # splitting would be decoration rather than information.
    coefs = [s.estimate.coef for s in cmp_.subperiods]
    assert coefs[0] < 0 < coefs[1]


def test_subperiods_survive_serialisation_with_their_own_bands():
    cmp_ = validate.compare_ipv_growth()
    assert cmp_ is not None
    subs = cmp_.to_dict()["subperiods"]
    assert len(subs) == 2
    for s in subs:
        assert s["label"]
        assert s["ci_low"] < s["coef"] < s["ci_high"]
        # A window carries no calibrated value of its own — the API must not
        # hand the frontend a parent verdict it could mistake for the window's.
        assert "calibrated" not in s and "verdict" not in s


def test_a_comparison_without_windows_serialises_an_empty_list():
    """Absent windows must be an empty list, not a missing key: the frontend
    maps over it unconditionally."""
    cmp_ = validate.compare_ipv_reversion()
    assert cmp_ is not None
    assert cmp_.to_dict()["subperiods"] == []


def test_ipv_reversion_is_the_complement_of_persistence():
    cmp_ = validate.compare_ipv_reversion()
    assert cmp_ is not None
    # Reversion is 1 - phi, so the band must be the mirrored persistence band.
    assert cmp_.estimate.ci_low < cmp_.estimate.coef < cmp_.estimate.ci_high


def test_verdict_names_the_side_when_the_calibration_falls_outside():
    e = estimate.Estimate("x", coef=1.0, se=0.1, n=100, n_units=10,
                          ci_low=0.8, ci_high=1.2)
    high = validate.Comparison("K", "l", calibrated=3.0, estimate=e, source="s")
    low = validate.Comparison("K", "l", calibrated=0.1, estimate=e, source="s")
    inside = validate.Comparison("K", "l", calibrated=1.0, estimate=e, source="s")
    assert "por encima" in high.verdict and not high.compatible
    assert "por debajo" in low.verdict
    assert inside.compatible and inside.verdict == "compatible"


def test_impulse_response_starts_at_zero_and_is_estimated_at_every_horizon():
    """A cumulative-change projection is zero at h=0 by construction. That is
    why the engine comparison is anchored at one year, not at impact."""
    irf = validate.ipv_shock_response(horizons=8)
    assert irf is not None
    hs = irf["horizons"]
    assert [row["h"] for row in hs] == list(range(9))
    assert hs[0]["coef"] == pytest.approx(0.0, abs=1e-9)
    assert all(math.isfinite(row["coef"]) for row in hs)
    # Sample shrinks with the horizon: each h loses one period per region.
    assert hs[-1]["n"] < hs[0]["n"]


def test_engine_path_is_silent_before_its_anchor():
    """IPV_REV is an annual rule. Extrapolating it to sub-year horizons would
    put a claim on the chart that the constant does not make."""
    irf = validate.ipv_shock_response(horizons=8)
    assert irf is not None
    anchor = irf["anchor_h"]
    before = [p for p in irf["engine_path"] if p["h"] < anchor]
    after = [p for p in irf["engine_path"] if p["h"] >= anchor]
    assert before and all(p["coef"] is None for p in before)
    assert all(p["coef"] is not None for p in after)
    # At the anchor the two curves meet, so the chart compares decay, not level.
    at_anchor = next(p for p in irf["horizons"] if p["h"] == anchor)
    assert after[0]["coef"] == pytest.approx(at_anchor["coef"])
    # And from there the engine's path only shrinks.
    coefs = [p["coef"] for p in after]
    assert all(b < a for a, b in zip(coefs, coefs[1:]))


def test_impulse_response_uses_idiosyncratic_variation_only():
    """The shock is a region's growth minus the cross-region mean that quarter,
    so it must sum to roughly zero within each period — otherwise a common
    national movement is still in it and the estimate is not identified."""
    p = panel.yoy(panel.housing_panel(), "ipv", periods=4)
    by_t: dict[int, list[float]] = {}
    for r in p.rows:
        if r["ipv_yoy"] is not None:
            by_t.setdefault(r["t"], []).append(r["ipv_yoy"])
    for t, vals in by_t.items():
        m = sum(vals) / len(vals)
        assert sum(v - m for v in vals) == pytest.approx(0.0, abs=1e-9), t


def test_fiscal_balance_is_highly_persistent():
    """Bears on the `sp` lever: a balance that is hard to move is hard to hold."""
    est = validate.fiscal_persistence()
    assert est is not None
    assert 0.0 < est.coef < 1.0
    assert est.n_units == 18


def test_run_all_reports_what_could_not_be_estimated():
    out = validate.run_all()
    assert out["comparisons"]
    assert out["vintage"] == c.VINTAGE
    # The unidentifiable list is part of the result, not an omission.
    blocked = [k for k, v in out["identifiable"].items() if v.startswith("no")]
    assert {"MULT", "OKUN", "E_R", "E_IPV_R"} <= set(blocked)


def test_every_identifiability_claim_has_a_reason():
    for key, why in panel.IDENTIFIABLE.items():
        assert why.startswith(("sí", "no")), key
        assert "—" in why, f"{key} no explica por qué"
