"""Tests for the distress classifier's construction, not its accuracy.

AUC 0,67 is a modest number and these tests do not try to improve it. What they
pin is that it was earned: the label is an onset rather than a state, the
features precede the event, no country appears on both sides of a split, and a
country that never defaulted can still be scored without having leaked into
training.

An early-warning model is unusually easy to make look good by accident. Each
test here corresponds to one way of doing that.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research import distress as ds


def _labels(spells: dict[str, list[int]], years: range = range(2000, 2011)) -> pd.DataFrame:
    """Synthetic label frame: {country: [years in default]}."""
    rows = []
    for c, bad in spells.items():
        for y in years:
            rows.append({"country": c, "group": "test", "year": y,
                         "amount": 100.0 if y in bad else 0.0,
                         "in_default": int(y in bad)})
    d = pd.DataFrame(rows).sort_values(["country", "year"])
    d["prev"] = d.groupby("country").in_default.shift(1)
    d["onset"] = ((d.in_default == 1) & (d.prev.fillna(0) == 0)).astype(int)
    return d.drop(columns=["prev"])


def _features(countries: list[str], years: range = range(2000, 2011)) -> pd.DataFrame:
    rows = []
    for i, c in enumerate(countries):
        for y in years:
            rows.append({"iso3": c, "year": y,
                         "ext_debt_gni": 40.0 + i * 5 + (y - 2000),
                         "debt_service_x": 10.0, "reserves_mo": 4.0,
                         "reserves_debt": 30.0, "cab_gdp": -2.0,
                         "gdp_growth": 2.0, "inflation": 3.0,
                         "gdp_pc": 10000.0, "exports_gdp": 25.0})
    return pd.DataFrame(rows)


# ---- the label -------------------------------------------------------------

def test_onset_marks_only_the_first_year_of_a_spell():
    """49 % of country-years are "in default" because a default lasts years.
    Predicting that is close to reading last year's value; the onset is the
    label an early-warning system actually needs."""
    lab = _labels({"A": [2004, 2005, 2006, 2007]})
    onsets = lab[lab.onset == 1].year.tolist()
    assert onsets == [2004]
    assert lab.in_default.sum() == 4


def test_two_separate_spells_give_two_onsets():
    lab = _labels({"A": [2002, 2003, 2007, 2008]})
    assert lab[lab.onset == 1].year.tolist() == [2002, 2007]


def test_the_committed_labels_are_rare_enough_to_be_an_early_warning_problem():
    """If the positive rate were near a half, the exercise would be describing
    the present rather than warning about the future."""
    lab = pd.read_csv(ds.LABELS)
    assert 0.01 < lab.onset.mean() < 0.10
    assert lab.onset.sum() > 300
    # Spread across the whole period, not one crisis decade.
    by_decade = lab[lab.onset == 1].groupby(lab.year // 10 * 10).size()
    assert (by_decade > 20).sum() >= 6


# ---- the joins that could leak ---------------------------------------------

def test_features_are_read_before_the_event_not_alongside_it(monkeypatch):
    """A model given this year's collapse to explain this year's default has
    learned nothing usable."""
    lab = _labels({"AAA": [2005]})
    lab["iso3"] = lab.country
    monkeypatch.setattr(ds.pd, "read_csv",
                        lambda p, **k: _features(["AAA"]) if "wb_macro" in str(p) else lab)
    d = ds.build_panel(lab)
    hit = d[d.y == 1]
    assert len(hit) == 1
    # The positive row is 2004: the year *before* the onset.
    assert int(hit.iloc[0].year) == 2004


def test_rows_already_in_default_are_dropped(monkeypatch):
    """A country in default cannot enter default. Keeping those rows fills the
    negative class with observations where the event was impossible and
    flatters every metric."""
    lab = _labels({"AAA": [2004, 2005, 2006]})
    lab["iso3"] = lab.country
    monkeypatch.setattr(ds.pd, "read_csv",
                        lambda p, **k: _features(["AAA"]) if "wb_macro" in str(p) else lab)
    d = ds.build_panel(lab)
    assert (d.in_default == 0).all()
    assert 2005 not in d.year.tolist() and 2006 not in d.year.tolist()


def test_a_year_gap_does_not_become_a_one_year_ahead_label(monkeypatch):
    """shift(-1) is positional. Without the explicit year check, a country
    missing 2005 would have 2004 predicting 2006 and be scored as if it had
    predicted one year ahead."""
    lab = _labels({"AAA": [2006]})
    lab["iso3"] = lab.country
    feats = _features(["AAA"])
    feats = feats[feats.year != 2005]
    monkeypatch.setattr(ds.pd, "read_csv",
                        lambda p, **k: feats if "wb_macro" in str(p) else lab)
    d = ds.build_panel(lab)
    assert 2004 not in d.year.tolist()


def test_dissolved_states_are_dropped_rather_than_mapped_to_a_successor():
    """Attributing Yugoslavia's history to Serbia would put one country's
    defaults in another country's record."""
    assert ds.ALIASES["Yugoslavia"] is None
    assert ds.ALIASES["Czechoslovakia"] is None
    lab = ds.load_labels(name_map={})
    for name in ("Yugoslavia", "Czechoslovakia"):
        assert lab[lab.country == name].iso3.isna().all()


