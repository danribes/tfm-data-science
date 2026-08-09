"""FastAPI service — all endpoints (spec §5). Shapes live in api/schemas.py."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse

from api.schemas import (ComparisonOut, ConstantsResponse, ConstantOut,
                          ContributionOut,
                          CountriesResponse, CountryOut, DebtPointOut,
                          EstimateOut, EvidenceResponse, IrfOut,
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
                          SensitivityResponse,
                          BacktestRowOut, BacktestVerdictOut, PredictionResponse,
                          DistressFeatureOut, DistressCountryOut, DistressResponse,
                          EmpiricalImportanceOut, RegimeSlopeOut, StateDependenceResponse,
                          VintageFileOut, VintageResponse)
from explain.facts import build_facts
from explain.fallback import fallback_narration
from explain.narrate import NarrationUnavailable, narrate
from explain.report import generate_policy_brief_html
from data.live import country_list, panel_builder
from engine import generic
from research import backtest as research_backtest
from engine.constants import (CONSTANTS_TABLE, ENGINE_VERSION, GOLD_DIR, VINTAGE,
                               load_kpis)
from engine.levers import PRESETS, Levers, validate_levers
from engine.montecarlo import run_montecarlo
from engine.redlines import RED_LINES, evaluate_redlines
from engine.spain import (PERSONAS, SERIES_KEYS, Y0, Y1, baseline,
                           persona_dependents, run_scenario, sensitivity_matrix)

app = FastAPI(title="evo core API", version=ENGINE_VERSION)


@app.get("/")
def root():
    """Redirect root access to interactive API documentation."""
    return RedirectResponse(url="/docs")


@app.on_event("startup")
def _warm_embedder() -> None:
    """Load the embedding model in the background at startup.

    It is lazy-loaded otherwise, so the first RAG request of a session paid
    ~23 s to bring e5-large onto the GPU — measured 28 s cold versus 5 s warm
    for the identical query. That penalty always landed on whoever asked the
    first question, which in a demo is the audience.

    Runs on a daemon thread so the API starts serving immediately, and failures
    are swallowed: a machine with no model cache should still serve the engine
    endpoints, just with a slow first RAG call.
    """
    import threading

    def _load() -> None:
        try:
            from rag import embed
            embed.get_model()
        except Exception:
            pass

    threading.Thread(target=_load, daemon=True, name="rag-warmup").start()

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


@app.get("/scenario/sensitivity", response_model=SensitivityResponse)
def scenario_sensitivity_base() -> SensitivityResponse:
    raw = sensitivity_matrix()
    return SensitivityResponse(**raw)


@app.post("/scenario/sensitivity", response_model=SensitivityResponse)
def scenario_sensitivity_custom(req: ScenarioRequest) -> SensitivityResponse:
    levers = Levers(**req.levers.model_dump())
    errors = validate_levers(levers)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})
    raw = sensitivity_matrix(base_levers=levers)
    return SensitivityResponse(**raw)


@app.get("/scenario/report", response_class=HTMLResponse)
def scenario_report_base(horizon: int = 2050) -> HTMLResponse:
    """Generate 1-Page Policy Brief HTML report for the baseline scenario (S0)."""
    html_content = generate_policy_brief_html(Levers(), horizon=horizon)
    return HTMLResponse(content=html_content)


@app.post("/scenario/report", response_class=HTMLResponse)
def scenario_report_custom(req: ScenarioRequest) -> HTMLResponse:
    """Generate 1-Page Policy Brief HTML report for a custom scenario."""
    levers = Levers(**req.levers.model_dump())
    errors = validate_levers(levers)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})
    html_content = generate_policy_brief_html(levers, horizon=req.horizon)
    return HTMLResponse(content=html_content)


#: The T1 evaluation is a committed artifact, not a live computation: training
#: the transfer network takes minutes, and a route that retrained on every page
#: load would be slower than it is informative. Regenerated deliberately with
#: `python -m research.dl_global`, which is also what makes the number quotable.
_T1_REPORT = GOLD_DIR.parents[1] / "docs" / "eval" / "t1-dl-global.json"


@app.get("/prediction", response_model=PredictionResponse)
def prediction() -> PredictionResponse:
    """The pre-registered house-price backtest, and whether the model won."""
    if not _T1_REPORT.exists():
        # A missing artifact is reported, not faked. The page says the
        # evaluation has not been run rather than showing an empty table that
        # reads like a model with no error.
        return PredictionResponse(
            available=False,
            note=("La evaluación T1 no se ha ejecutado en esta copia. "
                  "Genérala con `python -m research.dl_global`."))

    raw = json.loads(_T1_REPORT.read_text(encoding="utf-8"))
    rows = [BacktestRowOut(h=int(h), mase=m)
            for h, m in sorted(raw["mase_by_h"].items(), key=lambda kv: int(kv[0]))]
    methods = sorted({m for r in rows for m in r.mase})
    return PredictionResponse(
        available=True,
        protocol={
            "origins": f"{research_backtest.ORIGINS[0]}–{research_backtest.ORIGINS[-1]}",
            "test_start": str(research_backtest.TEST_START),
            "horizons": research_backtest.H,
            "n_ccaa": raw["verdict"]["total_ccaa"],
            "train_series": raw["n_series"],
            "train_windows": raw["n_windows"],
            "train_cutoff": raw["cutoff"],
            "seed": raw["seed"],
        },
        rows=rows,
        verdict=BacktestVerdictOut(**raw["verdict"]),
        methods=methods,
    )


#: Same reasoning as the T1 report: fitting the classifier and running grouped
#: cross-validation takes ~30 s, so the evaluation is a committed artifact
#: regenerated with `python -m research.distress`.
_DISTRESS_REPORT = GOLD_DIR.parents[1] / "docs" / "eval" / "distress.json"


@app.get("/distress", response_model=DistressResponse)
def distress() -> DistressResponse:
    """How much Spain resembles the countries that went on to default."""
    if not _DISTRESS_REPORT.exists():
        return DistressResponse(
            available=False,
            note=("El clasificador de distress no se ha entrenado en esta copia. "
                  "Genéralo con `python -m research.distress`."))

    raw = json.loads(_DISTRESS_REPORT.read_text(encoding="utf-8"))
    esp = raw.get("spain")
    return DistressResponse(
        available=True,
        n=raw["n"], n_positive=raw["n_positive"], base_rate=raw["base_rate"],
        n_countries=raw["n_countries"],
        auc=raw["auc"], auc_std=raw["auc_std"],
        pr_auc=raw["pr_auc"], pr_auc_lift=raw["pr_auc_lift"],
        beats_chance=raw["beats_chance"], years=raw["years"],
        importances=[DistressFeatureOut(**i) for i in raw["importances"]],
        spain=DistressCountryOut(**{k: v for k, v in esp.items()
                                    if k != "features"}) if esp else None,
    )


_STATE_DEP_REPORT = GOLD_DIR.parents[1] / "docs" / "eval" / "state_dependence.json"


@app.get("/state-dependence", response_model=StateDependenceResponse)
def state_dependence() -> StateDependenceResponse:
    """Whether a rate shock hits the same at 60 % debt as at 120 %."""
    if not _STATE_DEP_REPORT.exists():
        return StateDependenceResponse(
            available=False,
            note=("El contraste de dependencia del estado no se ha ejecutado. "
                  "Genéralo con `python -m research.state_dependence`."))
    raw = json.loads(_STATE_DEP_REPORT.read_text(encoding="utf-8"))
    return StateDependenceResponse(
        available=True,
        n=raw["n"], n_countries=raw["n_countries"], years=raw["years"],
        horizon_years=raw["horizon_years"],
        r2_grouped=raw["r2_grouped"], r2_std=raw["r2_std"],
        regimes=[RegimeSlopeOut(**r) for r in raw["regimes"]],
        engine_e_r=raw["engine_e_r"],
        importance=[EmpiricalImportanceOut(**i) for i in raw["importance"]],
        diff_ci=raw["diff_ci"], n_boot=raw["n_boot"],
        state_dependent=raw["state_dependent"],
        spain_excluded_reason=raw["spain_excluded_reason"],
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


@app.get("/evidence", response_model=EvidenceResponse)
def evidence() -> EvidenceResponse:
    """The engine's calibrated constants confronted with the frozen panels.

    Cheap enough to compute per request (a few thousand rows, closed-form OLS),
    so there is no cache to go stale against a new vintage.
    """
    from research import validate as research_validate

    try:
        out = research_validate.run_all()
    except Exception as exc:
        raise HTTPException(status_code=503,
                            detail=f"capa empírica no disponible: {exc}") from exc

    return EvidenceResponse(
        comparisons=[ComparisonOut(**row) for row in out["comparisons"]],
        irf=IrfOut(**out["irf"]) if out["irf"] else None,
        fiscal_persistence=(EstimateOut(**out["fiscal_persistence"])
                            if out["fiscal_persistence"] else None),
        identifiable=out["identifiable"],
        engine_version=out["engine_version"],
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


def _scenario_facts(req: RagChatRequest) -> dict:
    """The live scenario, trimmed to what the model needs.

    Only a summary: the full facts blob would crowd the retrieved passages out
    of the context window, and the passages are what the answer must rest on.
    """
    levers = Levers(**(req.levers or LeverValues()).model_dump())
    f = build_facts(levers, req.horizon)
    return {
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


@app.post("/rag/chat", response_model=RagChatResponse)
def rag_chat(req: RagChatRequest) -> RagChatResponse:
    """Answer from the corpus, with citations. Never answers ungrounded."""
    from rag import chat as rag_chat_mod, config as rag_config

    if req.collection not in rag_config.COLLECTIONS:
        raise HTTPException(status_code=422,
                            detail=f"colección desconocida: {req.collection}")

    facts = _scenario_facts(req) if req.include_scenario else None

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


@app.post("/rag/chat/stream")
def rag_chat_stream(req: RagChatRequest) -> StreamingResponse:
    """Same as /rag/chat but streamed: passages first, then the answer word by word.

    Time-to-first-content drops from ~5 s to under a second, because the reader
    does not wait for generation to finish before seeing anything.
    """
    from rag import chat as rag_chat_mod, config as rag_config

    if req.collection not in rag_config.COLLECTIONS:
        raise HTTPException(status_code=422,
                            detail=f"colección desconocida: {req.collection}")

    facts = _scenario_facts(req) if req.include_scenario else None

    # A *sync* generator handed to StreamingResponse is drained in a threadpool
    # and its frames arrive together at the end — measured: passages landed at
    # 4,6 s instead of 0,8 s, which silently defeated the whole feature. Running
    # the blocking producer on its own thread and awaiting a queue makes this a
    # true async generator, so each frame flushes as it is produced.
    async def events():
        import asyncio
        import queue
        import threading

        q: queue.Queue = queue.Queue()
        DONE = object()

        def produce() -> None:
            try:
                for item in rag_chat_mod.stream(
                        req.question, req.collection, top_k=req.top_k,
                        scenario_facts=facts):
                    q.put(item)
            except Exception as exc:
                q.put(("error", {"detail": f"{type(exc).__name__}: {exc}"}))
            finally:
                q.put(DONE)

        threading.Thread(target=produce, daemon=True, name="rag-stream").start()
        while True:
            item = await asyncio.to_thread(q.get)
            if item is DONE:
                return
            name, payload = item
            yield f"event: {name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        # Without this an intermediate proxy may buffer the whole stream and
        # hand it over at the end, which would silently undo the feature.
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
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
