# Phase-2 handoff notes (from phase-1 final review, 2026-08-07)

Binding items the phase-2 (HTML front + JS engine) spec must address, carried
from the phase-1 whole-branch review and task ledger:

1. **MC engine home.** Decide client-side vs server-side Monte Carlo. If
   client-side JS: `/constants` cannot currently express `MC_PB_DRIFT`
   (3-tuple) or `MC_EXT_SLOPE_*` — extend `ConstantOut.value` to
   `float | list[float]` FIRST, then harden the contract. If server-side:
   the gap is display-only (rail shows MC constants from docs).
2. **JS MC acceptance rule.** NumPy PCG64 draws are not reproducible in JS.
   The JS fan's acceptance test is the gold envelope ±2pp at 2030/2050/2070
   (`data/gold/gold_escenarios_deuda_mc.csv`), NOT the fixture's seed-42 pins
   (those bind the Python engine only).
3. **`ipvreal` is a derived display series.** Persona 02's red references
   series `ipvreal`, which the engine does not emit — v16's front derived it
   as `ipv − pi` at render time. The phase-2 front must derive it the same
   way, or a faithful consumer of the persona config KeyErrors.
4. **`/scenario` returns full 2026-2050 series regardless of `horizon`** —
   horizon selects only the red-line evaluation year. The front must not
   truncate twice.
5. **Persona display reds ≠ global RED_LINES.** Persona-level `reds` (in the
   `/personas` payload) are v16-verbatim display thresholds (e.g.
   "Sobrecarga > 40% renta" with threshold 15.0 on series `sobre` — label
   cites the Eurostat 40%-of-income overburden DEFINITION, threshold is 15%
   of population). Do not reconcile them with `/redlines`.
6. **Dual-engine contract.** The JS engine must reproduce
   `tests/fixtures/engine_anchors.json`: `debt_central`, `cuota_2026_base`,
   `presets_series_2035_2050` (7 series × 8 presets), `probe_bundle`
   (all-10-lever scenario), `base_gold_identity` — everything except the
   `montecarlo_seed42` block (see item 2).

Cheap hardening candidates (non-blocking, fold into any future touch):
- Consistency test: `api/schemas.LeverValues` defaults/bounds vs
  `engine.levers.LEVER_SPECS`/`BASE_LEVERS` (8 of 10 defaults + all bounds
  are deliberate literals in the frozen contract today).
- Sync test: `engine/montecarlo.mc_input_paths` ief/gnom vs `engine.spain`
  over 2026-2050 (and pb equal ex-`MC_PB_DRIFT`).
- `engine/redlines._ZERO_THRESHOLD_BAND` currently unused (defensive).
- `api/main.py` hardcodes 2026 in the MC endpoint; `ScenarioRequest.horizon`
  bounds hardcode 2026/2050 vs `Y0/Y1`.
- `DiskCache("data_cache")` is CWD-relative, no TTL (inherited MVP behavior).
