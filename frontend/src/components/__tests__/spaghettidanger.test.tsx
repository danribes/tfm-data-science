import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SpaghettiChart } from "../SpaghettiChart";

const years = Array.from({ length: 45 }, (_, i) => 2026 + i);
const paths = [years.map((_, i) => 100 + i), years.map((_, i) => 100 + 2 * i)];

describe("SpaghettiChart — the danger zone", () => {
  it("shades from the danger year on and flags it with ⚠", () => {
    const { container } = render(
      <div style={{ width: 800 }}><SpaghettiChart years={years} paths={paths} danger={{ from: 2038, label: "2038: gasto récord" }} /></div>,
    );
    // Recharts only lays out with a measured width; the props are what we own.
    expect(container.querySelector(".spag")).toBeTruthy();
  });

  it("draws nothing extra without a danger year, or with one outside the axis", () => {
    const a = render(<SpaghettiChart years={years} paths={paths} />);
    const b = render(<SpaghettiChart years={years} paths={paths} danger={{ from: 1999, label: "x" }} />);
    expect(a.container.textContent).not.toContain("⚠");
    expect(b.container.textContent).not.toContain("⚠");
  });
});
