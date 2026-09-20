"""Reproducible sensitivity of conditional Monte Carlo bands, not coverage testing.

    python -m research.uncertainty

Changes the assumed innovation scale and AR(1) persistence independently.
All scenarios use the same seed (common random numbers). A separate seed/path
count comparison distinguishes Monte Carlo numerical variability from model
assumptions. No observations are scored and no predictive coverage is claimed.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from engine import constants as c
from engine.montecarlo import run_montecarlo

ROOT = Path(__file__).resolve().parents[1]


def summarize(*, rho=.96, shock_scale=1.0, n_paths=4000, seed=42):
    result = run_montecarlo(rho=rho, shock_scale=shock_scale, n_paths=n_paths, seed=seed, n_show=0)
    return {"rho": rho, "shock_scale": shock_scale, "n_paths": n_paths, "seed": seed,
            "years": {str(year): {
                **{q: round(result.percentiles[q][year - 2026], 6) for q in ('p5', 'p50', 'p95')},
                "width_p5_p95": round(result.percentiles['p95'][year - 2026] - result.percentiles['p5'][year - 2026], 6),
            } for year in (2030, 2050, 2070)}}


def evaluate():
    return {
        "engine_version": c.ENGINE_VERSION, "scenario_reference_vintage": c.VINTAGE,
        "evaluation_kind": "conditional_simulation_sensitivity",
        "empirical_coverage_validated": False,
        "limitations": ["The shock distribution and fiscal reaction remain calibrated.",
                        "Innovation draws are independent across r, g and primary balance.",
                        "Parameter uncertainty, structural breaks and policy adaptation are not estimated.",
                        "Matching the inherited gold envelope is an implementation check, not predictive validation."],
        "input_sha256": {f: hashlib.sha256((c.GOLD_DIR / f).read_bytes()).hexdigest()
                         for f in ('gold_escenarios_deuda.csv', 'kpis_perfiles.json')},
        "assumption_sensitivity": [summarize(rho=rho, shock_scale=scale)
                                   for rho in (.5, .8, .96) for scale in (.5, 1., 1.5)],
        "sampling_sensitivity": [summarize(n_paths=n, seed=seed)
                                 for n in (1000, 4000) for seed in (17, 42, 73)],
    }


if __name__ == '__main__':
    output = ROOT / 'docs/eval/montecarlo-sensitivity.json'
    output.write_text(json.dumps(evaluate(), indent=2) + '\n')
    print(f'Wrote {output}')
