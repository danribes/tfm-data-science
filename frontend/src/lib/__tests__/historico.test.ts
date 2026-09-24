import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { GTOT_RECORD, INT_RECORD, recordCrossing } from "../historico";
import { baseline, runScenario, YEARS } from "../../engine/spain";
import { BASE_LEVERS } from "../../engine/vintage";

const ITEMS = ["pens", "int", "d1", "p2", "edu", "p51", "d3"] as const;

describe("gasto total — crece con pensiones e intereses", () => {
  it("starts at the observed 45,4 and grows exactly with pensions and interest", () => {
    const s = baseline();
    expect(s.gtot[0]).toBeCloseTo(45.4, 6);
    for (let k = 1; k < YEARS.length; k++) {
      const grown = (s.pens[k] - s.pens[0]) + (s.int[k] - s.int[0]);
      expect(s.gtot[k] - s.gtot[0]).toBeCloseTo(grown, 9);
    }
  });

  it("the seven items never add up to more than the total, whatever the levers", () => {
    for (const levers of [BASE_LEVERS, { ...BASE_LEVERS, r: 6, dem: 1, idx: 1 }, { ...BASE_LEVERS, sp: 4 }, { ...BASE_LEVERS, sp: -4, r: 0 }]) {
      const s = runScenario(levers);
      YEARS.forEach((y, k) => {
        const sum = ITEMS.reduce((a, key) => a + s[key][k], 0);
        expect(sum, `${y}`).toBeLessThan(s.gtot[k]);
      });
    }
  });
});

describe("GTOT_RECORD — el récord del gasto público", () => {
  it("matches the frozen vintage it was taken from", () => {
    const gold = JSON.parse(readFileSync(resolve(__dirname, "../../../../data/gold/kpis_perfiles.json"), "utf8"));
    const pts: [string, number][] = gold.series.gasto_total_pib_hist.puntos;
    const [year, value] = pts.reduce((m, p) => (p[1] > m[1] ? p : m));
    expect({ value, year: Math.round(Number(year)) }).toEqual(GTOT_RECORD);
  });

  it("the interest record matches the frozen vintage too", () => {
    const gold = JSON.parse(readFileSync(resolve(__dirname, "../../../../data/gold/kpis_perfiles.json"), "utf8"));
    const pts: [string, number][] = gold.series.intereses_deuda_hist.puntos;
    const [year, value] = pts.reduce((m, p) => (p[1] > m[1] ? p : m));
    expect({ value, year: Math.round(Number(year)) }).toEqual(INT_RECORD);
  });

  it("the base scenario passes it in 2038, and cutting the deficit delays it", () => {
    expect(recordCrossing(YEARS, baseline().gtot)).toBe(2038);
    const cut = recordCrossing(YEARS, runScenario({ ...BASE_LEVERS, sp: 3 }).gtot);
    expect(cut === null || cut > 2038).toBe(true);
  });
});
