# Design: Consolidated App — Phase 2: Front end (editorial dashboard)

Status: approved by user 2026-08-07
Author: Claude (session with Daniel Ribes)

## 0. Context

Phase 1 (core) is merged to master: committed gold vintage `2026-07-31`, the
v16 Spain engine ported to Python, 12-persona dependents, Monte Carlo DSA,
v12 red lines, the A1–A5 anchor battery with the committed dual-engine
fixture, and a FastAPI service with a frozen pydantic contract. 150 tests
green. Spec: `2026-08-06-consolidated-core-design.md`.

This spec covers **phase 2: the front end** — the visible app.
Phase 3 (ML stress score, Pareto explorer, contests page) remains separate.

Binding inputs:

- **API contract** — `api/schemas.py` (frozen in phase 1).
- **Visual grammar** — `docs/superpowers/specs/references/v16-visual-grammar.md`
  (865 lines: exact palettes, component anatomy, layout system, chart
  approach, interaction model, and a "do not carry over" list).
- **Handoff items** — `docs/superpowers/phase2-handoff-notes.md` (6 binding
  items from the phase-1 final review; §7 below resolves each).
- **Design lineage** — `legacy/design_data/design/` v12 (red-line anchors),
  v14 (12-tab IA + design conventions), v15 (12 persona cards), v16
  (the working single-file app this front supersedes).

## 0.1 Locked decisions (user-approved)

| Question | Decision |
|---|---|
| Stack | React + Vite + TypeScript + Recharts |
| Look | v16 editorial-paper grammar, modernized (fluid layout, dark mode, motion) |
| First shippable scope | Full shell + 10 levers + presets + red lines + Monte Carlo + **4 personas** (01 Bonista, 02 Banca hipotecaria, 03 Comprador/inquilino, 06 Político) |
| Engine | Hybrid: TypeScript engine in-browser for instant lever response; Python API for Monte Carlo and generic countries; both bound to `tests/fixtures/engine_anchors.json` |
| Language | Spanish for the Spain experience (persona copy served verbatim by the API) |
| Country scope | Spain only in this phase (the generic-country UI is deferred; its API already exists) |

## 1. Purpose & scope

Build `frontend/` — a Vite dev server (`npm run dev` → `localhost:5173`) and
a production build (`npm run build` → static `dist/`) that renders the
phase-1 API as an editorial dashboard: infographic character, dashboard
interactivity.

**Deliverables**

1. Running app: shell, lever rail, 4 persona tabs, Laboratorio, Datos y método.
2. TypeScript engine passing the same anchor fixture the Python engine passes.
3. Vitest suite (engine parity, store/URL, component render) + a Playwright
   smoke spec. No live network in tests.
4. `frontend/README.md`: run, test, build, and the API dependency.

**Not in this phase:** the remaining 8 personas, the generic-country UI, ML
stress score, Pareto, auth, deployment.

## 2. Repo layout

```
evo_final_work/
  frontend/
    index.html
    package.json  vite.config.ts  tsconfig.json  vitest.config.ts
    playwright.config.ts
    src/
      main.tsx  App.tsx
      api/          client.ts (typed fetch), hooks.ts (React Query), types.ts
      engine/       constants.ts levers.ts spain.ts index.ts
      engine/__tests__/anchors.test.ts
      state/        scenarioStore.ts (Zustand + URL sync), theme.ts
      components/   Gauge.tsx LeverRail.tsx PresetBar.tsx Semaphore.tsx
                    Chain.tsx Stamp.tsx NarrativeBlock.tsx
                    ProjectionChart.tsx FanChart.tsx KpiRow.tsx
                    Warnings.tsx ThemeToggle.tsx
      personas/     registry.ts + one module per shipped persona
      routes/       Inicio.tsx Persona.tsx Laboratorio.tsx Metodologia.tsx
      styles/       tokens.css base.css (ported + modernized v16 grammar)
    e2e/            smoke.spec.ts
  (phase-1 tree unchanged: api/ engine/ data/ scripts/ tests/)
```

Node 20+, npm. `frontend/node_modules/` and `frontend/dist/` gitignored.

## 3. Data flow

