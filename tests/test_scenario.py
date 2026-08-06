import json
from pathlib import Path

from data.models import FetchResult
from engine.scenario import ScenarioLevers, run_scenario, BASELINE_DEFAULTS

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_country_panel.json"

BASELINE_KEYS = [
    "debt_gdp", "gdp_growth", "inflation", "unemployment",
    "real_interest_rate", "net_lending_borrowing", "government_revenue_gdp",
]


def _empty_result():
    return FetchResult(values={}, source="worldbank", from_cache=False, fetched_at=0.0, error="no data")


def _panel_with_defaults():
    return {k: _empty_result() for k in BASELINE_KEYS}


def _panel_from_fixture():
    """Build a panel from the committed real-data fixture. Any of the seven
    baseline keys absent from the fixture (or present but empty) are wired
    up as genuinely unavailable, matching how build_country_panel would
    represent a missing indicator.
    """
    raw = json.loads(FIXTURE_PATH.read_text())
    panel = {}
    for key in BASELINE_KEYS:
        values = raw.get(key)
        if values:
            panel[key] = FetchResult(
                values={int(year): v for year, v in values.items()},
                source="worldbank", from_cache=False, fetched_at=0.0, error=None,
            )
        else:
            panel[key] = _empty_result()
    return panel


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


def test_run_scenario_reports_all_seven_defaults_used_when_panel_all_unavailable():
    levers = ScenarioLevers(horizon_years=2)
    result = run_scenario("XXX", _panel_with_defaults(), levers)
    assert set(result.defaults_used) == set(BASELINE_KEYS)
    assert result.baseline_years == {}


def test_run_scenario_defaults_used_reflects_only_genuinely_missing_indicators_on_fixture():
    panel = _panel_from_fixture()
    levers = ScenarioLevers(horizon_years=2)
    result = run_scenario("USA", panel, levers)

    # The fixture carries real data for these four -- they must NOT fall
    # back to a generic default, and their baseline year must be the fixture's
    # latest available year for that indicator.
    for key in ["debt_gdp", "gdp_growth", "real_interest_rate", "net_lending_borrowing"]:
        assert key not in result.defaults_used
        assert key in result.baseline_years

    assert result.baseline_years["debt_gdp"] == 2021
    assert result.baseline_years["gdp_growth"] == 2021
    assert result.baseline_years["real_interest_rate"] == 2021
    assert result.baseline_years["net_lending_borrowing"] == 2021

    # The fixture has no inflation, unemployment, or government_revenue_gdp
    # series -- those three, and only those three, must fall back to defaults.
    assert set(result.defaults_used) == {"inflation", "unemployment", "government_revenue_gdp"}
