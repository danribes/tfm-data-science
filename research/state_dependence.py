"""Does an interest-rate shock hit the same at 60 % debt as at 120 %?

The engine says yes: E_R = 0,45 points of GDP per point of rate, a constant,
applied identically whatever the debt level. Evidencia declares E_R not
identifiable from the frozen vintage — the Euríbor is national and the panel
regional. Both statements stay true. This module asks the *dynamic* version of
the question on external panels the vintage does not contain: IMF debt levels
joined to World Bank rates and growth, 1980-2024.

Method: a boosted local projection. The outcome is cumulative GDP growth over
the next three years; the treatment is this year's change in the real rate; the
controls are the macro state, debt level included. A gradient-boosted tree is
free to interact treatment with state — that freedom is the whole point, since
a linear projection would assume the engine's answer before looking. SHAP
splits each prediction into per-feature contributions, and the slope of the
rate-change contribution *within each debt regime* is the empirical E_R for
that regime.

What this is not: identification. A rate change here is not an exogenous shock
— central banks raise rates into booms — so levels of the effect carry that
bias. The comparison across debt regimes is more defensible than any level: the
endogeneity would have to differ systematically by debt tercile to manufacture
a difference in slopes.

Two limitations are structural and declared rather than patched. The grouped
R² is ~0: the model has no out-of-country predictive skill for three-year
growth, so every slope below describes the fitted surface, not a validated
forecast rule. And Spain itself has no treatment variable — eurozone members
stop reporting lending rates to the WDI — so the country this app is about
cannot receive a point attribution from this panel. The regime comparison is
the deliverable; a Spain-specific SHAP bar chart from a rate the panel does
not contain would be an invention wearing a method's name.

    python -m research.state_dependence      (~1 min)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = ROOT / "data" / "external"
OUT = ROOT / "docs" / "eval"

SEED = 42
#: Horizon of the cumulative-growth outcome, in years.
H = 3

FEATURES = {
    "d_real_rate": "Δ tipo de interés real (pp)",
    "debt_gdp": "Deuda pública (% PIB)",
    "gdp_growth": "Crecimiento del PIB (%)",
    "inflation": "Inflación (%)",
    "cab_gdp": "Cuenta corriente (% PIB)",
    "gdp_pc_log": "log PIB per cápita",
}

#: Debt regimes for the headline comparison. 60 and 90 are the treaty
#: reference and the literature's habitual danger line — chosen because they
#: are recognisable, not because they optimise the contrast.
REGIMES = ((0.0, 60.0, "deuda < 60 %"),
           (60.0, 90.0, "deuda 60–90 %"),
           (90.0, np.inf, "deuda > 90 %"))


def build_panel() -> pd.DataFrame:
    """Country-years with a rate change at t and growth through t+H.

    The outcome is compounded from annual growth rates, not summed — three
    years of 10 % is 33 %, not 30, and at crisis magnitudes the difference is
    not a rounding error.
    """
    wb = pd.read_csv(EXTERNAL / "wb_macro_panel.csv.gz")
    imf = pd.read_csv(EXTERNAL / "imf_debt_gdp.csv.gz")
    d = wb.merge(imf, on=["iso3", "year"], how="inner")
    d = d.sort_values(["iso3", "year"]).reset_index(drop=True)

    g = d.groupby("iso3")
    d["d_real_rate"] = g.real_rate.diff(1)
    d["gdp_pc_log"] = np.log(d.gdp_pc.where(d.gdp_pc > 0))

    # Forward cumulative growth, only where the next H years are consecutive.
    growth = d.gdp_growth / 100.0
    fwd = pd.Series(1.0, index=d.index)
    ok = pd.Series(True, index=d.index)
    for k in range(1, H + 1):
        fwd = fwd * (1.0 + g.gdp_growth.shift(-k) / 100.0)
        ok &= g.year.shift(-k) == d.year + k
    d["y_fwd"] = (fwd - 1.0) * 100.0
    d.loc[~ok, "y_fwd"] = np.nan
    del growth

    # Complete cases only. GradientBoostingRegressor does not take NaN, and
    # unlike the distress panel there is no reason to keep sparse rows here:
    # the question needs the treatment, the state and the controls together,
    # and a row missing inflation answers a different regression.
    d = d.dropna(subset=["y_fwd", *FEATURES])
    return d.reset_index(drop=True)


def _model():
    from sklearn.ensemble import GradientBoostingRegressor

    # The classic GBR rather than the histogram variant: shap's TreeExplainer
    # supports it exactly (additivity verified in the tests), and this panel is
    # small enough that the speed difference is irrelevant.
    return GradientBoostingRegressor(
        n_estimators=400, learning_rate=0.03, max_depth=3,
        subsample=0.8, random_state=SEED,
    )


def _slope(x: np.ndarray, s: np.ndarray) -> tuple[float, float]:
    """OLS slope of SHAP contribution on the feature, with its standard error.

    Within a regime, shap(d_real_rate) against d_real_rate is a scatter whose
    slope is "GDP points over H years per point of rate change, in this
    regime" — the empirical counterpart of the engine's constant.
    """
    x = x - x.mean()
    s = s - s.mean()
    denom = float((x ** 2).sum())
    if denom < 1e-12 or len(x) < 10:
        return float("nan"), float("nan")
    b = float((x * s).sum() / denom)
    resid = s - b * x
    se = float(np.sqrt((resid ** 2).sum() / max(len(x) - 2, 1) / denom))
    return b, se


@dataclass(frozen=True)
class Regime:
    label: str
    n: int
    slope: float
    se: float

    def to_dict(self) -> dict:
        return {"label": self.label, "n": self.n,
                "slope": self.slope, "se": self.se}


@dataclass(frozen=True)
class Result:
    n: int
    n_countries: int
    years: tuple[int, int]
    r2_grouped: float
    r2_std: float
    regimes: list[Regime]
    engine_e_r: float
    importance: list[dict]
    #: 90 % cluster-bootstrap interval for slope(high debt) − slope(low debt).
    diff_ci: tuple[float, float]
    n_boot: int

    @property
    def state_dependent(self) -> bool:
        """True only when the bootstrap interval for the slope difference
        excludes zero. The per-regime OLS errors are not used for this claim —
        they treat model outputs as data."""
        lo, hi = self.diff_ci
        return bool(np.isfinite(lo) and np.isfinite(hi) and (lo > 0 or hi < 0))

    def to_dict(self) -> dict:
        return {
            "n": self.n, "n_countries": self.n_countries, "years": list(self.years),
            "r2_grouped": self.r2_grouped, "r2_std": self.r2_std,
            "regimes": [r.to_dict() for r in self.regimes],
            "engine_e_r": self.engine_e_r, "horizon_years": H,
            "importance": self.importance,
            "diff_ci": list(self.diff_ci), "n_boot": self.n_boot,
            "state_dependent": self.state_dependent,
            "spain_excluded_reason": (
                "la zona euro no reporta tipos de préstamo al WDI: España no "
                "tiene variable de tratamiento en este panel"),
            "seed": SEED,
        }


def evaluate(panel: pd.DataFrame | None = None, n_boot: int = 60) -> Result:
    import shap
    from engine.constants import E_R
    from sklearn.model_selection import GroupKFold, cross_val_score

    d = panel if panel is not None else build_panel()
    cols = list(FEATURES)
    X = d[cols].to_numpy(dtype=float)
    y = d.y_fwd.to_numpy(dtype=float)
    groups = d.iso3.to_numpy()

    # Honest fit quality first: grouped by country, so the number reported is
    # for countries the model has not seen.
    scores = cross_val_score(_model(), X, y, groups=groups,
                             cv=GroupKFold(n_splits=5), scoring="r2")

    model = _model().fit(X, y)
    sv = shap.TreeExplainer(model).shap_values(X)
    rate_idx = cols.index("d_real_rate")

    regimes: list[Regime] = []
    for lo, hi, label in REGIMES:
        m = (d.debt_gdp >= lo) & (d.debt_gdp < hi)
        b, se = _slope(X[m.to_numpy(), rate_idx], sv[m.to_numpy(), rate_idx])
        regimes.append(Regime(label=label, n=int(m.sum()), slope=b, se=se))

    # The twin bars: how much each feature moved the outcome historically,
    # against the engine's structural attribution of the on-screen scenario.
    importance = [
        {"feature": c, "label": FEATURES[c],
         "mean_abs_shap": float(np.abs(sv[:, i]).mean())}
        for i, c in enumerate(cols)
    ]
    importance.sort(key=lambda r: -r["mean_abs_shap"])

    # Cluster bootstrap on the slope DIFFERENCE. The per-regime OLS errors
    # above treat SHAP values as data; they are model outputs, and countries
    # are the unit of independence. Resampling countries and refitting is the
    # only error bar here that means what it claims.
    rng = np.random.default_rng(SEED)
    countries = d.iso3.unique()
    diffs: list[float] = []
    lo_lo, lo_hi, _ = REGIMES[0]
    hi_lo, hi_hi, _ = REGIMES[-1]
    for _ in range(n_boot):
        pick = rng.choice(countries, size=len(countries), replace=True)
        bd = pd.concat([d[d.iso3 == c] for c in pick], ignore_index=True)
        bX = bd[cols].to_numpy(dtype=float)
        bm = _model().fit(bX, bd.y_fwd.to_numpy(dtype=float))
        bsv = shap.TreeExplainer(bm).shap_values(bX)
        mlo = ((bd.debt_gdp >= lo_lo) & (bd.debt_gdp < lo_hi)).to_numpy()
        mhi = ((bd.debt_gdp >= hi_lo) & (bd.debt_gdp < hi_hi)).to_numpy()
        blo, _se1 = _slope(bX[mlo, rate_idx], bsv[mlo, rate_idx])
        bhi, _se2 = _slope(bX[mhi, rate_idx], bsv[mhi, rate_idx])
        if np.isfinite(blo) and np.isfinite(bhi):
            diffs.append(bhi - blo)
    diff_ci = (float(np.percentile(diffs, 5)), float(np.percentile(diffs, 95))) \
        if diffs else (float("nan"), float("nan"))

    return Result(
        n=len(d), n_countries=int(d.iso3.nunique()),
        years=(int(d.year.min()), int(d.year.max())),
        r2_grouped=float(scores.mean()), r2_std=float(scores.std()),
        regimes=regimes, engine_e_r=float(E_R),
        importance=importance, diff_ci=diff_ci, n_boot=len(diffs),
    )


def main() -> None:
    d = build_panel()
    r = evaluate(d)

    print(f"panel: {r.n:,} país-año · {r.n_countries} países · "
          f"{r.years[0]}-{r.years[1]}")
    print(f"R² agrupado por país: {r.r2_grouped:.3f} ± {r.r2_std:.3f}")

    print(f"\nefecto de +1 pp de tipo real sobre el crecimiento a {H} años "
          f"(pendiente SHAP):")
    for reg in r.regimes:
        print(f"  {reg.label:<16} {reg.slope:+7.3f} ± {reg.se:.3f}   (n={reg.n:,})")
    print(f"\n  motor: E_R = {r.engine_e_r} pp de PIB por pp, constante por diseño")
    print(f"  ¿dependiente del estado?: "
          f"{'SÍ' if r.state_dependent else 'no distinguible con estos datos'}")

    print(f"\ndiferencia de pendientes (alta − baja deuda), "
          f"bootstrap por país ({r.n_boot} réplicas): "
          f"[{r.diff_ci[0]:+.3f}, {r.diff_ci[1]:+.3f}]")
    print("\nqué movió el crecimiento a 3 años, históricamente (|SHAP| medio):")
    for i in r.importance:
        print(f"   {i['label']:<34} {i['mean_abs_shap']:.3f}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "state_dependence.json").write_text(
        json.dumps(r.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\ninforme → {OUT / 'state_dependence.json'}")


if __name__ == "__main__":
    main()
