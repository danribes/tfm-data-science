"""Every named engine constant — the single source of truth (spec §4.1).

Spain constants are the v16 calibration, ported verbatim from
docs/superpowers/plans/references/v16-engine-extract.md S1 (extract L69-91:
`const BASE` and `const C`). They are calibrated defaults, NOT estimates —
phase 3 contests may replace them (AC-V6). Vintage-anchored values (V0,
BASE_LEVERS) load from the committed gold slice, never hardcoded twice.

Generic-engine defaults (OKUN_COEFFICIENT, PHILLIPS_SLOPE) are imported from
engine.generic to avoid duplication — CONSTANTS_TABLE always reflects the
canonical runtime values.
"""
from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path

from engine.generic import OKUN_COEFFICIENT, PHILLIPS_SLOPE

GOLD_DIR = Path(__file__).resolve().parents[1] / "data" / "gold"
VINTAGE = (GOLD_DIR / "VINTAGE").read_text(encoding="utf-8").strip()
ENGINE_VERSION = "1.0.0"

# ---- Spain semi-structural constants (v16 `const C`, extract L73-91) ----
MULT = 1.40      # fiscal multiplier (CORE Macro U3)
RHO = 0.62       # persistence of the GDP level deviation
E_R = 0.45       # pp of GDP per pp of interest rate (investment/consumption)
E_EXT = 0.25     # external-demand channel weight (U7)
E_PM = 0.012     # pp of GDP per 1 % import-price shock
OKUN = 0.48      # Okun beta, Spain calibration (generic engine uses 0.5)
KAPPA = 0.22     # Phillips slope
GAMMA = 0.045    # import-price pass-through to HICP (2021-23 episode)
THETA = 0.55     # inflation-expectations inertia
PHI = 0.30       # wage-setting: nominal wage response per pp of slack
A_Z = 1.10       # u* shifter: labour institutions (WS-PS)
A_TAU = 0.30     # u* shifter: tax wedge (WS)
A_LAM = 0.45     # u* shifter: productivity (PS)
REFI = 0.14      # share of sovereign debt refinanced each year
TERM = 0.17      # 10y term premium over Euribor (3.42 − 2.80 − 0.45)
DIFF = 1.4757    # implicit mortgage spread pp — build_v16.py bisection to the
                 # €744.89 median of gold_cuota_teorica.csv at Euribor 2.80
IPV_LR = 3.0     # house-price long-run growth (% a/a)
IPV_REV = 0.60   # yearly reversion of IPV toward IPV_LR
E_IPV_R = 2.6    # IPV response to the rate lever
E_IPV_G = 1.1    # IPV response to the growth deviation
RJUV = 2.317     # youth/total unemployment ratio (stable in the 5y series)
PM_DECAY = 0.45  # geometric decay of the import-price Phillips term (extract L116)

# ---- Monte Carlo DSA calibration (fitted against gold_escenarios_deuda_mc.csv;
#      seed-42 / 4000-path verification: max |dev| vs gold p5/p50/p95 at
#      2030/2050/2070 = 1.399 pp — see Task 8 / tests/test_anchors.py A5) ----
MC_START_YEAR = 2026
MC_HORIZON = 2070
MC_N_PATHS = 4000
MC_SEED_DEFAULT = 42
MC_RHO = 0.96          # AR(1) persistence of the r/g/sp shocks
MC_SIG_R = 0.42        # pp — annual innovation, effective interest rate
MC_SIG_G = 0.12        # pp — annual innovation, nominal growth
MC_SIG_SP = 0.30       # pp GDP — annual innovation, primary balance
MC_FB_UP = 0.010       # fiscal-reaction brake when debt runs above the deterministic path
MC_FB_DN = 0.005       # symmetric loosening when debt runs below it
MC_PB_DRIFT = (-0.10884, -0.34459, 0.75410)  # pb calib add-on: ≤2030 / 2031-2050 / 2051-2070
MC_EXT_SLOPE_R = 0.006       # r_efectivo slope after 2050: (3.47 − 3.44) / 5
MC_EXT_SLOPE_PB = -0.136     # pb slope after 2050: (−7.47 − (−6.79)) / 5
MC_EXT_SLOPE_DEMOG = 0.136   # presion_demog slope after 2050: (6.57 − 5.89) / 5

