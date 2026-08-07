import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { KpiRow } from "../KpiRow";
import { baseline, runScenario } from "../../engine/spain";
import { presetLevers } from "../../engine/levers";
import { BASE_LEVERS } from "../../engine/vintage";

const outs = [
  { k: "bono", lab: "Bono 10A España" }, { k: "spread", lab: "Spread ES–DE" },
  { k: "b", lab: "Deuda pública" }, { k: "saldo", lab: "Saldo público" },
  { k: "int", lab: "Intereses / PIB" },
];

describe("KpiRow — 5 gauge tiles from the API card outs", () => {
  it("renders 5 tiles with es-ES figures (base 2026: bono 3,42 · b 106,3)", () => {
    render(<KpiRow outs={outs} scn={baseline()} base={baseline()} k={0} fresh year={2026} />);
    expect(document.querySelectorAll(".out")).toHaveLength(5);
    expect(screen.getByText("3,42")).toBeInTheDocument();
    expect(screen.getByText("106,3")).toBeInTheDocument();
    expect(screen.getAllByText(/📅/)).toHaveLength(5);
  });

  it("stamp switches 📅→🔮 when a lever moves (spec §9)", () => {
    const scn = runScenario({ ...BASE_LEVERS, r: 4.8 });
    render(<KpiRow outs={outs} scn={scn} base={baseline()} k={0} fresh={false} year={2026} />);
    expect(screen.getAllByText(/🔮/)).toHaveLength(5);
    expect(screen.queryByText(/📅/)).toBeNull();
  });
});

describe("KpiRow — gauge frame widened to the preset envelope (flat-baseline saturation fix)", () => {
  // `r` (Euríbor) and `spread` are pure lever pass-throughs with a perfectly flat baseline
  // (no engine dynamics move them across years). Before this fix, the frame was built from a
  // ±4y baseline window plus a 6%-of-value floor — for a flat series that collapses to
  // ~value±6%, so applying preset S1 (r +200bp) pushed the raw fill to ~952% and the bar
  // pinned at 100%. The frame now also unions in this series' value at k under each of the 8
  // static presets, so the S1 move lands inside the dial instead of saturating it.
  it("Euríbor `r` under preset S1 no longer saturates the gauge", () => {
    const s1 = runScenario(presetLevers("S1"));
    const outsR = [{ k: "r", lab: "Euríbor" }];
    const { container } = render(
      <KpiRow outs={outsR} scn={s1} base={baseline()} k={0} fresh={false} year={2026} />,
    );
    const fill = container.querySelector(".gaugebar .f") as HTMLElement;
    const pct = parseFloat(fill.style.width);
    // Old formula: raw fill ≈ 952% → clamped to 100 (pinned, uninformative). New formula
    // lands inside the dial with room on both sides.
    expect(pct).toBeCloseTo(87.88, 1);
    expect(pct).toBeGreaterThan(5);
    expect(pct).toBeLessThan(95);
  });

  it("Euríbor `r` at base sits well apart from its S1 fill (frame has real headroom, not just clamped extremes)", () => {
    const outsR = [{ k: "r", lab: "Euríbor" }];
    const { container } = render(
      <KpiRow outs={outsR} scn={baseline()} base={baseline()} k={0} fresh year={2026} />,
    );
    const fill = container.querySelector(".gaugebar .f") as HTMLElement;
    expect(parseFloat(fill.style.width)).toBeCloseTo(12.12, 1);
  });

  it("gauge frame stays lever-independent: the `b` (debt) domain is identical whether the current scenario is base, S1, or S7", () => {
    const outsB = [{ k: "b", lab: "Deuda pública" }];
    const domainOf = (scn: ReturnType<typeof baseline>) => {
      const { container } = render(
        <KpiRow outs={outsB} scn={scn} base={baseline()} k={0} fresh={false} year={2026} />,
      );
      const bar = container.querySelector(".gaugebar") as HTMLElement;
      const fill = bar.querySelector(".f") as HTMLElement;
      const bm = bar.querySelector(".bm") as HTMLElement;
      // Back out [lo, hi] from two known points on the same linear scale: the fill (at
      // `value`) and the baseline marker (at `base`, always baseline() here, i.e. fixed).
      return { fillPct: parseFloat(fill.style.width), bmPct: parseFloat(bm.style.left) };
    };
    const atBase = domainOf(baseline());
    const atS1 = domainOf(runScenario(presetLevers("S1")));
    const atS7 = domainOf(runScenario(presetLevers("S7")));
    // The baseline marker sits at the same series value (base[k]) in all three renders, so
    // if the frame is truly lever-independent, its normalized position must be identical
    // across all three — only `fillPct` (which tracks the current scenario's value) differs.
    expect(atBase.bmPct).toBeCloseTo(atS1.bmPct, 6);
    expect(atS1.bmPct).toBeCloseTo(atS7.bmPct, 6);
    expect(atBase.fillPct).not.toBeCloseTo(atS1.fillPct, 1);
  });
});
