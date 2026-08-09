import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, delay, http } from "msw";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import Biblioteca from "../Biblioteca";
import { server } from "../../test/msw/server";

function ui() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter><Biblioteca /></MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Biblioteca — chat con citas", () => {
  it("lists every collection with its authority", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("Manuales de economía")).toBeInTheDocument());
    expect(screen.getByText("Canal crack23")).toBeInTheDocument();
    expect(screen.getByText("Método y diseño del propio modelo")).toBeInTheDocument();
    // The authority tag is the point: a channel must not look like a textbook.
    expect(screen.getByText("opinion")).toBeInTheDocument();
    expect(screen.getByText("academico")).toBeInTheDocument();
  });

  it("shows how much of the corpus is indexed", async () => {
    ui();
    await waitFor(() =>
      expect(screen.getByText(/473 documentos · 17\.169 pasajes indexados/)).toBeInTheDocument(),
    );
  });

  it("answers a question and cites the passage it used", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("Manuales de economía")).toBeInTheDocument());
    await userEvent.type(screen.getByLabelText("Pregunta"), "por qué sube la deuda");
    await userEvent.click(screen.getByRole("button", { name: "preguntar" }));

    await waitFor(() => expect(screen.getByText(/La deuda crece cuando/)).toBeInTheDocument());
    expect(screen.getByText(/Documento Ocasional 1803/)).toBeInTheDocument();
    expect(screen.getByText("[1]")).toBeInTheDocument();
  });

  it("says the corpus does not cover it instead of inventing an answer", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("Manuales de economía")).toBeInTheDocument());
    await userEvent.type(screen.getByLabelText("Pregunta"), "qué dice sobre la fusión fría");
    await userEvent.click(screen.getByRole("button", { name: "preguntar" }));

    await waitFor(() => expect(screen.getByText("El corpus no cubre esta pregunta.")).toBeInTheDocument());
    expect(screen.getByText(/sin pasajes/)).toBeInTheDocument();
    expect(screen.queryByText("[1]")).not.toBeInTheDocument();
  });

  it("discloses which model wrote the answer", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("Manuales de economía")).toBeInTheDocument());
    await userEvent.click(screen.getAllByRole("button", { name: /multiplicador fiscal/ })[0]);
    await waitFor(() =>
      expect(screen.getByText(/gemini-2\.5-flash/)).toBeInTheDocument(),
    );
    expect(screen.getByText(/El modelo elige las palabras/)).toBeInTheDocument();
  });

  it("an example question fills the box and asks it", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("Manuales de economía")).toBeInTheDocument());
    await userEvent.click(screen.getAllByRole("button", { name: /proyecciones locales/ })[0]);
    await waitFor(() => expect(screen.getByText(/La deuda crece cuando/)).toBeInTheDocument());
    expect((screen.getByLabelText("Pregunta") as HTMLInputElement).value)
      .toMatch(/proyecciones locales/);
  });

  it("switching collection carries the authority through to the citation", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("Canal crack23")).toBeInTheDocument());
    await userEvent.click(screen.getByText("Canal crack23"));
    await userEvent.type(screen.getByLabelText("Pregunta"), "la deuda");
    await userEvent.click(screen.getByRole("button", { name: "preguntar" }));

    await waitFor(() => expect(screen.getByText(/Documento Ocasional 1803/)).toBeInTheDocument());
    const list = screen.getByRole("list");
    expect(within(list).getByText("opinión — no es fuente académica")).toBeInTheDocument();
  });

  it("shows retrieved passages while the prose is still being written", async () => {
    // The latency fix: retrieval (~0,8 s) and generation (~4,6 s) fire together,
    // so the evidence must be readable before the answer lands. Delaying only
    // /rag/chat reproduces that window deterministically.
    server.use(
      http.post("http://localhost:8000/rag/chat", async () => {
        await delay(400);
        return HttpResponse.json({
          vintage: "2026-07-31", computed_not_advice: true,
          question: "x", collection: "libros",
          answer: "La deuda crece cuando el tipo efectivo supera al crecimiento nominal [1].",
          passages: [], grounded: true, provider: "gemini",
          model: "gemini-2.5-flash", error: null,
        });
      }),
    );
    ui();
    await waitFor(() => expect(screen.getByText("Manuales de economía")).toBeInTheDocument());
    await userEvent.click(screen.getAllByRole("button", { name: /multiplicador fiscal/ })[0]);

    // Passages first, with the interim wording…
    await waitFor(() => expect(screen.getByText(/Pasajes recuperados/)).toBeInTheDocument());
    expect(screen.getByText(/Redactando la respuesta/)).toBeInTheDocument();
    expect(screen.getByText(/Documento Ocasional 1803/)).toBeInTheDocument();

    // …then the prose replaces the placeholder.
    await waitFor(() => expect(screen.getByText(/La deuda crece cuando/)).toBeInTheDocument());
    expect(screen.queryByText(/Redactando la respuesta/)).not.toBeInTheDocument();
  });

  it("the scenario toggle is off by default", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("Manuales de economía")).toBeInTheDocument());
    expect(screen.getByRole("checkbox")).not.toBeChecked();
  });

  it("refuses to send an empty question", async () => {
    ui();
    await waitFor(() => expect(screen.getByText("Manuales de economía")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "preguntar" })).toBeDisabled();
  });
});
