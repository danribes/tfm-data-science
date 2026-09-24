import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/** Grid columns must be able to shrink below their content.
 *
 *  A bare `1fr` track has an automatic minimum: it never gets narrower than the
 *  widest thing inside it. One one-line badge made every KPI tile at least
 *  270 px, and persona pages scrolled sideways from 1025 to 1250 px and from
 *  1441 to 1821 px; Inicio forced four such columns inline and was 528 px wide
 *  on a 390 px phone. `minmax(0, 1fr)` lets the track shrink and the content
 *  wrap. jsdom does not lay anything out, so the check reads the sources. */

const SRC = join(__dirname, "..", "..");
const CSS = readFileSync(join(SRC, "styles", "base.css"), "utf-8");

function tsxFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) return name === "__tests__" ? [] : tsxFiles(p);
    return p.endsWith(".tsx") ? [p] : [];
  });
}

describe("grid tracks can shrink", () => {
  it("the KPI and row grids use minmax(0, …) in every breakpoint", () => {
    const decls = [...CSS.matchAll(/\.(outs|row2|row3)[^{]*\{[^}]*grid-template-columns:\s*([^;]+);/g)];
    expect(decls.length).toBeGreaterThan(4);
    for (const [, sel, cols] of decls) {
      const bare = cols.replace(/minmax\([^)]*\)/g, "");
      expect(bare, `.${sel}: ${cols}`).not.toMatch(/\d*\.?\d+fr/);
    }
  });

  it("no component forces a column count with an inline style", () => {
    for (const file of tsxFiles(SRC)) {
      const src = readFileSync(file, "utf-8");
      expect(src, file).not.toMatch(/gridTemplateColumns:\s*["'`]repeat\(\d+,\s*1fr\)/);
    }
  });
});
