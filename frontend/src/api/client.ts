import type {
  ConstantsResponse, ExplainRequest, ExplainResponse, HealthResponse,
  MonteCarloRequest, MonteCarloResponse,
  PersonasResponse, PresetsResponse,
  RagChatRequest, RagChatResponse, RagCollectionsResponse,
  RagSearchRequest, RagSearchResponse,
  RedLinesResponse, ScenarioRequest,
  ScenarioResponse, VintageResponse,
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
  explain: (body: ExplainRequest, signal?: AbortSignal) =>
    request<ExplainResponse>("/explain", { method: "POST", body: JSON.stringify(body), signal }),
  ragCollections: () => request<RagCollectionsResponse>("/rag/collections"),
  ragSearch: (body: RagSearchRequest, signal?: AbortSignal) =>
    request<RagSearchResponse>("/rag/search", { method: "POST", body: JSON.stringify(body), signal }),
  ragChat: (body: RagChatRequest, signal?: AbortSignal) =>
    request<RagChatResponse>("/rag/chat", { method: "POST", body: JSON.stringify(body), signal }),
};
