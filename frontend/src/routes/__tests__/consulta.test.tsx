import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DEFAULT_RAG_API_BASE, setRagConnection } from "../../api/client";
import type { Passage, RagChatRequest, RagCollection } from "../../api/types";
import { server } from "../../test/msw/server";
import Consulta from "../Consulta";

const PUBLIC: RagCollection = {
  id: "publicaciones", label: "Publicaciones institucionales", authority: "academico",
  note: "Fuentes públicas", documents: 3, chunks: 12,
};
const EMPTY_BOOKS: RagCollection = {
  id: "libros", label: "Libros vacíos", authority: "academico",
  note: "", documents: 0, chunks: 0,
};
const METHOD: RagCollection = {
  id: "metodo", label: "Método", authority: "propio", note: "", documents: 1, chunks: 2,
};
const PASSAGE: Passage = {
  chunk_id: 17, text: "La actividad responde a las condiciones monetarias.",
  title: "Informe económico público", collection: PUBLIC.id, authority: "academico",
  page: 4, section: null, score: 0.1, cita: "Informe económico público · p. 4",
};
const ANSWER = "Las condiciones monetarias afectan a la actividad [1].";
const clients: QueryClient[] = [];

function collectionsResponse(collections: RagCollection[], defaultCollection?: string) {
  return HttpResponse.json({
    vintage: "2026-07-31", computed_not_advice: true, collections,
    ...(defaultCollection ? { default_collection: defaultCollection } : {}),
    total_documents: collections.reduce((sum, collection) => sum + collection.documents, 0),
    total_chunks: collections.reduce((sum, collection) => sum + collection.chunks, 0),
  });
}

function advertise(collections: RagCollection[], base = DEFAULT_RAG_API_BASE) {
  server.use(http.get(`${base}/rag/collections`, () => collectionsResponse(collections)));
}

function answerStream(answer = ANSWER) {
  const frame = (event: string, data: unknown) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
  return new HttpResponse(
    frame("passages", { passages: [PASSAGE], grounded: true }) +
    frame("done", { answer, grounded: true, provider: "test", model: "test-model", error: null }),
    { headers: { "Content-Type": "text/event-stream" } },
  );
}

function ui() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  clients.push(client);
  return render(<QueryClientProvider client={client}><Consulta /></QueryClientProvider>);
}

beforeEach(() => {
  setRagConnection(null);
});

afterEach(() => {
  cleanup();
  for (const client of clients.splice(0)) client.clear();
  setRagConnection(null);
});

