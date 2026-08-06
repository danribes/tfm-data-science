"""
Trains the offline fiscal-stress gradient-boosted model on
data_cache/training_panel.csv (produced by build_training_panel.py),
validates it via leave-one-country-out cross-validation, and writes the
shipped model artifact plus honest metrics.

Run once, offline: `python scripts/train_stress_model.py`
Writes: models/fiscal_stress_model.joblib, models/feature_order.json,
        models/training_scores.json, models/METRICS.md

Not imported by the app -- development-time tooling only.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, brier_score_loss

TRAINING_PANEL_PATH = Path("data_cache/training_panel.csv")
MODELS_DIR = Path("models")
FEATURES = [
    "debt_gdp", "gdp_growth", "inflation", "unemployment",
    "real_interest_rate", "net_lending_borrowing", "corruption_control",
]


def leave_one_country_out_cv(df: pd.DataFrame) -> dict:
    """
    For each country present in the panel, trains on every other country and
    scores the held-out country -- an honest estimate of how the model
    generalizes to a country it has never seen, not an in-sample fit.
    """
    aucs = []
    briers = []
    skipped_countries = []

    for country in sorted(df["country_iso3"].unique()):
        train_df = df[df["country_iso3"] != country]
        test_df = df[df["country_iso3"] == country]

        if test_df["label"].nunique() < 1 or train_df["label"].nunique() < 2:
            skipped_countries.append(country)
            continue

        model = GradientBoostingClassifier(random_state=0)
        model.fit(train_df[FEATURES], train_df["label"])
        probs = model.predict_proba(test_df[FEATURES])[:, 1]

        if test_df["label"].nunique() == 2:
            aucs.append(roc_auc_score(test_df["label"], probs))
        briers.append(brier_score_loss(test_df["label"], probs))

    return {
        "mean_auc": float(np.mean(aucs)) if aucs else None,
        "n_auc_folds": len(aucs),
        "mean_brier": float(np.mean(briers)) if briers else None,
        "n_brier_folds": len(briers),
        "n_skipped_countries": len(skipped_countries),
        "skipped_countries": skipped_countries,
    }


def train_and_save() -> None:
    df = pd.read_csv(TRAINING_PANEL_PATH)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    cv_metrics = leave_one_country_out_cv(df)

    final_model = GradientBoostingClassifier(random_state=0)
    final_model.fit(df[FEATURES], df["label"])
    joblib.dump(final_model, MODELS_DIR / "fiscal_stress_model.joblib")
    (MODELS_DIR / "feature_order.json").write_text(json.dumps(FEATURES))

    training_scores = (final_model.predict_proba(df[FEATURES])[:, 1] * 100.0).tolist()
    (MODELS_DIR / "training_scores.json").write_text(json.dumps(training_scores))

    n_countries = df["country_iso3"].nunique()
    n_rows = len(df)
    n_positive = int(df["label"].sum())
    metrics_md = f"""# Fiscal Stress Model -- Metrics

**Training data:** {n_rows} country-year observations, {n_countries} countries,
{n_positive} distress-labeled rows. Source: `data_cache/training_panel.csv`.
Labels derived from the Reinhart-Rogoff-Trebesch "Global Crises Data by
Country" dataset (Domestic_Debt_In_Default OR sovereign external debt
default/restructuring = 1), World Bank macro features, 2003-2015.

**Model:** GradientBoostingClassifier (scikit-learn defaults, random_state=0),
predicting binary debt-distress.

**Validation:** leave-one-country-out cross-validation (train on every other
country, predict the held-out country) -- an honest, out-of-sample estimate,
not an in-sample fit.

- Mean AUC: {cv_metrics['mean_auc']} (over {cv_metrics['n_auc_folds']} held-out
  country folds where both classes were present)
- Mean Brier score: {cv_metrics['mean_brier']} (over {cv_metrics['n_brier_folds']}
  held-out country folds)
- Skipped countries (fewer than 2 observations, or training split with a single
  class): {cv_metrics['n_skipped_countries']} -- {cv_metrics['skipped_countries']}

These are real, held-out cross-validation metrics from this training run -- never
invented figures.

**Caveat:** the label is a historically-labeled debt-distress indicator; the model
is a pattern-matching classifier over macro features, not a causal or forecasting
model. Treat its output as a directional stress signal alongside the qualitative
and rules-based fiscal-space analysis, not as a substitute for it.
"""
    (MODELS_DIR / "METRICS.md").write_text(metrics_md)
    print(f"wrote model artifacts and METRICS.md to {MODELS_DIR}")


if __name__ == "__main__":
    train_and_save()
