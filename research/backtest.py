"""Rolling-origin backtest for the regional house-price index.

The protocol is pre-registered, and the point of writing it down before any
candidate exists is that it cannot be adjusted afterwards to suit a result:

  origins      2019Q4 → 2023Q4, one per quarter
  horizons     h = 1 … 8 quarters
  metric       MASE, scaled by the in-sample seasonal-naive error
  test set     2024Q1 onward is NEVER touched here
  baselines    seasonal naive, drift, naive
  win rule     a candidate must beat drift in at least 12 of the 17 CCAA at
               h ≤ 4. Losing is a publishable outcome; production does not
               change on a loss.

The held-out tail is the part that is easy to lose by accident. Every forecast
whose target falls on or after `TEST_START` is dropped rather than scored, so a
candidate tuned against this file still cannot see the final two years.

A forecaster is any callable `(train: pd.Series, h: int) -> list[float]`, which
is what lets a three-line drift rule and a neural network be compared without
either one getting a special path through the harness.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

import numpy as np
import pandas as pd

GOLD = Path(__file__).resolve().parents[1] / "data" / "gold"
EXTERNAL = Path(__file__).resolve().parents[1] / "data" / "external"

H = 8
ORIGINS = pd.period_range("2019Q4", "2023Q4", freq="Q")
#: Untouchable until the final evaluation, and enforced in `backtest` rather
#: than left to the caller's discipline.
TEST_START = pd.Period("2024Q1", freq="Q")

#: The bar a candidate has to clear, stated before any candidate exists.
WIN_MIN_CCAA = 12
WIN_HORIZON = 4


class Forecaster(Protocol):
    def __call__(self, train: pd.Series, h: int) -> list[float]: ...


# ---- baselines -------------------------------------------------------------

def snaive(train: pd.Series, h: int) -> list[float]:
    """Seasonal naive: the same quarter a year ago, recursively beyond h = 4."""
    out: list[float] = []
    for k in range(1, h + 1):
        idx = train.index[-1] + k
        while idx > train.index[-1]:
            idx -= 4
        out.append(float(train.loc[idx]) if idx in train.index else np.nan)
        if k > 4:
            out[-1] = out[k - 4 - 1]
    return out


def drift(train: pd.Series, h: int) -> list[float]:
    """Recent linear trend: the slope of the last eight quarters, extended.

    This is the one to beat. It is not a straw man — on a series with as much
    momentum as house prices, extending the recent slope is genuinely hard to
    improve on, which is exactly why it is the benchmark and not seasonal naive.
    """
    k = min(8, len(train) - 1)
    slope = (train.iloc[-1] - train.iloc[-1 - k]) / k
    return [float(train.iloc[-1] + slope * j) for j in range(1, h + 1)]


def naive(train: pd.Series, h: int) -> list[float]:
    """Last observed value. Informal reference, not part of the pre-registration."""
    return [float(train.iloc[-1])] * h


BASELINES: dict[str, Forecaster] = {"snaive": snaive, "drift": drift, "naive": naive}


# ---- data ------------------------------------------------------------------

def load_series(min_quarters: int = 60) -> dict[str, pd.Series]:
    """Quarterly house-price index per CCAA, from the frozen gold slice.

    Restricted to the regions that carry an affordability ratio, which drops
    Ceuta and Melilla and leaves exactly the 17 the win rule counts. The filter
    is not housekeeping: "12 of 17" only means something while the denominator
    is the one the rule was written against, and including the two cities would
    quietly change the bar to 12 of 19.
    """
    q = pd.read_csv(GOLD / "gold_ccaa_trimestral.csv")
    q = q[q["ratio_asequibilidad"].notna() | (q["ccaa"] == "Nacional")]
    q["p"] = pd.PeriodIndex(q["anyo"].astype(str) + "Q" + q["quarter"].astype(str),
                            freq="Q")
    q = q[(q["p"] >= pd.Period("2008Q1", freq="Q"))
          & (q["p"] <= pd.Period("2025Q4", freq="Q"))]
    out: dict[str, pd.Series] = {}
    for ccaa, d in q.groupby("ccaa"):
        s = d.set_index("p")["ipv_idx15"].dropna().sort_index()
        if len(s) >= min_quarters:
            out[str(ccaa)] = s
    return out


def load_global_panel() -> pd.DataFrame:
    """The foreign training corpus. No Spanish series, by construction."""
    return pd.read_csv(EXTERNAL / "hpi_regional_global.csv.gz")


# ---- harness ---------------------------------------------------------------

def mase_scale(train: pd.Series) -> float:
    """In-sample seasonal-naive error — the denominator of MASE.

    Computed on the training window of each origin, never on the whole series:
    using the full history would leak the level of post-origin volatility into
    the scale and make later origins look artificially easy.
    """
    return float(train.diff(4).abs().mean())


def backtest(series: dict[str, pd.Series],
             forecasters: dict[str, Forecaster]) -> pd.DataFrame:
    """Score every forecaster on every origin and horizon."""
    rows: list[dict] = []
    for ccaa, s in series.items():
        for t0 in ORIGINS:
            train = s[s.index <= t0]
            if len(train) < 12:
                continue
            scale = mase_scale(train)
            for name, f in forecasters.items():
                preds = f(train, H)
                for h, yhat in enumerate(preds, start=1):
                    t = t0 + h
                    # The held-out tail is dropped here, not by the caller.
                    if t not in s.index or t >= TEST_START or not np.isfinite(yhat):
                        continue
                    rows.append({"ccaa": ccaa, "origen": str(t0), "h": h,
                                 "metodo": name, "y": float(s.loc[t]),
                                 "yhat": float(yhat), "scale": scale})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["ae"] = (df.y - df.yhat).abs()
    df["e"] = df.y - df.yhat
    df["ase"] = df.ae / df.scale
    return df


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """MASE per method and horizon."""
    if df.empty:
        return pd.DataFrame(columns=["metodo", "h", "MASE", "n"])
    g = df.groupby(["metodo", "h"], as_index=False).agg(
        MASE=("ase", "mean"), n=("ase", "size"))
    return g


@dataclass(frozen=True)
class Verdict:
    """The pre-registered decision, computed rather than narrated."""
    candidate: str
    beaten_ccaa: int
    total_ccaa: int
    mase_candidate: float
    mase_drift: float
    #: Informative only — h 5-8 was never part of the win rule.
    mase_candidate_long: float
    mase_drift_long: float

    @property
    def wins(self) -> bool:
        return self.beaten_ccaa >= WIN_MIN_CCAA

    def to_dict(self) -> dict:
        return {
            "candidate": self.candidate,
            "beaten_ccaa": self.beaten_ccaa, "total_ccaa": self.total_ccaa,
            "required": WIN_MIN_CCAA, "horizon": WIN_HORIZON,
            "mase_candidate": self.mase_candidate, "mase_drift": self.mase_drift,
            "mase_candidate_long": self.mase_candidate_long,
            "mase_drift_long": self.mase_drift_long,
            "wins": self.wins,
            "verdict": ("bate al drift" if self.wins else "no bate al drift"),
        }


def judge(df: pd.DataFrame, candidate: str, benchmark: str = "drift") -> Verdict:
    """Apply the win rule. Nacional is excluded — it is an aggregate of the
    same regions, so counting it would score part of the panel twice."""
    short = df[df.h <= WIN_HORIZON]
    per_ccaa = short.groupby(["metodo", "ccaa"])["ase"].mean().unstack("metodo")
    per_ccaa = per_ccaa.drop(index="Nacional", errors="ignore")
    beaten = int((per_ccaa[candidate] < per_ccaa[benchmark]).sum())

    long = df[df.h.between(5, 8)].groupby("metodo")["ase"].mean()
    return Verdict(
        candidate=candidate,
        beaten_ccaa=beaten, total_ccaa=int(len(per_ccaa)),
        mase_candidate=float(short[short.metodo == candidate].ase.mean()),
        mase_drift=float(short[short.metodo == benchmark].ase.mean()),
        mase_candidate_long=float(long.get(candidate, np.nan)),
        mase_drift_long=float(long.get(benchmark, np.nan)),
    )


def run_baselines() -> pd.DataFrame:
    return backtest(load_series(), BASELINES)


def main() -> None:
    df = run_baselines()
    print(f"orígenes {ORIGINS[0]}–{ORIGINS[-1]} · h=1–{H} · "
          f"test {TEST_START}+ intocado · {df.ccaa.nunique()} series\n")
    piv = summarize(df).pivot(index="h", columns="metodo", values="MASE")
    print(piv.round(3).to_string())
    print(f"\nobservaciones puntuadas: {len(df):,}")
    print(f"regla: batir a drift en {WIN_MIN_CCAA}/17 CCAA con h<={WIN_HORIZON}")


if __name__ == "__main__":
    main()
