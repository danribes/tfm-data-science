"""Historical analog search engine (spec §2).

Loaded once at import time. find_analogs() is the public API.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from engine.constants import GOLD_DIR, VINTAGE
from engine.levers import LEVER_SPECS, Levers
from engine.spain import Y0, run_scenario

# ── Query features (order matters — covariance matrix built in this order) ──
QUERY_FEATURES = [
    "debt_gdp", "primary_balance_gdp", "interest_rate_10y",
    "gdp_growth", "unemployment", "inflation", "r_minus_g",
]

# ── Series-key → panel-column mapping ───────────────────────────────────────
_SERIES_TO_PANEL: dict[str, str] = {
    "b":    "debt_gdp",
    "pb":   "primary_balance_gdp",
    "bono": "interest_rate_10y",
    "g":    "gdp_growth",
    "u":    "unemployment",
    "pi":   "inflation",
}

# ── Country display names (Spanish) ─────────────────────────────────────────
_NAMES: dict[str, str] = {
    "AUT": "Austria", "BEL": "Bélgica", "CHE": "Suiza",
    "CZE": "República Checa", "DEU": "Alemania", "DNK": "Dinamarca",
    "ESP": "España", "FIN": "Finlandia", "FRA": "Francia",
    "GBR": "Reino Unido", "GRC": "Grecia", "HUN": "Hungría",
    "IRL": "Irlanda", "ISL": "Islandia", "ISR": "Israel",
    "ITA": "Italia", "JPN": "Japón", "KOR": "Corea del Sur",
    "LUX": "Luxemburgo", "MEX": "México", "NLD": "Países Bajos",
    "NOR": "Noruega", "NZL": "Nueva Zelanda", "POL": "Polonia",
    "PRT": "Portugal", "SVK": "Eslovaquia", "SVN": "Eslovenia",
    "SWE": "Suecia", "TUR": "Turquía", "USA": "Estados Unidos",
    "ARG": "Argentina", "BRA": "Brasil", "COL": "Colombia", "PER": "Perú",
    "ZAF": "Sudáfrica", "THA": "Tailandia", "IDN": "Indonesia",
    "EGY": "Egipto", "MAR": "Marruecos", "NGA": "Nigeria",
    "AUS": "Australia", "CAN": "Canadá",
}

# ── Structural diff labels ───────────────────────────────────────────────────
_DIFF_LABELS: dict[str, str] = {
    "emu_member":         "Zona euro",
    "fx_regime":          "Régimen cambiario",
    "ext_debt_share":     "Deuda externa / deuda total",
    "democracy":          "Calidad institucional (Polity5)",
    "trade_openness":     "Apertura comercial (X+M/PIB)",
    "debt_maturity":      "Vencimiento deuda (proxy ext_debt_share)",
    "tfp_trend":          "Tendencia TFP (media 5 años)",
    "labor_productivity": "Productividad laboral (media 5 años)",
}

# Spain 2026 baseline structural values (used for direction computation)
_SPAIN_STRUCT: dict[str, Any] = {
    "emu_member":           1,
    "fx_regime":            "fixed",
    "ext_debt_share":       51.0,   # WB 2022
    "democracy":            9.0,    # Polity5 Spain
    "trade_openness":       72.0,   # (X+M)/GDP Spain 2022
    "tfp_growth_5y":        0.2,    # PWT Spain 2017–2021 avg
    "labor_prod_growth_5y": 0.8,
}

# ── Module-level panel load ──────────────────────────────────────────────────

def _load() -> tuple[pd.DataFrame, dict, np.ndarray | None, bool]:
    panel = pd.read_csv(GOLD_DIR / "gold_analog_panel.csv")
    # Filter out non-country aggregate codes (keep only 3-char iso3)
    panel = panel[panel["iso3"].str.len() == 3].reset_index(drop=True)
    stats: dict = json.loads(
        (GOLD_DIR / "gold_analog_panel_stats.json").read_text(encoding="utf-8")
    )
    # Covariance matrix from the 7 query features (rows with all 7 values present)
    feat_data = panel[QUERY_FEATURES].dropna()
    cov = np.cov(feat_data.values.T)
    cond = float(np.linalg.cond(cov))
    if cond > 1e12:
        return panel, stats, None, True  # use_euclidean=True
    cov_inv = np.linalg.inv(cov)
    return panel, stats, cov_inv, False


ANALOG_PANEL, _STATS, _COV_INV, _USE_EUCLIDEAN = _load()

# ── Public helpers ───────────────────────────────────────────────────────────

def debt_payable_verdict(r_minus_g: float) -> str:
    """Classify debt sustainability from the Blanchard condition."""
    if r_minus_g < -0.5:
        return "auto"
    if r_minus_g > 0.5:
        return "requires_surplus"
    return "borderline"


# ── Private helpers ──────────────────────────────────────────────────────────

def _normalize(value: float, feat: str) -> float:
    s = _STATS.get(feat, {"mean": 0.0, "std": 1.0})
    std = s["std"] if s["std"] > 0 else 1.0
    return (value - s["mean"]) / std


def _query_vector(run: dict[str, list[float]]) -> dict[str, float]:
    q: dict[str, float] = {}
    for series_key, col in _SERIES_TO_PANEL.items():
        q[col] = run[series_key][0]
    q["r_minus_g"] = q["interest_rate_10y"] - q["gdp_growth"]
    return q


def _dominant_lever(levers: Levers) -> str | None:
    """Return the lever id with the largest fractional deviation from baseline."""
    from engine.constants import BASE_LEVERS
    max_frac = 0.0
    dom = None
    for spec in LEVER_SPECS:
        lid = spec["id"]
        span = spec["max"] - spec["min"]
        if span == 0:
            continue
        frac = abs(getattr(levers, lid) - BASE_LEVERS[lid]) / span
        if frac > max_frac:
            max_frac = frac
            dom = lid
    return dom


def _distance(q_norm: np.ndarray, row_norm: np.ndarray) -> float:
    diff = q_norm - row_norm
    if _USE_EUCLIDEAN or _COV_INV is None:
        return float(np.dot(diff, diff) ** 0.5)
    return float((diff @ _COV_INV @ diff) ** 0.5)


def _maybe(row: "pd.Series", col: str) -> float | None:
    v = row.get(col)
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else float(v)


def _outcome_trajectory(
    iso3: str, match_year: int, horizon: int
) -> tuple[list[dict], bool]:
    sub = ANALOG_PANEL[ANALOG_PANEL["iso3"] == iso3].sort_values("year")
    pts: list[dict] = []
    any_truncated = False
    for offset in range(1, horizon + 1):
        yr = match_year + offset
        row = sub[sub["year"] == yr]
        if row.empty:
            pts.append({
                "year_offset": offset,
                "debt_gdp": None,
                "gdp_growth": None,
                "primary_balance_gdp": None,
                "r_minus_g": None,
                "truncated": True,
            })
            any_truncated = True
        else:
            r = row.iloc[0]
            r_minus_g_val = _maybe(r, "r_minus_g")
            if r_minus_g_val is None:
                # Compute from component fields when direct value is NaN
                ir = _maybe(r, "interest_rate_10y")
                g = _maybe(r, "gdp_growth")
                r_minus_g_val = float(ir - g) if ir is not None and g is not None else 0.0
            pts.append({
                "year_offset": offset,
                "debt_gdp": _maybe(r, "debt_gdp"),
                "gdp_growth": _maybe(r, "gdp_growth"),
                "primary_balance_gdp": _maybe(r, "primary_balance_gdp"),
                "r_minus_g": r_minus_g_val,
                "truncated": False,
            })
    return pts, any_truncated


def structural_diffs(analog_row: "pd.Series") -> list[dict]:
    """Return 8 structural diff dicts comparing analog_row to Spain 2026."""
    diffs: list[dict] = []

    # 1. EMU membership
    emu_raw = analog_row.get("emu_member", 0)
    emu_a = 0 if emu_raw is None or (isinstance(emu_raw, float) and np.isnan(emu_raw)) \
            else int(emu_raw)
    emu_s = _SPAIN_STRUCT["emu_member"]
    diffs.append({
        "dimension": "emu_member",
        "label": _DIFF_LABELS["emu_member"],
        "spain_value": "Sí" if emu_s else "No",
        "analog_value": "Sí" if emu_a else "No",
        "direction": "converge" if emu_a == emu_s else "diverge",
    })

    # 2. FX regime
    fx_a = str(analog_row.get("fx_regime", "float"))
    fx_s = _SPAIN_STRUCT["fx_regime"]
    diffs.append({
        "dimension": "fx_regime",
        "label": _DIFF_LABELS["fx_regime"],
        "spain_value": fx_s,
        "analog_value": fx_a,
        "direction": "converge" if fx_a == fx_s else "diverge",
    })

    # 3. External debt share (gap > 20pp → diverge)
    ext_a = float(analog_row.get("ext_debt_share") or 0)
    ext_s = _SPAIN_STRUCT["ext_debt_share"]
    gap_ext = abs(ext_a - ext_s)
    diffs.append({
        "dimension": "ext_debt_share",
        "label": _DIFF_LABELS["ext_debt_share"],
        "spain_value": f"{ext_s:.0f}%",
        "analog_value": f"{ext_a:.0f}%",
        "direction": "diverge" if gap_ext > 20 else "neutral",
    })

    # 4. Democracy (Polity5 < 6 → diverge)
    dem_a = float(analog_row.get("democracy") or 9)
    dem_s = _SPAIN_STRUCT["democracy"]
    diffs.append({
        "dimension": "democracy",
        "label": _DIFF_LABELS["democracy"],
        "spain_value": str(int(dem_s)),
        "analog_value": str(int(dem_a)),
        "direction": "diverge" if dem_a < 6 else "converge",
    })

    # 5. Trade openness (within ±15pp → neutral)
    trd_a = float(analog_row.get("trade_openness") or 0)
    trd_s = _SPAIN_STRUCT["trade_openness"]
    gap_trd = abs(trd_a - trd_s)
    diffs.append({
        "dimension": "trade_openness",
        "label": _DIFF_LABELS["trade_openness"],
        "spain_value": f"{trd_s:.0f}%",
        "analog_value": f"{trd_a:.0f}%",
        "direction": "neutral" if gap_trd <= 15
                     else ("converge" if trd_a >= trd_s else "diverge"),
    })

    # 6. Debt maturity proxy (via ext_debt_share; >20pp → diverge)
    diffs.append({
        "dimension": "debt_maturity",
        "label": _DIFF_LABELS["debt_maturity"],
        "spain_value": "largo plazo",
        "analog_value": "largo plazo" if gap_ext <= 20 else "más corto",
        "direction": "diverge" if gap_ext > 20 else "neutral",
    })

    # 7. TFP trend (gap > 1pp → diverge)
    tfp_a = float(analog_row.get("tfp_growth_5y") or 0)
    tfp_s = _SPAIN_STRUCT["tfp_growth_5y"]
    gap_tfp = abs(tfp_a - tfp_s)
    diffs.append({
        "dimension": "tfp_trend",
        "label": _DIFF_LABELS["tfp_trend"],
        "spain_value": f"{tfp_s:+.1f}%/a",
        "analog_value": f"{tfp_a:+.1f}%/a",
        "direction": "diverge" if gap_tfp > 1.0 else "neutral",
    })

    # 8. Labor productivity (gap > 1.5pp → diverge)
    lp_a = float(analog_row.get("labor_prod_growth_5y") or 0)
    lp_s = _SPAIN_STRUCT["labor_prod_growth_5y"]
    gap_lp = abs(lp_a - lp_s)
    diffs.append({
        "dimension": "labor_productivity",
        "label": _DIFF_LABELS["labor_productivity"],
        "spain_value": f"{lp_s:+.1f}%/a",
        "analog_value": f"{lp_a:+.1f}%/a",
        "direction": "diverge" if gap_lp > 1.5 else "neutral",
    })

    return diffs


def _fallback_narrative(match: dict) -> str:
    iso3 = match["iso3"]
    name = _NAMES.get(iso3, iso3)
    yr = match["match_year"]
    outcome = match["outcome"]
    non_trunc = [p for p in outcome if not p["truncated"] and p["debt_gdp"] is not None]
    if non_trunc:
        debt_end = non_trunc[-1]["debt_gdp"]
        debt_start = match["match_snapshot"]["debt_gdp"]
        n_yrs = non_trunc[-1]["year_offset"]
        div_dims = [d["label"] for d in match["diffs"] if d["direction"] == "diverge"]
        top_div = div_dims[0] if div_dims else "ninguna identificada"
        direction = "aumentó" if debt_end > debt_start else "cayó"
        transferable = "no puede" if div_dims else "puede"
        return (
            f"{name} en {yr}: deuda pasó de {debt_start:.0f}% a {debt_end:.0f}% "
            f"en {n_yrs} años ({direction}). "
            f"Diferencias estructurales clave: {top_div}. "
            f"El resultado histórico {transferable} extrapolarse directamente a España "
            f"por {top_div}."
        )
    return f"{name} en {yr}: datos de trayectoria insuficientes para el horizonte solicitado."


def find_analogs(levers: Levers, horizon: int = 10) -> list[dict]:
    """Return top-3 historical analogs for `levers`, sorted by rank ascending."""
    run = run_scenario(levers)
    q_raw = _query_vector(run)

    # Normalize query vector (NaN → z-score 0 via _normalize with stats mean)
    q_norm = np.array([_normalize(q_raw[f], f) for f in QUERY_FEATURES])

    # Exclude ESP rows; aggregate codes already removed at load time
    panel = ANALOG_PANEL[ANALOG_PANEL["iso3"] != "ESP"].copy()

    # Dominant lever bonus: which lever deviated most from baseline?
    dom_lever = _dominant_lever(levers)
    dom_panel_col: str | None = _SERIES_TO_PANEL.get(dom_lever or "", None)

    # Precompute rolling stats for dominant lever bonus (keyed by (iso3, year))
    _rolling_stats: dict[tuple[str, int], tuple[float, float]] = {}
    if dom_panel_col and dom_panel_col in panel.columns:
        for iso3_grp, grp in panel.groupby("iso3"):
            grp_sorted = grp.sort_values("year")
            rol_mean = grp_sorted[dom_panel_col].rolling(5, min_periods=3).mean()
            rol_std = grp_sorted[dom_panel_col].rolling(5, min_periods=3).std()
            for i, (_, r) in enumerate(grp_sorted.iterrows()):
                m_val = rol_mean.iloc[i]
                s_val = rol_std.iloc[i]
                if pd.notna(m_val) and pd.notna(s_val):
                    _rolling_stats[(str(r["iso3"]), int(r["year"]))] = (
                        float(m_val), float(s_val)
                    )

    scores: list[tuple[float, int]] = []
    for idx, row in panel.iterrows():
        # Skip rows without 3+ forward data years
        if row["year"] > 2020:
            continue

        # Build normalized row vector; NaN → 0.0 (z-score = mean)
        row_vals = []
        for f in QUERY_FEATURES:
            v = row.get(f)
            row_vals.append(
                0.0 if (v is None or (isinstance(v, float) and np.isnan(v)))
                else float(v)
            )
        row_norm = np.array([_normalize(v, f) for v, f in zip(row_vals, QUERY_FEATURES)])

        dist = _distance(q_norm, row_norm)

        # Dominant lever bonus: 20% score reduction if the dominant variable was
        # anomalous (>1σ from country's own rolling mean) in this episode
        bonus = 0.0
        if dom_panel_col and dom_panel_col in QUERY_FEATURES:
            key = (str(row["iso3"]), int(row["year"]))
            if key in _rolling_stats:
                mean_val, std_val = _rolling_stats[key]
                val_idx = QUERY_FEATURES.index(dom_panel_col)
                if std_val > 0 and abs(row_vals[val_idx] - mean_val) > std_val:
                    bonus = 0.20 * dist

        scores.append((dist - bonus, int(idx)))

    scores.sort(key=lambda x: x[0])
    top3_idx = [idx for _, idx in scores[:3]]

    matches: list[dict] = []
    for rank, idx in enumerate(top3_idx, 1):
        row = ANALOG_PANEL.loc[idx]
        iso3 = str(row["iso3"])
        match_year = int(row["year"])
        snapshot: dict[str, float] = {}
        for f in QUERY_FEATURES:
            v = row.get(f)
            snapshot[f] = (
                0.0 if (v is None or (isinstance(v, float) and np.isnan(v)))
                else float(v)
            )
        outcome, any_trunc = _outcome_trajectory(iso3, match_year, horizon)
        diffs = structural_diffs(row)
        r_g_val = snapshot.get("r_minus_g", 0.0)

        match: dict = {
            "rank": rank,
            "iso3": iso3,
            "country_name": _NAMES.get(iso3, iso3),
            "match_year": match_year,
            "distance": round(scores[rank - 1][0], 4),
            "dominant_lever": dom_lever or "none",
            "match_snapshot": snapshot,
            "outcome": outcome,
            "outcome_truncated": any_trunc,
            "diffs": diffs,
            "debt_payable_verdict": debt_payable_verdict(r_g_val),
            "narrative": None,
        }
        matches.append(match)

    return matches