- **Static reference data** (`/personas`, `/presets`, `/redlines`,
  `/constants`, `/vintage`, `/health`) is fetched once on load via React
  Query (`staleTime: Infinity`) — it is vintage-immutable.
- **Scenario computation** runs **in the browser** on every lever change via
  `src/engine`. No network round-trip; target < 16 ms per recompute so
  dragging is smooth.
- **Monte Carlo** calls `POST /scenario/montecarlo` (debounced 400 ms,
  cancel-previous) — the fan is Python-computed by design.
- **Cross-check on load:** the app calls `POST /scenario` once with base
  levers and compares the API's `scenario.b` against the local engine's at
  2026/2035/2050. A mismatch > 1e-6 renders a visible engine-mismatch banner
  (dev and prod) rather than silently diverging.
- **API base URL** from `VITE_API_BASE` (default `http://localhost:8000`).
  Fetch failure → a blocking, plain-language error screen naming the URL and
  the command to start the API. Never a blank page, never fabricated data.

## 4. Engine (TypeScript port)

`src/engine/spain.ts` is a line-faithful port of the same v16 chain the
Python engine implements (`engine/spain.py`, itself verified against
`docs/superpowers/plans/references/v16-engine-extract.md` §S1). Same
constants, same order of state updates, same 40 series keys, same
deviation semantics (all levers at base → outputs equal baseline).

`src/engine/constants.ts` is generated, not hand-typed: a committed script
(`frontend/scripts/gen-constants.mjs`) reads `engine/constants.py`'s exported
`CONSTANTS_TABLE` via the running API's `/constants` and writes the TS file,
so a constant can never drift between languages. The generated file is
committed; a test asserts it matches the fixture's values.

**Parity is enforced, not assumed.** `engine/__tests__/anchors.test.ts` reads
`tests/fixtures/engine_anchors.json` (the phase-1 committed fixture, imported
across the repo boundary via a Vite alias) and asserts:

- `debt_central` at 2026/2030/2035/2050 (tolerance 1e-6 against the fixture's
  `engine` values);
- `cuota_2026_base` (± 0.01);
- `presets_series_2035_2050` — all 8 presets × 7 series (± 1e-6);
- `probe_bundle` — the all-10-lever scenario (± 1e-6);
- `base_gold_identity` — base `ief`/`gnom`/`pb` (± 1e-9).

The fixture's `montecarlo_seed42` block is **explicitly not** asserted: NumPy
PCG64 draws are not reproducible in JS. The MC acceptance rule is the gold
envelope ±2 pp, checked against the API response, per handoff note 2.

## 5. Visual system

Tokens live in `src/styles/tokens.css` as CSS custom properties, ported from
the grammar reference and extended:

- **Palette** — paper `#f7f5f0`, ink `#1a1a1a`, signature blue `#2a78d6`,
  plus semantic `--st-crossed` / `--st-near` / `--st-safe` for the semaphore.
  A `[data-theme="dark"]` block supplies the dark palette (new in this phase;
  v16 had none). Theme choice persists in `localStorage`, defaulting to
  `prefers-color-scheme`.
- **Typography** — the v16 stack, `font-variant-numeric: tabular-nums` on
  every figure, `es-ES` number formatting (decimal comma) through one shared
  `fmt()` helper — never ad-hoc `toFixed` at call sites.
- **Spacing** — 8-pt scale replacing v16's ad-hoc values.
- **Layout** — fluid CSS grid replacing v16's fixed 1680×1080 scale-to-fit
  canvas: a sticky 300 px lever rail + a main column that reflows; usable
  from 1280 px up, and the rail collapses to a drawer below 1024 px.

**Motion** (absent in v16, added here): number roll-ups on figure change
(~180 ms), chart path transitions, and gauge-fill transitions. All motion is
disabled under `prefers-reduced-motion: reduce`.

**Charts** — Recharts for time series and the fan:
`ProjectionChart` draws the dotted baseline plus the solid scenario line, with
`ReferenceLine`s for any red line bound to that series; `FanChart` draws the
p5–p95 band, the p25–p75 band, and the p50 line. Gauges, transmission chains,
stamps, and the semaphore are **hand-written SVG/CSS components** — the
editorial character lives there and Recharts offers nothing for them.

