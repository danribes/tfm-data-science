import type { Levers } from "../engine/levers";
import type { RedLineDef } from "../engine/redlines";

export interface ApiMeta { vintage: string; computed_not_advice: boolean }

export interface HealthResponse extends ApiMeta { status: string; engine_version: string }

export interface VintageFileOut { name: string; url: string; fetched_at: string; bytes: number }
export interface VintageResponse extends ApiMeta { n_files: number; files: VintageFileOut[] }

export interface ConstantOut { name: string; value: number; unit: string; provenance: string }
export interface ConstantsResponse extends ApiMeta { constants: ConstantOut[] }

export interface KpiOut { valor?: unknown; unidad?: string; fuente?: string; periodo?: string }
export interface SeriesOut { puntos: [string | number, number][]; fuente?: string }

export interface PersonaOutItem { k: string; lab: string }
export interface PersonaRedOut {
  t: string;
  thr: number | null;
  k: string | null;
  cmp: string | null;
  d: number | null;
  x: string;
}
export interface PersonaCard {
  id: string;
  pill: string;
  foot: string;
  h1: string;
  meta: string;
  hot: string[];
  series_keys: string[];
  outs: PersonaOutItem[];
  headline: string;
  reds: PersonaRedOut[];
}
export interface PersonasResponse extends ApiMeta {
  kpis: Record<string, KpiOut>;
  series: Record<string, SeriesOut>;
  personas: PersonaCard[];
}

export interface PresetOut { id: string; nm: string; set: Record<string, number> }
export interface PresetsResponse extends ApiMeta { presets: PresetOut[] }

export interface RedLinesResponse extends ApiMeta { redlines: RedLineDef[] }

export interface ScenarioRequest { levers?: Partial<Levers>; horizon?: number }

export interface RedLineStatusOut extends RedLineDef { value: number; status: string }
export interface PersonaDependentsOut { pill: string; headline: string; series: Record<string, number[]> }
export interface ScenarioResponse extends ApiMeta {
  horizon: number;
  years: number[];
  baseline: Record<string, number[]>;
  scenario: Record<string, number[]>;
  deltas: Record<string, number[]>;
  personas: Record<string, PersonaDependentsOut>;
  redlines: RedLineStatusOut[];
}

export interface ExplainRequest {
  levers?: Partial<Levers>;
  horizon?: number;
  headline?: string;
  /** false forces the deterministic path (offline build, smoke test). */
  narrate?: boolean;
}
export interface ContributionOut { lever_id: string; lever_name: string; delta: number; share: number }
export interface ExplainResponse extends ApiMeta {
  resumen: string;
  mecanismo: string;
  advertencia: string;
  /** "llm" or "deterministic" — shown to the reader, never hidden. */
  source: string;
  model: string | null;
  fallback_reason: string | null;
  contributions: ContributionOut[];
  interaction: number;
  joint_delta: number;
  headline_key: string;
  headline_year: number;
}

// ---- Evidencia: la calibración frente a los datos ----

export interface EstimateOut {
  name: string;
  coef: number;
  se: number;
  n: number;
  n_units: number;
  ci_low: number;
  ci_high: number;
  significant: boolean;
}
export interface SubperiodOut extends EstimateOut { label: string }
export interface ComparisonOut extends EstimateOut {
  constant: string;
  label: string;
  calibrated: number;
  source: string;
  /** false no es un fallo: es un hallazgo, y se muestra como tal. */
  compatible: boolean;
  verdict: string;
  /** El mismo estimador sobre ventanas más cortas, para enseñar que la cifra
   *  depende de la muestra. Vacío cuando partir no aporta. */
  subperiods: SubperiodOut[];
}
export interface EvidenceResponse extends ApiMeta {
  comparisons: ComparisonOut[];
  fiscal_persistence: EstimateOut | null;
  identifiable: Record<string, string>;
  engine_version: string;
}

// ---- RAG: la biblioteca con citas ----

export type Authority = "academico" | "propio" | "opinion";

export interface RagCollection {
  id: string;
  label: string;
  /** Se muestra al lector: un manual y un canal de YouTube no se citan igual. */
  authority: Authority;
  note: string;
  documents: number;
  chunks: number;
}
export interface RagCollectionsResponse extends ApiMeta {
  collections: RagCollection[];
  total_documents: number;
  total_chunks: number;
}

export interface Passage {
  chunk_id: number;
  text: string;
  title: string;
  collection: string;
  authority: Authority;
  page: number | null;
  section: string | null;
  score: number;
  cita: string;
}

export interface RagSearchRequest { query: string; collection?: string; top_k?: number }
export interface RagSearchResponse extends ApiMeta {
  query: string;
  collection: string;
  passages: Passage[];
}

export interface RagChatRequest {
  question: string;
  collection?: string;
  top_k?: number;
  /** Manda el escenario activo con la pregunta: teoría citada + números en pantalla. */
  include_scenario?: boolean;
  levers?: Partial<Levers>;
  horizon?: number;
}
export interface RagChatResponse extends ApiMeta {
  question: string;
  collection: string;
  answer: string;
  passages: Passage[];
  /** false cuando no se recuperó nada: el chat lo dice en vez de inventar. */
  grounded: boolean;
  provider: string | null;
  model: string | null;
  error: string | null;
}

export interface MonteCarloRequest {
  levers?: Partial<Levers>;
  seed?: number;
  n_paths?: number;
  horizon?: number;
  /** Individual trajectories to return for the spaghetti plot. */
  n_show?: number;
}
export type PercentileKey = "p5" | "p25" | "p50" | "p75" | "p95";
export interface MonteCarloResponse extends ApiMeta {
  years: number[];
  percentiles: Record<PercentileKey, number[]>;
  n_paths: number;
  seed: number;
  /** Individual paths — the spaghetti. Deterministic given the seed. */
  paths: number[][];
}
