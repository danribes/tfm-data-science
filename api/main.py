"""FastAPI service — all endpoints (spec §5). Shapes live in api/schemas.py."""
from __future__ import annotations

import csv
from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (ConstantsResponse, ConstantOut, CountriesResponse,
                          CountryOut, DebtPointOut, FiscalSpaceOut,
                          GenericScenarioRequest, GenericScenarioResponse,
                          HealthResponse, IndicatorOut, MonteCarloRequest,
                          MonteCarloResponse, PanelResponse, PersonaCard,
                          PersonaDependentsOut, PersonasResponse,
                          PresetOut, PresetsResponse, RedLineOut, RedLinesResponse,
                          RedLineStatusOut, ScenarioRequest, ScenarioResponse,
                          VintageFileOut, VintageResponse)
from data.live import country_list, panel_builder
from engine import generic
from engine.constants import (CONSTANTS_TABLE, ENGINE_VERSION, GOLD_DIR, VINTAGE,
                               load_kpis)
from engine.levers import PRESETS, Levers
from engine.montecarlo import run_montecarlo
from engine.redlines import RED_LINES, evaluate_redlines
from engine.spain import PERSONAS, Y0, Y1, baseline, persona_dependents, run_scenario

app = FastAPI(title="evo core API", version=ENGINE_VERSION)

# spec §5 conventions: CORS allows localhost + the file:// "null" origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["null"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", engine_version=ENGINE_VERSION)


@app.get("/vintage", response_model=VintageResponse)
def vintage() -> VintageResponse:
    with (GOLD_DIR / "provenance_vintage_manifest.csv").open(encoding="utf-8") as fh:
        files = [VintageFileOut(name=row["name"], url=row["url"],
                                 fetched_at=row["fetched_at"], bytes=int(row["bytes"]))
                 for row in csv.DictReader(fh)]
    return VintageResponse(n_files=len(files), files=files)


@app.get("/constants", response_model=ConstantsResponse)
def constants() -> ConstantsResponse:
    return ConstantsResponse(constants=[ConstantOut(**e) for e in CONSTANTS_TABLE])


@app.get("/personas", response_model=PersonasResponse)
def personas() -> PersonasResponse:
    kp = load_kpis()
    return PersonasResponse(kpis=kp["kpi"], series=kp["series"],
                             personas=[PersonaCard(**p) for p in PERSONAS])


@app.get("/presets", response_model=PresetsResponse)
def presets() -> PresetsResponse:
    return PresetsResponse(presets=[PresetOut(**p) for p in PRESETS])


@app.get("/redlines", response_model=RedLinesResponse)
def redlines() -> RedLinesResponse:
    return RedLinesResponse(redlines=[RedLineOut(**r) for r in RED_LINES])


@app.post("/scenario", response_model=ScenarioResponse)
def scenario(req: ScenarioRequest) -> ScenarioResponse:
    levers = Levers(**req.levers.model_dump())
    run = run_scenario(levers)
    base = baseline()
    deltas = {k: [s - b for s, b in zip(run[k], base[k])] for k in run}
    k = req.horizon - Y0
    return ScenarioResponse(
        horizon=req.horizon,
        years=list(range(Y0, Y1 + 1)),
        baseline=base,
        scenario=run,
        deltas=deltas,
        personas={pid: PersonaDependentsOut(**dep)
                  for pid, dep in persona_dependents(run).items()},
        redlines=[RedLineStatusOut(**st) for st in evaluate_redlines(run, k)],
    )


@app.post("/scenario/montecarlo", response_model=MonteCarloResponse)
def scenario_montecarlo(req: MonteCarloRequest) -> MonteCarloResponse:
    levers = Levers(**req.levers.model_dump())
    mc = run_montecarlo(levers, n_paths=req.n_paths, seed=req.seed)
    n = req.horizon - 2026 + 1
    return MonteCarloResponse(
        years=mc.years[:n],
        percentiles={p: v[:n] for p, v in mc.percentiles.items()},
        n_paths=mc.n_paths,
        seed=mc.seed,
    )


@app.get("/countries", response_model=CountriesResponse)
def countries() -> CountriesResponse:
    try:
        entries = country_list.load_country_list()   # never raises; cache-first
        return CountriesResponse(countries=[CountryOut(**e) for e in entries])
    except Exception as exc:                          # belt and braces: no 500s
        return CountriesResponse(countries=[], error=str(exc))


@app.get("/panel/{iso3}", response_model=PanelResponse)
def panel(iso3: str) -> PanelResponse:
    iso3 = iso3.upper()
    p = panel_builder.build_country_panel(iso3)
    indicators = {
        key: IndicatorOut(available=res.available, source=res.source,
                          from_cache=res.from_cache, error=res.error,
                          values=res.values)
        for key, res in p.items()
    }
    return PanelResponse(iso3=iso3, coverage_score=panel_builder.coverage_score(p),
                         indicators=indicators)


@app.post("/scenario/generic/{iso3}", response_model=GenericScenarioResponse)
def scenario_generic(iso3: str, req: GenericScenarioRequest) -> GenericScenarioResponse:
    iso3 = iso3.upper()
    p = panel_builder.build_country_panel(iso3)
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    levers = generic.ScenarioLevers(**kwargs)
    try:
        result = generic.run_scenario(iso3, p, levers)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return GenericScenarioResponse(
        country_iso3=result.country_iso3,
        coverage_score=result.coverage_score,
        defaults_used=result.defaults_used,
        baseline_years=result.baseline_years,
        debt_path=[DebtPointOut(**asdict(pt)) for pt in result.debt_path],
        unemployment_path_pct=result.unemployment_path_pct,
        inflation_path_pct=result.inflation_path_pct,
        nominal_wage_growth_path_pct=result.nominal_wage_growth_path_pct,
        fiscal_space_by_year=[FiscalSpaceOut(**asdict(fs)) for fs in result.fiscal_space_by_year],
    )
