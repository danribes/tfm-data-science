import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { BondCalculator, bondYield, primaToRedLine } from "../BondCalculator";
import { runScenario, YEARS } from "../../engine/spain";
import { BASE_LEVERS } from "../../engine/vintage";
import { useScenarioStore } from "../../state/scenarioStore";

describe("bondYield — the engine's own rule", () => {
  it("matches the scenario's 10-year yield for any Euríbor and premium", () => {
    for (const [r, prima] of [[2.8, 45], [4.8, 150], [6, 400], [0, 0], [1.95, 105]]) {
      expect(bondYield(r, prima)).toBeCloseTo(runScenario({ ...BASE_LEVERS, r, prima }).bono[0], 12);
    }
  });

  it("the premium it names takes the yield exactly to 7 %", () => {
    for (const r of [0, 2.8, 4.8, 6]) expect(bondYield(r, primaToRedLine(r))).toBeCloseTo(7, 12);
  });
});

describe("BondCalculator", () => {
  beforeEach(() => useScenarioStore.getState().resetAll());

  it("starts from the levers and says how far the red line is", () => {
    render(<BondCalculator />);
    expect(screen.getByText("3,42 %")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.getByText(/Le faltan 3,58 puntos para el 7 %/)).toBeInTheDocument();
    // 403 pb would be needed at a 2,80 % Euríbor: past the panel's 400.
    expect(screen.getByText(/ni con la prima al máximo del panel \(400 pb\) se llegaría/)).toBeInTheDocument();
  });

  it("raises the alert when the yield goes above 7 %", () => {
    render(<BondCalculator />);
    fireEvent.change(screen.getByLabelText("Euríbor a 12 meses"), { target: { value: "6" } });
    fireEvent.change(screen.getByLabelText("Prima de riesgo"), { target: { value: "150" } });
    expect(screen.getByRole("alert").textContent).toMatch(/7,67 %: por encima de la línea roja del 7 %/);
  });

  it("names the premium that would reach the line when it is within the panel", () => {
    render(<BondCalculator />);
    fireEvent.change(screen.getByLabelText("Euríbor a 12 meses"), { target: { value: "4.8" } });
    expect(screen.getByText(/la prima tendría que pasar de 203 pb para llegar a la línea roja/)).toBeInTheDocument();
  });

  it("charts the flat yield against the average rate, which catches up over the years", () => {
    render(<BondCalculator />);
    expect(screen.getByText(/bono a 10 años \(lo que cuesta la deuda nueva\)/)).toBeInTheDocument();
    expect(screen.getByText("tipo medio que paga el Estado por toda su deuda")).toBeInTheDocument();
    expect(screen.getByText(/La línea plana es el bono/)).toBeInTheDocument();
    // At base the average rate never reaches 7 %: no year is named.
    expect(screen.queryByText(/el tipo medio pasaría del 7 %/)).toBeNull();
  });

  it("names the year the average rate would pass 7 %, from the engine", () => {
    render(<BondCalculator />);
    fireEvent.change(screen.getByLabelText("Euríbor a 12 meses"), { target: { value: "6" } });
    fireEvent.change(screen.getByLabelText("Prima de riesgo"), { target: { value: "150" } });
    const ief = runScenario({ ...BASE_LEVERS, r: 6, prima: 150 }).ief;
    const year = YEARS[ief.findIndex((v) => v > 7)];
    expect(screen.getByText(new RegExp(`el tipo medio pasaría del 7 % en ${year}`))).toBeInTheDocument();
  });

  it("carries the values into the scenario when asked", () => {
    render(<BondCalculator />);
    fireEvent.change(screen.getByLabelText("Euríbor a 12 meses"), { target: { value: "5" } });
    fireEvent.click(screen.getByRole("button", { name: "Aplicar a mis palancas" }));
    expect(useScenarioStore.getState().levers.r).toBe(5);
    expect(useScenarioStore.getState().levers.prima).toBe(BASE_LEVERS.prima);
  });
});
