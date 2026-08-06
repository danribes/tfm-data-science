from dataclasses import dataclass
from typing import Dict

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
