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

describe("DistressGauge — puntuación exploratoria", () => {
  it("shows a score without a probability or base-rate risk ratio", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("0,0174")).toBeInTheDocument());
    expect(screen.getByText(/sin calibración para España/)).toBeInTheDocument();
    expect(screen.queryByText("1,74 %")).not.toBeInTheDocument();
    expect(screen.queryByText(/× por debajo/)).not.toBeInTheDocument();
  });

  it("declares that Spain was never in the training labels", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/no está en el conjunto etiquetado/)).toBeInTheDocument());
    expect(screen.getByText(/8\/12 variables/)).toBeInTheDocument();
    expect(screen.getByText(/no demuestra que el modelo se transfiera/)).toBeInTheDocument();
  });

  it("publishes the modest AUC instead of hiding it", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/AUC 0,674/)).toBeInTheDocument());
    expect(screen.getByText(/sin separación temporal/)).toBeInTheDocument();
    expect(screen.getByText(/no validan probabilidades absolutas/)).toBeInTheDocument();
  });

  it("uses a 0–1 score scale without a population-risk reference marker", async () => {
    const { container } = ui();
    await waitFor(() => expect(container.querySelector(".dg-bar")).toBeTruthy());
    const fill = container.querySelector(".dg-fill") as HTMLElement;
    const base = container.querySelector(".dg-base") as HTMLElement;
    expect(fill).toBeTruthy();
    expect(base).toBeNull();
    expect(parseFloat(fill.style.width)).toBeCloseTo(1.74);
  });
});
