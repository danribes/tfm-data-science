import { describe, expect, it } from "vitest";
import { SHIPPED_IDS } from "../registry";
import { outcomeFor, sorna, upIsBadFor } from "../sorna";

describe("sorna — the ironic line, persona by persona", () => {
  it("every shipped persona has a line for better, worse and no change", () => {
    for (const id of SHIPPED_IDS) {
      for (const [delta, word] of [[+5, "mejor"], [-5, "peor"], [0, "igual"]] as const) {
        // «g» up is good for everyone, so its sign picks the outcome directly.
        const line = sorna(id, "g", delta, 1, 2050);
        expect(line, `${id}/${word}`).toBeTruthy();
      }
    }
  });

  it("a better or worse line states its condition, so irony never reads as a forecast", () => {
    for (const id of SHIPPED_IDS) {
      for (const delta of [+5, -5]) {
        expect(sorna(id, "g", delta, 1, 2050)).toMatch(/^Si en 2050 las cosas quedan así/);
      }
    }
  });

  it("reads each series from the side of whoever asks", () => {
    expect(upIsBadFor("03", "precio")).toBe(true);   // dearer house, bad for the buyer
    expect(upIsBadFor("02", "ipv")).toBe(false);     // dearer house, better collateral
    expect(upIsBadFor("09", "pens")).toBe(false);    // pensions that keep up: good for the retiree
    expect(upIsBadFor("06", "pens")).toBe(true);     // the same bill, bad for the politician
    expect(outcomeFor("10", "ujuv", -1.9, 1)).toBe("mejor");
    expect(outcomeFor("10", "ujuv", +1.9, 1)).toBe("peor");
  });

  it("a change that rounds to zero is no change", () => {
    expect(outcomeFor("05", "d1", 0.004, 2)).toBe("igual");
    expect(outcomeFor("05", "d1", 0.006, 2)).toBe("mejor");
  });

  it("says nothing when it does not know who asked", () => {
    expect(sorna(undefined, "u", 1, 1, 2050)).toBeUndefined();
    expect(sorna("99", "u", 1, 1, 2050)).toBeUndefined();
  });
});