# ---- gold-slice loaders ----
@lru_cache(maxsize=1)
def load_kpis() -> dict:
    return json.loads((GOLD_DIR / "kpis_perfiles.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_central() -> dict[int, dict[str, float]]:
    out: dict[int, dict[str, float]] = {}
    with (GOLD_DIR / "gold_escenarios_deuda.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["escenario"] != "central":
                continue
            out[int(float(row["year"]))] = {
                "deuda": float(row["deuda"]), "pb": float(row["pb"]),
                "r_efectivo": float(row["r_efectivo"]),
                "g_nominal": float(row["g_nominal"]),
                "presion_demog": float(row["presion_demog"]),
            }
    return out


@lru_cache(maxsize=1)
def load_olddep() -> dict[int, float]:
    out: dict[int, float] = {}
    with (GOLD_DIR / "gold_projections.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["geo"] == "ES" and row["variant"] == "BSL":
                out[int(float(row["year"]))] = float(row["olddep"])
    return out


def _kpi(name: str) -> float:
    return float(load_kpis()["kpi"][name]["valor"])


# build_v16.py `calib` block (extract L1031-1040)
CAL_SALARIO_MES = round(_kpi("salario_medio") / 14, 2)   # 1749.79

# v16 `const V0` (extract L41-66): the vintage values anchoring year 0
V0: dict[str, float] = {
    "u": _kpi("paro_total"),                 # 10.1 % (2026-06)
    "pi": _kpi("hicp_es"),                   # 3.0 % a/a (2025-12)
    "g": _kpi("pib_yoy"),                    # 2.7 % a/a (2026-Q2)
    "bono": _kpi("bono10y_es"),              # 3.42 % (2026-06)
    "precio": _kpi("precio_vivienda_mediano"),  # 171444 EUR (2024)
    "cuota": _kpi("cuota_hipoteca_mediana"),    # 745 EUR/mes
    "salmes": CAL_SALARIO_MES,               # 1749.79 EUR (24497/14)
    "salario": _kpi("salario_medio"),        # 24497 EUR/año
    "ipv": _kpi("vivienda_precio_yoy"),      # 12.8 % a/a (2026-Q1)
    "pens": _kpi("gasto_pensiones_pib"),     # 13.23 % PIB (2024)
    "arop": _kpi("arop_infantil"),           # 28.5 % (2025)
    "edu": _kpi("gasto_educacion_pib"),      # 4.1 % PIB
    "d1": _kpi("salarios_publicos_pib"),     # 10.9 % PIB
    "p2": _kpi("consumo_intermedio_pib"),    # 5.7 % PIB
    "d3": _kpi("subvenciones_pib"),          # 1.4 % PIB
    "p51": _kpi("inversion_publica_pib"),    # 3.0 % PIB
    "gtot": _kpi("gasto_total_pib"),         # 45.4 % PIB
    "temp": _kpi("temporalidad"),            # 15.3 %
    "auton": _kpi("autoempleo"),             # 14.5 %
    "bls": _kpi("bls_endurecimiento"),       # 10.0 % neto
    "hip": _kpi("hipotecas_anuales"),        # 500906 /año
    "sobre": _kpi("sobrecarga_vivienda"),    # 7.2 %
    "ujuv": _kpi("paro_juvenil"),            # 23.4 %
    "vida": _kpi("esperanza_vida"),          # 84.0 años
}

# v16 `const BASE` (extract L69-70 / L1598-1599): lever base = the vintage
BASE_LEVERS: dict[str, float] = {
    "r": _kpi("euribor12m"),         # 2.8 % (2026-06)
    "prima": _kpi("spread_es_de"),   # 45 pb (2026-06)
    "sp": 0.0, "lam": 0.9, "pm": 0.0, "tau": 0.0,
    "z": 0.0, "ext": 1.8, "dem": 0.0, "idx": 0.0,
}

_V16 = "v16 calibration — calibrated default, not estimated (phase 3 contests may replace, AC-V6)"
_MC = "MC calibration fitted to gold_escenarios_deuda_mc.csv central envelopes (this repo, phase 1)"

CONSTANTS_TABLE: list[dict] = [
    {"name": "MULT", "value": MULT, "unit": "x", "provenance": _V16 + " · fiscal multiplier, CORE Macro U3"},
    {"name": "RHO", "value": RHO, "unit": "x", "provenance": _V16 + " · GDP-level persistence"},
    {"name": "E_R", "value": E_R, "unit": "pp GDP / pp rate", "provenance": _V16},
    {"name": "E_EXT", "value": E_EXT, "unit": "x", "provenance": _V16 + " · external-demand channel"},
    {"name": "E_PM", "value": E_PM, "unit": "pp GDP / %", "provenance": _V16 + " · import-price channel"},
    {"name": "OKUN", "value": OKUN, "unit": "pp u / pp GDP", "provenance": _V16 + " · Spain Okun (generic engine uses 0.5)"},
    {"name": "KAPPA", "value": KAPPA, "unit": "pp pi / pp gap", "provenance": _V16 + " · Phillips slope"},
    {"name": "GAMMA", "value": GAMMA, "unit": "pp pi / %", "provenance": _V16 + " · pass-through, 2021-23 episode"},
    {"name": "THETA", "value": THETA, "unit": "x", "provenance": _V16 + " · inflation inertia"},
    {"name": "PHI", "value": PHI, "unit": "pp wage / pp gap", "provenance": _V16 + " · wage-setting curve"},
    {"name": "A_Z", "value": A_Z, "unit": "pp u* / index", "provenance": _V16 + " · WS-PS shifter"},
    {"name": "A_TAU", "value": A_TAU, "unit": "pp u* / pp", "provenance": _V16 + " · WS-PS shifter"},
    {"name": "A_LAM", "value": A_LAM, "unit": "pp u* / pp", "provenance": _V16 + " · WS-PS shifter"},
    {"name": "REFI", "value": REFI, "unit": "share/yr", "provenance": _V16 + " · debt refinancing share 14 %/yr"},
    {"name": "TERM", "value": TERM, "unit": "pp", "provenance": _V16 + " · 10y term premium (3.42 − 2.80 − 0.45)"},
    {"name": "DIFF", "value": DIFF, "unit": "pp", "provenance": "build_v16.py bisection vs gold_cuota_teorica.csv €744.89 median at Euribor 2.80"},
    {"name": "IPV_LR", "value": IPV_LR, "unit": "% a/a", "provenance": _V16 + " · house-price long run"},
    {"name": "IPV_REV", "value": IPV_REV, "unit": "x", "provenance": _V16 + " · IPV reversion"},
    {"name": "E_IPV_R", "value": E_IPV_R, "unit": "pp IPV / pp rate", "provenance": _V16},
    {"name": "E_IPV_G", "value": E_IPV_G, "unit": "pp IPV / pp growth", "provenance": _V16},
    {"name": "RJUV", "value": RJUV, "unit": "x", "provenance": _V16 + " · youth/total unemployment ratio, 5y series"},
    {"name": "PM_DECAY", "value": PM_DECAY, "unit": "x", "provenance": _V16 + " · import-price shock decay"},
    {"name": "CAL_SALARIO_MES", "value": CAL_SALARIO_MES, "unit": "EUR/mes", "provenance": "kpis_perfiles.json salario_medio 24497 / 14 (build_v16 calib)"},
    {"name": "GENERIC_OKUN", "value": OKUN_COEFFICIENT, "unit": "pp u / pp GDP", "provenance": "engine.generic.OKUN_COEFFICIENT (generic engine calibrated default, literature 0.3-0.5), NOT country-specific — distinct from Spain's 0.48"},
    {"name": "GENERIC_PHILLIPS", "value": PHILLIPS_SLOPE, "unit": "pp pi / pp gap", "provenance": "engine.generic.PHILLIPS_SLOPE (generic engine calibrated default, NOT country-specific — distinct from Spain's 0.22)"},
    {"name": "MC_RHO", "value": MC_RHO, "unit": "x", "provenance": _MC},
    {"name": "MC_SIG_R", "value": MC_SIG_R, "unit": "pp", "provenance": _MC},
    {"name": "MC_SIG_G", "value": MC_SIG_G, "unit": "pp", "provenance": _MC},
    {"name": "MC_SIG_SP", "value": MC_SIG_SP, "unit": "pp GDP", "provenance": _MC},
    {"name": "MC_FB_UP", "value": MC_FB_UP, "unit": "1/yr", "provenance": _MC + " · fiscal-reaction brake"},
    {"name": "MC_FB_DN", "value": MC_FB_DN, "unit": "1/yr", "provenance": _MC + " · fiscal-reaction loosening"},
]