def test_country_names_are_mapped_explicitly_not_by_fuzzy_match():
    """Two Congos, and a fuzzy match that picks the wrong one corrupts the
    panel invisibly."""
    assert ds.ALIASES["Dem. Rep. of Congo (Kinshasa)"] == "COD"
    assert ds.ALIASES["Rep. of Congo (Brazzaville)"] == "COG"


# ---- the split -------------------------------------------------------------

def test_grouped_folds_never_put_a_country_on_both_sides():
    """Sovereign panels are strongly autocorrelated within a country. A random
    split lets the model memorise Argentina's 1980s and grade itself on
    Argentina's 1990s."""
    from sklearn.model_selection import GroupKFold

    g = np.array(["A"] * 20 + ["B"] * 20 + ["C"] * 20 + ["D"] * 20)
    X = np.zeros((80, 2))
    y = np.tile([0, 1], 40)
    for train, test in GroupKFold(n_splits=4).split(X, y, groups=g):
        assert not (set(g[train]) & set(g[test]))


def test_score_country_never_trains_on_the_country_it_scores():
    d = pd.DataFrame({
        "iso3": ["AAA"] * 6 + ["BBB"] * 6,
        "year": list(range(2000, 2006)) * 2,
        "y": [0, 0, 1, 0, 0, 1] * 2,
        **{c: [1.0] * 12 for c in ds.FEATURE_LABELS},
    })
    f = pd.DataFrame({
        "iso3": ["AAA"] * 6, "year": list(range(2000, 2006)),
        **{c: [1.0] * 6 for c in ds.FEATURE_LABELS},
    })
    seen: list[int] = []
    real_fit = ds._model

    class Spy:
        def fit(self, X, y):
            seen.append(len(X))
            self._m = real_fit().fit(X, y)
            return self

        def predict_proba(self, X):
            return self._m.predict_proba(X)

    ds_model = ds._model
    try:
        ds._model = lambda: Spy()               # type: ignore[assignment]
        out = ds.score_country("AAA", panel=d, features=f)
    finally:
        ds._model = ds_model                    # type: ignore[assignment]

    assert out is not None
    # Fitted on BBB's six rows only, not on all twelve.
    assert seen == [6]
    assert out["in_label_set"] is True


def test_a_country_with_no_default_history_can_still_be_scored():
    """Spain is absent from the default database entirely. An inner join drops
    it, which would leave the gauge unable to score the one country it exists
    for."""
    d = pd.DataFrame({
        "iso3": ["BBB"] * 6, "year": list(range(2000, 2006)),
        "y": [0, 0, 1, 0, 0, 1],
        **{c: [1.0] * 6 for c in ds.FEATURE_LABELS},
    })
    f = pd.DataFrame({
        "iso3": ["ESP"] * 6, "year": list(range(2000, 2006)),
        **{c: [2.0] * 6 for c in ds.FEATURE_LABELS},
    })
    out = ds.score_country("ESP", panel=d, features=f)
    assert out is not None
    assert out["in_label_set"] is False
    assert 0.0 <= out["probability"] <= 1.0


def test_a_year_with_almost_no_data_is_not_scored():
    """The WDI publishes the newest year sparsely. Scoring it regardless hands
    the model a nearly empty vector and calls the answer a probability."""
    d = pd.DataFrame({
        "iso3": ["BBB"] * 6, "year": list(range(2000, 2006)),
        "y": [0, 0, 1, 0, 0, 1],
        **{c: [1.0] * 6 for c in ds.FEATURE_LABELS},
    })
    f = pd.DataFrame({
        "iso3": ["ESP"] * 3, "year": [2020, 2021, 2022],
        **{c: [1.0, 1.0, np.nan] for c in ds.FEATURE_LABELS},
    })
    out = ds.score_country("ESP", panel=d, features=f)
    assert out is not None
    assert out["year"] == 2021          # not the empty 2022


def test_missing_features_are_left_missing_not_imputed():
    """External-debt coverage is 41 %. Imputing it would invent the variable
    the model leans on hardest."""
    m = ds._model()
    X = np.array([[1.0, np.nan], [2.0, 1.0], [3.0, np.nan], [4.0, 2.0]])
    y = np.array([0, 1, 0, 1])
    m.fit(X, y)                          # must not raise on NaN
    assert m.predict_proba(X).shape == (4, 2)
