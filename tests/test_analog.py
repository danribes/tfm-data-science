"""Scientific regression checks for descriptive historical matching."""
import numpy as np
import pandas as pd
import pytest
from engine.analog import (
    ANALOG_PANEL, QUERY_FEATURES, _fit_metric, _query_vector,
    find_analogs, structural_diffs, _outcome_trajectory,
)
from engine.levers import Levers, preset_levers
from engine.spain import run_scenario


def test_distance_is_invariant_to_measurement_units():
    # Changing debt from percentage points to a fraction must not change
    # Mahalanobis distance. The previous raw-covariance/z-score mix failed this.
    rng = np.random.default_rng(17)
    x = rng.normal(size=(100, len(QUERY_FEATURES)))
    x[:, 1] += x[:, 0] * .5
    frame = pd.DataFrame(x, columns=QUERY_FEATURES)
    def distance(f):
        stats, inv = _fit_metric(f)
        delta = np.array([(f.iloc[0][k] - f.iloc[1][k]) / stats[k]['std'] for k in QUERY_FEATURES])
        return float(np.sqrt(delta @ inv @ delta))
    expected = distance(frame)
    frame['debt_gdp'] *= .01
    assert distance(frame) == pytest.approx(expected, rel=1e-12)


def test_mahalanobis_matches_raw_coordinate_reference():
    frame = ANALOG_PANEL.dropna(subset=QUERY_FEATURES)
    stats, inv = _fit_metric(frame)
    raw = frame[QUERY_FEATURES].to_numpy()
    difference = raw[0] - raw[1]
    z_difference = difference / np.array([stats[k]['std'] for k in QUERY_FEATURES])
    assert z_difference @ inv @ z_difference == pytest.approx(
        difference @ np.linalg.inv(np.cov(raw.T)) @ difference, rel=1e-9)


def test_query_compares_total_balance_and_selected_year():
    run = run_scenario(preset_levers('S7'))
    q = _query_vector(run, 2040)
    assert q['overall_balance_gdp'] == run['saldo'][14]
    assert q['overall_balance_gdp'] != run['pb'][14]
    assert q['debt_gdp'] == run['b'][14]
    assert 'interest_rate_10y' not in q


def test_analog_schema_and_comparable_complete_matches():
    assert set(QUERY_FEATURES) <= set(ANALOG_PANEL.columns)
    assert 'lending_rate' in ANALOG_PANEL
    for levers in [Levers(), preset_levers('S7')]:
        matches = find_analogs(levers, horizon=10)
        assert len(matches) == 3
        assert [m['rank'] for m in matches] == [1, 2, 3]
        assert [m['distance'] for m in matches] == sorted(m['distance'] for m in matches)
        for m in matches:
            assert m['iso3'] != 'ESP'
            assert m['match_year'] <= 2020
            assert all(m['match_snapshot'][f] is not None for f in QUERY_FEATURES)
            assert m['match_snapshot']['interest_rate_10y'] is None
            assert m['match_snapshot']['r_minus_g'] is None
            assert m['debt_payable_verdict'] == 'not_assessed'
            assert all(p['r_minus_g'] is None for p in m['outcome'])


def test_future_missing_observations_remain_missing():
    points, truncated = _outcome_trajectory('ESP', 2023, 3)
    assert truncated
    assert all(p['truncated'] and p['debt_gdp'] is None for p in points)


def test_unobserved_structural_proxies_are_not_facts():
    row = pd.Series({'emu_member': 0, 'democracy': 10., 'fx_regime': 'fixed', 'ext_debt_share': 42.})
    diffs = {d['dimension']: d for d in structural_diffs(row)}
    for key in ['democracy', 'fx_regime', 'ext_debt_share', 'debt_maturity']:
        assert diffs[key]['direction'] == 'neutral'
        assert diffs[key]['analog_value'] == 'sin datos comparables'
    assert diffs['emu_member']['direction'] == 'diverge'
    assert {'tfp_trend', 'labor_productivity'} <= set(diffs)


def test_missing_macro_rows_cannot_appear_as_average_neighbors(monkeypatch):
    import engine.analog as module
    missing = ANALOG_PANEL.iloc[0].copy()
    missing['iso3'], missing['year'] = 'ZZZ', 2010
    missing['gdp_growth'] = np.nan
    monkeypatch.setattr(module, 'ANALOG_PANEL', pd.concat([ANALOG_PANEL, pd.DataFrame([missing])], ignore_index=True))
    assert all(m['iso3'] != 'ZZZ' for m in find_analogs(Levers()))
