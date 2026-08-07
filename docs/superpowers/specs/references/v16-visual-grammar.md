# v16 Visual/UX Grammar — Extraction Reference

> Source of truth for this doc: `legacy/design_data/design/v16_perfiles_lab/v16_perfiles_lab.html`
> (built artifact) + `_v16_template.html` (same file, data placeholder instead of
> baked JSON) + `build_v16.py` (the build script) + `v14_00_indice_app.md` +
> `v15_perfiles/v15_00_indice_perfiles.md` + `v15_perfiles/v15_perfil_01_bonista.html`
> (and a class-diff across all 12 v15 persona files).
>
> Scope: **visual/UX grammar only** — colors, type, layout, component anatomy,
> chart rendering, interaction/state mechanics. The calculation engine (the `run(L)`
> function, `LEVERS`/`PRESETS` economics, calibration constants) is captured
> elsewhere and is out of scope here except where it drives what's on screen
> (e.g. what triggers a re-render).
>
> Lineage: **v14** (12-tab full app, established the design system) → **v15**
> (12 static, JS-free persona cards, "cifras reales" — real numbers baked at
> build time) → **v16** (this doc's subject: adds an interactive 9-10-lever
> "laboratorio" on top of the v15 persona-card grammar, client-side recompute).

---

## A. Design tokens

### A.1 Color palette — v16 (`v16_perfiles_lab.html` lines 7–34)

Light (default, `color-scheme: light`):

```css
--page: #eeeee9; --surface: #fcfcfb; --card: #f9f9f7;
--ink: #0b0b0b; --ink-2: #52514e; --muted: #898781;
--grid: #e1e0d9; --baseline: #c3c2b7; --ring: rgba(11,11,11,0.10);
--s1: #2a78d6; --s2: #eb6834; --s3: #1baf7a;
--band-out: #cde2fb; --band-in: #9ec5f4;
--div-neg: #e34948; --good: #006300;
--accent: #2a78d6; --chip: #eef3fa; --code: #f2f1ed;
--retro: #7a5ea8; --chip-retro: #f1ecf9;
--warn: #a86a00; --chip-warn: #fdf3e2;
--lab: #b0399a; --chip-lab: #fbecf7;
```

Dark (`@media (prefers-color-scheme: dark)`, gated by
`:root:where(:not([data-theme="light"]))` — i.e. an explicit
`data-theme="light"` attribute on `<html>`/`<body>` forces light mode even
inside a dark OS):

```css
--page: #060606; --surface: #1a1a19; --card: #141413;
--ink: #f4f4f1; --ink-2: #b9b8b2; --muted: #898781;
--grid: #2a2a28; --baseline: #383835; --ring: rgba(255,255,255,0.10);
--s1: #6ba3e8; --s2: #f2895c; --s3: #3fc796;
--band-out: #1d3352; --band-in: #244d7d;
--div-neg: #f0706f; --good: #5fc25f;
--accent: #6ba3e8; --chip: #16283d; --code: #232322;
--retro: #a98cd8; --chip-retro: #2a2140;
--warn: #d9a441; --chip-warn: #3a2c12;
--lab: #e07ac8; --chip-lab: #38182f;
```

`--lab`/`--chip-lab` (magenta, `#b0399a` / `#fbecf7` light) is **v16-only** —
it marks everything belonging to the interactive lab layer (rail header,
lever "moved" state, preset chips, attribution bars) as visually distinct
from the v14/v15 base grammar's blue `--accent`.

Semantic role map (same names recur across every component):
- `--s1` blue / `--s2` orange / `--s3` green — generic series colors (chart 1/2/3).
- `--accent` (= `--s1`) — brand blue, "forward/base" badges, chip default state.
- `--retro` purple — retrospective/observed-data accent (📅 stamp).
- `--lab` magenta — v16 lab/scenario accent (🔮 stamp, lever UI).
- `--warn` amber — "near threshold" semaphore state.
- `--div-neg` red / `--good` dark green — bad/good deltas, crossed threshold, red-line markers.
- `--baseline` warm gray — dashed base/reference lines, "moved" tick marks.
- `--grid` — hairline borders and chart gridlines.
- `--ring` — box-shadow tint (translucent ink/white).

### A.2 Color palette — v15 (persona cards, `v15_perfil_01_bonista.html` lines 7–34)

Same token names, **near-identical values**, with two differences from v16:
1. v15 adds a 6-step quintile/severity scale not present in v16:
   `--q1:#eef4fc; --q2:#cde2fb; --q3:#9ec5f4; --q4:#6ba3e8; --q5:#2a78d6; --q6:#1c5db1;`
   (dark: `#131c2b / #16304f / #1c477c / #2a63ad / #3987e5 / #7ab1ef`).
2. v15's dark theme is slightly higher-contrast: `--ink:#ffffff` (v16 uses
   `#f4f4f1`), `--s1:#3987e5` (v16 `#6ba3e8`), `--good:#0ca30c` (v16 `#5fc25f`).
   Treat v16's dark values as the more recent/authoritative ones if the new
   frontend needs to pick a single source, but note the drift exists.

v15 has no `--lab`/`--chip-lab` — there is no lab layer, only `--accent`/`--retro`.

### A.3 Typography

```css
body { font: 13px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif;
  font-variant-numeric: tabular-nums; }
svg text { fill: var(--ink-2); font-size: 9.5px; }
.lbl { font-size: 9.5px; font-weight: 700; fill: var(--ink-2); }
```

- No web fonts — pure system-font stack, consistent v14/v15/v16.
- `tabular-nums` is applied app-wide (v16: on `body`; v15: per-element on
  `.o-val`/`.o-delta`/`.rl-item .t b`) so numbers never jitter width as levers move.
