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
