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


# ---------- modelo (servido desde los artefactos gold del protocolo) ----------

@lru_cache(maxsize=1)
def rendimiento() -> pd.DataFrame:
    return pd.read_csv(GOLD_DIR / "gold_rendimiento_pais.csv")


@lru_cache(maxsize=1)
def forecast_gold() -> pd.DataFrame:
    return pd.read_csv(GOLD_DIR / "gold_forecast_ccaa.csv")


@lru_cache(maxsize=1)
def escenarios_gold() -> pd.DataFrame:
    return pd.read_csv(GOLD_DIR / "gold_escenarios_deuda.csv")


class ScenarioPath(BaseModel):
    r_mercado: float = Field(3.5, ge=0.0, le=10.0, description="Tipo de mercado, %")
    g_real: float = Field(1.3, ge=-2.0, le=5.0, description="Crecimiento real, %")
    pb_palanca_pp: float = Field(0.0, ge=-5.0, le=5.0,
                                 description="Ajuste permanente del saldo primario, pp de PIB")
    con_demografia: bool = Field(True, description="Aplicar la presión demográfica del motor")
    hasta: int = Field(2050, ge=2030, le=2050)


@app.get("/performance/{module}")
def performance(module: str, solo_destacados: bool = False):
    """Funnel de rendimiento ajustado (A1). Residuales LOOCV con semiancho
    conformal 90 % por cuartil de renta — NUNCA una liga (docs/rendimiento_a1.md)."""
    if module != "health":
        raise HTTPException(404, "Módulo disponible: health (housing/education: futuras iteraciones)")
    df = rendimiento()
    if solo_destacados:
        df = df[df["destacado"]]
    return {"module": module, "modelo": df["modelo"].iloc[0],
            "nota": "residual out-of-fold con intervalo por grupo de renta; no es un ranking",
            "paises": df.to_dict("records")}


@app.get("/forecast/ccaa/{territorio}")
def forecast_ccaa(territorio: str, h: int = Query(8, ge=1, le=8),
                  escenario: str = Query("central_salarios_2pct")):
    """Pronóstico de producción T1: drift + abanico empírico 80/95 % y
    escenarios salariales (docs/forecast_t1_mvp.md; gold_forecast_ccaa.csv)."""
    df = forecast_gold()
    if escenario not in set(df["escenario"]):
        raise HTTPException(404, f"Escenarios: {sorted(df['escenario'].unique().tolist())}")
    sub = df[(df["ccaa"].str.lower() == territorio.lower())
             & (df["escenario"] == escenario) & (df["h"] <= h)]
    if sub.empty:
        raise HTTPException(404, f"Territorio '{territorio}' no encontrado "
                                 f"(disponibles: {sorted(df['ccaa'].unique().tolist())})")
    return {"territorio": sub["ccaa"].iloc[0], "modelo": "drift",
            "advertencia": "la banda es la parte informativa; punto ciego declarado en giros de ciclo",
            "puntos": sub.sort_values("h").drop(columns=["ccaa"]).to_dict("records")}


@app.get("/scenarios/debt")
def scenarios_debt():
    """Menú D1 pre-calculado (docs/escenarios_d1.md): 6 sendas de deuda 2024–2050."""
    df = escenarios_gold()
    return {"nota": "elegir es política, no estadística; aritmética determinista sin retroalimentaciones",
            "escenarios": [{"escenario": k, "puntos": g.drop(columns=["escenario"]).to_dict("records")}
                           for k, g in df.groupby("escenario")]}


@app.post("/scenario")
def scenario(path: ScenarioPath):
    """Simulador D1 interactivo: aritmética r−g con las palancas del usuario y la
    presión demográfica del motor de proyección (España)."""
    import math
    base = {"debt0": 105.2, "r0": 2.4 / 105.2 * 100, "pb0": -0.9, "deflactor": 2.0, "venc": 8}
    demog = {}
    if path.con_demografia:
        pars, pj = proj_params(), projections()
        s65 = (pj.query("geo=='ES' and variant=='BSL'").set_index("year")["share65"]
               .reindex(range(2024, path.hasta + 1)).interpolate())
        for mod, key in [("pensions", "pensions_oldage"), ("health", "te_gf07")]:
            b = pars[mod]["base"]["ES"]
            beta = pars[mod]["beta"][pars[mod]["drivers"].index("l_pop65_share")]
            spend = b[key] * (s65 / b["pop65_share"]) ** beta
            for y, v in (spend - spend.iloc[0]).items():
                demog[y] = demog.get(y, 0.0) + float(v)
    d, r = base["debt0"], base["r0"]
    g = path.g_real + base["deflactor"]
    out = []
    for y in range(2024, path.hasta + 1):
        r = r + (path.r_mercado - r) / base["venc"]
        pb = base["pb0"] - demog.get(y, 0.0) + path.pb_palanca_pp
        d = d * (1 + r / 100) / (1 + g / 100) - pb
        out.append({"year": y, "deuda": round(d, 1), "pb": round(pb, 2), "r_efectivo": round(r, 2)})
    return {"palancas": path.model_dump(), "geo": "ES",
            "nota": "mapa de sensibilidades, no pronóstico (docs/escenarios_d1.md §3.4)",
            "senda": out}


