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

/** Where this build points by default: the public API, or localhost in dev. */
const BUILD_API_BASE: string = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

const API_OVERRIDE_KEY = "evo.apiBase";

/** `?api=reset` clears the override before anything renders.
 *
 *  The in-app button cannot be the only way out. The health check gates the
 *  whole app, so once an override stops answering, every escape that depends on
 *  the app rendering is already gone — the reader is left on a retry screen
 *  with no way back. A URL they can type always works. */
function consumeResetParam(): boolean {
  try {
    const params = new URLSearchParams(location.search);
    if (params.get("api") !== "reset") return false;
    localStorage.removeItem(API_OVERRIDE_KEY);
    params.delete("api");
    const qs = params.toString();
    history.replaceState(null, "", location.pathname + (qs ? `?${qs}` : "") + location.hash);
    return true;
  } catch {
    return false;
  }
}

function readOverride(): string | null {
  if (consumeResetParam()) return null;
  try {
    const v = localStorage.getItem(API_OVERRIDE_KEY);
    return v && v.trim() ? v.trim().replace(/\/+$/, "") : null;
  } catch {
    return null; // private mode / blocked storage
  }
}

/** Live binding: importers see reassignments made by `setApiBase`.
 *
 *  The copyrighted corpus never ships to the public deploy, so the only way to
 *  query it from the published frontend is to point this at a tunnel to the
 *  machine that holds the index. The URL of a cloudflared quick tunnel is new
 *  on every run, which is why this is runtime state and not a build-time env. */
export let API_BASE: string = readOverride() ?? BUILD_API_BASE;

/** Repoint every API call. `null` restores the build-time default. */
export function setApiBase(url: string | null): void {
  const clean = url?.trim().replace(/\/+$/, "") || null;
  try {
    if (clean) localStorage.setItem(API_OVERRIDE_KEY, clean);
    else localStorage.removeItem(API_OVERRIDE_KEY);
  } catch {
    /* storage unavailable — the override still applies for this page view */
  }
  API_BASE = clean ?? BUILD_API_BASE;
}

/** The build-time target, for telling the reader what "restore" would mean. */
export const DEFAULT_API_BASE = BUILD_API_BASE;

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

async function request<T>(endpoint: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${endpoint}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch (cause) {
    throw new ApiError(endpoint, "sin conexión", { cause });
  }
  if (!res.ok) throw await failure(endpoint, res);
  return (await res.json()) as T;
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
  ragCollections: () => request<RagCollectionsResponse>("/rag/collections"),
  ragEval: () => request<RagEvalResponse>("/rag/eval"),
  regimes: () => request<RegimesResponse>("/regimes"),
  demography: () => request<DemographyResponse>("/demography"),
  ragSearch: (body: RagSearchRequest, signal?: AbortSignal) =>
    request<RagSearchResponse>("/rag/search", { method: "POST", body: JSON.stringify(body), signal }),
  ragChat: (body: RagChatRequest, signal?: AbortSignal) =>
    request<RagChatResponse>("/rag/chat", { method: "POST", body: JSON.stringify(body), signal }),
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
  const res = await fetch(`${API_BASE}/rag/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) throw await failure("/rag/chat/stream", res);
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
