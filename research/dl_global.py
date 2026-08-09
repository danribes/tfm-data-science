"""A global house-price model trained abroad and judged on Spain.

The bet, stated before the result: Spain has one housing cycle in the sample
and it is the one being forecast, so a model fitted on Spanish data can only
learn that cycle. The US and the UK have several decades of completed booms and
busts across 1.760 regions. If anything can anticipate a turn, it is a model
that has watched dozens of them die somewhere else.

Two cuts keep the exercise honest, and both are enforced in code rather than
promised in a comment:

  geography — no Spanish series is in the training corpus at all, by
              construction of `data/external/` (asserted in the tests)
  time      — only windows whose target ends on or before 2019Q3 are used, so
              the model has seen nothing from any geography that postdates the
              first validation origin

The second is the one that is easy to get wrong. Without it the model would
have learned the shape of the 2020-2023 world from Ohio and Manchester before
being asked to forecast it in Madrid, and beating drift would prove nothing.

The comparison is the same pre-registered grid every baseline runs through
(`research.backtest`). Losing is a result: this module reports the verdict and
changes nothing in production either way.

    python -m research.dl_global          (~3 min on CPU)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from research import backtest as bt

#: Input window and forecast horizon, in quarters.
W, H = 16, 8
#: Last quarter a training target may end on — one before the first validation
#: origin. Expressed as year*4 + quarter to match the panel's integer index.
CUTOFF = 2019 * 4 + 3
SEED = 42
EPOCHS = 8
#: House-price quarterly log changes beyond ±15 % are data errors far more
#: often than they are real events; clipping stops one of them dominating the
#: gradient.
CLIP = 0.15

OUT = Path(__file__).resolve().parents[1] / "docs" / "eval"


def _as_quarter(p: int) -> str:
    """Decode the panel's year*4 + quarter index, where quarter is 1-based.

    The naive `p // 4` and `p % 4 + 1` are both wrong, and wrong in a way that
    matters: they report the cut as 2019Q4 when it is 2019Q3, which is a claim
    that the model saw one quarter more than it did.
    """
    return f"{(p - 1) // 4}Q{(p - 1) % 4 + 1}"


def training_windows() -> tuple[np.ndarray, np.ndarray]:
    """Sliding windows from the foreign panel, cut at the temporal boundary.

    Series with a gap in their quarterly index are skipped outright rather than
    interpolated: a fabricated quarter inside a 16-step window teaches the
    model a transition that never happened.
    """
    d = bt.load_global_panel()
    d["p"] = d.anyo * 4 + d.quarter
    X: list[np.ndarray] = []
    Y: list[np.ndarray] = []

    for _, g in d.groupby("serie"):
        g = g.sort_values("p")
        v = np.log(g.valor.to_numpy(dtype=float))
        p = g.p.to_numpy()
        if len(v) < W + H + 1 or (np.diff(p) != 1).any():
            continue
        dl = np.clip(np.diff(v), -CLIP, CLIP)
        for i in range(W, len(dl) - H + 1):
            if p[i + H] > CUTOFF:      # the whole target must end before the cut
                break
            X.append(dl[i - W:i])
            Y.append(np.cumsum(dl[i:i + H]))

    return (np.asarray(X, dtype=np.float32), np.asarray(Y, dtype=np.float32))


def train(X: np.ndarray, Y: np.ndarray, *, verbose: bool = True):
    """Multi-output MLP: 16 quarterly log changes → 8 cumulative log changes.

    Deliberately small. With 1.760 series the constraint is not parameters, it
    is that the thing has to be explainable at a viva, and an MLP on log
    differences is a model whose every step can be recited.
    """
    import torch
    import torch.nn as nn

    torch.manual_seed(SEED)
    net = nn.Sequential(
        nn.Linear(W, 128), nn.ReLU(), nn.Dropout(0.1),
        nn.Linear(128, 128), nn.ReLU(), nn.Dropout(0.1),
        nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, H),
    )
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    ds = torch.utils.data.TensorDataset(torch.tensor(X), torch.tensor(Y))
    dl = torch.utils.data.DataLoader(ds, batch_size=1024, shuffle=True)

    net.train()
    for epoch in range(EPOCHS):
        total = 0.0
        for xb, yb in dl:
            opt.zero_grad()
            # MAE, not MSE: MASE is an absolute-error metric, so training on
            # squared error would optimise something the protocol does not score.
            loss = nn.functional.l1_loss(net(xb), yb)
            loss.backward()
            opt.step()
            total += float(loss) * len(xb)
        if verbose:
            print(f"  época {epoch + 1}/{EPOCHS}: MAE {total / len(ds):.5f}")

    net.eval()
    return net


def make_forecaster(net):
    """Wrap the network in the harness's forecaster signature."""
    import torch

    def forecaster(train_s: pd.Series, h: int) -> list[float]:
        v = np.log(train_s.to_numpy(dtype=float))
        if len(v) < W + 1:
            return [float("nan")] * h
        window = np.clip(np.diff(v), -CLIP, CLIP)[-W:]
        with torch.no_grad():
            cum = net(torch.tensor(window, dtype=torch.float32).unsqueeze(0))[0].numpy()
        # Back to levels: the model predicts cumulative log change from the last
        # observation, so the last observation is the only anchor needed.
        return [float(np.exp(v[-1] + cum[k])) for k in range(h)]

    return forecaster


