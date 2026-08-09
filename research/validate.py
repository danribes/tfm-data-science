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

from dataclasses import dataclass

from engine import constants as c
from research import estimate, panel


@dataclass(frozen=True)
class Comparison:
    constant: str
    label: str
    calibrated: float
    estimate: estimate.Estimate
    source: str

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
            **self.estimate.to_dict(),
        }


def compare_ipv_growth() -> Comparison | None:
    """IPV_LR — the long-run house-price growth the engine reverts towards."""
    p = panel.yoy(panel.housing_panel(), "ipv", periods=4)   # 4 quarters = a year
    est = estimate.pooled_mean(p.rows, "ipv_yoy", "ccaa",
                               name="crecimiento anual del IPV (% a/a)")
    if not est:
        return None
    return Comparison(
        constant="IPV_LR", label="Crecimiento a largo plazo del precio de la vivienda",
        calibrated=c.IPV_LR, estimate=est,
        source="gold_ccaa_trimestral.csv · 20 CCAA × 2007-2026",
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
        "fiscal_persistence": fp.to_dict() if fp else None,
        # Reported alongside the results on purpose: a reader should see what
        # was not estimable at the same time as what was.
        "identifiable": panel.IDENTIFIABLE,
        "engine_version": c.ENGINE_VERSION,
        "vintage": c.VINTAGE,
    }


if __name__ == "__main__":
    import json
    out = run_all()
    for row in out["comparisons"]:
        print(f"{row['constant']:9} calibrado {row['calibrated']:.2f} | "
              f"estimado {row['coef']:.2f} "
              f"[{row['ci_low']:.2f}, {row['ci_high']:.2f}] "
              f"n={row['n']} ({row['n_units']} unidades) → {row['verdict']}")
    if out["fiscal_persistence"]:
        f = out["fiscal_persistence"]
        print(f"{'saldo':9} persistencia {f['coef']:.2f} "
              f"[{f['ci_low']:.2f}, {f['ci_high']:.2f}] n={f['n']}")
    print("\nNo identificable con el vintage congelado:")
    for k, v in out["identifiable"].items():
        if v.startswith("no"):
            print(f"  {k}: {v}")
