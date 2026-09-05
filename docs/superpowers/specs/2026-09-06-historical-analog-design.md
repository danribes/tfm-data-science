# Historical Analog Feature — Design Spec
_España en escenarios · 2026-09-06_

## Purpose

When a user configures a macro scenario (10 levers + horizon), they can request
the three closest real historical episodes that shared Spain's projected macro
state. For each match the feature shows: how that episode actually evolved, the
structural differences between that country and Spain, and a rationale for
whether the outcome is likely to transfer.

---

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Similarity basis | Macro state (primary) + dominant lever bonus (20%) | Economic honesty: match what the country *was*, not just what policy was applied |
| Outcome window | User's horizon (truncated + flagged if data ends early) | Consistent with scenario view |
| Narration | Rule-based diff always; LLM prose when RAG available | Matches project's "no invented data" contract; degrades to template on public deploy |
| Trigger | On-demand button | Avoids double API traffic on every lever drag |
| Panel source | Static gold file frozen at 2026-07-31 | Consistent with project's frozen-vintage philosophy |

---

## 1. Data Layer

### 1.1 New gold file: `data/gold/gold_analog_panel.csv`

Built by `scripts/build_analog_panel.py`. Frozen at vintage `2026-07-31`.
Provenance logged to `manifest.csv` (same pattern as `refresh_vintage.py`).

**Columns:**

| Column | Type | Description | Source |
|---|---|---|---|
| `iso3` | str | ISO 3166-1 alpha-3 | — |
| `year` | int | Calendar year | — |
| `debt_gdp` | float | Gross govt debt % GDP | WB / IMF WEO |
| `primary_balance_gdp` | float | Primary balance % GDP | IMF WEO |
| `interest_rate_10y` | float | Nominal 10yr bond yield % | WB / OECD |
| `gdp_growth` | float | Real GDP growth % | WB |
| `unemployment` | float | Unemployment rate % | WB |
| `inflation` | float | CPI inflation % | WB |
| `emu_member` | int | 1 if EMU member in that year | static list |
| `fx_regime` | str | `fixed` / `float` / `peg` | Ilzetzki-Reinhart-Rogoff |
| `ext_debt_share` | float | External debt / total debt % | WB |
| `democracy` | float | Polity5 score –10…+10 | INSCR |
| `trade_openness` | float | (X+M) / GDP % | WB |

**Coverage target:** ≥120 countries, 1980–2023. Rows with missing `debt_gdp`
or `primary_balance_gdp` are dropped. ESP rows are included in the file but
excluded at search time.

### 1.2 New stats file: `data/gold/gold_analog_panel_stats.json`

Written by the same build script. Contains per-feature mean and std for
z-score normalisation, computed over the full panel (ESP included, so Spain's
normalised query vector is comparable). Shape:

```json
{ "debt_gdp": {"mean": 62.4, "std": 31.1}, … }
```

---

## 2. Search Engine (`engine/analog.py`)

### 2.1 Query vector

Six macro variables extracted from the existing `/scenario` year-1 output:

```
q = [debt_gdp, primary_balance_gdp, interest_rate_10y,
     gdp_growth, unemployment, inflation]
```

Normalised with the stats file z-scores.

### 2.2 Distance metric

Mahalanobis distance on the 6 normalised features (accounts for inter-variable
correlations, e.g. debt–yield). Falls back to weighted Euclidean if the
covariance matrix is ill-conditioned (condition number > 1e12).

### 2.3 Dominant lever bonus

