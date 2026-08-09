"""FastAPI service — all endpoints (spec §5). Shapes live in api/schemas.py."""
from __future__ import annotations

import csv
from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (ConstantsResponse, ConstantOut, ContributionOut,
                          CountriesResponse, CountryOut, DebtPointOut,
                          ExplainRequest, ExplainResponse, FiscalSpaceOut,
                          LeverValues,
                          GenericScenarioRequest, GenericScenarioResponse,
                          HealthResponse, IndicatorOut, MonteCarloRequest,
                          MonteCarloResponse, PanelResponse, PersonaCard,
                          PersonaDependentsOut, PersonasResponse,
                          PassageOut, PresetOut, PresetsResponse,
                          RagChatRequest, RagChatResponse, RagCollectionOut,
                          RagCollectionsResponse, RagSearchRequest,
                          RagSearchResponse, RedLineOut, RedLinesResponse,
                          RedLineStatusOut, ScenarioRequest, ScenarioResponse,
                          VintageFileOut, VintageResponse)
from explain.facts import build_facts
from explain.fallback import fallback_narration
from explain.narrate import NarrationUnavailable, narrate
from data.live import country_list, panel_builder
from engine import generic
from engine.constants import (CONSTANTS_TABLE, ENGINE_VERSION, GOLD_DIR, VINTAGE,
                               load_kpis)
from engine.levers import PRESETS, Levers
from engine.montecarlo import run_montecarlo
from engine.redlines import RED_LINES, evaluate_redlines
from engine.spain import (PERSONAS, SERIES_KEYS, Y0, Y1, baseline,
                           persona_dependents, run_scenario)

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
    mc = run_montecarlo(levers, n_paths=req.n_paths, seed=req.seed, n_show=req.n_show)
    n = req.horizon - 2026 + 1
    return MonteCarloResponse(
        years=mc.years[:n],
        percentiles={p: v[:n] for p, v in mc.percentiles.items()},
        n_paths=mc.n_paths,
        seed=mc.seed,
        paths=[p[:n] for p in mc.paths],
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


@app.get("/rag/collections", response_model=RagCollectionsResponse)
def rag_collections() -> RagCollectionsResponse:
    """What the library holds. Empty counts mean the corpus is not ingested yet."""
    from rag import config as rag_config, store as rag_store

    try:
        con = rag_store.connect()
        try:
            st = rag_store.stats(con)
        finally:
            con.close()
    except Exception:
        st = {"documents": 0, "chunks": 0, "by_collection": {}}

    out = []
    for cid, meta in rag_config.COLLECTIONS.items():
        counts = st["by_collection"].get(cid, {})
        out.append(RagCollectionOut(
            id=cid, label=meta["label"], authority=meta["authority"],
            note=meta["note"], documents=counts.get("documents", 0),
            chunks=counts.get("chunks", 0),
        ))
    return RagCollectionsResponse(collections=out,
                                  total_documents=st["documents"],
                                  total_chunks=st["chunks"])


@app.post("/rag/search", response_model=RagSearchResponse)
def rag_search(req: RagSearchRequest) -> RagSearchResponse:
    """Hybrid retrieval, no generation — the passages on their own."""
    from rag import config as rag_config, retrieve as rag_retrieve

    if req.collection not in rag_config.COLLECTIONS:
        raise HTTPException(status_code=422,
                            detail=f"colección desconocida: {req.collection}")
    try:
        hits = rag_retrieve.search(req.query, req.collection, req.top_k)
    except Exception as exc:
        raise HTTPException(status_code=503,
                            detail=f"corpus no disponible: {exc}") from exc
    return RagSearchResponse(
        query=req.query, collection=req.collection,
        passages=[PassageOut(**h.to_dict()) for h in hits],
    )


@app.post("/rag/chat", response_model=RagChatResponse)
def rag_chat(req: RagChatRequest) -> RagChatResponse:
    """Answer from the corpus, with citations. Never answers ungrounded."""
    from rag import chat as rag_chat_mod, config as rag_config

    if req.collection not in rag_config.COLLECTIONS:
        raise HTTPException(status_code=422,
                            detail=f"colección desconocida: {req.collection}")

    facts = None
    if req.include_scenario:
        levers = Levers(**(req.levers or LeverValues()).model_dump())
        f = build_facts(levers, req.horizon)
        # Only the summary the model needs — the full facts blob would crowd
        # the retrieved passages out of the context window.
        facts = {
            "vintage": f.vintage,
            "palancas_movidas": [
                {"palanca": m.name, "de": m.base, "a": m.value, "unidad": m.unit}
                for m in f.moved],
            "resultados": [
                {"serie": o.label, "año": o.year, "valor": o.value,
                 "delta_vs_base": o.delta, "unidad": o.unit}
                for o in f.outcomes],
            "lineas_rojas_cruzadas": [
                r.label for r in f.redlines if r.status == "crossed"],
        }

    try:
        ans = rag_chat_mod.ask(req.question, req.collection, top_k=req.top_k,
                               scenario_facts=facts)
    except Exception as exc:
        raise HTTPException(status_code=503,
                            detail=f"corpus no disponible: {exc}") from exc

    return RagChatResponse(
        question=req.question, collection=req.collection, answer=ans.text,
        passages=[PassageOut(**p) for p in ans.passages],
        grounded=ans.grounded, provider=ans.provider, model=ans.model,
        error=ans.error,
    )


@app.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest) -> ExplainResponse:
    """Narrate a scenario. Facts come from the engine; only prose comes from the LLM.

    The narration never blocks the response: if Claude is unreachable, the
    deterministic templates answer instead and `source` says so.
    """
    levers = Levers(**req.levers.model_dump())
    if req.headline not in SERIES_KEYS:
        raise HTTPException(status_code=422,
                            detail=f"unknown series: {req.headline!r}")
    facts = build_facts(levers, req.horizon, headline=req.headline)

    source, model, reason = "deterministic", None, None
    blocks = fallback_narration(facts)
    if req.narrate:
        try:
            result = narrate(facts)
            blocks = {"resumen": result.resumen, "mecanismo": result.mecanismo,
                      "advertencia": result.advertencia}
            source, model = "llm", result.model
        except NarrationUnavailable as exc:
            reason = str(exc)

    return ExplainResponse(
        **blocks,
        source=source,
        model=model,
        fallback_reason=reason,
        contributions=[ContributionOut(**asdict(ct)) for ct in facts.contributions],
        interaction=facts.interaction,
        joint_delta=facts.joint_delta,
        headline_key=facts.headline_key,
        headline_year=facts.headline_year,
    )
