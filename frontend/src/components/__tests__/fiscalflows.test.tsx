import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { runScenario, type Scenario } from "../../engine/spain";
import { BASE_LEVERS } from "../../engine/vintage";
import { BudgetFlowChart } from "../BudgetFlowChart";
import { DebtAmortizationFlowChart } from "../DebtAmortizationFlowChart";
import { budgetFlows, debtRatioBridge } from "../fiscalFlows";

/** Un presupuesto de juguete, pero completo.
 *
 *  Antes fijaba sólo gasto total, pensiones, educación e intereses y dejaba el
 *  resto de partidas con los valores reales del motor. Al empezar a pintarlas
 *  todas, las partes sumaban más que el total y `budgetFlows` devolvía null,
 *  como debe. Se fijan las siete: 37 de 40, residuo 3.
 */
function budgetScenario(balance: number): Scenario {
  const scn = runScenario(BASE_LEVERS);
  scn.gtot[0] = 40;
  scn.pens[0] = 13;
  scn.d1[0] = 9;
  scn.p2[0] = 5;
  scn.edu[0] = 4;
  scn.p51[0] = 2;
  scn.d3[0] = 1;
  scn.int[0] = 3;
  scn.saldo[0] = balance;
  return scn;
}

describe("illustrative budget conservation", () => {
  it.each([-1, 0, 5])("balances every source and use with fiscal balance %s", (balance) => {
    // A deficit below interest expense must not overdraw the financing node.
    const flow = budgetFlows(budgetScenario(balance), 0)!;
    expect(flow.revenues).toBe(40 + balance);
    expect(flow.sources.reduce((a, n) => a + n.val, 0)).toBeCloseTo(flow.targets.reduce((a, n) => a + n.val, 0), 10);
    for (const node of flow.sources) {
      expect(flow.links.filter((l) => l.s === node.id).reduce((a, l) => a + l.val, 0)).toBeCloseTo(node.val, 10);
    }
    for (const node of flow.targets) {
      expect(flow.links.filter((l) => l.t === node.id).reduce((a, l) => a + l.val, 0)).toBeCloseTo(node.val, 10);
    }
    expect(flow.targets.some((n) => n.id === "surplus")).toBe(balance > 0);
  });

  it("reports a breakdown that exceeds total expenditure instead of hiding it", () => {
    // Antes devolvía null y el gráfico desaparecía. Pero el desajuste no es un
    // dato corrupto: es el estado real del modelo a partir de 2035, porque el
    // gasto total y seis de las siete partidas están congelados en su valor
    // observado y sólo las pensiones evolucionan. Hacer desaparecer el gráfico
    // en los años que más se miran ocultaba justo eso.
    const scn = budgetScenario(-1);
    scn.pens[0] = 45;
    const flow = budgetFlows(scn, 0)!;
    expect(flow).not.toBeNull();
    expect(flow.exceso).toBeGreaterThan(0);
    expect(flow.identificado).toBeGreaterThan(flow.spending);
  });

  it("no señala descuadre cuando las partidas caben en el total", () => {
    const flow = budgetFlows(budgetScenario(-1), 0)!;
    expect(flow.exceso).toBe(0);
    expect(flow.identificado).toBeLessThan(flow.spending);
  });

  it("labels allocations as synthetic and follows the selected horizon", () => {
    const { rerender } = render(<BudgetFlowChart levers={BASE_LEVERS} horizon={2030} />);
    expect(screen.getByText(/conexiones proporcionales sintéticas/)).toBeInTheDocument();
    expect(screen.queryByText(/Oficial|Trazabilidad exacta/)).toBeNull();
    rerender(<BudgetFlowChart levers={BASE_LEVERS} horizon={2040} />);
    expect(screen.getByLabelText("Año de proyección:")).toHaveValue("2040");
  });
});

describe("debt ratio accounting", () => {
  it("closes the bridge in every modeled year, including a rate shock", () => {
    for (const levers of [BASE_LEVERS, { ...BASE_LEVERS, r: 4.8 }]) {
      const scn = runScenario(levers);
      for (let k = 0; k < scn.b.length; k++) expect(debtRatioBridge(scn, k).residual).toBeCloseTo(0, 10);
    }
  });

  it("distinguishes falling debt/GDP from a budget surplus", () => {
    const scn = budgetScenario(-2);
    scn.b[0] = 105.6 / 1.05 + 2;
    scn.gnom[0] = 5;
    const bridge = debtRatioBridge(scn, 0);
    expect(bridge.change).toBeLessThan(0);
    expect(bridge.fiscalContribution).toBe(2);
    expect(bridge.denominatorEffect).toBeLessThan(-2);
    expect(bridge.residual).toBeCloseTo(0, 10);
  });

  it("states the limitation on amortizations and updates with horizon", () => {
    const { rerender } = render(<DebtAmortizationFlowChart levers={BASE_LEVERS} horizon={2030} />);
    expect(screen.getByText(/no desglosa emisiones brutas/)).toBeInTheDocument();
    rerender(<DebtAmortizationFlowChart levers={BASE_LEVERS} horizon={2040} />);
    expect(screen.getByRole("img")).toHaveAttribute("aria-label", expect.stringContaining("2040"));
  });
});
