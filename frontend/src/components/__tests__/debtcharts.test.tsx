import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SpaghettiChart } from "../SpaghettiChart";
import {
  DebtVsGdpChart, RESCUE_YIELD, SnowballStrip, debtVsGdpSeries,
} from "../DebtVsGdpChart";
import { baseline, runScenario, YEARS } from "../../engine/spain";
import { BASE_LEVERS } from "../../engine/vintage";

describe("SpaghettiChart", () => {
  const years = [2026, 2027, 2028];
  const paths = [
    [100, 105, 110],
    [100, 102, 99],
  ];

  it("renders nothing without paths", () => {
    const { container } = render(<SpaghettiChart years={years} paths={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing without years", () => {
    const { container } = render(<SpaghettiChart years={[]} paths={paths} />);
    expect(container.firstChild).toBeNull();
  });

  it("mounts a chart surface for the strands", () => {
    const { container } = render(
      <SpaghettiChart years={years} paths={paths} median={[100, 103, 105]} />,
    );
    expect(container.querySelector(".spag")).toBeTruthy();
  });
});

describe("debtVsGdpSeries", () => {
  const scn = baseline();

  it("starts both series at 100 in the first year", () => {
    const s = debtVsGdpSeries(scn, YEARS);
    expect(s[0].pib).toBeCloseTo(100, 6);
    expect(s[0].deuda).toBeCloseTo(100, 6);
  });

  it("compounds GDP at the nominal growth rate", () => {
    const s = debtVsGdpSeries(scn, YEARS);
    expect(s[1].pib).toBeCloseTo(100 * (1 + scn.gnom[1] / 100), 6);
  });

  it("reproduces the debt ratio as the gap between the two curves", () => {
    // The whole point of the index: deuda/pib must equal b(t)/b(0).
    const s = debtVsGdpSeries(scn, YEARS);
    for (let i = 0; i < s.length; i++) {
      expect(s[i].deuda / s[i].pib).toBeCloseTo(scn.b[i] / scn.b[0], 6);
    }
  });

  it("carries the raw debt ratio alongside the indices", () => {
    const s = debtVsGdpSeries(scn, YEARS);
    expect(s.map((p) => p.ratio)).toEqual(YEARS.map((_, i) => scn.b[i]));
  });

  it("shows debt outrunning the economy when rates rise", () => {
    const hi = runScenario({ ...BASE_LEVERS, r: BASE_LEVERS.r + 2 });
    const base = debtVsGdpSeries(baseline(), YEARS);
    const shocked = debtVsGdpSeries(hi, YEARS);
    const lastB = base[base.length - 1];
    const lastS = shocked[shocked.length - 1];
    expect(lastS.deuda / lastS.pib).toBeGreaterThan(lastB.deuda / lastB.pib);
  });
});

describe("DebtVsGdpChart", () => {
  it("states the multiples and the resulting ratio move", () => {
    render(<DebtVsGdpChart scn={baseline()} years={YEARS} />);
    expect(screen.getByText(/Partiendo ambos de 100/)).toBeInTheDocument();
    expect(screen.getByText(/por eso la\s+ratio pasa de/)).toBeInTheDocument();
  });
});

describe("SnowballStrip", () => {
  it("uses 7 % as the rescue-zone threshold", () => {
    expect(RESCUE_YIELD).toBe(7);
  });

  it("flags the snowball when the effective rate beats growth", () => {
    const scn = runScenario({ ...BASE_LEVERS, r: 6, prima: 400 });
    render(<SnowballStrip scn={scn} k={20} />);
    expect(screen.getByText(/bola de nieve activa/)).toBeInTheDocument();
  });

  it("says growth is diluting when it beats the effective rate", () => {
    const scn = baseline();
    const k = scn.ief.findIndex((r, i) => r < scn.gnom[i]);
    if (k >= 0) {
      render(<SnowballStrip scn={scn} k={k} />);
      expect(screen.getByText(/el crecimiento diluye/)).toBeInTheDocument();
    }
  });

  it("marks the yield as bad once it reaches the rescue zone", () => {
    const scn = runScenario({ ...BASE_LEVERS, r: 6, prima: 400 });
    const { container } = render(<SnowballStrip scn={scn} k={0} />);
    expect(scn.bono[0]).toBeGreaterThanOrEqual(RESCUE_YIELD);
    expect(container.querySelector(".snow-val.bad")).toBeTruthy();
  });
});
