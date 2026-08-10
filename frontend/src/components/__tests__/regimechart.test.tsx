import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RegimeChart } from "../RegimeChart";

function ui() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}><RegimeChart /></QueryClientProvider>,
  );
}

describe("RegimeChart — crisis detectadas, no anotadas", () => {
  it("says the shading is detected by a model, not hand-annotated", async () => {
    ui();
    await waitFor(() =>
      expect(screen.getByText(/Siglo y medio de calma y crisis/)).toBeInTheDocument());
    expect(screen.getByText(/regímenes detectados, no anotados a mano/)).toBeInTheDocument();
    expect(screen.getByText(/no vienen de un libro de historia/)).toBeInTheDocument();
  });

  it("declares the Civil War gap as a data property, not a model finding", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/1936–39/)).toBeInTheDocument());
    expect(screen.getByText(/el Estado no publicó cuentas/)).toBeInTheDocument();
    expect(screen.getByText(/el hueco es del dato, no del modelo/)).toBeInTheDocument();
  });

  it("names how to reproduce the artifact", async () => {
    ui();
    await waitFor(() =>
      expect(screen.getByText(/python -m research.regimes/)).toBeInTheDocument());
    expect(screen.getByText(/gold_fiscal_historico.csv/)).toBeInTheDocument();
  });

  it("ties the episodes to the app's red lines", async () => {
    ui();
    await waitFor(() =>
      expect(screen.getByText(/las líneas rojas están ancladas en el malo/)).toBeInTheDocument());
  });
});
