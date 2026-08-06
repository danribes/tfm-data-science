from personas.mortgage_banker import french_amortization_payment, build_mortgage_dashboard
from personas.house_buyer_landlord import build_buy_to_let_view
from personas.retiree import build_retiree_dashboard
from engine.scenario import ScenarioResult
from engine.debt_dynamics import DebtPathPoint
from engine.fiscal_space import allocate_fiscal_space, SPENDING_CATEGORIES
from engine.ml_stress_score import StressScoreResult


def test_french_amortization_known_case():
    payment = french_amortization_payment(200000, 3.0, 25)
    assert 900 < payment < 1000


def test_mortgage_dashboard_risk_increases_with_unemployment():
    views = build_mortgage_dashboard(
        sovereign_rate_path_pct=[2.0, 2.0], unemployment_path_pct=[7.0, 12.0],
        years=[2025, 2026], loan_principal=200000, loan_term_years=25, baseline_unemployment_pct=7.0,
    )
    assert views[1].default_risk_proxy > views[0].default_risk_proxy


def test_buy_to_let_reports_na_rental_yield_and_real_growth():
    views = build_buy_to_let_view({2020: 100.0, 2021: 110.0}, [2020, 2021])
    assert views[1].house_price_growth_pct == 10.0
    assert "N/A" in views[1].rental_yield_pct


def _fake_scenario():
    shares = {c: 1.0 / len(SPENDING_CATEGORIES) for c in SPENDING_CATEGORIES}
    fiscal = [allocate_fiscal_space(35.0, 0.0, -2.0, shares) for _ in range(2)]
    debt_path = [
        DebtPathPoint(2025, 80.0, 2.0, 2.0, -2.0, 0.0),
        DebtPathPoint(2026, 81.0, 2.0, 2.0, -2.0, 0.0),
    ]
    return ScenarioResult(
        country_iso3="ESP", debt_path=debt_path, fiscal_space_by_year=fiscal,
        unemployment_path_pct=[7.0, 7.0], inflation_path_pct=[2.0, 2.0],
        nominal_wage_growth_path_pct=[2.0, 2.0], coverage_score=1.0,
    )


def test_retiree_dashboard_tracks_real_pension_purchasing_power():
    scenario = _fake_scenario()
    stress = StressScoreResult(score=40.0, percentile=50.0, available=True)
    dashboard = build_retiree_dashboard(scenario, stress, baseline_health_exp_gdp_pct=7.0)
    assert len(dashboard.years) == 2
    # wage growth == inflation each year -> real index stays at 100
    assert abs(dashboard.years[-1].real_pension_index - 100.0) < 1e-6
