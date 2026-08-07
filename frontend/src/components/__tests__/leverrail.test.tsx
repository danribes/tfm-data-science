import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";
import { LeverRail } from "../LeverRail";
import { queryClient } from "../../api/hooks";
import { useScenarioStore } from "../../state/scenarioStore";

const ui = (hot: string[] = []) =>
  render(<QueryClientProvider client={queryClient}><LeverRail hotIds={hot} /></QueryClientProvider>);

describe("LeverRail — 10 sliders, hot/moved states, horizon buttons", () => {
  beforeEach(() => {
    useScenarioStore.getState().resetAll();
    queryClient.clear();
  });
  it("renders 10 sliders with v16 names and base readouts (r → 2,80 %)", () => {
    ui();
    expect(screen.getAllByRole("slider")).toHaveLength(10);
    expect(screen.getByText("Tipo de interés · Euríbor 12m")).toBeInTheDocument();
    expect(screen.getByText("2,80 %")).toBeInTheDocument(); // nf(2.8, dec=2)
    expect(screen.getByText("ecb_euribor12m.csv · 2026-06")).toBeInTheDocument();
  });
  it("dragging r updates the store and the readout turns .moved", async () => {
    ui();
    const slider = screen.getAllByRole("slider")[0];
    fireEvent.change(slider, { target: { value: "4.8" } });
    expect(useScenarioStore.getState().levers.r).toBe(4.8);
    await waitFor(() => expect(screen.getByText("4,80 %")).toHaveClass("vv", "moved"));
  });
  it("hot levers get the .hot row highlight (persona hot list)", () => {
    ui(["r", "prima"]);
    expect(document.getElementById("lev-r")).toHaveClass("lev", "hot");
    expect(document.getElementById("lev-sp")).not.toHaveClass("hot");
  });
  it("horizon buttons set the store (2035) and mark .on", async () => {
    ui();
    fireEvent.click(screen.getByText("2035"));
    expect(useScenarioStore.getState().horizon).toBe(2035);
    await waitFor(() => expect(screen.getByText("2035")).toHaveClass("hb", "on"));
  });
  it("reset button returns everything to base", () => {
    ui();
    useScenarioStore.getState().setLever("sp", 1.0);
    fireEvent.click(screen.getByText(/volver a base/i));
    expect(useScenarioStore.getState().levers.sp).toBe(0.0);
  });
});
