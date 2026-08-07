import { describe, expect, it } from "vitest";
import { baseline, runScenario } from "../spain";
import { BASE_LEVERS } from "../vintage";
import { STATUS_LABEL, evaluatePersonaReds, evaluateRedlines, statusOf } from "../redlines";

describe("statusOf — 10% near band, 0.5pp band at zero thresholds (spec §4.5)", () => {
  it("crossed / near / safe for gt", () => {
    expect(statusOf(7.5, 7.0, "gt")).toBe("crossed"); // Bono 10A > 7
    expect(statusOf(6.5, 7.0, "gt")).toBe("near"); // |6.5−7| = 0.5 ≤ 0.7
    expect(statusOf(3.42, 7.0, "gt")).toBe("safe");
  });
  it("crossed / near / safe for lt (Déficit > 3 % PIB is saldo < −3)", () => {
    expect(statusOf(-3.5, -3.0, "lt")).toBe("crossed");
    expect(statusOf(-2.8, -3.0, "lt")).toBe("near"); // band 0.3
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
    expect(out[0].value).toBeCloseTo(9.8, 9); // 12.8 − 3.0
    expect(out[0].status).toBe("near"); // |9.8 − 10| = 0.2 ≤ 1.0
  });
  it("persona 07 null rows come back s/d, no crash", () => {
    const reds = [{ t: "WGI control de la corrupción", thr: null, k: null, cmp: null, d: null, x: "API archivada [hueco de datos]" }];
    const out = evaluatePersonaReds(reds, runScenario({ ...BASE_LEVERS }), 0);
    expect(out[0].status).toBe("sd");
    expect(out[0].value).toBeNull();
  });
});
