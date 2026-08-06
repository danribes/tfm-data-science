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
    """One of the 39-42 KPIs; a few (e.g. Monte Carlo fans, per-CCAA maxima)
    carry a dict-valued `valor` instead of a scalar — kpis_perfiles.json."""
    valor: Any
    unidad: str
    fuente: str
    periodo: str


class SeriesOut(BaseModel):
    puntos: list[list[Any]]
    fuente: str


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
    years: list[int]
    series: dict[str, list[float]]
    personas: dict[str, PersonaDependentsOut]
    redlines: list[RedLineStatusOut]


class MonteCarloRequest(BaseModel):
    levers: LeverValues = Field(default_factory=LeverValues)
    seed: int = Field(42, ge=0)
    n_paths: int = Field(4000, ge=100, le=4000)  # spec §6: capped at 4,000
    horizon: int = Field(2070, ge=2030, le=2070)  # spec §6: capped at 2070


class MonteCarloResponse(ApiMeta):
    years: list[int]
    percentiles: dict[str, list[float]]
    n_paths: int
    seed: int


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
    iso3: str
    horizon_years: int
    debt_path: list[DebtPointOut]
    fiscal_space: list[FiscalSpaceOut]
