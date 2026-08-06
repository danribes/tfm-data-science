"""Ported MVP engine tests (spec §7 test_generic_engine.py).
Concatenated verbatim from archive/mvp-app-v1/tests/, imports rewritten
to engine.generic / data.live.models."""


# ---- ported from archive/mvp-app-v1/tests/test_debt_engine.py ----
import json
from pathlib import Path

from engine.generic import project_debt_path

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_country_panel.json"
TOLERANCE_PP = 12.0  # accounts for the documented proxy mismatches (overall balance vs primary balance;
                      # whole-economy real rate vs effective sovereign rate) -- see fixture source_note


def _load_fixture():
    return json.loads(FIXTURE_PATH.read_text())


def test_debt_identity_reproduces_real_one_step_transitions_within_tolerance():
    fixture = _load_fixture()
    debt = {int(y): v for y, v in fixture["debt_gdp"].items()}
    growth = {int(y): v for y, v in fixture["gdp_growth"].items()}
    rate = {int(y): v for y, v in fixture["real_interest_rate"].items()}
    balance = {int(y): v for y, v in fixture["net_lending_borrowing"].items()}

    for year in range(2015, 2022):
        path = project_debt_path(
            initial_debt_gdp_pct=debt[year - 1],
            r_path_pct=[rate[year]],
            g_path_pct=[growth[year]],
            pb_path_pct=[balance[year]],
            start_year=year,
        )
        projected = path[0].debt_gdp_pct
        actual = debt[year]
        assert abs(projected - actual) <= TOLERANCE_PP, (
            f"{year}: projected {projected:.2f} vs actual {actual:.2f} exceeds {TOLERANCE_PP}pp tolerance"
        )


def test_higher_interest_rate_worsens_debt_path_monotonically():
    base = project_debt_path(80.0, [2.0] * 5, [2.0] * 5, [0.0] * 5, start_year=2025)
    higher_r = project_debt_path(80.0, [4.0] * 5, [2.0] * 5, [0.0] * 5, start_year=2025)
    for b, h in zip(base, higher_r):
        assert h.debt_gdp_pct >= b.debt_gdp_pct


def test_lower_growth_worsens_debt_path_monotonically():
    base = project_debt_path(80.0, [2.0] * 5, [2.0] * 5, [0.0] * 5, start_year=2025)
    lower_g = project_debt_path(80.0, [2.0] * 5, [0.5] * 5, [0.0] * 5, start_year=2025)
    for b, l in zip(base, lower_g):
        assert l.debt_gdp_pct >= b.debt_gdp_pct


def test_length_mismatch_raises():
    import pytest
    with pytest.raises(ValueError):
        project_debt_path(80.0, [2.0, 2.0], [2.0], [0.0, 0.0], start_year=2025)


# ---- ported from archive/mvp-app-v1/tests/test_satellite_equations.py ----
from engine.generic import okun_unemployment_gap, phillips_inflation, indexed_growth, OKUN_COEFFICIENT, PHILLIPS_SLOPE


def test_okun_zero_output_gap_gives_zero_unemployment_gap():
    assert okun_unemployment_gap(0.0) == 0.0


def test_okun_negative_output_gap_raises_unemployment():
    assert okun_unemployment_gap(-2.0) == OKUN_COEFFICIENT * 2.0


def test_phillips_baseline_with_no_gap_returns_base_inflation():
    assert phillips_inflation(2.0, 0.0) == 2.0


def test_phillips_tighter_labor_market_raises_inflation_pressure():
    tighter = phillips_inflation(2.0, -1.0)  # negative gap = unemployment below baseline = tight market
    assert tighter > 2.0


def test_indexed_growth_adds_delta_to_inflation():
    assert indexed_growth(2.5, 0.0) == 2.5
    assert indexed_growth(2.5, 1.0) == 3.5


# ---- ported from archive/mvp-app-v1/tests/test_fiscal_space.py ----
import pytest

