import { render, screen } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";
import { Warnings } from "../Warnings";
import { queryClient } from "../../api/hooks";
import { STALE_LIMIT_DAYS, staleDays, useAppHealth } from "../../state/appHealth";
import { useScenarioStore } from "../../state/scenarioStore";

// `now` is injectable so tests never need fake timers (they fight waitFor/React Query).
const ui = (now?: Date) =>
  render(<QueryClientProvider client={queryClient}><Warnings now={now} /></QueryClientProvider>);

describe("Warnings — honesty banners (spec §8)", () => {
  beforeEach(() => {
    useAppHealth.setState({ engineMismatch: false, extraWarnings: [] });
    queryClient.clear();
    useScenarioStore.getState().resetAll();
  });

  it("staleDays: 2026-08-07 is 7 days after vintage 2026-07-31", () => {
    expect(staleDays("2026-07-31", new Date("2026-08-07T12:00:00Z"))).toBe(7);
    expect(STALE_LIMIT_DAYS).toBe(90);
  });
  it("no banners when engine matches and vintage is fresh", () => {
    ui(new Date("2026-08-07T12:00:00Z"));
    expect(screen.queryByText(/desajuste del motor/i)).toBeNull();
    expect(screen.queryByText(/tiene \d+ días/)).toBeNull();
  });
  it("engine mismatch renders a visible error banner", () => {
    useAppHealth.setState({ engineMismatch: true });
    ui(new Date("2026-08-07T12:00:00Z"));
    expect(screen.getByText(/desajuste del motor: el cálculo local no coincide con la API/i)).toBeInTheDocument();
  });
  it("reports a gross-debt domain failure at an allowed combination of lever limits", () => {
    useScenarioStore.setState({ levers: {
      r: 0, prima: 0, sp: 4, lam: 2.5, pm: -50, tau: -5,
      z: -2, ext: 6, dem: -1, idx: -1.5,
    } });
    ui(new Date("2026-08-07T12:00:00Z"));
    expect(screen.getByText(/fuera del dominio de deuda bruta/)).toBeInTheDocument();
  });
  it("stale vintage (>90 días) renders a warning banner", async () => {
    ui(new Date("2026-12-01T12:00:00Z")); // 123 days after 2026-07-31
    expect(await screen.findByText(/tiene 123 días/)).toBeInTheDocument();
  });
});
