import { describe, expect, it } from "vitest";
import { nf, sg, eur, sgUnit, deltaUnit } from "../fmt";

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

describe("sgUnit — un cambio se dice en su propia unidad", () => {
  it("a percentage moves in puntos, not in %", () => {
    // 23,4 % → 21,5 %: «−1,9 %» would read as a relative fall.
    expect(sgUnit(-1.9, 1, "%")).toBe("−1,9 puntos");
    expect(sgUnit(0.4, 1, "% a/a")).toBe("+0,4 puntos");
  });
  it("a share of GDP moves in puntos de PIB", () => {
    expect(sgUnit(5.9, 1, "%PIB")).toBe("+5,9 puntos de PIB");
    expect(deltaUnit("%PIB")).toBe("puntos de PIB");
  });
  it("everything else keeps its unit; an index has none", () => {
    expect(sgUnit(-4784, 0, "€")).toBe("−4.784 €");
    expect(sgUnit(60, 0, "pb")).toBe("+60 pb");
    expect(sgUnit(-17.5, 1, "")).toBe("−17,5");
  });
  it("an integer change of one is «punto», singular", () => {
    expect(sgUnit(1, 0, "% neto")).toBe("+1 punto");
    expect(sgUnit(-1.2, 0, "%PIB")).toBe("−1 punto de PIB");
    expect(sgUnit(2, 0, "% neto")).toBe("+2 puntos");
    expect(sgUnit(1, 1, "%")).toBe("+1,0 puntos");
  });
});
