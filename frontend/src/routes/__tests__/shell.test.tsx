import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import App from "../../App";
import { server } from "../../test/msw/server";
import { queryClient } from "../../api/hooks";
import { useScenarioStore } from "../../state/scenarioStore";

describe("App shell", () => {
  beforeEach(() => {
    queryClient.clear();
    useScenarioStore.getState().resetAll();
    window.history.replaceState(null, "", "/");
    localStorage.clear();
  });

  it("boots: rail + nav + no-advice footer, no engine-mismatch banner (mock API == local engine)", async () => {
    render(<App />);
    // "💼 Bonista" appears in the nav AND in Inicio's persona card — use getAllByText
    await waitFor(() => expect(screen.getAllByText(/💼 Bonista/).length).toBeGreaterThanOrEqual(1));
    // The ten levers live in the rail; Inicio's bond calculator has its own two.
    expect(within(document.getElementById("scenario-levers")!).getAllByRole("slider")).toHaveLength(10);
    expect(screen.getByText(/proyección condicional, no recomendación/i)).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.queryByText(/desajuste del motor/i)).toBeNull());
  });

  it("theme toggle cycles system → light → dark and persists the choice", async () => {
    render(<App />);
    await waitFor(() => screen.getByRole("button", { name: /tema/i }));
    const button = () => screen.getByRole("button", { name: /tema/i });

    // Arranca siguiendo al sistema, que no guarda nada: la ausencia de valor
    // es lo que hace que «sistema» sea el estado por defecto de verdad.
    expect(localStorage.getItem("theme")).toBeNull();

    await userEvent.click(button());
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(localStorage.getItem("theme")).toBe("light");

    await userEvent.click(button());
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(localStorage.getItem("theme")).toBe("dark");

    await userEvent.click(button());
    expect(localStorage.getItem("theme")).toBeNull();
  });

  it("API down → wake-up screen while retrying, then the blocking screen", async () => {
    server.use(http.get("http://localhost:8000/health", () => HttpResponse.error()));
    render(<App />);
    // While the health probe retries, the visitor sees the wake-up screen —
    // the deployed API sleeps on the free tier, and a cold start is not an
    // outage. Only after the retry budget is spent does the down screen show.
    expect(await screen.findByText(/despertando el servidor/i)).toBeInTheDocument();
    expect(await screen.findByText(/no se puede conectar con la API/i, {}, { timeout: 3000 })).toBeInTheDocument();
    expect(screen.getByText(/http:\/\/localhost:8000/)).toBeInTheDocument();
    expect(screen.getByText(/uvicorn api\.main:app --reload --port 8000/)).toBeInTheDocument();
  });

  it("engine mismatch banner fires when the API scenario diverges", async () => {
    server.use(
      http.post("http://localhost:8000/scenario", () =>
        HttpResponse.json({
          vintage: "2026-07-31", computed_not_advice: true, horizon: 2050,
          years: Array.from({ length: 25 }, (_, i) => 2026 + i),
          baseline: { b: Array(25).fill(0) }, scenario: { b: Array(25).fill(999) },
          deltas: {}, personas: {}, redlines: [],
        })),
    );
    render(<App />);
    expect(await screen.findByText(/desajuste del motor/i)).toBeInTheDocument();
  });
});
