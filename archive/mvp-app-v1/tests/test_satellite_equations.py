from engine.satellite import okun_unemployment_gap, phillips_inflation, indexed_growth, OKUN_COEFFICIENT, PHILLIPS_SLOPE


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
