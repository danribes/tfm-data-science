import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "../../test/msw/server";
import { AnalogPanel } from "../../components/AnalogPanel";
import { AnalogCard } from "../../components/AnalogCard";
import { AnalogDiffRow } from "../../components/AnalogDiffRow";
import type { AnalogMatch, StructuralDiff } from "../../api/types";
import { BASE_LEVERS } from "../../engine/vintage";

// No setupServer/beforeAll/afterEach/afterAll here —
// global src/test/setup.ts already handles server lifecycle.

function makeQC() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

function ui(children: React.ReactNode) {
  return render(
    <QueryClientProvider client={makeQC()}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AnalogPanel", () => {
  it("renders closed by default — button visible, card content hidden", () => {
    ui(<AnalogPanel levers={BASE_LEVERS} horizon={10} />);
    expect(screen.getByRole("button", { name: /análogos históricos/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /buscar análogo histórico/i })).toBeNull();
  });

  it("expands on header click — search button and description visible", () => {
    ui(<AnalogPanel levers={BASE_LEVERS} horizon={10} />);
    fireEvent.click(screen.getByRole("button", { name: /análogos históricos/i }));
    expect(screen.getByRole("button", { name: /buscar análogo histórico/i })).toBeInTheDocument();
  });

  it("calls API and shows cards after clicking search button", async () => {
    ui(<AnalogPanel levers={BASE_LEVERS} horizon={10} />);
    fireEvent.click(screen.getByRole("button", { name: /análogos históricos/i }));
    fireEvent.click(screen.getByRole("button", { name: /buscar análogo histórico/i }));
    await waitFor(() => expect(screen.getByText("Irlanda · 2010")).toBeInTheDocument());
    expect(screen.getByText(/Portugal.*2011/)).toBeInTheDocument();
    expect(screen.getByText(/Bélgica.*1993/)).toBeInTheDocument();
  });

  it("shows deterministic template when rag_available is false", async () => {
    ui(<AnalogPanel levers={BASE_LEVERS} horizon={10} />);
    fireEvent.click(screen.getByRole("button", { name: /análogos históricos/i }));
    fireEvent.click(screen.getByRole("button", { name: /buscar análogo histórico/i }));
    await waitFor(() =>
      expect(
        screen.getByText(/análisis narrativo solo disponible en despliegue local/i),
      ).toBeInTheDocument(),
    );
  });

  it("shows error state on network failure", async () => {
    server.use(
      http.post("*/scenario/analog", () => HttpResponse.error()),
    );
    ui(<AnalogPanel levers={BASE_LEVERS} horizon={10} />);
    fireEvent.click(screen.getByRole("button", { name: /análogos históricos/i }));
    fireEvent.click(screen.getByRole("button", { name: /buscar análogo histórico/i }));
    await waitFor(() =>
      expect(screen.getByText(/error al buscar análogos/i)).toBeInTheDocument(),
    );
  });
});

const MOCK_MATCHES: AnalogMatch[] = [1, 2, 3].map((rank) => ({
  rank,
  iso3: rank === 1 ? "IRL" : rank === 2 ? "PRT" : "BEL",
  country_name: rank === 1 ? "Irlanda" : rank === 2 ? "Portugal" : "Bélgica",
  match_year: rank === 1 ? 2010 : rank === 2 ? 2011 : 1993,
  distance: rank * 0.3,
  dominant_lever: "prima",
  match_snapshot: {
    debt_gdp: 100,
    primary_balance_gdp: -4,
    interest_rate_10y: 5,
    gdp_growth: 1,
    unemployment: 10,
    inflation: 2,
    r_minus_g: 4,
  },
  outcome: [
    {
      year_offset: 1,
      debt_gdp: 105,
      gdp_growth: 1.2,
      primary_balance_gdp: -3,
      r_minus_g: 3.8,
      truncated: false,
    },
  ],
  outcome_truncated: false,
  debt_payable_verdict: "auto",
  narrative: null,
  diffs: [
    {
      dimension: "emu_member",
      label: "Zona euro",
      spain_value: "Sí",
      analog_value: "Sí",
      direction: "converge",
    },
  ],
}));

describe("AnalogCard", () => {
  it("renders tab buttons and active card header for all three matches", () => {
    render(<AnalogCard matches={MOCK_MATCHES} />);
    expect(screen.getByText("#1 Irlanda · 2010")).toBeInTheDocument();
    expect(screen.getByText("#2 Portugal · 2011")).toBeInTheDocument();
    expect(screen.getByText("#3 Bélgica · 1993")).toBeInTheDocument();
    // Active card h4
    expect(screen.getByText("Irlanda · 2010")).toBeInTheDocument();
  });

  it("switches active card on tab click", () => {
    render(<AnalogCard matches={MOCK_MATCHES} />);
    fireEvent.click(screen.getByText("#2 Portugal · 2011"));
    expect(screen.getByText("Portugal · 2011")).toBeInTheDocument();
  });
});

function makeRow(direction: StructuralDiff["direction"]): StructuralDiff {
  return {
    dimension: "emu_member",
    label: "Zona euro",
    spain_value: "Sí",
    analog_value: "Sí",
    direction,
  };
}

describe("AnalogDiffRow", () => {
  it("renders converge icon ✓", () => {
    render(
      <table>
        <tbody>
          <AnalogDiffRow diff={makeRow("converge")} />
        </tbody>
      </table>,
    );
    expect(screen.getByText("✓")).toBeInTheDocument();
    expect(screen.getByLabelText("converge")).toBeInTheDocument();
  });

  it("renders diverge icon ✗", () => {
    render(
      <table>
        <tbody>
          <AnalogDiffRow diff={makeRow("diverge")} />
        </tbody>
      </table>,
    );
    expect(screen.getByText("✗")).toBeInTheDocument();
    expect(screen.getByLabelText("diverge")).toBeInTheDocument();
  });

  it("renders neutral icon ≈", () => {
    render(
      <table>
        <tbody>
          <AnalogDiffRow diff={makeRow("neutral")} />
        </tbody>
      </table>,
    );
    expect(screen.getByText("≈")).toBeInTheDocument();
    expect(screen.getByLabelText("neutral")).toBeInTheDocument();
  });
});
