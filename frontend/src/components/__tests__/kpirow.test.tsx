import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { KpiRow } from "../KpiRow";
import { baseline, runScenario } from "../../engine/spain";
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