@lru_cache(maxsize=1)
def projections() -> pd.DataFrame:
    return pd.read_csv(GOLD_DIR / "gold_projections.csv")


@lru_cache(maxsize=1)
def proj_params() -> dict:
    import json
    f = MODELS_DIR / "projection_params.json"
    if not f.exists():
        raise model_missing("projection_params.json")
    return json.loads(f.read_text())


@app.get("/project/{module}")
def project(
    module: str,
    geo: str = Query("ES"),
    variant: str = Query("BSL", description="BSL|LFRT|LMRT|HMIGR|LMIGR|NMIGR|all"),
    to_year: int = Query(2060, ge=2030, le=2070),
    gdp_growth: float = Query(0.012, ge=-0.02, le=0.05, description="crecimiento anual real PIB pc"),
    unemployment_delta: float = Query(0.0, ge=-10, le=10, description="Δpp de paro vs base (sensibilidad)"),
):
    """Proyección 2023→2070 del gasto en pensiones/sanidad (%PIB), anclada en
    EUROPOP2023 (todas las variantes demográficas y migratorias) y en las
    elasticidades entrenadas sobre el panel UE con TODOS los drivers del modelo:
    share65 (proyectado), PIB pc (palanca de escenario), paro (sensibilidad),
    obesidad (mantenida). Banda = ±1,64σ del ajuste histórico (90%). NO es una
    predicción causal: es proyección condicionada a la senda declarada."""
    if module not in ("pensions", "health"):
        raise HTTPException(404, "Módulos proyectables: pensions, health")
    pars = proj_params()[module]
    geo = geo.upper()
    base = pars["base"].get(geo)
    if not base:
        raise HTTPException(404, f"Sin valores base para {geo}. Disponibles: {sorted(pars['base'])}")
    pj = projections()
    variants = ["BSL", "LFRT", "LMRT", "HMIGR", "LMIGR", "NMIGR"] if variant == "all" else [variant.upper()]
    b = dict(zip(pars["drivers"], pars["beta"]))
    y0, s0 = base["year"], base[pars["y"]]
    sh0 = base["pop65_share"]
    se_c = dict(zip(pars["drivers"], pars.get("se_cluster", pars["se"])))
    out = {"module": module, "geo": geo, "base_year": y0, "base_value_pct_gdp": round(s0, 2),
           "elasticities": {k: round(v, 3) for k, v in b.items()},
           "elasticities_se_cluster": {k: round(v, 3) for k, v in se_c.items()},
           "assumptions": {"gdp_growth": gdp_growth, "unemployment_delta": unemployment_delta,
                           "obesity": "constante", "nota": "proyección condicionada, no causal"},
           "nota_banda": "banda = ±1,64σ del residuo within histórico; NO incluye la "
                         "incertidumbre de las elasticidades (SE agrupados por país ≈ 2× "
                         "los clásicos) ni la autocorrelación del panel: orientativa",
           "paths": []}
    import math
    for var in variants:
        sub = pj.query("geo==@geo and variant==@var and year>=@y0 and year<=@to_year").sort_values("year")
        if sub.empty:
            continue
        sh_base_proj = float(sub.iloc[0]["share65"])
        pts = []
        for _, r in sub.iterrows():
            t = int(r["year"]) - y0
            ratio65 = (float(r["share65"]) / sh_base_proj)
            log_mult = b.get("l_pop65_share", 0) * math.log(max(ratio65, 1e-9))
            log_mult += b.get("l_gdp_pc_pps", 0) * math.log((1 + gdp_growth) ** t)
            log_mult += b.get("unemployment", 0) * unemployment_delta
            val = s0 * math.exp(log_mult)
            band = 1.64 * pars["sigma"]
            pts.append({"year": int(r["year"]), "value": round(val, 2),
                        "lo": round(val * math.exp(-band), 2), "hi": round(val * math.exp(band), 2),
                        "share65": round(float(r["share65"]), 1),
                        "net_migration": float(r["net_migration"]) if pd.notna(r["net_migration"]) else None})
        out["paths"].append({"variant": var, "points": pts})
    if not out["paths"]:
        raise HTTPException(404, f"Variante '{variant}' sin datos para {geo}")
    return out


@app.get("/shap/{module}")
def shap_curves(module: str):
    """Curvas de umbral SHAP (op. 3). Se sirven pre-computadas desde el notebook."""
    f = MODELS_DIR / f"shap_{module}.json"
    if not f.exists():
        raise model_missing(f"shap_{module}.json")
    import json
    return json.loads(f.read_text())
