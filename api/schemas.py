"""Pydantic response/request models — the FROZEN phase-2 contract (spec §5).
Do not change field names or shapes without a spec revision."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from engine.constants import BASE_LEVERS, VINTAGE


class ApiMeta(BaseModel):
    vintage: str = VINTAGE
    computed_not_advice: bool = True  # no-recommendation rule (phase 2 render gate)


class HealthResponse(ApiMeta):
    status: str
    engine_version: str


class VintageFileOut(BaseModel):
    name: str
    url: str
    fetched_at: str
    bytes: int


class VintageResponse(ApiMeta):
    n_files: int
    files: list[VintageFileOut]


class ConstantOut(BaseModel):
    name: str
    value: float
    unit: str
    provenance: str


class ConstantsResponse(ApiMeta):
    constants: list[ConstantOut]


class KpiOut(BaseModel):
    # `valor` is numeric for 39 of the 42 KPIs; deuda_mc_2030, deuda_mc_2050 and
    # cuota_hipoteca_max carry a structured dict valor (verified against the
    # gold kpis_perfiles.json while drafting) — hence Any, not float.
    valor: Optional[Any] = None
    unidad: Optional[str] = None
    fuente: Optional[str] = None
    periodo: Optional[str] = None


class SeriesOut(BaseModel):
    puntos: list[list]           # [[period, value], ...] — period is str or number
    fuente: Optional[str] = None


class PersonaOutItem(BaseModel):
    k: str
    lab: str


class PersonaRedOut(BaseModel):
    t: str
    thr: Optional[float] = None
    k: Optional[str] = None
    cmp: Optional[str] = None
    d: Optional[int] = None
    x: str


class PersonaCard(BaseModel):
    id: str
    pill: str
    foot: str
    h1: str
    meta: str
    hot: list[str]
    series_keys: list[str]
    outs: list[PersonaOutItem]
    headline: str
    reds: list[PersonaRedOut]


class PersonasResponse(ApiMeta):
    kpis: dict[str, KpiOut]
    series: dict[str, SeriesOut]
    personas: list[PersonaCard]


class PresetOut(BaseModel):
    id: str
    nm: str
    set: dict[str, float]


class PresetsResponse(ApiMeta):
    presets: list[PresetOut]


class RedLineOut(BaseModel):
    id: str
    label: str
    series: str
    threshold: float
    cmp: str
    source: str


class RedLinesResponse(ApiMeta):
    redlines: list[RedLineOut]


class LeverValues(BaseModel):
    """The 10 levers, bounds per spec §4.1 ranges; out-of-range -> 422."""
    r: float = Field(default_factory=lambda: BASE_LEVERS["r"], ge=0.0, le=6.0)
    prima: float = Field(default_factory=lambda: float(BASE_LEVERS["prima"]), ge=0.0, le=400.0)
    sp: float = Field(0.0, ge=-4.0, le=4.0)
    lam: float = Field(0.9, ge=-0.5, le=2.5)
    pm: float = Field(0.0, ge=-50.0, le=100.0)
    tau: float = Field(0.0, ge=-5.0, le=5.0)
    z: float = Field(0.0, ge=-2.0, le=2.0)
    ext: float = Field(1.8, ge=-4.0, le=6.0)
    dem: float = Field(0.0, ge=-1.0, le=1.0)
    idx: float = Field(0.0, ge=-1.5, le=1.0)


class ScenarioRequest(BaseModel):
    levers: LeverValues = Field(default_factory=LeverValues)
    horizon: int = Field(2050, ge=2026, le=2050)


class RedLineStatusOut(BaseModel):
    id: str
    label: str
    series: str
    value: float
    threshold: float
    cmp: str
    status: str
    source: str


class PersonaDependentsOut(BaseModel):
    pill: str
    headline: str
    series: dict[str, list[float]]


class ScenarioResponse(ApiMeta):
    horizon: int
    years: list[int]
    baseline: dict[str, list[float]]
    scenario: dict[str, list[float]]
    deltas: dict[str, list[float]]
    personas: dict[str, PersonaDependentsOut]
    redlines: list[RedLineStatusOut]


class MonteCarloRequest(BaseModel):
    levers: LeverValues = Field(default_factory=LeverValues)
    seed: int = Field(42, ge=0)
    n_paths: int = Field(4000, ge=100, le=4000)  # spec §6: capped at 4,000
    horizon: int = Field(2070, ge=2030, le=2070)  # spec §6: capped at 2070
    #: Individual trajectories to return for the spaghetti plot.
    n_show: int = Field(60, ge=0, le=200)


class MonteCarloResponse(ApiMeta):
    years: list[int]
    percentiles: dict[str, list[float]]
    n_paths: int
    seed: int
    #: Individual trajectories for the spaghetti plot (see McResult.paths).
    paths: list[list[float]] = Field(default_factory=list)


class CountryOut(BaseModel):
    iso3: str
    iso2: str
    name: str
    region: str


class CountriesResponse(ApiMeta):
    countries: list[CountryOut]
    error: Optional[str] = None


class IndicatorOut(BaseModel):
    available: bool
    source: Optional[str] = None
    from_cache: bool = False
    error: Optional[str] = None
    values: dict[int, float]


class PanelResponse(ApiMeta):
    iso3: str
    coverage_score: float
    indicators: dict[str, IndicatorOut]


class GenericScenarioRequest(BaseModel):
    horizon_years: int = Field(10, ge=1, le=50)
    tax_wedge_delta_pp: float = 0.0
    primary_balance_target_pct: float = 0.0
    indexation_delta_pp: float = 0.0
    output_gap_path_pct: Optional[list[float]] = None
    contingent_shocks_pct: Optional[list[float]] = None
    allocation_shares: Optional[dict[str, float]] = None


class DebtPointOut(BaseModel):
    year: int
    debt_gdp_pct: float
    interest_rate_pct: float
    growth_rate_pct: float
    primary_balance_pct: float
    contingent_shock_pct: float


class FiscalSpaceOut(BaseModel):
    total_revenue_pct_gdp: float
    total_spending_pct_gdp: float
    primary_balance_pct_gdp: float
    allocations_pct_gdp: dict[str, float]


class GenericScenarioResponse(ApiMeta):
    country_iso3: str
    coverage_score: float
    defaults_used: list[str]
    baseline_years: dict[str, int]
    debt_path: list[DebtPointOut]
    unemployment_path_pct: list[float]
    inflation_path_pct: list[float]
    nominal_wage_growth_path_pct: list[float]
    fiscal_space_by_year: list[FiscalSpaceOut]


# ---- /evidence (fase 3): la calibración frente a los datos ----

class EstimateOut(BaseModel):
    name: str
    coef: float
    se: float
    n: int
    n_units: int
    ci_low: float
    ci_high: float
    significant: bool


class SubperiodOut(EstimateOut):
    label: str


class ComparisonOut(EstimateOut):
    constant: str
    label: str
    calibrated: float
    source: str
    #: True cuando el valor calibrado cae dentro de la banda estimada. False no
    #: es un fallo: es un hallazgo, y se muestra como tal.
    compatible: bool
    verdict: str
    #: El mismo estimador sobre ventanas más cortas. La media de toda la muestra
    #: mezcla el pinchazo y la recuperación; publicando las mitades el lector ve
    #: que la cifra depende de la ventana, en vez de tener que preguntarlo.
    subperiods: list[SubperiodOut] = []


class IrfPointOut(EstimateOut):
    h: int
    years: float


class EnginePathPointOut(BaseModel):
    h: int
    years: float
    #: None antes del ancla: la regla del motor es anual y extrapolarla a
    #: horizontes intranuales inventaría una afirmación que la constante no hace.
    coef: float | None = None


class IrfOut(BaseModel):
    horizons: list[IrfPointOut]
    engine_path: list[EnginePathPointOut]
    anchor_h: int
    unit: str
    note: str


class EvidenceResponse(ApiMeta):
    comparisons: list[ComparisonOut]
    #: Respuesta dinámica a un choque regional, frente a lo que supone el motor.
    irf: IrfOut | None = None
    fiscal_persistence: EstimateOut | None = None
    #: Qué constantes NO puede juzgar el vintage y por qué. Se publica junto a
    #: los resultados: omitirlo daría una impresión de cobertura que no existe.
    identifiable: dict[str, str]
    engine_version: str


# ---- /rag (fase 3): biblioteca con citas ----

class RagSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    collection: str = Field("libros")
    top_k: int = Field(8, ge=1, le=25)


class PassageOut(BaseModel):
    chunk_id: int
    text: str
    title: str
    collection: str
    #: "academico" | "propio" | "opinion" — se muestra al lector; un manual y un
    #: canal de YouTube no se citan con la misma autoridad.
    authority: str
    page: int | None = None
    section: str | None = None
    score: float
    cita: str


class RagSearchResponse(ApiMeta):
    query: str
    collection: str
    passages: list[PassageOut]


class RagChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    collection: str = Field("libros")
    top_k: int = Field(8, ge=1, le=25)
    #: Cuando es true, el escenario activo viaja con la pregunta y la respuesta
    #: puede enlazar la teoría con los números en pantalla.
    include_scenario: bool = False
    levers: LeverValues | None = None
    horizon: int = Field(2050, ge=2026, le=2050)


class RagChatResponse(ApiMeta):
    question: str
    collection: str
    answer: str
    passages: list[PassageOut]
    grounded: bool
    provider: str | None = None
    model: str | None = None
    error: str | None = None


class RagCollectionOut(BaseModel):
    id: str
    label: str
    authority: str
    note: str
    documents: int
    chunks: int


class RagCollectionsResponse(ApiMeta):
    collections: list[RagCollectionOut]
    total_documents: int
    total_chunks: int


# ---- /explain (spec §10): engine-computed facts, LLM-narrated prose ----

class ExplainRequest(BaseModel):
    levers: LeverValues = Field(default_factory=LeverValues)
    horizon: int = Field(2026, ge=2026, le=2050)
    headline: str = Field("b", description="Serie que encabeza la explicación")
    #: False forces the deterministic path — used by the offline mock build and
    #: the smoke test, which must never depend on a network call.
    narrate: bool = True


class ContributionOut(BaseModel):
    lever_id: str
    lever_name: str
    delta: float
    share: float


class ExplainResponse(ApiMeta):
    resumen: str
    mecanismo: str
    advertencia: str
    #: "llm" when Claude wrote it, "deterministic" when the templates did. The
    #: UI shows this: a reader is entitled to know which produced the text.
    source: str
    model: str | None = None
    #: Populated only when source == "deterministic" and a narration was tried.
    fallback_reason: str | None = None
    contributions: list[ContributionOut]
    interaction: float
    joint_delta: float
    headline_key: str
    headline_year: int


class SensitivityTargetOut(BaseModel):
    key: str
    label: str
    unit: str


class SensitivityItemOut(BaseModel):
    lever_id: str
    lever_name: str
    unit: str
    #: dY/dL en las unidades propias de cada palanca. NO comparable entre filas.
    sensitivities: dict[str, dict[str, float]]
    lever_span: float
    #: dY/dL x el recorrido completo de la palanca: la misma pregunta para todas
    #: («¿qué pasa si la muevo de tope a tope?»), y por tanto la única columna
    #: que se puede ordenar.
    span_effects: dict[str, dict[str, float]]


class SensitivityResponse(ApiMeta):
    horizons: list[int]
    target_series: list[SensitivityTargetOut]
    matrix: dict[str, SensitivityItemOut]



# ---- Predicción: el backtest T1 y su veredicto pre-registrado ----

class BacktestVerdictOut(BaseModel):
    candidate: str
    beaten_ccaa: int
    total_ccaa: int
    required: int
    horizon: int
    mase_candidate: float
    mase_drift: float
    mase_candidate_long: float
    mase_drift_long: float
    #: False es el resultado real, y la página lo enseña como tal.
    wins: bool
    verdict: str


class BacktestRowOut(BaseModel):
    h: int
    mase: dict[str, float]


class PredictionResponse(ApiMeta):
    #: Artefacto congelado: entrenar la red cuesta minutos, así que la
    #: evaluación se calcula fuera de línea y se versiona con el repo.
    available: bool
    protocol: dict[str, object] = {}
    rows: list[BacktestRowOut] = []
    verdict: BacktestVerdictOut | None = None
    methods: list[str] = []
    note: str = ""


# ---- Distress: el complemento probabilístico del umbral del 7 % ----

class DistressFeatureOut(BaseModel):
    feature: str
    label: str
    mean: float
    std: float


class DistressCountryOut(BaseModel):
    iso3: str
    year: int
    probability: float
    base_rate: float
    #: False cuando el país no está en la base de impagos — el caso de España.
    in_label_set: bool
    coverage: str


class DistressResponse(ApiMeta):
    available: bool
    n: int = 0
    n_positive: int = 0
    base_rate: float = 0.0
    n_countries: int = 0
    auc: float = 0.0
    auc_std: float = 0.0
    pr_auc: float = 0.0
    pr_auc_lift: float = 0.0
    #: False es un resultado publicable: el modelo no distingue mejor que el azar.
    beats_chance: bool = False
    years: list[int] = []
    importances: list[DistressFeatureOut] = []
    spain: DistressCountryOut | None = None
    note: str = ""


# ---- Dependencia del estado: ¿E_R constante o no? ----

class RegimeSlopeOut(BaseModel):
    label: str
    n: int
    slope: float
    se: float


class EmpiricalImportanceOut(BaseModel):
    feature: str
    label: str
    mean_abs_shap: float


class StateDependenceResponse(ApiMeta):
    available: bool
    n: int = 0
    n_countries: int = 0
    years: list[int] = []
    horizon_years: int = 3
    #: ~0 y publicado como tal: sin poder predictivo fuera de país, las
    #: pendientes describen la superficie ajustada, no una regla validada.
    r2_grouped: float = 0.0
    r2_std: float = 0.0
    regimes: list[RegimeSlopeOut] = []
    engine_e_r: float = 0.0
    importance: list[EmpiricalImportanceOut] = []
    diff_ci: list[float] = []
    n_boot: int = 0
    #: False es el hallazgo del corte actual: la constancia del motor NO queda
    #: contradicha por este panel.
    state_dependent: bool = False
    spain_excluded_reason: str = ""
    note: str = ""


# ---- La biblioteca, evaluada: resumen de las dos capas ----

class RagEvalResponse(ApiMeta):
    available: bool
    #: Recuperación: ¿sale el documento correcto, y a qué altura de la lista?
    n_questions: int = 0
    hit_rate: float = 0.0
    mrr: float = 0.0
    top1: float = 0.0
    isolation_clean: bool = False
    guardrail_clean: bool = False
    #: Chat: ¿rechaza lo incontestable, cita lo que afirma, y las citas apuntan
    #: a pasajes reales?
    unanswerable_refused: int = 0
    unanswerable_total: int = 0
    answered: int = 0
    cited_share: float = 0.0
    dangling_answers: int = 0
    fidelity_supported: int = 0
    fidelity_checked: int = 0
    note: str = ""
