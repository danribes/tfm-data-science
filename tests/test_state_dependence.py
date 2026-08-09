"""Tests for the state-dependence module's construction.

The headline result is a null — the slope difference between debt regimes is
not distinguishable from zero — and these tests protect the machinery that
produced it, because a null from broken machinery is worth nothing. Outcome
strictly in the future, compounding rather than summing, gaps invalidating the
window, and a verdict that comes from the bootstrap interval alone.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research import state_dependence as sd


def _wb(rows: list[dict]) -> pd.DataFrame:
    base = {"ext_debt_gni": 40.0, "debt_service_x": 10.0, "reserves_mo": 4.0,
            "reserves_debt": 30.0, "cab_gdp": -1.0, "gdp_growth": 2.0,
            "inflation": 3.0, "gdp_pc": 10000.0, "exports_gdp": 25.0,
            "gov_debt_gdp": np.nan, "real_rate": 2.0}
    return pd.DataFrame([{**base, **r} for r in rows])


def _panel_files(monkeypatch, wb: pd.DataFrame, imf: pd.DataFrame) -> None:
    def fake_read(path, **kw):
        return wb if "wb_macro" in str(path) else imf
    monkeypatch.setattr(sd.pd, "read_csv", fake_read)


def test_outcome_is_strictly_future_and_compounded(monkeypatch):
    """y_fwd at year t must use growth at t+1..t+3 only, compounded — three
    years of 10 % is 33,1 %, and at crisis magnitudes summing is not a
    rounding error."""
    # 1999 exists only so that 2000 has a rate change; the first year of any
    # series is dropped by construction (its diff is undefined).
    wb = _wb([{"iso3": "AAA", "year": y, "gdp_growth": g}
              for y, g in [(1999, 0.0), (2000, 0.0), (2001, 10.0), (2002, 10.0),
                           (2003, 10.0), (2004, 5.0)]])
    imf = pd.DataFrame({"iso3": ["AAA"] * 6, "year": range(1999, 2005),
                        "debt_gdp": [50.0] * 6})
    _panel_files(monkeypatch, wb, imf)
    d = sd.build_panel()
    row = d[d.year == 2000]
    assert len(row) == 1
    assert float(row.y_fwd.iloc[0]) == pytest.approx(33.1, abs=0.01)


def test_a_gap_in_the_years_invalidates_the_window(monkeypatch):
    """shift(-k) is positional: without the consecutive-year check, a country
    missing 2002 would have 2000's outcome computed from 2001, 2003 and 2004
    and scored as if they were adjacent."""
    wb = _wb([{"iso3": "AAA", "year": y} for y in (2000, 2001, 2003, 2004, 2005)])
    imf = pd.DataFrame({"iso3": ["AAA"] * 5, "year": [2000, 2001, 2003, 2004, 2005],
                        "debt_gdp": [50.0] * 5})
    _panel_files(monkeypatch, wb, imf)
    d = sd.build_panel()
    assert 2000 not in d.year.tolist()
    assert 2001 not in d.year.tolist()


def test_rows_missing_any_feature_are_dropped(monkeypatch):
    wb = _wb([{"iso3": "AAA", "year": y} for y in range(2000, 2008)])
    wb.loc[wb.year == 2001, "inflation"] = np.nan
    imf = pd.DataFrame({"iso3": ["AAA"] * 8, "year": range(2000, 2008),
                        "debt_gdp": [50.0] * 8})
    _panel_files(monkeypatch, wb, imf)
    d = sd.build_panel()
    assert 2001 not in d.year.tolist()


def test_the_first_year_has_no_rate_change_and_is_dropped(monkeypatch):
    wb = _wb([{"iso3": "AAA", "year": y} for y in range(2000, 2008)])
    imf = pd.DataFrame({"iso3": ["AAA"] * 8, "year": range(2000, 2008),
                        "debt_gdp": [50.0] * 8})
    _panel_files(monkeypatch, wb, imf)
    d = sd.build_panel()
    assert d.year.min() == 2001


def test_slope_recovers_a_known_linear_relation():
    rng = np.random.default_rng(0)
    x = rng.normal(size=400)
    b, se = sd._slope(x, -0.45 * x + rng.normal(scale=1e-3, size=400))
    assert b == pytest.approx(-0.45, abs=0.01)
    assert se < 0.01


def test_slope_declines_on_too_few_points():
    b, se = sd._slope(np.arange(5.0), np.arange(5.0))
    assert np.isnan(b) and np.isnan(se)


def test_regimes_are_the_recognisable_thresholds():
    """60 is the treaty reference and 90 the literature's danger line. They
    are pinned so a refactor cannot quietly move them to values that optimise
    the contrast."""
    (l0, h0, _), (l1, h1, _), (l2, h2, _) = sd.REGIMES
    assert (l0, h0) == (0.0, 60.0)
    assert (l1, h1) == (60.0, 90.0)
    assert l2 == 90.0 and np.isinf(h2)


def test_verdict_comes_from_the_bootstrap_interval_alone():
    """The OLS errors on the SHAP scatter treat model outputs as data; the
    claim must not rest on them."""
    kw = dict(n=100, n_countries=10, years=(1990, 2020), r2_grouped=0.0,
              r2_std=0.1, regimes=[], engine_e_r=0.45, importance=[], n_boot=60)
    assert sd.Result(**kw, diff_ci=(0.01, 0.09)).state_dependent is True
    assert sd.Result(**kw, diff_ci=(-0.09, -0.01)).state_dependent is True
    assert sd.Result(**kw, diff_ci=(-0.03, 0.05)).state_dependent is False
    assert sd.Result(**kw, diff_ci=(float("nan"), float("nan"))).state_dependent is False


def test_shap_attributions_add_up_to_the_prediction():
    """The property the whole method rests on: SHAP contributions plus the
    expected value must equal the model output, or the twin chart lies."""
    import shap

    rng = np.random.default_rng(1)
    X = rng.normal(size=(300, 4))
    y = 2.0 * X[:, 0] + X[:, 1] * X[:, 2] + rng.normal(scale=0.1, size=300)
    m = sd._model().fit(X, y)
    ex = shap.TreeExplainer(m)
    sv = ex.shap_values(X[:20])
    assert np.allclose(sv.sum(axis=1) + ex.expected_value, m.predict(X[:20]), atol=1e-6)


def test_the_payload_declares_why_spain_is_absent():
    kw = dict(n=100, n_countries=10, years=(1990, 2020), r2_grouped=0.0,
              r2_std=0.1, regimes=[], engine_e_r=0.45, importance=[],
              diff_ci=(-0.1, 0.1), n_boot=60)
    payload = sd.Result(**kw).to_dict()
    assert "España" in payload["spain_excluded_reason"]
    assert "WDI" in payload["spain_excluded_reason"]


def test_the_committed_artifact_matches_the_schema():
    import json

    p = sd.OUT / "state_dependence.json"
    assert p.exists()
    d = json.loads(p.read_text(encoding="utf-8"))
    assert {"regimes", "importance", "diff_ci", "state_dependent",
            "r2_grouped", "engine_e_r", "spain_excluded_reason"} <= set(d)
    assert len(d["regimes"]) == 3
    # The committed run found no distinguishable difference; if a regeneration
    # flips that, this fails and the flip gets reviewed rather than shipped.
    assert d["state_dependent"] is False
