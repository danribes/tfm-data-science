# Phase 2 — Front End (Editorial Dashboard) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `frontend/` — a React 19 + Vite 8 + TypeScript editorial dashboard over the phase-1 FastAPI service, with an in-browser TS port of the v16 Spain engine proven equal to the Python engine by the committed dual-engine fixture.

**Architecture:** A persistent 10-lever rail drives an in-browser `runScenario()` (line-faithful TS port of `engine/spain.py`); all reference data (`/personas`, `/presets`, `/redlines`, `/constants`, `/vintage`, `/health`) is fetched once via TanStack Query; only Monte Carlo round-trips to the server (`POST /scenario/montecarlo`, debounced 400 ms). Four routes (Inicio, Persona genérica ×4, Laboratorio, Metodología) render the v16 editorial grammar (flat-bar gauges, semáforo, cadenas, narrativa in hand-written SVG/CSS; time series and fan in Recharts) with fluid layout, dark mode, and reduced-motion support — none of which v16 had.

**Tech Stack:** React 19, Vite 8, TypeScript 7, Recharts 3, Zustand 5, TanStack Query 5, React Router 7, MSW 2 (test mocking), Vitest 4, Testing Library 16, Playwright 1.62. Node 20+ floor (machine runs Node 22.22.0 / npm 10.9.4).

## Global Constraints

- Spec of record: `docs/superpowers/specs/2026-08-07-phase2-frontend-design.md` — §2 layout, §3 data flow, §4 engine parity, §5 visual system, §6 pages, §7 handoff resolutions, §8 error handling, §9 testing are binding.
- Everything lives under `frontend/`. **No change to phase-1 Python code, `data/gold/`, or `tests/fixtures/engine_anchors.json`.**
- Node 20+, npm. `frontend/node_modules/`, `frontend/dist/`, Playwright artifacts gitignored (via `frontend/.gitignore`, so the root tree is untouched).
- Dependency pins (verified against the npm registry on 2026-08-07): `vite ^8.2.1`, `@vitejs/plugin-react ^6.0.5`, `react`/`react-dom ^19.2.8`, `typescript ^7.0.2`, `recharts ^3.10.1`, `zustand ^5.0.14`, `@tanstack/react-query ^5.101.4`, `react-router-dom ^7.18.2`, `msw ^2.15.0`, `vitest ^4.1.10`, `@testing-library/react ^16.3.2`, `@playwright/test ^1.62.1`.
- React 19 idioms only: no `React.FC`, no default `import React`, automatic JSX runtime (`"jsx": "react-jsx"`).
- All UI copy is **Spanish**. Persona copy (`pill`, `h1`, `meta`, `outs[].lab`, `reds[].t/x`) and preset labels come from the API **verbatim** — never re-authored. Chrome copy this plan authors is Spanish too.
- All numbers render through `src/lib/fmt.ts` (`nf`/`sg`/`eur`, `es-ES`, decimal comma, U+2212 minus) — **never** ad-hoc `toFixed` at a call site. `font-variant-numeric: tabular-nums` app-wide.
- Scenario recompute is local and synchronous (< 16 ms — the engine is 25 iterations over 40 series). Monte Carlo is **server-side only**, never ported to JS (handoff note 1).
- Engine parity tolerances (spec §4): `debt_central` ±1e-6 vs fixture `engine` values; `cuota_2026_base` ±0.01; `presets_series_2035_2050` (8 presets × 7 series × 2 years) ±1e-6; `probe_bundle` ±1e-6; `base_gold_identity` ±1e-9. The fixture's `montecarlo_seed42` block is **explicitly not asserted in TS** (NumPy PCG64 is not reproducible in JS; the MC acceptance rule is the gold envelope ±2 pp, stated in Metodología — handoff note 2).
- No live network in tests: unit tests mock the API with MSW (node server); the Playwright smoke runs a Vite preview built with `VITE_MOCK_API=1` (MSW browser worker).
- Honesty gates (spec §8, non-negotiable): API unreachable → blocking screen naming the URL and the start command; single endpoint down → local "no disponible" state; stale vintage and engine mismatch → visible banners; standing "proyección condicional, no recomendación" notice in the shell driven by `computed_not_advice`.
- Dark mode via `[data-theme="dark"]` on `<html>`, persisted in `localStorage("theme")`, defaulting to `prefers-color-scheme`. All motion disabled under `prefers-reduced-motion: reduce`.
- Commits: one per task, `feat(frontend): …` / `test(frontend): …` conventional style, run from the repo root.

## File Structure

```
frontend/
  .gitignore  index.html  package.json  README.md
  vite.config.ts  vitest.config.ts  tsconfig.json  playwright.config.ts
  scripts/gen-constants.mjs          ← generator: API /constants + ../data/gold → TS
  public/mockServiceWorker.js        ← generated once by `npx msw init public/`
  e2e/smoke.spec.ts
  src/
    main.tsx  App.tsx
    lib/fmt.ts                       ← nf/sg/eur (es-ES, U+2212)
    lib/motion.ts                    ← useReducedMotion + useRollup (~180 ms)
    api/types.ts  api/client.ts  api/hooks.ts
    engine/constants.ts              ← GENERATED (named constants), committed
    engine/vintage.ts                ← GENERATED (V0, BASE_LEVERS, CENTRAL, OLDDEP), committed
    engine/levers.ts  engine/spain.ts  engine/derived.ts  engine/redlines.ts  engine/index.ts
    engine/__tests__/constants.test.ts  anchors.test.ts  spain.test.ts  derived.test.ts  redlines.test.ts
    state/scenarioStore.ts  state/theme.ts
    state/__tests__/store.test.ts  theme.test.ts
    components/Stamp.tsx  Gauge.tsx  Semaphore.tsx  Chain.tsx  NarrativeBlock.tsx  KpiRow.tsx
    components/ProjectionChart.tsx  FanChart.tsx  LeverRail.tsx  PresetBar.tsx
    components/Warnings.tsx  ThemeToggle.tsx  ApiDownScreen.tsx
    components/__tests__/*.test.tsx
    personas/registry.ts  personas/p01_bonista.ts  p02_banca.ts  p03_comprador.ts  p06_politico.ts
    routes/Inicio.tsx  Persona.tsx  Laboratorio.tsx  Metodologia.tsx
    routes/__tests__/inicio.test.tsx  persona.test.tsx  laboratorio.test.tsx  metodologia.test.tsx
    styles/tokens.css  styles/base.css
    test/setup.ts  test/msw/handlers.ts  test/msw/server.ts  test/msw/browser.ts  test/msw/fixtures.ts
tests/fixtures/engine_anchors.json   ← phase-1, read-only, imported via alias @fixtures
```

Responsibilities: `engine/` is pure (no React, no fetch); `api/` is typed I/O only; `state/` owns the lever vector + horizon + URL sync; `components/` are presentational (props in, DOM out); `routes/` compose; `personas/*.ts` hold only what the API card does **not** carry (v16 chains + narrative templates, Spanish, verbatim from the v16 extract).

---

### Task 1: Scaffold, design tokens, formatting and theme helpers

**Files:**
- Create: `frontend/package.json`, `frontend/.gitignore`, `frontend/index.html`, `frontend/vite.config.ts`, `frontend/vitest.config.ts`, `frontend/tsconfig.json`
- Create: `frontend/src/styles/tokens.css`, `frontend/src/styles/base.css`
- Create: `frontend/src/lib/fmt.ts`, `frontend/src/state/theme.ts`
- Create: `frontend/src/main.tsx`, `frontend/src/App.tsx` (minimal placeholders, replaced in Task 11)
- Test: `frontend/src/lib/__tests__/fmt.test.ts`, `frontend/src/state/__tests__/theme.test.ts`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: `nf(v: number | null | undefined, d: number): string`, `sg(v: number, d: number): string`, `eur(v: number): string` from `src/lib/fmt.ts`; `initTheme(): void`, `setTheme(t: "light" | "dark"): void`, `getTheme(): "light" | "dark"` from `src/state/theme.ts`; CSS custom properties (`--page`, `--ink`, `--lab`, `--st-crossed`…) and component classes (`.out`, `.gaugebar`, `.rl-item`, `.ch`, `.narr`, `.lev`, `.ps`, `.badge-fwd`, `.card`, `.legend`) used by every later component task; the `@fixtures` alias used by Task 5.

- [ ] **Step 1: Write `package.json`, configs, `.gitignore`, `index.html`**

`frontend/package.json`:

```json
{
  "name": "evo-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "engines": { "node": ">=20" },
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "build:mock": "tsc -b && vite build --mode mock",
    "preview": "vite preview --port 4173 --strictPort",
    "test": "vitest run",
    "test:watch": "vitest",
    "e2e": "playwright test",
    "gen:constants": "node scripts/gen-constants.mjs"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.101.4",
    "react": "^19.2.8",
    "react-dom": "^19.2.8",
    "react-router-dom": "^7.18.2",
    "recharts": "^3.10.1",
    "zustand": "^5.0.14"
  },
  "devDependencies": {
    "@playwright/test": "^1.62.1",
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.3.2",
    "@testing-library/user-event": "^14.6.1",
    "@types/node": "^22.10.0",
    "@types/react": "^19.2.0",
    "@types/react-dom": "^19.2.0",
    "@vitejs/plugin-react": "^6.0.5",
    "jsdom": "^26.0.0",
    "msw": "^2.15.0",
    "typescript": "^7.0.2",
    "vite": "^8.2.1",
    "vitest": "^4.1.10"
  }
}
```

`frontend/.gitignore`:

```
node_modules/
dist/
playwright-report/
test-results/
```

`frontend/index.html`:

```html
<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>España en escenarios — proyección condicional, no recomendación</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

`frontend/vite.config.ts` (Vite 8; the `@fixtures` alias crosses the `frontend/` boundary to the phase-1 fixture and is load-bearing for Task 5):

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@fixtures": path.resolve(__dirname, "../tests/fixtures"),
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: { fs: { allow: [path.resolve(__dirname, ".."), __dirname] } },
});
```

`frontend/vitest.config.ts`:

```ts
import { defineConfig, mergeConfig } from "vitest/config";
import viteConfig from "./vite.config";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: "jsdom",
      globals: false,
      setupFiles: ["./src/test/setup.ts"],
      include: ["src/**/*.test.{ts,tsx}"],
    },
  }),
);
```

`frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "resolveJsonModule": true,
    "verbatimModuleSyntax": true,
    "skipLibCheck": true,
    "noEmit": true,
    "types": ["vite/client"],
    "paths": {
      "@fixtures/*": ["../tests/fixtures/*"],
      "@/*": ["./src/*"]
    }
  },
  "include": ["src", "e2e", "vite.config.ts", "vitest.config.ts", "playwright.config.ts"]
}
```

`frontend/src/test/setup.ts`:

```ts
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 2: Write the failing tests for `fmt` and `theme`**

`frontend/src/lib/__tests__/fmt.test.ts` — expectations are the v16 helpers' documented behavior (grammar §A.3: `es-ES`, U+2212 minus, `s/d` for non-finite, `sg` always signed, `eur` integer):

```ts
import { describe, expect, it } from "vitest";
import { nf, sg, eur } from "../fmt";

describe("fmt — es-ES, decimal comma, U+2212 minus (v16 nf/sg/eur)", () => {
  it("nf formats with fixed decimals and decimal comma", () => {
    expect(nf(3.42, 2)).toBe("3,42");
    expect(nf(10.1, 1)).toBe("10,1");
    expect(nf(45, 0)).toBe("45");
  });
  it("nf uses U+2212 for negatives", () => {
    expect(nf(-3.0, 1)).toBe("−3,0");
  });
  it("nf returns s/d for null/undefined/non-finite", () => {
    expect(nf(null, 1)).toBe("s/d");
    expect(nf(undefined, 1)).toBe("s/d");
    expect(nf(Number.NaN, 1)).toBe("s/d");
    expect(nf(Infinity, 1)).toBe("s/d");
  });
  it("sg always prefixes an explicit sign", () => {
    expect(sg(0.16, 2)).toBe("+0,16");
    expect(sg(-0.5, 1)).toBe("−0,5");
    expect(sg(0, 1)).toBe("+0,0");
  });
  it("eur groups thousands with dot and drops decimals", () => {
    expect(eur(171444)).toBe("171.444");
    expect(eur(744.9971)).toBe("745");
    expect(eur(-1500)).toBe("−1.500");
  });
});
```

`frontend/src/state/__tests__/theme.test.ts`:

```ts
import { beforeEach, describe, expect, it } from "vitest";
import { getTheme, initTheme, setTheme } from "../theme";

describe("theme — data-theme attribute + localStorage persistence", () => {
  beforeEach(() => {
    localStorage.clear();
    delete document.documentElement.dataset.theme;
  });
  it("initTheme defaults to light when no preference stored (jsdom matchMedia is non-matching)", () => {
    initTheme();
    expect(document.documentElement.dataset.theme).toBe("light");
  });
  it("setTheme stamps the attribute and persists", () => {
    initTheme();
    setTheme("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(localStorage.getItem("theme")).toBe("dark");
    expect(getTheme()).toBe("dark");
  });
  it("initTheme honors a stored choice over the OS default", () => {
    localStorage.setItem("theme", "dark");
    initTheme();
    expect(document.documentElement.dataset.theme).toBe("dark");
  });
});
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd frontend && npm install && npx vitest run src/lib src/state`
Expected: FAIL — `Cannot find module '../fmt'` and `Cannot find module '../theme'`.

Note: jsdom lacks `window.matchMedia`; `theme.ts` must guard it (`typeof window.matchMedia === "function"`), so no matchMedia stub is needed in setup.

- [ ] **Step 4: Implement `fmt.ts` and `theme.ts`**

`frontend/src/lib/fmt.ts` (line-faithful port of `v16_perfiles_lab.html` L243–246):

```ts
/** v16 number helpers — es-ES, decimal comma, U+2212 minus. Never use toFixed in UI code. */
export function nf(v: number | null | undefined, d: number): string {
  if (v === null || v === undefined || !isFinite(v)) return "s/d";
  return new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: d,
    maximumFractionDigits: d,
  })
    .format(v)
    .replace("-", "−");
}

/** Signed delta: always an explicit +/− prefix. */
export function sg(v: number, d: number): string {
  return (v >= 0 ? "+" : "−") + nf(Math.abs(v), d);
}

/** Big absolute numbers (EUR, counts): no decimals, dot thousands. */
export function eur(v: number): string {
  return new Intl.NumberFormat("es-ES", { maximumFractionDigits: 0 })
    .format(v)
    .replace("-", "−");
}
```

`frontend/src/state/theme.ts`:

```ts
export type Theme = "light" | "dark";
const KEY = "theme";

function osPrefers(): Theme {
  if (typeof window.matchMedia === "function" && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }
  return "light";
}

export function getTheme(): Theme {
  return (document.documentElement.dataset.theme as Theme) ?? "light";
}

export function setTheme(t: Theme): void {
  document.documentElement.dataset.theme = t;
  localStorage.setItem(KEY, t);
}

export function initTheme(): void {
  const stored = localStorage.getItem(KEY) as Theme | null;
  document.documentElement.dataset.theme = stored ?? osPrefers();
}

export function toggleTheme(): Theme {
  const next: Theme = getTheme() === "dark" ? "light" : "dark";
  setTheme(next);
  return next;
}
```

- [ ] **Step 5: Write `tokens.css` and `base.css`**

`frontend/src/styles/tokens.css` — palette values are **verbatim** from the v16 grammar reference (§A.1) except the two spec §5 overrides (`--page: #f7f5f0`, `--ink: #1a1a1a` replace v16's `#eeeee9`/`#0b0b0b` in light mode). Dark values are v16's dark block unchanged. Spacing is the spec's 8-pt scale replacing v16's ad-hoc values:

```css
:root {
  /* --- light palette (v16 §A.1 + spec §5 paper/ink overrides) --- */
  --page: #f7f5f0;          /* spec §5 "paper" (v16 was #eeeee9) */
  --surface: #fcfcfb;
  --card: #f9f9f7;
  --ink: #1a1a1a;           /* spec §5 (v16 was #0b0b0b) */
  --ink-2: #52514e;
  --muted: #898781;
  --grid: #e1e0d9;
  --baseline: #c3c2b7;
  --ring: rgba(11, 11, 11, 0.10);
  --s1: #2a78d6; --s2: #eb6834; --s3: #1baf7a;
  --band-out: #cde2fb; --band-in: #9ec5f4;
  --div-neg: #e34948; --good: #006300;
  --accent: #2a78d6;        /* spec §5 "signature blue" */
  --chip: #eef3fa; --code: #f2f1ed;
  --retro: #7a5ea8; --chip-retro: #f1ecf9;
  --warn: #a86a00; --chip-warn: #fdf3e2;
  --lab: #b0399a; --chip-lab: #fbecf7;

  /* --- semantic semaphore tokens (spec §5) --- */
  --st-crossed: var(--div-neg);
  --st-crossed-bg: var(--div-neg);
  --st-crossed-fg: #ffffff;
  --st-near: var(--warn);
  --st-near-bg: var(--chip-warn);
  --st-safe: var(--good);
  --st-safe-bg: var(--chip);

  /* --- 8-pt spacing scale (spec §5, replaces v16 ad-hoc) --- */
  --sp-0: 4px; --sp-1: 8px; --sp-2: 16px; --sp-3: 24px; --sp-4: 32px;

  /* --- radii / shadow (v16 §A.4) --- */
  --rad-card: 8px; --rad-chip: 6px; --rad-pill: 999px;
  --shadow-app: 0 2px 6px var(--ring), 0 18px 44px -22px var(--ring);

  /* --- motion (spec §5; v16's single transition was .18s) --- */
  --dur: 180ms;
  --rail-w: 300px;
  color-scheme: light;
}

:root[data-theme="dark"] {
  --page: #060606;
  --surface: #1a1a19;
  --card: #141413;
  --ink: #f4f4f1;
  --ink-2: #b9b8b2;
  --muted: #898781;
  --grid: #2a2a28;
  --baseline: #383835;
  --ring: rgba(255, 255, 255, 0.10);
  --s1: #6ba3e8; --s2: #f2895c; --s3: #3fc796;
  --band-out: #1d3352; --band-in: #244d7d;
  --div-neg: #f0706f; --good: #5fc25f;
  --accent: #6ba3e8;
  --chip: #16283d; --code: #232322;
  --retro: #a98cd8; --chip-retro: #2a2140;
  --warn: #d9a441; --chip-warn: #3a2c12;
  --lab: #e07ac8; --chip-lab: #38182f;
  color-scheme: dark;
}

@media (prefers-reduced-motion: reduce) {
  :root { --dur: 0ms; }
  *, *::before, *::after { transition: none !important; animation: none !important; }
}
```

`frontend/src/styles/base.css` — v16 component grammar (§A.3–§B.10, §C.3) modernized: fluid layout replaces the 1680×1080 canvas; the rail is sticky at 300 px and collapses to a drawer below 1024 px (spec §5). Class names are kept from v16 so the grammar doc stays a working reference:

```css
* { box-sizing: border-box; }
html, body, #root { height: 100%; }
body {
  margin: 0;
  background: var(--page);
  color: var(--ink);
  font: 14px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif;
  font-variant-numeric: tabular-nums;
}
button { font: inherit; }
code { font: 0.75em ui-monospace, Consolas, monospace; background: var(--code); padding: 0 4px; border-radius: 3px; }

/* --- app shell: fluid grid, not fixed canvas (spec §5) --- */
.shell { min-height: 100%; display: flex; flex-direction: column; background: var(--surface); }
.body { display: flex; flex: 1; min-height: 0; }
.rail {
  flex: 0 0 var(--rail-w); width: var(--rail-w);
  border-right: 1px solid var(--grid); background: var(--card);
  padding: var(--sp-1); display: flex; flex-direction: column; gap: var(--sp-1);
  position: sticky; top: 0; align-self: flex-start; max-height: 100vh; overflow-y: auto;
}
.main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: var(--sp-1); padding: var(--sp-1) var(--sp-2); }
.topbar { display: flex; align-items: center; gap: var(--sp-1); padding: var(--sp-1) var(--sp-2); border-bottom: 1px solid var(--grid); flex-wrap: wrap; }
.topbar nav { display: flex; gap: var(--sp-0); flex-wrap: wrap; }
.topbar nav a { color: var(--ink-2); text-decoration: none; font-weight: 700; font-size: 12px; padding: 4px 10px; border-radius: var(--rad-pill); }
.topbar nav a.active { background: var(--chip); color: var(--accent); }
.foot { border-top: 1px solid var(--grid); padding: var(--sp-0) var(--sp-2); font-size: 11px; color: var(--muted); display: flex; gap: var(--sp-2); flex-wrap: wrap; }

/* rail drawer below 1024px (spec §5) */
.rail-toggle { display: none; }
@media (max-width: 1024px) {
  .rail-toggle { display: inline-block; }
  .rail { position: fixed; left: 0; top: 0; bottom: 0; z-index: 40; transform: translateX(-100%); transition: transform var(--dur) ease; box-shadow: var(--shadow-app); max-height: none; }
  .rail.open { transform: translateX(0); }
}

/* --- v16 §C.2 rhythm: 5 KPI → 2 charts → semáforo/cadenas/narrativa --- */
.outs { display: grid; grid-template-columns: repeat(5, 1fr); gap: var(--sp-1); }
.row2 { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-1); }
.row3 { display: grid; grid-template-columns: 1.05fr 0.95fr 1.2fr; gap: var(--sp-1); }
@media (max-width: 1440px) { .outs { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 1024px) { .row2, .row3 { grid-template-columns: 1fr; } .outs { grid-template-columns: repeat(2, 1fr); } }

/* --- card primitive (v16 §C.3) --- */
.card { border: 1px solid var(--grid); border-radius: var(--rad-card); background: var(--surface); padding: var(--sp-1) var(--sp-1) var(--sp-1); display: flex; flex-direction: column; min-width: 0; }
.card h4 { margin: 0 0 var(--sp-0); font-size: 12px; display: flex; align-items: baseline; gap: 6px; }
.card h4 small { font-weight: 600; color: var(--muted); font-size: 10px; }

/* --- KPI dial tile (v16 §B.1) --- */
.out { border: 1px solid var(--grid); border-radius: var(--rad-card); padding: var(--sp-1); background: var(--surface); position: relative; }
.out .o-label { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; font-weight: 800; }
.out .o-val { font-size: 21px; font-weight: 800; line-height: 1.1; }
.out .o-val small { font-size: 11px; font-weight: 700; color: var(--muted); }
.out .o-delta { font-size: 10.5px; font-weight: 700; }
.out .o-delta.bad { color: var(--div-neg); }
.out .o-delta.good { color: var(--good); }
.out .o-seal { position: absolute; top: 7px; right: 8px; font-size: 9px; }
.gaugebar { position: relative; height: 6px; border-radius: 4px; background: var(--grid); margin: 5px 0 3px; }
.gaugebar .f { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 4px; background: var(--s1); transition: width var(--dur) ease; }
.gaugebar .f.bad { background: var(--div-neg); }
.gaugebar .f.warn2 { background: var(--warn); }
.gaugebar .f.ok { background: var(--s3); }
.gaugebar .rl { position: absolute; top: -3px; bottom: -3px; width: 2px; background: var(--div-neg); }
.gaugebar .bm { position: absolute; top: -2px; bottom: -2px; width: 1px; background: var(--baseline); }

/* --- lever row (v16 §B.2) --- */
.levers { display: flex; flex-direction: column; gap: var(--sp-0); }
.lev { border-radius: var(--rad-chip); padding: 2px 5px 3px; }
.lev.hot { background: var(--chip-lab); }
.lev .l1 { display: flex; align-items: baseline; gap: 5px; }
.lev .nm { font-size: 10.5px; font-weight: 700; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.lev .sym { font-size: 9.5px; font-weight: 800; color: var(--lab); font-style: italic; }
.lev .vv { font-size: 11.5px; font-weight: 800; color: var(--ink); white-space: nowrap; }
.lev .vv.moved { color: var(--lab); }
.lev input[type="range"] { width: 100%; height: 13px; margin: 0; accent-color: var(--lab); cursor: pointer; }
.lev .src { font-size: 8.5px; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* --- preset chips (v16 §B.3) --- */
.presets { display: flex; flex-wrap: wrap; gap: var(--sp-0); }
.ps { font-size: 9.5px; font-weight: 700; padding: 3px 6px; border-radius: 5px; border: 1px solid var(--grid); background: var(--surface); color: var(--ink-2); cursor: pointer; }
.ps:hover { border-color: var(--lab); color: var(--lab); }
.ps.on { background: var(--lab); color: #fff; border-color: var(--lab); }
.horiz { display: flex; flex-wrap: wrap; gap: var(--sp-0); }
.hb { font-size: 9.5px; font-weight: 700; padding: 3px 6px; border-radius: 5px; border: 1px solid var(--grid); background: var(--surface); color: var(--ink-2); cursor: pointer; }
.hb.on { background: var(--accent); color: #fff; border-color: var(--accent); }

/* --- stamp badges (v16 §B.4) --- */
.badge-fwd { background: var(--chip); color: var(--accent); font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: var(--rad-pill); white-space: nowrap; }
.badge-fwd.lab { background: var(--chip-lab); color: var(--lab); }

/* --- semaphore (v16 §B.5, tokens from spec §5) --- */
.rl-item { display: grid; grid-template-columns: 18px 1fr auto; align-items: center; gap: 5px; border: 1px solid var(--grid); border-radius: var(--rad-chip); padding: 4px 7px; font-size: 10.5px; margin-bottom: var(--sp-0); }
.rl-item .ic { font-size: 12px; }
.rl-item .t b { white-space: nowrap; }
.rl-item .st { font-size: 9px; font-weight: 800; padding: 2px 7px; border-radius: var(--rad-pill); white-space: nowrap; }
.st.cross { background: var(--st-crossed-bg); color: var(--st-crossed-fg); }
.st.near { background: var(--st-near-bg); color: var(--st-near); }
.st.safe { background: var(--st-safe-bg); color: var(--st-safe); }
.st.sd { background: var(--code); color: var(--muted); }
.rl-item .x { font-size: 9px; color: var(--muted); grid-column: 2 / 4; }

/* --- transmission chain (v16 §B.6) --- */
.chain { display: flex; flex-direction: column; gap: 5px; margin-top: 2px; }
.ch { display: flex; align-items: center; gap: 5px; font-size: 10px; color: var(--ink-2); flex-wrap: wrap; }
.ch .a { font-weight: 700; color: var(--ink); background: var(--code); border-radius: 5px; padding: 2px 6px; white-space: nowrap; }
.ch .u { font-size: 8.5px; font-weight: 800; color: var(--accent); background: var(--chip); border-radius: var(--rad-pill); padding: 1px 6px; white-space: nowrap; }
.ch .arr { color: var(--baseline); }
.ch .d { font-weight: 800; white-space: nowrap; }
.ch .d.up { color: var(--div-neg); }
.ch .d.dn { color: var(--good); }
.ch .d.flat { color: var(--muted); }

/* --- narrative block (v16 §B.8) --- */
.narr { border-left: 3px solid var(--accent); border-radius: 0 7px 7px 0; padding: 6px 10px; background: var(--card); margin-top: 5px; }
.narr .h { font-size: 10px; font-weight: 800; color: var(--accent); }
.narr .x { font-size: 10.5px; color: var(--ink-2); line-height: 1.4; }
.narr .cite { font-size: 9px; color: var(--muted); margin-top: 3px; }

/* --- chart legend (v16 §B.9) --- */
.legend { font-size: 9px; color: var(--ink-2); display: flex; gap: 10px; flex-wrap: wrap; margin: 1px 0 2px; }
.legend i { display: inline-block; width: 9px; height: 3px; border-radius: 2px; vertical-align: middle; margin-right: 4px; }
.legend s { display: inline-block; width: 9px; height: 0; border-top: 2px dashed var(--baseline); vertical-align: middle; margin-right: 4px; text-decoration: none; }

/* --- persona head (v16 §B.10) --- */
.head { display: flex; align-items: baseline; gap: var(--sp-1); flex-wrap: wrap; }
.head h1 { margin: 0; font-size: 17px; font-weight: 800; }
.head .meta { margin-left: auto; font-size: 9px; color: var(--muted); }

/* --- banners (spec §8) --- */
.banner { border: 1px solid var(--warn); background: var(--chip-warn); color: var(--warn); border-radius: var(--rad-chip); padding: var(--sp-0) var(--sp-1); font-size: 11px; font-weight: 700; }
.banner.err { border-color: var(--div-neg); background: transparent; color: var(--div-neg); }
.blocking { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: var(--sp-3); background: var(--page); }
.blocking .card { max-width: 560px; }
```

