import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";
import { PresetBar } from "../PresetBar";
import { queryClient } from "../../api/hooks";
import { useScenarioStore } from "../../state/scenarioStore";

const ui = () => render(<QueryClientProvider client={queryClient}><PresetBar /></QueryClientProvider>);

describe("PresetBar — S0..S7 chips, .on by vector equality", () => {
  beforeEach(() => {
    useScenarioStore.getState().resetAll();
    queryClient.clear();
  });
  it("renders the 8 preset chips with API labels verbatim; S0 active at base", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("S7 adverso")).toBeInTheDocument());
    expect(screen.getAllByRole("button")).toHaveLength(8);
    expect(screen.getByText("S0 base")).toHaveClass("ps", "on");
  });
  it("clicking S1 applies r=4.8 and moves .on", async () => {
    ui();
    await waitFor(() => screen.getByText("S1 tipos +200 pb"));
    await userEvent.click(screen.getByText("S1 tipos +200 pb"));
    expect(useScenarioStore.getState().levers.r).toBeCloseTo(4.8, 9);
    expect(screen.getByText("S1 tipos +200 pb")).toHaveClass("on");
    expect(screen.getByText("S0 base")).not.toHaveClass("on");
  });
  it("hand-moving a lever off any preset clears .on everywhere", async () => {
    ui();
    await waitFor(() => screen.getByText("S0 base"));
    useScenarioStore.getState().setLever("r", 3.05);
    await waitFor(() => expect(screen.getByText("S0 base")).not.toHaveClass("on"));
  });
});
