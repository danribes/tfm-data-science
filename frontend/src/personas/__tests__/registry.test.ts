import { describe, expect, it } from "vitest";
import { SHIPPED_IDS, getPersonaModule } from "../registry";
import { baseline } from "../../engine/spain";
import { mockPersonaCards } from "../../test/msw/fixtures";

/** Every shipped persona, exercised against the real engine output.
 *
 *  These are cheap and they cover the failure that ships silently: a persona
 *  whose chain names a series the engine does not produce renders `undefined`
 *  into its narration, or throws on the page and nowhere else. Eight personas
 *  went in with no test at all; a per-id loop means the next one cannot.
 */
describe("personas · registry", () => {
  const R = baseline() as unknown as Record<string, number[]>;

  it("ships a module for every declared id", () => {
    for (const id of SHIPPED_IDS) {
      expect(getPersonaModule(id), `persona ${id}`).toBeDefined();
    }
    expect(SHIPPED_IDS.length).toBe(new Set(SHIPPED_IDS).size);
  });

  it("agrees with the set the server serves", () => {
    // The registry decides what renders; the API decides what data arrives. If
    // they disagree, a persona is either invisible or a blank page.
    expect(SHIPPED_IDS).toEqual(mockPersonaCards.map((c) => c.id));
  });

  it.each(SHIPPED_IDS)("persona %s names only series the engine produces", (id) => {
    const m = getPersonaModule(id)!;
    for (const ch of m.chains) {
      expect(Object.keys(R), `${id}: cadena "${ch.t}"`).toContain(ch.k);
    }
  });

  it.each(SHIPPED_IDS)("persona %s narrates without throwing or printing undefined", (id) => {
    const m = getPersonaModule(id)!;
    const text = m.narr(R as never, 4, 2030);
    expect(text.length).toBeGreaterThan(40);
    expect(text).not.toMatch(/undefined|NaN/);
  });

  it.each(SHIPPED_IDS)("persona %s cites its source", (id) => {
    expect(getPersonaModule(id)!.cite).toBeTruthy();
  });
});
