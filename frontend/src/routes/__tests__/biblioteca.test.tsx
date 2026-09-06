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
      http.post("http://localhost:8000/rag/chat/stream", () => {
        const frame = (e: string, d: unknown) =>
          `event: ${e}\ndata: ${JSON.stringify(d)}\n\n`;
        const stream = new ReadableStream({
          async start(c) {
            const enc = new TextEncoder();
            c.enqueue(enc.encode(frame("passages", {
              passages: [{
                chunk_id: 1,
                text: "El diferencial entre el tipo y el crecimiento determina la senda de la deuda.",
                title: "Banco de Espana - Documento Ocasional 1803 (ES)",
                collection: "libros", authority: "academico", page: 12,
                section: "3.1", score: 0.0387,
                cita: "Banco de Espana - Documento Ocasional 1803 (ES) · 3.1 · p. 12",
              }],
              grounded: true,
            })));
            // Hold the answer back so the passages-only window is observable.
            await delay(400);
            c.enqueue(enc.encode(frame("delta", {
              text: "La deuda crece cuando el tipo efectivo supera al crecimiento nominal [1].",
            })));
            c.enqueue(enc.encode(frame("done", {
              answer: "La deuda crece cuando el tipo efectivo supera al crecimiento nominal [1].",
              grounded: true, provider: "gemini", model: "gemini-2.5-flash", error: null,
            })));
            c.close();
          },
        });
        return new HttpResponse(stream, {
          headers: { "Content-Type": "text/event-stream" },
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

  // The public deploy ships without the RAG stack on purpose (copyrighted corpus,
  // local-only index). The API says so with a 503 + detail; the page must relay
  // that reason instead of asking whether the index is built.
  const DETAIL_503 =
    "La biblioteca no está disponible en este despliegue: el corpus con derechos " +
    "de autor y su índice vectorial viven sólo en la máquina local. (ModuleNotFoundError)";

  it("explains the library is local-only when /rag/collections answers 503", async () => {
    server.use(
      http.get("http://localhost:8000/rag/collections", () =>
        HttpResponse.json({ detail: DETAIL_503 }, { status: 503 }),
      ),
    );
    ui();
    await waitFor(() =>
      expect(screen.getByText(/sólo está disponible en el despliegue local/i)).toBeInTheDocument(),
    );
    expect(screen.getByText(/ModuleNotFoundError/)).toBeInTheDocument();
    expect(screen.queryByText(/¿Está el índice construido/)).not.toBeInTheDocument();
    expect(screen.getByLabelText("Pregunta")).toBeDisabled();
  });

  it("surfaces the server's reason when the chat stream answers 503", async () => {
    server.use(
      http.post("http://localhost:8000/rag/chat/stream", () =>
        HttpResponse.json({ detail: DETAIL_503 }, { status: 503 }),
      ),
    );
    ui();
    await waitFor(() => expect(screen.getByText("Manuales de economía")).toBeInTheDocument());
    await userEvent.type(screen.getByLabelText("Pregunta"), "por qué sube la deuda");
    await userEvent.click(screen.getByRole("button", { name: "preguntar" }));

    await waitFor(() =>
      expect(screen.getByText(/sólo está disponible en el despliegue local/i)).toBeInTheDocument(),
    );
    expect(screen.queryByText(/¿Está el índice construido/)).not.toBeInTheDocument();
  });

  it("keeps the generic message for a non-503 failure but shows the HTTP status", async () => {
    server.use(
      http.post("http://localhost:8000/rag/chat/stream", () =>
        HttpResponse.json({ detail: "boom" }, { status: 500 }),
      ),
    );
    ui();
    await waitFor(() => expect(screen.getByText("Manuales de economía")).toBeInTheDocument());
    await userEvent.type(screen.getByLabelText("Pregunta"), "por qué sube la deuda");
    await userEvent.click(screen.getByRole("button", { name: "preguntar" }));

    await waitFor(() => expect(screen.getByText(/No se pudo consultar la biblioteca/)).toBeInTheDocument());
    expect(screen.getByText(/boom/)).toBeInTheDocument();
  });
});
