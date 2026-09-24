import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AnalogCard, closeness } from "../AnalogCard";
import type { AnalogMatch } from "../../api/types";

const match = (distance: number, over: Partial<AnalogMatch> = {}): AnalogMatch => ({
  rank: 1, iso3: "LBR", country_name: "Liberia", match_year: 2004, distance,
  dominant_lever: "prima",
  match_snapshot: { debt_gdp: 543.4, overall_balance_gdp: -0.6, lending_rate: 18.1, gdp_growth: 2.6, unemployment: 2.4, inflation: 7.8 },
  outcome: [], outcome_truncated: false, diffs: [], debt_payable_verdict: "not_assessed", narrative: "",
  ...over,
});

describe("AnalogCard — which country, and how close", () => {
  it("names the country, not its ISO code", () => {
    render(<AnalogCard matches={[match(0.3)]} />);
    expect(screen.getByRole("heading", { name: "Liberia · 2004" })).toBeInTheDocument();
    expect(screen.queryByText(/LBR/)).toBeNull();
  });

  it("labels closeness on the panel's own scale", () => {
    expect(closeness(0.22)).toBe("cercano");
    expect(closeness(0.6)).toBe("cercano");
    expect(closeness(1.4)).toBe("moderado");
    expect(closeness(6.15)).toBe("lejano");
  });

  it("warns that a distant best match is only the least different", () => {
    render(<AnalogCard matches={[match(6.15)]} />);
    expect(screen.getByText("parecido lejano")).toBeInTheDocument();
    expect(screen.getByText(/Ningún país del registro histórico se parece de verdad a este escenario/)).toBeInTheDocument();
    expect(screen.getByText(/Liberia en\s+2004 es sólo el menos distinto/)).toBeInTheDocument();
  });

  it("says nothing extra for a close match", () => {
    render(<AnalogCard matches={[match(0.3)]} />);
    expect(screen.getByText("parecido cercano")).toBeInTheDocument();
    expect(screen.queryByText(/Ningún país del registro histórico/)).toBeNull();
  });
});
