"""Crisis and calm, detected rather than annotated by hand.

A two-state Gaussian hidden Markov model over Spain's fiscal balance
(1850-2025) and over national house-price growth. The point is pedagogical and
it is the app's own thesis: fiscal history is not a line that wobbles, it is
long calm interrupted by episodes — 1898, the Civil War, 2008-2013, COVID —
and a debt path should be read against that rhythm, not against an average.

The HMM is written out in numpy rather than imported, for the same reason
research/estimate.py hand-rolls its OLS: a reviewer can read exactly what was
computed. Two states, Gaussian emissions, EM with a log-space forward-backward
pass, Viterbi for the displayed path. ~100 lines, no library.

What keeps it honest:

  states are labelled by their properties, not their index — the crisis state
      is whichever fitted state has the higher emission variance. EM is free to
      converge with the states swapped, and without this rule the same data
      could paint calm red on one run and crisis red on another.

  the displayed intervals come from Viterbi, the confidence from the smoothed
      posteriors. Viterbi gives clean episodes; posteriors say how sure the
      model is inside them. Showing Viterbi alone would overstate certainty.

  detected episodes are validated against history in the tests — a model that
      does not find the post-Civil-War fiscal collapse or the 2008 crisis is
      wrong regardless of its likelihood. (The war years themselves, 1936-39,
      are absent from the source: the state published no accounts. The model
      finds the aftermath, 1940-50, because that is what the data contains.)

    python -m research.regimes
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold"
OUT = ROOT / "docs" / "eval"

SEED = 42
#: Fiscal series before this is a different state entirely (pre-modern
#: treasuries, war financing by default). Same cut research/panel.py uses.
FISCAL_START = 1850


# ---- the model, written out --------------------------------------------------

def _log_gauss(x: np.ndarray, mu: float, var: float) -> np.ndarray:
    return -0.5 * (np.log(2 * np.pi * var) + (x - mu) ** 2 / var)


def fit_hmm(x: np.ndarray, n_iter: int = 200, tol: float = 1e-6) -> dict:
    """Two-state Gaussian HMM via EM. Returns parameters, posteriors, Viterbi.

    Initialisation is deterministic: states start at the 25th and 75th
    percentile of the data with equal variances — enough to break symmetry
    without importing randomness into the displayed result.
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    assert n >= 20, "una serie más corta no identifica dos regímenes"

    mu = np.percentile(x, [75.0, 25.0]).astype(float)      # state 0 high, 1 low
    var = np.full(2, x.var() + 1e-6)
    A = np.array([[0.9, 0.1], [0.1, 0.9]])                  # sticky by default
    pi = np.array([0.5, 0.5])

    ll_prev = -np.inf
    for _ in range(n_iter):
        logb = np.stack([_log_gauss(x, mu[k], var[k]) for k in range(2)], axis=1)

        # forward-backward in log space; scaling via logsumexp
        la = np.zeros((n, 2))
        la[0] = np.log(pi) + logb[0]
        logA = np.log(A)
        for t in range(1, n):
            la[t] = logb[t] + np.logaddexp(la[t - 1, 0] + logA[0],
                                           la[t - 1, 1] + logA[1])
        lb = np.zeros((n, 2))
        for t in range(n - 2, -1, -1):
            tmp = logA + logb[t + 1] + lb[t + 1]
            lb[t] = np.logaddexp(tmp[:, 0], tmp[:, 1])

        ll = float(np.logaddexp(la[-1, 0], la[-1, 1]))
        lg = la + lb - ll
        gamma = np.exp(lg)                                   # smoothed posteriors

        # pairwise posteriors for the transition update
        xi = np.zeros((2, 2))
        for t in range(n - 1):
            m = (la[t][:, None] + logA + logb[t + 1][None, :]
                 + lb[t + 1][None, :]) - ll
            xi += np.exp(m)

        pi = gamma[0] / gamma[0].sum()
        A = xi / xi.sum(axis=1, keepdims=True)
        w = gamma.sum(axis=0)
        mu = (gamma * x[:, None]).sum(axis=0) / w
        var = (gamma * (x[:, None] - mu[None, :]) ** 2).sum(axis=0) / w
        var = np.maximum(var, 1e-8)

        if abs(ll - ll_prev) < tol:
            break
        ll_prev = ll

    # Viterbi path for the displayed episodes
    logb = np.stack([_log_gauss(x, mu[k], var[k]) for k in range(2)], axis=1)
    delta = np.log(pi) + logb[0]
    psi = np.zeros((n, 2), dtype=int)
    for t in range(1, n):
        cand = delta[:, None] + np.log(A)
        psi[t] = cand.argmax(axis=0)
        delta = cand.max(axis=0) + logb[t]
    path = np.zeros(n, dtype=int)
    path[-1] = int(delta.argmax())
    for t in range(n - 2, -1, -1):
        path[t] = psi[t + 1][path[t + 1]]

    # Label by property, not by index: crisis is the high-variance state.
    crisis = int(np.argmax(var))
    return {
        "mu": mu.tolist(), "var": var.tolist(), "A": A.tolist(),
        "loglik": ll, "crisis_state": crisis,
        "p_crisis": gamma[:, crisis].tolist(),
        "viterbi_crisis": (path == crisis).astype(int).tolist(),
    }


