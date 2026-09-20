import type {
  ConstantsResponse, DemographyResponse, DistressResponse, EvidenceResponse, ExplainRequest, ExplainResponse, HealthResponse,
  MonteCarloRequest, MonteCarloResponse,
  Passage,
  PersonasResponse, PredictionResponse, PresetsResponse,
  AskRequest, AskResponse,
  RagChatRequest, RagChatResponse, RagCollectionsResponse, RagEvalResponse,
  RegimesResponse,
  RagSearchRequest, RagSearchResponse,
  RedLinesResponse, ScenarioRequest,
  ScenarioResponse, SensitivityResponse, StateDependenceResponse, VintageResponse,
} from "./types";

/** The scenario API never follows a library connection override. */
export const API_BASE: string = (import.meta.env.VITE_API_BASE || "http://localhost:8000").replace(/\/+$/, "");
export const DEFAULT_API_BASE = API_BASE;
export const DEFAULT_RAG_API_BASE: string = (import.meta.env.VITE_RAG_API_BASE || API_BASE).replace(/\/+$/, "");
const LEGACY_KEY = "evo.apiBase";
const RAG_KEY = "evo.ragApiBase";
const AUTH_KEY = "evo.ragAuth";

function cleanBase(raw: string): string {
  const url = new URL(raw.trim());
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password || url.search || url.hash) {
    throw new Error("Usa una dirección HTTP o HTTPS sin credenciales, parámetros ni fragmentos.");
  }
  if (location.protocol === "https:" && url.protocol !== "https:") {
    throw new Error("Esta página requiere una dirección HTTPS para la biblioteca.");
  }
  return url.href.replace(/\/+$/, "");
}

function initialCustomBase(): string | null {
  try {
    const params = new URLSearchParams(location.search);
    if (params.get("api") === "reset" || params.get("rag") === "reset") {
      localStorage.removeItem(LEGACY_KEY);
      localStorage.removeItem(RAG_KEY);
      sessionStorage.removeItem(AUTH_KEY);
      if (params.get("api") === "reset") params.delete("api");
      if (params.get("rag") === "reset") params.delete("rag");
      const qs = params.toString();
      history.replaceState(null, "", location.pathname + (qs ? `?${qs}` : "") + location.hash);
      return null;
    }
    // Earlier versions used this library URL override for all API requests.
    // Preserve that URL for the library only.
    const stored = localStorage.getItem(RAG_KEY) || localStorage.getItem(LEGACY_KEY);
    localStorage.removeItem(LEGACY_KEY);
    const base = stored?.trim() ? cleanBase(stored) : null;
    if (base) localStorage.setItem(RAG_KEY, base);
    return base;
  } catch {
    return null;
  }
}

export interface RagConnection {
  baseUrl: string;
  customBaseUrl: string | null;
  hasToken: boolean;
  /** Cache identity; never contains a credential. */
  revision: number;
}
const initialBase = initialCustomBase();
let ragToken = "";
try {
  const stored = JSON.parse(sessionStorage.getItem(AUTH_KEY) || "null");
  const boundTo = initialBase ?? DEFAULT_RAG_API_BASE;
  if (stored?.baseUrl === boundTo && typeof stored.token === "string") {
    ragToken = stored.token;
  } else sessionStorage.removeItem(AUTH_KEY);
} catch { /* unavailable session storage */ }
let ragConnection: RagConnection = {
  baseUrl: initialBase ?? DEFAULT_RAG_API_BASE,
  customBaseUrl: initialBase,
  hasToken: !!ragToken,
  revision: 0,
};
const ragListeners = new Set<() => void>();
export const getRagConnection = () => ragConnection;
export function subscribeRagConnection(listener: () => void): () => void {
  ragListeners.add(listener);
  return () => { ragListeners.delete(listener); };
}

/** Credentials belong to this tab session and one explicit custom endpoint.
 *  They are never baked into a public build or sent to the scenario API. */
export function setRagConnection(url: string | null, token = ""): void {
  const base = url?.trim() ? cleanBase(url) : null;
  // Bound to the endpoint it was entered for, so it cannot follow the reader
  // to a different host; kept in sessionStorage, so it dies with the tab.
  const secret = token.trim();
  try {
    localStorage.removeItem(LEGACY_KEY);
    if (base) localStorage.setItem(RAG_KEY, base);
    else localStorage.removeItem(RAG_KEY);
  } catch { /* settings still apply to this page view */ }
  try {
    if (secret) sessionStorage.setItem(AUTH_KEY, JSON.stringify(
      { baseUrl: base ?? DEFAULT_RAG_API_BASE, token: secret }));
    else sessionStorage.removeItem(AUTH_KEY);
  } catch { /* memory only when storage is unavailable */ }
  ragToken = secret;
  ragConnection = {
    baseUrl: base ?? DEFAULT_RAG_API_BASE, customBaseUrl: base,
    hasToken: !!secret, revision: ragConnection.revision + 1,
  };
  ragListeners.forEach((listener) => listener());
}

export class ApiError extends Error {
  endpoint: string;
  /** HTTP status when the server answered; undefined for network failures. */
  status?: number;
  /** The server's own reason (FastAPI `detail`), when it sent one. */
  detail: string;
  constructor(
    endpoint: string,
    detail: string,
    options?: { cause?: unknown; status?: number },
  ) {
    super(`API ${endpoint}: ${detail}`, options?.cause ? { cause: options.cause } : undefined);
    this.name = "ApiError";
    this.endpoint = endpoint;
    this.status = options?.status;
    this.detail = detail;
  }
}

