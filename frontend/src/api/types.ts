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

export interface SensitivityTargetOut { key: string; label: string; unit: string }
export interface SensitivityItemOut {
  lever_id: string;
  lever_name: string;
  unit: string;
  /** dY/dL en unidades de cada palanca. No comparable entre filas. */
  sensitivities: Record<string, Record<string, number>>;
  lever_span: number;
  /** Efecto de mover la palanca de tope a tope: comparable entre filas. */
  span_effects: Record<string, Record<string, number>>;
}
export interface SensitivityResponse extends ApiMeta {
  horizons: number[];
  target_series: SensitivityTargetOut[];
  matrix: Record<string, SensitivityItemOut>;
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
export interface IrfPointOut extends EstimateOut { h: number; years: number }
export interface EnginePathPointOut {
  h: number;
  years: number;
  /** null antes del ancla: la regla del motor es anual. */
  coef: number | null;
}
export interface IrfOut {
  horizons: IrfPointOut[];
  engine_path: EnginePathPointOut[];
  anchor_h: number;
  unit: string;
  note: string;
}

export interface EvidenceResponse extends ApiMeta {
  comparisons: ComparisonOut[];
  irf: IrfOut | null;
  fiscal_persistence: EstimateOut | null;
  identifiable: Record<string, string>;
  engine_version: string;
}

// ---- Predicción: el backtest T1 ----

export interface BacktestVerdictOut {
  candidate: string;
  beaten_ccaa: number;
  total_ccaa: number;
  required: number;
  horizon: number;
  mase_candidate: number;
  mase_drift: number;
  mase_candidate_long: number;
  mase_drift_long: number;
  /** false es el resultado real y se enseña como tal. */
  wins: boolean;
  verdict: string;
}
export interface BacktestRowOut { h: number; mase: Record<string, number> }
export interface PredictionResponse extends ApiMeta {
  available: boolean;
  protocol: Record<string, string | number>;
  rows: BacktestRowOut[];
  verdict: BacktestVerdictOut | null;
  methods: string[];
  note: string;
}

export interface DistressFeatureOut { feature: string; label: string; mean: number; std: number }
export interface DistressCountryOut {
  iso3: string; year: number; probability: number; base_rate: number;
  /** false cuando el país no está en la base de impagos — el caso de España. */
  in_label_set: boolean; coverage: string;
}
export interface DistressResponse extends ApiMeta {
  available: boolean;
  n: number; n_positive: number; base_rate: number; n_countries: number;
  auc: number; auc_std: number; pr_auc: number; pr_auc_lift: number;
  beats_chance: boolean;
  years: number[];
  importances: DistressFeatureOut[];
  spain: DistressCountryOut | null;
  note: string;
}

export interface RegimeSlopeOut { label: string; n: number; slope: number; se: number }
export interface EmpiricalImportanceOut { feature: string; label: string; mean_abs_shap: number }
export interface StateDependenceResponse extends ApiMeta {
  available: boolean;
  n: number; n_countries: number; years: number[]; horizon_years: number;
  /** ~0 y publicado: las pendientes describen la superficie ajustada. */
  r2_grouped: number; r2_std: number;
  regimes: RegimeSlopeOut[];
  engine_e_r: number;
  importance: EmpiricalImportanceOut[];
  diff_ci: number[];
  n_boot: number;
  /** false es el hallazgo: la constante del motor no queda contradicha. */
  state_dependent: boolean;
  spain_excluded_reason: string;
  note: string;
}

export interface RagEvalResponse extends ApiMeta {
  available: boolean;
  n_questions: number; hit_rate: number; mrr: number; top1: number;
  isolation_clean: boolean; guardrail_clean: boolean;
  unanswerable_refused: number; unanswerable_total: number;
  answered: number; cited_share: number; dangling_answers: number;
  fidelity_supported: number; fidelity_checked: number;
  note: string;
}

export interface RegimeEpisodeOut { from: number | string; to: number | string }
export interface RegimeSeriesOut {
  periods: (number | string)[];
  values: number[];
  p_crisis: number[];
  episodes: RegimeEpisodeOut[];
  mu: number[];
  var: number[];
  unit: string;
}
export interface RegimesResponse extends ApiMeta {
  available: boolean;
  fiscal: RegimeSeriesOut | null;
  housing: RegimeSeriesOut | null;
  method: string;
  note: string;
}

export interface DemographyVariantOut {
  id: string;
  label: string;
  olddep_start: number;
  olddep_end: number;
  /** El valor de dem que reproduce esta variante. Azúcar sobre la palanca. */
  dem_equivalent: number;
}
export interface DemographyResponse extends ApiMeta {
  year_start: number;
  year_end: number;
  baseline_variant: string;
  variants: DemographyVariantOut[];
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

// ---- Análogos históricos ----

export interface AnalogOutcomePoint {
  year_offset: number;
  debt_gdp: number | null;
  gdp_growth: number | null;
  overall_balance_gdp: number | null;
  r_minus_g: number | null;
  truncated: boolean;
}

export interface StructuralDiff {
  dimension: string;
  label: string;
  spain_value: string;
  analog_value: string;
  direction: "converge" | "diverge" | "neutral";
}

export interface AnalogMatch {
  rank: number;
  iso3: string;
  country_name: string;
  match_year: number;
  distance: number;
  dominant_lever: string | null;
  match_snapshot: Record<string, number>;
  outcome: AnalogOutcomePoint[];
  outcome_truncated: boolean;
  diffs: StructuralDiff[];
  debt_payable_verdict: "auto" | "requires_surplus" | "borderline";
  narrative: string | null;
}

export interface AnalogResponse extends ApiMeta {
  horizon: number;
  query_snapshot: Record<string, number>;
  matches: AnalogMatch[];
  rag_available: boolean;
}

export type AnalogRequest = ScenarioRequest;
