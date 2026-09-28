import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { ApiError, DEFAULT_RAG_API_BASE, ragChatStream } from "../client";
import { server } from "../../test/msw/server";

const STREAM = `${DEFAULT_RAG_API_BASE}/rag/chat/stream`;
const badGateway = () =>
  new HttpResponse("<html>502 Bad Gateway</html>", { status: 502, headers: { "Content-Type": "text/html" } });

describe("ragChatStream ante un reinicio del Space", () => {
  it("reintenta un 502 del proxy antes de abrir el flujo, y la respuesta llega entera", async () => {
    let calls = 0;
    server.use(http.post(STREAM, () => {
      calls += 1;
      return calls <= 2 ? badGateway() : undefined; // el tercero lo atiende el mock normal
    }));
    const deltas: string[] = [];
    let done = false;
    await ragChatStream({ question: "¿Qué es la curva de Phillips?" }, {
      onDelta: (t) => deltas.push(t),
      onDone: () => { done = true; },
    });
    expect(calls).toBe(3);
    expect(deltas.join("").trim().length).toBeGreaterThan(0);
    expect(done).toBe(true);
  });

  it("no reintenta un error que la API explica", async () => {
    let calls = 0;
    server.use(http.post(STREAM, () => {
      calls += 1;
      return HttpResponse.json({ detail: "La biblioteca no está disponible." }, { status: 503 });
    }));
    const err = await ragChatStream({ question: "¿Qué es la curva de Phillips?" }, {}).catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect((err as ApiError).detail).toBe("La biblioteca no está disponible.");
    expect(calls).toBe(1);
  });

  it("si quien pregunta cancela mientras el Space no responde, no vuelve a llamar", async () => {
    let calls = 0;
    const controller = new AbortController();
    server.use(http.post(STREAM, () => {
      calls += 1;
      controller.abort(); // la pregunta se cancela mientras el Space no responde
      return badGateway();
    }));
    const err = await ragChatStream({ question: "¿Qué es la curva de Phillips?" }, {}, controller.signal)
      .catch((e) => e);
    expect(err).toBeDefined();
    expect(err).not.toBeInstanceOf(ApiError);
    expect(calls).toBe(1);
  });
});