from engine.generic import allocate_fiscal_space, SPENDING_CATEGORIES


def _equal_shares():
    return {c: 1.0 / len(SPENDING_CATEGORIES) for c in SPENDING_CATEGORIES}


def test_allocations_sum_to_total_spending():
    result = allocate_fiscal_space(35.0, 0.0, -2.0, _equal_shares())
    assert result.total_revenue_pct_gdp == 35.0
    assert result.total_spending_pct_gdp == pytest.approx(37.0)
    assert sum(result.allocations_pct_gdp.values()) == pytest.approx(37.0)


def test_tax_wedge_delta_shifts_revenue_and_spending():
    result = allocate_fiscal_space(35.0, 2.0, -2.0, _equal_shares())
    assert result.total_revenue_pct_gdp == 37.0
    assert result.total_spending_pct_gdp == pytest.approx(39.0)


def test_rejects_shares_not_summing_to_one():
    bad_shares = _equal_shares()
    bad_shares["health"] += 0.5
    with pytest.raises(ValueError):
        allocate_fiscal_space(35.0, 0.0, -2.0, bad_shares)


def test_rejects_missing_category():
    incomplete = _equal_shares()
    del incomplete["health"]
    with pytest.raises(ValueError):
        allocate_fiscal_space(35.0, 0.0, -2.0, incomplete)


# ---- ported from archive/mvp-app-v1/tests/test_scenario.py ----
import json
from pathlib import Path

from data.live.models import FetchResult
from engine.generic import ScenarioLevers, run_scenario, BASELINE_DEFAULTS

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


def test_output_gap_lever_moves_unemployment_inflation_and_debt():
    panel = _panel_with_defaults()
    base = run_scenario("XXX", panel, ScenarioLevers(horizon_years=5))
    recession = run_scenario(
        "XXX", panel,
        ScenarioLevers(horizon_years=5, output_gap_path_pct=[-4.0, -3.0, -2.0, -1.0, 0.0]),
    )
    # Negative output gap: unemployment up (Okun), inflation down (Phillips),
    # growth down so debt/GDP ends higher.
    assert recession.unemployment_path_pct[0] > base.unemployment_path_pct[0]
    assert recession.inflation_path_pct[0] < base.inflation_path_pct[0]
    assert recession.debt_path[-1].debt_gdp_pct > base.debt_path[-1].debt_gdp_pct
    # Baseline stays constant year over year; recession path is not constant.
    assert len(set(base.unemployment_path_pct)) == 1
    assert len(set(recession.unemployment_path_pct)) > 1


def test_contingent_shock_lever_raises_debt_path_from_year_one():
    panel = _panel_with_defaults()
    base = run_scenario("XXX", panel, ScenarioLevers(horizon_years=3))
    shocked = run_scenario(
        "XXX", panel,
        ScenarioLevers(horizon_years=3, contingent_shocks_pct=[10.0, 0.0, 0.0]),
    )
    first_year_jump = shocked.debt_path[0].debt_gdp_pct - base.debt_path[0].debt_gdp_pct
    assert abs(first_year_jump - 10.0) < 1e-9
    assert shocked.debt_path[-1].debt_gdp_pct > base.debt_path[-1].debt_gdp_pct


def test_list_levers_shorter_or_longer_than_horizon_are_normalized():
    panel = _panel_with_defaults()
    short = run_scenario(
        "XXX", panel,
        ScenarioLevers(horizon_years=5, output_gap_path_pct=[-2.0],
                       contingent_shocks_pct=[5.0, 0.0]),
    )
    assert len(short.unemployment_path_pct) == 5
    assert len(short.debt_path) == 5
    long = run_scenario(
        "XXX", panel,
        ScenarioLevers(horizon_years=2, output_gap_path_pct=[-2.0] * 10,
                       contingent_shocks_pct=[5.0] * 10),
    )
    assert len(long.unemployment_path_pct) == 2
    assert len(long.debt_path) == 2
