"""Spain semi-structural engine — faithful Python port of v16 `run(L)`
(docs/superpowers/plans/references/v16-engine-extract.md S1, L95-175).

Deviation semantics: the baseline freezes the vintage (gold central scenario +
V0 KPIs); the engine computes deviations from it. The baseline is NOT a
prediction. Debt identity: b_t = b_{t-1}(1+i)/(1+g) − sp, anchored to
gold_escenarios_deuda.csv (central). Variable names mirror the JS on purpose.
"""
from __future__ import annotations

from engine import constants as c
from engine.levers import Levers

Y0 = 2026
Y1 = 2050
N_YEARS = Y1 - Y0 + 1          # 25
YEARS = list(range(Y0, Y1 + 1))

# v16 R keys, in template order (extract L97-100)
SERIES_KEYS = [
    "lvl", "u", "pi", "g", "gnom", "wnom", "wreal", "wrealIdx", "b", "ief",
    "int", "pb", "saldo", "ipv", "precio", "cuota", "salmes", "salario", "esf",
    "pens", "dep", "arop", "edu", "d1", "nomreal", "p2", "d3", "p51", "gtot",
    "bls", "temp", "ujuv", "auton", "hip", "sobre", "bono", "spread", "r",
    "deficitAbs", "vida",
]


def french(principal: float, annual_rate_pct: float, n_months: int) -> float:
    """French amortization monthly payment (extract L93)."""
    i = annual_rate_pct / 1200.0
    return principal * i / (1 - (1 + i) ** (-n_months))


def run_scenario(levers: Levers) -> dict[str, list[float]]:
    L, B, V0 = levers, c.BASE_LEVERS, c.V0
    central, olddep = c.load_central(), c.load_olddep()
    R: dict[str, list[float]] = {k: [] for k in SERIES_KEYS}

    bono = L.r + c.TERM + L.prima / 100
    shock = (-(L.sp - B["sp"]) - c.E_R * (L.r - B["r"])
             + c.E_EXT * (L.ext - B["ext"]) - c.E_PM * (L.pm - B["pm"]))
    u_star_dev = c.A_Z * L.z + c.A_TAU * L.tau - c.A_LAM * (L.lam - B["lam"])

    lvl = 0.0; pi_dev = 0.0; di = 0.0
    b = central[Y0 - 1]["deuda"]                      # 105.6 (2025)
    sal_idx = 1.0; wr_idx = 1.0; pens_fac = 1.0; nom_idx = 1.0
    precio = V0["precio"]

    for k in range(N_YEARS):
        y = Y0 + k
        gc = central[y]
        prev = lvl
        lvl = c.RHO * lvl + (1 - c.RHO) * c.MULT * shock       # GDP level deviation (%)
        gap_u = c.OKUN * lvl                                    # slack: u below u*
        u = V0["u"] + u_star_dev - gap_u
        pi_dev = (c.THETA * pi_dev + c.KAPPA * gap_u
                  + c.GAMMA * (L.pm - B["pm"]) * c.PM_DECAY ** k)
        pi = V0["pi"] + pi_dev
        g = V0["g"] + (lvl - prev) + (L.lam - B["lam"])
        gnom = gc["g_nominal"] + (g - V0["g"]) + pi_dev

        # debt identity b_t = b_{t-1}(1+i)/(1+g) − sp, with 14 %/yr refinancing
        di = di + c.REFI * ((bono - V0["bono"]) - di)
        ief = gc["r_efectivo"] + di
        pb = gc["pb"] + L.sp - gc["presion_demog"] * L.dem
        b_prev = b
        b = b_prev * (1 + ief / 100) / (1 + gnom / 100) - pb
        intr = b_prev * ief / 100
        saldo = pb - intr

        # wage setting (WS)
        wnom = pi + L.lam + c.PHI * gap_u
        wreal = wnom - pi
        if k > 0:
            sal_idx *= 1 + wnom / 100
            wr_idx *= 1 + wreal / 100

        # housing
        ipv = (c.IPV_LR + (V0["ipv"] - c.IPV_LR) * c.IPV_REV ** k
               - c.E_IPV_R * (L.r - B["r"]) + c.E_IPV_G * (g - V0["g"]))
        if k > 0:
            precio *= 1 + ipv / 100
        cuota = french(precio * 0.8, L.r + c.DIFF, 300)
        salmes = V0["salmes"] * sal_idx
        esf = cuota / salmes * 100

        # pensions: mechanical identity pension x number / GDP
        if k > 0:
            pens_fac *= (1 + (pi + L.idx) / 100) / (1 + gnom / 100)
            nom_idx *= 1 + L.idx / 100
        dep_idx = 1 + (olddep[y] / olddep[Y0] - 1) * (1 + L.dem)
        dep = olddep[Y0] * dep_idx
        pens = V0["pens"] * dep_idx * pens_fac

        R["lvl"].append(lvl); R["u"].append(u); R["pi"].append(pi); R["g"].append(g)
        R["gnom"].append(gnom); R["wnom"].append(wnom); R["wreal"].append(wreal)
        R["wrealIdx"].append(wr_idx * 100); R["b"].append(b); R["ief"].append(ief)
        R["int"].append(intr); R["pb"].append(pb); R["saldo"].append(saldo)
        R["deficitAbs"].append(abs(min(0.0, saldo)))
        R["ipv"].append(ipv); R["precio"].append(precio); R["cuota"].append(cuota)
        R["salmes"].append(salmes); R["salario"].append(V0["salario"] * sal_idx)
        R["esf"].append(esf); R["pens"].append(pens); R["dep"].append(dep)
        R["nomreal"].append(nom_idx * 100)
        R["arop"].append(V0["arop"] + 0.55 * (u - V0["u"]) + 0.90 * L.sp)
        R["edu"].append(V0["edu"] - 0.090 * L.sp)
        R["d1"].append(V0["d1"] - 0.240 * L.sp)
        R["p2"].append(V0["p2"] - 0.125 * L.sp)
        R["d3"].append(V0["d3"] - 0.031 * L.sp)
        R["p51"].append(V0["p51"] - 0.145 * L.sp)
        R["gtot"].append(V0["gtot"] - 1.0 * L.sp)
        R["bls"].append(V0["bls"] + 12 * (L.r - B["r"]) + 2.5 * (u - V0["u"]))
        R["temp"].append(V0["temp"] + 0.25 * (u - V0["u"]) - 1.5 * L.z)
        R["ujuv"].append(c.RJUV * u)
        R["auton"].append(V0["auton"] + 0.12 * (u - V0["u"]) - 0.40 * (g - V0["g"]))
        R["hip"].append(max(0.0, V0["hip"] * (1 - 1.6 * (esf / (V0["cuota"] / V0["salmes"] * 100) - 1))))
        R["sobre"].append(V0["sobre"] + 0.18 * (esf - V0["cuota"] / V0["salmes"] * 100))
        R["bono"].append(bono); R["spread"].append(L.prima); R["r"].append(L.r)
        R["vida"].append(V0["vida"])
    return R


def baseline() -> dict[str, list[float]]:
    """The frozen-vintage baseline: all levers at base (cheap: 25 iterations)."""
    return run_scenario(Levers())
