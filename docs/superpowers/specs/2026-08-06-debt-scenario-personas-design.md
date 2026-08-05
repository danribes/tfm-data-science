# Design: Sovereign Fiscal Scenario Explorer (persona dashboards)

Status: approved by user 2026-08-06
Author: Claude (session with Daniel Ribes)

## 1. Purpose & scope

Standalone prototype predicting/exploring a country's fiscal "payability" (debt
sustainability + service funding + workforce/welfare trade-offs) under
user-controlled policy scenarios, presented through persona-specific
dashboards.

**Explicit constraint (user decision):** built independently from scratch.
Does NOT reuse, port, or reference code/content from `evo_final_work_old`
(plan_maestro, TFM) or `evo_final_work_data` (design v01-v16 mockups). Any
resemblance to concepts there (e.g. persona tabs, lever sliders) is
coincidental convergent design, not derived.

**Country scope:** generic — any country selectable at runtime, not hardcoded
to one country or a fixed comparison set.

**Data:** real data only, pulled from public REST APIs (World Bank, OECD,
Eurostat). No illustrative/simulated figures presented as if real.

**Deliverable:** Python app, Streamlit, run locally via `streamlit run`.

**Phasing (Approach A — MVP-first):** build the full engine (data pipeline +
scenario model + ML stress score + Pareto trade-off explorer) solidly first.
Ship 3 persona dashboards initially: **Retiree**, **Mortgage Banker**,
**House-buyer/Landlord** (combined tab, buy-to-live vs. buy-to-let toggle).
Remaining personas (tenant, investment banker, public worker, entrepreneur,
young job-seeker, immigrant, politician, etc.) are explicitly out of scope for
this spec/plan — a fast-follow phase, separate spec.

## 2. Architecture & stack

```
evo_final_work/
  data/        connectors (World Bank/OECD/Eurostat REST clients), indicator
               catalog config, disk cache
  engine/      debt/scenario equations, ML stress-score model, Pareto optimizer
  personas/    persona configs + narrative generation (templated + optional LLM hook)
  app/         Streamlit UI (main.py entrypoint, one module per tab)
  scripts/     offline model training (run once, not at app runtime)
  models/      shipped trained model artifact + metrics report
  tests/       pytest, with committed fixture data (no network required)
  docs/
```

The app is standalone at runtime: it calls the public World Bank API, OECD
SDMX-JSON API, and Eurostat REST API directly over HTTP (via `requests`). It
does not depend on this chat session's MCP tool connections — those are only
used during development to explore/verify indicator codes.

Language: English (code, comments, UI, docs). Rationale: matches this design
conversation; independent from the Spanish-language TFM project by the
user's own "build independently" decision.

## 3. Data layer

### 3.1 Indicator catalog

A config file (`data/indicator_catalog.yaml`) maps each variable block to
concrete indicator codes, with an explicit source priority per block:

| Block | Primary source | Fallback | Universal coverage? |
|---|---|---|---|
| Debt/GDP, GDP growth, inflation | World Bank WDI | — | Yes |
| Unemployment | World Bank WDI | OECD | Yes |
| Government interest rate proxy (10y bond yield) | World Bank / IMF | OECD | Partial |
| Corruption (control-of-corruption) | World Bank WGI | — | Yes |
| Net migration | World Bank WDI | — | Yes |
| Health/education expenditure (% GDP) | World Bank WDI | OECD/Eurostat (functional detail) | Yes (aggregate), Partial (functional detail) |
| Public wage bill (compensation of employees, COFOG) | OECD/Eurostat COFOG | — | OECD+EU only |
| Public order/safety spend (COFOG GF03) | OECD/Eurostat COFOG | — | OECD+EU only |
| Social protection/welfare spend (COFOG GF10) | OECD/Eurostat COFOG | World Bank WDI (social protection, aggregate) | Partial |
| Infrastructure maintenance vs. renovation split | Eurostat/OECD | — | EU/OECD only, and even there often not split |
| Public investment (gross fixed capital formation, % GDP) | World Bank WDI | OECD | Yes |
| Pension spend (% GDP) | World Bank/OECD/Eurostat | — | Partial |
| House price index (housing-availability proxy) | Eurostat/OECD | — | EU/OECD only |
| Productivity (GDP per hours worked or per worker) | World Bank/OECD | — | Partial |

