import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";
import Laboratorio from "../Laboratorio";
import { queryClient } from "../../api/hooks";
import { useScenarioStore } from "../../state/scenarioStore";

const ui = () => render(<QueryClientProvider client={queryClient}><Laboratorio /></QueryClientProvider>);

describe("Laboratorio — series explorer + MC fan + raw levers", () => {
  beforeEach(() => {
    queryClient.clear();
    useScenarioStore.getState().resetAll();
  });

  it("series selector offers all 41 keys and defaults to b", () => {
    ui();
    const select = screen.getByRole("combobox", { name: /serie/i });
    expect(select).toHaveValue("b");
    expect(select.querySelectorAll("option")).toHaveLength(41);
  });

  it("changing the series redraws the projection chart", async () => {
    ui();
    await userEvent.selectOptions(screen.getByRole("combobox", { name: /serie/i }), "esf");
    await waitFor(() => expect(screen.getByText(/esf ·/)).toBeInTheDocument());
    expect(document.querySelectorAll("path.recharts-curve").length).toBeGreaterThanOrEqual(2);
  });

  it("MC fan renders from the (debounced) server response with the ±2pp note", async () => {
    ui();
    await waitFor(
      () => expect(document.querySelectorAll("path.recharts-area-area")).toHaveLength(2),
      { timeout: 3000 }, // 400 ms debounce + MSW round-trip
    );
    expect(screen.getByText(/±2 pp/)).toBeInTheDocument();
    expect(screen.getByText(/4000 trayectorias/)).toBeInTheDocument();
  });

  it("raw lever table shows current vs base (r: 2,80 both at boot)", () => {
    ui();
    const rows = screen.getAllByRole("row");
    expect(rows.length).toBe(11); // header + 10 levers
    expect(rows[1].textContent).toContain("2,80");
  });
});
