from dataclasses import dataclass
from typing import Dict, List, Optional

from personas.mortgage_banker import french_amortization_payment, MORTGAGE_SPREAD_PP


@dataclass
class BuyToLiveYearView:
    year: int
    monthly_payment: float
    payment_to_income_pct: Optional[float]


@dataclass
class BuyToLetYearView:
    year: int
    house_price_index: Optional[float]
    house_price_growth_pct: Optional[float]
    rental_yield_pct: str


def build_buy_to_live_view(sovereign_rate_path_pct: List[float], years: List[int], home_price: float,
                            down_payment_pct: float, loan_term_years: int,
                            monthly_household_income: Optional[float]) -> List[BuyToLiveYearView]:
    principal = home_price * (1 - down_payment_pct / 100.0)
    views = []
    for year, rate in zip(years, sovereign_rate_path_pct):
        mortgage_rate = rate + MORTGAGE_SPREAD_PP
        payment = french_amortization_payment(principal, mortgage_rate, loan_term_years)
        ratio = (payment / monthly_household_income * 100.0) if monthly_household_income else None
        views.append(BuyToLiveYearView(year=year, monthly_payment=payment, payment_to_income_pct=ratio))
    return views


def build_buy_to_let_view(house_price_index_path: Dict[int, float], years: List[int]) -> List[BuyToLetYearView]:
    sorted_years = sorted(house_price_index_path)
    base_value = house_price_index_path.get(sorted_years[0]) if sorted_years else None
    views = []
    for year in years:
        value = house_price_index_path.get(year)
        growth = (value - base_value) / base_value * 100.0 if (value is not None and base_value) else None
        views.append(BuyToLetYearView(
            year=year, house_price_index=value, house_price_growth_pct=growth,
            rental_yield_pct="N/A -- no rent-price data source integrated in this MVP",
        ))
    return views
