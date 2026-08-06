from dataclasses import dataclass
from typing import List

MORTGAGE_SPREAD_PP = 1.5  # calibrated default: typical mortgage rate over the sovereign real-rate baseline; not country-specific
DEFAULT_RISK_UNEMPLOYMENT_WEIGHT = 0.6  # calibrated default, not empirically fit
DEFAULT_RISK_RATE_WEIGHT = 0.4          # calibrated default, not empirically fit


@dataclass
class MortgageYearView:
    year: int
    mortgage_rate_pct: float
    monthly_payment: float
    default_risk_proxy: float


def french_amortization_payment(principal: float, annual_rate_pct: float, term_years: int) -> float:
    monthly_rate = (annual_rate_pct / 100.0) / 12.0
    n_payments = term_years * 12
    if monthly_rate == 0:
        return principal / n_payments
    return principal * monthly_rate / (1 - (1 + monthly_rate) ** (-n_payments))


def build_mortgage_dashboard(sovereign_rate_path_pct: List[float], unemployment_path_pct: List[float],
                              years: List[int], loan_principal: float, loan_term_years: int,
                              baseline_unemployment_pct: float) -> List[MortgageYearView]:
    views = []
    baseline_mortgage_rate = sovereign_rate_path_pct[0] + MORTGAGE_SPREAD_PP
    for year, rate, unemployment in zip(years, sovereign_rate_path_pct, unemployment_path_pct):
        mortgage_rate = rate + MORTGAGE_SPREAD_PP
        payment = french_amortization_payment(loan_principal, mortgage_rate, loan_term_years)
        unemployment_gap = unemployment - baseline_unemployment_pct
        rate_gap = mortgage_rate - baseline_mortgage_rate
        risk = (DEFAULT_RISK_UNEMPLOYMENT_WEIGHT * max(0.0, unemployment_gap)
                + DEFAULT_RISK_RATE_WEIGHT * max(0.0, rate_gap))
        views.append(MortgageYearView(year=year, mortgage_rate_pct=mortgage_rate,
                                       monthly_payment=payment, default_risk_proxy=risk))
    return views
