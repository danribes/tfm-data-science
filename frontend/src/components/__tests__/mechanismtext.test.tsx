import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MechanismText } from "../MechanismText";

const TEXT = [
  "Qué hace en el modelo cada palanca que mueve esta cifra:",
  "  · Instituciones laborales: son los convenios, las indemnizaciones y el salario mínimo.",
  "Cuánto pesa cada una en el cambio de temporalidad en 2050 (−2,8 puntos en total).",
  "  · Instituciones laborales: −2,4 puntos (86 % del cambio).",
  "  · No mueven esta cifra, o casi nada: Prima de riesgo y Presión demográfica.",
  "Detalle técnico: A_Z = 1,10 · A_TAU = 0,30.",
].join("\n");

describe("MechanismText — the engine's mechanism, laid out", () => {
  it("turns the bullets into lists and the headings into paragraphs", () => {
    const { container } = render(<MechanismText text={TEXT} />);
    expect(container.querySelectorAll("ul")).toHaveLength(2);
    expect(container.querySelectorAll("li")).toHaveLength(3);
    expect(screen.getByText(/Cuánto pesa cada una/).tagName).toBe("P");
  });

  it("folds the constants into «Detalle técnico», not the body", () => {
    const { container } = render(<MechanismText text={TEXT} technical="Identidad de la deuda." />);
    const details = container.querySelector("details.tech-details")!;
    expect(details).toBeTruthy();
    expect(details.textContent).toContain("Constantes del modelo: A_Z = 1,10");
    expect(details.textContent).toContain("Identidad de la deuda.");
    const outside = [...container.querySelectorAll(":scope > .mech-text > p, :scope > .mech-text > ul")]
      .map((el) => el.textContent).join(" ");
    expect(outside).not.toContain("A_Z");
  });
});
