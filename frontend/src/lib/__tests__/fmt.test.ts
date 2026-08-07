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
