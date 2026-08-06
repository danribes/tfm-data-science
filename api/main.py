"""FastAPI app: static GET endpoints (spec §5). Response models live in
api/schemas.py."""
from __future__ import annotations

import csv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (ConstantsResponse, ConstantOut, HealthResponse,
                          PersonaCard, PersonasResponse, PresetOut, PresetsResponse,
                          RedLineOut, RedLinesResponse, VintageFileOut, VintageResponse)
from engine.constants import (CONSTANTS_TABLE, ENGINE_VERSION, GOLD_DIR, VINTAGE,
                               load_kpis)
from engine.levers import PRESETS
from engine.redlines import RED_LINES
from engine.spain import PERSONAS

app = FastAPI(title="evo API", version=ENGINE_VERSION)

# spec §5 CORS: local dev servers + the "null" origin (file:// dev pages)
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
