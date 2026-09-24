import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { AnswerPanel } from "../AnswerPanel";
import { baseline } from "../../engine/spain";
import { Q02, Q03 } from "../../personas/questions";
import type { PersonaQuestion } from "../../personas/questions";

function ui(q: PersonaQuestion, all: PersonaQuestion[]) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const scn = baseline();
  return render(
    <QueryClientProvider client={client}>
      <AnswerPanel q={q} all={all} scn={scn} base={scn} k={0} year={2026} onAsk={() => {}} />
    </QueryClientProvider>,
  );
}

describe("AnswerPanel · capa del modelo de aprendizaje profundo", () => {
  it("under a house-price question, states the scored window and not the held-out tail", async () => {
    const q = Q03.find((x) => x.series === "precio")!;
    ui(q, Q03);
    await userEvent.click(screen.getByRole("button", { name: /inteligencia artificial/ }));
    // Origins 2019Q4–2023Q4 with targets before 2024Q1: forecasts of 2020–2023.
    expect(await screen.findByText(/entre\s+2020\s+y\s+2023/)).toBeInTheDocument();
    expect(screen.getByText(/desde 2024 los guardamos sin tocar/)).toBeInTheDocument();
    expect(screen.queryByText(/regla más tonta posible/)).not.toBeInTheDocument();
    expect(screen.getByText("Resultado: gana la regla sencilla.")).toBeInTheDocument();
    expect(screen.queryAllByText(/drift|MASE|CCAA/)).toHaveLength(0);
  });

  it("says the horizons in months, not in quarter codes", async () => {
    ui(Q03.find((x) => x.series === "precio")!, Q03);
    await userEvent.click(screen.getByRole("button", { name: /inteligencia artificial/ }));
    const rows = await screen.findAllByRole("row");
    expect(rows.slice(1).map((r) => (r as HTMLTableRowElement).cells[0].textContent))
      // The mock serves h = 1, 2, 4, 8; h = 8 is outside the rule and is left out.
      .toEqual(["3 meses", "6 meses", "1 año"]);
  });

  it("is absent under a question the backtest never covered", () => {
    const q = Q02.find((x) => x.series === "u")!;
    ui(q, Q02);
    expect(screen.queryByRole("button", { name: /inteligencia artificial/ })).not.toBeInTheDocument();
  });
});
