"""Panel estimation with cluster-robust inference — plain numpy, no black box.

Written out rather than pulled from a library so a reviewer can read exactly
what was computed. Two estimators, both with standard errors clustered by unit:

  within_ols       fixed-effects regression (unit demeaning)
  local_projection Jordà impulse responses, horizon by horizon

Clustering is not decoration here. Regional house prices and national fiscal
series are strongly autocorrelated within a unit, so classical standard errors
would be far too small and every estimate would look significant. Clustering by
unit is the standard correction and is what makes a confidence band mean
anything.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Estimate:
    name: str
    coef: float
    se: float
    n: int
    n_units: int
    #: 90 % band — matches how the app already draws Monte Carlo (p5–p95).
    ci_low: float
    ci_high: float

    @property
    def significant(self) -> bool:
        """Whether the 90 % band excludes zero."""
        return (self.ci_low > 0) or (self.ci_high < 0)

    def contains(self, value: float) -> bool:
        """Whether a calibrated constant sits inside the estimated band.

        This is the question the whole exercise exists to answer: not "is the
        calibration exactly right" — it never is — but "is it a value the data
        can live with".
        """
        return self.ci_low <= value <= self.ci_high

    def to_dict(self) -> dict:
        return {
            "name": self.name, "coef": self.coef, "se": self.se,
            "n": self.n, "n_units": self.n_units,
            "ci_low": self.ci_low, "ci_high": self.ci_high,
            "significant": self.significant,
        }


Z90 = 1.6448536269514722  # two-sided 90 %


def _cluster_ols(X: np.ndarray, y: np.ndarray, groups: np.ndarray
                 ) -> tuple[np.ndarray, np.ndarray]:
    """OLS with cluster-robust (CR0) covariance. Returns (beta, se)."""
    XtX = X.T @ X
    XtX_inv = np.linalg.pinv(XtX)
    beta = XtX_inv @ (X.T @ y)
    resid = y - X @ beta

    meat = np.zeros_like(XtX)
    for g in np.unique(groups):
        m = groups == g
        Xg, ug = X[m], resid[m]
        s = Xg.T @ ug
        meat += np.outer(s, s)

    n_g = len(np.unique(groups))
    n, k = X.shape
    # Small-sample correction: without it, few clusters give overconfident
    # bands, and this panel has 18-20 units, not hundreds.
    scale = (n_g / max(n_g - 1, 1)) * ((n - 1) / max(n - k, 1))
    cov = XtX_inv @ meat @ XtX_inv * scale
    return beta, np.sqrt(np.maximum(np.diag(cov), 0.0))


def _demean(values: np.ndarray, groups: np.ndarray) -> np.ndarray:
    out = values.astype(float).copy()
    for g in np.unique(groups):
        m = groups == g
        out[m] -= out[m].mean(axis=0)
    return out


def within_ols(rows: list[dict], y_key: str, x_keys: list[str],
               unit_key: str, name: str = "") -> Estimate | None:
    """Fixed-effects regression of `y_key` on `x_keys`, unit-demeaned.

    Returns the coefficient on the FIRST regressor. None when too little
    complete data survives — a silent tiny-sample estimate is worse than none.
    """
    keys = [y_key, *x_keys]
    usable = [r for r in rows if all(r.get(k) is not None for k in keys)]
    if len(usable) < 30:
        return None

    groups = np.array([r[unit_key] for r in usable])
    y = np.array([r[y_key] for r in usable], dtype=float)
    X = np.array([[r[k] for k in x_keys] for r in usable], dtype=float)

    yd = _demean(y, groups)
    Xd = _demean(X, groups)

    beta, se = _cluster_ols(Xd, yd, groups)
    b, s = float(beta[0]), float(se[0])
    return Estimate(
        name=name or f"{y_key}~{x_keys[0]}", coef=b, se=s,
        n=len(usable), n_units=len(np.unique(groups)),
        ci_low=b - Z90 * s, ci_high=b + Z90 * s,
    )


def pooled_mean(rows: list[dict], key: str, unit_key: str,
                name: str = "") -> Estimate | None:
    """Mean of `key` with standard errors clustered by unit.

    A plain mean would understate uncertainty badly here: 77 quarters from one
    region are nowhere near 77 independent observations.
    """
    usable = [r for r in rows if r.get(key) is not None]
    if len(usable) < 30:
        return None
    groups = np.array([r[unit_key] for r in usable])
    y = np.array([r[key] for r in usable], dtype=float)
    X = np.ones((len(y), 1))
    beta, se = _cluster_ols(X, y, groups)
    b, s = float(beta[0]), float(se[0])
    return Estimate(name=name or f"media({key})", coef=b, se=s, n=len(y),
                    n_units=len(np.unique(groups)),
                    ci_low=b - Z90 * s, ci_high=b + Z90 * s)


def local_projection(rows: list[dict], y_key: str, shock_key: str,
                     unit_key: str, time_key: str, horizons: int = 8,
                     controls: list[str] | None = None) -> list[Estimate]:
    """Jordà local projections: one regression per horizon h.

        y[i, t+h] - y[i, t]  =  a_i + B_h * shock[i, t] + controls + e

    B_h traced over h is the impulse response. Preferred to a VAR on a panel
    this short because each horizon is estimated separately, so a
    misspecification at one horizon does not propagate into all the others.
    """
    controls = controls or []
    by_unit: dict[str, dict[int, dict]] = {}
    for r in rows:
        by_unit.setdefault(r[unit_key], {})[r[time_key]] = r

    out: list[Estimate] = []
    for h in range(horizons + 1):
        stacked: list[dict] = []
        for unit, by_t in by_unit.items():
            for t, r in by_t.items():
                fut = by_t.get(t + h)
                if fut is None:
                    continue
                if r.get(y_key) is None or fut.get(y_key) is None:
                    continue
                if r.get(shock_key) is None:
                    continue
                if any(r.get(c) is None for c in controls):
                    continue
                stacked.append({
                    unit_key: unit,
                    "_dy": fut[y_key] - r[y_key],
                    "_shock": r[shock_key],
                    **{c: r[c] for c in controls},
                })
        est = within_ols(stacked, "_dy", ["_shock", *controls], unit_key,
                         name=f"h={h}")
        if est:
            out.append(est)
    return out
