"""Generic (non-Spain) country engine — the MVP chain ported verbatim.

Concatenation of archive/mvp-app-v1/engine/{debt_dynamics,satellite,fiscal_space,
scenario}.py with only import-path adjustments (spec §4.4). Generic calibration:
OKUN_COEFFICIENT = 0.5 and PHILLIPS_SLOPE = 0.3 — calibrated defaults, NOT
country-specific, and deliberately DISTINCT from the Spain engine's 0.48 / 0.22.
Honesty fields defaults_used / baseline_years are retained.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from data.live.models import FetchResult

@dataclass
class DebtPathPoint:
    year: int
    debt_gdp_pct: float
    interest_rate_pct: float
    growth_rate_pct: float
    primary_balance_pct: float
    contingent_shock_pct: float


def project_debt_path(initial_debt_gdp_pct: float, r_path_pct: List[float], g_path_pct: List[float],
                       pb_path_pct: List[float], start_year: int,
                       contingent_shocks_pct: Optional[List[float]] = None) -> List[DebtPathPoint]:
    n = len(r_path_pct)
    if not (len(g_path_pct) == n and len(pb_path_pct) == n):
        raise ValueError("r_path_pct, g_path_pct, and pb_path_pct must have the same length")
    shocks = contingent_shocks_pct if contingent_shocks_pct is not None else [0.0] * n

    path = []
    debt_ratio = initial_debt_gdp_pct / 100.0
    for i in range(n):
        r = r_path_pct[i] / 100.0
        g = g_path_pct[i] / 100.0
        pb = pb_path_pct[i] / 100.0
        c = shocks[i] / 100.0
        delta = (r - g) / (1 + g) * debt_ratio - pb + c
        debt_ratio = debt_ratio + delta
        path.append(DebtPathPoint(
            year=start_year + i,
            debt_gdp_pct=debt_ratio * 100.0,
            interest_rate_pct=r_path_pct[i],
            growth_rate_pct=g_path_pct[i],
            primary_balance_pct=pb_path_pct[i],
            contingent_shock_pct=shocks[i],
        ))
    return path


OKUN_COEFFICIENT = 0.5  # calibrated default (literature range 0.3-0.5 for advanced economies); not country-specific
PHILLIPS_SLOPE = 0.3    # calibrated default: inflation response per point of unemployment gap; not country-specific


def okun_unemployment_gap(output_gap_pct: float, okun_coefficient: float = OKUN_COEFFICIENT) -> float:
    """Okun's law: unemployment gap (pp) implied by an output gap (% of potential GDP)."""
    return -okun_coefficient * output_gap_pct


def phillips_inflation(base_inflation_pct: float, unemployment_gap_pp: float,
                        phillips_slope: float = PHILLIPS_SLOPE) -> float:
    """Phillips curve: inflation (%) given a baseline and an unemployment gap (pp, negative = tight labor market)."""
    return base_inflation_pct - phillips_slope * unemployment_gap_pp


def indexed_growth(inflation_pct: float, indexation_delta_pp: float) -> float:
    """Wage/pension indexation rule: nominal growth (%) = inflation + a policy indexation lever (pp above/below full CPI indexation)."""
    return inflation_pct + indexation_delta_pp


SPENDING_CATEGORIES = [
    "health",
    "education",
    "welfare",
    "public_wage_bill",
    "security",
    "infrastructure",
    "public_investment",
]


@dataclass
class FiscalSpaceResult:
    total_revenue_pct_gdp: float
    total_spending_pct_gdp: float
    primary_balance_pct_gdp: float
    allocations_pct_gdp: Dict[str, float]


def allocate_fiscal_space(
    gdp_pct_revenue: float,
    tax_wedge_delta_pp: float,
    primary_balance_target_pct: float,
    allocation_shares: Dict[str, float],
) -> FiscalSpaceResult:
    """Allocate fiscal space to spending categories.

    Args:
        gdp_pct_revenue: Revenue as % of GDP.
        tax_wedge_delta_pp: Tax wedge change in percentage points.
        primary_balance_target_pct: Primary balance target as % of GDP.
        allocation_shares: Fraction of total spending assigned to each of
            SPENDING_CATEGORIES; must sum to 1.0.

    Returns:
        FiscalSpaceResult with total revenue, total spending, primary balance,
        and allocations by category.

    Raises:
        ValueError: If allocation_shares is missing categories or does not sum to 1.0.
    """
    # Validate all categories are present
    missing = set(SPENDING_CATEGORIES) - set(allocation_shares)
    if missing:
        raise ValueError(f"allocation_shares missing categories: {missing}")

    # Validate shares sum to 1.0
    share_sum = sum(allocation_shares[c] for c in SPENDING_CATEGORIES)
    if abs(share_sum - 1.0) > 1e-6:
        raise ValueError(f"allocation_shares must sum to 1.0, got {share_sum}")

    # Calculate revenue and spending
    total_revenue = gdp_pct_revenue + tax_wedge_delta_pp
    total_spending = total_revenue - primary_balance_target_pct

    # Allocate spending to categories
    allocations = {
        cat: total_spending * allocation_shares[cat] for cat in SPENDING_CATEGORIES
    }

    return FiscalSpaceResult(
        total_revenue_pct_gdp=total_revenue,
        total_spending_pct_gdp=total_spending,
        primary_balance_pct_gdp=primary_balance_target_pct,
        allocations_pct_gdp=allocations,
    )


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


def _normalize_path(path: Optional[List[float]], n: int) -> List[float]:
    """Fit a list-valued lever to the projection horizon: pad with 0.0 or
    truncate, so a UI-supplied path can never trip the length check in
    project_debt_path."""
    if not path:
        return [0.0] * n
    if len(path) >= n:
        return list(path[:n])
    return list(path) + [0.0] * (n - len(path))


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
    output_gaps = _normalize_path(levers.output_gap_path_pct, n)
    shocks = _normalize_path(levers.contingent_shocks_pct, n)

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
