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
    await userEvent.click(screen.getByRole("button", { name: /aprendizaje profundo sobre el precio de la vivienda/ }));
    expect(await screen.findByText(/con orígenes 2019Q4–2023Q4/)).toBeInTheDocument();
    expect(screen.getByText(/desde 2024Q1 quedan reservados, sin tocar/)).toBeInTheDocument();
    expect(screen.queryByText(/regla más tonta posible/)).not.toBeInTheDocument();
    // One word for the benchmark: the prose says «deriva», so the verdict does too.
    expect(screen.getByText("no bate a la deriva")).toBeInTheDocument();
    expect(screen.queryByText(/bate al drift/)).not.toBeInTheDocument();
  });

  it("is absent under a question the backtest never covered", () => {
    const q = Q02.find((x) => x.series === "u")!;
    ui(q, Q02);
    expect(screen.queryByRole("button", { name: /aprendizaje profundo/ })).not.toBeInTheDocument();
  });
});
