import type {
  ConstantsResponse, EvidenceResponse, ExplainRequest, ExplainResponse, HealthResponse,
  MonteCarloRequest, MonteCarloResponse,
  Passage,
  PersonasResponse, PredictionResponse, PresetsResponse,
  RagChatRequest, RagChatResponse, RagCollectionsResponse,
  RagSearchRequest, RagSearchResponse,
  RedLinesResponse, ScenarioRequest,
  ScenarioResponse, SensitivityResponse, VintageResponse,
} from "./types";

export const API_BASE: string = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export class ApiError extends Error {
  endpoint: string;
  constructor(endpoint: string, detail: string, options?: { cause?: unknown }) {
    super(`API ${endpoint}: ${detail}`, options);
    this.name = "ApiError";
    this.endpoint = endpoint;
  }
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
  if (!res.ok) throw new ApiError(endpoint, `HTTP ${res.status}`);
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
  evidence: () => request<EvidenceResponse>("/evidence"),
  prediction: () => request<PredictionResponse>("/prediction"),
  ragCollections: () => request<RagCollectionsResponse>("/rag/collections"),
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
  if (!res.ok || !res.body) throw new ApiError("/rag/chat/stream", `HTTP ${res.status}`);

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
