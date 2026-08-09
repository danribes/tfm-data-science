"""Confronting the engine's calibrated constants with the frozen data.

The app declares in its own Metodología that the constants are calibrations,
not estimates. This module is the answer to that: for every constant the data
can speak to, it reports the estimate, a 90 % band, and whether the calibrated
value sits inside it.

A calibration falling outside the band is not a failure — it is a finding, and
it is reported as one. What would be a failure is presenting a calibration as
if it had been measured.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from engine import constants as c
from research import estimate, panel


#: Sub-windows for the housing panel. The split is 2013q4/2014q1 because that
#: is where the national house-price index turns, not because it flatters
#: anything: the full-sample estimate averages a crash and a recovery into one
#: number, and a single number invites the reader to believe the average is a
#: description of either half. It is a description of neither.
#: Quarters in a year. The impulse response is anchored here because IPV_REV
#: is an annual rule and a cumulative projection is zero at h = 0.
ANNUAL_H = 4

IPV_WINDOWS: tuple[tuple[str, int, int], ...] = (
    ("2007–2013 · ajuste", 2007, 2013),
    ("2014–2026 · recuperación", 2014, 2026),
)


@dataclass(frozen=True)
class Subperiod:
    """One estimate restricted to a window, for showing sample dependence."""
    label: str
    estimate: estimate.Estimate

    def to_dict(self) -> dict:
        return {"label": self.label, **self.estimate.to_dict()}


@dataclass(frozen=True)
class Comparison:
    constant: str
    label: str
    calibrated: float
    estimate: estimate.Estimate
    source: str
    #: Same estimator, narrower windows. Empty when splitting is not meaningful.
    subperiods: tuple[Subperiod, ...] = ()

    @property
    def compatible(self) -> bool:
        return self.estimate.contains(self.calibrated)

    @property
    def verdict(self) -> str:
        if self.compatible:
            return "compatible"
        side = "por encima" if self.calibrated > self.estimate.ci_high else "por debajo"
        return f"fuera de la banda ({side})"

    def to_dict(self) -> dict:
        return {
            "constant": self.constant, "label": self.label,
            "calibrated": self.calibrated, "source": self.source,
            "compatible": self.compatible, "verdict": self.verdict,
            "subperiods": [s.to_dict() for s in self.subperiods],
            **self.estimate.to_dict(),
        }


def compare_ipv_growth() -> Comparison | None:
    """IPV_LR — the long-run house-price growth the engine reverts towards.

    Reported for the whole panel and for each sub-window. The full sample
    starts in 2007 and therefore contains the entire Spanish housing bust; a
    calibration drawn from a longer history is not thereby wrong, it is
    answering a different question. Showing the halves is what lets a reader
    tell those two things apart.
    """
    p = panel.yoy(panel.housing_panel(), "ipv", periods=4)   # 4 quarters = a year
    est = estimate.pooled_mean(p.rows, "ipv_yoy", "ccaa",
                               name="crecimiento anual del IPV (% a/a)")
    if not est:
        return None

    subs: list[Subperiod] = []
    for label, y0, y1 in IPV_WINDOWS:
        window = [r for r in p.rows if y0 <= r["year"] <= y1]
        sub = estimate.pooled_mean(window, "ipv_yoy", "ccaa", name=label)
        if sub:
            subs.append(Subperiod(label=label, estimate=sub))

    return Comparison(
        constant="IPV_LR", label="Crecimiento a largo plazo del precio de la vivienda",
        calibrated=c.IPV_LR, estimate=est,
        source="gold_ccaa_trimestral.csv · 20 CCAA × 2007-2026",
        subperiods=tuple(subs),
    )


def compare_ipv_reversion() -> Comparison | None:
    """IPV_REV — how fast house-price growth reverts towards its long run.

    Regressing next year's growth on this year's gives a persistence phi; the
    engine's reversion parameter is the complement, 1 - phi.
    """
    p = panel.yoy(panel.housing_panel(), "ipv", periods=4)
    by_unit: dict[str, dict[int, dict]] = {}
    for r in p.rows:
        by_unit.setdefault(r["ccaa"], {})[r["t"]] = r

    stacked: list[dict] = []
    for unit, by_t in by_unit.items():
        for t, r in by_t.items():
            nxt = by_t.get(t + 4)
            if not nxt or r.get("ipv_yoy") is None or nxt.get("ipv_yoy") is None:
                continue
            stacked.append({"ccaa": unit, "y": nxt["ipv_yoy"], "lag": r["ipv_yoy"]})

    phi = estimate.within_ols(stacked, "y", ["lag"], "ccaa", name="persistencia (phi)")
    if not phi:
        return None
    rev = estimate.Estimate(
        name="reversión (1 - phi)", coef=1.0 - phi.coef, se=phi.se,
        n=phi.n, n_units=phi.n_units,
        ci_low=1.0 - phi.ci_high, ci_high=1.0 - phi.ci_low,
    )
    return Comparison(
        constant="IPV_REV", label="Reversión anual del IPV hacia su tendencia",
        calibrated=c.IPV_REV, estimate=rev,
        source="gold_ccaa_trimestral.csv · AR(1) sobre el crecimiento interanual",
    )


def ipv_shock_response(horizons: int = 12) -> dict | None:
    """How long a regional house-price shock lasts, horizon by horizon.

    The shock is a region's year-on-year house-price growth *minus the average
    across regions in the same quarter*. Subtracting the quarter mean removes
    whatever hit the whole country at once — rates, the cycle, a national
    policy — and leaves the part that is specific to one region. That is what
    makes this estimable at all: the panel is regional, so only regional
    variation is identified. It is a statement about persistence, not a
    structural multiplier, and it is labelled as one.

    The response is demeaned the same way — a region's log price minus the
    average log price across regions that quarter — so shock and response are
    the same kind of object. Without that, the common national trend sits in
    the residual and every band widens until nothing is distinguishable.

    B_h is therefore the % gap in the level after a one-point idiosyncratic
    surge in annual growth. The engine's own assumption is returned on the same
    axis: it shrinks a deviation by IPV_REV per year, so (1 - IPV_REV)^((h-4)/4)
    of the one-year response should survive to quarter h. The anchor is h = 4
    and not h = 0 because a cumulative-change projection is zero at h = 0 by
    construction; one year is also the period IPV_REV is quoted in.
    """
    p = panel.yoy(panel.housing_panel(), "ipv", periods=4)

    growth_at: dict[int, list[float]] = {}
    level_at: dict[int, list[float]] = {}
    for r in p.rows:
        if r["ipv_yoy"] is not None:
            growth_at.setdefault(r["t"], []).append(r["ipv_yoy"])
        if r["ipv"]:
            level_at.setdefault(r["t"], []).append(math.log(r["ipv"]) * 100.0)
    mean_growth = {t: sum(v) / len(v) for t, v in growth_at.items() if v}
    mean_level = {t: sum(v) / len(v) for t, v in level_at.items() if v}

    rows: list[dict] = []
    for r in p.rows:
        if r["ipv_yoy"] is None or not r["ipv"] or r["t"] not in mean_growth:
            continue
        rows.append({
            "ccaa": r["ccaa"], "t": r["t"],
            "shock": r["ipv_yoy"] - mean_growth[r["t"]],
            "dev": math.log(r["ipv"]) * 100.0 - mean_level[r["t"]],
        })

    irf = estimate.local_projection(rows, "dev", "shock", "ccaa", "t",
                                    horizons=horizons)
    if len(irf) <= ANNUAL_H:
        return None

    anchor = irf[ANNUAL_H].coef
    return {
        "horizons": [
            {"h": h, "years": h / 4.0, **est.to_dict()}
            for h, est in enumerate(irf)
        ],
        "engine_path": [
            # Undefined before the anchor: the engine's rule is annual, and
            # extrapolating it back to sub-year horizons would invent a claim
            # the constant does not make.
            {"h": h, "years": h / 4.0,
             "coef": (anchor * (1.0 - c.IPV_REV) ** ((h - ANNUAL_H) / 4.0)
                      if h >= ANNUAL_H else None)}
            for h in range(len(irf))
        ],
        "anchor_h": ANNUAL_H,
        "unit": "% de desviación del precio por punto de choque",
        "note": ("choque idiosincrásico regional: crecimiento del IPV menos la "
                 "media de las CCAA en ese trimestre, con la respuesta "
                 "descontada de la misma media"),
    }


def fiscal_persistence() -> estimate.Estimate | None:
    """How persistent the revenue-minus-spending balance is across countries.

    Not tied to a named engine constant, but it is the empirical counterpart of
    assuming the primary balance can be moved and held — which is exactly what
    the `sp` lever assumes.
    """
    p = panel.fiscal_panel(since=1960)
    by_unit: dict[str, dict[int, dict]] = {}
    for r in p.rows:
        by_unit.setdefault(r["iso3"], {})[r["t"]] = r
    stacked: list[dict] = []
    for unit, by_t in by_unit.items():
        for t, r in by_t.items():
            nxt = by_t.get(t + 1)
            if not nxt:
                continue
            stacked.append({"iso3": unit, "y": nxt["balance_proxy"],
                            "lag": r["balance_proxy"]})
    return estimate.within_ols(stacked, "y", ["lag"], "iso3",
                               name="persistencia del saldo (proxy)")


def run_all() -> dict:
    """Everything the frozen vintage can say about the engine's calibration."""
    comparisons = [x for x in (compare_ipv_growth(), compare_ipv_reversion()) if x]
    fp = fiscal_persistence()
    return {
        "comparisons": [x.to_dict() for x in comparisons],
        "irf": ipv_shock_response(),
        "fiscal_persistence": fp.to_dict() if fp else None,
        # Reported alongside the results on purpose: a reader should see what
        # was not estimable at the same time as what was.
        "identifiable": panel.IDENTIFIABLE,
        "engine_version": c.ENGINE_VERSION,
        "vintage": c.VINTAGE,
    }


if __name__ == "__main__":
    out = run_all()
    for row in out["comparisons"]:
        print(f"{row['constant']:9} calibrado {row['calibrated']:.2f} | "
              f"estimado {row['coef']:.2f} "
              f"[{row['ci_low']:.2f}, {row['ci_high']:.2f}] "
              f"n={row['n']} ({row['n_units']} unidades) → {row['verdict']}")
        for sub in row.get("subperiods", []):
            print(f"{'':11} {sub['label']:26} {sub['coef']:6.2f} "
                  f"[{sub['ci_low']:.2f}, {sub['ci_high']:.2f}] n={sub['n']}")
    if out["fiscal_persistence"]:
        f = out["fiscal_persistence"]
        print(f"{'saldo':9} persistencia {f['coef']:.2f} "
              f"[{f['ci_low']:.2f}, {f['ci_high']:.2f}] n={f['n']}")
    print("\nNo identificable con el vintage congelado:")
    for k, v in out["identifiable"].items():
        if v.startswith("no"):
            print(f"  {k}: {v}")
