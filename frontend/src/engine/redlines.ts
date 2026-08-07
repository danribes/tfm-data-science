import type { Scenario } from "./spain";
import { seriesOf, type AnySeriesKey } from "./derived";

/**
 * Port of engine/redlines.py evaluator (spec §4.5). Statuses are COMPUTED
 * from the scenario — never hand-written (v16 "semáforo vivo" rule).
 * near = within 10 % of |threshold| (0.5pp absolute band when threshold is 0).
 * Red-line DEFINITIONS come from the API's /redlines and from persona cards —
 * they are not duplicated here.
 */
export const NEAR_FRACTION = 0.1;
export const ZERO_THRESHOLD_BAND = 0.5; // pp — absolute near-band for zero thresholds (e.g. g < 0)

export type RedLineStatus = "crossed" | "near" | "safe" | "sd";

export const STATUS_LABEL: Record<RedLineStatus, string> = {
  crossed: "cruzada",
  near: "cerca",
  safe: "segura",
  sd: "s/d",
};

export function statusOf(
  value: number | null,
  threshold: number | null,
  cmp: "gt" | "lt" | null,
): RedLineStatus {
  if (threshold === null || value === null || cmp === null || !isFinite(value)) return "sd";
  const crossed = cmp === "gt" ? value > threshold : value < threshold;
  if (crossed) return "crossed";
  const band = threshold !== 0 ? NEAR_FRACTION * Math.abs(threshold) : ZERO_THRESHOLD_BAND;
  return Math.abs(value - threshold) <= band ? "near" : "safe";
}

export interface RedLineDef {
  id: string;
  label: string;
  series: string;
  threshold: number;
  cmp: string;
  source: string;
}

/** Extends RedLineDef so any field added to the API's /redlines shape
 * propagates here automatically instead of silently going missing. */
export interface RedLineResult extends RedLineDef {
  value: number;
  status: RedLineStatus;
}

/** Global red lines (mirrors engine/redlines.py::evaluate_redlines). */
export function evaluateRedlines(defs: RedLineDef[], scn: Scenario, k: number): RedLineResult[] {
  return defs.map((rl) => {
    const value = seriesOf(scn, rl.series as AnySeriesKey)[k];
    return {
      ...rl,
      value,
      status: statusOf(value, rl.threshold, rl.cmp as "gt" | "lt"),
    };
  });
}

export interface PersonaRed {
  t: string;
  thr: number | null;
  k: string | null;
  cmp: string | null;
  d: number | null;
  x: string;
}

export interface PersonaRedResult {
  t: string;
  x: string;
  d: number | null;
  value: number | null;
  status: RedLineStatus;
}

/** Persona display reds (handoff note 5): never merged with the global red lines. */
export function evaluatePersonaReds(reds: PersonaRed[], scn: Scenario, k: number): PersonaRedResult[] {
  return reds.map((r) => {
    const value = r.k === null ? null : seriesOf(scn, r.k as AnySeriesKey)[k];
    return {
      t: r.t,
      x: r.x,
      d: r.d,
      value,
      status: statusOf(value, r.thr, r.cmp as "gt" | "lt" | null),
    };
  });
}
