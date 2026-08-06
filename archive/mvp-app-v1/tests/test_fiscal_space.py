import pytest

from engine.fiscal_space import allocate_fiscal_space, SPENDING_CATEGORIES


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
