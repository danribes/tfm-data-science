import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const MAIN = "https://engine.example.test";
const RAG = "https://corpus.example.test";
const OTHER_RAG = "https://other-corpus.example.test";
const TOKEN = "session-only-corpus-secret";

function mockFetch() {
  const fetchMock = vi.fn<typeof fetch>(async (input) => {
    if (String(input).endsWith("/rag/chat/stream")) {
      return new Response(
        'event: passages\ndata: {"passages":[],"grounded":false}\n\n' +
        'event: done\ndata: {"answer":"No coverage","grounded":false,"provider":null,"model":null}\n\n',
        { headers: { "Content-Type": "text/event-stream" } },
      );
    }
    return Response.json({ status: "ok" });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function auth(init?: RequestInit): string | null {
  return new Headers(init?.headers).get("Authorization");
}

beforeEach(() => {
  vi.resetModules();
  vi.stubEnv("VITE_API_BASE", MAIN);
  vi.stubEnv("VITE_RAG_API_BASE", "");
  localStorage.clear();
  sessionStorage.clear();
  window.history.replaceState(null, "", "/");
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
  localStorage.clear();
  sessionStorage.clear();
  window.history.replaceState(null, "", "/");
  vi.resetModules();
});

describe("independent RAG connection", () => {
  it("falls back to the main API without a custom RAG connection", async () => {
    const fetchMock = mockFetch();
    const client = await import("../client");

    expect(client.API_BASE).toBe(MAIN);
    expect(client.DEFAULT_API_BASE).toBe(MAIN);
    expect(client.getRagConnection()).toMatchObject({
      baseUrl: MAIN, customBaseUrl: null, hasToken: false,
    });
    await client.api.ragCollections();
    expect(fetchMock.mock.calls[0][0]).toBe(`${MAIN}/rag/collections`);
    expect(auth(fetchMock.mock.calls[0][1])).toBeNull();
  });

  it("uses the build-time RAG target without repointing the engine", async () => {
    vi.stubEnv("VITE_RAG_API_BASE", RAG);
    const fetchMock = mockFetch();
    const client = await import("../client");

    expect(client.getRagConnection()).toMatchObject({
      baseUrl: RAG, customBaseUrl: null, hasToken: false,
    });
    await client.api.health();
    await client.api.ragCollections();
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      `${MAIN}/health`, `${RAG}/rag/collections`,
    ]);
  });

  it("migrates a legacy override to RAG only and removes the legacy key", async () => {
    localStorage.setItem("evo.apiBase", `${RAG}/`);
    const fetchMock = mockFetch();
    const client = await import("../client");

    expect(localStorage.getItem("evo.apiBase")).toBeNull();
    expect(localStorage.getItem("evo.ragApiBase")).toBe(RAG);
    expect(client.getRagConnection()).toMatchObject({
      baseUrl: RAG, customBaseUrl: RAG, hasToken: false,
    });
    expect(client.API_BASE).toBe(MAIN);
    await client.api.health();
    await client.api.ragCollections();
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      `${MAIN}/health`, `${RAG}/rag/collections`,
    ]);
  });

  it("keeps an explicit RAG override when a legacy override also exists", async () => {
    localStorage.setItem("evo.apiBase", OTHER_RAG);
    localStorage.setItem("evo.ragApiBase", RAG);
    const client = await import("../client");

    expect(client.getRagConnection().baseUrl).toBe(RAG);
    expect(localStorage.getItem("evo.apiBase")).toBeNull();
  });

  it.each(["api", "rag"])("?%s=reset removes URL overrides and session credentials before import", async (param) => {
    vi.stubEnv("VITE_RAG_API_BASE", OTHER_RAG);
    localStorage.setItem("evo.apiBase", RAG);
    localStorage.setItem("evo.ragApiBase", RAG);
    sessionStorage.setItem("evo.ragAuth", JSON.stringify({ baseUrl: RAG, token: TOKEN }));
    window.history.replaceState(null, "", `/biblioteca?${param}=reset&h=2035#sources`);

    const client = await import("../client");

    expect(client.getRagConnection()).toMatchObject({
      baseUrl: OTHER_RAG, customBaseUrl: null, hasToken: false,
    });
    expect(localStorage.getItem("evo.apiBase")).toBeNull();
    expect(localStorage.getItem("evo.ragApiBase")).toBeNull();
    expect(sessionStorage.getItem("evo.ragAuth")).toBeNull();
    expect(new URLSearchParams(location.search).has(param)).toBe(false);
    expect(new URLSearchParams(location.search).get("h")).toBe("2035");
    expect(location.hash).toBe("#sources");
  });

  it("routes JSON and streaming RAG calls with the token while main routes stay unauthenticated", async () => {
    const fetchMock = mockFetch();
    const client = await import("../client");
    client.setRagConnection(`${RAG}/`, TOKEN);
    const signal = new AbortController().signal;
    const onDone = vi.fn();

    await client.api.health();
    await client.api.scenario({ horizon: 2035 });
    await client.api.ragEval();
    await client.api.ragCollections();
    await client.api.ragSearch({ query: "inflación" }, signal);
    await client.api.ragChat({ question: "inflación" }, signal);
    await client.ragChatStream({ question: "inflación" }, { onDone }, signal);

    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      `${MAIN}/health`, `${MAIN}/scenario`, `${RAG}/rag/eval`,
      `${RAG}/rag/collections`, `${RAG}/rag/search`, `${RAG}/rag/chat`, `${RAG}/rag/chat/stream`,
    ]);
    for (const [, init] of fetchMock.mock.calls.slice(0, 2)) expect(auth(init)).toBeNull();
    for (const [, init] of fetchMock.mock.calls.slice(2)) expect(auth(init)).toBe(`Bearer ${TOKEN}`);
    for (const [, init] of fetchMock.mock.calls.slice(4)) {
      expect(init?.method).toBe("POST");
      expect(init?.signal).toBe(signal);
      expect(new Headers(init?.headers).get("Content-Type")).toBe("application/json");
    }
    expect(onDone).toHaveBeenCalledWith(expect.objectContaining({ answer: "No coverage" }));
    expect(client.API_BASE).toBe(MAIN);
    expect(client.DEFAULT_API_BASE).toBe(MAIN);
  });

  it("leaves the engine usable when a custom RAG endpoint is unreachable", async () => {
    const fetchMock = mockFetch();
    fetchMock.mockImplementation(async (input) => {
      if (String(input).startsWith(RAG)) throw new TypeError("connection refused");
      return Response.json({ status: "ok" });
    });
    const client = await import("../client");
    client.setRagConnection(RAG, TOKEN);

    await expect(client.api.ragCollections()).rejects.toThrow();
    await expect(client.api.health()).resolves.toEqual({ status: "ok" });
    await expect(client.api.scenario({ horizon: 2035 })).resolves.toEqual({ status: "ok" });
    expect(fetchMock.mock.calls.slice(1).map(([url]) => url)).toEqual([
      `${MAIN}/health`, `${MAIN}/scenario`,
    ]);
    for (const [, init] of fetchMock.mock.calls.slice(1)) expect(auth(init)).toBeNull();
  });

  it("keeps the secret in session storage and restores it only for its bound endpoint", async () => {
    mockFetch();
    let client = await import("../client");
    client.setRagConnection(RAG, TOKEN);

    expect(localStorage.getItem("evo.ragApiBase")).toBe(RAG);
    expect(JSON.stringify(localStorage)).not.toContain(TOKEN);
    expect(JSON.parse(sessionStorage.getItem("evo.ragAuth")!)).toEqual({ baseUrl: RAG, token: TOKEN });
    vi.resetModules();
    client = await import("../client");
    expect(client.getRagConnection().hasToken).toBe(true);

    localStorage.setItem("evo.ragApiBase", OTHER_RAG);
    vi.resetModules();
    client = await import("../client");
    expect(client.getRagConnection()).toMatchObject({ baseUrl: OTHER_RAG, hasToken: false });
  });

  it("clears the previous endpoint's token and allows an explicit token for the replacement", async () => {
    const fetchMock = mockFetch();
    const client = await import("../client");
    client.setRagConnection(RAG, TOKEN);
    client.setRagConnection(OTHER_RAG);

    expect(client.getRagConnection().hasToken).toBe(false);
    expect(sessionStorage.getItem("evo.ragAuth")).toBeNull();
    await client.api.ragCollections();
    expect(fetchMock.mock.calls[0][0]).toBe(`${OTHER_RAG}/rag/collections`);
    expect(auth(fetchMock.mock.calls[0][1])).toBeNull();

    client.setRagConnection(OTHER_RAG, "replacement-secret");
    await client.api.ragCollections();
    expect(auth(fetchMock.mock.calls[1][1])).toBe("Bearer replacement-secret");
    expect(JSON.parse(sessionStorage.getItem("evo.ragAuth")!)).toEqual({
      baseUrl: OTHER_RAG, token: "replacement-secret",
    });
  });

  it("never attaches a corpus token when the custom RAG target is the main API", async () => {
    const fetchMock = mockFetch();
    const client = await import("../client");
    client.setRagConnection(`${MAIN}/`, TOKEN);

    await client.api.ragCollections();
    await client.api.health();
    await client.ragChatStream({ question: "inflación" }, {});
    for (const [url, init] of fetchMock.mock.calls) {
      expect(String(url).startsWith(MAIN)).toBe(true);
      expect(auth(init)).toBeNull();
    }
  });

  it("resetting the connection clears custom credentials and restores the build-time RAG target", async () => {
    vi.stubEnv("VITE_RAG_API_BASE", OTHER_RAG);
    const fetchMock = mockFetch();
    const client = await import("../client");
    client.setRagConnection(RAG, TOKEN);
    client.setRagConnection(null);

    expect(client.getRagConnection()).toMatchObject({
      baseUrl: OTHER_RAG, customBaseUrl: null, hasToken: false,
    });
    expect(localStorage.getItem("evo.ragApiBase")).toBeNull();
    expect(sessionStorage.getItem("evo.ragAuth")).toBeNull();
    await client.api.ragCollections();
    expect(fetchMock.mock.calls[0][0]).toBe(`${OTHER_RAG}/rag/collections`);
    expect(auth(fetchMock.mock.calls[0][1])).toBeNull();
  });

  it("provides stable snapshots and notifies subscribers when the connection changes", async () => {
    const client = await import("../client");
    const initial = client.getRagConnection();
    expect(client.getRagConnection()).toBe(initial);
    const listener = vi.fn();
    const unsubscribe = client.subscribeRagConnection(listener);

    client.setRagConnection(RAG, TOKEN);
    const changed = client.getRagConnection();
    expect(changed).not.toBe(initial);
    expect(changed.revision).toBeGreaterThan(initial.revision);
    expect(client.getRagConnection()).toBe(changed);
    expect(listener).toHaveBeenCalledTimes(1);

    unsubscribe();
    client.setRagConnection(null);
    expect(listener).toHaveBeenCalledTimes(1);
  });
});
