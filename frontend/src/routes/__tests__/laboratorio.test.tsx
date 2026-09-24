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
    // The heading names the series; the raw key is only the option value.
    await waitFor(() => expect(screen.getByText(/Esfuerzo vivienda ·/)).toBeInTheDocument());
    expect(document.querySelectorAll("path.recharts-curve").length).toBeGreaterThanOrEqual(2);
  });

  it("MC fan renders from the (debounced) server response with the ±2pp note", async () => {
    ui();
    await waitFor(
      () => expect(document.querySelectorAll("path.recharts-area-area")).toHaveLength(2),
      { timeout: 3000 }, // 400 ms debounce + MSW round-trip
    );
    expect(screen.getByText(/±2 pp/)).toBeInTheDocument();
    expect(screen.getByText(/4\.000 trayectorias/)).toBeInTheDocument();
  });

  it("names every series instead of showing its code", () => {
    ui();
    const options = [...screen.getByRole("combobox", { name: /serie/i }).querySelectorAll("option")];
    expect(options.filter((o) => o.textContent === o.value).map((o) => o.value)).toEqual([]);
  });

  it("explains each block in plain language before the technical detail", async () => {
    ui();
    // intro, series, fan, levers, budget, debt bridge, sensitivity
    expect(screen.getAllByText("Cómo leerlo").length).toBeGreaterThanOrEqual(7);
    expect(screen.getByText(/Palanca/, { selector: "b" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("el futuro del medio")).toBeInTheDocument(), { timeout: 3000 });
    expect(screen.queryByText("banda p5–p95")).not.toBeInTheDocument();
  });

  it("lever table says what each lever means", () => {
    ui();
    const rows = screen.getAllByRole("row");
    expect(rows[1].textContent).toContain("Lo que cuesta pedir dinero prestado en Europa");
  });

  it("raw lever table shows current vs base (r: 2,80 both at boot)", () => {
    ui();
    const rows = screen.getAllByRole("row");
    expect(rows.length).toBe(11); // header + 10 levers
    expect(rows[1].textContent).toContain("2,80");
  });
});
