import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";
import { LeverRail } from "../LeverRail";
import { useScenarioStore } from "../../state/scenarioStore";

function ui() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter><LeverRail /></MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("LeverRail — variantes demográficas EUROPOP", () => {
  beforeEach(() => useScenarioStore.getState().resetAll());

  it("offers the vintage's variants under the dem lever", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("Sin migración")).toBeInTheDocument());
    expect(screen.getByText("Base")).toBeInTheDocument();
    expect(screen.getByText("Migración alta")).toBeInTheDocument();
  });

  it("a chip sets the dem lever to the variant's equivalent — one input path", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("Sin migración")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Sin migración"));
    // Sugar over the existing lever: the store's dem moves, nothing else.
    expect(useScenarioStore.getState().levers.dem).toBeCloseTo(0.401, 3);
  });

  it("marks the active variant, and only that one", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("Sin migración")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Migración alta"));
    await waitFor(() =>
      expect(screen.getByText("Migración alta").className).toContain("on"));
    expect(screen.getByText("Sin migración").className).not.toContain("on");
    // dem = 0 by default means BSL starts active; after the click it must not be.
    expect(screen.getByText("Base").className).not.toContain("on");
  });

  it("carries the dependency mapping in the tooltip, not hidden", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("Sin migración")).toBeInTheDocument());
    const chip = screen.getByText("Sin migración");
    expect(chip.getAttribute("title")).toMatch(/33,4 → 71,3/);
    expect(chip.getAttribute("title")).toMatch(/\+0,401/);
  });
});
