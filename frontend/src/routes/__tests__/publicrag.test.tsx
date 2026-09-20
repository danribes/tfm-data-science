import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { DEFAULT_RAG_API_BASE, setRagConnection } from "../../api/client";
import type { RagChatRequest, RagCollectionsResponse, RagSearchRequest } from "../../api/types";
import { AnswerPanel } from "../../components/AnswerPanel";
import { baseline } from "../../engine/spain";
import { Q03 } from "../../personas/questions";
import { server } from "../../test/msw/server";
import Biblioteca from "../Biblioteca";
import Consulta from "../Consulta";

const PUBLIC: RagCollectionsResponse = {
  vintage: "2026-07-31", computed_not_advice: true,
  corpus_scope: "public_project_docs", retrieval_mode: "lexical", default_collection: "metodo",
  collections: [
    { id: "defensa_tfm", label: "Guía de defensa", authority: "propio", note: "Documentación propia", documents: 1, chunks: 3 },
    { id: "metodo", label: "Método público", authority: "propio", note: "Documentación propia", documents: 5, chunks: 17 },
  ], total_documents: 6, total_chunks: 20,
};
const NO_EVAL = "No hay una evaluación de calidad publicada para este modo público.";
const publicPassage = (collection: string) => ({
  chunk_id: 1, text: "El modelo produce escenarios condicionados a sus supuestos.",
  title: "Memoria del TFM", collection, authority: "propio", page: null,
  section: "Límites", score: 1, cita: "Memoria del TFM · Límites",
});
const clients: QueryClient[] = [];
const requests: RagChatRequest[] = [];

function ui(children: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  clients.push(client);
  return render(<QueryClientProvider client={client}>{children}</QueryClientProvider>);
}

beforeEach(() => {
  setRagConnection(null);
  requests.length = 0;
  server.use(
    http.get(`${DEFAULT_RAG_API_BASE}/rag/collections`, () => HttpResponse.json(PUBLIC)),
    http.get(`${DEFAULT_RAG_API_BASE}/rag/eval`, () => HttpResponse.json({ available: false, note: NO_EVAL })),
    http.post(`${DEFAULT_RAG_API_BASE}/rag/chat/stream`, async ({ request }) => {
      const body = await request.json() as RagChatRequest;
      requests.push(body);
      if (!PUBLIC.collections.some((collection) => collection.id === body.collection)) {
        return HttpResponse.json({ detail: "Colección no publicada" }, { status: 422 });
      }
      const frame = (event: string, data: unknown) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
      return new HttpResponse(
        frame("passages", { passages: [publicPassage(body.collection!)], grounded: true }) +
        frame("done", { answer: "Son escenarios condicionales [1].", grounded: true, provider: "test", model: "test", error: null }),
        { headers: { "Content-Type": "text/event-stream" } },
      );
    }),
  );
});

afterEach(() => {
  cleanup();
  for (const client of clients.splice(0)) client.clear();
  setRagConnection(null);
});

describe("public project library", () => {
  it("Biblioteca uses the advertised default, labels own documents and exposes only available collections", async () => {
    ui(<Biblioteca />);
    expect(await screen.findByText(/6 documentos · 20 pasajes indexados/)).toBeInTheDocument();
    expect(screen.getByText(/Biblioteca pública de documentación propia/)).toHaveTextContent(/coincidencias de palabras/);
    expect(screen.getByRole("button", { name: /Método público/ })).toHaveClass("on");
    expect(screen.queryByRole("button", { name: /Economía y métodos|libros/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /qué dice la literatura/ })).not.toBeInTheDocument();
    expect(await screen.findByText(NO_EVAL)).toBeInTheDocument();
    expect(screen.queryByText("97 %")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Por qué el modelo produce escenarios/ }));
    expect(await screen.findByText("Son escenarios condicionales [1].")).toBeInTheDocument();
    expect(requests[0].collection).toBe("metodo");
    expect(within(screen.getByRole("list")).getByText("documentación de este modelo")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Guía de defensa/ }));
    await userEvent.click(screen.getByRole("button", { name: "preguntar" }));
    await waitFor(() => expect(requests).toHaveLength(2));
    expect(requests[1].collection).toBe("defensa_tfm");
  });

  it("Consulta offers project questions and requests metodo when no books are advertised", async () => {
    ui(<Consulta />);
    expect(await screen.findByText("● Método público")).toBeInTheDocument();
    expect(screen.getByText(/Biblioteca pública de documentación propia/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /expectativas racionales/ })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Qué parámetros de vivienda/ }));
    expect(await screen.findByText("Son escenarios condicionales [1].")).toBeInTheDocument();
    expect(requests[0].collection).toBe("metodo");
    expect(screen.getByText("documentación del modelo")).toBeInTheDocument();
  });

  it("the persona source drawer retrieves public documentation without presenting it as academic literature", async () => {
    const searches: RagSearchRequest[] = [];
    server.use(http.post(`${DEFAULT_RAG_API_BASE}/rag/search`, async ({ request }) => {
      const body = await request.json() as RagSearchRequest;
      searches.push(body);
      return HttpResponse.json({ ...body, passages: [publicPassage(body.collection!)] });
    }));
    const scn = baseline();
    ui(<AnswerPanel q={Q03[0]} all={Q03} scn={scn} base={scn} k={0} year={2026} onAsk={() => {}} />);
    expect(searches).toHaveLength(0);
    expect(screen.queryByText(/Qué dice la literatura/)).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Fuentes sobre/ }));
    expect(await screen.findByText("Memoria del TFM · Límites")).toBeInTheDocument();
    expect(screen.getByText(/no sustituye fuentes académicas independientes/)).toBeInTheDocument();
    expect(searches).toEqual([{ query: Q03[0].concept, collection: "metodo", top_k: 4 }]);
  });
});