- Numbers are **Spanish-locale, decimal comma**, formatted through small helpers
  (`v16_perfiles_lab.html` lines 243–246):

```js
const nf = (v, d) => (v === null || v === undefined || !isFinite(v)) ? "s/d"
  : new Intl.NumberFormat("es-ES", {minimumFractionDigits: d, maximumFractionDigits: d}).format(v).replace("-", "−");
const sg = (v, d) => (v >= 0 ? "+" : "−") + nf(Math.abs(v), d);
const eur = v => new Intl.NumberFormat("es-ES", {maximumFractionDigits: 0}).format(v).replace("-", "−");
```

Note the `.replace("-", "−")`: ASCII hyphen-minus is swapped for the Unicode
minus sign (U+2212) for correct typographic rendering. `sg()` always prefixes
an explicit `+`/`−` sign — used everywhere a "vs base" delta is shown. `eur()`
drops decimals entirely for big absolute numbers (currency, counts of mortgages).

Font-size scale actually used (v16): 8.5px (motor/src footnotes) · 9px
(meta/notes/legend) · 9.5px (chart labels, chip text) · 10–10.5px (chain/body
text, lever names) · 11px (persona pill tabs off state) · 11.5px (lever value)
· 13px (`body`, card `h4`) · 17px (`.head h1`). v15 runs slightly larger
throughout (11–15–20px) since it has no rail competing for width.

### A.4 Spacing, borders, shadow, radius

- Card/panel border: `1px solid var(--grid)`.
- Card radius: `8px` (`.out`, `.card`); pill radius: `999px` (chips, tabs,
  presets, semaphore status badges); small chip/tag radius: `5–7px`.
- Outer app shadow: `box-shadow: 0 2px 6px var(--ring), 0 18px 44px -22px var(--ring);`
  — a tight contact shadow plus a soft ambient one, both tinted with the
  translucent `--ring` token rather than plain black.
- Card padding conventions: KPI tile `8px 11px 7px`; generic `.card`
  `7px 10px 8px` (v16) / `9px 12px` (v15, roomier since no rail).
- Gap rhythm: `.main` uses `gap: 8px` between head/outs/row2/row3; `.outs` and
  `.row2`/`.row3` grids use `gap: 9px`.

### A.5 Canvas dimensions and print

```css
.app { width: 1680px; height: 1080px; margin: 24px auto; background: var(--surface);
  border: 1px solid var(--ring); border-radius: 6px; overflow: hidden;
  box-shadow: 0 2px 6px var(--ring), 0 18px 44px -22px var(--ring);
  display: flex; flex-direction: column; transform-origin: top center; }
@media print { body { background: var(--surface); } .app { margin: 0; border: 0; border-radius: 0; box-shadow: none; } }
```

v15 additionally declares `@page { size: 1680px 1080px; margin: 0; }`
(not present in v16's `<style>`, but the render pipeline doc confirms the
same page box is used app-wide). Fixed canvas is **1680×1080px**, rendered via:

```bash
chrome-headless-shell --headless --window-size=1728,1128 --screenshot=out.png "file://…"
chrome-headless-shell --headless --print-to-pdf=out.pdf "file://…"
```

(the 1728×1128 window leaves ~24px chrome margin around the 1680×1080 `.app` box).

---

## B. Component anatomy

### B.1 KPI dial / gauge tile (`.out`)

