import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EmpiricalTwin } from "../EmpiricalTwin";

function ui() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}><EmpiricalTwin /></QueryClientProvider>,
  );
}

describe("EmpiricalTwin — el contraste del E_R constante", () => {
  it("shows the three debt regimes with their slopes", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/deuda < 60 %/)).toBeInTheDocument());
    const table = screen.getByText(/deuda < 60 %/).closest("table")!;
    expect(within(table).getAllByRole("row")).toHaveLength(4);   // header + 3
    expect(within(table).getAllByText("−0,035")).toHaveLength(2);
    expect(within(table).getByText("−0,020")).toBeInTheDocument();
  });

  it("renders the null as the finding, with the engine surviving", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/no distinguible/)).toBeInTheDocument());
    const badge = screen.getByText(/la constante del motor sobrevive/);
    expect(badge.className).toContain("safe");
    // "Not contradicted" is weaker than "validated", and the card must say so.
    expect(screen.getByText(/no contradicho/)).toBeInTheDocument();
    expect(screen.getByText(/menos y se dice tal cual/)).toBeInTheDocument();
  });

  it("publishes the zero out-of-country R² instead of hiding it", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/R² fuera de país/)).toBeInTheDocument());
    expect(screen.getByText(/−0,007/)).toBeInTheDocument();
    expect(screen.getByText(/superficie ajustada, no una regla validada/)).toBeInTheDocument();
  });

  it("declares why Spain cannot be scored", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/España no puntúa aquí/)).toBeInTheDocument());
    expect(screen.getByText(/no reporta tipos de préstamo al WDI/)).toBeInTheDocument();
  });

  it("scales the importance bars to the largest driver", async () => {
    const { container } = ui();
    await waitFor(() => expect(container.querySelector(".et-fill")).toBeTruthy());
    const widths = [...container.querySelectorAll(".et-fill")]
      .map((el) => parseFloat((el as HTMLElement).style.width));
    expect(Math.max(...widths)).toBeCloseTo(100, 0);
    expect(widths.length).toBe(3);
    // Rate change is a minor driver historically — the bar must show that.
    expect(Math.min(...widths)).toBeLessThan(20);
  });

  it("says it is not causal, next to the numbers", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/No es causalidad/)).toBeInTheDocument());
    expect(screen.getByText(/suben tipos en expansión/)).toBeInTheDocument();
  });
});
