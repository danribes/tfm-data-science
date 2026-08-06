from data.models import FetchResult
from engine.scenario import ScenarioLevers
from engine.pareto import compute_pareto_frontier, LEVER_BOUNDS


def _panel_with_defaults():
    keys = [
        "debt_gdp", "gdp_growth", "inflation", "unemployment",
        "real_interest_rate", "net_lending_borrowing", "government_revenue_gdp",
    ]
    return {k: FetchResult(values={}, source="worldbank", from_cache=False, fetched_at=0.0, error="no data")
            for k in keys}


def _to_min_vector(point):
    o = point.objectives
    return (o["final_debt_gdp_pct"], -o["health_education_funding_pct_gdp"], -o["welfare_wagebill_pct_gdp"])


def _dominates(a, b):
    return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))


def test_frontier_is_non_dominated():
    panel = _panel_with_defaults()
    base_levers = ScenarioLevers(horizon_years=5)
    frontier = compute_pareto_frontier("ESP", panel, base_levers, population_size=12, generations=5)
    assert len(frontier) > 0
    vectors = [_to_min_vector(p) for p in frontier]
    for i, vi in enumerate(vectors):
        for j, vj in enumerate(vectors):
            if i != j:
                assert not _dominates(vj, vi), f"point {i} dominated by point {j}"


def test_tighter_bounds_never_beat_looser_bounds():
    panel = _panel_with_defaults()
    base_levers = ScenarioLevers(horizon_years=5)
    tight_bounds = {k: (v[0] / 2.0, v[1] / 2.0) for k, v in LEVER_BOUNDS.items()}

    loose_frontier = compute_pareto_frontier("ESP", panel, base_levers, lever_bounds=LEVER_BOUNDS,
                                              population_size=12, generations=5)
    tight_frontier = compute_pareto_frontier("ESP", panel, base_levers, lever_bounds=tight_bounds,
                                              population_size=12, generations=5)

    best_loose = min(p.objectives["final_debt_gdp_pct"] for p in loose_frontier)
    best_tight = min(p.objectives["final_debt_gdp_pct"] for p in tight_frontier)
    assert best_tight >= best_loose - 1e-6
