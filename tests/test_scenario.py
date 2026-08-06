from data.models import FetchResult
from engine.scenario import ScenarioLevers, run_scenario


def _empty_result():
    return FetchResult(values={}, source="worldbank", from_cache=False, fetched_at=0.0, error="no data")


def _panel_with_defaults():
    keys = [
        "debt_gdp", "gdp_growth", "inflation", "unemployment",
        "real_interest_rate", "net_lending_borrowing", "government_revenue_gdp",
    ]
    return {k: _empty_result() for k in keys}


def test_run_scenario_falls_back_to_defaults_when_panel_empty():
    levers = ScenarioLevers(horizon_years=3)
    result = run_scenario("XXX", _panel_with_defaults(), levers)
    assert len(result.debt_path) == 3
    assert result.coverage_score == 0.0


def test_run_scenario_uses_real_revenue_when_available():
    panel = _panel_with_defaults()
    panel["government_revenue_gdp"] = FetchResult(
        values={2023: 29.65}, source="worldbank", from_cache=False, fetched_at=0.0, error=None
    )
    levers = ScenarioLevers(horizon_years=2)
    result = run_scenario("ESP", panel, levers)
    assert result.fiscal_space_by_year[0].total_revenue_pct_gdp == 29.65


def test_higher_indexation_delta_raises_wage_growth():
    panel = _panel_with_defaults()
    low = run_scenario("ESP", panel, ScenarioLevers(horizon_years=2, indexation_delta_pp=0.0))
    high = run_scenario("ESP", panel, ScenarioLevers(horizon_years=2, indexation_delta_pp=1.0))
    assert high.nominal_wage_growth_path_pct[0] > low.nominal_wage_growth_path_pct[0]