Markup (from `render()`'s `$("outs").innerHTML` builder, `v16_perfiles_lab.html` lines 887–910):

```html
<div class="out">
  <span class="o-seal">🔮</span>
  <div class="o-label">Bono 10A España</div>
  <div class="o-val">3,58 <small>%</small></div>
  <div class="o-delta bad">+0,16 vs base</div>
  <div class="gaugebar">
    <span class="f warn2" style="width:51.1%"></span>
    <span class="bm" style="left:48.9%"></span>
    <span class="rl" style="left:100%"></span>
  </div>
  <div class="o-note">r + prima de plazo 0,17 + spread/100</div>
</div>
```

CSS:

```css
.out { border: 1px solid var(--grid); border-radius: 8px; padding: 8px 11px 7px;
  background: var(--surface); position: relative; }
.out .o-label { font-size: 10px; color: var(--muted); text-transform: uppercase;
  letter-spacing: .06em; font-weight: 800; }
.out .o-val { font-size: 21px; font-weight: 800; line-height: 1.1; }
.out .o-val small { font-size: 11px; font-weight: 700; color: var(--muted); }
.out .o-delta { font-size: 10.5px; font-weight: 700; }
.out .o-delta.bad { color: var(--div-neg); } .out .o-delta.good { color: var(--good); }
.out .o-note { font-size: 9px; color: var(--muted); }
.out .o-seal { position: absolute; top: 7px; right: 8px; font-size: 9px; }
.gaugebar { position: relative; height: 6px; border-radius: 4px; background: var(--grid); margin: 5px 0 3px; }
.gaugebar .f { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 4px;
  background: var(--s1); transition: width .18s ease; }
.gaugebar .f.bad { background: var(--div-neg); }
.gaugebar .f.warn2 { background: var(--warn); }
.gaugebar .f.ok { background: var(--s3); }
.gaugebar .rl { position: absolute; top: -3px; bottom: -3px; width: 2px; background: var(--div-neg); }
.gaugebar .bm { position: absolute; top: -2px; bottom: -2px; width: 1px; background: var(--baseline); }
```

The "dial" is a flat horizontal bar, not an arc/radial gauge: a track
(`.gaugebar`, 6px tall) with (1) a colored fill `.f` whose `width%` is the
current value normalized to a per-KPI `[lo,hi]` domain declared in the
persona's `outs[].dial` tuple, (2) a thin vertical `.bm` "baseline mark" tick
showing where BASE sits, and (3) an optional `.rl` red-line tick at the
danger threshold (`outs[].red`). Fill color swaps `--s1`/`--warn`/`--div-neg`/`--s3`
based on distance-to-threshold logic in `render()` (lines 894–897): exact
crossing → `.bad`; within 12% of threshold → `.warn2`; otherwise unstyled/`.ok`.
**`width` is the only CSS property with a `transition` anywhere in v16** (`.18s ease`) —
every other visual change is an instant DOM replace.

The 📅/🔮 "stamp" badge (`.o-seal`, top-right corner, absolutely positioned)
switches per-tile between retrospective and conditional based on whether ANY
lever has moved from BASE and horizon = base year (`fresh` flag, line 874).

### B.2 Lever slider row (`.lev`)

Markup (`buildRail()`, lines 812–817):

```html
<div class="lev" id="lev-r">
  <div class="l1">
    <span class="sym">r</span>
    <span class="nm">Tipo de interés · Euríbor 12m</span>
    <span class="vv" id="vv-r">2,80 %</span>
  </div>
  <input type="range" id="in-r" min="0" max="6" step="0.05" value="2.8">
  <div class="src">ecb_euribor12m.csv · 2026-06</div>
</div>
```

CSS:

```css
.levers { display: flex; flex-direction: column; gap: 4px; flex: 1; min-height: 0; }
.lev { border-radius: 6px; padding: 2px 5px 3px; }
.lev.hot { background: var(--chip-lab); }
.lev .l1 { display: flex; align-items: baseline; gap: 5px; }
.lev .nm { font-size: 10.5px; font-weight: 700; flex: 1; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; }
.lev .sym { font-size: 9.5px; font-weight: 800; color: var(--lab); font-style: italic; }
.lev .vv { font-size: 11.5px; font-weight: 800; color: var(--ink); white-space: nowrap; }
.lev .vv.moved { color: var(--lab); }
.lev input[type=range] { width: 100%; height: 13px; margin: 0; accent-color: var(--lab); cursor: pointer; }
.lev .src { font-size: 8.5px; color: var(--muted); white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; }
```

Native `<input type=range>` styled only via `accent-color` (no custom
thumb/track skin) — the browser default slider tinted magenta. `.lev.hot`
highlights the whole row with a tinted background when the current persona
lists that lever id in its `hot: [...]` array (its 3–4 "most relevant"
levers). The value readout (`.vv`) turns magenta (`.moved`) once the lever's
value differs from `BASE[id]` by more than `1e-9`.

### B.3 Preset buttons (`.ps`)

```css
.presets { display: flex; flex-wrap: wrap; gap: 3px; }
.ps { font-size: 9.5px; font-weight: 700; padding: 3px 6px; border-radius: 5px;
  border: 1px solid var(--grid); background: var(--surface); color: var(--ink-2); cursor: pointer; }
.ps:hover { border-color: var(--lab); color: var(--lab); }
.ps.on { background: var(--lab); color: #fff; border-color: var(--lab); }
```

8 chip buttons (`S0`…`S7`) rendered from the `PRESETS` array; `.on` state is
computed live in `railState()` by comparing the *entire* current lever vector
against each preset's `{BASE, ...set}` merge (exact match within `1e-9`) —
i.e. "which preset (if any) are we currently equal to," not a sticky
selection flag.

### B.4 Stamp iconography

Four stamp conventions carried from v14 through v16 (`v14_00_indice_app.md`
line 25 + implementations):

| Stamp | Meaning | Visual |
|---|---|---|
| 📅 | Observed/retrospective data point | `--retro` purple accent; badge class `.badge-fwd` (v16) / `.badge-retro` (v15) |
| 🔮 | Conditional/forecast scenario | `--lab` magenta accent (v16) / plain `--accent` blue (v15, no lab layer) |
| dashed fan/band | Monte-Carlo p5–p95 uncertainty | filled polygon `var(--band-out)` @ `opacity:.75–.8`, median as solid line |
| red line | Hard threshold / danger level | `var(--div-neg)` dashed (`stroke-dasharray:"4 3"` in charts) or solid 2px tick (`.rl` in gauge bars) |

v16's head badge toggles stamp per current state (`render()` line 880–881):

```js
$("seal").textContent = fresh ? "📅 dato observado · vintage" : "🔮 condicional · " + y;
$("seal").className = "badge-fwd" + (fresh ? "" : " lab");
```

```css
.badge-fwd { background: var(--chip); color: var(--accent); font-size: 10px; font-weight: 700;
  padding: 2px 7px; border-radius: 999px; white-space: nowrap; }
.badge-fwd.lab { background: var(--chip-lab); color: var(--lab); }
```

v15 has a parallel but distinct pair since it has no lab state — every card
is simply "abanico = proyección MC · condicional" (`.badge-fwd`, blue) or, on
retrospective-only pages, `.badge-retro` (purple, `--chip-retro`/`--retro`).

### B.5 Traffic-light semaphore (`.rl-item`)

Markup (`render()` lines 935–943):

```html
<div class="rl-item">
  <span class="ic">🏛️</span>
  <span class="t">Deuda &gt; <b>105 %PIB</b></span>
  <span class="st near">100,7</span>
  <span class="x">cerca · narrativa crack23 · p50 la cruza en 2027</span>
</div>
```

```css
.rl-item { display: grid; grid-template-columns: 18px 1fr auto; align-items: center; gap: 5px;
  border: 1px solid var(--grid); border-radius: 6px; padding: 4px 7px; font-size: 10.5px; margin-bottom: 4px; }
.rl-item .ic { font-size: 12px; }
.rl-item .t b { white-space: nowrap; }
.rl-item .st { font-size: 9px; font-weight: 800; padding: 2px 7px; border-radius: 999px; white-space: nowrap; }
.st.cross { background: var(--div-neg); color: #fff; }
.st.near { background: var(--chip-warn); color: var(--warn); }
.st.safe { background: var(--chip); color: var(--good); }
.rl-item .x { font-size: 9px; color: var(--muted); grid-column: 2 / 4; }
```

Three-state status logic (`statusOf()`, lines 864–870):

```js
function statusOf(val, thr, cmp) {
  if (thr === null || val === null) return ["s/d", ""];
  const cross = cmp === "lt" ? val < thr : val > thr;
  if (cross) return ["cruzada", "cross"];
  const near = Math.abs(val - thr) <= Math.abs(thr || 1) * 0.12;
  return near ? ["cerca", "near"] : ["segura", "safe"];
}
```

Grid layout: icon (18px) · label+threshold (flexible) · status pill (auto,
right-aligned) on row 1; explanatory text spans columns 2–4 on row 2 (`.x`,
`grid-column: 2 / 4`). "Near" is defined as within 12% of the threshold's
magnitude — a single tolerance constant reused for both the semaphore and the
gauge-bar `.warn2` fill color.

### B.6 Transmission chain diagram (`.chain`/`.ch`)

Markup:

```html
<div class="ch">
  <span class="a">tipo BCE</span><span class="arr">→</span>
  <span class="u">Euríbor</span><span class="arr">→</span>
  coste refinanciación → intereses/PIB
  <span class="d up">2,9 %PIB (+0,3)</span>
</div>
```

```css
.chain { display: flex; flex-direction: column; gap: 5px; margin-top: 2px; }
.ch { display: flex; align-items: center; gap: 5px; font-size: 10px; color: var(--ink-2); flex-wrap: wrap; }
.ch .a { font-weight: 700; color: var(--ink); background: var(--code); border-radius: 5px;
  padding: 2px 6px; white-space: nowrap; }
.ch .u { font-size: 8.5px; font-weight: 800; color: var(--accent); background: var(--chip);
  border-radius: 999px; padding: 1px 6px; white-space: nowrap; }
.ch .arr { color: var(--baseline); }
.ch .d { font-weight: 800; white-space: nowrap; }
.ch .d.up { color: var(--div-neg); } .ch .d.dn { color: var(--good); } .ch .d.flat { color: var(--muted); }
```

Each row is a free-text causal sentence with two inline chips — `.a` (a
gray "code" pill, the starting variable) and `.u` (a blue rounded pill, an
intermediate unit/mechanism) — connected by `→` glyphs in muted
`--baseline` color, ending in a bold colored delta (`.d`, red=up/green=down/
gray=flat vs base). This is static narrative structure per persona
(`p.chains` array), only the trailing `.d` value and its up/dn/flat class
are computed live in `render()` (lines 946–953).

### B.7 Attribution card (`.at`)

```html
<div class="at" style="border-bottom:1px solid var(--grid);padding-bottom:4px">
  <span class="an" style="color:var(--ink)">total vs base</span>
  <span class="av up">+0,32</span>
</div>
<div class="at">
  <span class="an">r · Tipo de interés</span>
  <span class="av up">+0,20</span>
  <span class="ab"><i style="width:31.3%;left:50%;"></i></span>
</div>
```

```css
.at { display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 4px 6px;
  font-size: 10px; margin-bottom: 5px; }
.at .an { font-weight: 700; color: var(--ink-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.at .av { font-weight: 800; white-space: nowrap; }
.at .av.up { color: var(--div-neg); } .at .av.dn { color: var(--good); }
.at .ab { grid-column: 1 / 3; height: 4px; border-radius: 3px; background: var(--grid); position: relative; }
.at .ab i { position: absolute; top: 0; bottom: 0; border-radius: 3px; background: var(--lab); }
.at-none { font-size: 10px; color: var(--muted); line-height: 1.4; }
```

This is a **diverging bar chart built from CSS, not SVG**: the bar `.ab`
spans the full row width (`grid-column: 1/3`), and its fill `<i>` is
positioned with `left:50%` plus a signed `transform:translateX(-100%)` for
negative contributions, so bars grow left or right from a shared center
zero-line. Bar length = `|contribution| / max(|contributions|) * 50%` (half
the row width in each direction). Values come from re-running `run()` once
per moved lever (holding all others at BASE) to isolate its marginal effect;
the unexplained remainder is bucketed as `"interacción entre palancas"`
(rendered in a lighter-weight/opacity row, `q.soft`). When no levers have
moved, `.at-none` shows explanatory placeholder copy instead.

### B.8 Narrative block (`.narr`)

```html
<div class="narr">
  <div class="h">✦ Escenario condicional</div>
  <div class="x" id="narr">«Leemos la curva como la lee quien presta…»</div>
  <div class="cite" id="cite">trazado a <code>gold_escenarios_deuda.csv</code></div>
</div>
```

```css
.narr { border-left: 3px solid var(--accent); border-radius: 0 7px 7px 0; padding: 6px 10px;
  background: var(--card); margin-top: 5px; }
.narr .h { font-size: 10px; font-weight: 800; color: var(--accent); }
.narr .x { font-size: 10.5px; color: var(--ink-2); line-height: 1.4; }
.narr .cite { font-size: 9px; color: var(--muted); margin-top: 3px; }
.narr code { font: 9px ui-monospace, Consolas, monospace; background: var(--code);
  padding: 0 4px; border-radius: 3px; }
```

Blockquote-style card: thick colored left border instead of a full outline,
tinted `--card` background, small-caps-weight header with a "✦" glyph
(tagline: "el LLM narra, el sistema calcula" / "✦ Escenario condicional" in
v16). Body text (`.narr .x`) is generated by a per-persona `narr(R, k, y)`
JS function that plugs live scenario numbers into template sentences;
`.cite` names the source gold CSV in a monospace `<code>` chip.

### B.9 Projection chart legend/markers

Legend row above each chart (`render()` lines 914, 922–925):

```html
<div class="legend">
  <span><i style="background:var(--lab)"></i>escenario actual</span>
  <span><s></s>base congelada (vintage)</span>
  <span><i style="background:var(--band-out);height:8px"></i>banda p5–p95 heredada (MC)</span>
  <span><s style="border-color:var(--div-neg)"></s>línea roja</span>
</div>
```

```css
.legend { font-size: 9px; color: var(--ink-2); display: flex; gap: 10px; flex-wrap: wrap; margin: 1px 0 2px; }
.legend i { display: inline-block; width: 9px; height: 3px; border-radius: 2px;
  vertical-align: middle; margin-right: 4px; }
.legend s { display: inline-block; width: 9px; height: 0; border-top: 2px dashed var(--baseline);
  vertical-align: middle; margin-right: 4px; text-decoration: none; }
```

Convention: `<i>` = solid-color swatch (real line), `<s>` = dashed swatch
(base/reference line, using `text-decoration:none` to defeat the browser's
default strikethrough on `<s>`). This directly encodes section D's
"base dotted vs scenario solid" contract at the legend level.

### B.10 Persona card header

v16 (compact, competes with rail + tabs for width):

```html
<div class="head">
  <h1 id="h1">💼 Inversor en bonos: ¿me pagarán los 10 años?</h1>
  <span class="badge-fwd lab" id="seal">🔮 condicional</span>
  <span class="meta" id="meta">ecb_bono10y_es.csv · … · gold_escenarios_deuda.csv</span>
</div>
```
```css
.head { display: flex; align-items: baseline; gap: 8px; flex: 0 0 auto; }
.head h1 { margin: 0; font-size: 17px; font-weight: 800; }
.meta { margin-left: auto; font-size: 9px; color: var(--muted); }
```

v15 (roomier, own top pill nav instead of a lever rail):

```html
<div class="headline">
  <h1>💼 Inversor en bonos: ¿me pagarán los 10 años?</h1>
  <span class="badge-fwd">abanico = proyección MC · condicional</span>
  <span class="meta">ecb_bono10y_es.csv · … · gold_escenarios_deuda_mc.csv</span>
</div>
```
```css
.headline { display: flex; align-items: baseline; gap: 12px; }
.headline h1 { margin: 0; font-size: 20px; }
.headline .meta { margin-left: auto; font-size: 11px; color: var(--muted); }
```

Pattern in both: emoji-prefixed `<h1>` phrased as the persona's central
question, an inline pill badge stating the epistemic status of the whole
page (forecast/retro), and a right-flushed (`margin-left:auto`) small-caps
source-file list as the "meta" trust strip. No separate subtitle element —
the question IS the h1.

---

## C. Layout system

### C.1 Top-level split

```
.app (1680×1080, flex column)
├── .top      — brand + persona tabs + 2 status chips        (flex: 0 0 auto)
├── .body     — flex row, fills remaining height              (flex: 1)
│   ├── .rail — 300px fixed                                   (flex: 0 0 300px)
│   └── .main — everything else                                (flex: 1, min-width: 0)
└── .foot     — app-wide footer strip                          (flex: 0 0 auto)
```

```css
.body { display: flex; flex: 1; min-height: 0; }
.rail { flex: 0 0 300px; border-right: 1px solid var(--grid); background: var(--card);
  padding: 9px 11px; display: flex; flex-direction: column; gap: 7px; overflow: hidden; }
.main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 8px; padding: 9px 12px 0; }
```

`.rail` (v16-only — v15 has no lever panel) stacks, top to bottom: heading
("Palancas · variables independientes (§2.1)") → preset chips → scrollable
lever list (`flex:1; min-height:0`, so it's the one element that would
scroll/clip if levers overflow) → horizon-year buttons (`.horiz`) → a small
"motor declarado" footnote block (`.motor`) spelling out the frozen
calibration constants in prose.

### C.2 Main panel composition (the "5→2→4" pattern)

Exactly the v14 convention ("5 KPI con dial → 2 piezas centrales → semáforo +
cadenas + narrativa"), reused unchanged through v15 and v16:

```css
.outs { display: grid; grid-template-columns: repeat(5, 1fr); gap: 9px; flex: 0 0 auto; }
.row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; flex: 0 0 auto; }
.row3 { display: grid; grid-template-columns: 1.05fr .95fr .95fr 1.2fr; gap: 9px; flex: 1; min-height: 0; }
```

1. `.head` — title bar (§B.10).
2. `.outs` — **5-column** equal-width grid of KPI dial tiles (§B.1).
3. `.row2` — **2-column** equal-width grid: two chart cards (`#chA` historical,
   `#chB` projection).
4. `.row3` — **4-column** grid, uneven widths (`1.05fr .95fr .95fr 1.2fr`,
   narrative card gets the most room): semáforo (`#reds`) · transmisión
   (`#chains`) · atribución (`#attr`) · narrativa (`#narr`/`#cite`).
5. A thin local `.foot` line inside `.main` (not the app-wide footer) shows
   the current horizon year and a live "desviación de nivel del PIB" readout.

v15's equivalent bottom split is `.row2 { grid-template-columns: 1.15fr 1fr .78fr; }`
— only **3** columns (chart · fan chart · semáforo+chain+narr stacked in the
third card), because v15 has no separate attribution card (attribution is a
v16-only feature — it needs the lever-perturbation re-run, which only exists
once there's an interactive engine). A `.row3`-with-4-cards variant does
appear in 3 of the 12 v15 persona files (`04_emprendedor`, `05_funcionario`,
`12_autonomo`), confirming the 4-card layout was already being trialed
per-page in v15 before becoming the v16 standard.

### C.3 Card primitive

```css
.card { border: 1px solid var(--grid); border-radius: 8px; background: var(--surface);
  padding: 7px 10px 8px; display: flex; flex-direction: column; min-width: 0; }
.card h4 { margin: 0 0 3px; font-size: 11px; display: flex; align-items: baseline; gap: 6px; }
.card h4 small { font-weight: 600; color: var(--muted); font-size: 9px; }
.card svg.chart { width: 100%; display: block; }
```

Every `.row2`/`.row3` cell is a `.card`: bordered box, flex column, a
`<h4>` title with an inline muted `<small>` subtitle, then content. `min-width:0`
on both `.card` and its parent grid items is what lets long chart SVGs and
`text-overflow:ellipsis` labels actually shrink instead of blowing out the grid.

### C.4 Responsive / scaling behavior

**Not responsive in the reflow sense.** The canvas is a fixed 1680×1080px
box; on window resize, `fit()` (lines 1002–1006) uniformly scales the whole
`.app` down (never up — `Math.min(1, …)`) to fit the viewport width, via a
CSS transform, and compensates the resulting bottom gap:

```js
function fit() {
  const s = Math.min(1, (window.innerWidth - 24) / 1680);
  $("app").style.transform = "scale(" + s + ")";
  $("app").style.marginBottom = (24 - 1080 * (1 - s)) + "px";
}
window.addEventListener("resize", fit);
```

No CSS media queries alter layout below the fixed size — internal grid
columns/fractions never change; only the overall visual scale does. This is
the one piece of "responsiveness" v16 adds over v15 (which has no `fit()` at
all, being designed purely for one-shot PNG/PDF export at a fixed size).

---

## D. Chart implementation

**Hand-written SVG via JS string concatenation. No canvas, no D3, no
charting library, anywhere in v14/v15/v16.** The two generations differ only
in *when* the SVG markup is produced:

- **v15**: 100% client-JS-free. Coordinates are literal numbers baked
  straight into the HTML by the Python build script at generation time (see
  the full `<polyline points="46.0,148.9 57.0,156.0 …">` example in
  `v15_perfil_01_bonista.html` lines 168–169, 187, 191 — computed once,
  never touched by any script, viewable/printable with JS entirely disabled).
- **v16**: the exact same visual output, but computed **live in the browser**
  every time a lever moves, by the `chart(el, spec)` function.

### D.1 `chart(el, spec)` — the canonical renderer (`v16_perfiles_lab.html` lines 419–469)

```js
function chart(el, spec) {
  const W = 660, H = spec.h || 420, ml = 56, mr = 12, mt = 12, mb = 20;
  const xs = spec.x, n = xs.length;
  let lo = spec.lo, hi = spec.hi;
  if (lo === undefined) {
    const all = spec.lines.flatMap(l => l.v).concat(spec.band ? spec.band.lo.concat(spec.band.hi) : []).filter(isFinite);
    lo = Math.min.apply(null, all); hi = Math.max.apply(null, all);
    const pad = (hi - lo) * 0.16 || 1; lo -= pad; hi += pad;
  }
  const X = i => ml + (W - ml - mr) * (n === 1 ? 0 : i / (n - 1));
  const Y = v => mt + (H - mt - mb) * (1 - (v - lo) / (hi - lo || 1));
  const path = v => v.map((q, i) => (i ? "L" : "M") + X(i).toFixed(1) + " " + Y(q).toFixed(1)).join(" ");
  let s = '<svg class="chart" viewBox="0 0 ' + W + ' ' + H + '" role="img">';
  const ticks = 4;
  for (let t = 0; t <= ticks; t++) {
    const v = lo + (hi - lo) * t / ticks, y = Y(v);
    s += '<line x1="' + ml + '" y1="' + y.toFixed(1) + '" x2="' + (W - mr) + '" y2="' + y.toFixed(1) +
         '" stroke="var(--grid)" stroke-width="1"/>' +
         '<text x="' + (ml - 4) + '" y="' + (y + 3).toFixed(1) + '" text-anchor="end">' +
         nf(v, spec.dec !== undefined ? spec.dec : (hi - lo > 40 ? 0 : 1)) +
         (t === ticks && spec.u ? " " + spec.u : "") + '</text>';
  }
  if (spec.red !== undefined && spec.red >= lo && spec.red <= hi) {
    s += '<line x1="' + ml + '" y1="' + Y(spec.red).toFixed(1) + '" x2="' + (W - mr) + '" y2="' + Y(spec.red).toFixed(1) +
         '" stroke="var(--div-neg)" stroke-width="1" stroke-dasharray="4 3"/>';
  }
  if (spec.band) {
    const up = spec.band.hi.map((q, i) => (i ? "L" : "M") + X(i).toFixed(1) + " " + Y(q).toFixed(1)).join(" ");
    const dn = spec.band.lo.map((q, i) => "L" + X(i).toFixed(1) + " " + Y(q).toFixed(1)).reverse().join(" ");
    s += '<path d="' + up + " " + dn + ' Z" fill="var(--band-out)" opacity=".75"/>';
  }
  spec.lines.forEach(l => {
    s += '<path d="' + path(l.v) + '" fill="none" stroke="' + (l.c || "var(--s1)") + '" stroke-width="' +
         (l.w || 2) + '"' + (l.dash ? ' stroke-dasharray="5 4"' : "") + ' stroke-linejoin="round"/>';
    if (l.dot !== false) {
      const i = l.v.length - 1;
      s += '<circle cx="' + X(i).toFixed(1) + '" cy="' + Y(l.v[i]).toFixed(1) + '" r="3.2" fill="' + (l.c || "var(--s1)") + '"/>';
    }
  });
  (spec.ann || []).forEach(a => {
    s += '<text x="' + X(a.i).toFixed(1) + '" y="' + (Y(a.v) + (a.dy || -8)).toFixed(1) +
         '" class="lbl" text-anchor="' + (a.anch || "middle") + '">' + a.t + '</text>';
  });
  const lab = [0, Math.floor((n - 1) / 2), n - 1];
  lab.forEach((i, j) => {
    s += '<text x="' + X(i).toFixed(1) + '" y="' + (H - 6) + '" text-anchor="' +
         (j === 0 ? "start" : j === 2 ? "end" : "middle") + '">' + xs[i] + '</text>';
  });
  s += "</svg>";
  el.innerHTML = s;
}
```

Key structural facts:
- Fixed logical viewBox `660×420` (spec can override height via `spec.h`),
  margins `ml:56 mr:12 mt:12 mb:20` — left margin is wide to fit y-axis
  number labels.
- `X`/`Y` are simple linear scale closures (`X`: index → px; `Y`: value →
  px, inverted since SVG y grows downward). Domain auto-computed from data
  with a 16% padding if `lo`/`hi` aren't explicitly given.
- Draw order (back to front): 4 horizontal gridlines+labels → optional red
  threshold dashed line → optional uncertainty band (filled closed path, up
  edge forward + down edge reversed to close the polygon) → each line in
  `spec.lines[]` (path + optional end-dot) → optional point annotations →
  3 x-axis labels (first/middle/last only, not one per data point).
- **Base vs scenario line convention** (used by every `hB` "projection"
  chart, `render()` lines 926–931): base/frozen-vintage line first with
  `dash:true, dot:false` (dashed, muted `--baseline` color, no end marker),
  scenario line second, solid, `--lab` magenta, thicker (`w:2.4` vs `w:1.6`),
  **with** an end-dot. This directly implements "base dotted vs scenario line."
- Called twice per render: `chart($("chA"), {...historical spec...})` for the
  observed-data chart (purple `--retro` line, real dates on x-axis) and
  `chart($("chB"), {...projection spec...})` for the lever-driven forecast
  (base dashed + scenario solid, optional MC fan band, year labels 2026–2050).

### D.2 v15's build-time equivalent

Same SVG structure (viewBox `740×300` in v15, slightly different margin
constants), but every `<polyline>`/`<circle>`/`<text>` coordinate is a plain
number written once by the Python build script — no `<script>` tag computes
anything client-side. This is *only* possible because v15 has no levers: one
persona = one fixed scenario = one fixed set of coordinates, forever.

---

## E. Interaction / state

### E.1 State shape

All app state lives in three bare top-level mutable variables (lines 413–414):

```js
let L = Object.assign({}, BASE);   // current lever values, keyed by lever id
let HZ = 2026, CUR = 0;            // selected horizon year, selected persona index
```

`BASE` is the frozen-vintage lever vector (all levers at their observed
2026-07-31 values); `LEVERS` (lines 389–400) and `PRESETS` (lines 402–411)
are static config arrays, e.g.:

```js
const LEVERS = [
  {id:"r", sym:"r", nm:"Tipo de interés · Euríbor 12m", u:"%", min:0, max:6, st:0.05, d:2, src:"ecb_euribor12m.csv · 2026-06"},
  … 9 more …
];
const PRESETS = [
  {id:"S0", nm:"S0 base", set:{}},
  {id:"S7", nm:"S7 adverso", set:{r: BASE.r + 2, pm: 50, prima: 150}},
  … 6 more …
];
```

### E.2 Lever persistence across tabs

Switching persona tabs (`CUR`) or horizon (`HZ`) does **not** reset `L` — the
lever vector is a single shared global, so a scenario built on one persona's
tab stays applied when you jump to another persona's tab. Only the KPIs,
charts, semaphore, chains, attribution, and narrative shown change (each
persona pulls different fields off the same shared `run(L)` result). This is
the core "one engine, many views" principle stated in `v14_00_indice_app.md`
line 27 ("Un solo motor… las palancas repintan todas las páginas").

### E.3 URL-shareable state

```js
function readURL() {
  const q = new URLSearchParams(location.search);
  if (q.has("p")) CUR = Math.max(0, Math.min(P.length - 1, +q.get("p")));
  if (q.has("h")) HZ = Math.max(Y0, Math.min(Y1, +q.get("h")));
  LEVERS.forEach(v => { if (q.has(v.id)) L[v.id] = parseFloat(q.get(v.id)); });
  document.querySelectorAll(".hb").forEach(x => x.classList.toggle("on", +x.getAttribute("data-y") === HZ));
  LEVERS.forEach(v => $("in-" + v.id).value = L[v.id]);
}
function writeURL() {
  const q = new URLSearchParams();
  q.set("p", CUR); q.set("h", HZ);
  LEVERS.forEach(v => { if (Math.abs(L[v.id] - BASE[v.id]) > 1e-9) q.set(v.id, L[v.id]); });
  history.replaceState(null, "", "?" + q.toString());
}
```

`writeURL()` runs at the end of every `render()` call — the query string is
kept in sync live, using `history.replaceState` (no history-stack spam, no
navigation, no reload). Only *non-base* lever values are written (`p`=persona
index, `h`=horizon year, then one short param per moved lever id) so a
"scenario = base" URL is just `?p=0&h=2026`. There is no server-side
persistence, no accounts, no saved-scenario list — sharing = copying the URL.

### E.4 What re-renders on a lever move

Every `<input type=range>` fires the **entire** `render()` function on
`input` (line 818–820: `L[v.id] = parseFloat(e.target.value); render();`) —
there is no incremental/partial update, no memoization, no virtual-DOM diff.
`render()` (lines 872–985) does, in order: re-runs the engine twice
(`run(L)` and `run(BASE)`) for the full horizon range, rewrites `railState()`
(lever value labels + hot/moved classes + preset match), rewrites the h1/
badge/meta/footer text, fully replaces `#outs`, `#chA`, `#chB`, `#reds`,
`#chains`, `#attr`, `#narr`/`#cite` innerHTML, then calls `writeURL()`.
Every dynamic region is a plain `el.innerHTML = "<string>…"` replace built
via array `.map().join("")` template strings — no component framework.

### E.5 Transitions / animation

Essentially none. Grepping every `<style>` block in v16 turns up exactly
**one** CSS `transition` in the whole file — the KPI gauge fill:
`.gaugebar .f { transition: width .18s ease; }` — and **zero** `@keyframes`
anywhere. So a lever drag causes the gauge bars to animate their width over
180ms, while literally everything else (numbers, chart SVGs, chip states,
badges, semaphore colors) snaps instantly on the next `render()` paint.

### E.6 Init sequence

```js
buildRail();   // builds lever/preset/tab DOM once, wires all event listeners
readURL();     // applies any ?p=&h=&<lever>= params over BASE/defaults
render();      // first paint
fit();         // apply initial viewport scale
window.addEventListener("resize", fit);
```

---

## F. What NOT to carry over

These are v16-specific workarounds for being a single, offline, static HTML
file — they should NOT be replicated in the new API-backed frontend:

1. **The entire embedded-data build pipeline.** `build_v16.py` reads
   `data/kpis_perfiles.json` + gold CSVs, runs Python-side calibration
   (including a binary-search-solved implicit mortgage differential via a
   French-amortization helper), assembles one big `payload` dict, and does a
   literal string substitution of `_v16_template.html`'s
   `const D = /*__DATA__*/null;` placeholder with the full JSON blob —
   producing a ~90KB self-contained HTML file with the entire dataset
   inlined in a `<script>` tag. The new frontend should fetch this over a
   real API, not bake it into the page source.
2. **Single hardcoded country + single frozen vintage.** Everything assumes
   Spain ("ES") and vintage `2026-07-31` baked at build time; there is no
   country selector, no vintage selector, no concept of comparing vintages.
   Multi-country/multi-vintage needs to be a first-class API parameter, not
   a rebuild.
3. **Zero network calls, ever.** No `fetch`, no XHR, nothing — by design,
   since it has to run as a `file://` URL for the screenshot/PDF pipeline.
   The new frontend obviously needs to talk to a real backend.
4. **Fixed 1680×1080 canvas + `transform: scale()` "fit."** This is
   screenshot/print-driven layout, not responsive design. `fit()`
   uniformly shrinks the whole app rather than reflowing columns/breakpoints
   — fine for a maquette meant to be rendered to PNG/PDF at one fixed size,
   wrong for a real multi-device web app. The 5/2/4-column grid ratios are
   worth keeping as a *content* pattern; the fixed-canvas-plus-scale
   mechanism is not.
5. **URL-query-string-only state, no persistence.** No accounts, no saved
   scenarios, no server-synced state — sharing a scenario means copying a
   URL with `?p=&h=&r=&prima=…` params. A real product will likely want
   actual scenario persistence (saved/named scenarios, user accounts)
   alongside (not necessarily instead of) shareable links.
6. **Full non-incremental re-render via `innerHTML` string concatenation.**
   Every `render()` call rebuilds ~7 DOM subtrees from scratch by
   `.map().join("")`-ing raw HTML strings (including numbers interpolated
   directly into markup with no escaping — safe here only because all data
   is trusted/build-time, not user input). A reactive framework (React/Vue/
   Svelte/etc.) doing targeted updates is the obvious, correct replacement
   — but the *visual result* it should reproduce (which regions redraw
   together, what stays static) is exactly what `render()`'s structure
   documents.
7. **Bare global mutable state (`L`, `CUR`, `HZ`).** Three top-level `let`s
   with no encapsulation, no reducer, no store. Fine for a 1000-line
   single-file prototype; should become proper app state (store/context/URL
   router state) in the real build — though the *shape* of that state
   (lever vector + persona index + horizon year, with only non-base levers
   serialized to the URL) is worth preserving as-is.
8. **v15's build-time-baked SVG coordinates.** v15's polylines/circles are
   literal numbers computed once in Python for one specific vintage's data —
   not reusable, not parametrized. The *drawing algorithm* (`chart()`'s
   scale-and-path logic) is exactly what should be ported to the new
   frontend (as a component, ideally still hand-rolled SVG rather than
   pulling in a charting library, to keep the same visual language); the
   baked numbers themselves are throwaway.
9. **Hardcoded `es-ES` locale formatting with no i18n layer.** `nf`/`sg`/`eur`
   call `Intl.NumberFormat("es-ES", …)` directly inline everywhere. Keep the
   decimal-comma/tabular-nums *look*, but route it through a proper i18n/
   locale settings mechanism rather than a hardcoded literal if the new
   frontend needs to support more than one locale.
10. **No accessibility beyond `role="img"` on charts.** SVGs get `role="img"`
    but no `aria-label`/`<title>` (v15 does add `aria-label` on some;
    v16 does not). No focus management, no keyboard-only lever control
    beyond native `<input type=range>` semantics. Worth actually addressing
    properly in the new build rather than copying as-is.