Detect the lever with the largest absolute delta from baseline (normalised by
lever range). Boost panel rows where that variable was anomalous (>1σ from the
country's own rolling mean). Weight: 20% of total score. The macro distance
remains the primary driver.

### 2.4 Exclusions

- `iso3 == "ESP"` — always excluded
- Rows where the forward outcome window has <3 complete years of data
- Rows where `debt_gdp` is null

### 2.5 Output

Top 3 matches sorted by score ascending (lower = closer). Each match carries:
- Identity: `iso3`, `year`, `country_name`
- Match snapshot: 6 macro values at match year
- Outcome trajectory: `debt_gdp`, `gdp_growth`, `primary_balance_gdp`
  for t+1 … t+horizon (each point has `truncated: bool`)
- Structural features: 6 diff columns
- `dominant_lever`: lever key that drove the bonus

### 2.6 Panel loading

Loaded once at API startup into a module-level DataFrame (same pattern as
`PERSONAS` and `RED_LINES`). No per-request I/O.

---

## 3. API

### 3.1 Endpoint

`POST /scenario/analog`

Request body: existing `ScenarioRequest` (levers + horizon) — no new schema.

### 3.2 Response schema (new models in `api/schemas.py`)

```python
class AnalogOutcomePoint(BaseModel):
    year_offset: int          # 1, 2, … horizon
    debt_gdp: float | None
    gdp_growth: float | None
    primary_balance_gdp: float | None
    truncated: bool

class StructuralDiff(BaseModel):
    dimension: str            # "emu_member", "fx_regime", …
    label: str                # human-readable Spanish label
    spain_value: str
    analog_value: str
    direction: str            # "converge" | "diverge" | "neutral"

class AnalogMatch(BaseModel):
    rank: int                 # 1, 2, 3
    iso3: str
    country_name: str
    match_year: int
    distance: float
    dominant_lever: str
    match_snapshot: dict[str, float]
    outcome: list[AnalogOutcomePoint]
    outcome_truncated: bool
    diffs: list[StructuralDiff]
    narrative: str | None     # None on public deploy

class AnalogResponse(ApiMeta):
    horizon: int
    query_snapshot: dict[str, float]
    matches: list[AnalogMatch]   # always 3, sorted by rank
    rag_available: bool
```

### 3.3 Narrative generation

When RAG is available (local deploy): single call to RAG chat internals with
a structured prompt. Passages retrieved from `macro`, `dsa`, and `espana`
collections. Response capped at 120 words.

Prompt template:
```
[country] en [year] partió de [snapshot]. En [horizon] años la deuda pasó
de X% a Y%. Las diferencias estructurales clave respecto a España son
[diverge dims]. ¿Converge o diverge el resultado? Cita solo los pasajes
recuperados.
```

When RAG unavailable (public deploy): `narrative` is `None`; `rag_available`
is `False`. The frontend renders a deterministic template string instead. No
503 is surfaced to the client.

---

## 4. Structural Diff

Six dimensions, computed deterministically in `engine/analog.py`:

| Dimension | `direction` logic |
|---|---|
| `emu_member` | `diverge` if analog not EMU (no FX adjustment, shared monetary policy) |
| `fx_regime` | `diverge` if analog had float (devaluation path available to them) |
| `ext_debt_share` | `diverge` if gap >20pp (rollover and sudden-stop risk differ) |
| `democracy` | `diverge` if analog Polity5 <6 (reform capacity and credibility differ) |
| `trade_openness` | `neutral` if within ±15pp; `converge`/`diverge` outside |
| `debt_maturity` | Proxied by ext_debt_share; `diverge` if analog had materially shorter maturity |

`direction` semantics: `converge` → structural similarity makes historical
outcome more transferable; `diverge` → gap that likely changed the trajectory;
`neutral` → gap too small to matter.

**Fallback narrative template** (deterministic, no LLM):
```
[Country, year]: deuda pasó de X% a Y% en N años.
Diferencias estructurales clave: [diverge dims].
El resultado histórico [puede / no puede] extrapolarse
directamente a España por [top diverge reason].
```

---

## 5. Frontend

### 5.1 Placement

Collapsible panel at the bottom of `/escenario`, below the redlines section.
Closed by default. Header: "Análogos históricos".

### 5.2 Components

| Component | Responsibility |
|---|---|
| `AnalogPanel.tsx` | Collapsible wrapper, "Buscar análogo histórico" button, loading state, error state |
| `AnalogCard.tsx` | Single match card; 3-tab selector for rank 1/2/3 |
| `AnalogDiffRow.tsx` | One structural diff row with converge/diverge/neutral icon |

`ProjectionChart` reused for the outcome trajectory (supports multiple series
+ `labels` prop for real calendar years).

### 5.3 Card layout (per match)

```
┌─────────────────────────────────────────────────┐
│ 🇮🇪 Irlanda · 2010   distancia: 0.42            │
│ Palanca dominante: tipo de interés (+320 pb)    │
├─────────────────────────────────────────────────┤
│ SITUACIÓN EN EL MOMENTO                         │
│  Deuda 86%  │  Saldo –8.1%  │  Paro 14.1%      │
├─────────────────────────────────────────────────┤
│ TRAYECTORIA (N años)                            │
│  [ProjectionChart: outcome vs Spain scenario]   │
├─────────────────────────────────────────────────┤
│ DIFERENCIAS ESTRUCTURALES                       │
│  ✓ Zona euro: Sí / Sí → converge               │
│  ✗ Deuda externa: 78% / 51% → diverge          │
│  …                                              │
├─────────────────────────────────────────────────┤
│ VALORACIÓN                                      │
│  [narrative prose or deterministic template]    │
│  ⚠ Análisis local — no disponible en despliegue │
└─────────────────────────────────────────────────┘
```

### 5.4 MSW mock

`POST /scenario/analog` mock added to the existing handler set. Returns 3
hardcoded matches (Ireland 2010, Portugal 2011, Belgium 1993). Tests run fully
offline.

---

## 6. Testing

### 6.1 Python (pytest)

| Test | Assertion |
|---|---|
| `test_analog_panel_schema` | CSV exists, required columns present, no nulls in key fields, ≥100 rows |
| `test_analog_no_spain` | No match has iso3=ESP |
| `test_analog_search_returns_3` | `find_analogs()` returns exactly 3 for any valid query |
| `test_analog_outcome_truncation` | Match near 2023 has `truncated=True` on later points |
| `test_analog_diff_directions` | `direction` ∈ `{converge, diverge, neutral}` for all diffs |
| `test_analog_endpoint_smoke` | `POST /scenario/analog` with defaults → 200, 3 matches |
| `test_analog_narrative_none_without_rag` | RAG mocked unavailable → `narrative=None`, no exception |
| `test_dominant_lever_bonus` | Moving `tip` far shifts ranking toward high-yield episodes |

### 6.2 Frontend (Vitest + MSW)

| Test | Assertion |
|---|---|
| `AnalogPanel renders closed by default` | Button visible, card hidden |
| `AnalogPanel opens on button click` | Panel expands, spinner shown |
| `AnalogCard renders all 3 tabs` | Tab switcher cycles rank 1/2/3 |
| `AnalogDiffRow converge/diverge icons` | Correct icon per direction value |
| `narrative absent → template shown` | Falls back cleanly when `rag_available=false` |

---

## 7. Files changed

| File | Action |
|---|---|
| `scripts/build_analog_panel.py` | New — builds and freezes the gold panel |
| `data/gold/gold_analog_panel.csv` | New — frozen panel |
| `data/gold/gold_analog_panel_stats.json` | New — normalisation stats |
| `engine/analog.py` | New — KNN search + diff logic |
| `api/schemas.py` | Edit — add 4 new response models |
| `api/main.py` | Edit — add `POST /scenario/analog` endpoint |
| `tests/test_analog.py` | New — 8 Python tests |
| `frontend/src/components/AnalogPanel.tsx` | New |
| `frontend/src/components/AnalogCard.tsx` | New |
| `frontend/src/components/AnalogDiffRow.tsx` | New |
| `frontend/src/routes/Escenario.tsx` | Edit — mount `AnalogPanel` at bottom |
| `frontend/src/api/types.ts` | Edit — add analog response types |
| `frontend/src/mocks/handlers.ts` | Edit — add analog mock handler |
| `frontend/src/__tests__/AnalogPanel.test.tsx` | New — 5 frontend tests |

---

## 8. Out of scope

- Multi-country comparison (analog vs analog) — not requested
- Updating the analog panel without a full vintage refresh — by design
- Lever attribution card (already a known gap in the frontend README)
- Showing more than 3 analogs
