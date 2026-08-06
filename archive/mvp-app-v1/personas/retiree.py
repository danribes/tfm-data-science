from dataclasses import dataclass
from typing import List, Optional

from engine.scenario import ScenarioResult
from engine.ml_stress_score import StressScoreResult


@dataclass
class RetireeYearView:
    year: int
    nominal_pension_index: float
    real_pension_index: float
    health_funding_adequacy_pct: Optional[float]


@dataclass
class RetireeDashboard:
    years: List[RetireeYearView]
    fiscal_stress: StressScoreResult
    health_baseline_pct_gdp: Optional[float]


def build_retiree_dashboard(scenario: ScenarioResult, stress: StressScoreResult,
                             baseline_health_exp_gdp_pct: Optional[float]) -> RetireeDashboard:
    """Pension growth uses the same indexation lever as wages (design spec §4.2's
    wage/pension indexation rule) -- this MVP does not model a separate
    pension-specific indexation rule."""
    nominal_index = 100.0
    real_index = 100.0
    years = []
    for i, wage_growth in enumerate(scenario.nominal_wage_growth_path_pct):
        inflation = scenario.inflation_path_pct[i]
        nominal_index *= (1.0 + wage_growth / 100.0)
        real_index *= (1.0 + wage_growth / 100.0) / (1.0 + inflation / 100.0)

        adequacy = None
        if baseline_health_exp_gdp_pct and baseline_health_exp_gdp_pct > 0:
            allocated = scenario.fiscal_space_by_year[i].allocations_pct_gdp["health"]
            adequacy = allocated / baseline_health_exp_gdp_pct * 100.0

        years.append(RetireeYearView(
            year=scenario.debt_path[i].year,
            nominal_pension_index=nominal_index,
            real_pension_index=real_index,
            health_funding_adequacy_pct=adequacy,
        ))

    return RetireeDashboard(years=years, fiscal_stress=stress, health_baseline_pct_gdp=baseline_health_exp_gdp_pct)
