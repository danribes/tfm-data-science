"""Satellite equations for fiscal-scenario modeling: Okun's law, Phillips curve, wage/pension indexation."""

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