def episodes(periods: list, flags: list[int]) -> list[dict]:
    """Contiguous crisis runs as labelled intervals."""
    out: list[dict] = []
    start = None
    for p, f in zip(periods, flags):
        if f and start is None:
            start = p
        elif not f and start is not None:
            out.append({"from": start, "to": prev})
            start = None
        prev = p
    if start is not None:
        out.append({"from": start, "to": periods[-1]})
    return out


# ---- the two series ----------------------------------------------------------

def fiscal_series() -> tuple[list[int], np.ndarray]:
    f = pd.read_csv(GOLD / "gold_fiscal_historico.csv")
    esp = f[(f.iso3 == "ESP") & (f.year >= FISCAL_START)].sort_values("year")
    esp = esp.assign(bal=esp.rev_gdp - esp.exp_gdp).dropna(subset=["bal"])
    return esp.year.astype(int).tolist(), esp.bal.to_numpy(dtype=float)


def housing_series() -> tuple[list[str], np.ndarray]:
    q = pd.read_csv(GOLD / "gold_ccaa_trimestral.csv")
    nac = q[q.ccaa == "Nacional"].sort_values(["anyo", "quarter"])
    nac = nac.assign(yoy=nac.ipv.pct_change(4) * 100).dropna(subset=["yoy"])
    labels = [f"{y}T{t}" for y, t in zip(nac.anyo, nac.quarter)]
    return labels, nac.yoy.to_numpy(dtype=float)


def run_all() -> dict:
    fy, fx = fiscal_series()
    fh = fit_hmm(fx)
    hy, hx = housing_series()
    hh = fit_hmm(hx)
    return {
        "fiscal": {
            "periods": fy, "values": fx.round(3).tolist(),
            "p_crisis": [round(p, 4) for p in fh["p_crisis"]],
            "episodes": episodes(fy, fh["viterbi_crisis"]),
            "mu": fh["mu"], "var": fh["var"],
            "unit": "saldo (ingresos − gastos), % PIB",
        },
        "housing": {
            "periods": hy, "values": hx.round(3).tolist(),
            "p_crisis": [round(p, 4) for p in hh["p_crisis"]],
            "episodes": episodes(hy, hh["viterbi_crisis"]),
            "mu": hh["mu"], "var": hh["var"],
            "unit": "IPV, % interanual",
        },
        "method": ("HMM gaussiano de 2 estados, EM en numpy, sin librería. "
                   "Crisis = el estado de mayor varianza. Episodios por "
                   "Viterbi; confianza por posteriores suavizadas."),
        "seed": SEED,
    }


def main() -> None:
    out = run_all()
    for name in ("fiscal", "housing"):
        d = out[name]
        print(f"\n== {name} · {len(d['periods'])} periodos · {d['unit']}")
        for e in d["episodes"]:
            print(f"   crisis {e['from']} → {e['to']}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "regimes.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\ninforme → {OUT / 'regimes.json'}")


if __name__ == "__main__":
    main()
