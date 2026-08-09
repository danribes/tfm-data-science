"""Tests for the pre-registered rolling-origin protocol.

What is fixed here is the protocol, not the scores. A backtest is only worth
anything if the rules cannot move once a candidate exists, so these tests pin
the rules: the held-out tail stays held out, the MASE scale is computed on the
training window, the win rule counts what it says it counts.

The measured MASE of any method belongs to the data and is free to change with
the vintage. It is printed by `python -m research.backtest`, not asserted.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research import backtest as bt


def _series(n: int = 72, start: str = "2008Q1", slope: float = 1.0) -> pd.Series:
    idx = pd.period_range(start, periods=n, freq="Q")
    return pd.Series(100.0 + slope * np.arange(n, dtype=float), index=idx)


# ---- the held-out tail -----------------------------------------------------

def test_nothing_from_the_test_period_is_ever_scored():
    """The single property that makes the final evaluation meaningful. If one
    2024 observation leaks in, the test set is no longer untouched and no later
    result about it can be believed."""
    df = bt.backtest({"X": _series()}, {"drift": bt.drift})
    scored = [pd.Period(o, freq="Q") + int(h) for o, h in zip(df.origen, df.h)]
    assert scored, "el backtest no puntuó nada"
    assert max(scored) < bt.TEST_START


def test_late_origins_are_truncated_per_horizon_not_dropped_whole():
    """An origin contributes exactly the horizons that land before the test
    set, which for the last few is fewer than eight and for 2023Q4 is none at
    all — its h=1 is already 2024Q1. Truncating per origin instead of per
    horizon would throw away legitimate observations from 2022 and 2023."""
    df = bt.backtest({"X": _series()}, {"drift": bt.drift})
    assert df[df.origen == "2023Q4"].empty          # even h=1 is the test set
    assert df[df.origen == "2023Q3"].h.max() == 1   # h=1 → 2023Q4, still fair
    assert df[df.origen == "2022Q4"].h.max() == 4   # h=5 would reach 2024Q1
    assert df[df.origen == "2019Q4"].h.max() == bt.H


def test_every_origin_in_the_grid_is_used():
    df = bt.backtest({"X": _series()}, {"drift": bt.drift})
    used = {pd.Period(o, freq="Q") for o in df.origen}
    # Origins whose whole horizon falls in the test set contribute nothing.
    expected = {o for o in bt.ORIGINS if o + 1 < bt.TEST_START}
    assert used == expected


# ---- the metric ------------------------------------------------------------

def test_mase_scale_uses_only_the_training_window():
    """Scaling by the full series would leak post-origin volatility into the
    denominator and make late origins look easier than they were."""
    s = _series()
    early = bt.mase_scale(s[s.index <= pd.Period("2019Q4", freq="Q")])
    full = bt.mase_scale(s)
    assert early == pytest.approx(4.0)     # slope 1.0 → 4 per year, exactly
    assert full == pytest.approx(4.0)
    # And the harness must call it per origin, not once per series.
    df = bt.backtest({"X": _series(slope=1.0)}, {"drift": bt.drift})
    assert df.scale.notna().all() and (df.scale > 0).all()


def test_a_perfect_forecaster_scores_zero():
    s = _series()

    def oracle(train: pd.Series, h: int) -> list[float]:
        nxt = [train.index[-1] + k for k in range(1, h + 1)]
        return [float(s.loc[p]) if p in s.index else np.nan for p in nxt]

    df = bt.backtest({"X": s}, {"oracle": oracle})
    assert df.ase.max() == pytest.approx(0.0, abs=1e-9)


def test_drift_is_exact_on_a_straight_line():
    """A sanity anchor on the benchmark itself: extending a constant slope
    should reproduce a linear series to the last decimal."""
    df = bt.backtest({"X": _series(slope=2.0)}, {"drift": bt.drift})
    assert df.ae.max() == pytest.approx(0.0, abs=1e-9)


def test_non_finite_forecasts_are_dropped_not_scored_as_zero():
    def broken(train: pd.Series, h: int) -> list[float]:
        return [np.nan] * h

    df = bt.backtest({"X": _series()}, {"drift": bt.drift, "broken": broken})
    assert "broken" not in set(df.metodo)
    assert "drift" in set(df.metodo)


# ---- the win rule ----------------------------------------------------------

def _two_method_frame(better_in: int, total: int = 17) -> pd.DataFrame:
    rows = []
    for i in range(total):
        cand = 0.5 if i < better_in else 1.5
        for h in (1, 2, 3, 4, 5, 6, 7, 8):
            for name, ase in (("cand", cand), ("drift", 1.0)):
                rows.append({"ccaa": f"R{i}", "origen": "2020Q1", "h": h,
                             "metodo": name, "ase": ase, "y": 1.0, "yhat": 1.0,
                             "scale": 1.0, "ae": 0.0, "e": 0.0})
    return pd.DataFrame(rows)


def test_the_win_rule_needs_twelve_of_seventeen():
    assert bt.judge(_two_method_frame(12), "cand").wins is True
    assert bt.judge(_two_method_frame(11), "cand").wins is False


def test_the_rule_is_judged_on_short_horizons_only():
    """h 5-8 is reported but was never part of the bar. A candidate that only
    wins late must still lose."""
    df = _two_method_frame(0)
    df.loc[(df.metodo == "cand") & (df.h >= 5), "ase"] = 0.01
    v = bt.judge(df, "cand")
    assert v.wins is False
    assert v.mase_candidate_long < v.mase_drift_long   # and it is still reported


def test_nacional_does_not_vote():
    """It is an aggregate of the same regions; counting it would score part of
    the panel twice and make the denominator 18."""
    df = _two_method_frame(17)
    nac = df[df.ccaa == "R0"].copy()
    nac["ccaa"] = "Nacional"
    v = bt.judge(pd.concat([df, nac], ignore_index=True), "cand")
    assert v.total_ccaa == 17


def test_the_verdict_says_which_way_it_went():
    d = bt.judge(_two_method_frame(17), "cand").to_dict()
    assert d["verdict"] == "bate al drift"
    assert d["required"] == bt.WIN_MIN_CCAA and d["horizon"] == bt.WIN_HORIZON
    assert bt.judge(_two_method_frame(3), "cand").to_dict()["verdict"] == "no bate al drift"


# ---- the panels ------------------------------------------------------------

def test_the_spanish_panel_is_the_seventeen_the_rule_counts():
    s = bt.load_series()
    assert "Nacional" in s
    assert len(s) - 1 == 17
    # Ceuta and Melilla have no affordability ratio and are out by construction.
    assert "Ceuta" not in s and "Melilla" not in s


def test_the_training_corpus_contains_no_spanish_series():
    """The property the whole transfer argument rests on. If a Spanish series
    were in here, beating drift on Spain would prove nothing."""
    g = bt.load_global_panel()
    assert set(g.fuente.unique()) <= {"fhfa_metro", "fhfa_state", "zillow", "uk"}
    assert g.serie.nunique() > 1500
    spanish = {c.lower() for c in bt.load_series()}
    assert not {s.lower() for s in g.serie.unique()} & spanish
