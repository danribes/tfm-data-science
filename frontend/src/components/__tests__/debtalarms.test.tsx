import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DebtAlarms } from "../DebtAlarms";
import { BudgetFlowChart } from "../BudgetFlowChart";
import { baseline, runScenario } from "../../engine/spain";
import { BASE_LEVERS } from "../../engine/vintage";

// The API's own definitions (engine/redlines.py RED_LINES), the debt ones.
const DEFS = [
  { id: "bono_rescate", label: "Bono 10A > 7 %", series: "bono", threshold: 7.0, cmp: "gt", source: "zona rescate [hist]" },
  { id: "deficit_maastricht", label: "Déficit > 3 % PIB", series: "saldo", threshold: -3.0, cmp: "lt", source: "umbral Maastricht [regla UE]" },
  { id: "deficit_record_2012", label: "Déficit > 11,5 % PIB", series: "saldo", threshold: -11.5, cmp: "lt", source: "récord 2012 [hist]" },
  { id: "deuda_105", label: "Deuda > 105 % PIB", series: "b", threshold: 105.0, cmp: "gt", source: "crack23 [comentario]" },
  { id: "deuda_120", label: "Deuda > 120 % PIB", series: "b", threshold: 120.0, cmp: "gt", source: "pico COVID [hist]" },
  { id: "paro_record", label: "Paro > 26,9 %", series: "u", threshold: 26.9, cmp: "gt", source: "[hist]" },
  { id: "inflacion_10", label: "Inflación > 10 %", series: "pi", threshold: 10.0, cmp: "gt", source: "[hist]" },
  { id: "esfuerzo_40", label: "Esfuerzo vivienda > 40 %", series: "esf", threshold: 40.0, cmp: "gt", source: "[UE]" },
  { id: "pobreza_infantil_30", label: "Pobreza infantil > 30 %", series: "arop", threshold: 30.0, cmp: "gt", source: "[hist]" },
];

const whenOf = (label: string) => within(screen.getByText(label).closest("tr")!).getAllByRole("cell")[1].textContent;

describe("DebtAlarms — ¿cuándo es demasiada deuda?", () => {
  it("says first that the app gives no verdict on paying the debt", () => {
    render(<DebtAlarms scn={baseline()} defs={DEFS} />);
    expect(screen.getByText(/Ningún modelo puede decir si una deuda se podrá pagar/)).toBeInTheDocument();
    expect(screen.getByText(/«cerca» quiere decir que está a menos de un 10 % del umbral/)).toBeInTheDocument();
  });

  it("gives the year each alarm goes off in the base scenario", () => {
    render(<DebtAlarms scn={baseline()} defs={DEFS} />);
    expect(whenOf("Deuda > 105 % PIB")).toBe("ya cruzada hoy");
    expect(whenOf("Deuda > 120 % PIB")).toBe("salta en 2033");
    expect(whenOf("Déficit > 3 % PIB")).toBe("ya cruzada hoy");
    expect(whenOf("Déficit > 11,5 % PIB")).toBe("salta en 2043");
    expect(whenOf("Bono 10A > 7 %")).toBe("no salta antes de 2050");
    expect(whenOf("Gasto público > 51,4 % PIB")).toBe("salta en 2038");
    expect(whenOf("Bola de nieve de la deuda")).toBe("salta en 2037");
    expect(whenOf("Intereses de la deuda > 5,0 % PIB")).toBe("salta en 2041");
  });

  it("lists the other red lines in their own group, with the same rule", () => {
    render(<DebtAlarms scn={baseline()} defs={DEFS} />);
    expect(screen.getByText("Y las demás líneas rojas, fuera de la deuda")).toBeInTheDocument();
    expect(whenOf("Paro > 26,9 %")).toBe("no salta antes de 2050");
    expect(whenOf("Esfuerzo vivienda > 40 %")).toBe("ya cruzada hoy");
    expect(whenOf("Pobreza infantil > 30 %")).toBe("no salta antes de 2050");
  });

  it("alerts when the levers put the 10-year bond above 7 %, and does not call it «hoy»", () => {
    render(<DebtAlarms scn={runScenario({ ...BASE_LEVERS, r: 6, prima: 150 })} defs={DEFS} />);
    expect(screen.getByRole("alert").textContent).toMatch(/el bono a 10 años se pagaría al 7,67 %, por\s+encima de la línea roja del 7 %/);
    // Spain is not above 7 % today: the levers put it there.
    expect(whenOf("Bono 10A > 7 %")).toBe("salta en 2026, por tus palancas");
    expect(whenOf("Intereses de la deuda > 5,0 % PIB")).toBe("salta en 2029");
  });

  it("no bond alert while the bond stays under 7 %", () => {
    render(<DebtAlarms scn={baseline()} defs={DEFS} />);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("moves with the levers: more productivity switches alarms off", () => {
    render(<DebtAlarms scn={runScenario({ ...BASE_LEVERS, lam: BASE_LEVERS.lam + 1 })} defs={DEFS} />);
    expect(whenOf("Déficit > 11,5 % PIB")).toBe("no salta antes de 2050");
    expect(whenOf("Bola de nieve de la deuda")).toBe("no salta antes de 2050");
    expect(whenOf("Deuda > 120 % PIB")).toBe("salta en 2040");
  });
});

describe("BudgetFlowChart — when the record line starts", () => {
  it("before the record, says which year it would be passed", () => {
    render(<BudgetFlowChart levers={BASE_LEVERS} horizon={2035} />);
    expect(screen.getByText(/todavía no llega a su récord de 2020/)).toBeInTheDocument();
    expect(screen.getByText(/lo pasaría en 2038/)).toBeInTheDocument();
  });

  it("after it, says since when", () => {
    render(<BudgetFlowChart levers={BASE_LEVERS} horizon={2050} />);
    expect(screen.getByText(/y lo pasa desde 2038/)).toBeInTheDocument();
  });
});
