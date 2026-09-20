"""Export the actual descriptive matching population and current neighbours.

    python -m tools.evaluate_analogs

This is a reproducibility record, not a predictive benchmark. The legacy
`gold_analog_panel_stats.json` is preserved provenance and is not loaded by the
current engine. Runtime scaling uses complete non-Spanish rows through 2020.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from engine import analog
from engine.constants import ENGINE_VERSION, GOLD_DIR
from engine.levers import Levers


def main():
    panel = analog.ANALOG_PANEL
    eligible = panel[(panel.iso3 != 'ESP') & (panel.year <= 2020)]
    complete = eligible.replace([np.inf, -np.inf], np.nan).dropna(subset=analog.QUERY_FEATURES)
    report = {
        'engine_version': ENGINE_VERSION, 'evaluation_kind': 'descriptive_reproducibility',
        'predictive_validation_completed': False,
        'source_sha256': hashlib.sha256((GOLD_DIR / 'gold_analog_panel.csv').read_bytes()).hexdigest(),
        'features': analog.QUERY_FEATURES, 'n_eligible': len(eligible), 'n_complete': len(complete),
        'n_countries': int(complete.iso3.nunique()),
        'years': [int(complete.year.min()), int(complete.year.max())],
        'normalization': analog._STATS,
        'inverse_covariance_standardized': analog._COV_INV.tolist(),
        'missingness_policy': 'complete cases; no average imputation',
        'distance': 'Mahalanobis in standardized coordinates; no lever bonus',
        'legacy_stats_used': False, 'limitations': analog.LIMITATIONS,
        'baseline_matches': {str(year): analog.find_analogs(Levers(), horizon=max(1, year-2026), query_year=year)
                             for year in (2026, 2036, 2050)},
    }
    path = Path(__file__).resolve().parents[1] / 'docs/eval/analog-metric.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f'Wrote {path}')


if __name__ == '__main__':
    main()
