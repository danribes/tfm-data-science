import { nf, sg } from "../lib/fmt";
import { useRollup } from "../lib/motion";
import { runScenario, type Scenario } from "../engine/spain";
import { PRESETS, presetLevers } from "../engine/levers";
import { seriesOf, type AnySeriesKey } from "../engine/derived";
import type { PersonaRedOut } from "../api/types";
import { Gauge, dialDomain } from "./Gauge";
import { Stamp } from "./Stamp";

/** Display format per engine series (decimals, unit suffix). */
export const SERIES_FORMAT: Record<string, { dec: number; unit: string }> = {
  lvl: { dec: 2, unit: "%" }, u: { dec: 1, unit: "%" }, pi: { dec: 1, unit: "%" },
  g: { dec: 1, unit: "%" }, gnom: { dec: 1, unit: "%" }, wnom: { dec: 1, unit: "%" },
  wreal: { dec: 1, unit: "%" }, wrealIdx: { dec: 1, unit: "" }, b: { dec: 1, unit: "%PIB" },
  ief: { dec: 2, unit: "%" }, int: { dec: 1, unit: "%PIB" }, pb: { dec: 1, unit: "%PIB" },
  saldo: { dec: 1, unit: "%PIB" }, ipv: { dec: 1, unit: "% a/a" }, precio: { dec: 0, unit: "€" },
  cuota: { dec: 0, unit: "€/mes" }, salmes: { dec: 0, unit: "€/mes" }, salario: { dec: 0, unit: "€/año" },
  esf: { dec: 1, unit: "%" }, pens: { dec: 2, unit: "%PIB" }, dep: { dec: 1, unit: "/100" },
  arop: { dec: 1, unit: "%" }, edu: { dec: 2, unit: "%PIB" }, d1: { dec: 2, unit: "%PIB" },
  nomreal: { dec: 1, unit: "" }, p2: { dec: 2, unit: "%PIB" }, d3: { dec: 2, unit: "%PIB" },
  p51: { dec: 2, unit: "%PIB" }, gtot: { dec: 1, unit: "%PIB" }, bls: { dec: 0, unit: "% neto" },
  temp: { dec: 1, unit: "%" }, ujuv: { dec: 1, unit: "%" }, auton: { dec: 1, unit: "%" },
  hip: { dec: 0, unit: "/año" }, sobre: { dec: 1, unit: "%" }, bono: { dec: 2, unit: "%" },
  spread: { dec: 0, unit: "pb" }, r: { dec: 2, unit: "%" }, deficitAbs: { dec: 1, unit: "%PIB" },
  vida: { dec: 1, unit: "años" }, ipvreal: { dec: 1, unit: "% a/a" },
};

/** Series where a positive delta is bad (red). Everything else: positive = good (green). */
export const UP_IS_BAD = new Set([
  "b", "u", "pi", "cuota", "esf", "int", "bono", "spread", "r", "arop", "dep",
  "pens", "sobre", "temp", "ujuv", "bls", "deficitAbs",
]);

/** Half-width (years) of the baseline window used to build a gauge's frame. */
const GAUGE_WINDOW = 4;

// The frame also has to cover whatever the 8 static presets (S0..S7) can reach, so a
// lever pass-through with a flat baseline (e.g. Euríbor `r`, `spread`) doesn't pin the
// bar the moment a real preset is applied. Presets are static config — not the user's
// current lever position — so folding them into the frame keeps the frame fully
// lever-independent (spec: no user-lever input may feed the domain).
//
// Computing 8 scenarios per gauge per render would be wasteful, so both the scenarios
// and their per-series projections are memoized at module scope: the 8 preset runs
// happen once per session (runScenario is ~1 ms; 8 runs total for the whole app), and
// each series' preset values are derived once per series key and reused by every gauge
// tile (across all personas, all renders) that reads that key.
let _presetScenarios: Scenario[] | null = null;
function presetScenarios(): Scenario[] {
  if (_presetScenarios === null) {
    _presetScenarios = PRESETS.map((p) => runScenario(presetLevers(p.id)));
  }
  return _presetScenarios;
}

