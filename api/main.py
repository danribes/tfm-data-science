"""API del proyecto "Dinero público → Resultados" (esqueleto F-app).

Sirve la capa GOLD ya extraída (atlas + siglo) y deja huecos claros (501)
para los artefactos de modelo que producirán los notebooks:
  api/models/gbm_{module}.txt          — LightGBM (op. 2)
  api/models/conformal_{module}.json   — cuantiles por grupo de renta (op. 2)
  api/models/forecast_ccaa.pkl         — forecaster trimestral (op. 6)

Arranque local:  uvicorn main:app --reload   (desde api/, con GOLD_DIR=../storage/gold)
Docker:          docker compose up --build   (raíz del repo)
"""
from __future__ import annotations

import os
import pathlib
from functools import lru_cache

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

GOLD_DIR = pathlib.Path(os.environ.get("GOLD_DIR", "../storage/gold")).resolve()
MODELS_DIR = pathlib.Path(__file__).parent / "models"

app = FastAPI(
    title="Dinero público → Resultados",
    version="0.1.0",
    description="Atlas fiscal (1900–2023), rendimiento ajustado y simulador de escenarios. "
                "Endpoints de modelo devuelven 501 hasta que los notebooks entrenen los artefactos.",
)


# ---------- carga de datos (una vez) ----------

@lru_cache(maxsize=1)
def panel() -> pd.DataFrame:
    return pd.read_csv(GOLD_DIR / "gold_panel_anual.csv")


@lru_cache(maxsize=1)
def century() -> pd.DataFrame:
    return pd.read_csv(GOLD_DIR / "gold_century_fiscal.csv")


@lru_cache(maxsize=1)
def ccaa() -> pd.DataFrame:
    return pd.read_csv(GOLD_DIR / "gold_ccaa_trimestral.csv")


def model_missing(artifact: str) -> HTTPException:
    return HTTPException(
        status_code=501,
        detail=f"Artefacto '{artifact}' no entrenado todavía. Entrénalo en los notebooks "
               f"(ops. 2/6 del plan) y colócalo en api/models/. Slots actuales: "
               f"{[p.name for p in MODELS_DIR.glob('*') if p.name != '.gitkeep'] or 'vacíos'}",
    )


# ---------- meta ----------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "gold_dir": str(GOLD_DIR),
        "datasets": {
            "panel": len(panel()),
            "century": len(century()),
            "ccaa": len(ccaa()),
        },
        "model_slots": [p.name for p in MODELS_DIR.glob("*") if p.name != ".gitkeep"] or "vacíos",
    }


@app.get("/countries")
def countries():
    df = panel()
    return sorted(df["geo"].unique().tolist())


@app.get("/variables")
def variables():
    df = panel()
    return sorted(df["variable"].unique().tolist())


# ---------- atlas (RQ B1–B15: datos reales, disponibles YA) ----------

@app.get("/atlas/{variable}")
def atlas(variable: str, geo: str | None = Query(None, description="p.ej. ES; omitir = todos")):
    df = panel()
    sub = df[df["variable"] == variable]
    if sub.empty:
        raise HTTPException(404, f"Variable '{variable}' no existe. Ver /variables")
    if geo:
        sub = sub[sub["geo"] == geo.upper()]
        if sub.empty:
            raise HTTPException(404, f"Sin datos de '{variable}' para geo={geo}")
    return {
        "variable": variable,
        "series": [
            {"geo": g, "points": grp.sort_values("year")[["year", "value"]].to_dict("records")}
            for g, grp in sub.groupby("geo")
        ],
    }


@app.get("/century/{variable}")
def century_series(variable: str, iso3: str | None = Query(None, description="p.ej. ESP")):
    df = century()
    sub = df[df["variable"] == variable]
    if sub.empty:
        raise HTTPException(404, f"Variable '{variable}' no existe en el panel del siglo "
                                 f"(disponibles: {sorted(df['variable'].unique().tolist())})")
    if iso3:
        sub = sub[sub["iso3"] == iso3.upper()]
    return {
        "variable": variable,
        "series": [
            {"iso3": c, "points": grp.sort_values("year")[["year", "value"]].to_dict("records")}
            for c, grp in sub.groupby("iso3")
        ],
    }


@app.get("/ccaa/affordability")
def ccaa_affordability(territorio: str | None = None):
    df = ccaa()
    if territorio:
        df = df[df["ccaa"].str.lower() == territorio.lower()]
        if df.empty:
            raise HTTPException(404, f"Territorio '{territorio}' no encontrado")
    cols = ["ccaa", "anyo", "quarter", "ipv", "ipc", "salario_anual", "ratio_asequibilidad", "salario_flag"]
    return df[cols].to_dict("records")


# ---------- modelo (huecos 501 hasta entrenar) ----------

class ScenarioPath(BaseModel):
    geo: str = Field(..., description="País ISO2, p.ej. ES")
    horizon: int = Field(5, ge=1, le=10, description="Años a proyectar")
    delta_housing_pp: float = Field(0.0, description="Cambio en gasto vivienda, pp de PIB")
    delta_capital_share: float = Field(0.0, description="Cambio en la cuota de capital, pp")
    primary_balance_pct: float = Field(0.0, description="Saldo primario supuesto, % PIB")


@app.get("/performance/{module}")
def performance(module: str):
    """Funnel de rendimiento ajustado (op. 2). Requiere gbm_{module} + conformal_{module}."""
    if module not in ("health", "housing", "education"):
        raise HTTPException(404, "Módulos: health, housing, education")
    if not (MODELS_DIR / f"gbm_{module}.txt").exists():
        raise model_missing(f"gbm_{module}.txt")
    raise model_missing(f"conformal_{module}.json")  # placeholder hasta implementar inferencia


@app.get("/forecast/ccaa/{territorio}")
def forecast_ccaa(territorio: str, h: int = Query(8, ge=1, le=12)):
    """Predicción trimestral de asequibilidad (op. 6). Requiere forecast_ccaa.pkl."""
    if not (MODELS_DIR / "forecast_ccaa.pkl").exists():
        raise model_missing("forecast_ccaa.pkl")
    raise model_missing("forecast_ccaa.pkl")


@app.post("/scenario")
def scenario(path: ScenarioPath):
    """Simulador D1 (op. 7): senda de gasto → outcomes proyectados + trayectoria de deuda.
    Requiere el modelo de rendimiento entrenado; la aritmética de deuda (r−g) se añade aquí."""
    if not (MODELS_DIR / "gbm_health.txt").exists():
        raise model_missing("gbm_health.txt")
    raise model_missing("scenario engine")


@app.get("/shap/{module}")
def shap_curves(module: str):
    """Curvas de umbral SHAP (op. 3). Se sirven pre-computadas desde el notebook."""
    f = MODELS_DIR / f"shap_{module}.json"
    if not f.exists():
        raise model_missing(f"shap_{module}.json")
    import json
    return json.loads(f.read_text())
