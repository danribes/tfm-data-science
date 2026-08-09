import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/** Every state modifier a component asks for must exist in the stylesheet.
 *
 *  This exists because of a bug it would have caught. Two routes rendered
 *  `class="st crossed"` while the stylesheet only defines `.st.cross`, so the
 *  verdict badge — the single most important element on both pages — rendered
 *  as plain grey text for weeks. The component tests asserted
 *  `className).toContain("crossed")` and passed the whole time: they were
 *  checking that the string was written, not that it meant anything.
 *
 *  jsdom does not load the stylesheet, so no amount of render-testing catches
 *  this. Reading both files and comparing is crude and it works.
 */

const SRC = join(__dirname, "..", "..");
const CSS = readFileSync(join(SRC, "styles", "base.css"), "utf-8");

function tsxFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) return name === "__tests__" ? [] : tsxFiles(p);
    return p.endsWith(".tsx") ? [p] : [];
  });
}

/** Modifiers defined for a base class, e.g. `st` → {cross, near, safe, sd}. */
function definedFor(base: string): Set<string> {
  const out = new Set<string>();
  for (const m of CSS.matchAll(new RegExp(`\\.${base}\\.([a-z0-9-]+)`, "g"))) {
    out.add(m[1]);
  }
  return out;
}

/** Modifiers a component asks for in `className="base modifier"`. */
function usedFor(base: string): Map<string, string[]> {
  const out = new Map<string, string[]>();
  for (const file of tsxFiles(SRC)) {
    const src = readFileSync(file, "utf-8");
    for (const m of src.matchAll(new RegExp(`["'\`]${base} ([a-z0-9-]+)["'\`]`, "g"))) {
      out.set(m[1], [...(out.get(m[1]) ?? []), file.slice(SRC.length + 1)]);
    }
  }
  return out;
}

describe("stylesheet · los modificadores que se usan existen", () => {
  it.each(["st", "band-cal", "banner"])(
    "every .%s modifier used in a component is defined in base.css",
    (base) => {
      const defined = definedFor(base);
      const missing = [...usedFor(base)]
        .filter(([mod]) => !defined.has(mod))
        .map(([mod, files]) => `.${base}.${mod} (${files.join(", ")})`);
      expect(missing, `sin definir en base.css: ${missing.join(" · ")}`).toEqual([]);
    },
  );

  it("the semaphore states a reader depends on are all styled", () => {
    // Named explicitly: these four carry the safe/near/crossed meaning across
    // the whole app, and losing one silently turns a warning into grey text.
    const st = definedFor("st");
    for (const state of ["cross", "near", "safe", "sd"]) {
      expect(st, `falta .st.${state}`).toContain(state);
    }
  });

  it("a row marked out of scope actually dims its cells", () => {
    // `.dim` on a <tr> does nothing unless the rule reaches the <td>, where the
    // colour lives. Prediccion greys the horizons outside the win rule this way.
    expect(CSS).toMatch(/\.guide-t\s+tr\.dim\s+td\s*\{/);
  });
});
