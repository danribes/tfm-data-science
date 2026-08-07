import { describe, expect, it } from "vitest";
import anchors from "@fixtures/engine_anchors.json";
import { BASE_LEVERS } from "../vintage";
import { presetLevers, type Levers } from "../levers";
import { Y0, baseline, runScenario } from "../spain";

/** All ten levers moved at once — verbatim from tests/test_anchors.py PROBE. */
const PROBE: Levers = {
  r: 4.8,
  prima: 150.0,
  sp: 1.0,
  lam: 1.4,
  pm: 50.0,
  tau: 1.5,
  z: -1.0,
  ext: 3.0,
  dem: 0.6,
  idx: -0.5,
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
      // fixture stores round(value, 4); round the TS value to the same grain first.
      expect(Math.abs(Math.round(scn.b[idx(2050)] * 1e4) / 1e4 - pin)).toBeLessThanOrEqual(1e-6);
    }
  });

  it("A4 presets_series_2035_2050: 8 presets × 7 series × 2 years ± 1e-6", () => {
    // e.g. S1 2035: u 10.699724 · pi 2.711975 · wrealIdx 106.847929 · cuota 851.980821
    //              · esf 35.70086 · pens 16.6086 · saldo −10.687951
    for (const [pid, byYear] of Object.entries(anchors.presets_series_2035_2050)) {
      const scn = runScenario(presetLevers(pid));
      for (const [year, series] of Object.entries(byYear)) {
        const pins = series as Record<string, number>;
        for (const key of PINNED_SERIES) {
          expect(
            Math.abs(Math.round(scn[key][idx(year)] * 1e6) / 1e6 - pins[key]),
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
    // 2026: ief 2.68 · gnom 3.3 · pb −1.35 · 2050: ief 3.47 · gnom 3.3 · pb −7.47
    const base = baseline();
    for (const [year, rows] of Object.entries(anchors.base_gold_identity)) {
      const k = idx(year);
      const r = rows as Record<string, { engine: number }>;
      expect(Math.abs(base.ief[k] - r.ief.engine)).toBeLessThanOrEqual(1e-9);
      expect(Math.abs(base.gnom[k] - r.gnom.engine)).toBeLessThanOrEqual(1e-9);
      expect(Math.abs(base.pb[k] - r.pb.engine)).toBeLessThanOrEqual(1e-9);
    }
  });

  it("montecarlo_seed42 deliberately NOT asserted (NumPy PCG64 draws are not reproducible in JS)", () => {
    // The Monte Carlo block exists in the fixture (so Metodología's claim about it stays true),
    // but its draws are generator/platform-specific — they are never replayed against the TS
    // engine. The real MC acceptance rule per the phase-1 handoff note: the gold envelope
    // ±2 pp, checked against the API response (server-computed), not against a JS reproduction
    // of the NumPy seed. This test only guards that the fixture still ships the block.
    expect(anchors.montecarlo_seed42["2050"].p50).toBeCloseTo(231.2999, 4);
  });

  it("probe differs from BASE on every lever (probe is a real all-lever move)", () => {
    // r: 4.8 vs 2.8, prima: 150 vs 45, sp: 1 vs 0, lam: 1.4 vs 0.9, pm: 50 vs 0,
    // tau: 1.5 vs 0, z: -1 vs 0, ext: 3 vs 1.8, dem: 0.6 vs 0, idx: -0.5 vs 0
    for (const id of Object.keys(PROBE) as (keyof Levers)[]) {
      expect(Math.abs(PROBE[id] - BASE_LEVERS[id])).toBeGreaterThan(1e-9);
    }
  });
});
