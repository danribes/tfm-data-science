import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import Prediccion from "../Prediccion";

function ui() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter><Prediccion /></MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Predicción — el backtest y su veredicto", () => {
  it("states the rule before it states the result", () => {
    ui();
    // Rendered before the query resolves: a reader must be able to see what the
    // bar was without having seen whether it was cleared.
    expect(screen.getByText(/Qué se preguntó, y antes de mirar/)).toBeInTheDocument();
    expect(screen.getByText(/se fijó/)).toBeInTheDocument();
  });

  it("shows the loss as a loss, not as a neutral figure", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/5 \/ 17/)).toBeInTheDocument());
    const badge = screen.getByText(/5 \/ 17/);
    expect(badge.className).toContain("cross");
    expect(badge.className).not.toContain("safe");
    expect(badge.textContent).toMatch(/no bate al drift/);
  });

  it("says plainly that nothing was retuned after the fact", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/No se han añadido épocas/)).toBeInTheDocument());
    expect(screen.getByText(/La regla estaba escrita antes/)).toBeInTheDocument();
  });

  it("computes the shortfall from the payload rather than asserting it in prose", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/0,400/)).toBeInTheDocument());
    // 0,4000 vs 0,3953 is +1,2 %. If a future vintage narrows or widens that,
    // the sentence has to move with it.
    expect(screen.getByText(/1,2 % peor/)).toBeInTheDocument();
  });

  it("renders every method and horizon in the table", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/La tabla completa/)).toBeInTheDocument());
    const table = screen.getByText(/La tabla completa/).closest("section")!
      .querySelector("table")!;
    expect(within(table).getAllByRole("row")).toHaveLength(5);   // header + 4
    expect(within(table).getByText(/DL global/)).toBeInTheDocument();
    expect(within(table).getByText(/drift/)).toBeInTheDocument();
  });

  it("greys the horizons that fall outside the rule instead of hiding them", async () => {
    const { container } = ui();
    await waitFor(() => expect(screen.getByText(/La tabla completa/)).toBeInTheDocument());
    const rows = container.querySelectorAll("tbody tr");
    // h=1,2,4 are inside the h<=4 rule; h=8 is outside and stays visible.
    expect(rows).toHaveLength(4);
    expect(rows[3].className).toContain("dim");
    expect(rows[0].className).not.toContain("dim");
  });

  it("lists the leakage guards with the numbers behind them", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/Cómo se evitó hacer trampa/)).toBeInTheDocument());
    const s = screen.getByText(/Cómo se evitó hacer trampa/).closest("section")!;
    expect(within(s).getByText(/Nada español en el entrenamiento/)).toBeInTheDocument();
    expect(within(s).getByText(/113.649/)).toBeInTheDocument();
    expect(within(s).getByText(/2019Q3/)).toBeInTheDocument();
    expect(within(s).getByText(/2024Q1/)).toBeInTheDocument();
    expect(within(s).getByText(/Ceuta y Melilla/)).toBeInTheDocument();
  });

  it("says the losing model changes nothing in production", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/Qué se hace con esto/)).toBeInTheDocument());
    expect(screen.getByText(/siguen saliendo del motor/)).toBeInTheDocument();
  });

  it("draws the MASE = 1 reference so the axis has a meaning", async () => {
    const { container } = ui();
    await waitFor(() => expect(screen.getByText(/Error por horizonte/)).toBeInTheDocument());
    // Scoped to the legend: "naive estacional" also names the MASE=1 reference
    // line and a column header, which is the point — the same benchmark under
    // three guises.
    const legend = container.querySelector(".legend") as HTMLElement;
    expect(legend).toBeTruthy();
    expect(within(legend).getByText(/naive estacional/)).toBeInTheDocument();
    expect(within(legend).getByText(/DL global \(candidato\)/)).toBeInTheDocument();
    expect(within(legend).getByText(/drift \(referencia\)/)).toBeInTheDocument();
  });
});