Each COFOG row is a distinct indicator code fetched independently — public
wage bill, security spend, and social-welfare spend are never merged into one
composite number.

### 3.2 Country coverage badge

On country selection, the app computes and displays a **coverage score**
(fraction of catalog indicators with real data available for that country) so
data-sparsity is visible up front, not discovered mid-exploration.

### 3.3 Caching

Disk cache under `data_cache/`, keyed by `(country_iso3, indicator_code)`,
stored as Parquet/JSON with a fetch timestamp. No automatic expiry (macro
data revises infrequently); a manual "Refresh data" button in the UI
re-fetches and overwrites cache for the current country.

## 4. Engine

### 4.1 Debt dynamics (core, deterministic)

Standard debt/GDP law of motion:

```
Δd_t = (r_t − g_t) / (1 + g_t) × d_{t−1} − pb_t + c_t
```

where `d` = debt/GDP, `r` = effective interest rate, `g` = real GDP growth,
`pb` = primary balance (% GDP), `c` = contingent liabilities shock (user
lever, default 0). Baseline `r`, `g`, `pb`, `d_0` calibrated from the
selected country's most recent real WDI data. Projected to a user-chosen
horizon (2026-2050 range, default annual steps).

### 4.2 Satellite equations (transparent, all constants visible in-UI)

- Okun's law: output-gap → unemployment-gap.
- Phillips curve: unemployment-gap → inflation.
- Wage/pension indexation rule: inflation + policy indexation lever → nominal
  wage/pension growth.
- Fiscal-space allocator: given total revenue (tax-wedge lever × GDP) and a
  primary-balance target, splits residual spending capacity across
  health/education/welfare/public-wage-bill/security/infrastructure/public-investment
  per user-set allocation-share levers; running below available data
  resolution (e.g. no real infra maintenance/renovation split for the
  country) marks that sub-allocation "illustrative split of an aggregate —
  not independently sourced" rather than presenting it as real.

All model constants (elasticities, pass-throughs) are named, visible in the
"Data & Methodology" tab, and documented with their source or "calibrated
default, not country-specific" label where a literature value wasn't found.

### 4.3 ML stress-score component

Gradient-boosted classifier/regressor (XGBoost or scikit-learn
GradientBoosting), trained **offline** (not at app runtime) on a real
cross-country panel built from World Bank WDI indicators, labeled using a
public historical fiscal/debt-crisis dataset (Reinhart-Rogoff crisis-dates
style list, or the closest publicly-available equivalent found during
implementation). Output: a 0-100 fiscal-stress score for the current
scenario's macro state, plus a percentile vs. the historical cross-country
distribution.

Validation: leave-one-country-out cross-validation, reported honestly
(AUC/Brier score) in `models/METRICS.md`, shipped alongside the model. This
is explicitly a pattern-matching signal, not a certified default predictor —
stated as such in the UI wherever the score is shown.

### 4.4 Pareto / multi-objective explorer

NSGA-II (`pymoo`) over policy levers (tax wedge, public-wage-bill delta,
welfare-spend delta, headcount delta) against objectives (final debt/GDP,
health+education funding adequacy vs. a baseline need, public headcount,
welfare spend). Produces a non-dominated frontier for the given country's
current calibration; user can click a frontier point to load its lever
values into the main scenario controls.

### 4.5 GenAI narrative layer (optional, degrades gracefully)

Default: deterministic template-based narrative per persona tab, driven off
computed scenario deltas — no external API call, works with zero
configuration.

