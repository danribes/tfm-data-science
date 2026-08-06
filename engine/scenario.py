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
    defaults_used: List[str] = field(default_factory=list)
    baseline_years: Dict[str, int] = field(default_factory=dict)


# Generic calibration defaults substituted when a baseline indicator is
# unavailable for a country. Keyed by the panel/indicator key used below.
# Kept in one place so app/tab_methodology.py can render the same values
# the engine actually falls back to.
BASELINE_DEFAULTS = {
    "debt_gdp": 60.0,
    "gdp_growth": 1.5,
    "inflation": 2.0,
    "unemployment": 7.0,
    "real_interest_rate": 2.0,
    "net_lending_borrowing": -2.0,
    "government_revenue_gdp": 35.0,
}

# Human-readable labels for the same seven baseline indicators, shared by
# app/main.py (defaults-used / staleness warnings) and app/tab_methodology.py
# (engine constants table, baseline-calibration table).
BASELINE_INDICATOR_LABELS = {
    "debt_gdp": "Debt/GDP",
    "gdp_growth": "GDP growth",
    "inflation": "Inflation",
    "unemployment": "Unemployment",
    "real_interest_rate": "Real interest rate",
    "net_lending_borrowing": "Net lending/borrowing (primary-balance proxy)",
    "government_revenue_gdp": "Government revenue (% GDP)",
}


def _latest_value(result: FetchResult, indicator_key: str, defaults_used: List[str],
                   baseline_years: Dict[str, int]) -> float:
    default = BASELINE_DEFAULTS[indicator_key]
    if not result.available:
        defaults_used.append(indicator_key)
        return default
    latest_year = max(result.values)
    baseline_years[indicator_key] = latest_year
    return result.values[latest_year]


def run_scenario(country_iso3: str, panel: Dict[str, FetchResult], levers: ScenarioLevers) -> ScenarioResult:
    defaults_used: List[str] = []
    baseline_years: Dict[str, int] = {}

    baseline_debt = _latest_value(panel["debt_gdp"], "debt_gdp", defaults_used, baseline_years)
    baseline_growth = _latest_value(panel["gdp_growth"], "gdp_growth", defaults_used, baseline_years)
    baseline_inflation = _latest_value(panel["inflation"], "inflation", defaults_used, baseline_years)
    baseline_unemployment = _latest_value(panel["unemployment"], "unemployment", defaults_used, baseline_years)
    baseline_rate = _latest_value(panel["real_interest_rate"], "real_interest_rate", defaults_used, baseline_years)
    baseline_pb = _latest_value(panel["net_lending_borrowing"], "net_lending_borrowing", defaults_used, baseline_years)
    baseline_revenue = _latest_value(panel["government_revenue_gdp"], "government_revenue_gdp", defaults_used, baseline_years)

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
        defaults_used=defaults_used,
        baseline_years=baseline_years,
    )
