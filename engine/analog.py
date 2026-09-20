"""Descriptive historical neighbours using comparable macroeconomic variables.

The frozen legacy panel misnames WB private lending rates as sovereign yields.
Those rates are display-only, correctly labelled, and never used to compute a
sovereign interest-growth differential or a sustainability verdict. Similarity
is descriptive, not a causal estimate or a validated forecast.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine.constants import GOLD_DIR, BASE_LEVERS
from engine.levers import LEVER_SPECS, Levers
from engine.spain import Y0, Y1, run_scenario

QUERY_FEATURES = [
    "debt_gdp", "overall_balance_gdp", "gdp_growth", "unemployment", "inflation",
]
_SERIES_TO_PANEL = {
    "b": "debt_gdp", "saldo": "overall_balance_gdp", "g": "gdp_growth",
    "u": "unemployment", "pi": "inflation",
}

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


LIMITATIONS = (
    "Vecinos descriptivos; sin validación predictiva independiente. "
    "La búsqueda usa cinco variables completas y excluye España. "
    "El tipo bancario de préstamo no es un rendimiento soberano y no entra en "
    "la distancia. No se estima r−g soberano ni sostenibilidad de la deuda. "
    "Episodios cercanos del mismo país pueden solaparse."
)


def _fit_metric(frame: pd.DataFrame) -> tuple[dict, np.ndarray]:
    """Fit standardization and covariance in the SAME coordinate system.

    The pseudoinverse permits redundant features without changing units or
    silently switching to a different distance. Complete cases are required;
    missing measurements are never treated as observed average values.
    """
    complete = frame[QUERY_FEATURES].replace([np.inf, -np.inf], np.nan).dropna()
    if len(complete) <= len(QUERY_FEATURES):
        raise ValueError("Insufficient complete historical observations for analog metric")
    means = complete.mean()
    stds = complete.std().replace(0.0, 1.0)
    z = (complete - means) / stds
    covariance = np.cov(z.to_numpy(), rowvar=False)
    stats = {f: {"mean": float(means[f]), "std": float(stds[f])} for f in QUERY_FEATURES}
    return stats, np.linalg.pinv(covariance, hermitian=True)


def _load() -> tuple[pd.DataFrame, dict, np.ndarray]:
    panel = pd.read_csv(GOLD_DIR / "gold_analog_panel.csv")
    panel = panel[panel.iso3.str.fullmatch(r"[A-Z]{3}")].copy()
    # Compatibility adapter for the preserved 2026-09-06 source artifact.
    if "lending_rate" not in panel and "interest_rate_10y" in panel:
        panel = panel.rename(columns={"interest_rate_10y": "lending_rate"})
    panel = panel.drop(columns=["r_minus_g"], errors="ignore")
    candidates = panel[(panel.iso3 != "ESP") & (panel.year <= 2020)]
    stats, cov_inv = _fit_metric(candidates)
    return panel.reset_index(drop=True), stats, cov_inv


ANALOG_PANEL, _STATS, _COV_INV = _load()


def _normalize(value: float, feat: str) -> float:
    return (value - _STATS[feat]["mean"]) / _STATS[feat]["std"]


def _distance(q_norm: np.ndarray, row_norm: np.ndarray) -> float:
    diff = q_norm - row_norm
    return float(np.sqrt(max(0.0, diff @ _COV_INV @ diff)))


def _query_vector(run: dict[str, list[float]], year: int = Y0) -> dict[str, float]:
    if not Y0 <= year <= Y1:
        raise ValueError(f"query year must be between {Y0} and {Y1}")
    return {col: float(run[key][year - Y0]) for key, col in _SERIES_TO_PANEL.items()}


def _dominant_lever(levers: Levers) -> str | None:
    deltas = [(abs(getattr(levers, s["id"]) - BASE_LEVERS[s["id"]]) /
               (s["max"] - s["min"]), s["id"]) for s in LEVER_SPECS]
    size, lever = max(deltas)
    return lever if size > 0 else None


def _maybe(row: pd.Series, col: str) -> float | None:
    value = row.get(col)
    return None if value is None or pd.isna(value) else float(value)


def _outcome_trajectory(iso3: str, match_year: int, horizon: int) -> tuple[list[dict], bool]:
    country = ANALOG_PANEL[ANALOG_PANEL.iso3 == iso3].set_index("year")
    points = []
    for offset in range(1, horizon + 1):
        year = match_year + offset
        row = country.loc[year] if year in country.index else pd.Series(dtype=float)
        points.append({
            "year_offset": offset,
            **{key: _maybe(row, key) for key in
               ("debt_gdp", "gdp_growth", "overall_balance_gdp")},
            # Retained for old clients; the source cannot identify this quantity.
            "r_minus_g": None,
            "truncated": row.empty,
        })
    return points, any(p["truncated"] for p in points)


def structural_diffs(row: pd.Series) -> list[dict]:
    """Observed context only; static political proxies are not historical data."""
    spain = ANALOG_PANEL[ANALOG_PANEL.iso3 == "ESP"].sort_values("year")
    emu = _maybe(row, "emu_member")
    diffs = [{"dimension": "emu_member", "label": "Zona euro",
              "spain_value": "Sí (2026)",
              "analog_value": "sin datos" if emu is None else ("Sí" if emu else "No"),
              "direction": "neutral" if emu is None else ("converge" if emu else "diverge")}]
    # The legacy panel contains time-invariant hand-assigned FX/political
    # values and a debt/GNI ratio. None establishes these historical contrasts.
    for dimension, label in (("fx_regime", "Régimen cambiario histórico"),
                             ("ext_debt_share", "Deuda externa / deuda total"),
                             ("democracy", "Calidad institucional observada"),
                             ("debt_maturity", "Vencimiento de la deuda")):
        diffs.append({"dimension": dimension, "label": label,
                      "spain_value": "sin datos comparables", "analog_value": "sin datos comparables",
                      "direction": "neutral"})
    for dimension, col, label, threshold in (
        ("trade_openness", "trade_openness", "Apertura comercial (% PIB)", 15.0),
        ("tfp_trend", "tfp_growth_5y", "Tendencia TFP (% anual, media 5 años)", 1.0),
        ("labor_productivity", "labor_prod_growth_5y", "Productividad laboral (% anual, media 5 años)", 1.5),
    ):
        available = spain.dropna(subset=[col]) if col in spain else pd.DataFrame()
        reference = available.iloc[-1] if not available.empty else pd.Series(dtype=float)
        a, b = _maybe(row, col), _maybe(reference, col)
        diffs.append({"dimension": dimension, "label": label,
                      "spain_value": "sin datos" if b is None else f"{b:.1f} ({int(reference.year)})",
                      "analog_value": "sin datos" if a is None else f"{a:.1f}",
                      "direction": "neutral" if a is None or b is None else
                          ("diverge" if abs(a - b) > threshold else "converge")})
    return diffs


def _fallback_narrative(match: dict) -> str:
    observed = [p for p in match["outcome"] if p["debt_gdp"] is not None]
    statement = "Trayectoria posterior incompleta."
    if observed:
        point = observed[-1]
        statement = (f"La deuda pasó de {match['match_snapshot']['debt_gdp']:.1f}% "
                     f"a {point['debt_gdp']:.1f}% del PIB en {point['year_offset']} años.")
    return (f"{match['country_name']} en {match['match_year']}: {statement} "
            "La similitud descriptiva no demuestra que España vaya a seguir esa trayectoria.")


def find_analogs(levers: Levers, horizon: int = 10, *, query_year: int | None = None) -> list[dict]:
    """Top three complete historical neighbours of the selected scenario year.

    The historical follow-up length is `horizon`. The dominant lever is context
    only: no unvalidated bonus changes the Mahalanobis ranking.
    """
    if not 1 <= horizon <= Y1 - Y0:
        raise ValueError("analog horizon must be between 1 and 24 years")
    year = Y0 + horizon if query_year is None else query_year
    query = _query_vector(run_scenario(levers), year)
    qz = np.array([_normalize(query[f], f) for f in QUERY_FEATURES])
    candidates = ANALOG_PANEL[(ANALOG_PANEL.iso3 != "ESP") & (ANALOG_PANEL.year <= 2020)]
    candidates = candidates.replace([np.inf, -np.inf], np.nan).dropna(subset=QUERY_FEATURES)
    scores = []
    for idx, row in candidates.iterrows():
        z = np.array([_normalize(float(row[f]), f) for f in QUERY_FEATURES])
        scores.append((_distance(qz, z), int(idx)))
    scores.sort()
    matches = []
    for rank, (distance, idx) in enumerate(scores[:3], 1):
        row = ANALOG_PANEL.loc[idx]
        snapshot = {f: _maybe(row, f) for f in QUERY_FEATURES}
        snapshot.update(lending_rate=_maybe(row, "lending_rate"), interest_rate_10y=None, r_minus_g=None)
        outcome, truncated = _outcome_trajectory(str(row.iso3), int(row.year), horizon)
        match = {"rank": rank, "iso3": str(row.iso3), "country_name": _NAMES.get(row.iso3, row.iso3),
                 "match_year": int(row.year), "distance": round(distance, 6),
                 "dominant_lever": _dominant_lever(levers), "match_snapshot": snapshot,
                 "outcome": outcome, "outcome_truncated": truncated,
                 "diffs": structural_diffs(row), "debt_payable_verdict": "not_assessed",
                 "narrative": None}
        match["narrative"] = _fallback_narrative(match)
        matches.append(match)
    return matches
