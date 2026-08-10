"""Tests for the regime detector: the machinery, and the history it must find.

Unusually, some history IS pinned here. The whole value of an unsupervised
regime model in this app is that it recovers episodes everyone can verify —
the post-war fiscal collapse, 2008. A fit that drifts away from those under a
refactor is broken no matter how good its likelihood looks, so the recognisable
episodes are asserted, with tolerance at the edges.
"""
from __future__ import annotations

import numpy as np
import pytest

from research import regimes as rg


def _synthetic(n1: int = 60, n2: int = 25, seed: int = 0) -> np.ndarray:
    """Calm around 0 with tight noise, then a wild negative regime, then calm."""
    r = np.random.default_rng(seed)
    calm1 = r.normal(0.0, 0.4, n1)
    wild = r.normal(-6.0, 2.5, n2)
    calm2 = r.normal(0.0, 0.4, n1)
    return np.concatenate([calm1, wild, calm2])


def test_recovers_a_planted_regime():
    x = _synthetic()
    fit = rg.fit_hmm(x)
    flags = np.array(fit["viterbi_crisis"])
    # The middle block is the crisis; edges may wobble by a step or two.
    assert flags[65:80].all()
    assert not flags[:55].any()
    assert not flags[-55:].any()


def test_crisis_is_the_high_variance_state_not_an_index():
    """EM may converge with the states in either order. The label must follow
    the property, or the same data could paint calm red on a different run."""
    x = _synthetic()
    fit = rg.fit_hmm(x)
    assert fit["var"][fit["crisis_state"]] == max(fit["var"])


def test_fit_is_deterministic():
    x = _synthetic()
    a, b = rg.fit_hmm(x), rg.fit_hmm(x)
    assert a["viterbi_crisis"] == b["viterbi_crisis"]
    assert a["mu"] == b["mu"]


def test_posteriors_are_probabilities_and_agree_with_viterbi_in_the_core():
    x = _synthetic()
    fit = rg.fit_hmm(x)
    p = np.array(fit["p_crisis"])
    assert ((p >= 0) & (p <= 1)).all()
    # Deep inside the planted crisis the smoothed posterior should be sure.
    assert p[68:77].min() > 0.9


def test_a_short_series_is_refused():
    with pytest.raises(AssertionError):
        rg.fit_hmm(np.zeros(10))


def test_episodes_extracts_contiguous_runs():
    eps = rg.episodes([2000, 2001, 2002, 2003, 2004, 2005],
                      [0, 1, 1, 0, 0, 1])
    assert eps == [{"from": 2001, "to": 2002}, {"from": 2005, "to": 2005}]


def test_episode_open_at_the_end_closes_on_the_last_period():
    eps = rg.episodes(["a", "b", "c"], [0, 1, 1])
    assert eps == [{"from": "b", "to": "c"}]


# ---- the history the fit must recover ---------------------------------------

def test_fiscal_regimes_find_the_recognisable_episodes():
    fy, fx = rg.fiscal_series()
    fit = rg.fit_hmm(fx)
    eps = rg.episodes(fy, fit["viterbi_crisis"])

    def covered(year: int) -> bool:
        return any(e["from"] <= year <= e["to"] for e in eps)

    # The post-Civil-War collapse and the 2008 crisis. The war years 1936-39
    # are absent from the source itself — the state published no accounts — so
    # the aftermath is what an honest fit can find.
    assert covered(1941) and covered(1945)
    assert covered(2009) and covered(2012) and covered(2020)
    # And the calm that a variance-based state must leave alone.
    assert not covered(1901)
    assert not covered(1960)


def test_civil_war_years_are_missing_from_the_source_not_mislabelled():
    fy, _ = rg.fiscal_series()
    assert 1935 in fy and 1940 in fy
    assert not any(y in fy for y in (1936, 1937, 1938, 1939))


def test_housing_regime_is_the_crash_and_only_the_crash():
    hy, hx = rg.housing_series()
    fit = rg.fit_hmm(hx)
    eps = rg.episodes(hy, fit["viterbi_crisis"])
    assert len(eps) >= 1
    first = eps[0]
    assert first["from"].startswith("2008")
    assert first["to"].startswith(("2013", "2014"))
    # The 2015-2026 recovery must not be painted as crisis.
    joined = " ".join(f"{e['from']}–{e['to']}" for e in eps)
    assert "2019" not in joined and "2024" not in joined


def test_committed_artifact_matches_the_module():
    import json

    p = rg.OUT / "regimes.json"
    assert p.exists()
    d = json.loads(p.read_text(encoding="utf-8"))
    assert {"fiscal", "housing", "method", "seed"} <= set(d)
    for k in ("fiscal", "housing"):
        s = d[k]
        assert len(s["periods"]) == len(s["values"]) == len(s["p_crisis"])
        assert s["episodes"], k
