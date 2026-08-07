import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";
import Persona from "../Persona";
import { queryClient } from "../../api/hooks";
import { useScenarioStore } from "../../state/scenarioStore";

const ui = (id: string) =>
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/persona/${id}`]}>
        <Routes><Route path="/persona/:id" element={<Persona />} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );

describe("Persona — generic renderer over the API card", () => {
  beforeEach(() => {
    queryClient.clear();
    useScenarioStore.getState().resetAll();
  });

  it.each(["01", "02", "03", "06"])("persona %s renders h1, 5 gauges, 3 reds, chains, narrative", async (id) => {
    ui(id);
    await waitFor(() => expect(document.querySelectorAll(".out")).toHaveLength(5));
    expect(document.querySelectorAll(".rl-item")).toHaveLength(3);
    expect(document.querySelectorAll(".ch").length).toBeGreaterThanOrEqual(3);
    expect(document.querySelector(".narr .x")!.textContent!.length).toBeGreaterThan(40);
    expect(document.querySelector(".head h1")).not.toBeNull();
  });

  it("persona 01 shows its API copy verbatim", async () => {
    ui("01");
    await waitFor(() =>
      expect(screen.getByText("💼 Inversor en bonos: ¿me pagarán los 10 años?")).toBeInTheDocument());
    expect(screen.getByText("Bono 10A España")).toBeInTheDocument();
    // Appears twice by design: the head's provenance line lists all 6 sources for the
    // card, and the historical-chart caption cites the one source behind that series.
    expect(screen.getAllByText(/ecb_bono10y_es\.csv/).length).toBeGreaterThanOrEqual(1);
  });

  it("persona 02's ipvreal red evaluates without crashing (handoff note 3: 12,8 − 3,0 = 9,8 → cerca)", async () => {
    ui("02");
    await waitFor(() => expect(screen.getByText(/IPV real a\/a > 10 %/)).toBeInTheDocument());
    const row = screen.getByText(/IPV real a\/a > 10 %/).closest(".rl-item")!;
    expect(row.querySelector(".st")!.className).toContain("near");
    expect(row.querySelector(".st")!.textContent).toBe("9,8");
  });

  it("sets the rail hot ids from the card (persona 01: r, prima, sp, dem)", async () => {
    ui("01");
    await waitFor(() =>
      expect(useScenarioStore.getState().hotIds).toEqual(["r", "prima", "sp", "dem"]));
  });

  it("unknown id shows a Spanish not-found note, no crash", async () => {
    ui("99");
    expect(await screen.findByText(/perfil no disponible/i)).toBeInTheDocument();
  });
});
