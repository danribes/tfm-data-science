const NEAR = 0.10; // same near fraction as the semaphore (spec §4.5 — v16 used 12%)

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
  let fillClass = "f";
  if (red !== undefined) {
    const crossed = redCmp === "gt" ? value > red : value < red;
    if (crossed) fillClass = "f bad";
    else if (Math.abs(value - red) <= Math.abs(red || 1) * NEAR) fillClass = "f warn2";
  }
  return (
    <div className="gaugebar">
      <span className={fillClass} style={{ width: pct(value, lo, hi) }} />
      <span className="bm" style={{ left: pct(base, lo, hi) }} />
      {red !== undefined && <span className="rl" style={{ left: pct(red, lo, hi) }} />}
    </div>
  );
}
