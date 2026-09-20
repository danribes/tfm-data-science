import { describe, expect, it } from "vitest";
import { BASE_LEVERS, CENTRAL, V0 } from "../vintage";
import { IPV_LR, IPV_REV } from "../constants";
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
  it("a zero-interest loan repays only principal", () => {
    expect(french(120000, 0, 300)).toBe(400);
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
  it.each(PRESETS.map((p) => p.id))("%s fiscal flows match independently reconstructed nominal accounts", (presetId) => {
    const run = runScenario(presetLevers(presetId));
    let nominalGdp = 100;
    let nominalDebt = CENTRAL[Y0 - 1].deuda;
    for (let k = 0; k < N_YEARS; k++) {
      nominalGdp *= 1 + run.gnom[k] / 100;
      const interestPayment = nominalDebt * run.ief[k] / 100;
      const primarySurplus = run.pb[k] * nominalGdp / 100;
      const overallSurplus = primarySurplus - interestPayment;
      nominalDebt -= overallSurplus;
      // Current-GDP accounting intentionally corrects the original v16 pins.
      expect(run.int[k]).toBeCloseTo(100 * interestPayment / nominalGdp, 10);
      expect(run.saldo[k]).toBeCloseTo(100 * overallSurplus / nominalGdp, 10);
      expect(run.b[k]).toBeCloseTo(100 * nominalDebt / nominalGdp, 10);
      expect(run.deficitAbs[k]).toBeCloseTo(Math.max(0, -100 * overallSurplus / nominalGdp), 10);
    }
  });
  it("annual housing reversion removes the declared fraction of the growth gap", () => {
    const gap = V0.ipv - IPV_LR;
    expect(base.ipv[0]).toBeCloseTo(V0.ipv, 12);
    expect(base.ipv[1] - IPV_LR).toBeCloseTo(gap * (1 - IPV_REV), 12);
    expect(base.ipv[2] - IPV_LR).toBeCloseTo(gap * (1 - IPV_REV) ** 2, 12);
    expect(base.precio[0]).toBe(V0.precio);
    expect(base.precio[1]).toBeCloseTo(V0.precio * (1 + base.ipv[1] / 100), 9);
  });
  it("bono = r + TERM + prima/100 (base: 2.8 + 0.17 + 0.45 = 3.42)", () => {
    const s1 = runScenario({ ...BASE_LEVERS, r: 4.8 });
    expect(s1.bono[0]).toBeCloseTo(4.8 + 0.17 + 0.45, 9);
  });
});