Placeholder `frontend/src/main.tsx` (replaced in Task 11 — kept minimal so `npm run dev` boots today):

```tsx
import { createRoot } from "react-dom/client";
import { initTheme } from "./state/theme";
import "./styles/tokens.css";
import "./styles/base.css";
import App from "./App";

initTheme();
createRoot(document.getElementById("root")!).render(<App />);
```

Placeholder `frontend/src/App.tsx`:

```tsx
export default function App() {
  return <div className="shell"><p style={{ padding: 16 }}>España en escenarios — en construcción (tarea 11).</p></div>;
}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/lib src/state`
Expected: PASS (8 tests). Also verify the shell boots: `npm run dev` → `http://localhost:5173` shows the placeholder, then Ctrl-C.

- [ ] **Step 7: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/package.json frontend/package-lock.json frontend/.gitignore frontend/index.html \
  frontend/vite.config.ts frontend/vitest.config.ts frontend/tsconfig.json \
  frontend/src/styles frontend/src/lib frontend/src/state frontend/src/test/setup.ts \
  frontend/src/main.tsx frontend/src/App.tsx
git commit -m "feat(frontend): scaffold Vite 8 + React 19 app with v16 tokens, fmt and theme helpers"
```

---

### Task 2: Constants generator (`gen-constants.mjs`) → `constants.ts` + `vintage.ts`

**Files:**
- Create: `frontend/scripts/gen-constants.mjs`
- Create (generated, then committed): `frontend/src/engine/constants.ts`, `frontend/src/engine/vintage.ts`
- Test: `frontend/src/engine/__tests__/constants.test.ts`

**Interfaces:**
- Consumes: running API at `http://localhost:8000` (`/constants`, `/health`) — **generation time only**; committed gold files `data/gold/gold_escenarios_deuda.csv`, `data/gold/gold_projections.csv`, `data/gold/kpis_perfiles.json`, `data/gold/VINTAGE` (read from disk, same vintage the API serves).
- Produces: `src/engine/constants.ts` named exports `MULT, RHO, E_R, E_EXT, E_PM, OKUN, KAPPA, GAMMA, THETA, PHI, A_Z, A_TAU, A_LAM, REFI, TERM, DIFF, IPV_LR, IPV_REV, E_IPV_R, E_IPV_G, RJUV, PM_DECAY, CAL_SALARIO_MES` (all `number`) plus `CONSTANTS_META: { name: string; value: number; unit: string; provenance: string }[]` (all 31 API rows, for Metodología); `src/engine/vintage.ts` exports `VINTAGE: string`, `ENGINE_VERSION: string`, `V0: Record<V0Key, number>` (24 keys `u pi g bono precio cuota salmes salario ipv pens arop edu d1 p2 d3 p51 gtot temp auton bls hip sobre ujuv vida`), `BASE_LEVERS: { r; prima; sp; lam; pm; tau; z; ext; dem; idx: number }`, `CENTRAL: Record<number, { deuda: number; pb: number; r_efectivo: number; g_nominal: number; presion_demog: number }>` (years 2024–2050, `central` rows), `OLDDEP: Record<number, number>` (ES/BSL rows).

Rationale (record in the plan, do not reopen): spec §4 mandates a generated `constants.ts` from `/constants`. The engine additionally needs the vintage-anchored data (`V0`, `BASE_LEVERS`, `CENTRAL`, `OLDDEP`) that `/constants` does not carry; the same generator reads it from the committed gold files — one script, two generated files, both committed, drift caught by this task's test and Task 5's parity battery.

- [ ] **Step 1: Write the failing test**

`frontend/src/engine/__tests__/constants.test.ts` — pins are REAL values from `engine/constants.py`, `data/gold/*`, and the fixture:

```ts
import { describe, expect, it } from "vitest";
import * as C from "../constants";
import { BASE_LEVERS, CENTRAL, ENGINE_VERSION, OLDDEP, V0, VINTAGE } from "../vintage";
import anchors from "@fixtures/engine_anchors.json";

describe("generated constants match the Python engine and the committed vintage", () => {
  it("named v16 constants (engine/constants.py values)", () => {
    expect(C.MULT).toBe(1.4);
    expect(C.RHO).toBe(0.62);
    expect(C.E_R).toBe(0.45);
    expect(C.E_EXT).toBe(0.25);
    expect(C.E_PM).toBe(0.012);
    expect(C.OKUN).toBe(0.48);
    expect(C.KAPPA).toBe(0.22);
    expect(C.GAMMA).toBe(0.045);
    expect(C.THETA).toBe(0.55);
    expect(C.PHI).toBe(0.3);
    expect(C.A_Z).toBe(1.1);
    expect(C.A_TAU).toBe(0.3);
    expect(C.A_LAM).toBe(0.45);
    expect(C.REFI).toBe(0.14);
    expect(C.TERM).toBe(0.17);
    expect(C.DIFF).toBe(1.4757);
    expect(C.IPV_LR).toBe(3.0);
    expect(C.IPV_REV).toBe(0.6);
    expect(C.E_IPV_R).toBe(2.6);
    expect(C.E_IPV_G).toBe(1.1);
    expect(C.RJUV).toBe(2.317);
    expect(C.PM_DECAY).toBe(0.45);
    expect(C.CAL_SALARIO_MES).toBe(1749.79);
  });
  it("31 provenance rows for Metodología", () => {
    expect(C.CONSTANTS_META).toHaveLength(31);
    expect(C.CONSTANTS_META[0]).toMatchObject({ name: "MULT", value: 1.4, unit: "x" });
    expect(C.CONSTANTS_META.map((r) => r.name)).toContain("MC_SIG_R");
  });
  it("vintage-anchored values", () => {
    expect(VINTAGE).toBe(anchors.vintage); // "2026-07-31"
    expect(ENGINE_VERSION).toBe("1.0.0");
    expect(V0.u).toBe(10.1);
    expect(V0.pi).toBe(3.0);
    expect(V0.g).toBe(2.7);
    expect(V0.bono).toBe(3.42);
    expect(V0.precio).toBe(171444);
    expect(V0.cuota).toBe(745);
    expect(V0.salmes).toBe(1749.79);
    expect(V0.salario).toBe(24497);
    expect(V0.ipv).toBe(12.8);
    expect(V0.pens).toBe(13.23);
    expect(V0.vida).toBe(84.0);
    expect(BASE_LEVERS).toEqual({
      r: 2.8, prima: 45, sp: 0.0, lam: 0.9, pm: 0.0,
      tau: 0.0, z: 0.0, ext: 1.8, dem: 0.0, idx: 0.0,
    });
    expect(CENTRAL[2025]).toEqual({ deuda: 105.6, pb: -1.13, r_efectivo: 2.57, g_nominal: 3.3, presion_demog: 0.23 });
    expect(CENTRAL[2026].r_efectivo).toBe(2.68);
    expect(CENTRAL[2050].pb).toBe(-7.47);
    expect(OLDDEP[2026]).toBe(32.6);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/engine/__tests__/constants.test.ts`
Expected: FAIL — `Cannot find module '../constants'`.

- [ ] **Step 3: Write the generator and run it**

`frontend/scripts/gen-constants.mjs`:

```js
#!/usr/bin/env node
/**
 * Generates src/engine/constants.ts and src/engine/vintage.ts.
 * Sources: the running phase-1 API (/constants, /health) for named constants,
 * and the committed gold slice (../data/gold) for vintage-anchored data.
 * Both outputs are COMMITTED; src/engine/__tests__/constants.test.ts pins them.
 * Usage: API_BASE=http://localhost:8000 node scripts/gen-constants.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const GOLD = path.resolve(here, "../../data/gold");
const OUT = path.resolve(here, "../src/engine");
const API = process.env.API_BASE ?? "http://localhost:8000";

const constants = await (await fetch(`${API}/constants`)).json();
const health = await (await fetch(`${API}/health`)).json();

// ---- constants.ts: one named export per scalar the engine chain uses ----
const CHAIN_NAMES = [
  "MULT", "RHO", "E_R", "E_EXT", "E_PM", "OKUN", "KAPPA", "GAMMA", "THETA",
  "PHI", "A_Z", "A_TAU", "A_LAM", "REFI", "TERM", "DIFF", "IPV_LR", "IPV_REV",
  "E_IPV_R", "E_IPV_G", "RJUV", "PM_DECAY", "CAL_SALARIO_MES",
];
const byName = Object.fromEntries(constants.constants.map((c) => [c.name, c]));
for (const n of CHAIN_NAMES) {
  if (!(n in byName)) throw new Error(`API /constants missing ${n}`);
}
const constantsTs = [
  "// GENERATED by scripts/gen-constants.mjs — do not edit. Regenerate with `npm run gen:constants`.",
  `// Source: ${API}/constants, vintage ${constants.vintage}.`,
  ...CHAIN_NAMES.map((n) => `export const ${n} = ${byName[n].value};`),
  "",
  "export interface ConstantMeta { name: string; value: number; unit: string; provenance: string }",
  `export const CONSTANTS_META: ConstantMeta[] = ${JSON.stringify(constants.constants, null, 2)};`,
  "",
].join("\n");
writeFileSync(path.join(OUT, "constants.ts"), constantsTs);

// ---- vintage.ts: V0 / BASE_LEVERS / CENTRAL / OLDDEP from the gold slice ----
const kpis = JSON.parse(readFileSync(path.join(GOLD, "kpis_perfiles.json"), "utf-8"));
const vintage = readFileSync(path.join(GOLD, "VINTAGE"), "utf-8").trim();
const kpi = (name) => {
  const v = Number(kpis.kpi[name].valor);
  if (!Number.isFinite(v)) throw new Error(`kpi ${name} is not numeric`);
  return v;
};
// mirrors engine/constants.py V0 exactly (24 keys)
const V0 = {
  u: kpi("paro_total"), pi: kpi("hicp_es"), g: kpi("pib_yoy"), bono: kpi("bono10y_es"),
  precio: kpi("precio_vivienda_mediano"), cuota: kpi("cuota_hipoteca_mediana"),
  salmes: byName.CAL_SALARIO_MES.value, salario: kpi("salario_medio"),
  ipv: kpi("vivienda_precio_yoy"), pens: kpi("gasto_pensiones_pib"),
  arop: kpi("arop_infantil"), edu: kpi("gasto_educacion_pib"),
  d1: kpi("salarios_publicos_pib"), p2: kpi("consumo_intermedio_pib"),
  d3: kpi("subvenciones_pib"), p51: kpi("inversion_publica_pib"),
  gtot: kpi("gasto_total_pib"), temp: kpi("temporalidad"), auton: kpi("autoempleo"),
  bls: kpi("bls_endurecimiento"), hip: kpi("hipotecas_anuales"),
  sobre: kpi("sobrecarga_vivienda"), ujuv: kpi("paro_juvenil"), vida: kpi("esperanza_vida"),
};
// mirrors engine/constants.py BASE_LEVERS exactly
const BASE_LEVERS = {
  r: kpi("euribor12m"), prima: kpi("spread_es_de"),
  sp: 0.0, lam: 0.9, pm: 0.0, tau: 0.0, z: 0.0, ext: 1.8, dem: 0.0, idx: 0.0,
};

const parseCsv = (file) => {
  const [head, ...rows] = readFileSync(path.join(GOLD, file), "utf-8").trim().split(/\r?\n/);
  const cols = head.split(",");
  return rows.map((r) => Object.fromEntries(r.split(",").map((v, i) => [cols[i], v])));
};
const CENTRAL = {};
for (const row of parseCsv("gold_escenarios_deuda.csv")) {
  if (row.escenario !== "central") continue;
  CENTRAL[Math.trunc(Number(row.year))] = {
    deuda: Number(row.deuda), pb: Number(row.pb), r_efectivo: Number(row.r_efectivo),
    g_nominal: Number(row.g_nominal), presion_demog: Number(row.presion_demog),
  };
}
const OLDDEP = {};
for (const row of parseCsv("gold_projections.csv")) {
  if (row.geo === "ES" && row.variant === "BSL") OLDDEP[Math.trunc(Number(row.year))] = Number(row.olddep);
}

const vintageTs = [
  "// GENERATED by scripts/gen-constants.mjs — do not edit. Regenerate with `npm run gen:constants`.",
  `// Source: ../data/gold (vintage ${vintage}) + ${API}/health.`,
  'import type { Levers } from "./levers";',
  "",
  `export const VINTAGE = ${JSON.stringify(vintage)};`,
  `export const ENGINE_VERSION = ${JSON.stringify(health.engine_version)};`,
  "",
  "export type V0Key = keyof typeof V0;",
  `export const V0 = ${JSON.stringify(V0, null, 2)} as const;`,
  "",
  `export const BASE_LEVERS: Levers = ${JSON.stringify(BASE_LEVERS, null, 2)};`,
  "",
  "export interface CentralRow { deuda: number; pb: number; r_efectivo: number; g_nominal: number; presion_demog: number }",
  `export const CENTRAL: Record<number, CentralRow> = ${JSON.stringify(CENTRAL, null, 2)};`,
  "",
  `export const OLDDEP: Record<number, number> = ${JSON.stringify(OLDDEP, null, 2)};`,
  "",
].join("\n");
writeFileSync(path.join(OUT, "vintage.ts"), vintageTs);

