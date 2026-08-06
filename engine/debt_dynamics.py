from dataclasses import dataclass
from typing import List, Optional


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
