import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier

from scripts.train_stress_model import leave_one_country_out_cv, FEATURES
from engine.ml_stress_score import FiscalStressModel


def _synthetic_panel() -> pd.DataFrame:
    rng = np.random.RandomState(0)
    rows = []
    for country, base_debt, label_rate in [
        ("AAA", 40.0, 0.1), ("BBB", 90.0, 0.6), ("CCC", 60.0, 0.3), ("DDD", 110.0, 0.7),
    ]:
        for year in range(2005, 2013):
            label = 1 if rng.random_sample() < label_rate else 0
            rows.append({
                "country_iso3": country, "year": year, "label": label,
                "debt_gdp": base_debt + rng.normal(0, 5), "gdp_growth": rng.normal(2.0, 1.5),
                "inflation": rng.normal(2.5, 1.0), "unemployment": rng.normal(8.0, 2.0),
                "real_interest_rate": rng.normal(1.5, 1.0),
                "net_lending_borrowing": rng.normal(-2.0, 1.5),
                "corruption_control": rng.normal(0.3, 0.5),
            })
    return pd.DataFrame(rows)


def test_loco_cv_produces_non_degenerate_metrics():
    df = _synthetic_panel()
    metrics = leave_one_country_out_cv(df)
    assert metrics["n_brier_folds"] > 0
    assert 0.0 <= metrics["mean_brier"] <= 1.0
    if metrics["mean_auc"] is not None:
        assert 0.0 <= metrics["mean_auc"] <= 1.0


def test_trained_model_predicts_probabilities_in_unit_interval():
    df = _synthetic_panel()
    model = GradientBoostingClassifier(random_state=0)
    model.fit(df[FEATURES], df["label"])
    probs = model.predict_proba(df[FEATURES])[:, 1]
    assert np.all(probs >= 0.0) and np.all(probs <= 1.0)


def test_model_wrapper_reports_unavailable_when_artifact_missing(tmp_path, monkeypatch):
    import engine.ml_stress_score as mod
    monkeypatch.setattr(mod, "MODEL_PATH", tmp_path / "nonexistent.joblib")
    model = mod.FiscalStressModel()
    result = model.score({f: 0.0 for f in mod.FEATURES})
    assert result.available is False
    assert result.score is None
    assert "not found" in result.error
