import json
from pathlib import Path

from engine.debt_dynamics import project_debt_path

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