If `ANTHROPIC_API_KEY` is set in the environment: swaps in LLM-generated
persona narratives, and enables a "describe a scenario in plain English" text
box that parses free text into lever-delta settings. Without the key, this
box is hidden/disabled with a short explanation, not silently broken.

## 5. Personas & UI (MVP scope)

Tabs, in order:

1. **Retiree** — pension purchasing power (nominal vs. real, indexation
   lever), fiscal-stress score, healthcare funding adequacy.
2. **Mortgage Banker** — interest-rate/spread pass-through to mortgage
   payments, household debt-service burden, default-risk proxy from
   unemployment + rate scenario.
3. **House-buyer/Landlord** — toggle between buy-to-live (affordability,
   payment-to-income) and buy-to-let (rental yield proxy, if house-price and
   rent data available for the country; else marked N/A) framings, sharing
   the same underlying mortgage/rate engine as tab 2.
4. **Model Lab** — Pareto frontier explorer (§4.4), raw scenario-lever panel.
5. **Data & Methodology** — sources, coverage badge per indicator, all engine
   constants with provenance, ML model metrics, explicit list of known gaps
   (data not available for many non-OECD/EU countries).

Scenario state (country + all levers) lives in Streamlit `session_state`,
shared across all tabs — moving a lever once updates every tab consistently.

No screen issues a "buy/sell/vote"-style recommendation; every output is a
labeled conditional projection ("if levers set to X, by year Y, indicator Z
is..."), never framed as a certainty or advice.

## 6. Error handling / data gaps

- Indicator missing for selected country/source → UI shows
  **"N/A — not available for this country"**, never a fabricated or
  interpolated-and-unlabeled number.
- API request fails (timeout, 4xx/5xx) → fall back to disk cache if present
  (with a "showing cached data from <date>" notice); if no cache, show a
  clear warning banner, block only the affected chart/metric, not the whole
  app.
- Country with low overall coverage score → an upfront banner:
  "Limited data coverage for this country ({score}%) — several
  metrics will show as unavailable."
- ML stress-score model file missing/fails to load → that specific
  score/gauge shows "model unavailable," rest of the app functions normally.

## 7. Testing

- `tests/test_debt_engine.py` — debt identity reproduces a committed
  real-data fixture's historical debt/GDP path within tolerance;
  parameter-sweep sanity (higher `r` or lower `g` worsens the path,
  monotonically).
- `tests/test_satellite_equations.py` — Okun/Phillips/indexation unit tests
  against known input/output pairs.
- `tests/test_ml_model.py` — trained model loads, produces probabilities in
  [0,1], leave-one-country-out metric computed and asserted non-degenerate
  (not testing for a specific accuracy bar, since sample size is small).
- `tests/test_pareto.py` — returned frontier is non-dominated; more
  constrained lever bounds never produce a strictly better frontier than
  looser bounds.
- `tests/test_data_layer.py` — mocked HTTP responses; cache write/read
  round-trip; missing-indicator path returns the N/A sentinel, never raises
  or fabricates.
- Manual smoke test (documented in implementation plan, not automated): run
  the app locally for 2 countries with different coverage (e.g. Spain =
  rich, a smaller/poorer country = sparse) and confirm graceful degradation,
  all 5 tabs render, no crash.

## 8. Explicitly out of scope (this spec)

- The 9+ remaining personas (tenant, investment banker, public worker,
  entrepreneur, young job-seeker, immigrant, politician, children/childhood,
  permanent/temporary-contract worker, self-employed) — fast-follow phase,
  separate design once the engine above is proven.
- Any reuse of `evo_final_work_old` or `evo_final_work_data` content.
- Deployment (Streamlit Community Cloud, Docker, etc.) — local run only for
  this phase.
- Real-time/live data streaming — data refresh is manual/on-demand.
- Individual-level tax/pricing personalization (legally distinct from the
  airline-pricing analog discussed earlier — public tax/pension systems
  require horizontal equity; this prototype does not attempt individual
  price discrimination).