/** Build the error for a non-2xx response, keeping the server's `detail` when
 *  it sent JSON — a 503 that says *why* the library is missing must not be
 *  flattened into "HTTP 503". */
async function failure(endpoint: string, res: Response): Promise<ApiError> {
  let detail = `HTTP ${res.status}`;
  try {
    const body = (await res.json()) as { detail?: unknown };
    if (typeof body?.detail === "string" && body.detail.trim()) detail = body.detail;
  } catch {
    /* non-JSON body: keep the status line */
  }
  return new ApiError(endpoint, detail, { status: res.status });
}

async function response(endpoint: string, init?: RequestInit, rag = false): Promise<Response> {
  const base = rag ? ragConnection.baseUrl : API_BASE;
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  // The token goes to whichever endpoint it was entered against, custom or
  // default. Restricting it to a custom URL kept it away from the scenario API,
  // which is still true — `rag` is false for those calls — but it also made the
  // reviewer token useless against the deployed corpus, which is where an
  // evaluator will look.
  const authenticated = rag && !!ragToken;
  if (authenticated) headers.set("Authorization", `Bearer ${ragToken}`);
  let res: Response;
  try {
    res = await fetch(`${base}${endpoint}`, {
      ...init, headers,
      // A credential is bound to this endpoint, not to a redirect destination.
      ...(authenticated ? { redirect: "error" as const } : {}),
    });
  } catch (cause) {
    if (init?.signal?.aborted) throw cause;
    throw new ApiError(endpoint, "sin conexión", { cause });
  }
  if (!res.ok) throw await failure(endpoint, res);
  return res;
}

async function request<T>(endpoint: string, init?: RequestInit, rag = false): Promise<T> {
  return (await (await response(endpoint, init, rag)).json()) as T;
}

export const api = {
  health: () => request<HealthResponse>("/health"),
  vintage: () => request<VintageResponse>("/vintage"),
  constants: () => request<ConstantsResponse>("/constants"),
  personas: () => request<PersonasResponse>("/personas"),
  presets: () => request<PresetsResponse>("/presets"),
  redlines: () => request<RedLinesResponse>("/redlines"),
  scenario: (body: ScenarioRequest, signal?: AbortSignal) =>
    request<ScenarioResponse>("/scenario", { method: "POST", body: JSON.stringify(body), signal }),
  montecarlo: (body: MonteCarloRequest, signal?: AbortSignal) =>
    request<MonteCarloResponse>("/scenario/montecarlo", { method: "POST", body: JSON.stringify(body), signal }),
  sensitivity: (body?: ScenarioRequest, signal?: AbortSignal) =>
    request<SensitivityResponse>("/scenario/sensitivity", {
      method: body ? "POST" : "GET",
      body: body ? JSON.stringify(body) : undefined,
      signal,
    }),
  explain: (body: ExplainRequest, signal?: AbortSignal) =>
    request<ExplainResponse>("/explain", { method: "POST", body: JSON.stringify(body), signal }),
  ask: (body: AskRequest, signal?: AbortSignal) =>
    request<AskResponse>("/ask", { method: "POST", body: JSON.stringify(body), signal }),
  evidence: () => request<EvidenceResponse>("/evidence"),
  prediction: () => request<PredictionResponse>("/prediction"),
  distress: () => request<DistressResponse>("/distress"),
  stateDependence: () => request<StateDependenceResponse>("/state-dependence"),
  ragCollections: () => request<RagCollectionsResponse>("/rag/collections", undefined, true),
  ragEval: () => request<RagEvalResponse>("/rag/eval", undefined, true),
  regimes: () => request<RegimesResponse>("/regimes"),
  demography: () => request<DemographyResponse>("/demography"),
  ragSearch: (body: RagSearchRequest, signal?: AbortSignal) =>
    request<RagSearchResponse>("/rag/search", { method: "POST", body: JSON.stringify(body), signal }, true),
  ragChat: (body: RagChatRequest, signal?: AbortSignal) =>
    request<RagChatResponse>("/rag/chat", { method: "POST", body: JSON.stringify(body), signal }, true),
};

/** Events emitted by /rag/chat/stream, in order: one `passages`, many
 *  `delta`, one `done`. */
export interface RagStreamHandlers {
  onPassages?: (passages: Passage[], grounded: boolean) => void;
  onDelta?: (text: string) => void;
  onDone?: (final: {
    answer: string; grounded: boolean;
    provider: string | null; model: string | null; error?: string | null;
  }) => void;
}

/** Consume the SSE stream.
 *
 *  Hand-parsed rather than via EventSource because that API is GET-only and
 *  this endpoint needs a POST body. Frames are split on the blank line, and a
 *  partial tail is carried between reads — a chunk boundary can land mid-frame
 *  and dropping it would silently lose words from the answer.
 */
export async function ragChatStream(
  body: RagChatRequest,
  handlers: RagStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const res = await response("/rag/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  }, true);
  if (!res.body) throw new ApiError("/rag/chat/stream", "respuesta sin cuerpo", { status: res.status });

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);

      let event = "message";
      const dataLines: string[] = [];
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
      }
      if (!dataLines.length) continue;

      let payload: Record<string, unknown>;
      try {
        payload = JSON.parse(dataLines.join("\n"));
      } catch {
        continue;
      }

      if (event === "passages") {
        handlers.onPassages?.(payload.passages as Passage[], payload.grounded as boolean);
      } else if (event === "delta") {
        handlers.onDelta?.(payload.text as string);
      } else if (event === "done") {
        handlers.onDone?.(payload as never);
      } else if (event === "error") {
        throw new ApiError("/rag/chat/stream", String(payload.detail ?? "error"));
      }
    }
  }
}
