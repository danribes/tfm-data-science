import { render, screen } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it } from "vitest";
import { Warnings } from "../Warnings";
import { queryClient } from "../../api/hooks";
import { STALE_LIMIT_DAYS, staleDays, useAppHealth } from "../../state/appHealth";

// `now` is injectable so tests never need fake timers (they fight waitFor/React Query).
const ui = (now?: Date) =>
  render(<QueryClientProvider client={queryClient}><Warnings now={now} /></QueryClientProvider>);

describe("Warnings — honesty banners (spec §8)", () => {
  beforeEach(() => {
    useAppHealth.setState({ engineMismatch: false, extraWarnings: [] });
    queryClient.clear();
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
  it("stale vintage (>90 días) renders a warning banner", async () => {
    ui(new Date("2026-12-01T12:00:00Z")); // 123 days after 2026-07-31
    expect(await screen.findByText(/tiene 123 días/)).toBeInTheDocument();
  });
});
