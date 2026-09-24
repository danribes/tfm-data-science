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


def test_every_searchable_country_has_a_spanish_name():
    """The card printed the ISO code when a country had no name: «LBR · 2004»
    instead of Liberia. Every code the search can return now has one."""
    from engine import analog
    codes = set(analog.ANALOG_PANEL.iso3)
    assert sorted(c for c in codes if c not in analog._NAMES) == []
    assert analog._NAMES["LBR"] == "Liberia"


def test_no_regional_aggregate_is_searchable():
    """WEO regions with three-letter codes (the …Q family, EDE, MAE, OAE) are
    not countries. GNQ and IRQ end in Q too and are."""
    from engine import analog
    codes = set(analog.ANALOG_PANEL.iso3)
    assert not codes & analog.AGGREGATES
    assert {"GNQ", "IRQ"} <= codes


def test_closeness_cutoffs_match_the_panel():
    """The card calls a match close up to 0,6 and distant past 2,5
    (frontend/src/components/AnalogCard.tsx). Those come from the panel: the
    distance from a country-year to its nearest neighbour in another country
    is under 0,6 for 90 % of them, and 2,5 is about the 99th percentile."""
    import numpy as np
    from engine import analog as a
    p = a.ANALOG_PANEL[(a.ANALOG_PANEL.iso3 != "ESP") & (a.ANALOG_PANEL.year <= 2020)]
    p = p.dropna(subset=a.QUERY_FEATURES)
    z = np.array([[a._normalize(v, f) for f, v in zip(a.QUERY_FEATURES, row)]
                  for row in p[a.QUERY_FEATURES].to_numpy()])
    iso = p.iso3.to_numpy()
    rng = np.random.default_rng(0)
    nn = []
    for i in rng.choice(len(z), size=600, replace=False):
        diff = z - z[i]
        d = np.sqrt(np.maximum(0.0, np.einsum("ij,jk,ik->i", diff, a._COV_INV, diff)))
        nn.append(d[iso != iso[i]].min())
    p90, p99 = np.percentile(nn, [90, 99])
    assert p90 <= 0.6
    assert 1.8 <= p99 <= 3.2
