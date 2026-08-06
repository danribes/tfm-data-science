"""Stochastic DSA (spec §4.3) — plan_maestro-style Monte Carlo around the
deterministic path: normal AR(1) shocks on r, g and sp, 4,000 paths to 2070.

The deterministic backbone applies the same lever-deviation chain as
engine/spain.py to the gold central scenario, extended past 2050 with the
MC_EXT_* slopes. MC_PB_DRIFT and the MC_FB_* fiscal-reaction terms are
calibration constants fitted so the seed-42/4000-path envelope reproduces the
inherited gold fan (gold_escenarios_deuda_mc.csv central) within ±2 pp at
2030/2050/2070 — the fan is a calibrated reproduction of plan_maestro's
stochastic identity, not a new forecasting claim.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from engine import constants as c
from engine.levers import Levers


@dataclass
class McResult:
    years: list[int]
    percentiles: dict[str, list[float]]
    n_paths: int
    seed: int


_PCT_LEVELS = (5, 25, 50, 75, 95)


def mc_input_paths(levers: Levers) -> tuple[list[int], np.ndarray, np.ndarray, np.ndarray]:
    """Deterministic (years, ief, gnom, pb) to 2070 under `levers`.

    Mirrors the engine/spain.py deviation chain (extract L95-175) for the three
    debt-identity inputs, over 45 years instead of 25.
    """
    L, B, V0 = levers, c.BASE_LEVERS, c.V0
    central = c.load_central()
    years = list(range(c.MC_START_YEAR, c.MC_HORIZON + 1))

    bono = L.r + c.TERM + L.prima / 100
    shock = (-(L.sp - B["sp"]) - c.E_R * (L.r - B["r"])
             + c.E_EXT * (L.ext - B["ext"]) - c.E_PM * (L.pm - B["pm"]))

    ief, gnom, pb = [], [], []
    lvl = pi_dev = di = 0.0
    for k, y in enumerate(years):
        if y <= 2050:
            c_r, c_g = central[y]["r_efectivo"], central[y]["g_nominal"]
            c_pb, c_dm = central[y]["pb"], central[y]["presion_demog"]
        else:
            c_r = central[2050]["r_efectivo"] + c.MC_EXT_SLOPE_R * (y - 2050)
            c_g = central[2050]["g_nominal"]
            c_pb = central[2050]["pb"] + c.MC_EXT_SLOPE_PB * (y - 2050)
            c_dm = central[2050]["presion_demog"] + c.MC_EXT_SLOPE_DEMOG * (y - 2050)
        prev = lvl
        lvl = c.RHO * lvl + (1 - c.RHO) * c.MULT * shock
        gap_u = c.OKUN * lvl
        pi_dev = (c.THETA * pi_dev + c.KAPPA * gap_u
                  + c.GAMMA * (L.pm - B["pm"]) * c.PM_DECAY ** k)
        g = V0["g"] + (lvl - prev) + (L.lam - B["lam"])
        di = di + c.REFI * ((bono - V0["bono"]) - di)
        drift = (c.MC_PB_DRIFT[0] if y <= 2030
                 else c.MC_PB_DRIFT[1] if y <= 2050 else c.MC_PB_DRIFT[2])
        ief.append(c_r + di)
        gnom.append(c_g + (g - V0["g"]) + pi_dev)
        pb.append(c_pb + L.sp - c_dm * L.dem + drift)
    return years, np.asarray(ief), np.asarray(gnom), np.asarray(pb)


def run_montecarlo(levers: Levers = Levers(), n_paths: int = c.MC_N_PATHS,
                   seed: int = c.MC_SEED_DEFAULT) -> McResult:
    years, ief, gnom, pb = mc_input_paths(levers)
    b0 = c.load_central()[c.MC_START_YEAR - 1]["deuda"]     # 105.6 (2025)

    # deterministic reference path (anchor for the fiscal-reaction brake)
    b_det: list[float] = []
    b = b0
    for i in range(len(years)):
        b = b * (1 + ief[i] / 100) / (1 + gnom[i] / 100) - pb[i]
        b_det.append(b)

    rng = np.random.default_rng(seed)
    paths = np.full(n_paths, b0, dtype=float)
    b_det_prev = b0
    e_r = np.zeros(n_paths); e_g = np.zeros(n_paths); e_sp = np.zeros(n_paths)
    percentiles: dict[str, list[float]] = {f"p{p}": [] for p in _PCT_LEVELS}
    for i in range(len(years)):
        e_r = c.MC_RHO * e_r + rng.normal(0.0, c.MC_SIG_R, n_paths)
        e_g = c.MC_RHO * e_g + rng.normal(0.0, c.MC_SIG_G, n_paths)
        e_sp = c.MC_RHO * e_sp + rng.normal(0.0, c.MC_SIG_SP, n_paths)
        dev = paths - b_det_prev
        pb_eff = (pb[i] + e_sp + c.MC_FB_UP * np.maximum(0.0, dev)
                  + c.MC_FB_DN * np.minimum(0.0, dev))
        paths = (paths * (1 + (ief[i] + e_r) / 100) / (1 + (gnom[i] + e_g) / 100)
                 - pb_eff)
        b_det_prev = b_det[i]
        q = np.percentile(paths, _PCT_LEVELS)
        for j, p in enumerate(_PCT_LEVELS):
            percentiles[f"p{p}"].append(float(q[j]))
    return McResult(years=years, percentiles=percentiles, n_paths=n_paths, seed=seed)
