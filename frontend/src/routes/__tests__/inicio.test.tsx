import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";
import Inicio from "../Inicio";
import { queryClient } from "../../api/hooks";
import { useScenarioStore } from "../../state/scenarioStore";
import { SHIPPED_IDS } from "../../personas/registry";

const ui = () =>
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter><Inicio /></MemoryRouter>
    </QueryClientProvider>,
  );

describe("Inicio — headline figures + global semaphore + persona cards", () => {
  beforeEach(() => {
    queryClient.clear();
    useScenarioStore.getState().resetAll();
  });

  it("shows vintage/coverage banner and the four headline figures at base", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/141 fuentes/)).toBeInTheDocument());
    expect(screen.getByText(/vintage 2026-07-31/)).toBeInTheDocument();
    // baseline pins: deuda 2050 = 223,8 %PIB · paro 10,1 % · IPCA 3,0 %.
    // Scoped to the tiles: "10,1"/"3,0" also appear in the semaphore rows below.
    const tiles = document.querySelectorAll(".out");
    expect(tiles).toHaveLength(4);
    expect(tiles[0].textContent).toContain("223,8"); // Deuda 2050
    expect(tiles[2].textContent).toContain("10,1");  // Paro
    expect(tiles[3].textContent).toContain("3,0");   // IPCA
  });

  it("renders the 9 global red lines with computed statuses (deuda_105 crossed at base 2026)", async () => {
    ui();
    await waitFor(() => expect(document.querySelectorAll(".rl-item")).toHaveLength(9));
    const deuda105 = screen.getByText("Deuda > 105 % PIB").closest(".rl-item")!;
    expect(deuda105.querySelector(".st")!.className).toContain("cross");
  });

  it("links to every shipped persona, whatever that set is", async () => {
    ui();
    await waitFor(() => expect(screen.getByText(/💼 Bonista/)).toBeInTheDocument());
    // Scoped to the persona *cards*: the macro-to-micro section also links to
    // individual personas in prose, and those are not cards.
    const cards = screen
      .getAllByRole("link")
      .filter((a) => a.getAttribute("href")?.startsWith("/persona/") && a.classList.contains("card"));
    // Derived from SHIPPED_IDS rather than a literal list. The literal version
    // of this test kept passing under the name "the four shipped personas" for
    // as long as the mock stayed four personas behind the app.
    expect(cards.map((a) => a.getAttribute("href")))
      .toEqual(SHIPPED_IDS.map((id) => `/persona/${id}`));
    expect(cards.length).toBeGreaterThanOrEqual(12);
  });
});
