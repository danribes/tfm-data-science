import { BASE_LEVERS } from "./vintage";

export interface Levers {
  r: number;
  prima: number;
  sp: number;
  lam: number;
  pm: number;
  tau: number;
  z: number;
  ext: number;
  dem: number;
  idx: number;
}
export type LeverId = keyof Levers;

export interface LeverSpec {
  id: LeverId;
  sym: string;
  nm: string;
  unit: string;
  min: number;
  max: number;
  step: number;
  dec: number;
  src: string;
}

// v16 `const LEVERS` — Spanish copy verbatim (engine/levers.py LEVER_SPECS)
export const LEVER_SPECS: LeverSpec[] = [
  { id: "r", sym: "r", nm: "Tipo de interés · Euríbor 12m", unit: "%", min: 0.0, max: 6.0, step: 0.05, dec: 2, src: "ecb_euribor12m.csv · 2026-06" },
  { id: "prima", sym: "σ", nm: "Prima de riesgo · spread ES–DE", unit: "pb", min: 0.0, max: 400.0, step: 5.0, dec: 0, src: "ecb_bono10y_{es,de}.csv · 2026-06" },
  { id: "sp", sym: "sp", nm: "Saldo primario · Δ vs central", unit: "pp PIB", min: -4.0, max: 4.0, step: 0.1, dec: 1, src: "gold_escenarios_deuda.csv (central)" },
  { id: "lam", sym: "λ", nm: "Productividad", unit: "%/año", min: -0.5, max: 2.5, step: 0.1, dec: 1, src: "PWT + INE · desplaza la PS" },
  { id: "pm", sym: "pᵐ", nm: "Precio importaciones/energía", unit: "% a/a", min: -50.0, max: 100.0, step: 5.0, dec: 0, src: "WEO commodity prices" },
  { id: "tau", sym: "τ", nm: "Presión fiscal · cuña laboral", unit: "pp", min: -5.0, max: 5.0, step: 0.25, dec: 2, src: "Eurostat GFS · desplaza la WS" },
  { id: "z", sym: "z", nm: "Instituciones laborales", unit: "índice", min: -2.0, max: 2.0, step: 0.1, dec: 1, src: "OECD/Eurostat · desplaza la WS" },
  { id: "ext", sym: "Y*", nm: "Demanda externa", unit: "% a/a", min: -4.0, max: 6.0, step: 0.1, dec: 1, src: "WEO · canal exterior (U7)" },
  { id: "dem", sym: "β₆₅", nm: "Presión demográfica", unit: "×", min: -1.0, max: 1.0, step: 0.05, dec: 2, src: "gold_projections.csv · variante" },
  { id: "idx", sym: "ι", nm: "Indexación pensiones/nóminas", unit: "IPC+pp", min: -1.5, max: 1.0, step: 0.1, dec: 1, src: "regla de revalorización · palanca" },
];

// v16 `const PRESETS` verbatim; r offsets resolved against BASE (S1/S7: BASE.r + 2 = 4.8)
export const PRESETS: { id: string; nm: string; set: Partial<Levers> }[] = [
  { id: "S0", nm: "S0 base", set: {} },
  { id: "S1", nm: "S1 tipos +200 pb", set: { r: BASE_LEVERS.r + 2 } },
  { id: "S2", nm: "S2 petróleo +50 %", set: { pm: 50.0 } },
  { id: "S3", nm: "S3 consolidación", set: { sp: 1.0 } },
  { id: "S4", nm: "S4 productividad", set: { lam: 1.4 } },
  { id: "S5", nm: "S5 desregulación lab.", set: { z: -1.0, tau: -1.5 } },
  { id: "S6", nm: "S6 envejecimiento", set: { dem: 0.6 } },
  { id: "S7", nm: "S7 adverso", set: { r: BASE_LEVERS.r + 2, pm: 50.0, prima: 150.0 } },
];

const EPS = 1e-9;
export const LEVER_IDS = LEVER_SPECS.map((s) => s.id);

export function presetLevers(presetId: string): Levers {
  const p = PRESETS.find((q) => q.id === presetId);
  if (!p) throw new Error(`unknown preset id: ${presetId} (valid: S0..S7)`);
  return { ...BASE_LEVERS, ...p.set };
}

export function isMoved(L: Levers, id: LeverId): boolean {
  return Math.abs(L[id] - BASE_LEVERS[id]) > EPS;
}

export function allAtBase(L: Levers): boolean {
  return LEVER_IDS.every((id) => !isMoved(L, id));
}

/** v16 railState(): which preset the CURRENT full vector equals, if any. */
export function activePresetId(L: Levers): string | null {
  for (const p of PRESETS) {
    const target = { ...BASE_LEVERS, ...p.set };
    if (LEVER_IDS.every((id) => Math.abs(L[id] - target[id]) <= EPS)) return p.id;
  }
  return null;
}
