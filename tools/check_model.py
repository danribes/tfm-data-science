"""Reproduce the model invariant and boundary audit without network access.

Run ``python -m tools.check_model``; optional ``--output PATH`` selects the report.
Negative-debt domain findings are recorded, not clipped or treated as forecasts.
"""
import argparse
import hashlib
import itertools
import json
import math
from dataclasses import asdict
from pathlib import Path
import numpy as np
from engine import constants as c
from engine.levers import LEVER_SPECS, PRESETS, Levers, preset_levers
from engine.spain import N_YEARS, Y0, SERIES_KEYS, french, run_scenario
from engine.montecarlo import mc_input_paths, run_montecarlo


def main(output: Path) -> None:
    seed = 20260920
    rng = np.random.default_rng(seed)
    cases = [('base', Levers())] + [(p['id'], preset_levers(p['id'])) for p in PRESETS]
    for j, values in enumerate(itertools.product(*[(s['min'], s['max']) for s in LEVER_SPECS])):
        cases.append((f'corner{j}', Levers(**dict(zip([s['id'] for s in LEVER_SPECS], values)))))
    for j in range(256):
        cases.append((f'random{j}', Levers(**{s['id']: float(rng.uniform(s['min'], s['max'])) for s in LEVER_SPECS})))
    report = {'engine_version': c.ENGINE_VERSION, 'scope': 'Invariant and boundary probes of the local model; not predictive validation', 'deterministic_seed': seed, 'n_scenarios': len(cases), 'n_corner_cases': 1024, 'n_random_cases': 256, 'n_years': N_YEARS, 'n_series': len(SERIES_KEYS), 'nonfinite': [], 'max_nominal_debt_identity_error': 0., 'max_reported_debt_flow_error': 0., 'violations': {}, 'extremes': {}}
    keys = ['b', 'u', 'ujuv', 'arop', 'sobre', 'precio', 'esf', 'pens', 'gnom']
    for key in keys:
        report['extremes'][key] = {'min': math.inf, 'min_case': None, 'max': -math.inf, 'max_case': None}
    lookup = dict(cases)
    for name, lev in cases:
        out = run_scenario(lev)
        bad = [key for key, values in out.items() if not np.all(np.isfinite(values))]
        if bad: report['nonfinite'].append({'case': name, 'series': bad})
        gdp, debt, prev_ratio = 100., c.load_central()[Y0 - 1]['deuda'], c.load_central()[Y0 - 1]['deuda']
        for k in range(N_YEARS):
            gdp *= 1 + out['gnom'][k] / 100
            interest = debt * out['ief'][k] / 100
            surplus = out['pb'][k] * gdp / 100 - interest
            debt -= surplus
            report['max_nominal_debt_identity_error'] = max(report['max_nominal_debt_identity_error'], abs(debt / gdp * 100 - out['b'][k]))
            report['max_reported_debt_flow_error'] = max(report['max_reported_debt_flow_error'], abs(out['b'][k] - (prev_ratio / (1 + out['gnom'][k]/100) - out['saldo'][k])))
            prev_ratio = out['b'][k]
        violations = {}
        if min(out['b']) < 0: violations['negative_gross_debt'] = min(out['b'])
        for key in ['u', 'ujuv', 'arop', 'sobre', 'temp']:
            if min(out[key]) < 0 or max(out[key]) > 100: violations[f'{key}_outside_0_100'] = [min(out[key]), max(out[key])]
        for kind, value in violations.items():
            entry = report['violations'].setdefault(kind, {'count': 0, 'example': {'case': name, 'value': value, 'levers': asdict(lev)}})
            entry['count'] += 1
        for key in keys:
            ext = report['extremes'][key]
            if min(out[key]) < ext['min']: ext.update(min=min(out[key]), min_case=name)
            if max(out[key]) > ext['max']: ext.update(max=max(out[key]), max_case=name)

    base = run_scenario(Levers())
    report['interest_base_2026'] = {'reported_pct_current_gdp': base['int'][0], 'independent_euros_pct_current_gdp': 100 * (105.6 * .0268) / 103.3, 'saldo_pct_current_gdp': base['saldo'][0], 'v16_previous_gdp_interest': 105.6 * .0268}
    spread = run_scenario(Levers(), alpha_spread=.04, b_crit=85.6)
    report['spread_20pp_excess'] = {'actual_addon_bps': spread['spread'][0] - c.BASE_LEVERS['prima'], 'expected_addon_bps': 80.0, 'effective_interest_addon_pp': spread['ief'][0] - base['ief'][0]}
    report['omega_zero_baseline_inflation'] = run_scenario(Levers(), omega=0)['pi'][0]
    mc_cases = cases[:9] + [(report['extremes']['b'][direction + '_case'], lookup[report['extremes']['b'][direction + '_case']]) for direction in ['min', 'max']]
    report.update(mc_runs=0, mc_failed=[], mc_min_p5=math.inf, mc_seed=101, mc_paths_per_run=257, mc_shown_per_run=60, mc_parameter_pairs=[{'rho': rho, 'shock_scale': scale} for rho, scale in [(0,1),(.96,0),(.96,1),(.96,1.5)]], mc_scenario_cases=[name for name, _ in mc_cases], mc_max_zero_shock_identity_error=0.)
    for name, lev in mc_cases:
        for rho, scale in [(0,1),(.96,0),(.96,1),(.96,1.5)]:
            mc = run_montecarlo(lev, n_paths=257, seed=101, n_show=60, rho=rho, shock_scale=scale)
            report['mc_runs'] += 1
            q = np.asarray([mc.percentiles[p] for p in ['p5','p25','p50','p75','p95']])
            if not np.isfinite(q).all() or not np.isfinite(mc.paths).all() or np.any(np.diff(q,axis=0)<0):
                report['mc_failed'].append({'case':name, 'rho':rho, 'scale':scale, 'failure':'nonfinite or unordered quantiles'})
            report['mc_min_p5'] = min(report['mc_min_p5'], float(q.min()))
            if scale == 0:
                _, ir, gr, pb = mc_input_paths(lev)
                b = c.load_central()[Y0 - 1]['deuda']
                expected = []
                for i in range(len(ir)):
                    b = b * (1 + ir[i]/100) / (1 + gr[i]/100) - pb[i]
                    expected.append(b)
                error = float(np.max(np.abs(q - np.asarray(expected))))
                report['mc_max_zero_shock_identity_error'] = max(error, report['mc_max_zero_shock_identity_error'])
                if error > 1e-8: report['mc_failed'].append({'case':name, 'rho':rho, 'scale':scale, 'failure':'zero-shock debt identity', 'error':error})
    report['optional_feedback'] = {'scope': 'Python-only function overrides, not HTTP or frontend controls', 'runs':0, 'nonfinite':[], 'omega':[0,.5,1], 'alpha_spread':[0,.01,.04], 'b_crit':110, 'max_debt': -math.inf}
    for name, lev in mc_cases:
        for omega, alpha in itertools.product([0,.5,1],[0,.01,.04]):
            out = run_scenario(lev, omega=omega, alpha_spread=alpha)
            report['optional_feedback']['runs'] += 1
            bad = [key for key, values in out.items() if not np.all(np.isfinite(values))]
            if bad: report['optional_feedback']['nonfinite'].append({'case':name, 'omega':omega, 'alpha_spread':alpha, 'series':bad})
            finite_debts = [v for v in out['b'] if math.isfinite(v)]
            report['optional_feedback']['max_debt'] = max(report['optional_feedback']['max_debt'], max(finite_debts))
    try: report['french_zero_rate'] = french(100000,0,300)
    except Exception as err: report['french_zero_rate'] = type(err).__name__
    report['interpretation'] = ['Negative values violate the label gross debt; the unrestricted recursion continues below zero without modeling assets. The API and UI warn when visible outputs leave this domain.', 'No clipping was applied. Finite values and invariant success do not establish economic plausibility or forecast calibration.', 'The French mortgage helper handles zero interest by equal principal payments; exposed mortgage rates remain positive because Euribor minimum zero has a positive fixed mortgage differential.', 'Monte Carlo zero-shock identity is against its own documented drift/fiscal-reaction backbone, not the distinct deterministic display path.']
    root = Path(__file__).resolve().parents[1]
    sources = [
        'engine/spain.py', 'engine/montecarlo.py', 'engine/constants.py',
        'engine/levers.py', 'tools/check_model.py', 'data/gold/estimated_params.json',
        'data/gold/kpis_perfiles.json', 'data/gold/gold_escenarios_deuda.csv',
        'data/gold/gold_projections.csv',
    ]
    report['source_sha256'] = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sources
    }
    output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:report[k] for k in ['n_scenarios','nonfinite','max_nominal_debt_identity_error','max_reported_debt_flow_error','violations','interest_base_2026','spread_20pp_excess','mc_runs','mc_failed','mc_max_zero_shock_identity_error','optional_feedback']},indent=2, allow_nan=False))

    if (report["nonfinite"] or report["mc_failed"] or report["optional_feedback"]["nonfinite"]
        or report["max_nominal_debt_identity_error"] > 1e-8
        or report["max_reported_debt_flow_error"] > 1e-8
        or abs(report["spread_20pp_excess"]["actual_addon_bps"] - 80) > 1e-8):
        raise SystemExit("Numerical or accounting failure; inspect the report.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "docs/eval/model-audit.json")
    main(parser.parse_args().output)
