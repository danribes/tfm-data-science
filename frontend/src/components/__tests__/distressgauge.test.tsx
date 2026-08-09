import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DistressGauge } from "../DistressGauge";

function ui() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}><DistressGauge /></QueryClientProvider>,
  );
}

describe("DistressGauge — el complemento probabilístico del 7 %", () => {
  it("shows Spain's probability against the base rate, not alone", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("1,74 %")).toBeInTheDocument());
    // A probability with no reference reads as either alarming or meaningless.
    expect(screen.getByText(/9,7 % de tasa base/)).toBeInTheDocument();
    expect(screen.getByText(/6× por debajo/)).toBeInTheDocument();
  });

  it("declares that Spain was never in the training labels", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/no está en la base de impagos/)).toBeInTheDocument());
    expect(screen.getByText(/sin haberla visto nunca/)).toBeInTheDocument();
  });

  it("publishes the modest AUC instead of hiding it", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/AUC 0,674/)).toBeInTheDocument());
    expect(screen.getByText(/capacidad discriminante modesta/)).toBeInTheDocument();
    expect(screen.getByText(/posición relativa, no la cifra absoluta/)).toBeInTheDocument();
  });

  it("marks the base rate on the bar itself", async () => {
    const { container } = ui();
    await waitFor(() => expect(container.querySelector(".dg-bar")).toBeTruthy());
    const fill = container.querySelector(".dg-fill") as HTMLElement;
    const base = container.querySelector(".dg-base") as HTMLElement;
    expect(fill).toBeTruthy();
    expect(base).toBeTruthy();
    // Log scale: Spain (1,74 %) must sit left of the base-rate marker (9,7 %).
    expect(parseFloat(fill.style.width)).toBeLessThan(parseFloat(base.style.left));
  });
});
