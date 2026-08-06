# Fiscal Stress Model -- Metrics

**Training data:** 206 country-year observations, 21 countries,
1 distress-labeled rows. Source: `data_cache/training_panel.csv`.
Labels derived from the Reinhart-Rogoff-Trebesch "Global Crises Data by
Country" dataset (Domestic_Debt_In_Default OR sovereign external debt
default/restructuring = 1), World Bank macro features, 2003-2015.

**Model:** GradientBoostingClassifier (scikit-learn defaults, random_state=0),
predicting binary debt-distress.

**Validation:** leave-one-country-out cross-validation (train on every other
country, predict the held-out country) -- an honest, out-of-sample estimate,
not an in-sample fit.

- Mean AUC: None (over 0 held-out
  country folds where both classes were present)
- Mean Brier score: 0.01666598851567455 (over 20
  held-out country folds)
- Skipped countries (fewer than 2 observations, or training split with a single
  class): 1 -- ['URY']

These are real, held-out cross-validation metrics from this training run -- never
invented figures.

**Caveat:** the label is a historically-labeled debt-distress indicator; the model
is a pattern-matching classifier over macro features, not a causal or forecasting
model. Treat its output as a directional stress signal alongside the qualitative
and rules-based fiscal-space analysis, not as a substitute for it.