const _presetSeriesCache = new Map<AnySeriesKey, number[][]>();
/** The 8 presets' full projections for one series key, computed once and cached. */
function presetSeriesFor(key: AnySeriesKey): number[][] {
  let cached = _presetSeriesCache.get(key);
  if (!cached) {
    cached = presetScenarios().map((scn) => seriesOf(scn, key));
    _presetSeriesCache.set(key, cached);
  }
  return cached;
}

interface TileProps {
  out: { k: string; lab: string };
  scn: Scenario;
  base: Scenario;
  k: number;
  fresh: boolean;
  year: number;
  red?: PersonaRedOut;
}

/** One tile = one component so useRollup (a hook) can animate its figure (spec §5). */
function KpiTile({ out, scn, base, k, fresh, year, red }: TileProps) {
  const key = out.k as AnySeriesKey;
  const fmtSpec = SERIES_FORMAT[out.k] ?? { dec: 1, unit: "" };
  const scnSeries = seriesOf(scn, key);
  const baseSeries = seriesOf(base, key);
  const value = scnSeries[k];
  const baseValue = baseSeries[k];
  const shown = useRollup(value); // ~180 ms roll-up on change; exact on first render
  const delta = value - baseValue;
  // Gauge frame is lever-independent: built ONLY from constants (never the user's current
  // scenario) so moving a lever moves the needle, not the frame. Task 13 first fixed this by
  // windowing the baseline around the selected year instead of spanning 2026-2050 (that older
  // domain let a compounding series' 2050 endpoint dwarf any near-term move — a 200bp rate rise
  // shifted debt at 2026 by 0.83pp but the gauge by only ~0.3 points). But for series whose
  // baseline is flat (e.g. Euríbor `r`, `spread` — pure lever pass-throughs with no engine
  // dynamics), the window collapses to ~baseValue, so any real lever move lands far outside the
  // frame and the bar pins at 0 or 100. So the frame is now the baseline window UNION the value
  // this series takes at the same year under each of the 8 static presets (S0..S7) — sized to
  // the real reachable space while remaining lever-independent, since presets are fixed config,
  // not the live lever position.
  const lo_i = Math.max(0, k - GAUGE_WINDOW);
  const hi_i = Math.min(baseSeries.length - 1, k + GAUGE_WINDOW);
  const presetValuesAtK = presetSeriesFor(key).map((series) => series[k]);
  const [lo, hi] = dialDomain(
    [...baseSeries.slice(lo_i, hi_i + 1), ...presetValuesAtK],
    red?.thr ?? undefined,
  );
  const deltaClass =
    Math.abs(delta) <= 1e-9 ? "" : (delta > 0) === UP_IS_BAD.has(out.k) ? "bad" : "good";
  return (
    <div className="out">
      <span className="o-seal"><Stamp fresh={fresh} year={year} /></span>
      <div className="o-label">{out.lab}</div>
      <div className="o-val">{nf(shown, fmtSpec.dec)} <small>{fmtSpec.unit}</small></div>
      <div className={`o-delta ${deltaClass}`}>{sg(delta, fmtSpec.dec)} vs base</div>
      <Gauge
        value={value}
        lo={lo}
        hi={hi}
        base={baseValue}
        red={red?.thr ?? undefined}
        redCmp={(red?.cmp as "gt" | "lt") ?? "gt"}
      />
    </div>
  );
}

export function KpiRow({
  outs,
  scn,
  base,
  k,
  fresh,
  year,
  personaReds,
}: {
  outs: { k: string; lab: string }[];
  scn: Scenario;
  base: Scenario;
  k: number;
  fresh: boolean;
  year: number;
  personaReds?: PersonaRedOut[];
}) {
  return (
    <div className="outs">
      {outs.map((o) => (
        <KpiTile
          key={o.k}
          out={o}
          scn={scn}
          base={base}
          k={k}
          fresh={fresh}
          year={year}
          red={personaReds?.find((r) => r.k === o.k)}
        />
      ))}
    </div>
  );
}
