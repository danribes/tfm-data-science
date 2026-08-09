"""Tests for the global transfer model's honesty, not its accuracy.

The model lost against drift on the pre-registered rule, and these tests do not
try to defend it. What they defend is the claim that the loss was measured
fairly — because a transfer model that quietly saw the future, or quietly saw
Spain, would be worth less than no model at all even if it had won.

Training is not exercised here: a network is slow and stochastic, and the parts
worth pinning are deterministic. `python -m research.dl_global` runs the real
thing and writes docs/eval/t1-dl-global.json.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research import backtest as bt
from research import dl_global as dg


def _panel(series: dict[str, tuple[int, int, int]]) -> pd.DataFrame:
    """Synthetic foreign panel: {name: (start_year, start_q, n_quarters)}."""
    rows = []
    for name, (y0, q0, n) in series.items():
        for i in range(n):
            p = y0 * 4 + (q0 - 1) + i
            rows.append({"fuente": "test", "serie": name,
                         "anyo": p // 4, "quarter": p % 4 + 1,
                         "valor": 100.0 * (1.01 ** i)})
    return pd.DataFrame(rows)


# ---- the temporal cut ------------------------------------------------------

def test_no_training_target_reaches_past_the_cutoff(monkeypatch):
    """The cut that matters. Without it the model learns the 2020-2023 world
    from Ohio before being asked to forecast it in Madrid, and beating drift
    would prove nothing about transfer."""
    monkeypatch.setattr(dg.bt, "load_global_panel",
                        lambda: _panel({"A": (2000, 1, 120)}))
    X, Y = dg.training_windows()
    assert len(X) > 0
    # The last usable window starts W steps in and its target spans H more; the
    # count is what pins the boundary, since the panel runs well past 2019Q3.
    d = _panel({"A": (2000, 1, 120)})
    p = (d.anyo * 4 + d.quarter).to_numpy()
    usable = sum(1 for i in range(dg.W, len(p) - 1 - dg.H + 1)
                 if p[i + dg.H] <= dg.CUTOFF)
    assert len(X) == usable


def test_a_panel_entirely_after_the_cutoff_yields_nothing(monkeypatch):
    monkeypatch.setattr(dg.bt, "load_global_panel",
                        lambda: _panel({"A": (2021, 1, 60)}))
    X, Y = dg.training_windows()
    assert len(X) == 0 and len(Y) == 0


def test_the_cutoff_sits_one_quarter_before_the_first_validation_origin():
    """2019Q3, with the first origin at 2019Q4. Stated as an equality so that
    moving one without the other fails here rather than silently."""
    assert dg.CUTOFF == 2019 * 4 + 3
    first_origin = bt.ORIGINS[0]
    assert dg.CUTOFF + 1 == first_origin.year * 4 + first_origin.quarter
    # And it must be reported as the quarter it actually is.
    assert dg._as_quarter(dg.CUTOFF) == "2019Q3"
    assert dg._as_quarter(dg.CUTOFF + 1) == "2019Q4"


# ---- window construction ---------------------------------------------------

def test_windows_have_the_declared_shape(monkeypatch):
    monkeypatch.setattr(dg.bt, "load_global_panel",
                        lambda: _panel({"A": (2000, 1, 80)}))
    X, Y = dg.training_windows()
    assert X.shape[1] == dg.W
    assert Y.shape[1] == dg.H
    assert X.dtype == np.float32 and Y.dtype == np.float32


def test_targets_are_cumulative_so_each_horizon_is_a_level_not_a_step(monkeypatch):
    """Y[k] is the log change from the origin to t+k+1. A per-step target would
    force the forecaster to compound its own errors."""
    monkeypatch.setattr(dg.bt, "load_global_panel",
                        lambda: _panel({"A": (2000, 1, 80)}))
    _, Y = dg.training_windows()
    # The synthetic series grows at a constant 1 % a quarter.
    step = np.log(1.01)
    assert Y[0] == pytest.approx(np.cumsum([step] * dg.H), rel=1e-4)


def test_series_with_a_gap_are_skipped_not_interpolated(monkeypatch):
    """A fabricated quarter inside a 16-step window teaches a transition that
    never happened."""
    good = _panel({"A": (2000, 1, 80)})
    broken = _panel({"B": (2000, 1, 80)})
    broken = broken[broken.quarter != 3]          # punch holes in B
    monkeypatch.setattr(dg.bt, "load_global_panel",
                        lambda: pd.concat([good, broken], ignore_index=True))
    n_both = len(dg.training_windows()[0])

    monkeypatch.setattr(dg.bt, "load_global_panel", lambda: good)
    n_good = len(dg.training_windows()[0])
    assert n_both == n_good


def test_short_series_contribute_nothing(monkeypatch):
    monkeypatch.setattr(dg.bt, "load_global_panel",
                        lambda: _panel({"A": (2000, 1, dg.W + dg.H)}))
    assert len(dg.training_windows()[0]) == 0


def test_extreme_moves_are_clipped(monkeypatch):
    d = _panel({"A": (2000, 1, 80)})
    d.loc[40, "valor"] = 1e6                       # one absurd print
    monkeypatch.setattr(dg.bt, "load_global_panel", lambda: d)
    X, Y = dg.training_windows()
    assert np.abs(X).max() <= dg.CLIP + 1e-6


# ---- the forecaster contract ----------------------------------------------

def test_forecaster_matches_the_harness_signature():
    """It has to be pluggable into the same grid as a three-line drift rule,
    with no special path through the harness."""
    class Flat:
        def __call__(self, x):
            import torch
            return torch.zeros((x.shape[0], dg.H))

    f = dg.make_forecaster(Flat())
    idx = pd.period_range("2010Q1", periods=40, freq="Q")
    s = pd.Series(np.linspace(100, 140, 40), index=idx)
    out = f(s, 8)
    assert len(out) == 8
    # A zero cumulative log change means the level is held flat at the last obs.
    assert out == pytest.approx([float(s.iloc[-1])] * 8)


def test_forecaster_declines_rather_than_guesses_on_a_short_history():
    class Flat:
        def __call__(self, x):
            raise AssertionError("no debería llegar a llamarse")

    f = dg.make_forecaster(Flat())
    idx = pd.period_range("2010Q1", periods=dg.W, freq="Q")
    out = f(pd.Series(np.arange(1.0, dg.W + 1.0), index=idx), 8)
    assert len(out) == 8 and all(np.isnan(v) for v in out)


def test_a_declining_forecaster_is_dropped_by_the_harness():
    """NaNs must not be scored as anything — least of all as zero error."""
    idx = pd.period_range("2008Q1", periods=72, freq="Q")
    s = pd.Series(100.0 + np.arange(72), index=idx)

    def refuses(train, h):
        return [float("nan")] * h

    df = bt.backtest({"X": s}, {"drift": bt.drift, "refuses": refuses})
    assert "refuses" not in set(df.metodo)
