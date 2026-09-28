import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AnswerText } from "../AnswerText";

// Salida real del modelo en /consulta (curva de Phillips, 28-09-2026): el
// prompt pide prosa, pero el modelo escribe Markdown y la página lo pintaba
// tal cual, con los asteriscos a la vista.
const ANSWER = [
  "La curva de Phillips ilustra una asociación negativa entre inflación y desempleo [3].",
  "",
  "* **Relación inicial (años 60):** Durante los años 60, la economía podía combinar ambas [2].",
  "* **Cambio en los años 70:** Las expectativas se desanclaron [1, 6].",
  "",
  "**La inestabilidad de la curva y el papel de las expectativas:**",
  "",
  "El resultado sería una inflación *creciente* [2].",
].join("\n");

describe("AnswerText — la respuesta del corpus, sin Markdown a la vista", () => {
  it("no deja ningún asterisco del Markdown en pantalla", () => {
    const { container } = render(<AnswerText text={ANSWER} />);
    expect(container.textContent).not.toContain("*");
  });

  it("convierte las viñetas en lista y conserva las citas", () => {
    const { container } = render(<AnswerText text={ANSWER} />);
    const items = container.querySelectorAll("ul > li");
    expect(items).toHaveLength(2);
    expect(items[0].querySelector("strong")?.textContent).toBe("Relación inicial (años 60):");
    expect(items[1].textContent).toContain("[1, 6]");
  });

  it("pone en negrita y cursiva lo marcado, dentro de párrafos", () => {
    render(<AnswerText text={ANSWER} />);
    const heading = screen.getByText("La inestabilidad de la curva y el papel de las expectativas:");
    expect(heading.tagName).toBe("STRONG");
    expect(heading.parentElement?.tagName).toBe("P");
    expect(screen.getByText("creciente").tagName).toBe("EM");
  });

  it("numera las listas numeradas y quita las almohadillas de los títulos", () => {
    const { container } = render(<AnswerText text={"## Dos causas\n1. El tipo [1].\n2. El crecimiento [2]."} />);
    expect(container.querySelectorAll("ol > li")).toHaveLength(2);
    expect(container.textContent).not.toContain("#");
    expect(screen.getByText("Dos causas").tagName).toBe("STRONG");
  });

  it("quita las comillas invertidas del código en línea", () => {
    // Salida real en /biblioteca: «el término `(r - γt)` de la ecuación».
    const { container } = render(<AnswerText text="el término `(r - γt)` y la deuda `bt-1` [1]" />);
    expect(container.textContent).not.toContain("`");
    expect([...container.querySelectorAll("code")].map((c) => c.textContent)).toEqual(["(r - γt)", "bt-1"]);
  });

  it("no busca negritas dentro del código", () => {
    const { container } = render(<AnswerText text="la fórmula `a*b*c` no lleva cursiva" />);
    expect(container.querySelector("em")).toBeNull();
    expect(container.querySelector("code")?.textContent).toBe("a*b*c");
  });

  it("deja literal una marca sin cerrar, como llega a mitad del streaming", () => {
    const { container } = render(<AnswerText text="Primero [1]. **Cambio en" />);
    expect(container.textContent).toBe("Primero [1]. **Cambio en");
  });

  it("no interpreta HTML: el texto del modelo no es marcado", () => {
    const { container } = render(<AnswerText text={"<b>no</b> es negrita"} />);
    expect(container.querySelector("b")).toBeNull();
    expect(container.textContent).toBe("<b>no</b> es negrita");
  });
});
