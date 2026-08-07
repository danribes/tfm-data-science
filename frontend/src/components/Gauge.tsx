import { statusOf, type RedLineStatus } from "../engine/redlines";

/** The dial paints exactly what the semáforo says. The near-band rule lives in
 *  ONE place (engine/redlines.ts::statusOf) — the fraction, the zero-threshold
 *  absolute band, and the gt/lt direction all come from there. An earlier
 *  version re-derived the band here as `|value − red| <= |red || 1| * 0.10`,
 *  which silently became a 0.1-absolute band when the threshold was 0 while
 *  statusOf used ZERO_THRESHOLD_BAND = 0.5 — so a `g < 0` red line would show
 *  a green dial beside an amber semáforo row on the same card. */
const STATUS_CLASS: Record<RedLineStatus, string> = {
  crossed: "f bad",
  near: "f warn2",
  safe: "f ok",
  sd: "f",
};

export function dialDomain(values: number[], red?: number): [number, number] {
  const all = red === undefined ? values : [...values, red];
  const lo = Math.min(...all);
  const hi = Math.max(...all);
  const pad = (hi - lo) * 0.16 || 1; // v16 chart() auto-domain rule
  return [lo - pad, hi + pad];
}

const pct = (v: number, lo: number, hi: number) =>
  `${Math.round(Math.min(100, Math.max(0, ((v - lo) / (hi - lo || 1)) * 100)) * 100) / 100}%`;

export function Gauge({
  value,
  lo,
  hi,
  base,
  red,
  redCmp = "gt",
}: {
  value: number;
  lo: number;
  hi: number;
  base: number;
  red?: number;
  redCmp?: "gt" | "lt";
}) {
  // No red line → no status to paint: the plain blue fill (default `.f`).
  // With one, `safe` is green (--s3); without that branch base.css's
  // `.gaugebar .f.ok` rule was dead and safe rendered blue.
  const fillClass = red === undefined ? "f" : STATUS_CLASS[statusOf(value, red, redCmp)];
  return (
    <div className="gaugebar">
      <span className={fillClass} style={{ width: pct(value, lo, hi) }} />
      <span className="bm" style={{ left: pct(base, lo, hi) }} />
      {red !== undefined && <span className="rl" style={{ left: pct(red, lo, hi) }} />}
    </div>
  );
}
