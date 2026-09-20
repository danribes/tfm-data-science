import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { afterEach, describe, expect, it } from "vitest";
import { API_BASE, setRagConnection } from "../client";
import { useRagSearch } from "../hooks";
import { server } from "../../test/msw/server";

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    {children}
  </QueryClientProvider>;
}

const collections = {
  vintage: "2026-07-31", computed_not_advice: true,
  collections: [
    { id: "libros", label: "Libros privados", authority: "academico", note: "", documents: 0, chunks: 0 },
    { id: "publico", label: "Fuentes públicas", authority: "academico", note: "", documents: 2, chunks: 8 },
  ], total_documents: 2, total_chunks: 8,
};

afterEach(() => { setRagConnection(null); });

describe("source drawer library queries", () => {
  it("waits until opened, selects an advertised nonempty collection and isolates endpoint caches", async () => {
    let listings = 0;
    const requested: string[] = [];
    server.use(
      http.get(`${API_BASE}/rag/collections`, () => { listings++; return HttpResponse.json(collections); }),
      http.post(`${API_BASE}/rag/search`, async ({ request }) => {
        const body = await request.json() as { collection: string };
        requested.push(body.collection);
        return HttpResponse.json({ passages: [{ text: "Fuente pública" }] });
      }),
      http.get("https://private.example/rag/collections", () => HttpResponse.json(collections)),
      http.post("https://private.example/rag/search", () =>
        HttpResponse.json({ passages: [{ text: "Fuente privada" }] })),
    );
    const { result, rerender } = renderHook(({ open }) => useRagSearch("deuda pública", open), {
      initialProps: { open: false }, wrapper,
    });
    expect(listings).toBe(0);
    rerender({ open: true });
    await waitFor(() => expect(result.current.data?.passages[0].text).toBe("Fuente pública"));
    expect(requested).toEqual(["publico"]);
    act(() => setRagConnection("https://private.example", "session-secret"));
    await waitFor(() => expect(result.current.data?.passages[0].text).toBe("Fuente privada"));
  });

  it("passes the collections failure reason to the sources drawer without searching", async () => {
    server.use(http.get(`${API_BASE}/rag/collections`, () =>
      HttpResponse.json({ detail: "El índice público está en mantenimiento." }, { status: 503 })));
    const { result } = renderHook(() => useRagSearch("deuda pública", true), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toMatchObject({ detail: "El índice público está en mantenimiento." });
    expect(result.current.isPending).toBe(false);
    expect(result.current.data).toBeUndefined();
  });
});