**Stamps** are computed from state, never authored: levers at base + horizon
"hoy" → 📅 (observed); anything else → 🔮 (conditional projection).

## 6. Pages

| Route | Content |
|---|---|
| `/` Inicio | Vintage + coverage banner, the scenario's headline figures (debt 2050, deficit, unemployment, CPI), red-line semaphore, and cards linking to each persona |
| `/persona/:id` | The v14 rhythm: 5 KPI gauges → 2 charts → semaphore + transmission chain + narrative. Renders generically from the API's persona card (`pill`, `h1`, `meta`, `hot`, `outs`, `reds`, `headline`) + the local engine's series. Shipped: `01`, `02`, `03`, `06` |
| `/laboratorio` | Full series explorer (pick any of the 40), the Monte Carlo fan with its ±2 pp gold-envelope note, and the raw lever panel |
| `/metodologia` | The 31 constants with provenance, the vintage and its staleness note, red-line thresholds with sources, the engine-parity statement, and a known-gaps list |

The lever rail is persistent across all routes — the scenario you build
follows you between personas. That was v16's core argument and it survives.

## 7. Handoff-note resolutions (phase-1 final review)

1. **MC engine home** — resolved: **server-side**. The front never reruns the
   fan locally, so `/constants` needs no schema change this phase.
2. **JS MC acceptance rule** — the fan is validated against the gold envelope
   ±2 pp; the fixture's seed-42 pins bind Python only. Stated in `Metodologia`.
3. **`ipvreal` is derived** — `src/engine/derived.ts` computes
   `ipvreal = ipv − pi`, exactly as v16's front did. Persona 02's red line
   reads it from there; a unit test pins it.
4. **`/scenario` returns the full 2026–2050 series regardless of `horizon`** —
   the front slices for display and never re-truncates.
5. **Persona display reds ≠ global RED_LINES** — persona `reds` (from
   `/personas`) render inside the persona's own semaphore; `/redlines`
   renders the global semaphore. They are never merged, and `Metodologia`
   explains the difference (e.g. "Sobrecarga > 40 % renta" with threshold
   15.0 is a population share, not an income share).
6. **Dual-engine contract** — §4 above.

## 8. Error handling

- API unreachable → blocking screen with the URL and the start command.
- Any single endpoint failing → that surface degrades to an explicit "no
  disponible" state; the rest of the app keeps working.
- `defaults_used` / stale-vintage warnings from the API render as visible
  banners (inherited honesty requirement, non-negotiable).
- Engine mismatch (§3) → visible banner.
- No screen issues buy/sell/vote advice: a standing "proyección condicional,
  no recomendación" notice is part of the shell, and `computed_not_advice`
  from the API drives it.

## 9. Testing

| Suite | Covers |
|---|---|
| `engine/__tests__/anchors.test.ts` | The dual-engine contract (§4) — the load-bearing test of this phase |
| `engine/__tests__/derived.test.ts` | `ipvreal` and any other derived series |
| `state/__tests__/store.test.ts` | Lever set/reset, preset application, URL round-trip (`?p=…&r=…`), persistence across route changes |
| `components/__tests__/*.test.tsx` | Gauge/Semaphore/Stamp/Chart render from fixed props; stamp switches 📅→🔮 on a lever move; red-line status colors match status strings |
| `routes/__tests__/persona.test.tsx` | Each shipped persona renders from a mocked API payload with no missing-key crashes |
| `e2e/smoke.spec.ts` (Playwright) | Boot, move a lever, assert a gauge figure and a chart path change, switch persona, confirm the scenario persisted, toggle theme, no console errors |

All tests run offline: the API is mocked (MSW) in unit tests; the Playwright
smoke runs against a Vite preview with a mocked API layer. `npm test` runs
vitest; `npm run e2e` runs Playwright.

## 10. Out of scope (this phase)

- Personas 04, 05, 07, 08, 09, 10, 11, 12 (fast-follow; the renderer is
  already generic, so each is configuration plus a check).
- Generic-country UI (the API exists; the front comes later).
- ML stress score, Pareto explorer, contests page (phase 3).
- Auth, deployment, SSR, i18n framework (Spanish is hardcoded by decision).
- Any change to phase-1 Python code, `data/gold/`, or the committed fixture.
