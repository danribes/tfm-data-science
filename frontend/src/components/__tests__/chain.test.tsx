import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Chain } from "../Chain";
import { baseline, runScenario } from "../../engine/spain";
import { BASE_LEVERS } from "../../engine/vintage";

const specs = [
  { a: "tipo BCE", u: "Euríbor", t: "coste de refinanciación", k: "int" as const, d: 1, un: "%PIB" },
];

describe("Chain — trailing delta computed vs base", () => {
  it("flat at base", () => {
    render(<Chain specs={specs} scn={baseline()} base={baseline()} k={0} />);
    expect(screen.getByText(/\(\+0,0\)/)).toHaveClass("d", "flat");
  });

  it("r +200pb raises int → .up (red)", () => {
    const scn = runScenario({ ...BASE_LEVERS, r: 4.8 });
    render(<Chain specs={specs} scn={scn} base={baseline()} k={24} />);
    const d = document.querySelector(".ch .d")!;
    expect(d.className).toContain("up");
    expect(d.textContent).toMatch(/%PIB \(\+/);
  });
});