describe("Consulta — available library service", () => {
  it.each([
    { state: "missing", collections: [METHOD, PUBLIC] },
    { state: "empty", collections: [EMPTY_BOOKS, METHOD, PUBLIC] },
  ])("selects an available academic collection when libros is $state", async ({ collections }) => {
    advertise(collections);
    const received = vi.fn();
    server.use(http.post(`${DEFAULT_RAG_API_BASE}/rag/chat/stream`, async ({ request }) => {
      received(await request.json());
      return answerStream();
    }));
    ui();

    expect(await screen.findByText(`● ${PUBLIC.label}`)).toBeInTheDocument();
    expect(screen.queryByText(/corpus desconectado|biblioteca no disponible/i)).not.toBeInTheDocument();
    const question = screen.getByRole("textbox", { name: "Pregunta económica" });
    expect(question).toBeEnabled();
    await userEvent.type(question, "¿Cómo responde la actividad?");
    await userEvent.click(screen.getByRole("button", { name: "Preguntar" }));

    expect(await screen.findByText(ANSWER)).toBeInTheDocument();
    expect(received).toHaveBeenCalledWith({
      question: "¿Cómo responde la actividad?", collection: PUBLIC.id, top_k: 6,
    });
  });

  it("uses the advertised nonempty default collection even when libros is available", async () => {
    const books = { ...EMPTY_BOOKS, label: "Libros disponibles", documents: 2, chunks: 10 };
    const received = vi.fn();
    server.use(
      http.get(`${DEFAULT_RAG_API_BASE}/rag/collections`, () =>
        collectionsResponse([books, METHOD], METHOD.id),
      ),
      http.post(`${DEFAULT_RAG_API_BASE}/rag/chat/stream`, async ({ request }) => {
        received(await request.json());
        return answerStream();
      }),
    );
    ui();

    expect(await screen.findByText(`● ${METHOD.label}`)).toBeInTheDocument();
    await userEvent.type(screen.getByRole("textbox", { name: "Pregunta económica" }), "¿Cómo funciona el modelo?");
    await userEvent.click(screen.getByRole("button", { name: "Preguntar" }));

    expect(await screen.findByText(ANSWER)).toBeInTheDocument();
    expect(received).toHaveBeenCalledWith({
      question: "¿Cómo funciona el modelo?", collection: METHOD.id, top_k: 6,
    });
  });

  it("shows a collections 503 reason without claiming the corpus must be local", async () => {
    const detail = "El índice público se está actualizando. Reintenta en unos minutos.";
    server.use(http.get(`${DEFAULT_RAG_API_BASE}/rag/collections`, () =>
      HttpResponse.json({ detail }, { status: 503 }),
    ));
    ui();

    expect(await screen.findByRole("alert")).toHaveTextContent(detail);
    expect(screen.getByText("Biblioteca no disponible")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Pregunta económica" })).toBeDisabled();
    expect(screen.queryByText(/derechos de autor|copyright|sólo.*local|máquina local/i)).not.toBeInTheDocument();
  });

  it("shows the actual stream 503 reason from an otherwise available service", async () => {
    advertise([PUBLIC]);
    const detail = "El proveedor de respuestas no está disponible temporalmente.";
    server.use(http.post(`${DEFAULT_RAG_API_BASE}/rag/chat/stream`, () =>
      HttpResponse.json({ detail }, { status: 503 }),
    ));
    ui();
    await screen.findByText(`● ${PUBLIC.label}`);
    await userEvent.type(screen.getByRole("textbox", { name: "Pregunta económica" }), "¿Qué es la inflación?");
    await userEvent.click(screen.getByRole("button", { name: "Preguntar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(detail);
    expect(screen.queryByText(/derechos de autor|copyright|sólo.*local|máquina local/i)).not.toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("textbox", { name: "Pregunta económica" })).toBeEnabled());
  });

  it.each([
    { state: "no collections", collections: [] },
    { state: "only empty collections", collections: [EMPTY_BOOKS] },
  ])("disables questions and examples when the service advertises $state", async ({ collections }) => {
    advertise(collections);
    ui();

    expect(await screen.findByText("El servicio no anuncia ninguna colección con pasajes disponibles.")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Pregunta económica" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Preguntar" })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Qué es la curva de Phillips/ })).toBeDisabled();
  });

  it("loads collections from a changed connection and clears the previous answer and sources", async () => {
    advertise([PUBLIC]);
    server.use(http.post(`${DEFAULT_RAG_API_BASE}/rag/chat/stream`, () => answerStream()));
    const customBase = "https://public-library.example.test";
    const customCollection: RagCollection = { ...PUBLIC, id: "informes", label: "Informes abiertos" };
    const loadCustomCollections = vi.fn(() => collectionsResponse([customCollection]));
    const customRequest = vi.fn<(body: RagChatRequest) => void>();
    server.use(
      http.get(`${customBase}/rag/collections`, loadCustomCollections),
      http.post(`${customBase}/rag/chat/stream`, async ({ request }) => {
        customRequest(await request.json() as RagChatRequest);
        return answerStream("Respuesta del servicio seleccionado.");
      }),
    );
    ui();
    await screen.findByText(`● ${PUBLIC.label}`);
    await userEvent.type(screen.getByRole("textbox", { name: "Pregunta económica" }), "Explica la política monetaria");
    await userEvent.click(screen.getByRole("button", { name: "Preguntar" }));
    await screen.findByText(ANSWER);
    expect(screen.getByText(PASSAGE.cita)).toBeInTheDocument();

    await userEvent.click(screen.getByText("Conexión de biblioteca"));
    await userEvent.type(screen.getByLabelText("Dirección de otra biblioteca (opcional)"), customBase);
    await userEvent.click(screen.getByRole("button", { name: "Guardar conexión" }));

    expect(await screen.findByText(`● ${customCollection.label}`)).toBeInTheDocument();
    expect(loadCustomCollections).toHaveBeenCalledTimes(1);
    expect(screen.queryByText(ANSWER)).not.toBeInTheDocument();
    expect(screen.queryByText(PASSAGE.cita)).not.toBeInTheDocument();
    expect(screen.queryByText("Explica la política monetaria")).not.toBeInTheDocument();
    await userEvent.type(screen.getByRole("textbox", { name: "Pregunta económica" }), "Explica la inflación");
    await userEvent.click(screen.getByRole("button", { name: "Preguntar" }));
    expect(await screen.findByText("Respuesta del servicio seleccionado.")).toBeInTheDocument();
    expect(customRequest).toHaveBeenCalledWith(expect.objectContaining({ collection: customCollection.id }));
  });
});
