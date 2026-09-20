import pytest
from engine.montecarlo import run_montecarlo


def test_zero_innovations_have_no_simulation_dispersion():
    result = run_montecarlo(n_paths=200, shock_scale=0, n_show=0)
    assert result.percentiles['p5'] == result.percentiles['p95']


def test_sensitivity_controls_expose_assumption_dependence():
    low = run_montecarlo(n_paths=1000, shock_scale=.5, rho=.5, n_show=0)
    high = run_montecarlo(n_paths=1000, shock_scale=1.5, rho=.96, n_show=0)
    width = lambda r: r.percentiles['p95'][-1] - r.percentiles['p5'][-1]
    assert width(high) > width(low) * 2


@pytest.mark.parametrize('kwargs', [{'rho': 1}, {'rho': -.1}, {'shock_scale': -1}, {'shock_scale': float('nan')}])
def test_invalid_research_controls_rejected(kwargs):
    with pytest.raises(ValueError):
        run_montecarlo(n_paths=100, **kwargs)
