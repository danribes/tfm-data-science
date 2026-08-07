import * as C from "./constants";
import { BASE_LEVERS, CENTRAL, OLDDEP, V0 } from "./vintage";
import type { Levers } from "./levers";

export const Y0 = 2026;
export const Y1 = 2050;
export const N_YEARS = Y1 - Y0 + 1; // 25
export const YEARS: number[] = Array.from({ length: N_YEARS }, (_, k) => Y0 + k);

/** v16 R keys, template order (engine/spain.py SERIES_KEYS). */
export const SERIES_KEYS = [
  "lvl", "u", "pi", "g", "gnom", "wnom", "wreal", "wrealIdx", "b", "ief",
  "int", "pb", "saldo", "ipv", "precio", "cuota", "salmes", "salario", "esf",
  "pens", "dep", "arop", "edu", "d1", "nomreal", "p2", "d3", "p51", "gtot",
  "bls", "temp", "ujuv", "auton", "hip", "sobre", "bono", "spread", "r",
  "deficitAbs", "vida",
] as const;
export type SeriesKey = (typeof SERIES_KEYS)[number];
export type Scenario = Record<SeriesKey, number[]>;

/** French amortization monthly payment (engine/spain.py french()). */
export function french(principal: number, annualRatePct: number, nMonths: number): number {
  const i = annualRatePct / 1200.0;
  return (principal * i) / (1 - Math.pow(1 + i, -nMonths));
}

export function runScenario(L: Levers): Scenario {
  const B = BASE_LEVERS;
  const R = Object.fromEntries(SERIES_KEYS.map((k) => [k, [] as number[]])) as Scenario;

  const bono = L.r + C.TERM + L.prima / 100;
  const shock =
    -(L.sp - B.sp) - C.E_R * (L.r - B.r) + C.E_EXT * (L.ext - B.ext) - C.E_PM * (L.pm - B.pm);
  const uStarDev = C.A_Z * L.z + C.A_TAU * L.tau - C.A_LAM * (L.lam - B.lam);

  let lvl = 0.0;
  let piDev = 0.0;
  let di = 0.0;
  let b = CENTRAL[Y0 - 1].deuda; // 105.6 (2025)
  let salIdx = 1.0;
  let wrIdx = 1.0;
  let pensFac = 1.0;
  let nomIdx = 1.0;
  let precio = V0.precio;

  for (let k = 0; k < N_YEARS; k++) {
    const y = Y0 + k;
    const gc = CENTRAL[y];
    const prev = lvl;
    lvl = C.RHO * lvl + (1 - C.RHO) * C.MULT * shock; // GDP level deviation (%)
    const gapU = C.OKUN * lvl; // slack: u below u*
    const u = V0.u + uStarDev - gapU;
    piDev = C.THETA * piDev + C.KAPPA * gapU + C.GAMMA * (L.pm - B.pm) * Math.pow(C.PM_DECAY, k);
    const pi = V0.pi + piDev;
    const g = V0.g + (lvl - prev) + (L.lam - B.lam);
    const gnom = gc.g_nominal + (g - V0.g) + piDev;

    // debt identity b_t = b_{t-1}(1+i)/(1+g) − sp, with 14 %/yr refinancing
    di = di + C.REFI * ((bono - V0.bono) - di);
    const ief = gc.r_efectivo + di;
    const pb = gc.pb + L.sp - gc.presion_demog * L.dem;
    const bPrev = b;
    b = (bPrev * (1 + ief / 100)) / (1 + gnom / 100) - pb;
    const intr = (bPrev * ief) / 100;
    const saldo = pb - intr;

    // wage setting (WS)
    const wnom = pi + L.lam + C.PHI * gapU;
    const wreal = wnom - pi;
    if (k > 0) {
      salIdx *= 1 + wnom / 100;
      wrIdx *= 1 + wreal / 100;
    }

    // housing
    const ipv =
      C.IPV_LR + (V0.ipv - C.IPV_LR) * Math.pow(C.IPV_REV, k) -
      C.E_IPV_R * (L.r - B.r) + C.E_IPV_G * (g - V0.g);
    if (k > 0) precio *= 1 + ipv / 100;
    const cuota = french(precio * 0.8, L.r + C.DIFF, 300);
    const salmes = V0.salmes * salIdx;
    const esf = (cuota / salmes) * 100;

    // pensions: mechanical identity pension x number / GDP
    if (k > 0) {
      pensFac *= (1 + (pi + L.idx) / 100) / (1 + gnom / 100);
      nomIdx *= 1 + L.idx / 100;
    }
    const depIdx = 1 + (OLDDEP[y] / OLDDEP[Y0] - 1) * (1 + L.dem);
    const dep = OLDDEP[Y0] * depIdx;
    const pens = V0.pens * depIdx * pensFac;

    R.lvl.push(lvl); R.u.push(u); R.pi.push(pi); R.g.push(g);
    R.gnom.push(gnom); R.wnom.push(wnom); R.wreal.push(wreal);
    R.wrealIdx.push(wrIdx * 100); R.b.push(b); R.ief.push(ief);
    R.int.push(intr); R.pb.push(pb); R.saldo.push(saldo);
    R.deficitAbs.push(Math.abs(Math.min(0.0, saldo)));
    R.ipv.push(ipv); R.precio.push(precio); R.cuota.push(cuota);
    R.salmes.push(salmes); R.salario.push(V0.salario * salIdx);
    R.esf.push(esf); R.pens.push(pens); R.dep.push(dep);
    R.nomreal.push(nomIdx * 100);
    R.arop.push(V0.arop + 0.55 * (u - V0.u) + 0.90 * L.sp);
    R.edu.push(V0.edu - 0.090 * L.sp);
    R.d1.push(V0.d1 - 0.240 * L.sp);
    R.p2.push(V0.p2 - 0.125 * L.sp);
    R.d3.push(V0.d3 - 0.031 * L.sp);
    R.p51.push(V0.p51 - 0.145 * L.sp);
    R.gtot.push(V0.gtot - 1.0 * L.sp);
    R.bls.push(V0.bls + 12 * (L.r - B.r) + 2.5 * (u - V0.u));
    R.temp.push(V0.temp + 0.25 * (u - V0.u) - 1.5 * L.z);
    R.ujuv.push(C.RJUV * u);
    R.auton.push(V0.auton + 0.12 * (u - V0.u) - 0.40 * (g - V0.g));
    R.hip.push(Math.max(0.0, V0.hip * (1 - 1.6 * (esf / ((V0.cuota / V0.salmes) * 100) - 1))));
    R.sobre.push(V0.sobre + 0.18 * (esf - (V0.cuota / V0.salmes) * 100));
    R.bono.push(bono); R.spread.push(L.prima); R.r.push(L.r);
    R.vida.push(V0.vida);
  }
  return R;
}

let _baseline: Scenario | null = null;
/** The frozen-vintage baseline: all levers at base. Computed once per session. */
export function baseline(): Scenario {
  if (_baseline === null) _baseline = runScenario({ ...BASE_LEVERS });
  return _baseline;
}
