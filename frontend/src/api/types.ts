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

export interface MonteCarloRequest { levers?: Partial<Levers>; seed?: number; n_paths?: number; horizon?: number }
export type PercentileKey = "p5" | "p25" | "p50" | "p75" | "p95";
export interface MonteCarloResponse extends ApiMeta {
  years: number[];
  percentiles: Record<PercentileKey, number[]>;
  n_paths: number;
  seed: number;
}