if (vintage !== constants.vintage) {
  throw new Error(`VINTAGE file (${vintage}) != API vintage (${constants.vintage}) — refuse to generate from mixed vintages`);
}
console.log(`Wrote constants.ts (${CHAIN_NAMES.length} named + ${constants.constants.length} meta rows) and vintage.ts (vintage ${vintage})`);
```

Also create a hand-written stub `frontend/src/engine/levers.ts` **type only** so `vintage.ts` compiles before Task 3 fills it in:

```ts
export interface Levers {
  r: number; prima: number; sp: number; lam: number; pm: number;
  tau: number; z: number; ext: number; dem: number; idx: number;
}
export type LeverId = keyof Levers;
```

Run: `cd frontend && npm run gen:constants`
Expected output: `Wrote constants.ts (23 named + 31 meta rows) and vintage.ts (vintage 2026-07-31)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/engine/__tests__/constants.test.ts`
Expected: PASS (3 tests). Spot-check the generated files by eye: `constants.ts` must contain `export const RHO = 0.62;` and `export const DIFF = 1.4757;`; `vintage.ts` must contain `"2025": {` … `"deuda": 105.6`.

- [ ] **Step 5: Commit (generator AND generated output)**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/scripts/gen-constants.mjs frontend/src/engine/constants.ts \
  frontend/src/engine/vintage.ts frontend/src/engine/levers.ts \
  frontend/src/engine/__tests__/constants.test.ts
git commit -m "feat(frontend): generate engine constants + vintage data from API and gold slice"
```

---

### Task 3: Engine port I — levers, presets and the v16 chain (`spain.ts`)

**Files:**
- Modify: `frontend/src/engine/levers.ts` (replace the Task-2 type stub with the full module)
- Create: `frontend/src/engine/spain.ts`, `frontend/src/engine/index.ts`
- Test: `frontend/src/engine/__tests__/spain.test.ts`

**Interfaces:**
- Consumes: `constants.ts` named exports and `vintage.ts` (`V0`, `BASE_LEVERS`, `CENTRAL`, `OLDDEP`) from Task 2.
- Produces: from `levers.ts` — `Levers`, `LeverId`, `LeverSpec { id: LeverId; sym: string; nm: string; unit: string; min: number; max: number; step: number; dec: number; src: string }`, `LEVER_SPECS: LeverSpec[]` (10), `PRESETS: { id: string; nm: string; set: Partial<Levers> }[]` (8), `presetLevers(presetId: string): Levers`, `activePresetId(L: Levers): string | null`, `isMoved(L: Levers, id: LeverId): boolean`, `allAtBase(L: Levers): boolean`. From `spain.ts` — `Y0 = 2026`, `Y1 = 2050`, `N_YEARS = 25`, `YEARS: number[]`, `SERIES_KEYS` (40, template order), `SeriesKey`, `Scenario = Record<SeriesKey, number[]>`, `french(principal: number, annualRatePct: number, nMonths: number): number`, `runScenario(L: Levers): Scenario`, `baseline(): Scenario` (memoized). `index.ts` re-exports everything in `engine/`.

- [ ] **Step 1: Write the failing test**

`frontend/src/engine/__tests__/spain.test.ts` — every expected number is a REAL pin from `tests/fixtures/engine_anchors.json` (`base_2026` block) or from `engine/levers.py`:

```ts
import { describe, expect, it } from "vitest";
import { BASE_LEVERS } from "../vintage";
import { LEVER_SPECS, PRESETS, activePresetId, allAtBase, isMoved, presetLevers } from "../levers";
import { N_YEARS, SERIES_KEYS, Y0, Y1, YEARS, baseline, french, runScenario } from "../spain";

describe("levers & presets (v16 const LEVERS / const PRESETS)", () => {
  it("has the 10 lever specs in order with v16 ranges", () => {
    expect(LEVER_SPECS.map((s) => s.id)).toEqual([
      "r", "prima", "sp", "lam", "pm", "tau", "z", "ext", "dem", "idx",
    ]);
    const r = LEVER_SPECS[0];
    expect(r).toMatchObject({ sym: "r", nm: "Tipo de interés · Euríbor 12m", unit: "%", min: 0, max: 6, step: 0.05, dec: 2 });
    expect(LEVER_SPECS[8]).toMatchObject({ id: "dem", sym: "β₆₅", min: -1, max: 1, step: 0.05, dec: 2 });
  });
  it("presets resolve against BASE (S1: r = 2.8 + 2 = 4.8)", () => {
    expect(PRESETS.map((p) => p.id)).toEqual(["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7"]);
    expect(presetLevers("S1").r).toBeCloseTo(4.8, 12);
    expect(presetLevers("S7")).toMatchObject({ r: 4.8, pm: 50.0, prima: 150.0 });
    expect(presetLevers("S0")).toEqual({ ...BASE_LEVERS });
    expect(() => presetLevers("S9")).toThrow(/S0\.\.S7/);
  });
  it("activePresetId detects by full-vector equality", () => {
    expect(activePresetId({ ...BASE_LEVERS })).toBe("S0");
    expect(activePresetId(presetLevers("S3"))).toBe("S3");
    expect(activePresetId({ ...BASE_LEVERS, r: 3.05 })).toBeNull();
  });
  it("isMoved / allAtBase use the 1e-9 v16 threshold", () => {
    expect(isMoved({ ...BASE_LEVERS }, "r")).toBe(false);
    expect(isMoved({ ...BASE_LEVERS, r: 2.8 + 1e-10 }, "r")).toBe(false);
    expect(isMoved({ ...BASE_LEVERS, r: 2.85 }, "r")).toBe(true);
    expect(allAtBase({ ...BASE_LEVERS })).toBe(true);
  });
});

describe("spain.ts — v16 chain, base year (fixture base_2026 pins)", () => {
  const base = baseline();
  it("shape: 25 years × 40 series", () => {
    expect(Y0).toBe(2026);
    expect(Y1).toBe(2050);
    expect(N_YEARS).toBe(25);
    expect(YEARS[0]).toBe(2026);
    expect(YEARS[24]).toBe(2050);
    expect(SERIES_KEYS).toHaveLength(40);
    for (const k of SERIES_KEYS) expect(base[k]).toHaveLength(25);
  });
  it("french(): cuota 2026 = 744.997065 (fixture cuota_2026_base 744.9971 ± 0.01)", () => {
    expect(french(171444 * 0.8, 2.8 + 1.4757, 300)).toBeCloseTo(744.9971, 2);
  });
  it("base 2026 values equal the fixture base_2026 block", () => {
    expect(base.u[0]).toBeCloseTo(10.1, 6);
    expect(base.pi[0]).toBeCloseTo(3.0, 6);
    expect(base.g[0]).toBeCloseTo(2.7, 6);
    expect(base.bono[0]).toBeCloseTo(3.42, 6);
    expect(base.cuota[0]).toBeCloseTo(744.997065, 6);
    expect(base.esf[0]).toBeCloseTo(42.57637, 5);
    expect(base.b[0]).toBeCloseTo(106.316196, 6);
    expect(base.pens[0]).toBeCloseTo(13.23, 6);
    expect(base.dep[0]).toBeCloseTo(32.6, 6);
    expect(base.ujuv[0]).toBeCloseTo(23.4017, 4);
  });
  it("deviation semantics: all levers at base ⇒ scenario === baseline", () => {
    const again = runScenario({ ...BASE_LEVERS });
    for (const k of SERIES_KEYS) {
      for (let i = 0; i < 25; i++) expect(again[k][i]).toBe(base[k][i]);
    }
  });
  it("bono = r + TERM + prima/100 (base: 2.8 + 0.17 + 0.45 = 3.42)", () => {
    const s1 = runScenario({ ...BASE_LEVERS, r: 4.8 });
    expect(s1.bono[0]).toBeCloseTo(4.8 + 0.17 + 0.45, 9);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/engine/__tests__/spain.test.ts`
Expected: FAIL — `levers.ts` has no export `LEVER_SPECS`; `Cannot find module '../spain'`.

- [ ] **Step 3: Implement `levers.ts` and `spain.ts`**

`frontend/src/engine/levers.ts` (full module; Spanish copy **verbatim** from `engine/levers.py` `LEVER_SPECS` / `PRESETS`, which ported v16 `const LEVERS`/`const PRESETS` verbatim):

```ts
import { BASE_LEVERS } from "./vintage";

export interface Levers {
  r: number; prima: number; sp: number; lam: number; pm: number;
  tau: number; z: number; ext: number; dem: number; idx: number;
}
export type LeverId = keyof Levers;

export interface LeverSpec {
  id: LeverId; sym: string; nm: string; unit: string;
  min: number; max: number; step: number; dec: number; src: string;
}

export const LEVER_SPECS: LeverSpec[] = [
  { id: "r", sym: "r", nm: "Tipo de interés · Euríbor 12m", unit: "%", min: 0.0, max: 6.0, step: 0.05, dec: 2, src: "ecb_euribor12m.csv · 2026-06" },
  { id: "prima", sym: "σ", nm: "Prima de riesgo · spread ES–DE", unit: "pb", min: 0.0, max: 400.0, step: 5.0, dec: 0, src: "ecb_bono10y_{es,de}.csv · 2026-06" },
  { id: "sp", sym: "sp", nm: "Saldo primario · Δ vs central", unit: "pp PIB", min: -4.0, max: 4.0, step: 0.1, dec: 1, src: "gold_escenarios_deuda.csv (central)" },
  { id: "lam", sym: "λ", nm: "Productividad", unit: "%/año", min: -0.5, max: 2.5, step: 0.1, dec: 1, src: "PWT + INE · desplaza la PS" },
  { id: "pm", sym: "pᵐ", nm: "Precio importaciones/energía", unit: "% a/a", min: -50.0, max: 100.0, step: 5.0, dec: 0, src: "WEO commodity prices" },
  { id: "tau", sym: "τ", nm: "Presión fiscal · cuña laboral", unit: "pp", min: -5.0, max: 5.0, step: 0.25, dec: 2, src: "Eurostat GFS · desplaza la WS" },
  { id: "z", sym: "z", nm: "Instituciones laborales", unit: "índice", min: -2.0, max: 2.0, step: 0.1, dec: 1, src: "OECD/Eurostat · desplaza la WS" },
  { id: "ext", sym: "Y*", nm: "Demanda externa", unit: "% a/a", min: -4.0, max: 6.0, step: 0.1, dec: 1, src: "WEO · canal exterior (U7)" },
  { id: "dem", sym: "β₆₅", nm: "Presión demográfica", unit: "×", min: -1.0, max: 1.0, step: 0.05, dec: 2, src: "gold_projections.csv · variante" },
  { id: "idx", sym: "ι", nm: "Indexación pensiones/nóminas", unit: "IPC+pp", min: -1.5, max: 1.0, step: 0.1, dec: 1, src: "regla de revalorización · palanca" },
];

export const PRESETS: { id: string; nm: string; set: Partial<Levers> }[] = [
  { id: "S0", nm: "S0 base", set: {} },
  { id: "S1", nm: "S1 tipos +200 pb", set: { r: BASE_LEVERS.r + 2 } },
  { id: "S2", nm: "S2 petróleo +50 %", set: { pm: 50.0 } },
  { id: "S3", nm: "S3 consolidación", set: { sp: 1.0 } },
  { id: "S4", nm: "S4 productividad", set: { lam: 1.4 } },
  { id: "S5", nm: "S5 desregulación lab.", set: { z: -1.0, tau: -1.5 } },
  { id: "S6", nm: "S6 envejecimiento", set: { dem: 0.6 } },
  { id: "S7", nm: "S7 adverso", set: { r: BASE_LEVERS.r + 2, pm: 50.0, prima: 150.0 } },
];

const EPS = 1e-9;
export const LEVER_IDS = LEVER_SPECS.map((s) => s.id);

export function presetLevers(presetId: string): Levers {
  const p = PRESETS.find((q) => q.id === presetId);
  if (!p) throw new Error(`unknown preset id: ${presetId} (valid: S0..S7)`);
  return { ...BASE_LEVERS, ...p.set };
}

export function isMoved(L: Levers, id: LeverId): boolean {
  return Math.abs(L[id] - BASE_LEVERS[id]) > EPS;
}

export function allAtBase(L: Levers): boolean {
  return LEVER_IDS.every((id) => !isMoved(L, id));
}

/** v16 railState(): which preset the CURRENT full vector equals, if any. */
export function activePresetId(L: Levers): string | null {
  for (const p of PRESETS) {
    const target = { ...BASE_LEVERS, ...p.set };
    if (LEVER_IDS.every((id) => Math.abs(L[id] - target[id]) <= EPS)) return p.id;
  }
  return null;
}
```

`frontend/src/engine/spain.ts` — line-faithful port of `engine/spain.py` `run_scenario` (same constants, same update order, same 40 keys, same deviation semantics). Comments cite the Python lines so a reviewer can diff side by side:

```ts
import * as C from "./constants";
import { BASE_LEVERS, CENTRAL, OLDDEP, V0 } from "./vintage";
import type { Levers } from "./levers";

export const Y0 = 2026;
export const Y1 = 2050;
export const N_YEARS = Y1 - Y0 + 1; // 25
export const YEARS: number[] = Array.from({ length: N_YEARS }, (_, k) => Y0 + k);

/** v16 R keys, template order (engine/spain.py SERIES_KEYS). */
export const SERIES_KEYS = [
  "lvl", "u", "pi", "g", "gnom", "wnom", "wreal", "wrealIdx", "b", "ief",
  "int", "pb", "saldo", "ipv", "precio", "cuota", "salmes", "salario", "esf",
  "pens", "dep", "arop", "edu", "d1", "nomreal", "p2", "d3", "p51", "gtot",
  "bls", "temp", "ujuv", "auton", "hip", "sobre", "bono", "spread", "r",
  "deficitAbs", "vida",
] as const;
export type SeriesKey = (typeof SERIES_KEYS)[number];
export type Scenario = Record<SeriesKey, number[]>;

/** French amortization monthly payment (engine/spain.py french()). */
export function french(principal: number, annualRatePct: number, nMonths: number): number {
  const i = annualRatePct / 1200.0;
  return (principal * i) / (1 - Math.pow(1 + i, -nMonths));
}

export function runScenario(L: Levers): Scenario {
  const B = BASE_LEVERS;
  const R = Object.fromEntries(SERIES_KEYS.map((k) => [k, [] as number[]])) as Scenario;

  const bono = L.r + C.TERM + L.prima / 100;
  const shock =
    -(L.sp - B.sp) - C.E_R * (L.r - B.r) + C.E_EXT * (L.ext - B.ext) - C.E_PM * (L.pm - B.pm);
  const uStarDev = C.A_Z * L.z + C.A_TAU * L.tau - C.A_LAM * (L.lam - B.lam);

  let lvl = 0.0;
  let piDev = 0.0;
  let di = 0.0;
  let b = CENTRAL[Y0 - 1].deuda; // 105.6 (2025)
  let salIdx = 1.0;
  let wrIdx = 1.0;
  let pensFac = 1.0;
  let nomIdx = 1.0;
  let precio = V0.precio;

  for (let k = 0; k < N_YEARS; k++) {
    const y = Y0 + k;
    const gc = CENTRAL[y];
    const prev = lvl;
    lvl = C.RHO * lvl + (1 - C.RHO) * C.MULT * shock; // GDP level deviation (%)
    const gapU = C.OKUN * lvl; // slack: u below u*
    const u = V0.u + uStarDev - gapU;
    piDev = C.THETA * piDev + C.KAPPA * gapU + C.GAMMA * (L.pm - B.pm) * Math.pow(C.PM_DECAY, k);
    const pi = V0.pi + piDev;
    const g = V0.g + (lvl - prev) + (L.lam - B.lam);
    const gnom = gc.g_nominal + (g - V0.g) + piDev;

    // debt identity b_t = b_{t-1}(1+i)/(1+g) − sp, with 14 %/yr refinancing
    di = di + C.REFI * ((bono - V0.bono) - di);
    const ief = gc.r_efectivo + di;
    const pb = gc.pb + L.sp - gc.presion_demog * L.dem;
    const bPrev = b;
    b = (bPrev * (1 + ief / 100)) / (1 + gnom / 100) - pb;
    const intr = (bPrev * ief) / 100;
    const saldo = pb - intr;

    // wage setting (WS)
    const wnom = pi + L.lam + C.PHI * gapU;
    const wreal = wnom - pi;
    if (k > 0) {
      salIdx *= 1 + wnom / 100;
      wrIdx *= 1 + wreal / 100;
    }

    // housing
    const ipv =
      C.IPV_LR + (V0.ipv - C.IPV_LR) * Math.pow(C.IPV_REV, k) -
      C.E_IPV_R * (L.r - B.r) + C.E_IPV_G * (g - V0.g);
    if (k > 0) precio *= 1 + ipv / 100;
    const cuota = french(precio * 0.8, L.r + C.DIFF, 300);
    const salmes = V0.salmes * salIdx;
    const esf = (cuota / salmes) * 100;

    // pensions: mechanical identity pension x number / GDP
    if (k > 0) {
      pensFac *= (1 + (pi + L.idx) / 100) / (1 + gnom / 100);
      nomIdx *= 1 + L.idx / 100;
    }
    const depIdx = 1 + (OLDDEP[y] / OLDDEP[Y0] - 1) * (1 + L.dem);
    const dep = OLDDEP[Y0] * depIdx;
    const pens = V0.pens * depIdx * pensFac;

    R.lvl.push(lvl); R.u.push(u); R.pi.push(pi); R.g.push(g);
    R.gnom.push(gnom); R.wnom.push(wnom); R.wreal.push(wreal);
    R.wrealIdx.push(wrIdx * 100); R.b.push(b); R.ief.push(ief);
    R.int.push(intr); R.pb.push(pb); R.saldo.push(saldo);
    R.deficitAbs.push(Math.abs(Math.min(0.0, saldo)));
    R.ipv.push(ipv); R.precio.push(precio); R.cuota.push(cuota);
    R.salmes.push(salmes); R.salario.push(V0.salario * salIdx);
    R.esf.push(esf); R.pens.push(pens); R.dep.push(dep);
    R.nomreal.push(nomIdx * 100);
    R.arop.push(V0.arop + 0.55 * (u - V0.u) + 0.90 * L.sp);
    R.edu.push(V0.edu - 0.090 * L.sp);
    R.d1.push(V0.d1 - 0.240 * L.sp);
    R.p2.push(V0.p2 - 0.125 * L.sp);
    R.d3.push(V0.d3 - 0.031 * L.sp);
    R.p51.push(V0.p51 - 0.145 * L.sp);
    R.gtot.push(V0.gtot - 1.0 * L.sp);
    R.bls.push(V0.bls + 12 * (L.r - B.r) + 2.5 * (u - V0.u));
    R.temp.push(V0.temp + 0.25 * (u - V0.u) - 1.5 * L.z);
    R.ujuv.push(C.RJUV * u);
    R.auton.push(V0.auton + 0.12 * (u - V0.u) - 0.40 * (g - V0.g));
    R.hip.push(Math.max(0.0, V0.hip * (1 - 1.6 * (esf / ((V0.cuota / V0.salmes) * 100) - 1))));
    R.sobre.push(V0.sobre + 0.18 * (esf - (V0.cuota / V0.salmes) * 100));
    R.bono.push(bono); R.spread.push(L.prima); R.r.push(L.r);
    R.vida.push(V0.vida);
  }
  return R;
}

let _baseline: Scenario | null = null;
/** The frozen-vintage baseline: all levers at base. Computed once per session. */
export function baseline(): Scenario {
  if (_baseline === null) _baseline = runScenario({ ...BASE_LEVERS });
  return _baseline;
}
```

`frontend/src/engine/index.ts`:

```ts
export * from "./constants";
export * from "./vintage";
export * from "./levers";
export * from "./spain";
export * from "./derived";   // Task 4 — create as empty `export {};` now, filled next task
export * from "./redlines";  // Task 4 — create as empty `export {};` now, filled next task
```

(Create `derived.ts` and `redlines.ts` as `export {};` placeholders so `index.ts` compiles; Task 4 replaces them.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/engine/__tests__/spain.test.ts`
Expected: PASS (9 tests). If `base.b[0]` is off, diff the loop against `engine/spain.py` line by line — the usual culprits are the `k > 0` guards and using `V0.cuota/V0.salmes` (constants) instead of the running `cuota/salmes` in the `hip`/`sobre` lines.

- [ ] **Step 5: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/src/engine
git commit -m "feat(frontend): TypeScript port of v16 Spain engine chain with lever/preset config"
```

---

### Task 4: Engine port II — derived series (`ipvreal`) and red-line evaluator

**Files:**
- Create: `frontend/src/engine/derived.ts` (replaces placeholder), `frontend/src/engine/redlines.ts` (replaces placeholder)
- Test: `frontend/src/engine/__tests__/derived.test.ts`, `frontend/src/engine/__tests__/redlines.test.ts`

**Interfaces:**
- Consumes: `Scenario`, `SeriesKey`, `baseline()`, `runScenario()` from Task 3.
- Produces: from `derived.ts` — `ipvreal(scn: Scenario): number[]`, `type AnySeriesKey = SeriesKey | "ipvreal"`, `seriesOf(scn: Scenario, key: AnySeriesKey): number[]`, `ALL_SERIES_KEYS: AnySeriesKey[]` (41: the 40 + `ipvreal`). From `redlines.ts` — `NEAR_FRACTION = 0.10`, `ZERO_THRESHOLD_BAND = 0.5`, `type RedLineStatus = "crossed" | "near" | "safe" | "sd"`, `STATUS_LABEL: Record<RedLineStatus, string>` (`cruzada/cerca/segura/s/d`), `statusOf(value: number | null, threshold: number | null, cmp: "gt" | "lt" | null): RedLineStatus`, `evaluateRedlines(defs: { id: string; label: string; series: string; threshold: number; cmp: string; source: string }[], scn: Scenario, k: number)` → `{ id, label, series, value, threshold, cmp, status, source }[]`, `evaluatePersonaReds(reds: { t: string; thr: number | null; k: string | null; cmp: string | null; d: number | null; x: string }[], scn: Scenario, k: number)` → `{ t, x, d, value, status }[]`.

Handoff note 3 (binding): the engine does NOT emit `ipvreal`; v16's front derived it as `ipv − pi` at render time and persona 02's red line reads it. Handoff note 5 (binding): persona `reds` are **display** thresholds, never merged with the global `/redlines`. Spec §4.5 note: the near band is **10 %** of |threshold| (0.5 pp absolute for zero thresholds) — this overrides v16's 12 % everywhere in phase 2, matching the Python evaluator the API uses.

- [ ] **Step 1: Write the failing tests**

`frontend/src/engine/__tests__/derived.test.ts` — pins: at base 2026, `ipv = 12.8` (V0) and `pi = 3.0`, so `ipvreal[0] = 9.8` exactly:

```ts
import { describe, expect, it } from "vitest";
import { baseline } from "../spain";
import { ALL_SERIES_KEYS, ipvreal, seriesOf } from "../derived";

describe("derived series — ipvreal = ipv − pi (handoff note 3)", () => {
  const base = baseline();
  it("ipvreal at base 2026 is 12.8 − 3.0 = 9.8", () => {
    expect(ipvreal(base)[0]).toBeCloseTo(9.8, 9);
  });
  it("ipvreal is element-wise over the whole horizon", () => {
    const v = ipvreal(base);
    for (let i = 0; i < 25; i++) expect(v[i]).toBeCloseTo(base.ipv[i] - base.pi[i], 12);
  });
  it("seriesOf resolves engine keys and the derived key", () => {
    expect(seriesOf(base, "b")).toBe(base.b);
    expect(seriesOf(base, "ipvreal")[0]).toBeCloseTo(9.8, 9);
  });
  it("ALL_SERIES_KEYS = 40 engine keys + ipvreal", () => {
    expect(ALL_SERIES_KEYS).toHaveLength(41);
    expect(ALL_SERIES_KEYS).toContain("ipvreal");
  });
});
```

`frontend/src/engine/__tests__/redlines.test.ts` — thresholds are the REAL v12 values from `engine/redlines.py` / `/redlines`:

```ts
import { describe, expect, it } from "vitest";
import { baseline, runScenario } from "../spain";
import { BASE_LEVERS } from "../vintage";
import { STATUS_LABEL, evaluatePersonaReds, evaluateRedlines, statusOf } from "../redlines";

describe("statusOf — 10% near band, 0.5pp band at zero thresholds (spec §4.5)", () => {
  it("crossed / near / safe for gt", () => {
    expect(statusOf(7.5, 7.0, "gt")).toBe("crossed");   // Bono 10A > 7
    expect(statusOf(6.5, 7.0, "gt")).toBe("near");      // |6.5−7| = 0.5 ≤ 0.7
    expect(statusOf(3.42, 7.0, "gt")).toBe("safe");
  });
  it("crossed / near / safe for lt (Déficit > 3 % PIB is saldo < −3)", () => {
    expect(statusOf(-3.5, -3.0, "lt")).toBe("crossed");
    expect(statusOf(-2.8, -3.0, "lt")).toBe("near");    // band 0.3
    expect(statusOf(-1.0, -3.0, "lt")).toBe("safe");
  });
  it("zero threshold uses the 0.5pp absolute band (PIB a/a < 0)", () => {
    expect(statusOf(0.3, 0.0, "lt")).toBe("near");
    expect(statusOf(0.8, 0.0, "lt")).toBe("safe");
    expect(statusOf(-0.1, 0.0, "lt")).toBe("crossed");
  });
  it("null threshold/series → s/d (persona 07 data-gap rows)", () => {
    expect(statusOf(null, 7.0, "gt")).toBe("sd");
    expect(statusOf(5.0, null, "gt")).toBe("sd");
    expect(STATUS_LABEL.sd).toBe("s/d");
  });
});

describe("evaluateRedlines against the local scenario", () => {
  const DEUDA_105 = { id: "deuda_105", label: "Deuda > 105 %PIB", series: "b", threshold: 105.0, cmp: "gt", source: "crack23 [comentario]" };
  it("base 2026: deuda 106.316196 crosses the 105 line", () => {
    const out = evaluateRedlines([DEUDA_105], baseline(), 0);
    expect(out[0].status).toBe("crossed");
    expect(out[0].value).toBeCloseTo(106.316196, 6);
  });
  it("persona reds evaluate ipvreal without KeyError (persona 02, handoff note 3)", () => {
    const reds = [{ t: "IPV real a/a > 10 %", thr: 10.0, k: "ipvreal", cmp: "gt", d: 1, x: "burbuja 2004-07 [hist] · IPV nominal − IPCA" }];
    const out = evaluatePersonaReds(reds, baseline(), 0);
    expect(out[0].value).toBeCloseTo(9.8, 9);   // 12.8 − 3.0
    expect(out[0].status).toBe("near");          // |9.8 − 10| = 0.2 ≤ 1.0
  });
  it("persona 07 null rows come back s/d, no crash", () => {
    const reds = [{ t: "WGI control de la corrupción", thr: null, k: null, cmp: null, d: null, x: "API archivada [hueco de datos]" }];
    const out = evaluatePersonaReds(reds, runScenario({ ...BASE_LEVERS }), 0);
    expect(out[0].status).toBe("sd");
    expect(out[0].value).toBeNull();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/engine/__tests__/derived.test.ts src/engine/__tests__/redlines.test.ts`
Expected: FAIL — the placeholder modules export nothing.

- [ ] **Step 3: Implement `derived.ts` and `redlines.ts`**

`frontend/src/engine/derived.ts`:

```ts
import { SERIES_KEYS, type Scenario, type SeriesKey } from "./spain";

export type DerivedKey = "ipvreal";
export type AnySeriesKey = SeriesKey | DerivedKey;

/** v16 front-derived series: real house-price growth = nominal IPV − HICP (handoff note 3). */
export function ipvreal(scn: Scenario): number[] {
  return scn.ipv.map((v, i) => v - scn.pi[i]);
}

export function seriesOf(scn: Scenario, key: AnySeriesKey): number[] {
  return key === "ipvreal" ? ipvreal(scn) : scn[key];
}

export const ALL_SERIES_KEYS: AnySeriesKey[] = [...SERIES_KEYS, "ipvreal"];
```

`frontend/src/engine/redlines.ts` (port of `engine/redlines.py` evaluator; the red-line DEFINITIONS come from the API `/redlines` and the persona cards — they are not duplicated here):

```ts
import type { Scenario } from "./spain";
import { seriesOf, type AnySeriesKey } from "./derived";

export const NEAR_FRACTION = 0.10;        // spec §4.5 — overrides v16's 12 %
export const ZERO_THRESHOLD_BAND = 0.5;   // pp absolute near-band for the g < 0 line

export type RedLineStatus = "crossed" | "near" | "safe" | "sd";
export const STATUS_LABEL: Record<RedLineStatus, string> = {
  crossed: "cruzada", near: "cerca", safe: "segura", sd: "s/d",
};

export function statusOf(
  value: number | null,
  threshold: number | null,
  cmp: "gt" | "lt" | null,
): RedLineStatus {
  if (threshold === null || value === null || cmp === null || !isFinite(value)) return "sd";
  const crossed = cmp === "gt" ? value > threshold : value < threshold;
  if (crossed) return "crossed";
  const band = threshold !== 0 ? NEAR_FRACTION * Math.abs(threshold) : ZERO_THRESHOLD_BAND;
  return Math.abs(value - threshold) <= band ? "near" : "safe";
}

export interface RedLineDef {
  id: string; label: string; series: string; threshold: number; cmp: string; source: string;
}
export interface RedLineResult extends RedLineDef {
  value: number; status: RedLineStatus;
}

/** Global semaphore: /redlines defs + local scenario, evaluated at year index k. */
export function evaluateRedlines(defs: RedLineDef[], scn: Scenario, k: number): RedLineResult[] {
  return defs.map((rl) => {
    const value = seriesOf(scn, rl.series as AnySeriesKey)[k];
    return { ...rl, value, status: statusOf(value, rl.threshold, rl.cmp as "gt" | "lt") };
  });
}

export interface PersonaRed {
  t: string; thr: number | null; k: string | null; cmp: string | null; d: number | null; x: string;
}
export interface PersonaRedResult {
  t: string; x: string; d: number | null; value: number | null; status: RedLineStatus;
}

/** Persona display reds (handoff note 5): never merged with global red lines. */
export function evaluatePersonaReds(reds: PersonaRed[], scn: Scenario, k: number): PersonaRedResult[] {
  return reds.map((r) => {
    const value = r.k === null ? null : seriesOf(scn, r.k as AnySeriesKey)[k];
    return { t: r.t, x: r.x, d: r.d, value, status: statusOf(value, r.thr, r.cmp as "gt" | "lt" | null) };
  });
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/engine/__tests__/derived.test.ts src/engine/__tests__/redlines.test.ts`
Expected: PASS (11 tests).

- [ ] **Step 5: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/src/engine/derived.ts frontend/src/engine/redlines.ts frontend/src/engine/__tests__
git commit -m "feat(frontend): derived ipvreal series and red-line evaluator (10% near band)"
```

---

### Task 5: Dual-engine anchors parity battery (the load-bearing test)

**Files:**
- Test: `frontend/src/engine/__tests__/anchors.test.ts`

**Interfaces:**
- Consumes: `runScenario`, `baseline`, `Y0`, `french` (Task 3), `presetLevers` (Task 3), `BASE_LEVERS` (Task 2), and the phase-1 fixture via the `@fixtures` alias (Task 1). The fixture file is **read-only** — never regenerate or edit it from `frontend/`.
- Produces: nothing new — this is the phase's load-bearing test (spec §9 row 1). Later tasks may not change engine behavior without this suite catching it.

- [ ] **Step 1: Write the battery (it should PASS immediately — that is the point)**

The PROBE deltas are copied verbatim from `tests/test_anchors.py` (the single source of truth the fixture generator used): `{ r: 4.8, prima: 150.0, sp: 1.0, lam: 1.4, pm: 50.0, tau: 1.5, z: -1.0, ext: 3.0, dem: 0.6, idx: -0.5 }`. Fixture pins quoted in comments so a reviewer sees real numbers without opening the JSON.

`frontend/src/engine/__tests__/anchors.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import anchors from "@fixtures/engine_anchors.json";
import { BASE_LEVERS } from "../vintage";
import { presetLevers, type Levers } from "../levers";
import { Y0, baseline, runScenario } from "../spain";

/** All ten levers moved at once — verbatim from tests/test_anchors.py PROBE. */
const PROBE: Levers = {
  r: 4.8, prima: 150.0, sp: 1.0, lam: 1.4, pm: 50.0,
  tau: 1.5, z: -1.0, ext: 3.0, dem: 0.6, idx: -0.5,
};
const PINNED_SERIES = ["u", "pi", "wrealIdx", "cuota", "esf", "pens", "saldo"] as const;
const idx = (year: string | number) => Number(year) - Y0;

describe("dual-engine contract: TS engine reproduces the committed phase-1 fixture", () => {
  it("fixture is the committed vintage", () => {
    expect(anchors.vintage).toBe("2026-07-31");
  });

  it("A1 debt_central: base b at 2026/2030/2035/2050 ± 1e-6 vs fixture engine values", () => {
    // 2026: 106.316196 · 2030: 112.885096 · 2035: 129.142456 · 2050: 223.84141
    const base = baseline();
    for (const [year, pins] of Object.entries(anchors.debt_central)) {
      expect(Math.abs(base.b[idx(year)] - pins.engine)).toBeLessThanOrEqual(1e-6);
    }
  });

  it("A2 cuota_2026_base: 744.9971 ± 0.01", () => {
    expect(Math.abs(baseline().cuota[0] - anchors.cuota_2026_base)).toBeLessThanOrEqual(0.01);
  });

  it("A3 presets_debt_2050: all 8 presets ± 1e-6 (S0 223.8414 … S7 349.7973)", () => {
    for (const [pid, pin] of Object.entries(anchors.presets_debt_2050)) {
      const scn = runScenario(presetLevers(pid));
      // fixture rounds to 4 decimals; compare at that grain then at 1e-6 on the rounded value
      expect(Math.abs(Math.round(scn.b[idx(2050)] * 1e4) / 1e4 - pin)).toBeLessThanOrEqual(1e-6);
    }
  });

  it("A4 presets_series_2035_2050: 8 presets × 7 series × 2 years ± 1e-6", () => {
    // e.g. S1 2035: u 10.699724 · pi 2.711975 · wrealIdx 106.847929 · cuota 851.980821
    //              · esf 35.70086 · pens 16.6086 · saldo −10.687951
    for (const [pid, byYear] of Object.entries(anchors.presets_series_2035_2050)) {
      const scn = runScenario(presetLevers(pid));
      for (const [year, series] of Object.entries(byYear)) {
        for (const key of PINNED_SERIES) {
          const pin = (series as Record<string, number>)[key];
          expect(
            Math.abs(Math.round(scn[key][idx(year)] * 1e6) / 1e6 - pin),
            `${pid} ${year} ${key}`,
          ).toBeLessThanOrEqual(1e-6);
        }
      }
    }
  });

  it("A5 probe_bundle: all-10-lever scenario ± 1e-6 (2050 b = 373.487643)", () => {
    const scn = runScenario(PROBE);
    for (const [year, series] of Object.entries(anchors.probe_bundle)) {
      for (const [key, pin] of Object.entries(series as Record<string, number>)) {
        expect(
          Math.abs(Math.round(scn[key as keyof typeof scn][idx(year)] * 1e6) / 1e6 - pin),
          `probe ${year} ${key}`,
        ).toBeLessThanOrEqual(1e-6);
      }
    }
  });

  it("A6 base_gold_identity: ief/gnom/pb ± 1e-9 vs fixture engine values", () => {
    // 2026: ief 2.68 gnom 3.3 pb −1.35 · 2050: ief 3.47 gnom 3.3 pb −7.47
    const base = baseline();
    for (const [year, rows] of Object.entries(anchors.base_gold_identity)) {
      const k = idx(year);
      const r = rows as Record<string, { engine: number }>;
      expect(Math.abs(base.ief[k] - r.ief.engine)).toBeLessThanOrEqual(1e-9);
      expect(Math.abs(base.gnom[k] - r.gnom.engine)).toBeLessThanOrEqual(1e-9);
      expect(Math.abs(base.pb[k] - r.pb.engine)).toBeLessThanOrEqual(1e-9);
    }
  });

  it("montecarlo_seed42 is deliberately NOT asserted (PCG64 not reproducible in JS)", () => {
    // Guard that the block still exists so Metodología's claim about it stays true.
    expect(anchors.montecarlo_seed42["2050"].p50).toBeCloseTo(231.2999, 4);
  });

  it("probe differs from BASE on every lever (probe is a real all-lever move)", () => {
    // r: 4.8 vs 2.8, prima: 150 vs 45, sp: 1 vs 0, lam: 1.4 vs 0.9, pm: 50 vs 0,
    // tau: 1.5 vs 0, z: −1 vs 0, ext: 3 vs 1.8, dem: 0.6 vs 0, idx: −0.5 vs 0
    for (const id of Object.keys(PROBE) as (keyof Levers)[]) {
      expect(Math.abs(PROBE[id] - BASE_LEVERS[id])).toBeGreaterThan(1e-9);
    }
  });
});
```

Note on A3–A5 rounding: the fixture generator stored `round(value, 6)` (and 4 decimals for `presets_debt_2050`), so the TS value is rounded to the fixture's grain before the ±1e-6 comparison — same convention `tests/test_anchors.py` uses on the Python side.

- [ ] **Step 2: Run the battery**

Run: `cd frontend && npx vitest run src/engine/__tests__/anchors.test.ts`
Expected: PASS (8 tests). If any A-block fails, do NOT touch the fixture — fix `spain.ts` (Task 3) until the battery is green; the Python engine already passes the same numbers (`cd .. && python -m pytest tests/test_anchors.py` to confirm the other side).

- [ ] **Step 3: Run the whole engine suite together**

Run: `cd frontend && npx vitest run src/engine`
Expected: PASS — constants (3), spain (9), derived (4), redlines (7), anchors (8).

- [ ] **Step 4: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/src/engine/__tests__/anchors.test.ts
git commit -m "test(frontend): dual-engine anchors parity battery against phase-1 fixture"
```

---

### Task 6: API layer — types, client, hooks, MSW handlers

**Files:**
- Create: `frontend/src/api/types.ts`, `frontend/src/api/client.ts`, `frontend/src/api/hooks.ts`
- Create: `frontend/src/test/msw/fixtures.ts`, `frontend/src/test/msw/handlers.ts`, `frontend/src/test/msw/server.ts`, `frontend/src/test/msw/browser.ts`
- Create: `frontend/public/mockServiceWorker.js` (generated: `cd frontend && npx msw init public/ --save`)
- Modify: `frontend/src/test/setup.ts` (start/stop the MSW node server)
- Test: `frontend/src/api/__tests__/client.test.ts`

**Interfaces:**
- Consumes: engine (`runScenario`, `baseline`, `YEARS`, `Y0`) for the mocked `/scenario` handler; `evaluateRedlines` for its `redlines` block.
- Produces: `types.ts` mirrors `api/schemas.py` verbatim — `ApiMeta { vintage: string; computed_not_advice: boolean }`, `HealthResponse`, `VintageResponse { n_files: number; files: { name; url; fetched_at; bytes }[] }`, `ConstantsResponse { constants: { name: string; value: number; unit: string; provenance: string }[] }`, `KpiOut { valor?: unknown; unidad?: string; fuente?: string; periodo?: string }`, `SeriesOut { puntos: [string | number, number][]; fuente?: string }`, `PersonaOutItem { k: string; lab: string }`, `PersonaRedOut { t: string; thr: number | null; k: string | null; cmp: string | null; d: number | null; x: string }`, `PersonaCard { id; pill; foot; h1; meta; hot: string[]; series_keys: string[]; outs: PersonaOutItem[]; headline: string; reds: PersonaRedOut[] }`, `PersonasResponse { kpis: Record<string, KpiOut>; series: Record<string, SeriesOut>; personas: PersonaCard[] }`, `PresetsResponse { presets: { id; nm; set: Record<string, number> }[] }`, `RedLinesResponse { redlines: RedLineDef[] }`, `ScenarioRequest { levers?: Partial<Levers>; horizon?: number }`, `ScenarioResponse { horizon; years: number[]; baseline; scenario; deltas: Record<string, number[]>; personas: Record<string, { pill; headline; series: Record<string, number[]> }>; redlines: (RedLineDef & { value: number; status: string })[] }`, `MonteCarloRequest { levers?: Partial<Levers>; seed?: number; n_paths?: number; horizon?: number }`, `MonteCarloResponse { years: number[]; percentiles: Record<"p5" | "p25" | "p50" | "p75" | "p95", number[]>; n_paths: number; seed: number }` (all responses `& ApiMeta`). `client.ts` — `API_BASE` (from `import.meta.env.VITE_API_BASE ?? "http://localhost:8000"`), `class ApiError extends Error { endpoint: string; cause?: unknown }`, `api = { health(), vintage(), constants(), personas(), presets(), redlines(), scenario(req: ScenarioRequest, signal?: AbortSignal), montecarlo(req: MonteCarloRequest, signal?: AbortSignal) }` (each returns the typed promise). `hooks.ts` — `queryClient: QueryClient`, `useHealth() / useVintage() / useConstants() / usePersonas() / usePresets() / useRedlines()` (all `staleTime: Infinity`, `retry: 1`), `useMonteCarlo(levers: Levers, enabled: boolean)` (debounced 400 ms, cancel-previous, horizon 2070, seed 42, n_paths 4000). `test/msw/*` — `handlers`, `server` (node), `worker` (browser), `mockFixtures` (exported so route tests can assert against the same data).

- [ ] **Step 1: Write the failing test**

`frontend/src/api/__tests__/client.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { api, ApiError } from "../client";
import { server } from "../../test/msw/server";
import { http, HttpResponse } from "msw";

describe("typed API client against MSW", () => {
  it("GET /health carries vintage and the no-advice flag", async () => {
    const h = await api.health();
    expect(h.vintage).toBe("2026-07-31");
    expect(h.computed_not_advice).toBe(true);
    expect(h.engine_version).toBe("1.0.0");
  });
  it("GET /presets returns the 8 v16 presets with Spanish labels verbatim", async () => {
    const p = await api.presets();
    expect(p.presets).toHaveLength(8);
    expect(p.presets[1]).toEqual({ id: "S1", nm: "S1 tipos +200 pb", set: { r: 4.8 } });
    expect(p.presets[7].set).toEqual({ r: 4.8, pm: 50.0, prima: 150.0 });
  });
  it("GET /redlines returns the 9 v12 lines", async () => {
    const r = await api.redlines();
    expect(r.redlines).toHaveLength(9);
    expect(r.redlines.find((x) => x.id === "deuda_105")).toMatchObject({ series: "b", threshold: 105.0, cmp: "gt" });
  });
  it("GET /personas returns cards 01/02/03/06 with outs and reds", async () => {
    const pe = await api.personas();
    expect(pe.personas.map((c) => c.id)).toEqual(["01", "02", "03", "06"]);
    const p02 = pe.personas[1];
    expect(p02.pill).toBe("🏦 Banca");
    expect(p02.reds[0].k).toBe("ipvreal");
    expect(p02.outs).toHaveLength(5);
  });
  it("POST /scenario echoes full 2026–2050 series regardless of horizon (handoff note 4)", async () => {
    const s = await api.scenario({ levers: { r: 4.8 }, horizon: 2035 });
    expect(s.years).toHaveLength(25);
    expect(s.scenario.b).toHaveLength(25);
    expect(s.horizon).toBe(2035);
  });
  it("POST /scenario/montecarlo returns 5 percentile arrays", async () => {
    const mc = await api.montecarlo({ levers: {}, seed: 42, n_paths: 4000, horizon: 2070 });
    expect(Object.keys(mc.percentiles).sort()).toEqual(["p25", "p5", "p50", "p75", "p95"].sort());
    expect(mc.percentiles.p50).toHaveLength(mc.years.length);
    // fixture pins: p50 2030 = 113.3, 2050 = 231.2999
    expect(mc.percentiles.p50[mc.years.indexOf(2030)]).toBeCloseTo(113.3, 4);
    expect(mc.percentiles.p50[mc.years.indexOf(2050)]).toBeCloseTo(231.2999, 4);
  });
  it("network/HTTP failure throws ApiError naming the endpoint", async () => {
    server.use(http.get("http://localhost:8000/constants", () => HttpResponse.error()));
    await expect(api.constants()).rejects.toThrowError(ApiError);
    await expect(api.constants()).rejects.toThrow(/\/constants/);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/api`
Expected: FAIL — `Cannot find module '../client'`.

- [ ] **Step 3: Implement types, client, hooks, MSW**

`frontend/src/api/types.ts` (shapes confirmed against the live phase-1 API on 2026-08-07):

```ts
import type { Levers } from "../engine/levers";
import type { RedLineDef } from "../engine/redlines";

export interface ApiMeta { vintage: string; computed_not_advice: boolean }

export interface HealthResponse extends ApiMeta { status: string; engine_version: string }

export interface VintageFileOut { name: string; url: string; fetched_at: string; bytes: number }
export interface VintageResponse extends ApiMeta { n_files: number; files: VintageFileOut[] }

export interface ConstantOut { name: string; value: number; unit: string; provenance: string }
export interface ConstantsResponse extends ApiMeta { constants: ConstantOut[] }

export interface KpiOut { valor?: unknown; unidad?: string; fuente?: string; periodo?: string }
export interface SeriesOut { puntos: [string | number, number][]; fuente?: string }
export interface PersonaOutItem { k: string; lab: string }
export interface PersonaRedOut {
  t: string; thr: number | null; k: string | null; cmp: string | null; d: number | null; x: string;
}
export interface PersonaCard {
  id: string; pill: string; foot: string; h1: string; meta: string;
  hot: string[]; series_keys: string[]; outs: PersonaOutItem[];
  headline: string; reds: PersonaRedOut[];
}
export interface PersonasResponse extends ApiMeta {
  kpis: Record<string, KpiOut>;
  series: Record<string, SeriesOut>;
  personas: PersonaCard[];
}

export interface PresetOut { id: string; nm: string; set: Record<string, number> }
export interface PresetsResponse extends ApiMeta { presets: PresetOut[] }

export interface RedLinesResponse extends ApiMeta { redlines: RedLineDef[] }

export interface ScenarioRequest { levers?: Partial<Levers>; horizon?: number }
export interface RedLineStatusOut extends RedLineDef { value: number; status: string }
export interface PersonaDependentsOut { pill: string; headline: string; series: Record<string, number[]> }
export interface ScenarioResponse extends ApiMeta {
  horizon: number; years: number[];
  baseline: Record<string, number[]>;
  scenario: Record<string, number[]>;
  deltas: Record<string, number[]>;
  personas: Record<string, PersonaDependentsOut>;
  redlines: RedLineStatusOut[];
}

export interface MonteCarloRequest { levers?: Partial<Levers>; seed?: number; n_paths?: number; horizon?: number }
export type PercentileKey = "p5" | "p25" | "p50" | "p75" | "p95";
export interface MonteCarloResponse extends ApiMeta {
  years: number[]; percentiles: Record<PercentileKey, number[]>; n_paths: number; seed: number;
}
```

`frontend/src/api/client.ts`:

```ts
import type {
  ConstantsResponse, HealthResponse, MonteCarloRequest, MonteCarloResponse,
  PersonasResponse, PresetsResponse, RedLinesResponse, ScenarioRequest,
  ScenarioResponse, VintageResponse,
} from "./types";

export const API_BASE: string = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export class ApiError extends Error {
  endpoint: string;
  constructor(endpoint: string, detail: string, options?: { cause?: unknown }) {
    super(`API ${endpoint}: ${detail}`, options);
    this.name = "ApiError";
    this.endpoint = endpoint;
  }
}

async function request<T>(endpoint: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${endpoint}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch (cause) {
    throw new ApiError(endpoint, "sin conexión", { cause });
  }
  if (!res.ok) throw new ApiError(endpoint, `HTTP ${res.status}`);
  return (await res.json()) as T;
}

export const api = {
  health: () => request<HealthResponse>("/health"),
  vintage: () => request<VintageResponse>("/vintage"),
  constants: () => request<ConstantsResponse>("/constants"),
  personas: () => request<PersonasResponse>("/personas"),
  presets: () => request<PresetsResponse>("/presets"),
  redlines: () => request<RedLinesResponse>("/redlines"),
  scenario: (body: ScenarioRequest, signal?: AbortSignal) =>
    request<ScenarioResponse>("/scenario", { method: "POST", body: JSON.stringify(body), signal }),
  montecarlo: (body: MonteCarloRequest, signal?: AbortSignal) =>
    request<MonteCarloResponse>("/scenario/montecarlo", { method: "POST", body: JSON.stringify(body), signal }),
};
```

`frontend/src/api/hooks.ts`:

```ts
import { QueryClient, keepPreviousData, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import type { Levers } from "../engine/levers";
import { api } from "./client";

export const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: Infinity, retry: 1, refetchOnWindowFocus: false } },
});

const STATIC = { staleTime: Infinity } as const;
export const useHealth = () => useQuery({ queryKey: ["health"], queryFn: api.health, ...STATIC });
export const useVintage = () => useQuery({ queryKey: ["vintage"], queryFn: api.vintage, ...STATIC });
export const useConstants = () => useQuery({ queryKey: ["constants"], queryFn: api.constants, ...STATIC });
export const usePersonas = () => useQuery({ queryKey: ["personas"], queryFn: api.personas, ...STATIC });
export const usePresets = () => useQuery({ queryKey: ["presets"], queryFn: api.presets, ...STATIC });
export const useRedlines = () => useQuery({ queryKey: ["redlines"], queryFn: api.redlines, ...STATIC });

/** Debounced value: trails `value` by `ms` (spec §3: MC debounced 400 ms). */
export function useDebounced<T>(value: T, ms: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return debounced;
}

/** Monte Carlo fan — server-side by design (handoff note 1). Cancel-previous via query key + signal. */
export function useMonteCarlo(levers: Levers, enabled: boolean) {
  const debouncedLevers = useDebounced(levers, 400);
  return useQuery({
    queryKey: ["montecarlo", debouncedLevers],
    queryFn: ({ signal }) =>
      api.montecarlo({ levers: debouncedLevers, seed: 42, n_paths: 4000, horizon: 2070 }, signal),
    enabled,
    staleTime: Infinity,
    placeholderData: keepPreviousData,
  });
}
```

`frontend/src/test/msw/fixtures.ts` — mock payloads use REAL phase-1 values: preset/red-line/persona blocks verbatim from the API; historical series truncated to first/last real points (full arrays live server-side; mocks stay small on purpose):

```ts
import type { PersonaCard, PresetOut } from "../../api/types";
import type { RedLineDef } from "../../engine/redlines";
import { CONSTANTS_META } from "../../engine/constants";

export const MOCK_VINTAGE = "2026-07-31";

export const mockPresets: PresetOut[] = [
  { id: "S0", nm: "S0 base", set: {} },
  { id: "S1", nm: "S1 tipos +200 pb", set: { r: 4.8 } },
  { id: "S2", nm: "S2 petróleo +50 %", set: { pm: 50.0 } },
  { id: "S3", nm: "S3 consolidación", set: { sp: 1.0 } },
  { id: "S4", nm: "S4 productividad", set: { lam: 1.4 } },
  { id: "S5", nm: "S5 desregulación lab.", set: { z: -1.0, tau: -1.5 } },
  { id: "S6", nm: "S6 envejecimiento", set: { dem: 0.6 } },
  { id: "S7", nm: "S7 adverso", set: { r: 4.8, pm: 50.0, prima: 150.0 } },
];

export const mockRedlines: RedLineDef[] = [
  { id: "bono_rescate", label: "Bono 10A > 7 %", series: "bono", threshold: 7.0, cmp: "gt", source: "zona rescate: GRC/PRT/IRL pidieron rescate con bonos ≈7 %; ES tocó 7,6 % en jul-2012 [hist]" },
  { id: "paro_record", label: "Paro > 26,9 %", series: "u", threshold: 26.9, cmp: "gt", source: "máximo histórico ES (T1-2013) [hist]" },
  { id: "deficit_maastricht", label: "Déficit > 3 % PIB", series: "saldo", threshold: -3.0, cmp: "lt", source: "umbral Maastricht [regla UE]" },
  { id: "deficit_suelo_2009", label: "Déficit > 11,3 % PIB", series: "saldo", threshold: -11.3, cmp: "lt", source: "suelo 2009: ES −11,3 % PIB [hist]" },
  { id: "deuda_105", label: "Deuda > 105 % PIB", series: "b", threshold: 105.0, cmp: "gt", source: "crack23: «deuda brutal que ya está por encima del 105 %» [comentario]" },
  { id: "deuda_120", label: "Deuda > 120 % PIB", series: "b", threshold: 120.0, cmp: "gt", source: "≈ pico COVID ES 2020: 119,3 [hist]" },
  { id: "inflacion_10", label: "Inflación > 10 %", series: "pi", threshold: 10.0, cmp: "gt", source: "ola inflacionaria 2022: ES pico 10,8 % jul-2022 [hist]" },
  { id: "esfuerzo_40", label: "Esfuerzo vivienda > 40 %", series: "esf", threshold: 40.0, cmp: "gt", source: "definición Eurostat de sobrecarga (housing cost overburden) [UE]" },
  { id: "pobreza_infantil_30", label: "Pobreza infantil > 30 %", series: "arop", threshold: 30.0, cmp: "gt", source: "ES 27–28 % crónico, 30 % en picos post-2013; media UE ≈19 % [hist]" },
];

/** The 4 shipped cards — verbatim from the phase-1 /personas payload (engine/spain.py PERSONAS). */
export const mockPersonaCards: PersonaCard[] = [
  {
    id: "01", pill: "💼 Bonista", foot: "💼 bonista",
    h1: "💼 Inversor en bonos: ¿me pagarán los 10 años?",
    meta: "ecb_bono10y_es.csv · ecb_bono10y_de.csv · eurostat_gov_debt_es.csv · eurostat_gov_deficit_es.csv · interest_paid.csv · gold_escenarios_deuda.csv",
    hot: ["r", "prima", "sp", "dem"], series_keys: ["bono10y_es_5a"],
    outs: [
      { k: "bono", lab: "Bono 10A España" }, { k: "spread", lab: "Spread ES–DE" },
      { k: "b", lab: "Deuda pública" }, { k: "saldo", lab: "Saldo público" },
      { k: "int", lab: "Intereses / PIB" },
    ],
    headline: "b",
    reds: [
      { t: "Deuda > 105 %PIB", thr: 105.0, k: "b", cmp: "gt", d: 1, x: "narrativa crack23 [comentario]" },
      { t: "Deuda > 120 %PIB", thr: 120.0, k: "b", cmp: "gt", d: 1, x: "techo COVID 2020: 119,3 [hist]" },
      { t: "Bono 10A > 7 %", thr: 7.0, k: "bono", cmp: "gt", d: 2, x: "zona rescate: crisis 2012 [hist]" },
    ],
  },
  {
    id: "02", pill: "🏦 Banca", foot: "🏦 banca hipotecaria",
    h1: "🏦 Banco hipotecario: ¿a quién presto, a qué tipo y con qué mora esperada?",
    meta: "ecb_euribor12m.csv · bls_criterios_vivienda.csv · ine_hipotecas_ccaa.csv · eurostat_hpi_q_es.csv · gold_cuota_teorica.csv",
    hot: ["r", "z", "tau", "ext"], series_keys: ["euribor12m_5a"],
    outs: [
      { k: "r", lab: "Euríbor 12m" }, { k: "bls", lab: "BLS endurecimiento" },
      { k: "hip", lab: "Nueva producción" }, { k: "ipv", lab: "Precio vivienda a/a" },
      { k: "cuota", lab: "Cuota mediana" },
    ],
    headline: "cuota",
    reds: [
      { t: "IPV real a/a > 10 %", thr: 10.0, k: "ipvreal", cmp: "gt", d: 1, x: "burbuja 2004-07 [hist] · IPV nominal − IPCA" },
      { t: "BLS endurecimiento > 20 %", thr: 20.0, k: "bls", cmp: "gt", d: 0, x: "nivel de contracción de crédito [hist]" },
      { t: "Paro > 15 % (motor de mora)", thr: 15.0, k: "u", cmp: "gt", d: 1, x: "último nivel visto en 2021-07 (15,2) [hist]" },
    ],
  },
  {
    id: "03", pill: "🔑 Comprador", foot: "🔑 comprador de vivienda",
    h1: "🔑 Comprador de vivienda: ¿qué esfuerzo me exige el techo?",
    meta: "gold_cuota_teorica.csv · ine_salarios.csv (EAES) · ecb_euribor12m.csv · eurostat_hpi_q_es.csv · eurostat_overburden_es.csv",
    hot: ["r", "lam", "z", "pm"], series_keys: ["vivienda_precio_yoy_5a"],
    outs: [
      { k: "precio", lab: "Precio mediano CCAA" }, { k: "cuota", lab: "Cuota mediana" },
      { k: "esf", lab: "Esfuerzo cuota/renta" }, { k: "ipv", lab: "Precio vivienda a/a" },
      { k: "sobre", lab: "Sobrecarga vivienda" },
    ],
    headline: "esf",
    reds: [
      { t: "Esfuerzo cuota/renta > 35 %", thr: 35.0, k: "esf", cmp: "gt", d: 1, x: "regla prudencial [regla]" },
      { t: "Sobrecarga > 40 % renta", thr: 15.0, k: "sobre", cmp: "gt", d: 1, x: "definición Eurostat · muerde al flujo nuevo [UE]" },
      { t: "IPV a/a > 10 %", thr: 10.0, k: "ipv", cmp: "gt", d: 1, x: "burbuja 2004-07 [hist]" },
    ],
  },
  {
    id: "06", pill: "🗳️ Político", foot: "🗳️ político (decisor honesto)",
    h1: "🗳️ ¿Qué palanca puedo mover sin cruzar una línea roja?",
    meta: "eurostat_gov_debt_es · eurostat_gov_deficit_es · eurostat_une_rt_m_es · eurostat_gdp_q_es · interest_paid · gold_escenarios_deuda",
    hot: ["sp", "r", "tau", "z", "lam", "dem"], series_keys: ["deficit_pib_hist"],
    outs: [
      { k: "b", lab: "Deuda pública" }, { k: "saldo", lab: "Saldo público" },
      { k: "u", lab: "Paro total" }, { k: "g", lab: "PIB real" },
      { k: "int", lab: "Intereses" },
    ],
    headline: "b",
    reds: [
      { t: "Deuda > 120 % PIB", thr: 120.0, k: "b", cmp: "gt", d: 1, x: "techo COVID 2020: 119,3 [hist]" },
      { t: "Déficit > 3 % PIB", thr: -3.0, k: "saldo", cmp: "lt", d: 1, x: "regla fiscal UE [regla UE]" },
      { t: "Paro > 15 %", thr: 15.0, k: "u", cmp: "gt", d: 1, x: "coste social del ajuste [hist]" },
    ],
  },
];

/** Historical series — REAL first/last points from the live payload, truncated for test size. */
export const mockSeries = {
  bono10y_es_5a: { fuente: "ecb_bono10y_es.csv", puntos: [["2021-07", 0.331], ["2021-08", 0.214], ["2021-09", 0.327], ["2026-04", 3.448], ["2026-05", 3.488], ["2026-06", 3.417]] },
  euribor12m_5a: { fuente: "ecb_euribor12m.csv", puntos: [["2021-07", -0.491], ["2021-08", -0.498], ["2021-09", -0.492], ["2026-04", 2.747], ["2026-05", 2.804], ["2026-06", 2.798]] },
  vivienda_precio_yoy_5a: { fuente: "eurostat_hpi_q_es.csv", puntos: [["2020-Q2", 2.2], ["2020-Q3", 1.8], ["2020-Q4", 1.7], ["2025-Q3", 12.8], ["2025-Q4", 12.9], ["2026-Q1", 12.8]] },
  deficit_pib_hist: { fuente: "eurostat_gov_deficit_es.csv", puntos: [["1995.0", -6.8], ["1996.0", -5.9], ["1997.0", -3.9], ["2023.0", -3.3], ["2024.0", -3.2], ["2025.0", -2.4]] },
} as const;

export const mockKpis = {
  euribor12m: { valor: 2.8, fuente: "ecb_euribor12m.csv", periodo: "2026-06" },
  spread_es_de: { valor: 45, fuente: "ecb_bono10y_es.csv · ecb_bono10y_de.csv", periodo: "2026-06" },
  paro_total: { valor: 10.1, periodo: "2026-06" },
  hicp_es: { valor: 3.0, periodo: "2025-12" },
  pib_yoy: { valor: 2.7, periodo: "2026-Q2" },
} as const;

/** Fixture montecarlo_seed42 pins at 2030/2050/2070; linear in between (display-only mock). */
export function mockPercentiles(years: number[]) {
  const pins: Record<string, Record<number, number>> = {
    p5:  { 2026: 106.3, 2030: 107.2674, 2050: 176.4991, 2070: 271.9047 },
    p25: { 2026: 106.3, 2030: 110.7682, 2050: 206.8693, 2070: 347.1841 },
    p50: { 2026: 106.3, 2030: 113.3,    2050: 231.2999, 2070: 408.8999 },
    p75: { 2026: 106.3, 2030: 116.0439, 2050: 258.6826, 2070: 483.7138 },
    p95: { 2026: 106.3, 2030: 119.7131, 2050: 303.8985, 2070: 619.477 },
  };
  const interp = (pin: Record<number, number>, y: number): number => {
    const ys = Object.keys(pin).map(Number).sort((a, b) => a - b);
    if (y <= ys[0]) return pin[ys[0]];
    if (y >= ys[ys.length - 1]) return pin[ys[ys.length - 1]];
    const hi = ys.find((p) => p >= y)!;
    const lo = ys[ys.indexOf(hi) - 1];
    return pin[lo] + ((pin[hi] - pin[lo]) * (y - lo)) / (hi - lo);
  };
  return Object.fromEntries(
    (["p5", "p25", "p50", "p75", "p95"] as const).map((p) => [p, years.map((y) => interp(pins[p], y))]),
  ) as Record<"p5" | "p25" | "p50" | "p75" | "p95", number[]>;
}
```

`frontend/src/test/msw/handlers.ts` — `/scenario` runs the REAL TS engine so the shell's cross-check (Task 11) passes by construction; every response carries `ApiMeta`:

```ts
import { http, HttpResponse } from "msw";
import { BASE_LEVERS } from "../../engine/vintage";
import { SERIES_KEYS, YEARS, baseline, runScenario } from "../../engine/spain";
import { evaluateRedlines } from "../../engine/redlines";
import { CONSTANTS_META } from "../../engine/constants";
import type { MonteCarloRequest, ScenarioRequest } from "../../api/types";
import {
  MOCK_VINTAGE, mockKpis, mockPercentiles, mockPersonaCards, mockPresets, mockRedlines, mockSeries,
} from "./fixtures";

const META = { vintage: MOCK_VINTAGE, computed_not_advice: true };
const BASE = "http://localhost:8000";

export const handlers = [
  http.get(`${BASE}/health`, () =>
    HttpResponse.json({ ...META, status: "ok", engine_version: "1.0.0" })),
  http.get(`${BASE}/vintage`, () =>
    HttpResponse.json({
      ...META, n_files: 141,
      files: [{ name: "gov_10a_exp_TE", url: "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/gov_10a_exp?na_item=TE", fetched_at: "2026-07-18T08:31:29", bytes: 366460 }],
    })),
  http.get(`${BASE}/constants`, () => HttpResponse.json({ ...META, constants: CONSTANTS_META })),
  http.get(`${BASE}/personas`, () =>
    HttpResponse.json({ ...META, kpis: mockKpis, series: mockSeries, personas: mockPersonaCards })),
  http.get(`${BASE}/presets`, () => HttpResponse.json({ ...META, presets: mockPresets })),
  http.get(`${BASE}/redlines`, () => HttpResponse.json({ ...META, redlines: mockRedlines })),

  http.post(`${BASE}/scenario`, async ({ request }) => {
    const body = (await request.json()) as ScenarioRequest;
    const levers = { ...BASE_LEVERS, ...(body.levers ?? {}) };
    const horizon = body.horizon ?? 2050;
    const scn = runScenario(levers);
    const base = baseline();
    const deltas = Object.fromEntries(
      SERIES_KEYS.map((k) => [k, scn[k].map((v, i) => v - base[k][i])]),
    );
    return HttpResponse.json({
      ...META, horizon, years: YEARS,
      baseline: base, scenario: scn, deltas,
      personas: {},
      redlines: evaluateRedlines(mockRedlines, scn, horizon - 2026),
    });
  }),

  http.post(`${BASE}/scenario/montecarlo`, async ({ request }) => {
    const body = (await request.json()) as MonteCarloRequest;
    const horizon = body.horizon ?? 2070;
    const years = Array.from({ length: horizon - 2026 + 1 }, (_, i) => 2026 + i);
    return HttpResponse.json({
      ...META, years, percentiles: mockPercentiles(years),
      n_paths: body.n_paths ?? 4000, seed: body.seed ?? 42,
    });
  }),
];
```

`frontend/src/test/msw/server.ts`:

```ts
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
```

`frontend/src/test/msw/browser.ts` (used by the mocked preview build for Playwright, Task 15):

```ts
import { setupWorker } from "msw/browser";
import { handlers } from "./handlers";

export const worker = setupWorker(...handlers);
```

Append to `frontend/src/test/setup.ts`:

```ts
import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll } from "vitest";
import { server } from "./msw/server";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

Generate the worker script once: `cd frontend && npx msw init public/ --save` (commits `public/mockServiceWorker.js`).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/api`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/src/api frontend/src/test frontend/public/mockServiceWorker.js
git commit -m "feat(frontend): typed API client, React Query hooks and MSW mock layer"
```

---

### Task 7: Scenario store — levers, horizon, URL sync

**Files:**
- Create: `frontend/src/state/scenarioStore.ts`
- Test: `frontend/src/state/__tests__/store.test.ts`

**Interfaces:**
- Consumes: `Levers`, `LeverId`, `LEVER_IDS`, `presetLevers`, `activePresetId`, `isMoved`, `allAtBase` (Task 3); `BASE_LEVERS` (Task 2); `Y0`, `Y1`, `runScenario`, `baseline` (Task 3).
- Produces: `useScenarioStore` (Zustand) with state `{ levers: Levers; horizon: number }` and actions `setLever(id: LeverId, value: number)`, `applyPreset(presetId: string)`, `setHorizon(year: number)`, `resetAll()`; helpers `kIndex(horizon: number): number` (= `horizon − Y0`), `stateToSearch(levers: Levers, horizon: number): string`, `searchToPatch(search: string): { levers: Partial<Levers>; horizon?: number }`, `initFromUrl(): void`, `startUrlSync(): () => void`; hook `useScenario(): Scenario` (memoized local recompute — the <16 ms path); `HORIZON_YEARS = [2026, 2030, 2035, 2040, 2050]`.

State shape preserved from v16 (§E.1/E.3): lever vector + horizon, only **non-base** lever values serialized to the query string via `history.replaceState` (no history spam). Persona lives in the route path (`/persona/:id`), not in the store.

- [ ] **Step 1: Write the failing test**

`frontend/src/state/__tests__/store.test.ts`:

```ts
import { beforeEach, describe, expect, it } from "vitest";
import { BASE_LEVERS } from "../../engine/vintage";
import {
  HORIZON_YEARS, initFromUrl, kIndex, searchToPatch, stateToSearch, useScenarioStore,
} from "../scenarioStore";

describe("scenarioStore — lever vector + horizon (v16 state shape)", () => {
  beforeEach(() => {
    useScenarioStore.getState().resetAll();
    window.history.replaceState(null, "", "/");
  });

  it("boots at base levers, horizon 2026", () => {
    const s = useScenarioStore.getState();
    expect(s.levers).toEqual({ ...BASE_LEVERS });
    expect(s.horizon).toBe(2026);
    expect(kIndex(s.horizon)).toBe(0);
  });

  it("setLever / resetAll", () => {
    useScenarioStore.getState().setLever("r", 4.8);
    expect(useScenarioStore.getState().levers.r).toBe(4.8);
    useScenarioStore.getState().resetAll();
    expect(useScenarioStore.getState().levers).toEqual({ ...BASE_LEVERS });
  });

  it("applyPreset replaces the whole vector (S7: r 4.8, pm 50, prima 150)", () => {
    useScenarioStore.getState().setLever("z", -1.0);
    useScenarioStore.getState().applyPreset("S7");
    const L = useScenarioStore.getState().levers;
    expect(L).toEqual({ ...BASE_LEVERS, r: 4.8, pm: 50.0, prima: 150.0 });
    expect(L.z).toBe(0.0); // preset resets levers outside its set
  });

  it("setHorizon clamps to [2026, 2050] and HORIZON_YEARS are the rail buttons", () => {
    useScenarioStore.getState().setHorizon(2035);
    expect(useScenarioStore.getState().horizon).toBe(2035);
    useScenarioStore.getState().setHorizon(2099);
    expect(useScenarioStore.getState().horizon).toBe(2050);
    expect(HORIZON_YEARS).toEqual([2026, 2030, 2035, 2040, 2050]);
  });

  it("URL round-trip: only moved levers + horizon serialize", () => {
    expect(stateToSearch({ ...BASE_LEVERS }, 2026)).toBe("h=2026");
    const search = stateToSearch({ ...BASE_LEVERS, r: 4.8, sp: 1.0 }, 2035);
    expect(search).toBe("h=2035&r=4.8&sp=1");
    const patch = searchToPatch(`?${search}`);
    expect(patch.horizon).toBe(2035);
    expect(patch.levers).toEqual({ r: 4.8, sp: 1.0 });
  });

  it("searchToPatch ignores junk and clamps to lever ranges", () => {
    const patch = searchToPatch("?h=2032&r=99&foo=bar&z=-1.0");
    expect(patch.levers.r).toBe(6.0);   // clamped to LEVER_SPECS max
    expect(patch.levers.z).toBe(-1.0);
    expect((patch.levers as Record<string, unknown>).foo).toBeUndefined();
  });

  it("initFromUrl applies ?h & levers to the store", () => {
    window.history.replaceState(null, "", "/?h=2035&r=4.8");
    initFromUrl();
    expect(useScenarioStore.getState().levers.r).toBe(4.8);
    expect(useScenarioStore.getState().horizon).toBe(2035);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/state/__tests__/store.test.ts`
Expected: FAIL — `Cannot find module '../scenarioStore'`.

- [ ] **Step 3: Implement the store**

`frontend/src/state/scenarioStore.ts`:

```ts
import { useMemo } from "react";
import { create } from "zustand";
import { BASE_LEVERS } from "../engine/vintage";
import {
  LEVER_IDS, LEVER_SPECS, isMoved, presetLevers, type LeverId, type Levers,
} from "../engine/levers";
import { Y0, Y1, runScenario, type Scenario } from "../engine/spain";

export const HORIZON_YEARS = [2026, 2030, 2035, 2040, 2050];

interface ScenarioState {
  levers: Levers;
  horizon: number;
  setLever: (id: LeverId, value: number) => void;
  applyPreset: (presetId: string) => void;
  setHorizon: (year: number) => void;
  resetAll: () => void;
}

const clampHorizon = (y: number) => Math.min(Y1, Math.max(Y0, Math.round(y)));

export const useScenarioStore = create<ScenarioState>()((set) => ({
  levers: { ...BASE_LEVERS },
  horizon: Y0,
  setLever: (id, value) => set((s) => ({ levers: { ...s.levers, [id]: value } })),
  applyPreset: (presetId) => set({ levers: presetLevers(presetId) }),
  setHorizon: (year) => set({ horizon: clampHorizon(year) }),
  resetAll: () => set({ levers: { ...BASE_LEVERS }, horizon: Y0 }),
}));

export const kIndex = (horizon: number): number => horizon - Y0;

/** Local recompute — spec §3: <16 ms, no network. */
export function useScenario(): Scenario {
  const levers = useScenarioStore((s) => s.levers);
  return useMemo(() => runScenario(levers), [levers]);
}

// ---- URL sync (v16 §E.3: replaceState, only non-base levers) ----
const spec = Object.fromEntries(LEVER_SPECS.map((s) => [s.id, s]));

export function stateToSearch(levers: Levers, horizon: number): string {
  const q = new URLSearchParams();
  q.set("h", String(horizon));
  for (const id of LEVER_IDS) {
    if (isMoved(levers, id)) q.set(id, String(levers[id]));
  }
  return q.toString();
}

export function searchToPatch(search: string): { levers: Partial<Levers>; horizon?: number } {
  const q = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const levers: Partial<Levers> = {};
  for (const id of LEVER_IDS) {
    const raw = q.get(id);
    if (raw === null) continue;
    const v = Number.parseFloat(raw);
    if (!Number.isFinite(v)) continue;
    levers[id] = Math.min(spec[id].max, Math.max(spec[id].min, v));
  }
  const h = q.get("h");
  return { levers, horizon: h !== null && Number.isFinite(Number(h)) ? clampHorizon(Number(h)) : undefined };
}

export function initFromUrl(): void {
  const { levers, horizon } = searchToPatch(window.location.search);
  useScenarioStore.setState((s) => ({
    levers: { ...s.levers, ...levers },
    horizon: horizon ?? s.horizon,
  }));
}

/** Subscribe once at boot; returns unsubscribe. Keeps ?h=&<lever>= live without history spam. */
export function startUrlSync(): () => void {
  return useScenarioStore.subscribe((s) => {
    const search = stateToSearch(s.levers, s.horizon);
    window.history.replaceState(null, "", `${window.location.pathname}?${search}`);
  });
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/state/__tests__/store.test.ts`
Expected: PASS (7 tests). Note `stateToSearch` renders `sp=1` (not `1.0`) — JS `String(1.0)`; the test pins that.

- [ ] **Step 5: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/src/state/scenarioStore.ts frontend/src/state/__tests__/store.test.ts
git commit -m "feat(frontend): Zustand scenario store with v16 URL-sync semantics"
```

---

### Task 8: Editorial primitives — Stamp, Gauge, Semaphore, Chain, NarrativeBlock, KpiRow

**Files:**
- Create: `frontend/src/lib/motion.ts`, `frontend/src/components/Stamp.tsx`, `Gauge.tsx`, `Semaphore.tsx`, `Chain.tsx`, `NarrativeBlock.tsx`, `KpiRow.tsx`
- Test: `frontend/src/components/__tests__/stamp.test.tsx`, `gauge.test.tsx`, `semaphore.test.tsx`, `chain.test.tsx`, `kpirow.test.tsx`

**Interfaces:**
- Consumes: `nf`, `sg`, `eur` (Task 1); `statusOf`, `STATUS_LABEL`, `RedLineStatus`, `PersonaRedResult`, `RedLineResult` (Task 4); `allAtBase` (Task 3); CSS classes from `base.css` (Task 1).
- Produces: `useReducedMotion(): boolean` and `useRollup(value: number, ms?: number): number` from `src/lib/motion.ts` (roll-up = spec §5 number animation, ~180 ms, no-op under reduced motion; Task 9's charts reuse `useReducedMotion`). Plus:
  - `Stamp({ fresh, year }: { fresh: boolean; year: number })` → `<span class="badge-fwd[ lab]">📅 dato observado · vintage | 🔮 condicional · {year}</span>`.
  - `Gauge({ value, lo, hi, base, red, redCmp }: { value: number; lo: number; hi: number; base: number; red?: number; redCmp?: "gt" | "lt" })` → `.gaugebar` div; exported helper `dialDomain(values: number[], red?: number): [number, number]` (min/max ∪ red, 16 % pad — same rule as the v16 `chart()` auto-domain).
  - `Semaphore({ items }: { items: SemaphoreItem[] })` where `SemaphoreItem = { icon?: string; title: string; valueText: string; status: RedLineStatus; note: string }` — rows with `.st.cross/.near/.safe/.sd` pills labeled `cruzada/cerca/segura/s⁄d`.
  - `Chain({ specs, scn, base, k }: { specs: ChainSpec[]; scn: Scenario; base: Scenario; k: number })` with `ChainSpec = { a: string; u: string; t: string; k: SeriesKey; d: number; un: string }` (v16 persona `chains` row shape).
  - `NarrativeBlock({ text, cite, header = "✦ Escenario condicional" }: { text: string; cite: string; header?: string })`.
  - `KpiRow({ outs, scn, base, k, fresh, year, personaReds }: { outs: { k: string; lab: string }[]; scn: Scenario; base: Scenario; k: number; fresh: boolean; year: number; personaReds?: PersonaRedOut[] })` — the 5-tile `.outs` grid; each tile: label, value (`nf`, per-series decimals), `sg` delta vs base with `.bad/.good`, `Gauge`, `Stamp`.
  - `SERIES_FORMAT: Record<string, { dec: number; unit: string }>` exported from `KpiRow.tsx` — decimals/units for every engine key used by tiles (e.g. `b {dec:1, unit:"%PIB"}`, `cuota {dec:0, unit:"€/mes"}`, `bono {dec:2, unit:"%"}`, `hip {dec:0, unit:"/año"}`, `u {dec:1, unit:"%"}`).

Semantics locked here: **delta polarity** — for series where up is bad (`b, u, pi, cuota, esf, int, bono, spread, r, arop, dep, pens, sobre, temp, ujuv, bls, deficitAbs`) a positive delta gets `.bad`; for the rest (`g, gnom, wnom, wreal, wrealIdx, salario, salmes, saldo, pb, edu, d1, p2, d3, p51, gtot, hip, auton, nomreal, lvl, precio, ipv, ief, vida`) a positive delta gets `.good`. Export `UP_IS_BAD: Set<string>` from `KpiRow.tsx` so Chain and Inicio reuse the same polarity.

- [ ] **Step 1: Write the failing tests**

`frontend/src/components/__tests__/stamp.test.tsx` (spec §5: stamps computed, never authored):

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Stamp } from "../Stamp";

describe("Stamp — 📅 observed vs 🔮 conditional", () => {
  it("fresh (levers at base + horizon hoy) → 📅 dato observado", () => {
    render(<Stamp fresh year={2026} />);
    const el = screen.getByText(/📅 dato observado · vintage/);
    expect(el).toHaveClass("badge-fwd");
    expect(el).not.toHaveClass("lab");
  });
  it("any lever moved or horizon > hoy → 🔮 condicional · year", () => {
    render(<Stamp fresh={false} year={2035} />);
    const el = screen.getByText("🔮 condicional · 2035");
    expect(el).toHaveClass("badge-fwd", "lab");
  });
});
```

`frontend/src/components/__tests__/gauge.test.tsx`:

```tsx
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Gauge, dialDomain } from "../Gauge";

describe("Gauge — flat v16 dial bar", () => {
  it("fill width is value normalized to [lo,hi]", () => {
    const { container } = render(<Gauge value={106.3} lo={100} hi={130} base={106.3} red={120} redCmp="gt" />);
    const fill = container.querySelector(".gaugebar .f") as HTMLElement;
    expect(fill.style.width).toBe("21%"); // (106.3−100)/30 = 0.21
  });
  it("crossed threshold → .bad, within 10% of |thr| → .warn2, else default", () => {
    const bad = render(<Gauge value={121} lo={100} hi={130} base={106} red={120} redCmp="gt" />).container;
    expect(bad.querySelector(".f")!.className).toContain("bad");
    const warn = render(<Gauge value={112} lo={100} hi={130} base={106} red={120} redCmp="gt" />).container;
    expect(warn.querySelector(".f")!.className).toContain("warn2"); // |112−120| = 8 ≤ 12
    const ok = render(<Gauge value={104} lo={100} hi={130} base={106} red={120} redCmp="gt" />).container;
    expect(ok.querySelector(".f")!.className).not.toContain("bad");
    expect(ok.querySelector(".f")!.className).not.toContain("warn2");
  });
  it("renders baseline tick and red tick at their normalized positions", () => {
    const { container } = render(<Gauge value={110} lo={100} hi={130} base={106} red={120} redCmp="gt" />);
    expect((container.querySelector(".bm") as HTMLElement).style.left).toBe("20%");
    expect((container.querySelector(".rl") as HTMLElement).style.left).toBe("66.67%");
  });
  it("dialDomain pads min/max by 16% and includes the red line", () => {
    const [lo, hi] = dialDomain([100, 110], 120);
    expect(lo).toBeCloseTo(100 - 20 * 0.16, 9);
    expect(hi).toBeCloseTo(120 + 20 * 0.16, 9);
  });
});
```

`frontend/src/components/__tests__/semaphore.test.tsx` (spec §9: status colors match status strings):

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Semaphore } from "../Semaphore";

const items = [
  { title: "Deuda > 105 %PIB", valueText: "106,3", status: "crossed" as const, note: "narrativa crack23 [comentario]" },
  { title: "Bono 10A > 7 %", valueText: "6,5", status: "near" as const, note: "zona rescate 2012 [hist]" },
  { title: "Paro > 26,9 %", valueText: "10,1", status: "safe" as const, note: "máximo histórico ES (T1-2013) [hist]" },
  { title: "WGI control de la corrupción", valueText: "s/d", status: "sd" as const, note: "API archivada [hueco de datos]" },
];

describe("Semaphore — computed statuses, never authored", () => {
  it("maps status → pill class and Spanish label", () => {
    render(<Semaphore items={items} />);
    expect(screen.getByText("106,3")).toHaveClass("st", "cross");
    expect(screen.getByText("6,5")).toHaveClass("st", "near");
    expect(screen.getByText("10,1")).toHaveClass("st", "safe");
    expect(screen.getByText("s/d")).toHaveClass("st", "sd");
    expect(screen.getByText(/cerca ·/)).toBeInTheDocument(); // note row prefixes the label
  });
});
```

`frontend/src/components/__tests__/chain.test.tsx` — uses the REAL persona-01 chain spec and real engine numbers:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Chain } from "../Chain";
import { baseline, runScenario } from "../../engine/spain";
import { BASE_LEVERS } from "../../engine/vintage";

const specs = [
  { a: "tipo BCE", u: "Euríbor", t: "coste de refinanciación", k: "int" as const, d: 1, un: "%PIB" },
];

describe("Chain — trailing delta computed vs base", () => {
  it("flat at base", () => {
    render(<Chain specs={specs} scn={baseline()} base={baseline()} k={0} />);
    expect(screen.getByText(/\(\+0,0\)/)).toHaveClass("d", "flat");
  });
  it("r +200pb raises int → .up (red)", () => {
    const scn = runScenario({ ...BASE_LEVERS, r: 4.8 });
    render(<Chain specs={specs} scn={scn} base={baseline()} k={24} />);
    const d = document.querySelector(".ch .d")!;
    expect(d.className).toContain("up");
    expect(d.textContent).toMatch(/%PIB \(\+/);
  });
});
```

`frontend/src/components/__tests__/kpirow.test.tsx` — real persona-01 outs, real base values:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { KpiRow } from "../KpiRow";
import { baseline, runScenario } from "../../engine/spain";
import { BASE_LEVERS } from "../../engine/vintage";

const outs = [
  { k: "bono", lab: "Bono 10A España" }, { k: "spread", lab: "Spread ES–DE" },
  { k: "b", lab: "Deuda pública" }, { k: "saldo", lab: "Saldo público" },
  { k: "int", lab: "Intereses / PIB" },
];

describe("KpiRow — 5 gauge tiles from the API card outs", () => {
  it("renders 5 tiles with es-ES figures (base 2026: bono 3,42 · b 106,3)", () => {
    render(<KpiRow outs={outs} scn={baseline()} base={baseline()} k={0} fresh year={2026} />);
    expect(document.querySelectorAll(".out")).toHaveLength(5);
    expect(screen.getByText("3,42")).toBeInTheDocument();
    expect(screen.getByText("106,3")).toBeInTheDocument();
    expect(screen.getAllByText(/📅/)).toHaveLength(5);
  });
  it("stamp switches 📅→🔮 when a lever moves (spec §9)", () => {
    const scn = runScenario({ ...BASE_LEVERS, r: 4.8 });
    render(<KpiRow outs={outs} scn={scn} base={baseline()} k={0} fresh={false} year={2026} />);
    expect(screen.getAllByText(/🔮/)).toHaveLength(5);
    expect(screen.queryByText(/📅/)).toBeNull();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/components`
Expected: FAIL — modules not found.

- [ ] **Step 3: Implement motion hooks, the five primitives + KpiRow**

`frontend/src/lib/motion.ts`:

```ts
import { useEffect, useRef, useState, useSyncExternalStore } from "react";

function subscribe(cb: () => void): () => void {
  if (typeof window.matchMedia !== "function") return () => {};
  const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
  mq.addEventListener("change", cb);
  return () => mq.removeEventListener("change", cb);
}
function getSnapshot(): boolean {
  return typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}
/** True when the OS asks for reduced motion — gates ALL animation (spec §5). */
export function useReducedMotion(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, () => false);
}

/** Roll a displayed number to its new value over ~180 ms (spec §5). First render is exact;
 *  animation only happens on CHANGE, so tests reading the initial DOM see final values. */
export function useRollup(value: number, ms = 180): number {
  const [shown, setShown] = useState(value);
  const fromRef = useRef(value);
  const reduced = useReducedMotion();
  useEffect(() => {
    if (reduced || !Number.isFinite(value)) {
      fromRef.current = value;
      setShown(value);
      return;
    }
    const from = fromRef.current;
    if (from === value) return;
    let raf = 0;
    const t0 = performance.now();
    const step = (t: number) => {
      const p = Math.min(1, (t - t0) / ms);
      setShown(from + (value - from) * p);
      if (p < 1) raf = requestAnimationFrame(step);
      else fromRef.current = value;
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [value, ms, reduced]);
  return shown;
}
```

`frontend/src/components/Stamp.tsx`:

```tsx
export function Stamp({ fresh, year }: { fresh: boolean; year: number }) {
  return fresh ? (
    <span className="badge-fwd">📅 dato observado · vintage</span>
  ) : (
    <span className="badge-fwd lab">🔮 condicional · {year}</span>
  );
}
```

`frontend/src/components/Gauge.tsx`:

```tsx
const NEAR = 0.10; // same near fraction as the semaphore (spec §4.5 — v16 used 12%)

export function dialDomain(values: number[], red?: number): [number, number] {
  const all = red === undefined ? values : [...values, red];
  let lo = Math.min(...all);
  let hi = Math.max(...all);
  const pad = (hi - lo) * 0.16 || 1; // v16 chart() auto-domain rule
  return [lo - pad, hi + pad];
}

const pct = (v: number, lo: number, hi: number) =>
  `${Math.round(Math.min(100, Math.max(0, ((v - lo) / (hi - lo || 1)) * 100)) * 100) / 100}%`;

export function Gauge({ value, lo, hi, base, red, redCmp = "gt" }: {
  value: number; lo: number; hi: number; base: number; red?: number; redCmp?: "gt" | "lt";
}) {
  let fillClass = "f";
  if (red !== undefined) {
    const crossed = redCmp === "gt" ? value > red : value < red;
    if (crossed) fillClass = "f bad";
    else if (Math.abs(value - red) <= Math.abs(red || 1) * NEAR) fillClass = "f warn2";
  }
  return (
    <div className="gaugebar">
      <span className={fillClass} style={{ width: pct(value, lo, hi) }} />
      <span className="bm" style={{ left: pct(base, lo, hi) }} />
      {red !== undefined && <span className="rl" style={{ left: pct(red, lo, hi) }} />}
    </div>
  );
}
```

`frontend/src/components/Semaphore.tsx`:

```tsx
import { STATUS_LABEL, type RedLineStatus } from "../engine/redlines";

export interface SemaphoreItem {
  icon?: string; title: string; valueText: string; status: RedLineStatus; note: string;
}
const PILL_CLASS: Record<RedLineStatus, string> = {
  crossed: "st cross", near: "st near", safe: "st safe", sd: "st sd",
};

export function Semaphore({ items }: { items: SemaphoreItem[] }) {
  return (
    <div>
      {items.map((it) => (
        <div className="rl-item" key={it.title}>
          <span className="ic">{it.icon ?? "🚨"}</span>
          <span className="t"><b>{it.title}</b></span>
          <span className={PILL_CLASS[it.status]}>{it.valueText}</span>
          <span className="x">{STATUS_LABEL[it.status]} · {it.note}</span>
        </div>
      ))}
    </div>
  );
}
```

`frontend/src/components/Chain.tsx`:

```tsx
import { nf, sg } from "../lib/fmt";
import type { Scenario, SeriesKey } from "../engine/spain";

export interface ChainSpec { a: string; u: string; t: string; k: SeriesKey; d: number; un: string }
const EPS = 1e-9;

export function Chain({ specs, scn, base, k }: {
  specs: ChainSpec[]; scn: Scenario; base: Scenario; k: number;
}) {
  return (
    <div className="chain">
      {specs.map((c) => {
        const value = scn[c.k][k];
        const delta = value - base[c.k][k];
        const dir = delta > EPS ? "up" : delta < -EPS ? "dn" : "flat";
        return (
          <div className="ch" key={c.k + c.t}>
            <span className="a">{c.a}</span><span className="arr">→</span>
            <span className="u">{c.u}</span><span className="arr">→</span>
            {c.t}
            <span className={`d ${dir}`}>{nf(value, c.d)} {c.un} ({sg(delta, c.d)})</span>
          </div>
        );
      })}
    </div>
  );
}
```

`frontend/src/components/NarrativeBlock.tsx`:

```tsx
export function NarrativeBlock({ text, cite, header = "✦ Escenario condicional" }: {
  text: string; cite: string; header?: string;
}) {
  return (
    <div className="narr">
      <div className="h">{header}</div>
      <div className="x">{text}</div>
      <div className="cite"><code>{cite}</code></div>
    </div>
  );
}
```

`frontend/src/components/KpiRow.tsx`:

```tsx
import { nf, sg } from "../lib/fmt";
import { useRollup } from "../lib/motion";
import type { Scenario } from "../engine/spain";
import type { PersonaRedOut } from "../api/types";
import { Gauge, dialDomain } from "./Gauge";
import { Stamp } from "./Stamp";

/** Display format per engine series (decimals, unit suffix). */
export const SERIES_FORMAT: Record<string, { dec: number; unit: string }> = {
  lvl: { dec: 2, unit: "%" }, u: { dec: 1, unit: "%" }, pi: { dec: 1, unit: "%" },
  g: { dec: 1, unit: "%" }, gnom: { dec: 1, unit: "%" }, wnom: { dec: 1, unit: "%" },
  wreal: { dec: 1, unit: "%" }, wrealIdx: { dec: 1, unit: "" }, b: { dec: 1, unit: "%PIB" },
  ief: { dec: 2, unit: "%" }, int: { dec: 1, unit: "%PIB" }, pb: { dec: 1, unit: "%PIB" },
  saldo: { dec: 1, unit: "%PIB" }, ipv: { dec: 1, unit: "% a/a" }, precio: { dec: 0, unit: "€" },
  cuota: { dec: 0, unit: "€/mes" }, salmes: { dec: 0, unit: "€/mes" }, salario: { dec: 0, unit: "€/año" },
  esf: { dec: 1, unit: "%" }, pens: { dec: 2, unit: "%PIB" }, dep: { dec: 1, unit: "/100" },
  arop: { dec: 1, unit: "%" }, edu: { dec: 2, unit: "%PIB" }, d1: { dec: 2, unit: "%PIB" },
  nomreal: { dec: 1, unit: "" }, p2: { dec: 2, unit: "%PIB" }, d3: { dec: 2, unit: "%PIB" },
  p51: { dec: 2, unit: "%PIB" }, gtot: { dec: 1, unit: "%PIB" }, bls: { dec: 0, unit: "% neto" },
  temp: { dec: 1, unit: "%" }, ujuv: { dec: 1, unit: "%" }, auton: { dec: 1, unit: "%" },
  hip: { dec: 0, unit: "/año" }, sobre: { dec: 1, unit: "%" }, bono: { dec: 2, unit: "%" },
  spread: { dec: 0, unit: "pb" }, r: { dec: 2, unit: "%" }, deficitAbs: { dec: 1, unit: "%PIB" },
  vida: { dec: 1, unit: "años" }, ipvreal: { dec: 1, unit: "% a/a" },
};

/** Series where a positive delta is bad (red). Everything else: positive = good (green). */
export const UP_IS_BAD = new Set([
  "b", "u", "pi", "cuota", "esf", "int", "bono", "spread", "r", "arop", "dep",
  "pens", "sobre", "temp", "ujuv", "bls", "deficitAbs",
]);

interface TileProps {
  out: { k: string; lab: string };
  scn: Scenario; base: Scenario; k: number;
  fresh: boolean; year: number;
  red?: PersonaRedOut;
}

/** One tile = one component so useRollup (a hook) can animate its figure (spec §5). */
function KpiTile({ out, scn, base, k, fresh, year, red }: TileProps) {
  const key = out.k as keyof Scenario;
  const fmtSpec = SERIES_FORMAT[out.k] ?? { dec: 1, unit: "" };
  const value = scn[key][k];
  const baseValue = base[key][k];
  const shown = useRollup(value); // ~180 ms roll-up on change; exact on first render
  const delta = value - baseValue;
  const [lo, hi] = dialDomain([...base[key], ...scn[key]], red?.thr ?? undefined);
  const deltaClass =
    Math.abs(delta) <= 1e-9 ? "" : (delta > 0) === UP_IS_BAD.has(out.k) ? "bad" : "good";
  return (
    <div className="out">
      <span className="o-seal"><Stamp fresh={fresh} year={year} /></span>
      <div className="o-label">{out.lab}</div>
      <div className="o-val">{nf(shown, fmtSpec.dec)} <small>{fmtSpec.unit}</small></div>
      <div className={`o-delta ${deltaClass}`}>{sg(delta, fmtSpec.dec)} vs base</div>
      <Gauge value={value} lo={lo} hi={hi} base={baseValue}
        red={red?.thr ?? undefined} redCmp={(red?.cmp as "gt" | "lt") ?? "gt"} />
    </div>
  );
}

export function KpiRow({ outs, scn, base, k, fresh, year, personaReds }: {
  outs: { k: string; lab: string }[];
  scn: Scenario; base: Scenario; k: number;
  fresh: boolean; year: number;
  personaReds?: PersonaRedOut[];
}) {
  return (
    <div className="outs">
      {outs.map((o) => (
        <KpiTile key={o.k} out={o} scn={scn} base={base} k={k} fresh={fresh} year={year}
          red={personaReds?.find((r) => r.k === o.k)} />
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/components`
Expected: PASS (12 tests). If `gauge.test` position pins fail on rounding, keep the component (2-decimal rounding in `pct`) and fix pins only if you mis-derived them — `(120−100)/30 = 66.67%` is exact at 2 decimals.

- [ ] **Step 5: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/src/components frontend/src/lib/motion.ts
git commit -m "feat(frontend): v16 editorial primitives (stamp, gauge, semaphore, chain, narrative, KPI row)"
```

---

### Task 9: Charts — ProjectionChart and FanChart (Recharts)

**Files:**
- Create: `frontend/src/components/ProjectionChart.tsx`, `frontend/src/components/FanChart.tsx`
- Test: `frontend/src/components/__tests__/charts.test.tsx`

**Interfaces:**
- Consumes: `nf` (Task 1); `YEARS` (Task 3); percentile types (Task 6); `useReducedMotion` from `src/lib/motion.ts` (Task 8).
- Produces:
  - `ProjectionChart({ years, baseline, scenario, redLines = [], unit = "", dec = 1, height = 260 }: { years: number[]; baseline: number[]; scenario: number[]; redLines?: { value: number; label: string }[]; unit?: string; dec?: number; height?: number })` — dashed baseline (`--baseline`), solid scenario (`--lab`, width 2.4), `ReferenceLine` per red line (`--div-neg`, dash `4 3`), legend row per v16 §B.9.
  - `FanChart({ years, percentiles, height = 260 }: { years: number[]; percentiles: Record<"p5" | "p25" | "p50" | "p75" | "p95", number[]>; height?: number })` — p5–p95 band (`--band-out`, opacity .75), p25–p75 band (`--band-in`), p50 solid line (`--s1`).

Recharts is used **only** here (spec §5); jsdom cannot layout `ResponsiveContainer`, so both components take an explicit pixel `width`/`height` fallback when `process.env.NODE_ENV === "test"` — implemented by wrapping in `ResponsiveContainer` with `initialDimension={{ width: 660, height }}` (Recharts 3 supports `initialDimension`, which makes jsdom render real SVG paths).

- [ ] **Step 1: Write the failing test**

`frontend/src/components/__tests__/charts.test.tsx` — real data: baseline b vs S1 scenario b, fixture MC pins:

```tsx
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProjectionChart } from "../ProjectionChart";
import { FanChart } from "../FanChart";
import { YEARS, baseline, runScenario } from "../../engine/spain";
import { BASE_LEVERS } from "../../engine/vintage";
import { mockPercentiles } from "../../test/msw/fixtures";

describe("ProjectionChart — dotted base, solid scenario, red ReferenceLine", () => {
  it("renders two line paths and a reference line", () => {
    const scn = runScenario({ ...BASE_LEVERS, r: 4.8 });
    const { container } = render(
      <ProjectionChart years={YEARS} baseline={baseline().b} scenario={scn.b}
        redLines={[{ value: 120, label: "Deuda > 120 % PIB" }]} unit="%PIB" dec={1} />,
    );
    const curves = container.querySelectorAll("path.recharts-curve");
    expect(curves.length).toBeGreaterThanOrEqual(2);
    const dashed = Array.from(curves).filter((p) => p.getAttribute("stroke-dasharray"));
    expect(dashed.length).toBeGreaterThanOrEqual(1); // the frozen-vintage baseline
    expect(container.querySelectorAll(".recharts-reference-line").length).toBe(1);
    expect(container.textContent).toContain("base congelada (vintage)");
    expect(container.textContent).toContain("escenario actual");
  });
});

describe("FanChart — p5–p95, p25–p75, p50 (MC fan is server data)", () => {
  it("renders two bands and a median line from fixture-pinned percentiles", () => {
    const years = Array.from({ length: 45 }, (_, i) => 2026 + i);
    const { container } = render(<FanChart years={years} percentiles={mockPercentiles(years)} />);
    expect(container.querySelectorAll("path.recharts-area-area").length).toBe(2);
    expect(container.querySelectorAll("path.recharts-curve").length).toBeGreaterThanOrEqual(3);
    expect(container.textContent).toContain("banda p5–p95");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/components/__tests__/charts.test.tsx`
Expected: FAIL — modules not found.

- [ ] **Step 3: Implement both charts**

`frontend/src/components/ProjectionChart.tsx`:

```tsx
import {
  CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { nf } from "../lib/fmt";
import { useReducedMotion } from "../lib/motion";

export function ProjectionChart({ years, baseline, scenario, redLines = [], unit = "", dec = 1, height = 260 }: {
  years: number[]; baseline: number[]; scenario: number[];
  redLines?: { value: number; label: string }[]; unit?: string; dec?: number; height?: number;
}) {
  const reduced = useReducedMotion();
  const data = years.map((y, i) => ({ year: y, base: baseline[i], esc: scenario[i] }));
  return (
    <div>
      <div className="legend">
        <span><i style={{ background: "var(--lab)" }} />escenario actual</span>
        <span><s />base congelada (vintage)</span>
        {redLines.length > 0 && <span><s style={{ borderColor: "var(--div-neg)" }} />línea roja</span>}
      </div>
      <ResponsiveContainer width="100%" height={height} initialDimension={{ width: 660, height }}>
        <LineChart data={data} margin={{ top: 12, right: 12, bottom: 4, left: 0 }}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          <XAxis dataKey="year" ticks={[years[0], years[Math.floor((years.length - 1) / 2)], years[years.length - 1]]}
            tick={{ fontSize: 9.5, fill: "var(--ink-2)" }} tickLine={false} axisLine={{ stroke: "var(--grid)" }} />
          <YAxis width={56} tick={{ fontSize: 9.5, fill: "var(--ink-2)" }} tickLine={false}
            axisLine={false} tickFormatter={(v: number) => nf(v, dec)}
            domain={["auto", "auto"]} />
          <Tooltip formatter={(v: number) => `${nf(v, dec)} ${unit}`} labelFormatter={(y) => `año ${y}`} />
          {redLines.map((rl) => (
            <ReferenceLine key={rl.label} y={rl.value} stroke="var(--div-neg)" strokeDasharray="4 3"
              label={{ value: rl.label, fontSize: 9, fill: "var(--div-neg)", position: "insideTopRight" }} />
          ))}
          <Line type="linear" dataKey="base" stroke="var(--baseline)" strokeWidth={1.6}
            strokeDasharray="5 4" dot={false} isAnimationActive={false} name="base" />
          <Line type="linear" dataKey="esc" stroke="var(--lab)" strokeWidth={2.4} dot={false}
            isAnimationActive={!reduced} animationDuration={200} name="escenario" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

`frontend/src/components/FanChart.tsx`:

```tsx
import {
  Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { nf } from "../lib/fmt";
import { useReducedMotion } from "../lib/motion";
import type { PercentileKey } from "../api/types";

export function FanChart({ years, percentiles, height = 260 }: {
  years: number[]; percentiles: Record<PercentileKey, number[]>; height?: number;
}) {
  const reduced = useReducedMotion();
  const data = years.map((y, i) => ({
    year: y,
    band95: [percentiles.p5[i], percentiles.p95[i]],
    band50: [percentiles.p25[i], percentiles.p75[i]],
    p50: percentiles.p50[i],
  }));
  return (
    <div>
      <div className="legend">
        <span><i style={{ background: "var(--band-out)", height: 8 }} />banda p5–p95</span>
        <span><i style={{ background: "var(--band-in)", height: 8 }} />banda p25–p75</span>
        <span><i style={{ background: "var(--s1)" }} />mediana p50</span>
      </div>
      <ResponsiveContainer width="100%" height={height} initialDimension={{ width: 660, height }}>
        <ComposedChart data={data} margin={{ top: 12, right: 12, bottom: 4, left: 0 }}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          <XAxis dataKey="year" ticks={[years[0], 2050, years[years.length - 1]]}
            tick={{ fontSize: 9.5, fill: "var(--ink-2)" }} tickLine={false} axisLine={{ stroke: "var(--grid)" }} />
          <YAxis width={56} tick={{ fontSize: 9.5, fill: "var(--ink-2)" }} tickLine={false}
            axisLine={false} tickFormatter={(v: number) => nf(v, 0)} domain={["auto", "auto"]} />
          <Tooltip formatter={(v: number | number[]) =>
            Array.isArray(v) ? `${nf(v[0], 1)} – ${nf(v[1], 1)}` : nf(v, 1)}
            labelFormatter={(y) => `año ${y}`} />
          <Area dataKey="band95" fill="var(--band-out)" fillOpacity={0.75} stroke="none"
            isAnimationActive={!reduced} animationDuration={200} />
          <Area dataKey="band50" fill="var(--band-in)" fillOpacity={0.8} stroke="none"
            isAnimationActive={!reduced} animationDuration={200} />
          <Line dataKey="p50" stroke="var(--s1)" strokeWidth={2} dot={false}
            isAnimationActive={!reduced} animationDuration={200} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/components/__tests__/charts.test.tsx`
Expected: PASS (2 tests). If Recharts renders zero-size in jsdom, check `initialDimension` is passed (it exists in Recharts 3; if the installed minor lacks it, set explicit `width={660}` when `import.meta.env.MODE === "test"` instead — same visual contract in the browser).

- [ ] **Step 5: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/src/components/ProjectionChart.tsx frontend/src/components/FanChart.tsx \
  frontend/src/components/__tests__/charts.test.tsx
git commit -m "feat(frontend): Recharts projection and Monte Carlo fan charts"
```

---

### Task 10: Lever rail, preset bar, horizon buttons

**Files:**
- Create: `frontend/src/components/LeverRail.tsx`, `frontend/src/components/PresetBar.tsx`
- Test: `frontend/src/components/__tests__/leverrail.test.tsx`, `frontend/src/components/__tests__/presetbar.test.tsx`

**Interfaces:**
- Consumes: `LEVER_SPECS`, `isMoved`, `activePresetId` (Task 3); `useScenarioStore`, `HORIZON_YEARS` (Task 7); `usePresets` (Task 6); `nf` (Task 1); `VINTAGE` (Task 2).
- Produces: `LeverRail({ hotIds = [] }: { hotIds?: string[] })` — the full rail: heading, `PresetBar`, 10 `.lev` rows (native `<input type="range">`, `accent-color: var(--lab)`), horizon `.hb` buttons, reset button, "motor declarado" footnote. `PresetBar()` — 8 `.ps` chips from `/presets` (labels verbatim), `.on` computed live via `activePresetId` (v16 §B.3: equality, not sticky selection).

- [ ] **Step 1: Write the failing tests**

`frontend/src/components/__tests__/presetbar.test.tsx`:

```tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";
import { PresetBar } from "../PresetBar";
import { queryClient } from "../../api/hooks";
import { useScenarioStore } from "../../state/scenarioStore";

const ui = () => render(<QueryClientProvider client={queryClient}><PresetBar /></QueryClientProvider>);

describe("PresetBar — S0..S7 chips, .on by vector equality", () => {
  beforeEach(() => {
    useScenarioStore.getState().resetAll();
    queryClient.clear();
  });
  it("renders the 8 preset chips with API labels verbatim; S0 active at base", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("S7 adverso")).toBeInTheDocument());
    expect(screen.getAllByRole("button")).toHaveLength(8);
    expect(screen.getByText("S0 base")).toHaveClass("ps", "on");
  });
  it("clicking S1 applies r=4.8 and moves .on", async () => {
    ui();
    await waitFor(() => screen.getByText("S1 tipos +200 pb"));
    await userEvent.click(screen.getByText("S1 tipos +200 pb"));
    expect(useScenarioStore.getState().levers.r).toBeCloseTo(4.8, 9);
    expect(screen.getByText("S1 tipos +200 pb")).toHaveClass("on");
    expect(screen.getByText("S0 base")).not.toHaveClass("on");
  });
  it("hand-moving a lever off any preset clears .on everywhere", async () => {
    ui();
    await waitFor(() => screen.getByText("S0 base"));
    useScenarioStore.getState().setLever("r", 3.05);
    await waitFor(() => expect(screen.getByText("S0 base")).not.toHaveClass("on"));
  });
});
```

`frontend/src/components/__tests__/leverrail.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";
import { LeverRail } from "../LeverRail";
import { queryClient } from "../../api/hooks";
import { useScenarioStore } from "../../state/scenarioStore";

const ui = (hot: string[] = []) =>
  render(<QueryClientProvider client={queryClient}><LeverRail hotIds={hot} /></QueryClientProvider>);

describe("LeverRail — 10 sliders, hot/moved states, horizon buttons", () => {
  beforeEach(() => {
    useScenarioStore.getState().resetAll();
    queryClient.clear();
  });
  it("renders 10 sliders with v16 names and base readouts (r → 2,80 %)", () => {
    ui();
    expect(screen.getAllByRole("slider")).toHaveLength(10);
    expect(screen.getByText("Tipo de interés · Euríbor 12m")).toBeInTheDocument();
    expect(screen.getByText("2,80 %")).toBeInTheDocument(); // nf(2.8, dec=2)
    expect(screen.getByText("ecb_euribor12m.csv · 2026-06")).toBeInTheDocument();
  });
  it("dragging r updates the store and the readout turns .moved", async () => {
    ui();
    const slider = screen.getAllByRole("slider")[0];
    fireEvent.change(slider, { target: { value: "4.8" } });
    expect(useScenarioStore.getState().levers.r).toBe(4.8);
    await waitFor(() => expect(screen.getByText("4,80 %")).toHaveClass("vv", "moved"));
  });
  it("hot levers get the .hot row highlight (persona hot list)", () => {
    ui(["r", "prima"]);
    expect(document.getElementById("lev-r")).toHaveClass("lev", "hot");
    expect(document.getElementById("lev-sp")).not.toHaveClass("hot");
  });
  it("horizon buttons set the store (2035) and mark .on", async () => {
    ui();
    fireEvent.click(screen.getByText("2035"));
    expect(useScenarioStore.getState().horizon).toBe(2035);
    await waitFor(() => expect(screen.getByText("2035")).toHaveClass("hb", "on"));
  });
  it("reset button returns everything to base", () => {
    ui();
    useScenarioStore.getState().setLever("sp", 1.0);
    fireEvent.click(screen.getByText(/volver a base/i));
    expect(useScenarioStore.getState().levers.sp).toBe(0.0);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/components/__tests__/presetbar.test.tsx src/components/__tests__/leverrail.test.tsx`
Expected: FAIL — modules not found.

- [ ] **Step 3: Implement `PresetBar` and `LeverRail`**

`frontend/src/components/PresetBar.tsx`:

```tsx
import { usePresets } from "../api/hooks";
import { activePresetId } from "../engine/levers";
import { useScenarioStore } from "../state/scenarioStore";

export function PresetBar() {
  const { data, isError } = usePresets();
  const levers = useScenarioStore((s) => s.levers);
  const applyPreset = useScenarioStore((s) => s.applyPreset);
  if (isError) return <div className="banner err">Presets no disponibles</div>;
  if (!data) return null;
  const active = activePresetId(levers);
  return (
    <div className="presets">
      {data.presets.map((p) => (
        <button key={p.id} type="button" className={p.id === active ? "ps on" : "ps"}
          onClick={() => applyPreset(p.id)}>
          {p.nm}
        </button>
      ))}
    </div>
  );
}
```

`frontend/src/components/LeverRail.tsx`:

```tsx
import { nf } from "../lib/fmt";
import { LEVER_SPECS, isMoved } from "../engine/levers";
import { VINTAGE } from "../engine/vintage";
import { HORIZON_YEARS, useScenarioStore } from "../state/scenarioStore";
import { PresetBar } from "./PresetBar";

export function LeverRail({ hotIds = [] }: { hotIds?: string[] }) {
  const levers = useScenarioStore((s) => s.levers);
  const horizon = useScenarioStore((s) => s.horizon);
  const setLever = useScenarioStore((s) => s.setLever);
  const setHorizon = useScenarioStore((s) => s.setHorizon);
  const resetAll = useScenarioStore((s) => s.resetAll);
  return (
    <aside className="rail" aria-label="Palancas del escenario">
      <h4 style={{ margin: 0, fontSize: 12 }}>Palancas · variables independientes</h4>
      <PresetBar />
      <div className="levers">
        {LEVER_SPECS.map((s) => (
          <div className={hotIds.includes(s.id) ? "lev hot" : "lev"} id={`lev-${s.id}`} key={s.id}>
            <div className="l1">
              <span className="sym">{s.sym}</span>
              <span className="nm">{s.nm}</span>
              <span className={isMoved(levers, s.id) ? "vv moved" : "vv"}>
                {nf(levers[s.id], s.dec)} {s.unit}
              </span>
            </div>
            <input type="range" aria-label={s.nm} min={s.min} max={s.max} step={s.step}
              value={levers[s.id]}
              onChange={(e) => setLever(s.id, Number.parseFloat(e.target.value))} />
            <div className="src">{s.src}</div>
          </div>
        ))}
      </div>
      <div className="horiz" role="group" aria-label="Horizonte">
        {HORIZON_YEARS.map((y) => (
          <button key={y} type="button" className={y === horizon ? "hb on" : "hb"}
            onClick={() => setHorizon(y)}>
            {y}
          </button>
        ))}
      </div>
      <button type="button" className="ps" onClick={resetAll}>↺ volver a base</button>
      <div className="src" style={{ whiteSpace: "normal" }}>
        Motor v16 · constantes congeladas del vintage {VINTAGE} · el escenario te sigue entre páginas
      </div>
    </aside>
  );
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/components/__tests__/presetbar.test.tsx src/components/__tests__/leverrail.test.tsx`
Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/src/components/LeverRail.tsx frontend/src/components/PresetBar.tsx frontend/src/components/__tests__
git commit -m "feat(frontend): persistent lever rail with presets and horizon buttons"
```

---

### Task 11: App shell — routing, warnings, theme toggle, API-down screen, engine cross-check

**Files:**
- Modify: `frontend/src/App.tsx`, `frontend/src/main.tsx` (replace Task-1 placeholders)
- Create: `frontend/src/components/Warnings.tsx`, `frontend/src/components/ThemeToggle.tsx`, `frontend/src/components/ApiDownScreen.tsx`, `frontend/src/state/appHealth.ts`
- Create: placeholder routes `frontend/src/routes/Inicio.tsx`, `Persona.tsx`, `Laboratorio.tsx`, `Metodologia.tsx` (each `return <p>…página en la tarea N…</p>` — replaced in Tasks 12–14)
- Test: `frontend/src/components/__tests__/warnings.test.tsx`, `frontend/src/routes/__tests__/shell.test.tsx`

**Interfaces:**
- Consumes: `api`, `ApiError` (Task 6); `useHealth`, `queryClient` (Task 6); `baseline` (Task 3); `initFromUrl`, `startUrlSync` (Task 7); `initTheme`, `toggleTheme`, `getTheme` (Task 1); `usePersonas` (Task 6).
- Produces: `appHealth.ts` — `useAppHealth` (Zustand) `{ engineMismatch: boolean; extraWarnings: string[]; setEngineMismatch(v: boolean): void; addWarning(text: string): void }`; `crossCheckEngine(): Promise<void>` (POST `/scenario` base levers, compares `scenario.b` at indexes 0/9/24 = 2026/2035/2050 vs local `baseline().b`, tolerance 1e-6 → sets `engineMismatch`); `staleDays(vintage: string, now?: Date): number` and `STALE_LIMIT_DAYS = 90`. `Warnings()` — renders (a) engine-mismatch banner, (b) stale-vintage banner, (c) any `extraWarnings` (the `defaults_used` slot — Spain endpoints don't emit it in phase 2, the generic API does later; the hook is here so honesty warnings are one mechanism). `ThemeToggle()` — button `🌙/☀️`. `ApiDownScreen({ error }: { error: unknown })` — blocking screen naming `API_BASE` and the start command `uvicorn api.main:app --reload --port 8000`. `App()` — `BrowserRouter` + `QueryClientProvider`, topbar (brand, nav Inicio/Personas ×4 (pill labels from `/personas`)/Laboratorio/Metodología, `ThemeToggle`), `LeverRail` persistent across ALL routes (spec §6), `Warnings`, `Routes`, footer `«Proyección condicional, no recomendación de compra, venta o voto» · vintage {…}` gated on `computed_not_advice`.

- [ ] **Step 1: Write the failing tests**

`frontend/src/components/__tests__/warnings.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";
import { Warnings } from "../Warnings";
import { queryClient } from "../../api/hooks";
import { STALE_LIMIT_DAYS, staleDays, useAppHealth } from "../../state/appHealth";

// `now` is injectable so tests never need fake timers (they fight waitFor/React Query).
const ui = (now?: Date) =>
  render(<QueryClientProvider client={queryClient}><Warnings now={now} /></QueryClientProvider>);

describe("Warnings — honesty banners (spec §8)", () => {
  beforeEach(() => {
    useAppHealth.setState({ engineMismatch: false, extraWarnings: [] });
    queryClient.clear();
  });

  it("staleDays: 2026-08-07 is 7 days after vintage 2026-07-31", () => {
    expect(staleDays("2026-07-31", new Date("2026-08-07T12:00:00Z"))).toBe(7);
    expect(STALE_LIMIT_DAYS).toBe(90);
  });
  it("no banners when engine matches and vintage is fresh", () => {
    ui(new Date("2026-08-07T12:00:00Z"));
    expect(screen.queryByText(/desajuste del motor/i)).toBeNull();
    expect(screen.queryByText(/tiene \d+ días/)).toBeNull();
  });
  it("engine mismatch renders a visible error banner", () => {
    useAppHealth.setState({ engineMismatch: true });
    ui(new Date("2026-08-07T12:00:00Z"));
    expect(screen.getByText(/desajuste del motor: el cálculo local no coincide con la API/i)).toBeInTheDocument();
  });
  it("stale vintage (>90 días) renders a warning banner", async () => {
    ui(new Date("2026-12-01T12:00:00Z")); // 123 days after 2026-07-31
    expect(await screen.findByText(/tiene 123 días/)).toBeInTheDocument();
  });
});
```

`frontend/src/routes/__tests__/shell.test.tsx`:

```tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import App from "../../App";
import { server } from "../../test/msw/server";
import { queryClient } from "../../api/hooks";
import { useScenarioStore } from "../../state/scenarioStore";

describe("App shell", () => {
  beforeEach(() => {
    queryClient.clear();
    useScenarioStore.getState().resetAll();
    window.history.replaceState(null, "", "/");
    localStorage.clear();
  });

  it("boots: rail + nav + no-advice footer, no engine-mismatch banner (mock API == local engine)", async () => {
    render(<App />);
    // "💼 Bonista" appears in the nav AND in Inicio's persona card — use getAllByText
    await waitFor(() => expect(screen.getAllByText(/💼 Bonista/).length).toBeGreaterThanOrEqual(1));
    expect(screen.getAllByRole("slider")).toHaveLength(10);
    expect(screen.getByText(/proyección condicional, no recomendación/i)).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.queryByText(/desajuste del motor/i)).toBeNull());
  });

  it("theme toggle stamps data-theme and persists", async () => {
    render(<App />);
    await waitFor(() => screen.getByRole("button", { name: /tema/i }));
    await userEvent.click(screen.getByRole("button", { name: /tema/i }));
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(localStorage.getItem("theme")).toBe("dark");
  });

  it("API down → blocking screen with URL and start command, never a blank page", async () => {
    server.use(http.get("http://localhost:8000/health", () => HttpResponse.error()));
    render(<App />);
    expect(await screen.findByText(/no se puede conectar con la API/i)).toBeInTheDocument();
    expect(screen.getByText(/http:\/\/localhost:8000/)).toBeInTheDocument();
    expect(screen.getByText(/uvicorn api\.main:app --reload --port 8000/)).toBeInTheDocument();
  });

  it("engine mismatch banner fires when the API scenario diverges", async () => {
    server.use(
      http.post("http://localhost:8000/scenario", () =>
        HttpResponse.json({
          vintage: "2026-07-31", computed_not_advice: true, horizon: 2050,
          years: Array.from({ length: 25 }, (_, i) => 2026 + i),
          baseline: { b: Array(25).fill(0) }, scenario: { b: Array(25).fill(999) },
          deltas: {}, personas: {}, redlines: [],
        })),
    );
    render(<App />);
    expect(await screen.findByText(/desajuste del motor/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/components/__tests__/warnings.test.tsx src/routes/__tests__/shell.test.tsx`
Expected: FAIL — modules not found / placeholder App has no rail.

- [ ] **Step 3: Implement app health, warnings, toggle, blocking screen, shell**

`frontend/src/state/appHealth.ts`:

```ts
import { create } from "zustand";
import { api } from "../api/client";
import { baseline } from "../engine/spain";

export const STALE_LIMIT_DAYS = 90;

export function staleDays(vintage: string, now: Date = new Date()): number {
  const v = new Date(`${vintage}T00:00:00Z`);
  return Math.floor((now.getTime() - v.getTime()) / 86_400_000);
}

interface AppHealth {
  engineMismatch: boolean;
  extraWarnings: string[];
  setEngineMismatch: (v: boolean) => void;
  addWarning: (text: string) => void;
}
export const useAppHealth = create<AppHealth>()((set) => ({
  engineMismatch: false,
  extraWarnings: [],
  setEngineMismatch: (v) => set({ engineMismatch: v }),
  addWarning: (text) => set((s) => ({ extraWarnings: [...s.extraWarnings, text] })),
}));

/** Spec §3 cross-check: POST /scenario at base once, compare b at 2026/2035/2050 (idx 0/9/24). */
export async function crossCheckEngine(): Promise<void> {
  try {
    const res = await api.scenario({ levers: {}, horizon: 2050 });
    const local = baseline();
    const mismatch = [0, 9, 24].some(
      (i) => Math.abs((res.scenario.b?.[i] ?? Number.NaN) - local.b[i]) > 1e-6,
    );
    useAppHealth.getState().setEngineMismatch(mismatch);
  } catch {
    // API down is handled by the blocking screen; a failed cross-check is not a mismatch.
  }
}
```

`frontend/src/components/Warnings.tsx`:

```tsx
import { useHealth } from "../api/hooks";
import { STALE_LIMIT_DAYS, staleDays, useAppHealth } from "../state/appHealth";

export function Warnings({ now }: { now?: Date }) {
  const engineMismatch = useAppHealth((s) => s.engineMismatch);
  const extraWarnings = useAppHealth((s) => s.extraWarnings);
  const { data: health } = useHealth();
  const days = health ? staleDays(health.vintage, now) : 0;
  return (
    <div>
      {engineMismatch && (
        <div className="banner err" role="alert">
          ⚠️ Desajuste del motor: el cálculo local no coincide con la API (tolerancia 10⁻⁶).
          Los números en pantalla podrían no ser los del motor verificado.
        </div>
      )}
      {health && days > STALE_LIMIT_DAYS && (
        <div className="banner" role="status">
          El vintage {health.vintage} tiene {days} días — los datos observados pueden estar desactualizados.
        </div>
      )}
      {extraWarnings.map((w) => (
        <div className="banner" role="status" key={w}>{w}</div>
      ))}
    </div>
  );
}
```

`frontend/src/components/ThemeToggle.tsx`:

```tsx
import { useState } from "react";
import { getTheme, toggleTheme } from "../state/theme";

export function ThemeToggle() {
  const [theme, setThemeState] = useState(getTheme());
  return (
    <button type="button" className="ps" aria-label="Cambiar tema"
      onClick={() => setThemeState(toggleTheme())}>
      {theme === "dark" ? "☀️ tema claro" : "🌙 tema oscuro"}
    </button>
  );
}
```

`frontend/src/components/ApiDownScreen.tsx`:

```tsx
import { API_BASE } from "../api/client";

export function ApiDownScreen({ error }: { error: unknown }) {
  return (
    <div className="blocking">
      <div className="card">
        <h4>No se puede conectar con la API</h4>
        <p style={{ fontSize: 12, color: "var(--ink-2)" }}>
          Esta aplicación calcula sobre los datos del servicio de fase 1 y no inventa nada:
          sin API no hay números. Comprueba que el servicio está arrancado en{" "}
          <code>{API_BASE}</code> y recarga.
        </p>
        <p style={{ fontSize: 12 }}>
          Arranque (desde la raíz del repo):{" "}
          <code>uvicorn api.main:app --reload --port 8000</code>
        </p>
        {error instanceof Error && (
          <p className="src" style={{ whiteSpace: "normal" }}>Detalle: {error.message}</p>
        )}
      </div>
    </div>
  );
}
```

`frontend/src/App.tsx` (full shell):

```tsx
import { useEffect } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import { queryClient, useHealth, usePersonas } from "./api/hooks";
import { crossCheckEngine } from "./state/appHealth";
import { ApiDownScreen } from "./components/ApiDownScreen";
import { LeverRail } from "./components/LeverRail";
import { ThemeToggle } from "./components/ThemeToggle";
import { Warnings } from "./components/Warnings";
import { SHIPPED_IDS } from "./personas/registry";
import Inicio from "./routes/Inicio";
import Laboratorio from "./routes/Laboratorio";
import Metodologia from "./routes/Metodologia";
import Persona from "./routes/Persona";

function Shell() {
  const health = useHealth();
  const personas = usePersonas();
  useEffect(() => {
    if (health.isSuccess) void crossCheckEngine();
  }, [health.isSuccess]);

  if (health.isPending) return <div className="blocking"><div className="card"><h4>Cargando…</h4></div></div>;
  if (health.isError) return <ApiDownScreen error={health.error} />;

  const cards = (personas.data?.personas ?? []).filter((c) => SHIPPED_IDS.includes(c.id));
  return (
    <div className="shell">
      <header className="topbar">
        <strong>España en escenarios</strong>
        <nav>
          <NavLink to="/" end>Inicio</NavLink>
          {cards.map((c) => (
            <NavLink key={c.id} to={`/persona/${c.id}`}>{c.pill}</NavLink>
          ))}
          <NavLink to="/laboratorio">Laboratorio</NavLink>
          <NavLink to="/metodologia">Datos y método</NavLink>
        </nav>
        <span style={{ marginLeft: "auto" }} className="badge-fwd">vintage {health.data.vintage}</span>
        <ThemeToggle />
      </header>
      <div className="body">
        <LeverRail />
        <main className="main">
          <Warnings />
          <Routes>
            <Route path="/" element={<Inicio />} />
            <Route path="/persona/:id" element={<Persona />} />
            <Route path="/laboratorio" element={<Laboratorio />} />
            <Route path="/metodologia" element={<Metodologia />} />
          </Routes>
        </main>
      </div>
      <footer className="foot">
        {health.data.computed_not_advice && (
          <span>Proyección condicional, no recomendación de compra, venta o voto.</span>
        )}
        <span>Motor v{health.data.engine_version} · vintage {health.data.vintage}</span>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Shell />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

`frontend/src/main.tsx` (final form — URL state before first paint, optional MSW for the mocked preview):

```tsx
import { createRoot } from "react-dom/client";
import App from "./App";
import { initTheme } from "./state/theme";
import { initFromUrl, startUrlSync } from "./state/scenarioStore";
import "./styles/tokens.css";
import "./styles/base.css";

async function boot() {
  if (import.meta.env.VITE_MOCK_API === "1") {
    const { worker } = await import("./test/msw/browser");
    await worker.start({ onUnhandledRequest: "bypass" });
  }
  initTheme();
  initFromUrl();
  startUrlSync();
  createRoot(document.getElementById("root")!).render(<App />);
}
void boot();
```

Create `frontend/src/personas/registry.ts` now with just the id list (Task 13 fills the modules):

```ts
export const SHIPPED_IDS = ["01", "02", "03", "06"];
```

And the four placeholder routes, e.g. `frontend/src/routes/Inicio.tsx`:

```tsx
export default function Inicio() {
  return <p>Inicio — se implementa en la tarea 12.</p>;
}
```

(same pattern for `Persona.tsx` — `const { id } = useParams(); return <p>Persona {id} — tarea 13.</p>;`, `Laboratorio.tsx`, `Metodologia.tsx` — tarea 14.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/components/__tests__/warnings.test.tsx src/routes/__tests__/shell.test.tsx`
Expected: PASS (8 tests). The no-mismatch assertion passes **because** the MSW `/scenario` handler runs the same TS engine — by construction identical.

- [ ] **Step 5: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/src/App.tsx frontend/src/main.tsx frontend/src/components frontend/src/state/appHealth.ts \
  frontend/src/routes frontend/src/personas/registry.ts
git commit -m "feat(frontend): app shell with routing, honesty banners, theme toggle and engine cross-check"
```

---

### Task 12: Inicio route

**Files:**
- Modify: `frontend/src/routes/Inicio.tsx` (replace placeholder)
- Test: `frontend/src/routes/__tests__/inicio.test.tsx`

**Interfaces:**
- Consumes: `useScenario`, `useScenarioStore`, `kIndex` (Task 7); `baseline`, `YEARS` (Task 3); `useRedlines`, `useVintage`, `usePersonas` (Task 6); `evaluateRedlines`, `STATUS_LABEL` (Task 4); `Semaphore` (Task 8); `nf`, `sg` (Task 1); `Stamp` (Task 8); `allAtBase` (Task 3); `SHIPPED_IDS` (Task 11); `SERIES_FORMAT`, `UP_IS_BAD` (Task 8).
- Produces: `Inicio` default export. Content (spec §6): vintage + coverage banner (`/vintage`: `n_files` fuentes), headline figures — **deuda 2050** (`b[24]`), **déficit** (`saldo` at horizon), **paro** (`u` at horizon), **IPCA** (`pi` at horizon) — each with `sg` delta vs base; global red-line semaphore (all 9 `/redlines` evaluated locally at the horizon index); persona link cards (pill + h1, `<Link to="/persona/:id">`) for the 4 shipped ids.

- [ ] **Step 1: Write the failing test**

`frontend/src/routes/__tests__/inicio.test.tsx`:

```tsx
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";
import Inicio from "../Inicio";
import { queryClient } from "../../api/hooks";
import { useScenarioStore } from "../../state/scenarioStore";

const ui = () =>
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter><Inicio /></MemoryRouter>
    </QueryClientProvider>,
  );

describe("Inicio — headline figures + global semaphore + persona cards", () => {
  beforeEach(() => {
    queryClient.clear();
    useScenarioStore.getState().resetAll();
  });

  it("shows vintage/coverage banner and the four headline figures at base", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/141 fuentes/)).toBeInTheDocument());
    expect(screen.getByText(/vintage 2026-07-31/)).toBeInTheDocument();
    // baseline pins: deuda 2050 = 223,8 %PIB · paro 10,1 % · IPCA 3,0 %.
    // Scoped to the tiles: "10,1"/"3,0" also appear in the semaphore rows below.
    const tiles = document.querySelectorAll(".out");
    expect(tiles).toHaveLength(4);
    expect(tiles[0].textContent).toContain("223,8"); // Deuda 2050
    expect(tiles[2].textContent).toContain("10,1");  // Paro
    expect(tiles[3].textContent).toContain("3,0");   // IPCA
  });

  it("renders the 9 global red lines with computed statuses (deuda_105 crossed at base 2026)", async () => {
    ui();
    await waitFor(() => expect(document.querySelectorAll(".rl-item")).toHaveLength(9));
    const deuda105 = screen.getByText("Deuda > 105 % PIB").closest(".rl-item")!;
    expect(deuda105.querySelector(".st")!.className).toContain("cross");
  });

  it("links to the four shipped personas", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/💼 Bonista/)).toBeInTheDocument());
    const links = screen.getAllByRole("link").filter((a) => a.getAttribute("href")?.startsWith("/persona/"));
    expect(links.map((a) => a.getAttribute("href"))).toEqual([
      "/persona/01", "/persona/02", "/persona/03", "/persona/06",
    ]);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/routes/__tests__/inicio.test.tsx`
Expected: FAIL — placeholder renders "tarea 12".

- [ ] **Step 3: Implement Inicio**

`frontend/src/routes/Inicio.tsx`:

```tsx
import { Link } from "react-router-dom";
import { usePersonas, useRedlines, useVintage } from "../api/hooks";
import { baseline } from "../engine/spain";
import { evaluateRedlines } from "../engine/redlines";
import { allAtBase } from "../engine/levers";
import { nf, sg } from "../lib/fmt";
import { Semaphore } from "../components/Semaphore";
import { Stamp } from "../components/Stamp";
import { SERIES_FORMAT, UP_IS_BAD } from "../components/KpiRow";
import { kIndex, useScenario, useScenarioStore } from "../state/scenarioStore";
import { SHIPPED_IDS } from "../personas/registry";

const HEADLINES: { k: "b" | "saldo" | "u" | "pi"; lab: string; at2050?: boolean }[] = [
  { k: "b", lab: "Deuda 2050", at2050: true },
  { k: "saldo", lab: "Saldo público" },
  { k: "u", lab: "Paro" },
  { k: "pi", lab: "IPCA" },
];

export default function Inicio() {
  const vintage = useVintage();
  const redlines = useRedlines();
  const personas = usePersonas();
  const scn = useScenario();
  const levers = useScenarioStore((s) => s.levers);
  const horizon = useScenarioStore((s) => s.horizon);
  const k = kIndex(horizon);
  const base = baseline();
  const fresh = allAtBase(levers) && horizon === 2026;

  return (
    <div>
      <div className="head">
        <h1>España en escenarios</h1>
        <Stamp fresh={fresh} year={horizon} />
        {vintage.isSuccess ? (
          <span className="meta">vintage {vintage.data.vintage} · {vintage.data.n_files} fuentes congeladas</span>
        ) : vintage.isError ? (
          <span className="meta">cobertura no disponible</span>
        ) : null}
      </div>

      <div className="outs" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
        {HEADLINES.map(({ k: key, lab, at2050 }) => {
          const i = at2050 ? 24 : k;
          const f = SERIES_FORMAT[key];
          const delta = scn[key][i] - base[key][i];
          const cls = Math.abs(delta) <= 1e-9 ? "" : (delta > 0) === UP_IS_BAD.has(key) ? "bad" : "good";
          return (
            <div className="out" key={key}>
              <div className="o-label">{lab}</div>
              <div className="o-val">{nf(scn[key][i], f.dec)} <small>{f.unit}</small></div>
              <div className={`o-delta ${cls}`}>{sg(delta, f.dec)} vs base</div>
            </div>
          );
        })}
      </div>

      <div className="card">
        <h4>Líneas rojas <small>evaluadas en {horizon} · umbrales v12 con fuente</small></h4>
        {redlines.isSuccess ? (
          <Semaphore
            items={evaluateRedlines(redlines.data.redlines, scn, k).map((r) => ({
              title: r.label,
              valueText: nf(r.value, SERIES_FORMAT[r.series]?.dec ?? 1),
              status: r.status,
              note: r.source,
            }))}
          />
        ) : redlines.isError ? (
          <div className="banner err">Líneas rojas no disponibles</div>
        ) : null}
      </div>

      <div className="row2">
        {(personas.data?.personas ?? [])
          .filter((c) => SHIPPED_IDS.includes(c.id))
          .map((c) => (
            <Link key={c.id} to={`/persona/${c.id}`} className="card" style={{ textDecoration: "none", color: "inherit" }}>
              <h4>{c.pill}</h4>
              <span style={{ fontSize: 12, color: "var(--ink-2)" }}>{c.h1}</span>
            </Link>
          ))}
        {personas.isError && <div className="banner err">Personas no disponibles</div>}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/routes/__tests__/inicio.test.tsx`
Expected: PASS (3 tests). Note the semaphore label pin uses the API's `"Deuda > 105 % PIB"` (with spaces, from `/redlines`) — not persona-red copy.

- [ ] **Step 5: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/src/routes/Inicio.tsx frontend/src/routes/__tests__/inicio.test.tsx
git commit -m "feat(frontend): Inicio route with headline figures, global semaphore and persona cards"
```

---

### Task 13: Generic Persona route + the 4 persona modules

**Files:**
- Modify: `frontend/src/routes/Persona.tsx` (replace placeholder), `frontend/src/personas/registry.ts`
- Create: `frontend/src/personas/p01_bonista.ts`, `p02_banca.ts`, `p03_comprador.ts`, `p06_politico.ts`
- Test: `frontend/src/routes/__tests__/persona.test.tsx`

**Interfaces:**
- Consumes: `usePersonas` (Task 6); `useScenario`, `useScenarioStore`, `kIndex` (Task 7); `baseline`, `Y0`, `YEARS`, `Scenario` (Task 3); `allAtBase` (Task 3); `evaluatePersonaReds` (Task 4); `KpiRow`, `Semaphore`, `Chain`, `ChainSpec`, `NarrativeBlock`, `Stamp` (Task 8); `ProjectionChart` (Task 9); `nf`, `sg`, `eur` (Task 1); `seriesOf` (Task 4); `SERIES_FORMAT` (Task 8); `LeverRail` hot wiring via `Outlet` context is NOT used — `Persona` renders inside the shell; the rail reads hot ids from a small store field added here.
- Produces: `registry.ts` — `SHIPPED_IDS`, `interface PersonaModule { id: string; chains: ChainSpec[]; narr: (R: Scenario, k: number, y: number) => string; cite: string }`, `getPersonaModule(id: string): PersonaModule | undefined`. `Persona` default export rendering the v14 rhythm **generically from the API card**: head (h1 + stamp + meta) → `KpiRow` (5 gauges from `outs`) → `.row2` two charts (chA: historical `series_keys[0]` points from `/personas.series`; chB: projection of the card's `headline` series, baseline dashed + scenario solid + red `ReferenceLine`s from the card's `reds` bound to the headline series) → `.row3` semáforo (`reds` via `evaluatePersonaReds`) + cadenas + narrativa. Adding persona 04 later = one module + one registry line, zero renderer changes (spec §10).
- Also: `useScenarioStore` gains `hotIds: string[]` + `setHotIds(ids: string[])` (Persona sets them from `card.hot` on mount so the rail highlights; Inicio/Laboratorio clear them). `App.tsx` passes `hotIds` from the store to `LeverRail` (one-line change: `const hotIds = useScenarioStore((s) => s.hotIds); … <LeverRail hotIds={hotIds} />`).

Persona modules carry ONLY what the API card does not: the v16 `chains` arrays and `narr` templates, Spanish, **verbatim from the v16 extract** (S2). No KPI labels, no reds, no h1 — those come from the API.

- [ ] **Step 1: Write the failing test**

`frontend/src/routes/__tests__/persona.test.tsx` (spec §9: each shipped persona renders from the mocked payload with no missing-key crashes):

```tsx
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";
import Persona from "../Persona";
import { queryClient } from "../../api/hooks";
import { useScenarioStore } from "../../state/scenarioStore";

const ui = (id: string) =>
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/persona/${id}`]}>
        <Routes><Route path="/persona/:id" element={<Persona />} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );

describe("Persona — generic renderer over the API card", () => {
  beforeEach(() => {
    queryClient.clear();
    useScenarioStore.getState().resetAll();
  });

  it.each(["01", "02", "03", "06"])("persona %s renders h1, 5 gauges, 3 reds, chains, narrative", async (id) => {
    ui(id);
    await waitFor(() => expect(document.querySelectorAll(".out")).toHaveLength(5));
    expect(document.querySelectorAll(".rl-item")).toHaveLength(3);
    expect(document.querySelectorAll(".ch").length).toBeGreaterThanOrEqual(3);
    expect(document.querySelector(".narr .x")!.textContent!.length).toBeGreaterThan(40);
    expect(document.querySelector(".head h1")).not.toBeNull();
  });

  it("persona 01 shows its API copy verbatim", async () => {
    ui("01");
    await waitFor(() =>
      expect(screen.getByText("💼 Inversor en bonos: ¿me pagarán los 10 años?")).toBeInTheDocument());
    expect(screen.getByText("Bono 10A España")).toBeInTheDocument();
    expect(screen.getByText(/ecb_bono10y_es\.csv/)).toBeInTheDocument();
  });

  it("persona 02's ipvreal red evaluates without crashing (handoff note 3: 12,8 − 3,0 = 9,8 → cerca)", async () => {
    ui("02");
    await waitFor(() => expect(screen.getByText(/IPV real a\/a > 10 %/)).toBeInTheDocument());
    const row = screen.getByText(/IPV real a\/a > 10 %/).closest(".rl-item")!;
    expect(row.querySelector(".st")!.className).toContain("near");
    expect(row.querySelector(".st")!.textContent).toBe("9,8");
  });

  it("sets the rail hot ids from the card (persona 01: r, prima, sp, dem)", async () => {
    ui("01");
    await waitFor(() =>
      expect(useScenarioStore.getState().hotIds).toEqual(["r", "prima", "sp", "dem"]));
  });

  it("unknown id shows a Spanish not-found note, no crash", async () => {
    ui("99");
    expect(await screen.findByText(/perfil no disponible/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/routes/__tests__/persona.test.tsx`
Expected: FAIL — placeholder route; `hotIds` missing from store.

- [ ] **Step 3: Implement store `hotIds`, registry, 4 modules, generic route**

Add to `ScenarioState` in `frontend/src/state/scenarioStore.ts` (and to the `create` body; `resetAll` does NOT clear `hotIds` — they belong to the visible route, not the scenario):

```ts
  hotIds: string[];
  setHotIds: (ids: string[]) => void;
  // in create():
  hotIds: [],
  setHotIds: (ids) => set({ hotIds: ids }),
```

And in `App.tsx`: `const hotIds = useScenarioStore((s) => s.hotIds);` … `<LeverRail hotIds={hotIds} />`.

`frontend/src/personas/registry.ts`:

```ts
import type { Scenario } from "../engine/spain";
import type { ChainSpec } from "../components/Chain";
import { p01 } from "./p01_bonista";
import { p02 } from "./p02_banca";
import { p03 } from "./p03_comprador";
import { p06 } from "./p06_politico";

export interface PersonaModule {
  id: string;
  chains: ChainSpec[];
  narr: (R: Scenario, k: number, y: number) => string;
  cite: string;
}

export const SHIPPED_IDS = ["01", "02", "03", "06"];
const MODULES: Record<string, PersonaModule> = { "01": p01, "02": p02, "03": p03, "06": p06 };
export const getPersonaModule = (id: string): PersonaModule | undefined => MODULES[id];
```

`frontend/src/personas/p01_bonista.ts` (chains + narrative verbatim from the v16 extract S2, persona 01):

```ts
import { nf } from "../lib/fmt";
import type { PersonaModule } from "./registry";

export const p01: PersonaModule = {
  id: "01",
  chains: [
    { a: "tipo BCE", u: "Euríbor", t: "coste de refinanciación", k: "int", d: 1, un: "%PIB" },
    { a: "saldo primario", u: "emisión neta", t: "senda de deuda", k: "b", d: 1, un: "%PIB" },
    { a: "prima de riesgo", u: "spread", t: "cupón exigido", k: "bono", d: 2, un: "%" },
  ],
  narr: (R, k, y) =>
    `Con las palancas de hoy el cupón a 10 años sale a ${nf(R.bono[k], 2)} % y el spread a ${nf(R.spread[k], 0)} pb. ` +
    `En ${y} la identidad de deuda deja el saldo en ${nf(R.b[k], 1)} %PIB con ${nf(R.int[k], 1)} puntos de PIB en intereses — gasto que nadie elige. ` +
    `La banda p5–p95 del Monte Carlo heredado sigue debajo: lo que un acreedor mira no es la mediana, es la anchura.`,
  cite: "gold_escenarios_deuda.csv",
};
```

`frontend/src/personas/p02_banca.ts`:

```ts
import { eur, nf, sg } from "../lib/fmt";
import type { PersonaModule } from "./registry";

export const p02: PersonaModule = {
  id: "02",
  chains: [
    { a: "Euríbor", u: "cuota nueva", t: "esfuerzo del hogar", k: "esf", d: 1, un: "%" },
    { a: "IPV", u: "LTV efectivo", t: "severidad si impago", k: "ipv", d: 1, un: "% a/a" },
    { a: "paro", u: "mora", t: "pérdida esperada", k: "u", d: 1, un: "%" },
  ],
  narr: (R, k, y) =>
    `El margen lo marca un Euríbor al ${nf(R.r[k], 2)} % y el riesgo lo marcan el empleo (paro ${nf(R.u[k], 1)} %) ` +
    `y un colateral que se mueve al ${sg(R.ipv[k], 1)} % anual. En ${y} la cuota mediana teórica sale a ${eur(R.cuota[k])} €/mes ` +
    `y el esfuerzo sobre la nómina media a ${nf(R.esf[k], 1)} %. Hueco declarado: la serie de mora bancaria (NPL, Banco de España) sigue sin conectar — data/README.md.`,
  cite: "gold_cuota_teorica.csv",
};
```

`frontend/src/personas/p03_comprador.ts`:

```ts
import { eur, nf } from "../lib/fmt";
import type { PersonaModule } from "./registry";

export const p03: PersonaModule = {
  id: "03",
  chains: [
    { a: "Euríbor", u: "cuota", t: "esfuerzo sobre la nómina", k: "esf", d: 1, un: "%" },
    { a: "IPV", u: "entrada 20 %", t: "años de ahorro previo", k: "precio", d: 0, un: "€" },
    { a: "salarios", u: "WS: π+λ+φ·holgura", t: "renta disponible", k: "salmes", d: 0, un: "€/mes" },
  ],
  narr: (R, k, y) =>
    `En ${y} el precio mediano sale a ${eur(R.precio[k])} € — entrada del 20 %: ${eur(R.precio[k] * 0.2)} € — ` +
    `y la cuota a ${eur(R.cuota[k])} €/mes contra un salario bruto de ${eur(R.salmes[k])} €/mes. ` +
    `El esfuerzo queda en ${nf(R.esf[k], 1)} % frente a la regla prudencial del 35 %. ` +
    `Las dos ramas cuelgan de la misma palanca: el tipo mueve la cuota por arriba y el precio por abajo.`,
  cite: "gold_cuota_teorica.csv",
};
```

`frontend/src/personas/p06_politico.ts`:

```ts
import { nf, sg } from "../lib/fmt";
import type { PersonaModule } from "./registry";

export const p06: PersonaModule = {
  id: "06",
  chains: [
    { a: "saldo primario", u: "bola de nieve r−g", t: "senda de deuda", k: "b", d: 1, un: "%PIB" },
    { a: "palanca de gasto", u: "multiplicador 1,4", t: "paro", k: "u", d: 1, un: "%" },
    { a: "tipos", u: "refinanciación", t: "espacio fiscal", k: "int", d: 1, un: "%PIB" },
  ],
  narr: (R, k, y) =>
    `Ninguna palanca sale gratis y el tablero lo enseña: con este escenario la deuda de ${y} queda en ${nf(R.b[k], 1)} %PIB, ` +
    `el saldo en ${nf(R.saldo[k], 1)} y los intereses en ${nf(R.int[k], 1)} puntos de PIB, mientras el paro se sitúa en ${nf(R.u[k], 1)} % ` +
    `y el PIB crece al ${sg(R.g[k], 1)} %. Consolidar desplaza la mediana pero no borra la banda; sostener el gasto apuntala el PIB de hoy y empina la senda. ` +
    `La elección «correcta» no aparece en ninguna columna del CSV.`,
  cite: "gold_escenarios_deuda.csv",
};
```

`frontend/src/routes/Persona.tsx`:

```tsx
import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { usePersonas, useRedlines } from "../api/hooks";
import { baseline, YEARS } from "../engine/spain";
import { allAtBase } from "../engine/levers";
import { evaluatePersonaReds } from "../engine/redlines";
import { seriesOf, type AnySeriesKey } from "../engine/derived";
import { nf } from "../lib/fmt";
import { Chain } from "../components/Chain";
import { KpiRow, SERIES_FORMAT } from "../components/KpiRow";
import { NarrativeBlock } from "../components/NarrativeBlock";
import { ProjectionChart } from "../components/ProjectionChart";
import { Semaphore } from "../components/Semaphore";
import { Stamp } from "../components/Stamp";
import { getPersonaModule } from "../personas/registry";
import { kIndex, useScenario, useScenarioStore } from "../state/scenarioStore";

export default function Persona() {
  const { id } = useParams<{ id: string }>();
  const personas = usePersonas();
  const redlines = useRedlines();
  const scn = useScenario();
  const levers = useScenarioStore((s) => s.levers);
  const horizon = useScenarioStore((s) => s.horizon);
  const setHotIds = useScenarioStore((s) => s.setHotIds);
  const card = personas.data?.personas.find((c) => c.id === id);
  const mod = id ? getPersonaModule(id) : undefined;

  useEffect(() => {
    setHotIds(card?.hot ?? []);
    return () => setHotIds([]);
  }, [card, setHotIds]);

  if (personas.isPending) return <p>Cargando perfil…</p>;
  if (personas.isError) return <div className="banner err">Personas no disponibles — el resto de la app sigue funcionando.</div>;
  if (!card || !mod) return <p>Perfil no disponible — perfiles publicados: 01, 02, 03, 06.</p>;

  const base = baseline();
  const k = kIndex(horizon);
  const fresh = allAtBase(levers) && horizon === 2026;
  const year = horizon;
  const hist = personas.data.series[card.series_keys[0]];
  const headlineKey = card.headline as AnySeriesKey;
  const headlineDec = SERIES_FORMAT[card.headline]?.dec ?? 1;
  const personaRedLines = card.reds
    .filter((r) => r.k === card.headline && r.thr !== null)
    .map((r) => ({ value: r.thr as number, label: r.t }));
  const globalRedLines = (redlines.data?.redlines ?? [])
    .filter((rl) => rl.series === card.headline)
    .map((rl) => ({ value: rl.threshold, label: rl.label }));

  return (
    <div>
      <div className="head">
        <h1>{card.h1}</h1>
        <Stamp fresh={fresh} year={year} />
        <span className="meta">{card.meta}</span>
      </div>

      <KpiRow outs={card.outs} scn={scn} base={base} k={k} fresh={fresh} year={year} personaReds={card.reds} />

      <div className="row2">
        <div className="card">
          <h4>Histórico <small>{hist?.fuente ?? "serie no disponible"}</small></h4>
          {hist ? (
            <ProjectionChart
              years={hist.puntos.map((_, i) => i)}
              baseline={hist.puntos.map(([, v]) => v)}
              scenario={hist.puntos.map(([, v]) => v)}
              dec={2}
            />
          ) : (
            <div className="banner err">Serie histórica no disponible</div>
          )}
        </div>
        <div className="card">
          <h4>Proyección 2026–2050 <small>{card.outs.find((o) => o.k === card.headline)?.lab ?? card.headline} · base punteada vs escenario</small></h4>
          <ProjectionChart
            years={YEARS}
            baseline={seriesOf(base, headlineKey)}
            scenario={seriesOf(scn, headlineKey)}
            redLines={[...personaRedLines, ...globalRedLines.filter((g) => !personaRedLines.some((p) => p.value === g.value))]}
            unit={SERIES_FORMAT[card.headline]?.unit ?? ""}
            dec={headlineDec}
          />
        </div>
      </div>

      <div className="row3">
        <div className="card">
          <h4>Semáforo del perfil <small>umbrales de presentación — no son las líneas rojas globales</small></h4>
          <Semaphore
            items={evaluatePersonaReds(card.reds, scn, k).map((r) => ({
              title: r.t,
              valueText: r.value === null ? "s/d" : nf(r.value, r.d ?? 1),
              status: r.status,
              note: r.x,
            }))}
          />
        </div>
        <div className="card">
          <h4>Transmisión <small>de la palanca al bolsillo</small></h4>
          <Chain specs={mod.chains} scn={scn} base={base} k={k} />
        </div>
        <div className="card">
          <NarrativeBlock text={mod.narr(scn, k, year)} cite={`trazado a ${mod.cite}`} />
        </div>
      </div>
    </div>
  );
}
```

Note on the historical chart: chA reuses `ProjectionChart` with identical base/scenario arrays (a single observed line, no divergence) — the v16 chA is an observed-data line chart; a dedicated component would duplicate the chart shell for one styling difference. The `.legend` still reads "escenario actual"; acceptable for phase 2 and noted in Known deviations.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/routes/__tests__/persona.test.tsx`
Expected: PASS (8 tests: 4 parametrized + 4 singles).

- [ ] **Step 5: Run the full suite (store change touched earlier tests)**

Run: `cd frontend && npx vitest run`
Expected: all green — the `hotIds` addition must not break Task 7/10/11 tests.

- [ ] **Step 6: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/src/personas frontend/src/routes/Persona.tsx frontend/src/routes/__tests__/persona.test.tsx \
  frontend/src/state/scenarioStore.ts frontend/src/App.tsx
git commit -m "feat(frontend): generic persona renderer with v16 chains/narratives for 01, 02, 03, 06"
```

---

### Task 14: Laboratorio and Metodología routes

**Files:**
- Modify: `frontend/src/routes/Laboratorio.tsx`, `frontend/src/routes/Metodologia.tsx` (replace placeholders)
- Test: `frontend/src/routes/__tests__/laboratorio.test.tsx`, `frontend/src/routes/__tests__/metodologia.test.tsx`

**Interfaces:**
- Consumes: `ALL_SERIES_KEYS`, `seriesOf` (Task 4); `useScenario`, `useScenarioStore`, `kIndex` (Task 7); `baseline`, `YEARS` (Task 3); `useMonteCarlo`, `useConstants`, `useRedlines`, `useHealth`, `useVintage` (Task 6); `ProjectionChart`, `FanChart` (Task 9); `SERIES_FORMAT` (Task 8); `LEVER_SPECS` (Task 3); `nf` (Task 1); `CONSTANTS_META` shape (Task 2); `STALE_LIMIT_DAYS`, `staleDays` (Task 11).
- Produces: `Laboratorio` — series explorer (a `<select>` over all 41 keys, default `b`), `ProjectionChart` of the chosen series with any global red lines bound to it, `FanChart` fed by `useMonteCarlo(levers, true)` (debounced 400 ms, horizon 2070) with the ±2 pp gold-envelope note, and a raw lever table (current vs base values). `Metodologia` — 31-constants provenance table, vintage staleness note, red-line thresholds + sources, engine-parity statement, persona-reds-vs-global-redlines explanation, MC validation rule, known-gaps list.

- [ ] **Step 1: Write the failing tests**

`frontend/src/routes/__tests__/laboratorio.test.tsx`:

```tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";
import Laboratorio from "../Laboratorio";
import { queryClient } from "../../api/hooks";
import { useScenarioStore } from "../../state/scenarioStore";

const ui = () => render(<QueryClientProvider client={queryClient}><Laboratorio /></QueryClientProvider>);

describe("Laboratorio — series explorer + MC fan + raw levers", () => {
  beforeEach(() => {
    queryClient.clear();
    useScenarioStore.getState().resetAll();
  });

  it("series selector offers all 41 keys and defaults to b", () => {
    ui();
    const select = screen.getByRole("combobox", { name: /serie/i });
    expect(select).toHaveValue("b");
    expect(select.querySelectorAll("option")).toHaveLength(41);
  });

  it("changing the series redraws the projection chart", async () => {
    ui();
    await userEvent.selectOptions(screen.getByRole("combobox", { name: /serie/i }), "esf");
    await waitFor(() => expect(screen.getByText(/esf ·/)).toBeInTheDocument());
    expect(document.querySelectorAll("path.recharts-curve").length).toBeGreaterThanOrEqual(2);
  });

  it("MC fan renders from the (debounced) server response with the ±2pp note", async () => {
    ui();
    await waitFor(
      () => expect(document.querySelectorAll("path.recharts-area-area")).toHaveLength(2),
      { timeout: 3000 }, // 400 ms debounce + MSW round-trip
    );
    expect(screen.getByText(/±2 pp/)).toBeInTheDocument();
    expect(screen.getByText(/4000 trayectorias/)).toBeInTheDocument();
  });

  it("raw lever table shows current vs base (r: 2,80 both at boot)", () => {
    ui();
    const rows = screen.getAllByRole("row");
    expect(rows.length).toBe(11); // header + 10 levers
    expect(rows[1].textContent).toContain("2,80");
  });
});
```

`frontend/src/routes/__tests__/metodologia.test.tsx`:

```tsx
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";
import Metodologia from "../Metodologia";
import { queryClient } from "../../api/hooks";

const ui = () => render(<QueryClientProvider client={queryClient}><Metodologia /></QueryClientProvider>);

describe("Metodología — provenance, parity, honesty", () => {
  beforeEach(() => queryClient.clear());

  it("renders the 31 constants with provenance", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("MULT")).toBeInTheDocument());
    // 31 data rows + header
    expect(screen.getAllByRole("row")).toHaveLength(32);
    expect(screen.getAllByText(/v16 calibration/).length).toBeGreaterThan(10);
  });

  it("lists the 9 red lines with their sources", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/máximo histórico ES \(T1-2013\)/)).toBeInTheDocument());
    expect(screen.getByText(/umbral Maastricht/)).toBeInTheDocument();
  });

  it("states engine parity, the MC ±2pp rule, and the seed-42 caveat", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/mismo fixture de anclas/i)).toBeInTheDocument());
    expect(screen.getByText(/±2 pp/)).toBeInTheDocument();
    expect(screen.getByText(/PCG64/)).toBeInTheDocument();
  });

  it("explains persona reds vs global red lines (the 15% sobre / 40% renta case)", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/Sobrecarga > 40 % renta/)).toBeInTheDocument());
    expect(screen.getByText(/15,0/)).toBeInTheDocument();
  });

  it("shows the known-gaps list", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/mora bancaria/i)).toBeInTheDocument());
    expect(screen.getByText(/RETA/)).toBeInTheDocument();
    expect(screen.getByText(/govindicators\.org/)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/routes/__tests__/laboratorio.test.tsx src/routes/__tests__/metodologia.test.tsx`
Expected: FAIL — placeholders.

- [ ] **Step 3: Implement Laboratorio**

`frontend/src/routes/Laboratorio.tsx`:

```tsx
import { useState } from "react";
import { useMonteCarlo, useRedlines } from "../api/hooks";
import { baseline, YEARS } from "../engine/spain";
import { ALL_SERIES_KEYS, seriesOf, type AnySeriesKey } from "../engine/derived";
import { LEVER_SPECS } from "../engine/levers";
import { BASE_LEVERS } from "../engine/vintage";
import { nf } from "../lib/fmt";
import { FanChart } from "../components/FanChart";
import { ProjectionChart } from "../components/ProjectionChart";
import { SERIES_FORMAT } from "../components/KpiRow";
import { useScenario, useScenarioStore } from "../state/scenarioStore";

export default function Laboratorio() {
  const [seriesKey, setSeriesKey] = useState<AnySeriesKey>("b");
  const scn = useScenario();
  const levers = useScenarioStore((s) => s.levers);
  const redlines = useRedlines();
  const mc = useMonteCarlo(levers, true);
  const base = baseline();
  const f = SERIES_FORMAT[seriesKey] ?? { dec: 1, unit: "" };
  const bound = (redlines.data?.redlines ?? [])
    .filter((rl) => rl.series === seriesKey)
    .map((rl) => ({ value: rl.threshold, label: rl.label }));

  return (
    <div>
      <div className="head"><h1>Laboratorio</h1>
        <span className="meta">explorador de las 40 series del motor + abanico Monte Carlo (servidor)</span>
      </div>

      <div className="card">
        <h4>
          <label htmlFor="serie-select">Serie</label>
          <small>{seriesKey} · {f.unit || "índice"}</small>
        </h4>
        <select id="serie-select" aria-label="Serie" value={seriesKey}
          onChange={(e) => setSeriesKey(e.target.value as AnySeriesKey)}
          style={{ maxWidth: 320, marginBottom: 8 }}>
          {ALL_SERIES_KEYS.map((k) => <option key={k} value={k}>{k}</option>)}
        </select>
        <ProjectionChart years={YEARS} baseline={seriesOf(base, seriesKey)}
          scenario={seriesOf(scn, seriesKey)} redLines={bound} unit={f.unit} dec={f.dec} />
      </div>

      <div className="row2">
        <div className="card">
          <h4>Abanico Monte Carlo · deuda/PIB hasta 2070
            <small>{mc.data ? `${mc.data.n_paths} trayectorias · semilla ${mc.data.seed}` : "4000 trayectorias · semilla 42"}</small>
          </h4>
          {mc.isError && <div className="banner err">Monte Carlo no disponible — el resto de la app sigue funcionando.</div>}
          {mc.isPending && !mc.data && <p style={{ fontSize: 12 }}>Calculando abanico…</p>}
          {mc.data && <FanChart years={mc.data.years} percentiles={mc.data.percentiles} />}
          <p className="src" style={{ whiteSpace: "normal" }}>
            El abanico se calcula en el servidor (Python). Validación: envolvente dorada
            gold_escenarios_deuda_mc.csv con tolerancia ±2 pp en 2030/2050/2070 — los pines de
            semilla 42 del fixture atan solo al motor Python.
          </p>
        </div>
        <div className="card">
          <h4>Palancas en crudo <small>vector actual vs base congelada</small></h4>
          <table style={{ fontSize: 11, borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr><th style={{ textAlign: "left" }}>palanca</th><th>actual</th><th>base</th></tr>
            </thead>
            <tbody>
              {LEVER_SPECS.map((s) => (
                <tr key={s.id}>
                  <td>{s.sym} · {s.nm}</td>
                  <td style={{ textAlign: "right" }}>{nf(levers[s.id], s.dec)}</td>
                  <td style={{ textAlign: "right", color: "var(--muted)" }}>{nf(BASE_LEVERS[s.id], s.dec)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Implement Metodología**

`frontend/src/routes/Metodologia.tsx`:

```tsx
import { useConstants, useHealth, useRedlines, useVintage } from "../api/hooks";
import { nf } from "../lib/fmt";
import { STALE_LIMIT_DAYS, staleDays } from "../state/appHealth";

const KNOWN_GAPS = [
  "Mora bancaria (NPL, Banco de España): la serie sigue sin conectar — el riesgo de crédito del perfil 🏦 se lee por proxy (paro + colateral).",
  "Bases de cotización del RETA: sin API pública — la senda de la cuota de autónomo no está modelada.",
  "WGI control de la corrupción: API archivada — descarga manual en govindicators.org.",
  "Contratos menores · adjudicación: la señal vive a nivel de contrato, sin serie pública.",
  "Personas 04, 05, 07–12: configuración pendiente (el renderizador ya es genérico).",
];

export default function Metodologia() {
  const constants = useConstants();
  const redlines = useRedlines();
  const health = useHealth();
  const vintage = useVintage();
  const days = health.data ? staleDays(health.data.vintage) : null;

  return (
    <div>
      <div className="head"><h1>Datos y método</h1>
        <span className="meta">todo lo que se muestra es computado; nada es consejo</span>
      </div>

      <div className="card">
        <h4>Vintage <small>congelado — la app nunca mezcla fechas</small></h4>
        <p style={{ fontSize: 12 }}>
          Datos congelados el <b>{health.data?.vintage ?? "…"}</b>
          {vintage.data ? <> ({vintage.data.n_files} ficheros fuente)</> : null}.
          {days !== null && (days > STALE_LIMIT_DAYS
            ? ` Aviso: el vintage tiene ${days} días — los datos observados pueden estar desactualizados.`
            : ` Antigüedad actual: ${days} días (umbral de aviso: ${STALE_LIMIT_DAYS}).`)}
        </p>
      </div>

      <div className="card">
        <h4>Paridad de motores <small>el mismo número en Python y en el navegador</small></h4>
        <p style={{ fontSize: 12 }}>
          El motor TypeScript de esta página pasa el mismo fixture de anclas que el motor Python
          (tests/fixtures/engine_anchors.json, vintage {health.data?.vintage ?? "…"}): senda central de
          deuda 2026/2030/2035/2050 (±10⁻⁶), cuota 2026 (±0,01), 8 presets × 7 series en 2035/2050
          (±10⁻⁶), sonda con las 10 palancas (±10⁻⁶) e identidad contable base (±10⁻⁹). Al arrancar,
          la app además cruza su cálculo local contra POST /scenario y muestra un aviso si difieren.
        </p>
        <p style={{ fontSize: 12 }}>
          Monte Carlo se calcula <b>solo</b> en el servidor: los sorteos NumPy PCG64 no son
          reproducibles en JS, así que los pines de semilla 42 del fixture atan al motor Python y la
          regla de aceptación del abanico es la envolvente dorada ±2 pp en 2030/2050/2070.
        </p>
      </div>

      <div className="card">
        <h4>Constantes del motor <small>calibración v16 — defaults declarados, no estimaciones</small></h4>
        {constants.isSuccess ? (
          <table style={{ fontSize: 11, borderCollapse: "collapse" }}>
            <thead><tr><th style={{ textAlign: "left" }}>nombre</th><th>valor</th><th style={{ textAlign: "left" }}>unidad</th><th style={{ textAlign: "left" }}>procedencia</th></tr></thead>
            <tbody>
              {constants.data.constants.map((c) => (
                <tr key={c.name}>
                  <td><code>{c.name}</code></td>
                  <td style={{ textAlign: "right" }}>{nf(c.value, c.value < 0.1 ? 4 : 2)}</td>
                  <td>{c.unit}</td>
                  <td style={{ color: "var(--ink-2)" }}>{c.provenance}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : constants.isError ? (
          <div className="banner err">Constantes no disponibles</div>
        ) : null}
        <p className="src" style={{ whiteSpace: "normal" }}>
          Las constantes MC vectoriales (MC_PB_DRIFT y las pendientes de extrapolación) viven solo en
          el servidor: /constants expresa escalares y el abanico nunca se recalcula en el navegador.
        </p>
      </div>

      <div className="card">
        <h4>Líneas rojas globales <small>umbrales v12, con fuente empírica</small></h4>
        {redlines.isSuccess ? (
          <ul style={{ fontSize: 12, margin: 0, paddingLeft: 18 }}>
            {redlines.data.redlines.map((rl) => (
              <li key={rl.id}><b>{rl.label}</b> — serie <code>{rl.series}</code>, umbral {nf(rl.threshold, 1)} · {rl.source}</li>
            ))}
          </ul>
        ) : redlines.isError ? (
          <div className="banner err">Líneas rojas no disponibles</div>
        ) : null}
        <p style={{ fontSize: 12 }}>
          Los semáforos de cada perfil usan umbrales de <b>presentación</b> propios y nunca se mezclan
          con estas líneas globales. Ejemplo: la fila «Sobrecarga &gt; 40 % renta» del perfil 🔑 evalúa
          la serie <code>sobre</code> contra {nf(15.0, 1)} — el 40 % es la definición Eurostat de
          sobrecarga (porcentaje de la renta), el 15,0 es el umbral sobre la cuota de población que la
          sufre. Estado «cerca» = a menos del 10 % del umbral (0,5 pp absolutos para umbrales en cero).
        </p>
      </div>

      <div className="card">
        <h4>Huecos conocidos <small>lo que falta se declara, no se rellena</small></h4>
        <ul style={{ fontSize: 12, margin: 0, paddingLeft: 18 }}>
          {KNOWN_GAPS.map((g) => <li key={g}>{g}</li>)}
        </ul>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/routes/__tests__/laboratorio.test.tsx src/routes/__tests__/metodologia.test.tsx`
Expected: PASS (9 tests).

- [ ] **Step 6: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/src/routes/Laboratorio.tsx frontend/src/routes/Metodologia.tsx frontend/src/routes/__tests__
git commit -m "feat(frontend): Laboratorio series explorer with MC fan and Metodología provenance page"
```

---

### Task 15: Playwright smoke, README, final full-suite run

**Files:**
- Create: `frontend/playwright.config.ts`, `frontend/e2e/smoke.spec.ts`, `frontend/README.md`

**Interfaces:**
- Consumes: the whole app; the mocked build (`npm run build:mock` → MSW browser worker from Task 6/11).
- Produces: `npm run e2e` green offline; `frontend/README.md` documenting run/test/build and the API dependency (spec §1 deliverable 4).

- [ ] **Step 1: Write the Playwright config and smoke spec**

`frontend/playwright.config.ts`:

```ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  use: { baseURL: "http://localhost:4173" },
  webServer: {
    command: "npm run build:mock && npm run preview",
    url: "http://localhost:4173",
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
  },
});
```

`frontend/e2e/smoke.spec.ts` (spec §9 row 6, exactly: boot, move a lever, gauge figure + chart path change, switch persona, scenario persisted, toggle theme, no console errors — all numbers are engine-real: base b 2026 = 106,3; with r = 4,80 the S1 vector gives b 2026 = 107,1 and deuda 2050 306,9):

```ts
import { expect, test } from "@playwright/test";

test("smoke: boot → lever → persona → persistence → theme → no console errors", async ({ page }) => {
  const errors: string[] = [];
  page.on("console", (msg) => { if (msg.type() === "error") errors.push(msg.text()); });
  page.on("pageerror", (err) => errors.push(String(err)));

  // boot
  await page.goto("/");
  await expect(page.getByText("España en escenarios").first()).toBeVisible();
  await expect(page.getByText(/proyección condicional, no recomendación/i)).toBeVisible();
  await expect(page.getByText("223,8")).toBeVisible(); // deuda 2050 at base

  // persona 01: capture gauge figure and chart path
  // (the name matches both the nav pill and Inicio's card link — either navigates)
  await page.getByRole("link", { name: /Bonista/ }).first().click();
  await expect(page.getByText("💼 Inversor en bonos: ¿me pagarán los 10 años?")).toBeVisible();
  // "106,3" appears in the Deuda tile AND the semaphore row — .first() avoids strict-mode
  await expect(page.getByText("106,3").first()).toBeVisible(); // b 2026 base
  const pathBefore = await page.locator("path.recharts-curve").last().getAttribute("d");

  // move the r lever to 4.8 (the S1 vector)
  await page.locator('input[type="range"]').first().fill("4.8");
  await expect(page.getByText("4,80 %")).toBeVisible();
  await expect(page).toHaveURL(/r=4\.8/);
  await expect(page.getByText("107,1").first()).toBeVisible(); // b 2026 moves 106,3 → 107,1
  await expect
    .poll(async () => page.locator("path.recharts-curve").last().getAttribute("d"))
    .not.toBe(pathBefore); // chart path changed
  await expect(page.getByText("S1 tipos +200 pb")).toHaveClass(/on/); // vector now equals S1

  // switch persona: scenario persists (v16 core argument)
  await page.getByRole("link", { name: /Político/ }).click();
  await expect(page.getByText("🗳️ ¿Qué palanca puedo mover sin cruzar una línea roja?")).toBeVisible();
  await expect(page.getByText("4,80 %")).toBeVisible();
  await expect(page.getByText(/🔮 condicional/).first()).toBeVisible();

  // theme toggle persists to <html data-theme>
  await page.getByRole("button", { name: /cambiar tema/i }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

  expect(errors).toEqual([]);
});
```

- [ ] **Step 2: Install the browser and run the smoke**

Run: `cd frontend && npx playwright install chromium && npm run e2e`
Expected: 1 passed. The preview is fully offline — MSW's worker intercepts every `http://localhost:8000/*` call (`VITE_MOCK_API=1` build).

- [ ] **Step 3: Write `frontend/README.md`**

```markdown
# frontend — España en escenarios (fase 2)

Panel editorial sobre la API de fase 1: 10 palancas, presets S0–S7, líneas rojas,
Monte Carlo y 4 perfiles (01 Bonista, 02 Banca, 03 Comprador, 06 Político).
El escenario se calcula EN el navegador con un port TypeScript del motor v16,
verificado contra el mismo fixture de anclas que el motor Python
(`tests/fixtures/engine_anchors.json`, vintage 2026-07-31).

## Requisitos

- Node 20+ (desarrollado con Node 22) y npm.
- Para usar la app: la API de fase 1 en marcha —
  `uvicorn api.main:app --reload --port 8000` desde la raíz del repo.
  `VITE_API_BASE` cambia la URL (por defecto `http://localhost:8000`).
- Para los tests: nada — todo corre offline con MSW.

## Comandos

| Comando | Qué hace |
|---|---|
| `npm install` | dependencias |
| `npm run dev` | Vite dev server en http://localhost:5173 (necesita la API) |
| `npm test` | Vitest: paridad de motores, store/URL, componentes, rutas (offline) |
| `npm run e2e` | Playwright smoke contra un preview con API simulada (offline) |
| `npm run build` | build de producción en `dist/` |
| `npm run gen:constants` | regenera `src/engine/constants.ts` + `vintage.ts` desde la API y `data/gold/` (solo al cambiar de vintage; el resultado se commitea) |

## Contratos que no se negocian

- `src/engine/` es un port línea a línea de `engine/spain.py`; el test
  `src/engine/__tests__/anchors.test.ts` es el contrato de doble motor.
- Monte Carlo nunca se calcula en JS (PCG64 no reproducible); el abanico llega de
  `POST /scenario/montecarlo` y su regla de aceptación es la envolvente dorada ±2 pp.
- Copy de personas y presets: verbatim de la API. Números: siempre `es-ES` vía `src/lib/fmt.ts`.
- Sin API no hay app: pantalla de bloqueo con la URL y el comando de arranque, jamás datos inventados.
```

- [ ] **Step 4: Final full-suite run (the phase gate)**

Run, from `frontend/`:

```bash
npm test          # every vitest suite: engine parity, store, components, routes
npm run e2e       # Playwright smoke, offline
npm run build     # tsc -b && vite build must be clean
```

And from the repo root, confirm phase 1 is untouched:

```bash
git status --porcelain -- api engine data tests scripts   # must be empty
python -m pytest -q                                        # 150 phase-1 tests still green
```

Expected: everything green; no diff outside `frontend/` and `docs/`.

- [ ] **Step 5: Commit**

```bash
cd /home/dan/projects/evo_final_work
git add frontend/playwright.config.ts frontend/e2e frontend/README.md
git commit -m "test(frontend): Playwright smoke and README; phase-2 suite complete"
```

---

## Self-review

**1. Spec coverage** (each binding section → task):

| Spec item | Task(s) |
|---|---|
| §2 repo layout (`frontend/` tree, Node 20+, npm, gitignore) | 1 (scaffold, `.gitignore`), 2 (generator), all tasks respect the tree |
| §3 static data once via React Query, `staleTime: Infinity` | 6 |
| §3 in-browser recompute < 16 ms | 3 (pure 25-iteration engine), 7 (`useScenario` memo) |
| §3 MC debounced 400 ms, cancel-previous, server-side | 6 (`useMonteCarlo`), 14 (Laboratorio) |
| §3 cross-check on load + mismatch banner | 11 (`crossCheckEngine`, `Warnings`, shell test) |
| §3 `VITE_API_BASE`, blocking error screen | 6 (`API_BASE`), 11 (`ApiDownScreen`) |
| §4 line-faithful TS port, same 40 keys/order/deviation semantics | 3 |
| §4 generated `constants.ts` + drift test | 2 |
| §4 anchors battery incl. tolerances; `montecarlo_seed42` not asserted | 5 |
| §4/§7-3 `ipvreal` derived + unit test | 4 |
| §5 tokens (paper/ink/accent, `--st-*`, dark block, localStorage + `prefers-color-scheme`) | 1 |
| §5 typography (`tabular-nums`, `fmt()` only) | 1, 8 (all figures via `nf`/`sg`/`eur`) |
| §5 8-pt spacing, fluid grid, sticky 300 px rail, drawer < 1024 px | 1 (CSS), 10 (rail) |
| §5 motion (number roll-ups ~180 ms, chart transitions, gauge fill) + reduced-motion | 8 (`useRollup` in KpiTile, gauge `transition: width`), 9 (`animationDuration`), 1 (`--dur` + reduced-motion kill switch) |
| §5 Recharts for series+fan; SVG/CSS for gauges/chains/stamps/semaphore | 9, 8 |
| §5 stamps computed from state | 8 (`Stamp`), 13 (`fresh` derivation), tests |
| §6 Inicio (vintage+coverage, headline figures, semaphore, persona cards) | 12 |
| §6 Persona generic ×4 (5 KPI → 2 charts → semáforo+cadena+narrativa) | 13 |
| §6 Laboratorio (41-series explorer, MC fan + ±2 pp note, raw levers) | 14 |
| §6 Metodología (31 constants, staleness, red-line sources, parity, gaps) | 14 |
| §6 lever rail persistent across routes | 11 (shell), 15 (smoke asserts persistence) |
| §7-1 MC server-side, no `/constants` schema change | 6, 14 (Metodología states vector constants stay server-side) |
| §7-2 JS MC rule = gold envelope ±2 pp | 5 (comment), 14 (Metodología copy) |
| §7-4 full series regardless of horizon; front slices only | 6 (client test), 12/13 (`kIndex` display slicing) |
| §7-5 persona reds ≠ global red lines, explained | 4 (`evaluatePersonaReds` separate), 13 (separate semaphores), 14 (Metodología explanation + 15,0/40 % case) |
| §8 API down / endpoint down / stale vintage / mismatch / no-advice | 11 (+ per-surface `isError` fallbacks in 10, 12, 13, 14) |
| §9 test table rows 1–6 | 5, 4, 7, 8+9+10, 13, 15 — all offline via MSW |
| §10 out of scope respected | no generic-country UI, no extra personas, no phase-1 edits (Task 15 gate) |

**2. Placeholder scan:** no TBDs; every code step carries full code; the only intentionally deferred files are Task-11 route placeholders explicitly replaced in Tasks 12–14, and `derived.ts`/`redlines.ts` `export {};` stubs created in Task 3 and replaced in Task 4 (each replacement is a named task step, not an open end).

**3. Name/type consistency:** verified across tasks — `nf/sg/eur` (1→8,9,10,12,13,14), `runScenario/baseline/SERIES_KEYS/Y0/YEARS/Scenario` (3→5,6,7,8,9,12,13,14), `BASE_LEVERS/CENTRAL/OLDDEP/V0/VINTAGE` (2→3,5,6,7,10,14), `statusOf/evaluateRedlines/evaluatePersonaReds/STATUS_LABEL/RedLineStatus/RedLineDef` (4→6,8,12,13), `useScenarioStore/useScenario/kIndex/HORIZON_YEARS/stateToSearch/searchToPatch/initFromUrl/startUrlSync/hotIds/setHotIds` (7,13→10,11,12,14), `SemaphoreItem/ChainSpec/SERIES_FORMAT/UP_IS_BAD/dialDomain` (8→12,13,14), `useMonteCarlo/queryClient/api/ApiError/API_BASE` (6→11,14), `SHIPPED_IDS/getPersonaModule/PersonaModule` (11,13), `crossCheckEngine/staleDays/STALE_LIMIT_DAYS/useAppHealth` (11→14).

## Known deviations (intentional, for the reviewer)

1. **`vintage.ts` as a second generated file.** Spec §4 names only `constants.ts` as generated; the engine also needs V0/BASE_LEVERS/CENTRAL/OLDDEP, which `/constants` cannot carry. The same committed generator emits both, and both are pinned by tests. Alternative (hand-typing 25×5 CSV rows) would recreate exactly the drift the spec forbids.
2. **Persona identity lives in the route path, not `?p=`.** Spec §2 defines `/persona/:id`; v16's `?p=` index is therefore redundant. The URL still carries `h` + moved levers (`?h=2035&r=4.8`), so scenario sharing works as in v16. Spec §9's `?p=…&r=…` example is satisfied in substance (round-trip test covers `h` + levers; the persona is in the path).
3. **Gauge dial domains are computed** (min/max of baseline ∪ scenario ∪ red line, 16 % pad). The API card's `outs` carry no v16 `dial:[lo,hi]` tuples, so authored domains would have been invented data. Same normalization rule as the v16 chart auto-domain.
4. **Near band is 10 % everywhere** (semaphore AND gauge warn state), matching `engine/redlines.py`/spec §4.5; v16 used 12 %. One tolerance, one honesty rule.
5. **Horizon buttons: 2026/2030/2035/2040/2050.** The v16 extract confirms `.hb` buttons exist but the exact year list isn't recoverable from the captured lines; this set covers the fixture's anchor years plus a mid-point.
6. **KPI tile `o-note` (formula footnote) omitted** — the note strings were v16-authored copy not present in the API payload; the tile shows the computed delta line instead. Same reason there is no attribution card: spec §6's row-3 is semáforo + cadena + narrativa (v16's attribution card needed the per-lever re-run and was dropped by the spec).
7. **Persona historical chart (chA) reuses `ProjectionChart`** with a single observed series rather than a dedicated retro-styled component (purple `--retro` line, date x-axis). Visual difference: legend wording and line color. Flagged for a fast-follow polish pass.
8. **MC percentiles in mocks are linear interpolations between the fixture's real 2030/2050/2070 pins** — display-plumbing only; the real fan always comes from the API, and no test asserts fan *values* beyond the pinned years.
9. **`defaults_used` banner slot is generic.** The Spain endpoints never emit `defaults_used` (it belongs to `GenericScenarioResponse`, out of scope §10); `Warnings` exposes `addWarning()` so the inherited honesty mechanism exists the day the generic UI lands.
10. **Stale-vintage threshold set at 90 days** — the spec demands the banner but no number; 90 days ≈ one quarter of drift on a quarterly-refresh dataset. Trivial to change (`STALE_LIMIT_DAYS`).





