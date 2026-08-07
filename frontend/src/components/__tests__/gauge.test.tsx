import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Gauge, dialDomain } from "../Gauge";
import { statusOf } from "../../engine/redlines";

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

  it("agrees with statusOf on a zero threshold (the g < 0 case)", () => {
    // Regression guard for the two-implementations bug: the dial used to
    // re-derive its own near-band, giving 0.1 absolute at thr = 0 where
    // statusOf uses ZERO_THRESHOLD_BAND = 0.5. Values in (0.1, 0.5] were
    // amber in the semáforo and green on the dial — same card, same number.
    // Persona 04 ships `thr: 0.0` reds, so this must stay in agreement.
    for (const value of [-0.4, 0.05, 0.3, 0.5, 0.9]) {
      const { container } = render(
        <Gauge value={value} lo={-2} hi={3} base={1.8} red={0} redCmp="lt" />,
      );
      const cls = container.querySelector(".f")!.className;
      const expected = { crossed: "bad", near: "warn2", safe: "ok", sd: "" }[
        statusOf(value, 0, "lt")
      ];
      expect(cls, `value ${value}`).toContain(expected);
    }
    // The band edge is the semáforo's, not 0.1: 0.3 is "cerca", not "segura".
    expect(statusOf(0.3, 0, "lt")).toBe("near");
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
