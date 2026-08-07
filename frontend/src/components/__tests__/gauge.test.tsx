import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Gauge, dialDomain } from "../Gauge";

describe("Gauge — flat v16 dial bar", () => {
  it("fill width is value normalized to [lo,hi]", () => {
    const { container } = render(
      <Gauge value={106.3} lo={100} hi={130} base={106.3} red={120} redCmp="gt" />,
    );
    const fill = container.querySelector(".gaugebar .f") as HTMLElement;
    expect(fill.style.width).toBe("21%"); // (106.3−100)/30 = 0.21
  });

  it("crossed threshold → .bad, within 10% |thr| → .warn2, else default", () => {
    const bad = render(
      <Gauge value={121} lo={100} hi={130} base={106} red={120} redCmp="gt" />,
    ).container;
    expect(bad.querySelector(".f")!.className).toContain("bad");

    const warn = render(
      <Gauge value={112} lo={100} hi={130} base={106} red={120} redCmp="gt" />,
    ).container;
    expect(warn.querySelector(".f")!.className).toContain("warn2"); // |112−120| = 8 ≤ 12

    const ok = render(
      <Gauge value={104} lo={100} hi={130} base={106} red={120} redCmp="gt" />,
    ).container;
    expect(ok.querySelector(".f")!.className).not.toContain("bad");
    expect(ok.querySelector(".f")!.className).not.toContain("warn2");
  });

  it("renders baseline tick and red tick at normalized positions", () => {
    const { container } = render(
      <Gauge value={110} lo={100} hi={130} base={106} red={120} redCmp="gt" />,
    );
    expect((container.querySelector(".bm") as HTMLElement).style.left).toBe("20%");
    expect((container.querySelector(".rl") as HTMLElement).style.left).toBe("66.67%");
  });

  it("dialDomain pads min/max by 16% and includes the red line", () => {
    const [lo, hi] = dialDomain([100, 110], 120);
    expect(lo).toBeCloseTo(100 - 20 * 0.16, 9);
    expect(hi).toBeCloseTo(120 + 20 * 0.16, 9);
  });
});
