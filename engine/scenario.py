from dataclasses import dataclass, field
from typing import Dict, List, Optional

from data.models import FetchResult
from engine.debt_dynamics import project_debt_path, DebtPathPoint
from engine.satellite import okun_unemployment_gap, phillips_inflation, indexed_growth
from engine.fiscal_space import allocate_fiscal_space, FiscalSpaceResult, SPENDING_CATEGORIES


@dataclass
class ScenarioLevers:
    horizon_years: int = 10
    tax_wedge_delta_pp: float = 0.0
    primary_balance_target_pct: float = 0.0
    output_gap_path_pct: Optional[List[float]] = None
    contingent_shocks_pct: Optional[List[float]] = None
    indexation_delta_pp: float = 0.0
    allocation_shares: Dict[str, float] = field(default_factory=lambda: {
        "health": 0.30, "education": 0.20, "welfare": 0.25,
        "public_wage_bill": 0.15, "security": 0.05, "infrastructure": 0.03, "public_investment": 0.02,
    })


@dataclass
class ScenarioResult:
    country_iso3: str
    debt_path: List[DebtPathPoint]
    fiscal_space_by_year: List[FiscalSpaceResult]
    unemployment_path_pct: List[float]
    inflation_path_pct: List[float]
    nominal_wage_growth_path_pct: List[float]
    coverage_score: float


def _latest_value(result: FetchResult, default: float) -> float:
    if not result.available:
        return default
    latest_year = max(result.values)
    return result.values[latest_year]


def run_scenario(country_iso3: str, panel: Dict[str, FetchResult], levers: ScenarioLevers) -> ScenarioResult:
    baseline_debt = _latest_value(panel["debt_gdp"], default=60.0)
    baseline_growth = _latest_value(panel["gdp_growth"], default=1.5)
    baseline_inflation = _latest_value(panel["inflation"], default=2.0)
    baseline_unemployment = _latest_value(panel["unemployment"], default=7.0)
    baseline_rate = _latest_value(panel["real_interest_rate"], default=2.0)
    baseline_pb = _latest_value(panel["net_lending_borrowing"], default=-2.0)
    baseline_revenue = _latest_value(panel["government_revenue_gdp"], default=35.0)

    n = levers.horizon_years
    output_gaps = levers.output_gap_path_pct or [0.0] * n
    shocks = levers.contingent_shocks_pct or [0.0] * n

    unemployment_path = []
    inflation_path = []
    wage_growth_path = []
    for gap in output_gaps:
        u_gap = okun_unemployment_gap(gap)
        unemployment_path.append(baseline_unemployment + u_gap)
        inf = phillips_inflation(baseline_inflation, u_gap)
        inflation_path.append(inf)
        wage_growth_path.append(indexed_growth(inf, levers.indexation_delta_pp))

    r_path = [baseline_rate] * n
    g_path = [baseline_growth + g for g in output_gaps]
    pb_path = [levers.primary_balance_target_pct] * n

    debt_path = project_debt_path(baseline_debt, r_path, g_path, pb_path, start_year=2025,
                                   contingent_shocks_pct=shocks)

    fiscal_space_by_year = [
        allocate_fiscal_space(baseline_revenue, levers.tax_wedge_delta_pp,
                               levers.primary_balance_target_pct, levers.allocation_shares)
        for _ in range(n)
    ]

    coverage = sum(1 for r in panel.values() if r.available) / len(panel) if panel else 0.0

    return ScenarioResult(
        country_iso3=country_iso3,
        debt_path=debt_path,
        fiscal_space_by_year=fiscal_space_by_year,
        unemployment_path_pct=unemployment_path,
        inflation_path_pct=inflation_path,
        nominal_wage_growth_path_pct=wage_growth_path,
        coverage_score=coverage,
    )
