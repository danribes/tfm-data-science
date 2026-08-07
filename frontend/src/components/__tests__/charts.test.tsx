import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProjectionChart } from "../ProjectionChart";
import { FanChart } from "../FanChart";
import { YEARS, baseline, runScenario } from "../../engine/spain";
import { BASE_LEVERS } from "../../engine/vintage";
import { mockPercentiles } from "../../test/msw/fixtures";

describe("ProjectionChart — dotted base, solid scenario, red ReferenceLine", () => {
  it("renders two line paths and a reference line", () => {
    const scn = runScenario({ ...BASE_LEVERS, r: 4.8 });
    const { container } = render(
      <ProjectionChart years={YEARS} baseline={baseline().b} scenario={scn.b}
        redLines={[{ value: 120, label: "Deuda > 120 % PIB" }]} unit="%PIB" dec={1} />,
    );
    const curves = container.querySelectorAll("path.recharts-curve");
    expect(curves.length).toBeGreaterThanOrEqual(2);
    const dashed = Array.from(curves).filter((p) => p.getAttribute("stroke-dasharray"));
    expect(dashed.length).toBeGreaterThanOrEqual(1); // the frozen-vintage baseline
    expect(container.querySelectorAll(".recharts-reference-line").length).toBe(1);
    expect(container.textContent).toContain("base congelada (vintage)");
    expect(container.textContent).toContain("escenario actual");
  });
});

describe("FanChart — p5–p95, p25–p75, p50 (MC fan is server data)", () => {
  it("renders two bands and a median line from fixture-pinned percentiles", () => {
    const years = Array.from({ length: 45 }, (_, i) => 2026 + i);
    const { container } = render(<FanChart years={years} percentiles={mockPercentiles(years)} />);
    expect(container.querySelectorAll("path.recharts-area-area").length).toBe(2);
    expect(container.querySelectorAll("path.recharts-curve").length).toBeGreaterThanOrEqual(3);
    expect(container.textContent).toContain("banda p5–p95");
  });
});
