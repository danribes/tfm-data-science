import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { DEFAULT_RAG_API_BASE } from "../../api/client";
import { server } from "../../test/msw/server";
import { AnswerPanel } from "../AnswerPanel";
import { baseline } from "../../engine/spain";
import { Q02, Q03, Q10 } from "../../personas/questions";
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

describe("AnswerPanel · capa de fuentes cuando el servicio se reinicia", () => {
  // Hugging Face contesta 502 con una página HTML mientras el contenedor del
  // Space arranca o se reinicia tras un despliegue. No es la API quien falla,
  // y enseñar «HTTP 502» como respuesta definitiva deja la capa rota.
  const q = Q03.find((x) => x.concept === "esfuerzo hipotecario de los hogares")!;
  const open = () => userEvent.click(screen.getByRole("button", { name: /Fuentes sobre/ }));

  it("reintenta un 502 del proxy y acaba enseñando los pasajes", async () => {
    let calls = 0;
    server.use(http.post(`${DEFAULT_RAG_API_BASE}/rag/search`, () => {
      calls += 1;
      if (calls === 1) {
        return new HttpResponse("<html>502 Bad Gateway</html>",
          { status: 502, headers: { "Content-Type": "text/html" } });
      }
      return undefined; // el siguiente intento lo atiende el mock normal
    }));
    ui(q, Q03);
    await open();
    expect(await screen.findByText(/Documento Ocasional 1803/)).toBeInTheDocument();
    expect(screen.queryByText(/No se ha podido consultar el corpus/)).toBeNull();
    expect(calls).toBe(2);
  });

  it("no reintenta un error que la API explica: lo enseña a la primera", async () => {
    let calls = 0;
    server.use(http.post(`${DEFAULT_RAG_API_BASE}/rag/search`, () => {
      calls += 1;
      return HttpResponse.json({ detail: "La biblioteca no está disponible." }, { status: 503 });
    }));
    ui(q, Q03);
    await open();
    expect(await screen.findByText(/La biblioteca no está disponible/)).toBeInTheDocument();
    expect(calls).toBe(1);
  });
});

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

  it("under a question the backtest never covered, says so before showing the house-price test", async () => {
    const q = Q02.find((x) => x.series === "u")!;
    ui(q, Q02);
    await userEvent.click(screen.getByRole("button", { name: /inteligencia artificial/ }));
    expect(await screen.findByText(/no la hemos probado/)).toBeInTheDocument();
    expect(screen.getByText(/Sí la probamos con el precio de la vivienda/)).toBeInTheDocument();
    expect(screen.getByText("Resultado: gana la regla sencilla.")).toBeInTheDocument();
  });

  it("under a house-price question, does not claim it was untested", async () => {
    ui(Q03.find((x) => x.series === "precio")!, Q03);
    await userEvent.click(screen.getByRole("button", { name: /inteligencia artificial/ }));
    await screen.findByText("Resultado: gana la regla sencilla.");
    expect(screen.queryByText(/no la hemos probado/)).not.toBeInTheDocument();
  });
});

describe("AnswerPanel · qué cifra es la de cabecera", () => {
  it("names the youth rate under «¿Voy a encontrar trabajo?», not just «paro»", () => {
    ui(Q10.find((x) => x.series === "ujuv")!, Q10);
    // Headline label and the main chart title both say which rate it is.
    expect(screen.getAllByText("Paro juvenil (menores de 25)")).toHaveLength(2);
    expect(screen.getByText(/De cada cien jóvenes menores de 25 años/)).toBeInTheDocument();
  });

  it("says a change in a percentage in puntos, not in %", () => {
    const q = Q10.find((x) => x.series === "ujuv")!;
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const base = baseline();
    // A scenario whose youth rate sits 1,9 points under the base.
    const scn = { ...base, ujuv: base.ujuv.map((v) => v - 1.9) };
    render(
      <QueryClientProvider client={client}>
        <AnswerPanel q={q} all={Q10} scn={scn} base={base} k={24} year={2050} onAsk={() => {}} />
      </QueryClientProvider>,
    );
    expect(screen.getByText(/−1,9 puntos frente al escenario base/)).toBeInTheDocument();
    expect(screen.queryByText(/−1,9 % frente/)).not.toBeInTheDocument();
  });
});

describe("AnswerPanel · y en corto, con la sorna al final", () => {
  function panel(persona: string | undefined, shift: number) {
    const q = Q10.find((x) => x.series === "ujuv")!;
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const base = baseline();
    const scn = { ...base, ujuv: base.ujuv.map((v) => v + shift) };
    return render(
      <QueryClientProvider client={client}>
        <AnswerPanel q={q} all={Q10} scn={scn} base={base} k={24} year={2050} onAsk={() => {}} persona={persona} />
      </QueryClientProvider>,
    );
  }
  const paragraph = () => screen.getByText("Y en corto").parentElement!.querySelector("p")!.textContent!;

  it("one colloquial paragraph that ends on the young reader's ironic line", () => {
    panel("10", +2);
    const text = paragraph();
    expect(text).toMatch(/^Resumiendo:/);
    expect(text).toContain("no una bola de cristal");
    expect(text.trim()).toMatch(/la comida de casa no tiene rival\.$/);
    // The two blocks are one now.
    expect(screen.queryByText("Y con un poco de sorna")).not.toBeInTheDocument();
  });

  it("and the better-news line when the youth rate falls", () => {
    panel("10", -2);
    expect(paragraph().trim()).toMatch(/el casero también ha visto el escenario\.$/);
  });

  it("without a persona there is no joke to end on", () => {
    panel(undefined, +2);
    expect(paragraph().trim()).toMatch(/no una bola de cristal\.$/);
  });
});

describe("AnswerPanel · cómo se calcula, en llano", () => {
  it("leads with the plain mechanism and folds the engine shorthand away", async () => {
    const q = Q03.find((x) => x.series === "precio")!;
    const { container } = ui(q, Q03);
    await userEvent.click(screen.getByRole("button", { name: /Cómo se calcula este número/ }));
    const body = container.querySelector(".layer.open .layer-body")!;
    expect(body.firstElementChild!.textContent).toBe(q.plain);
    const details = body.querySelector("details.tech-details")!;
    expect(details.textContent).toContain("IPV_LR");
    // The shorthand is nowhere outside the technical note.
    const outside = [...body.children].filter((el) => !el.contains(details)).map((el) => el.textContent).join(" ");
    expect(outside).not.toContain("IPV_LR");
  });
});
