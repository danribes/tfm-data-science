# Sovereign Fiscal Scenario Explorer

Prototype: explore a country's fiscal sustainability under user-controlled
policy scenarios, through persona-specific dashboards. Real data only
(World Bank, Eurostat, OECD public APIs) -- see the in-app "Data &
Methodology" tab for sources, coverage, and known gaps.

All model outputs are labeled conditional projections under user-chosen
levers -- never forecasts, advice, or buy/sell/vote-style recommendations.

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Train the ML fiscal-stress model (one-time, offline)

```
python scripts/build_training_panel.py
python scripts/train_stress_model.py
```

This writes `models/fiscal_stress_model.joblib`, `models/feature_order.json`,
`models/training_scores.json`, and `models/METRICS.md`. Requires network
access (World Bank API + Reinhart-Rogoff-Trebesch crisis dataset). The app
runs fine without this step -- the fiscal-stress score just shows
"model unavailable" until it's done.

The shipped fiscal-stress score is a directional pattern-matching signal
against a small, heavily imbalanced historical panel -- not a validated
predictor. See `models/METRICS.md` (surfaced in the in-app Data &
Methodology tab) for the real, honestly-reported cross-validation metrics.

## Run

```
streamlit run app/main.py
```

## Manual smoke test

Run the app locally for two countries with very different data coverage to
confirm graceful degradation, that all 5 tabs render, and nothing crashes:

1. Select **Spain (ESP)** in the sidebar -- expect a high coverage badge,
   all tabs populated, and house-price / COFOG-derived metrics present.
2. Select a smaller/poorer, non-EU/OECD country (e.g. **Haiti (HTI)** or
   **Chad (TCD)**) -- expect a "limited data coverage" banner, several
   metrics showing "N/A -- not available for this country" instead of a
   crash, and a prominent warning above the tabs listing which of the seven
   baseline scenario indicators fell back to a generic calibration default
   for this country. The ML fiscal-stress score's six macro features always
   get a value (real, or the disclosed generic default above); corruption
   control has no fallback and is never substituted -- when it's unavailable
   for this country, the score shows an honest "model unavailable" /
   missing-feature message instead of scoring on a fabricated value. The
   score does not compute "from whichever macro features are available";
   it's all-seven-features-or-honestly-unavailable.
3. Click **Refresh data** in the sidebar and confirm the panel re-fetches
   without error.
4. On the **House-buyer/Landlord** tab, toggle to "Buy-to-let" for a
   non-EU/OECD country and confirm the house-price chart shows the
   "N/A -- house price data not available for this country" warning
   instead of fabricated numbers.
5. Move every scenario lever in the sidebar and confirm all 5 tabs update
   consistently (shared `st.session_state`).

## Automated smoke check

```
streamlit run app/main.py --server.headless true &
sleep 5
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8501
kill %1
```

Expected: prints `200`.

## Known gaps & limitations

- **Plain-English scenario parsing (design spec section 4.5) is not implemented
  in this MVP; LLM narratives are.** The design spec described a text box where
  a user could describe a scenario in plain English and have it parsed into
  lever settings when `ANTHROPIC_API_KEY` is set. That parsing box does not
  exist. What is implemented is the separate LLM-generated narrative captions
  on each persona tab (see `personas/narrative.py`), which summarize an
  already-run scenario in prose -- they do not accept or parse free-text input.
- See the in-app "Data & Methodology" tab for the full, live list of known
  gaps (data coverage limitations, calibrated engine constants and their
  generic-default fallback values, per-country baseline vintage, and Model
  Lab's lever-to-objective wiring).

## Tests

```
pytest
```