@dataclass(frozen=True)
class Run:
    n_windows: int
    n_series: int
    verdict: dict
    mase_by_h: dict

    def to_dict(self) -> dict:
        return {"n_windows": self.n_windows, "n_series": self.n_series,
                "cutoff": _as_quarter(CUTOFF),
                "window": W, "horizon": H, "epochs": EPOCHS, "seed": SEED,
                "verdict": self.verdict, "mase_by_h": self.mase_by_h}


def run(verbose: bool = True) -> Run:
    X, Y = training_windows()
    if verbose:
        print(f"entrenamiento: {len(X):,} ventanas de series extranjeras, "
              f"objetivos que acaban <= 2019Q3")
    net = train(X, Y, verbose=verbose)

    series = bt.load_series()
    forecasters = dict(bt.BASELINES)
    forecasters["dl_global"] = make_forecaster(net)
    df = bt.backtest(series, forecasters)

    verdict = bt.judge(df, "dl_global")
    piv = bt.summarize(df).pivot(index="h", columns="metodo", values="MASE")
    return Run(n_windows=len(X), n_series=int(bt.load_global_panel().serie.nunique()),
               verdict=verdict.to_dict(),
               mase_by_h={str(h): {m: round(float(piv.loc[h, m]), 4)
                                   for m in piv.columns if pd.notna(piv.loc[h, m])}
                          for h in piv.index})


def main() -> None:
    r = run()
    piv = pd.DataFrame(r.mase_by_h).T
    print("\n" + piv.round(3).to_string())

    v = r.verdict
    print(f"\nregla pre-registrada: batir a drift en {v['required']}/17 CCAA con "
          f"h<={v['horizon']}")
    print(f"resultado: {v['beaten_ccaa']}/{v['total_ccaa']} → {v['verdict'].upper()}")
    print(f"  MASE h<=4  dl_global {v['mase_candidate']:.3f} vs "
          f"drift {v['mase_drift']:.3f}")
    print(f"  MASE h5-8  dl_global {v['mase_candidate_long']:.3f} vs "
          f"drift {v['mase_drift_long']:.3f}   (informativo, fuera de la regla)")

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "t1-dl-global.json"
    path.write_text(json.dumps(r.to_dict(), ensure_ascii=False, indent=2),
                    encoding="utf-8")
    print(f"\ninforme → {path}")


if __name__ == "__main__":
    main()
