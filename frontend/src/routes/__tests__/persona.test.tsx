import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";
import Persona from "../Persona";
import { queryClient } from "../../api/hooks";
import { useScenarioStore } from "../../state/scenarioStore";
import { SHIPPED_IDS } from "../../personas/registry";
import { ANSWER_YEAR } from "../../personas/questions";
import { Y0 } from "../../engine/spain";

const ui = (id: string) =>
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/persona/${id}`]}>
        <Routes><Route path="/persona/:id" element={<Persona />} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );

/** Every profile now opens on its question set, so the gauges, semaphore and
 *  chains these tests assert live behind the toggle. */
async function openFullPanel() {
  const showAll = document.querySelector<HTMLButtonElement>(".show-all");
  if (showAll) fireEvent.click(showAll);
  await waitFor(() => expect(document.querySelectorAll(".out").length).toBeGreaterThan(0));
}

describe("Persona — generic renderer over the API card", () => {
  beforeEach(() => {
    queryClient.clear();
    useScenarioStore.getState().resetAll();
  });

  it.each(SHIPPED_IDS)("persona %s renders h1, gauges, reds, chains, narrative", async (id) => {
    ui(id);
    // Profiles with a question set open on the question, not the full panel;
    // this asserts the generic renderer, so open it where that toggle exists.
    await waitFor(() => expect(document.querySelector(".head h1")).not.toBeNull());
    await openFullPanel();
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
    await openFullPanel();
    expect(screen.getByText("Bono 10A España")).toBeInTheDocument();
    // Appears twice by design: the head's provenance line lists all 6 sources for the
    // card, and the historical-chart caption cites the one source behind that series.
    expect(screen.getAllByText(/ecb_bono10y_es\.csv/).length).toBeGreaterThanOrEqual(1);
  });

  it("persona 02's ipvreal red evaluates without crashing (handoff note 3: 12,8 − 3,0 = 9,8 → cerca)", async () => {
    ui("02");
    await waitFor(() => expect(document.querySelector(".head h1")).not.toBeNull());
    await openFullPanel();
    await waitFor(() => expect(screen.getByText(/Precio vivienda real \(IPV − inflación\) > \+10 % al año/)).toBeInTheDocument());
    const row = screen.getByText(/Precio vivienda real \(IPV − inflación\) > \+10 % al año/).closest(".rl-item")!;
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

describe("Persona — the free-text box", () => {
  beforeEach(() => {
    queryClient.clear();
    useScenarioStore.getState().resetAll();
  });

  it("answers a question typed without accents", async () => {
    ui("03");
    await waitFor(() => expect(document.querySelector(".consulta-input")).not.toBeNull());
    // «cuanto» must reach «¿Cuánto…»: Spanish is routinely typed unaccented.
    fireEvent.change(document.querySelector(".consulta-input")!, {
      target: { value: "cuanto pagare de hipoteca" },
    });
    fireEvent.submit(document.querySelector(".consulta-form")!);
    await waitFor(() => expect(document.querySelector(".answer-value")).not.toBeNull());
  });

  it("says so when it cannot answer, instead of doing nothing", async () => {
    ui("03");
    await waitFor(() => expect(document.querySelector(".consulta-input")).not.toBeNull());
    fireEvent.change(document.querySelector(".consulta-input")!, {
      target: { value: "quien ganara las elecciones" },
    });
    fireEvent.submit(document.querySelector(".consulta-form")!);
    await waitFor(() => expect(document.querySelector(".ask-nomatch")).not.toBeNull());
    expect(document.querySelector(".answer-value")).toBeNull();
  });
});

describe("Persona — a question is answered about a year worth asking about", () => {
  beforeEach(() => {
    queryClient.clear();
    useScenarioStore.getState().resetAll();
  });

  it("clicking a suggested question moves the horizon off the baseline year", async () => {
    // At Y0 every delta is zero, so the answer returned today's value and read
    // as a broken feature: the reader asks about the future and is shown the
    // present.
    expect(useScenarioStore.getState().horizon).toBe(Y0);
    ui("03");
    const chip = await screen.findByRole("button", { name: /vivienda media/i });
    fireEvent.click(chip);
    await waitFor(() =>
      expect(useScenarioStore.getState().horizon).toBe(ANSWER_YEAR));
  });

  it("a horizon the reader chose is never overridden", async () => {
    useScenarioStore.getState().setHorizon(2042);
    ui("03");
    const chip = await screen.findByRole("button", { name: /vivienda media/i });
    fireEvent.click(chip);
    await waitFor(() => expect(document.querySelector(".answer")).not.toBeNull());
    expect(useScenarioStore.getState().horizon).toBe(2042);
  });
});
