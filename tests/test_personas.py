import sys

from personas.mortgage_banker import french_amortization_payment, build_mortgage_dashboard
from personas.house_buyer_landlord import build_buy_to_live_view, build_buy_to_let_view
from personas.retiree import build_retiree_dashboard
from personas import narrative as narrative_mod
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


def test_mortgage_dashboard_empty_paths_returns_empty_list_no_exception():
    views = build_mortgage_dashboard(
        sovereign_rate_path_pct=[], unemployment_path_pct=[], years=[],
        loan_principal=200000, loan_term_years=25, baseline_unemployment_pct=7.0,
    )
    assert views == []


def test_buy_to_let_reports_na_rental_yield_and_real_growth():
    views = build_buy_to_let_view({2020: 100.0, 2021: 110.0}, [2020, 2021])
    assert views[1].house_price_growth_pct == 10.0
    assert "N/A" in views[1].rental_yield_pct


def test_buy_to_let_view_empty_price_path_returns_none_growth_no_exception():
    views = build_buy_to_let_view({}, [2020, 2021])
    assert [v.house_price_growth_pct for v in views] == [None, None]
    assert all("N/A" in v.rental_yield_pct for v in views)


def test_buy_to_live_view_empty_years_returns_empty_list_no_exception():
    views = build_buy_to_live_view(
        sovereign_rate_path_pct=[], years=[], home_price=300000.0,
        down_payment_pct=20.0, loan_term_years=25, monthly_household_income=4000.0,
    )
    assert views == []


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


def test_retiree_dashboard_empty_wage_path_returns_empty_years_no_exception():
    scenario = ScenarioResult(
        country_iso3="ESP", debt_path=[], fiscal_space_by_year=[],
        unemployment_path_pct=[], inflation_path_pct=[],
        nominal_wage_growth_path_pct=[], coverage_score=0.0,
    )
    stress = StressScoreResult(score=None, percentile=None, available=False, error="model unavailable")
    dashboard = build_retiree_dashboard(scenario, stress, baseline_health_exp_gdp_pct=7.0)
    assert dashboard.years == []


def test_render_narrative_falls_back_to_template_when_llm_call_fails(monkeypatch):
    # Force the LLM path "on" and make the anthropic call fail without ever
    # touching the network -- render_narrative must still return the
    # template narrative, not raise.
    monkeypatch.setattr(narrative_mod, "llm_available", lambda: True)

    class _FakeAnthropicModule:
        class Anthropic:
            def __init__(self):
                raise RuntimeError("simulated failure -- no network call made")

    monkeypatch.setitem(sys.modules, "anthropic", _FakeAnthropicModule)

    kwargs = dict(year=2030, real_index=97.3, adequacy="82%")
    result = narrative_mod.render_narrative("retiree", "irrelevant summary", **kwargs)
    assert result == narrative_mod.render_template_narrative("retiree", **kwargs)
